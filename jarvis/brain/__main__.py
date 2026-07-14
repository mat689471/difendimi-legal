"""Parla con Jarvis dal terminale.

    python -m jarvis.brain                 # modalità conversazione
    python -m jarvis.brain "esegui df -h"  # singola istruzione

Il pianificatore LLM (per obiettivi complessi) si attiva da solo se trova
ANTHROPIC_API_KEY nell'ambiente e il pacchetto 'anthropic'.
"""

from __future__ import annotations

import sys

from .brain import Brain
from .planner import LlmPlanner


def _print(reply) -> None:
    for a in reply.advisories:
        icona = {"attenzione": "⚠️", "suggerimento": "💡", "info": "ℹ️"}.get(a.level, "•")
        print(f"  {icona} {a.message}")
    print(f"  Jarvis: {reply.text}")


def main() -> int:
    brain = Brain()
    llm = LlmPlanner()
    planner = llm if llm.available() else None
    if planner:
        print("(pianificatore LLM attivo: posso scomporre obiettivi complessi)")

    args = sys.argv[1:]
    if args:
        goal = " ".join(args)
        for reply in brain.plan_and_do(goal, planner=planner):
            _print(reply)
        return 0

    print("Jarvis: Sono a sua disposizione, signore. (scriva 'esci' per uscire)")
    while True:
        try:
            msg = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nJarvis: A presto, signore.")
            return 0
        if msg.lower() in ("esci", "exit", "quit", "basta"):
            print("Jarvis: A presto, signore.")
            return 0
        if not msg:
            continue
        for reply in brain.plan_and_do(msg, planner=planner):
            _print(reply)


if __name__ == "__main__":
    raise SystemExit(main())
