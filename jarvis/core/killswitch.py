"""Kill switch: il freno d'emergenza di Jarvis.

Meccanismo principale: un file sentinella. Se il file esiste, Jarvis e'
"fermato" e non esegue nessuna nuova azione finche' non viene riarmato.
Puo' essere armato dalla CLI (`jarvis stop`), dall'interfaccia, o da un
altro terminale mentre Jarvis lavora.

Opzionale: la gestione di SIGINT/SIGTERM che arma il kill switch. E'
disattivata per default perche' altrimenti "cattura" il Ctrl+C anche a un
processo che vuole solo terminare (es. il server). Attivala con
`install_signals=True` solo dove vuoi che un segnale fermi l'agente.

Jarvis controlla `is_engaged()` PRIMA di ogni azione. Cosi' un "stop"
impedisce almeno tutte le azioni successive a quella gia' partita.
"""

from __future__ import annotations

import signal
from pathlib import Path


class KillSwitch:
    def __init__(self, sentinel_path: str = "jarvis/logs/STOP", install_signals: bool = False):
        self.sentinel = Path(sentinel_path)
        if install_signals:
            self._install_signal_handlers()

    def _install_signal_handlers(self) -> None:
        def _handler(signum, _frame):
            self.engage(reason=f"segnale {signal.Signals(signum).name}")
        try:
            signal.signal(signal.SIGINT, _handler)
            signal.signal(signal.SIGTERM, _handler)
        except ValueError:
            # succede se non siamo nel thread principale: non e' fatale.
            pass

    def engage(self, reason: str = "stop manuale") -> None:
        """Attiva il kill switch: Jarvis si ferma."""
        self.sentinel.parent.mkdir(parents=True, exist_ok=True)
        self.sentinel.write_text(reason, encoding="utf-8")

    def disengage(self) -> None:
        """Riarma Jarvis (rimuove il blocco)."""
        if self.sentinel.exists():
            self.sentinel.unlink()

    def is_engaged(self) -> bool:
        return self.sentinel.exists()

    def reason(self) -> str | None:
        if self.sentinel.exists():
            return self.sentinel.read_text(encoding="utf-8").strip()
        return None
