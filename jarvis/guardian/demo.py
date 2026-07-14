"""Demo del Guardiano: alcune scene, e come Jarvis reagisce.

    python -m jarvis.guardian
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .guardian import Guardian, GuardianConfig


def _say(title: str, advisories) -> None:
    print(f"\n▸ {title}")
    if not advisories:
        print("   (Jarvis tace: nulla da segnalare)")
    for a in advisories:
        icona = {"attenzione": "⚠️", "suggerimento": "💡", "info": "ℹ️"}.get(a.level, "•")
        print(f"   {icona} {a.message}")


def main() -> int:
    g = Guardian(GuardianConfig(session_break_minutes=120))

    # scena 1: comando innocuo, di giorno -> silenzio
    day = datetime(2026, 7, 14, 15, 0)
    _say("Ore 15:00 — comando ordinario", g.observe(risk="SAFE", now=day))

    # scena 2: azione irreversibile alle 3 di notte
    night = datetime(2026, 7, 14, 3, 0)
    _say("Ore 03:00 — stai per cancellare qualcosa senza ritorno",
         g.observe(risk="CATASTROPHIC", now=night))

    # scena 3: ordine di trading con soldi veri, di notte
    _say("Ore 03:05 — ordine live con denaro reale",
         g.observe(risk="ELEVATED", real_money=True, now=night + timedelta(minutes=5)))

    # scena 4: raffica di azioni in un minuto (l'avviso scatta appena superata
    # la soglia; lo raccogliamo)
    g2 = Guardian(GuardianConfig(rapid_count=5, rapid_window_sec=60))
    t = datetime(2026, 7, 14, 16, 0)
    raffica = []
    for i in range(6):
        raffica += g2.observe(risk="SAFE", now=t + timedelta(seconds=i * 5))
    _say("Sei azioni in mezzo minuto", raffica)

    # scena 5: sessione lunga
    g3 = Guardian(GuardianConfig(session_break_minutes=120))
    start = datetime(2026, 7, 14, 9, 0)
    g3.observe(risk="SAFE", now=start)
    _say("Al lavoro da oltre 2 ore",
         g3.observe(risk="SAFE", now=start + timedelta(hours=2, minutes=10)))

    print("\nIl Guardiano non blocca nulla: la decisione resta sempre tua.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
