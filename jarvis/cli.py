"""Interfaccia a riga di comando per il modulo di automazione di sistema.

Esempi:
    python -m jarvis.cli run "df -h" "free -m"
    python -m jarvis.cli plan piano.txt
    python -m jarvis.cli stop
    python -m jarvis.cli start
    python -m jarvis.cli log
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# consente sia `python -m jarvis.cli` sia `python jarvis/cli.py`
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from jarvis.agent import Jarvis, load_config
    from jarvis.core import AuditLog, KillSwitch
else:
    from .agent import Jarvis, load_config
    from .core import AuditLog, KillSwitch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jarvis", description="Jarvis - automazione di sistema")
    parser.add_argument("--config", default="jarvis/config.yaml")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="esegue uno o piu' comandi")
    p_run.add_argument("commands", nargs="+")

    p_plan = sub.add_parser("plan", help="esegue i comandi elencati in un file (uno per riga)")
    p_plan.add_argument("file")

    sub.add_parser("stop", help="arma il kill switch (Jarvis si ferma)")
    sub.add_parser("start", help="disarma il kill switch (Jarvis riparte)")
    sub.add_parser("status", help="stato del kill switch")

    p_log = sub.add_parser("log", help="mostra le ultime voci del registro di audit")
    p_log.add_argument("-n", type=int, default=20)

    args = parser.parse_args(argv)

    # comandi che non richiedono l'inizializzazione completa dell'agente
    # (ma usano gli STESSI percorsi del config, cosi' stop/log agiscono sui
    #  file davvero usati dall'agente)
    if args.cmd in ("stop", "start", "status", "log"):
        cfg = load_config(args.config)
        ks = KillSwitch(cfg["stop_sentinel"])
        if args.cmd == "stop":
            ks.engage("stop manuale via CLI")
            print("⏹ Kill switch ARMATO. Jarvis non eseguira' nuove azioni.")
        elif args.cmd == "start":
            ks.disengage()
            print("▶ Kill switch disarmato. Jarvis puo' operare.")
        elif args.cmd == "status":
            print(f"Kill switch armato: {ks.is_engaged()} ({ks.reason() or 'operativo'})")
        elif args.cmd == "log":
            for entry in AuditLog(cfg["audit_path"]).tail(args.n):
                print(f"{entry.get('iso')}  {entry.get('event'):16}  "
                      f"[{entry.get('risk', '-')}]  {entry.get('command', entry.get('note', ''))}")
        return 0

    jarvis = Jarvis.from_config(args.config)

    if args.cmd == "run":
        jarvis.execute_plan(args.commands)
    elif args.cmd == "plan":
        lines = [ln.strip() for ln in Path(args.file).read_text(encoding="utf-8").splitlines()]
        commands = [ln for ln in lines if ln and not ln.startswith("#")]
        jarvis.execute_plan(commands)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
