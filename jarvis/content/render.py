"""Render vero dei video: da props JSON a file .mp4.

Collega la pipeline a Remotion: costruisce il comando di render corretto
(entry, composizione, browser, GL software per i server headless) e lo esegue
sotto le regole di Jarvis — controlla il kill switch prima di partire e
registra inizio/fine nell'audit log.

Il render e' pesante (avvia un browser headless e codifica video): puo'
richiedere minuti per un video da 45s. Per questo NON passa dal timeout breve
dell'executor, ma ha un suo timeout generoso.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .pipeline import COMPOSITION_ID, REMOTION

ENTRY = "src/index.ts"


def find_browser() -> str | None:
    """Trova un browser utilizzabile per il render. Ordine:
    1) variabile JARVIS_BROWSER; 2) il Chrome Headless Shell pre-installato;
    3) None -> Remotion userà (o scaricherà) il proprio."""
    override = os.environ.get("JARVIS_BROWSER")
    if override and Path(override).exists():
        return override
    base = Path("/opt/pw-browsers")
    if base.exists():
        for pattern in ("chromium_headless_shell-*/chrome-linux/headless_shell",
                        "chromium-*/chrome-linux/chrome"):
            for p in sorted(base.glob(pattern)):
                if p.exists():
                    return str(p)
    return None


def render_command(props_path: str | os.PathLike[str], output_path: str | os.PathLike[str],
                   composition: str = COMPOSITION_ID) -> str:
    """Il comando di render, pronto da eseguire (anche a mano)."""
    browser = find_browser()
    parts = [
        f'cd "{REMOTION}"', "&&",
        "npx", "remotion", "render", ENTRY, composition,
        f'"{output_path}"', f'--props="{props_path}"',
        "--gl=swiftshader",  # rendering software: funziona su server senza GPU
    ]
    if browser:
        parts.append(f'--browser-executable="{browser}"')
    return " ".join(parts)


def render(props_path: str | os.PathLike[str], output_path: str | os.PathLike[str],
           *, killswitch=None, audit=None, timeout: int = 1800) -> bool:
    """Renderizza un video. Ritorna True se il file .mp4 e' stato creato.

    Rispetta il kill switch (non parte se e' armato) e registra nell'audit.
    """
    if killswitch is not None and killswitch.is_engaged():
        if audit:
            audit.record("render_blocked", output=str(output_path),
                         note=f"kill switch ({killswitch.reason()})")
        return False

    command = render_command(props_path, output_path)
    if audit:
        audit.record("render_started", output=str(output_path))
    try:
        proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        if audit:
            audit.record("render_timeout", output=str(output_path), note=f"oltre {timeout}s")
        return False

    ok = proc.returncode == 0 and Path(output_path).exists()
    if audit:
        audit.record("render_done" if ok else "render_failed", output=str(output_path),
                     exit_code=proc.returncode,
                     note="" if ok else (proc.stderr or "")[-500:])
    return ok
