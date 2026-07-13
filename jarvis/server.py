"""Ponte HTTP locale tra l'interfaccia (voce/UI) e il modulo di automazione.

IMPORTANTE — sicurezza:
  * il server si lega SOLO a 127.0.0.1 (localhost). Non e' esposto in rete.
  * le operazioni CATASTROFICHE sono negate via HTTP: per quelle serve la
    conferma esplicita da terminale. Un pulsante web non deve poter
    formattare un disco. Il resto (incluso sudo) gira in autonomia, come da
    configurazione.

Nessuna dipendenza esterna: solo la standard library.
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from jarvis.agent import Jarvis  # noqa: E402

UI_DIR = ROOT / "ui"

# Via HTTP le operazioni catastrofiche vengono sempre negate.
_DENY = lambda command, reason: False  # noqa: E731
_jarvis = Jarvis.from_config(str(ROOT / "config.yaml"), confirmer=_DENY)


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

    def _static(self, rel: str):
        # normalizza ed evita path traversal fuori da ui/
        target = (UI_DIR / rel.lstrip("/")).resolve()
        if not str(target).startswith(str(UI_DIR)) or not target.is_file():
            self.send_error(404, "non trovato")
            return
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
        }.get(target.suffix, "application/octet-stream")
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):  # silenzia il logging su stderr
        pass

    # --- routing ---------------------------------------------------------
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._static("index.html")
        if self.path.startswith("/api/status"):
            return self._json({
                "stopped": _jarvis.killswitch.is_engaged(),
                "reason": _jarvis.killswitch.reason(),
                "autonomy": _jarvis.executor.autonomy,
            })
        if self.path.startswith("/api/log"):
            return self._json({"entries": _jarvis.audit.tail(30)})
        if self.path.startswith("/api/"):
            return self._json({"error": "endpoint sconosciuto"}, 404)
        return self._static(self.path)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "JSON non valido"}, 400)

        if self.path == "/api/run":
            command = (data.get("command") or "").strip()
            if not command:
                return self._json({"error": "comando mancante"}, 400)
            r = _jarvis.executor.run(command)
            return self._json({
                "command": r.command, "executed": r.executed, "exit_code": r.exit_code,
                "stdout": r.stdout, "stderr": r.stderr, "risk": r.risk, "note": r.note,
            })
        if self.path == "/api/stop":
            _jarvis.killswitch.engage("stop dall'interfaccia")
            return self._json({"stopped": True})
        if self.path == "/api/start":
            _jarvis.killswitch.disengage()
            return self._json({"stopped": False})
        return self._json({"error": "endpoint sconosciuto"}, 404)


def main(host: str = "127.0.0.1", port: int = 8787):
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Jarvis in ascolto su http://{host}:{port}  (solo locale)")
    print("Apri quell'indirizzo nel browser. Ctrl+C per fermare.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nJarvis: arresto del server.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    main(port=p)
