"""Ponte HTTP locale tra l'interfaccia (voce/UI) e il modulo di automazione.

SICUREZZA — Jarvis risponde SOLO a te:
  * si lega SOLO a 127.0.0.1 (localhost): non e' esposto in rete;
  * ogni chiamata richiede il TUO token segreto. Il token viene generato alla
    prima esecuzione e stampato nel terminale come parte dell'URL. Solo chi ha
    quel token (tu, dal terminale) puo' aprire l'interfaccia e dare comandi;
  * controlla l'header Host per bloccare gli attacchi di DNS-rebinding
    (un sito malevolo che prova a comandare Jarvis dal tuo browser);
  * le operazioni CATASTROFICHE restano negate via HTTP: per quelle serve la
    conferma esplicita da terminale.

Nessuna dipendenza esterna: solo la standard library.
"""

from __future__ import annotations

import json
import secrets
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from jarvis.agent import Jarvis  # noqa: E402
from jarvis.brain import Brain  # noqa: E402
from jarvis.guardian import Guardian  # noqa: E402

UI_DIR = ROOT / "ui"
TOKEN_FILE = ROOT / "logs" / "owner.token"
ALLOWED_HOSTS = {"127.0.0.1", "localhost"}

# Via HTTP le operazioni catastrofiche vengono sempre negate.
_DENY = lambda command, reason: False  # noqa: E731
_jarvis = Jarvis.from_config(str(ROOT / "config.yaml"), confirmer=_DENY)
# Il Cervello: capisce il linguaggio naturale e coordina i moduli.
_brain = Brain(jarvis=_jarvis, guardian=Guardian())


def _load_or_create_token() -> str:
    """Il segreto che rende Jarvis tuo. Persistente tra i riavvii, solo-lettura owner."""
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    if TOKEN_FILE.exists():
        tok = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if tok:
            return tok
    tok = secrets.token_urlsafe(24)
    TOKEN_FILE.write_text(tok, encoding="utf-8")
    try:
        TOKEN_FILE.chmod(0o600)  # leggibile solo dal tuo utente di sistema
    except OSError:
        pass
    return tok


OWNER_TOKEN = _load_or_create_token()


class Handler(BaseHTTPRequestHandler):
    server_version = "Jarvis/0.1"

    # --- utility ---------------------------------------------------------
    def _json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ALLOWED_HOSTS

    def _query_token(self) -> str:
        if "?" not in self.path:
            return ""
        query = self.path.split("?", 1)[1]
        for part in query.split("&"):
            if part.startswith("k="):
                return part[2:]
        return ""

    def _bare_path(self) -> str:
        return self.path.split("?", 1)[0]

    def _serve_static(self, rel: str):
        target = (UI_DIR / rel.lstrip("/")).resolve()
        if not str(target).startswith(str(UI_DIR)) or not target.is_file():
            self.send_error(404, "non trovato")
            return
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".mp3": "audio/mpeg",
        }.get(target.suffix, "application/octet-stream")
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass

    # --- routing ---------------------------------------------------------
    def do_GET(self):
        if not self._host_ok():
            return self._json({"error": "host non consentito"}, 403)
        bare = self._bare_path()

        if bare in ("/", "/index.html"):
            # la pagina si apre solo con il token corretto nell'URL (?k=...)
            if not secrets.compare_digest(self._query_token(), OWNER_TOKEN):
                return self._json({"error": "Non autorizzato. Apri Jarvis con l'URL mostrato nel terminale."}, 401)
            return self._serve_static("index.html")

        if bare.startswith("/api/"):
            if not self._authorized():
                return self._json({"error": "Non autorizzato"}, 401)
            if bare.startswith("/api/status"):
                return self._json({
                    "stopped": _jarvis.killswitch.is_engaged(),
                    "reason": _jarvis.killswitch.reason(),
                    "autonomy": _jarvis.executor.autonomy,
                })
            if bare.startswith("/api/log"):
                return self._json({"entries": _jarvis.audit.tail(30)})
            return self._json({"error": "endpoint sconosciuto"}, 404)

        # asset statici (js/css/mp3): non contengono segreti, nessun token
        return self._serve_static(bare)

    def do_POST(self):
        if not self._host_ok():
            return self._json({"error": "host non consentito"}, 403)
        if not self._authorized():
            return self._json({"error": "Non autorizzato"}, 401)

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "JSON non valido"}, 400)

        bare = self._bare_path()
        if bare == "/api/say":
            # linguaggio naturale -> Cervello (capisce l'intento e coordina)
            message = (data.get("message") or "").strip()
            if not message:
                return self._json({"error": "messaggio mancante"}, 400)
            reply = _brain.handle(message)
            return self._json({
                "text": reply.text, "intent": reply.intent,
                "advisories": [{"level": a.level, "key": a.key, "message": a.message}
                               for a in reply.advisories],
                "data": reply.data,
            })
        if bare == "/api/run":
            command = (data.get("command") or "").strip()
            if not command:
                return self._json({"error": "comando mancante"}, 400)
            r = _jarvis.executor.run(command)
            return self._json({
                "command": r.command, "executed": r.executed, "exit_code": r.exit_code,
                "stdout": r.stdout, "stderr": r.stderr, "risk": r.risk, "note": r.note,
            })
        if bare == "/api/stop":
            _jarvis.killswitch.engage("stop dall'interfaccia")
            return self._json({"stopped": True})
        if bare == "/api/start":
            _jarvis.killswitch.disengage()
            return self._json({"stopped": False})
        return self._json({"error": "endpoint sconosciuto"}, 404)

    def _authorized(self) -> bool:
        """Le chiamate API richiedono il token nell'header X-Jarvis-Token.
        L'header custom impedisce anche le richieste cross-site dal browser
        (nessun CORS impostato -> il browser blocca il preflight)."""
        provided = self.headers.get("X-Jarvis-Token", "")
        return bool(provided) and secrets.compare_digest(provided, OWNER_TOKEN)


def main(host: str = "127.0.0.1", port: int = 8787):
    from jarvis.env import load_env
    load_env()  # carica jarvis/.env se presente (chiavi API)
    httpd = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}/?k={OWNER_TOKEN}"
    print("=" * 68)
    print("  JARVIS — risponde solo a te.")
    print(f"  Apri QUESTO indirizzo nel browser (contiene il tuo token):\n")
    print(f"    {url}\n")
    print("  Chi non ha questo token non puo' comandare Jarvis. Ctrl+C per fermare.")
    print("=" * 68)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nJarvis: arresto del server.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    main(port=p)
