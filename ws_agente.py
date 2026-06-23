#!/usr/bin/env python3
"""
ws_agente.py — Server WebSocket per l'interfaccia 3D dell'agente AI
Dipendenze: pip install anthropic websockets
Avvio:      python ws_agente.py
Browser:    apri interfaccia.html
"""
from __future__ import annotations

import asyncio
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import datetime
import uuid

import anthropic
import websockets

# ─────────────────────────────────────────────────────────────────────────────
# COSTANTI
# ─────────────────────────────────────────────────────────────────────────────
MODEL       = "claude-opus-4-8"
MEMORY_DIR  = pathlib.Path("memoria")
MEMORY_FILE = MEMORY_DIR / "memoria.json"
SKILLS_DIR  = pathlib.Path("skills")
OWN_FILES   = {"agente.py", "ws_agente.py", "interfaccia.html"}
CMD_TIMEOUT = 90
PORT        = 8765

# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICAZIONE COMANDI DISTRUTTIVI (identica ad agente.py)
# ─────────────────────────────────────────────────────────────────────────────
def is_destructive(command: str) -> bool:
    patterns = [
        r'\bRemove-Item\b', r'\bri\b',  r'\bdel\b',    r'\berase\b',
        r'\brd\b',          r'\brmdir\b',r'\brm\b',     r'\bformat\b(?!-)',
        r'\bClear-Content\b',r'\bcc\b', r'-Recurse\b',  r'-Force\b',
        r'\breg\s+delete\b', r'\bRemove-ItemProperty\b',
        r'\bStop-Process\b', r'\bkill\b', r'\btaskkill\b',
        r'\bSet-ExecutionPolicy\b',
        r'(?<![>])>(?![>])',
    ]
    for p in patterns:
        if re.search(p, command, re.IGNORECASE):
            return True
    return not command.strip()

# ─────────────────────────────────────────────────────────────────────────────
# MEMORIA
# ─────────────────────────────────────────────────────────────────────────────
def load_memory() -> dict:
    MEMORY_DIR.mkdir(exist_ok=True)
    if MEMORY_FILE.exists():
        with io.open(MEMORY_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_memory(data: dict) -> None:
    MEMORY_DIR.mkdir(exist_ok=True)
    with io.open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────────────────────────────────────
# SKILL
# ─────────────────────────────────────────────────────────────────────────────
def list_skills() -> list[dict]:
    SKILLS_DIR.mkdir(exist_ok=True)
    out = []
    for path in sorted(SKILLS_DIR.iterdir()):
        if not path.is_file() or path.suffix not in (".ps1", ".py"):
            continue
        with io.open(path, "r", encoding="utf-8") as f:
            first = f.readline().strip()
        clean = first.lstrip("#").strip()
        parts = [p.strip() for p in clean.split("|")]
        desc = parts[1] if len(parts) >= 2 else clean
        out.append({"name": path.stem, "desc": desc})
    return out

def save_skill(name: str, desc: str, code: str, ext: str = ".ps1") -> pathlib.Path:
    SKILLS_DIR.mkdir(exist_ok=True)
    header = f"# {name} | {desc} | {datetime.date.today().isoformat()}\n"
    path = SKILLS_DIR / (name + ext)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(header + code)
    return path

def skill_has_destructive(path: pathlib.Path) -> bool:
    with io.open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#") and is_destructive(s):
                return True
    return False

# ─────────────────────────────────────────────────────────────────────────────
# ESECUZIONE POWERSHELL (sincrona, eseguita in thread)
# ─────────────────────────────────────────────────────────────────────────────
def _ps_sync(command: str) -> tuple[str, str, int]:
    proc = subprocess.Popen(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace"
    )
    try:
        out, err = proc.communicate(timeout=CMD_TIMEOUT)
        return out, err, proc.returncode
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        return out or "", f"[TIMEOUT] Killato dopo {CMD_TIMEOUT}s.\n" + (err or ""), -1

async def run_ps(cmd: str) -> tuple[str, str, int]:
    return await asyncio.to_thread(_ps_sync, cmd)

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
Sei un agente AI autonomo che opera su Windows 10/11 con PowerShell.
Raggiungi l'obiettivo dell'utente eseguendo comandi PowerShell uno alla volta.

Rispondi SEMPRE con un oggetto JSON valido e nient'altro (nessun testo prima o dopo).
Formati disponibili:

{"type":"command","cmd":"<comando PS>","reason":"<motivazione breve>"}
{"type":"save_skill","name":"<nome_senza_estensione>","ext":".ps1","description":"<desc>","code":"<codice>"}
{"type":"run_skill","name":"<nome_senza_estensione>","reason":"<motivazione>"}
{"type":"message","text":"<testo per l'utente>"}
{"type":"done","summary":"<riepilogo>"}

Campo opzionale aggiungibile a qualsiasi risposta:
"memory_update":{"chiave":"valore"}

VINCOLI ASSOLUTI:
- Non modificare mai agente.py, ws_agente.py, interfaccia.html.
- Una sola azione per risposta.
- Preferisci skill esistenti se applicabili.
"""

def _parse(raw: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE).replace("```", "").strip()
    try: return json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m: return json.loads(m.group())
        raise

# ─────────────────────────────────────────────────────────────────────────────
# LOOP AGENTE (una istanza per connessione WebSocket)
# ─────────────────────────────────────────────────────────────────────────────
async def agent_loop(ws, client: anthropic.Anthropic, inbox: asyncio.Queue,
                     confirms: dict[str, asyncio.Future]) -> None:
    memory = load_memory()
    skills = list_skills()

    # Invia stato iniziale al browser
    await ws.send(json.dumps({
        "type": "init", "model": MODEL,
        "memory": memory, "skills": skills
    }))

    # Attende il primo obiettivo
    msg = await inbox.get()
    if msg.get("type") != "objective":
        return

    ctx = []
    if memory:
        ctx.append("MEMORIA:\n" + json.dumps(memory, ensure_ascii=False))
    if skills:
        ctx.append("SKILL:\n" + "\n".join(f"- {s['name']}: {s['desc']}" for s in skills))
    first = ("\n\n".join(ctx) + "\n\n" if ctx else "") + "OBIETTIVO: " + msg["text"]
    history: list[dict] = [{"role": "user", "content": first}]

    while True:
        # Chiama Claude in un thread separato (blocca senza bloccare il loop async)
        try:
            resp = await asyncio.to_thread(lambda: client.messages.create(
                model=MODEL, max_tokens=4096,
                system=SYSTEM_PROMPT, messages=history
            ))
        except Exception as e:
            await ws.send(json.dumps({"type": "error", "text": str(e)}))
            return

        raw = resp.content[0].text.strip()
        history.append({"role": "assistant", "content": raw})

        try:
            action = _parse(raw)
        except Exception:
            history.append({"role": "user", "content": "ERRORE: risposta non JSON valido. Riprova."})
            continue

        # Aggiornamento memoria (campo opzionale)
        if isinstance(action.get("memory_update"), dict):
            memory.update(action["memory_update"])
            save_memory(memory)
            await ws.send(json.dumps({"type": "memory_update", "data": memory}))

        atype = action.get("type", "")

        # ── command ────────────────────────────────────────────────────────────
        if atype == "command":
            cmd    = action.get("cmd", "").strip()
            reason = action.get("reason", "")

            # Vincolo di stabilità
            if any(f in cmd for f in OWN_FILES):
                fb = f"[SICUREZZA] Rifiutato: il comando fa riferimento a un file protetto."
                await ws.send(json.dumps({"type": "result", "stdout": fb, "stderr": "", "rc": -1}))
                history.append({"role": "user", "content": fb})
                continue

            destr = is_destructive(cmd)
            await ws.send(json.dumps({"type": "command", "cmd": cmd, "reason": reason, "destructive": destr}))

            if destr:
                cid = uuid.uuid4().hex[:8]
                fut: asyncio.Future = asyncio.get_event_loop().create_future()
                confirms[cid] = fut
                await ws.send(json.dumps({"type": "destructive", "cmd": cmd, "id": cid}))
                answer = await fut          # aspetta la risposta del browser
                confirms.pop(cid, None)
                if answer == "n":
                    await ws.send(json.dumps({"type": "skipped"}))
                    history.append({"role": "user", "content": "Comando saltato dall'utente."})
                    continue

            stdout, stderr, rc = await run_ps(cmd)
            await ws.send(json.dumps({"type": "result", "stdout": stdout, "stderr": stderr, "rc": rc}))

            fb = f"Comando eseguito. RC={rc}"
            if stdout.strip(): fb += f"\nSTDOUT:\n{stdout}"
            if stderr.strip(): fb += f"\nSTDERR:\n{stderr}"
            history.append({"role": "user", "content": fb})

        # ── save_skill ─────────────────────────────────────────────────────────
        elif atype == "save_skill":
            name = action.get("name", "skill").strip()
            ext  = action.get("ext", ".ps1")
            desc = action.get("description", "")
            code = action.get("code", "")
            save_skill(name, desc, code, ext)
            skills = list_skills()
            await ws.send(json.dumps({"type": "skill_saved", "name": name, "skills": skills}))
            history.append({"role": "user", "content": f"Skill '{name}' salvata."})

        # ── run_skill ──────────────────────────────────────────────────────────
        elif atype == "run_skill":
            name = action.get("name", "").strip()
            skill_path: pathlib.Path | None = None
            for ext in (".ps1", ".py"):
                c = SKILLS_DIR / (name + ext)
                if c.exists(): skill_path = c; break

            if skill_path is None:
                fb = f"ERRORE: skill '{name}' non trovata."
                await ws.send(json.dumps({"type": "result", "stdout": "", "stderr": fb, "rc": -1}))
                history.append({"role": "user", "content": fb})
                continue

            if skill_has_destructive(skill_path):
                cid = uuid.uuid4().hex[:8]
                fut = asyncio.get_event_loop().create_future()
                confirms[cid] = fut
                await ws.send(json.dumps({"type": "destructive", "cmd": f"[SKILL] {skill_path.name}", "id": cid}))
                answer = await fut
                confirms.pop(cid, None)
                if answer == "n":
                    await ws.send(json.dumps({"type": "skipped"}))
                    history.append({"role": "user", "content": f"Skill '{name}' saltata."})
                    continue

            if skill_path.suffix == ".ps1":
                stdout, stderr, rc = await run_ps(f"& '{skill_path}'")
            else:
                def _py():
                    p = subprocess.Popen(
                        [sys.executable, str(skill_path)],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        text=True, encoding="utf-8", errors="replace"
                    )
                    try:
                        o, e = p.communicate(timeout=CMD_TIMEOUT)
                        return o, e, p.returncode
                    except subprocess.TimeoutExpired:
                        p.kill(); o, e = p.communicate()
                        return o or "", f"[TIMEOUT]\n" + (e or ""), -1
                stdout, stderr, rc = await asyncio.to_thread(_py)

            await ws.send(json.dumps({"type": "result", "stdout": stdout, "stderr": stderr, "rc": rc}))
            fb = f"Skill '{name}' eseguita. RC={rc}"
            if stdout.strip(): fb += f"\nSTDOUT:\n{stdout}"
            if stderr.strip(): fb += f"\nSTDERR:\n{stderr}"
            history.append({"role": "user", "content": fb})

        # ── message ────────────────────────────────────────────────────────────
        elif atype == "message":
            await ws.send(json.dumps({"type": "message", "text": action.get("text", "")}))
            reply = await inbox.get()
            history.append({"role": "user", "content": reply.get("text", "(nessuna risposta)")})

        # ── done ───────────────────────────────────────────────────────────────
        elif atype == "done":
            await ws.send(json.dumps({"type": "done", "summary": action.get("summary", "")}))
            new = await inbox.get()
            if new.get("type") == "objective":
                history.append({"role": "user", "content": "NUOVO OBIETTIVO: " + new["text"]})
            else:
                break

        else:
            history.append({"role": "user", "content": f"Tipo '{atype}' non riconosciuto."})


# ─────────────────────────────────────────────────────────────────────────────
# GESTORE CONNESSIONE WEBSOCKET
# ─────────────────────────────────────────────────────────────────────────────
async def handler(ws):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        await ws.send(json.dumps({"type": "error", "text": "ANTHROPIC_API_KEY non impostata."}))
        return

    client = anthropic.Anthropic(api_key=api_key)
    inbox:    asyncio.Queue                   = asyncio.Queue()
    confirms: dict[str, asyncio.Future]       = {}

    # Task separato per ricevere messaggi dal browser
    async def receiver():
        try:
            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("type") == "confirm":
                    fut = confirms.pop(msg["id"], None)
                    if fut and not fut.done():
                        fut.set_result(msg["answer"])
                else:
                    await inbox.put(msg)
        except websockets.exceptions.ConnectionClosed:
            pass

    recv_task = asyncio.create_task(receiver())
    try:
        await agent_loop(ws, client, inbox, confirms)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        recv_task.cancel()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
async def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERRORE: variabile d'ambiente ANTHROPIC_API_KEY non impostata. Uscita.")
        sys.exit(1)

    print(f"◈ Server WebSocket avviato su ws://localhost:{PORT}")
    print(f"  Modello: {MODEL}")
    print(f"  Apri interfaccia.html nel browser per iniziare.\n")

    async with websockets.serve(handler, "localhost", PORT):
        await asyncio.Future()  # blocca per sempre

if __name__ == "__main__":
    asyncio.run(main())
