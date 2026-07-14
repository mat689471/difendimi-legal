"""Attivazione di Jarvis.

    python -m jarvis            # accende Jarvis: controlli + interfaccia
    python -m jarvis --check    # solo diagnostica, non avvia il server

Un unico comando per accendere il tuo Jarvis: verifica che tutto sia a posto,
poi apre l'interfaccia (voce + volto) a cui parli in italiano. Da lì il
Cervello coordina i moduli — sistema, contenuti, stato — sotto le regole di
sicurezza (audit, kill switch, Guardiano, conferma sulle cose gravi).
"""

from __future__ import annotations

import importlib
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _check() -> list[str]:
    """Diagnostica di avvio. Ritorna la lista dei problemi bloccanti (vuota = ok)."""
    problemi: list[str] = []
    print("Controllo di sistema:")

    # dipendenza obbligatoria
    try:
        importlib.import_module("yaml")
        print("  ✓ PyYAML")
    except ImportError:
        print("  ✗ PyYAML mancante  →  pip install -r jarvis/requirements.txt")
        problemi.append("PyYAML")

    # moduli interni
    for mod in ("jarvis.core", "jarvis.brain", "jarvis.guardian", "jarvis.content"):
        try:
            importlib.import_module(mod)
            print(f"  ✓ {mod}")
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ {mod}: {exc}")
            problemi.append(mod)

    # opzionali (non bloccano)
    print("Opzionali:")
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("  ✓ ANTHROPIC_API_KEY rilevata (funzioni LLM attivabili)")
    else:
        print("  · ANTHROPIC_API_KEY assente — metti la chiave in jarvis/.env "
              "(vedi jarvis/.env.example)")
    node = shutil.which("node")
    print(f"  {'✓' if node else '·'} node {'(' + node + ')' if node else '— serve solo per il render video'}")
    remotion_ok = (ROOT.parent / "remotion" / "node_modules" / "remotion").exists()
    print(f"  {'✓' if remotion_ok else '·'} dipendenze Remotion "
          f"{'installate' if remotion_ok else '— `cd remotion && npm install` per il render'}")
    try:
        importlib.import_module("anthropic")
        print("  ✓ anthropic (pianificatore/idee LLM disponibili)")
    except ImportError:
        print("  · anthropic assente — pianificatore/idee LLM inattivi (opzionale)")

    return problemi


def main() -> int:
    print("=" * 60)
    print("  J.A.R.V.I.S.  —  attivazione")
    print("=" * 60)
    from jarvis.env import load_env
    caricate = load_env()
    if caricate:
        print(f"Segreti caricati da jarvis/.env: {', '.join(caricate)}\n")
    problemi = _check()
    if problemi:
        print(f"\n⚠️  Attivazione interrotta: risolvi prima {', '.join(problemi)}.")
        return 1
    print("\n✓ Tutto a posto.")

    if "--check" in sys.argv:
        return 0

    print("\nAccendo l'interfaccia di Jarvis…\n")
    from jarvis.server import main as server_main
    server_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
