"""Registro di audit append-only: la "scatola nera" di Jarvis.

Ogni azione (comando, esito, rischio, decisione) viene scritta su un file
JSONL append-only. Serve a ricostruire *cosa* Jarvis ha fatto e *perche'*,
anche a posteriori. E' il presupposto del principio "log + stop".
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


class AuditLog:
    def __init__(self, path: str | os.PathLike[str]):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: str, **fields: Any) -> dict[str, Any]:
        entry = {
            "ts": time.time(),
            "iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            "event": event,
            **fields,
        }
        # append-only: apriamo sempre in modalita' 'a', mai sovrascrivere.
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def tail(self, n: int = 20) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines[-n:] if line.strip()]
