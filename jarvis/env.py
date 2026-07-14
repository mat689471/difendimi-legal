"""Carica i segreti da un file `.env` locale (senza dipendenze esterne).

Cosi' NON devi mettere le chiavi nel codice né litigare con le variabili
d'ambiente del terminale: le scrivi in `jarvis/.env` (che è escluso da Git) e
Jarvis le legge all'avvio.

Formato del file (una riga per chiave):
    ANTHROPIC_API_KEY=sk-ant-...
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_ENV = Path(__file__).resolve().parent / ".env"


def load_env(path: str | os.PathLike[str] = DEFAULT_ENV, *, override: bool = False) -> list[str]:
    """Legge le coppie CHIAVE=VALORE dal file e le mette in os.environ.
    Non sovrascrive chiavi gia' presenti (salvo override=True). Ritorna i nomi
    delle chiavi caricate. Se il file non esiste, non fa nulla."""
    p = Path(path)
    if not p.exists():
        return []
    caricate: list[str] = []
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and (override or key not in os.environ):
            os.environ[key] = value
            caricate.append(key)
    return caricate
