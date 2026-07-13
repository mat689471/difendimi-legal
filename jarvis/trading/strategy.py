"""Strategie: producono segnali (buy/sell/flat) a partire dai prezzi.

Una strategia NON esegue ordini: propone soltanto. L'esecuzione, con tutti i
controlli di rischio, resta al TradingEngine. Cosi' una strategia sbagliata
non puo' comunque sforare i limiti hard.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque


class Strategy(ABC):
    @abstractmethod
    def signal(self, price: float) -> str:
        """Ritorna 'buy', 'sell' o 'flat' dato l'ultimo prezzo."""


class SmaCrossover(Strategy):
    """Incrocio di medie mobili: veloce sopra lenta -> buy, sotto -> sell."""

    def __init__(self, fast: int = 5, slow: int = 20):
        if fast >= slow:
            raise ValueError("la media veloce deve essere piu' corta della lenta")
        self.fast_window: deque[float] = deque(maxlen=fast)
        self.slow_window: deque[float] = deque(maxlen=slow)
        self._prev: str | None = None

    def signal(self, price: float) -> str:
        self.fast_window.append(price)
        self.slow_window.append(price)
        if len(self.slow_window) < self.slow_window.maxlen:
            return "flat"  # dati insufficienti
        fast = sum(self.fast_window) / len(self.fast_window)
        slow = sum(self.slow_window) / len(self.slow_window)
        state = "buy" if fast > slow else "sell"
        # emette il segnale solo al cambio di stato (sul crossover)
        if state != self._prev:
            self._prev = state
            return state
        return "flat"
