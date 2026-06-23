#!/usr/bin/env python3
"""
agente.py — Agente AI autonomo per PowerShell (Windows 10/11)
Dipendenza: pip install anthropic
Avvio:      python agente.py
"""

from __future__ import annotations

import io
import json
import os
import pathlib
import re
import subprocess
import sys
import datetime

import anthropic

# ─────────────────────────────────────────────────────────────────────────────
# COSTANTI
# ─────────────────────────────────────────────────────────────────────────────
MODEL       = "claude-opus-4-8"
LOG_FILE    = "agent_log.txt"
MEMORY_DIR  = pathlib.Path("memoria")
MEMORY_FILE = MEMORY_DIR / "memoria.json"
SKILLS_DIR  = pathlib.Path("skills")
OWN_FILE    = pathlib.Path(__file__).resolve()   # usato dal vincolo di stabilità
CMD_TIMEOUT = 90  # secondi prima di killare il processo


# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICAZIONE COMANDI DISTRUTTIVI
#
# Funzione isolata e completamente commentata.
# Riceve la stringa grezza del comando e restituisce:
#   True  → il comando è distruttivo (richiede conferma utente)
#   False → il comando è sicuro (eseguito automaticamente)
#
# Principio fail-safe: in caso di dubbio si preferisce True.
# ─────────────────────────────────────────────────────────────────────────────
def is_destructive(command: str) -> bool:
    # Ogni elemento è un pattern regex che identifica un comando, un alias,
    # un flag o un operatore considerato potenzialmente distruttivo.
    # re.IGNORECASE applicato in re.search rende tutti i match case-insensitive,
    # quindi "remove-item", "REMOVE-ITEM" e "Remove-Item" sono equivalenti.
    patterns = [
        r'\bRemove-Item\b',          # cmdlet PS: cancella file, dir, chiavi registro
        r'\bri\b',                   # alias PowerShell di Remove-Item
        r'\bdel\b',                  # comando CMD classico per eliminare file
        r'\berase\b',                # alias CMD di del
        r'\brd\b',                   # alias CMD di rmdir (remove directory)
        r'\brmdir\b',                # rimuove directory in CMD e PowerShell
        r'\brm\b',                   # alias Unix/PowerShell di Remove-Item
        r'\bformat\b',               # formatta un volume o disco
        r'\bClear-Content\b',        # svuota il contenuto di un file (senza cancellarlo)
        r'\bcc\b',                   # alias PowerShell di Clear-Content
        r'-Recurse\b',               # flag PS: rende un'operazione ricorsiva (amplifica impatto)
        r'-Force\b',                 # flag PS: bypassa protezioni e attributi read-only
        r'\breg\s+delete\b',         # cancella chiavi o valori dal Registro di sistema
        r'\bRemove-ItemProperty\b',  # rimuove proprietà/valori dal registro via PS
        r'\bStop-Process\b',         # termina un processo in esecuzione
        r'\bkill\b',                 # alias PS di Stop-Process, e comando Unix
        r'\btaskkill\b',             # termina processi tramite CMD
        r'\bSet-ExecutionPolicy\b',  # modifica la policy di esecuzione degli script PS
        r'(?<![>])>(?![>])',         # redirect singolo > (sovrascrive file; >> non è flaggato)
    ]

    for pattern in patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True

    # Comando vuoto: non classificabile → fail-safe, considerato distruttivo
    return not command.strip()


# ─────────────────────────────────────────────────────────────────────────────
# MEMORIA PERSISTENTE
# ─────────────────────────────────────────────────────────────────────────────
def load_memory() -> dict:
    MEMORY_DIR.mkdir(exist_ok=True)
    if MEMORY_FILE.exists():
        with io.open(MEMORY_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_memory(data: dict) -> None:
    MEMORY_DIR.mkdir(exist_ok=True)
    with io.open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# SKILL PERSISTENTI
# ─────────────────────────────────────────────────────────────────────────────
def list_skills() -> list[dict]:
    """Elenca le skill disponibili leggendo l'intestazione di ogni file."""
    SKILLS_DIR.mkdir(exist_ok=True)
    skills = []
    for path in sorted(SKILLS_DIR.iterdir()):
        if not path.is_file() or path.suffix not in (".ps1", ".py"):
            continue
        with io.open(path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        # Formato intestazione atteso: # nome | descrizione | data
        clean = first_line.lstrip("#").strip()
        parts = [p.strip() for p in clean.split("|")]
        desc = parts[1] if len(parts) >= 2 else clean
        skills.append({"name": path.stem, "file": path.name, "desc": desc, "path": path})
    return skills


def save_skill(name: str, description: str, code: str, ext: str = ".ps1") -> pathlib.Path:
    SKILLS_DIR.mkdir(exist_ok=True)
    date_str = datetime.date.today().isoformat()
    # Intestazione obbligatoria: nome | descrizione | data
    header = f"# {name} | {description} | {date_str}\n"
    path = SKILLS_DIR / (name + ext)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(header + code)
    return path


def skill_has_destructive(path: pathlib.Path) -> bool:
    """Restituisce True se il file della skill contiene righe distruttive."""
    with io.open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            # Ignora righe vuote e commenti
            if stripped and not stripped.startswith("#") and is_destructive(stripped):
                return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# ESECUZIONE POWERSHELL
# ─────────────────────────────────────────────────────────────────────────────
def run_powershell(command: str) -> tuple[str, str, int]:
    """Esegue un comando PowerShell e ritorna (stdout, stderr, returncode).
    Dopo CMD_TIMEOUT secondi killa il processo e ritorna rc=-1."""
    proc = subprocess.Popen(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        stdout, stderr = proc.communicate(timeout=CMD_TIMEOUT)
        return stdout, stderr, proc.returncode
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        timeout_msg = f"[TIMEOUT] Processo killato dopo {CMD_TIMEOUT}s.\n"
        return (stdout or ""), timeout_msg + (stderr or ""), -1


# ─────────────────────────────────────────────────────────────────────────────
# LOG
# ─────────────────────────────────────────────────────────────────────────────
def log_command(command: str, returncode: int, destructive: bool, confirmed: bool | None) -> None:
    ts       = datetime.datetime.now().isoformat(timespec="seconds")
    conf_str = "n/a" if confirmed is None else ("sì" if confirmed else "no")
    entry = (
        f"[{ts}] RC={returncode} "
        f"DISTRUTTIVO={'sì' if destructive else 'no'} "
        f"CONFERMATO={conf_str} "
        f"CMD={command!r}\n"
    )
    with io.open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
Sei un agente AI autonomo che opera su Windows 10/11 con PowerShell.
Raggiungi l'obiettivo dell'utente eseguendo comandi PowerShell uno alla volta.

Rispondi SEMPRE con un oggetto JSON valido e nient'altro (nessun testo prima o dopo).
Usa ESATTAMENTE uno dei seguenti formati per risposta:

Eseguire un comando PowerShell:
{"type":"command","cmd":"<comando PS>","reason":"<motivazione breve>"}

Salvare una nuova skill riutilizzabile:
{"type":"save_skill","name":"<nome_senza_estensione>","ext":".ps1","description":"<descrizione>","code":"<codice>"}

Eseguire una skill già salvata:
{"type":"run_skill","name":"<nome_senza_estensione>","reason":"<motivazione>"}

Inviare un messaggio o fare una domanda all'utente:
{"type":"message","text":"<testo>"}

Dichiarare l'obiettivo completato:
{"type":"done","summary":"<riepilogo di cosa è stato fatto>"}

CAMPO OPZIONALE: aggiungi "memory_update":{"chiave":"valore",...} in qualsiasi risposta
per salvare fatti o preferenze da ricordare nelle sessioni future.

VINCOLI ASSOLUTI:
- Non modificare mai il file agente.py.
- Una sola azione per risposta.
- Preferisci skill esistenti se applicabili.
- Usa l'escaping corretto per caratteri speciali PowerShell nelle stringhe.
- Se non sei sicuro dell'effetto di un'azione, scegli l'alternativa più conservativa.
"""


# ─────────────────────────────────────────────────────────────────────────────
# PARSING RISPOSTA DEL MODELLO
# ─────────────────────────────────────────────────────────────────────────────
def parse_response(raw: str) -> dict:
    """Estrae il JSON dalla risposta del modello, gestisce eventuali code block markdown."""
    cleaned = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Ultima risorsa: cerca il primo oggetto JSON nel testo
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise


# ─────────────────────────────────────────────────────────────────────────────
# RICHIESTA CONFERMA
# ─────────────────────────────────────────────────────────────────────────────
def ask_confirm(prompt: str) -> str:
    """Chiede conferma interattiva. Restituisce 's', 'n', o 'stop'."""
    while True:
        ans = input(prompt).strip().lower()
        if ans in ("s", "n", "stop"):
            return ans
        print("  Risposta non valida — digita s, n, o stop.")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    # Verifica chiave API — mai in chiaro nel codice
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERRORE: variabile d'ambiente ANTHROPIC_API_KEY non impostata. Uscita.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Carica memoria e skill all'avvio
    memory = load_memory()
    skills = list_skills()

    # ── Banner di avvio ───────────────────────────────────────────────────────
    sep = "=" * 64
    print(f"\n{sep}")
    print(f"  Agente AI autonomo   |   Modello: {MODEL}")
    print(sep)
    print("  AVVISO: l'agente esegue i comandi da solo senza chiedere.")
    print("  Solo i comandi DISTRUTTIVI richiedono la tua conferma [s/n].")
    print("  Scrivi 'stop' in qualsiasi momento per uscire.")
    print(f"{sep}\n")

    if memory:
        print("Fatti in memoria:")
        for k, v in memory.items():
            print(f"  {k}: {v}")
    else:
        print("Memoria: vuota.")
    print()

    if skills:
        print("Skill disponibili:")
        for s in skills:
            print(f"  [{s['name']}]  {s['desc']}")
    else:
        print("Skill: nessuna.")
    print()

    # ── Obiettivo iniziale ────────────────────────────────────────────────────
    print("Obiettivo: ", end="", flush=True)
    objective = input().strip()
    if objective.lower() == "stop" or not objective:
        print("Uscita.")
        return

    # Contesto iniziale per il modello (memoria + skill)
    context_parts: list[str] = []
    if memory:
        context_parts.append(
            "MEMORIA CORRENTE:\n" + json.dumps(memory, ensure_ascii=False, indent=2)
        )
    if skills:
        lines = [f"- {s['name']}: {s['desc']}" for s in skills]
        context_parts.append("SKILL DISPONIBILI:\n" + "\n".join(lines))

    first_msg = ("\n\n".join(context_parts) + "\n\n" if context_parts else "") + f"OBIETTIVO: {objective}"

    # Cronologia della conversazione
    history: list[dict] = [{"role": "user", "content": first_msg}]

    # ── Loop principale ───────────────────────────────────────────────────────
    while True:
        # Chiamata al modello
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        raw_text = response.content[0].text.strip()
        history.append({"role": "assistant", "content": raw_text})

        # Parsing JSON
        try:
            action = parse_response(raw_text)
        except (json.JSONDecodeError, ValueError):
            print(f"[ERRORE] Risposta non JSON valido:\n{raw_text}")
            history.append({
                "role": "user",
                "content": "ERRORE: la risposta non è JSON valido. Riprova con il formato corretto.",
            })
            continue

        # Aggiornamento memoria opzionale (presente in qualsiasi tipo di azione)
        if isinstance(action.get("memory_update"), dict):
            memory.update(action["memory_update"])
            save_memory(memory)
            print(f"[MEMORIA] Aggiornata: {action['memory_update']}")

        action_type = action.get("type", "")

        # ── command ────────────────────────────────────────────────────────────
        if action_type == "command":
            cmd    = action.get("cmd", "").strip()
            reason = action.get("reason", "")

            # Vincolo di stabilità: l'agente non modifica se stesso
            if OWN_FILE.name in cmd or str(OWN_FILE) in cmd:
                msg = f"[SICUREZZA] Rifiutato: il comando fa riferimento a {OWN_FILE.name}."
                print(msg)
                history.append({"role": "user", "content": msg})
                continue

            destr     = is_destructive(cmd)
            confirmed: bool | None = None  # None = eseguito senza conferma

            print(f"\n{'─'*64}")
            print(f"COMANDO : {cmd}")
            print(f"Motivo  : {reason}")
            if destr:
                print("TIPO    : [DISTRUTTIVO — richiede conferma]")
            print(f"{'─'*64}")

            if destr:
                ans = ask_confirm("Eseguire? [s/n/stop]: ")
                if ans == "stop":
                    print("Sessione terminata.")
                    return
                if ans == "n":
                    confirmed = False
                    log_command(cmd, -1, True, False)
                    msg = "Comando saltato dall'utente."
                    print(msg)
                    history.append({"role": "user", "content": msg})
                    continue
                confirmed = True

            stdout, stderr, rc = run_powershell(cmd)
            log_command(cmd, rc, destr, confirmed)

            print(f"Return code : {rc}")
            if stdout.strip():
                print("STDOUT:\n" + stdout)
            if stderr.strip():
                print("STDERR:\n" + stderr)

            result = f"Comando eseguito. RC={rc}"
            if stdout.strip():
                result += f"\nSTDOUT:\n{stdout}"
            if stderr.strip():
                result += f"\nSTDERR:\n{stderr}"
            history.append({"role": "user", "content": result})

        # ── save_skill ─────────────────────────────────────────────────────────
        elif action_type == "save_skill":
            name = action.get("name", "skill").strip()
            ext  = action.get("ext", ".ps1")
            desc = action.get("description", "")
            code = action.get("code", "")

            path = save_skill(name, desc, code, ext)
            skills = list_skills()  # aggiorna lista in-memory
            msg = f"Skill '{name}' salvata in {path}."
            print(f"\n[SKILL] {msg}")
            history.append({"role": "user", "content": msg})

        # ── run_skill ──────────────────────────────────────────────────────────
        elif action_type == "run_skill":
            name   = action.get("name", "").strip()
            reason = action.get("reason", "")

            # Cerca il file skill (.ps1 o .py)
            skill_path: pathlib.Path | None = None
            for ext in (".ps1", ".py"):
                candidate = SKILLS_DIR / (name + ext)
                if candidate.exists():
                    skill_path = candidate
                    break

            if skill_path is None:
                msg = f"ERRORE: skill '{name}' non trovata in {SKILLS_DIR}/."
                print(f"[SKILL] {msg}")
                history.append({"role": "user", "content": msg})
                continue

            print(f"\n{'─'*64}")
            print(f"SKILL  : {skill_path.name}")
            print(f"Motivo : {reason}")
            print(f"{'─'*64}")

            has_destr = skill_has_destructive(skill_path)
            confirmed_skill: bool | None = None

            if has_destr:
                print("TIPO   : [SKILL CON COMANDI DISTRUTTIVI — richiede conferma]")
                ans = ask_confirm("Eseguire la skill? [s/n/stop]: ")
                if ans == "stop":
                    print("Sessione terminata.")
                    return
                if ans == "n":
                    msg = f"Skill '{name}' saltata dall'utente."
                    print(msg)
                    log_command(f"[SKILL:{name}]", -1, True, False)
                    history.append({"role": "user", "content": msg})
                    continue
                confirmed_skill = True

            if skill_path.suffix == ".ps1":
                stdout, stderr, rc = run_powershell(f"& '{skill_path}'")
            else:  # .py
                proc = subprocess.Popen(
                    [sys.executable, str(skill_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                try:
                    stdout, stderr = proc.communicate(timeout=CMD_TIMEOUT)
                    rc = proc.returncode
                except subprocess.TimeoutExpired:
                    proc.kill()
                    stdout, stderr = proc.communicate()
                    stderr = f"[TIMEOUT] Killato dopo {CMD_TIMEOUT}s.\n" + (stderr or "")
                    rc = -1

            log_command(f"[SKILL:{name}]", rc, has_destr, confirmed_skill)

            print(f"Return code : {rc}")
            if stdout.strip():
                print("STDOUT:\n" + stdout)
            if stderr.strip():
                print("STDERR:\n" + stderr)

            result = f"Skill '{name}' eseguita. RC={rc}"
            if stdout.strip():
                result += f"\nSTDOUT:\n{stdout}"
            if stderr.strip():
                result += f"\nSTDERR:\n{stderr}"
            history.append({"role": "user", "content": result})

        # ── message ────────────────────────────────────────────────────────────
        elif action_type == "message":
            text = action.get("text", "")
            print(f"\n[AGENTE] {text}")
            print("\nRisposta (o 'stop'): ", end="", flush=True)
            user_input = input().strip()
            if user_input.lower() == "stop":
                print("Sessione terminata.")
                return
            history.append({"role": "user", "content": user_input or "(nessuna risposta)"})

        # ── done ───────────────────────────────────────────────────────────────
        elif action_type == "done":
            summary = action.get("summary", "Obiettivo raggiunto.")
            print(f"\n{'='*64}")
            print("OBIETTIVO RAGGIUNTO")
            print(summary)
            print(f"{'='*64}")

            print("\nNuovo obiettivo? (o 'stop' per uscire): ", end="", flush=True)
            user_input = input().strip()
            if user_input.lower() == "stop" or not user_input:
                print("Sessione terminata.")
                return

            history.append({"role": "user", "content": f"NUOVO OBIETTIVO: {user_input}"})

        # ── tipo sconosciuto ───────────────────────────────────────────────────
        else:
            msg = (
                f"ERRORE: tipo azione '{action_type}' non riconosciuto. "
                "Usa solo: command, save_skill, run_skill, message, done."
            )
            print(f"[WARN] {msg}")
            history.append({"role": "user", "content": msg})


if __name__ == "__main__":
    main()
