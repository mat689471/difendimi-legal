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


class Rsi:
    """Indicatore RSI (media semplice di guadagni/perdite sul periodo).
    Ritorna None finche' non ha dati sufficienti, poi un valore 0..100."""

    def __init__(self, period: int = 14):
        self.period = period
        self._prev: float | None = None
        self._gains: deque[float] = deque(maxlen=period)
        self._losses: deque[float] = deque(maxlen=period)

    def update(self, price: float) -> float | None:
        if self._prev is None:
            self._prev = price
            return None
        change = price - self._prev
        self._prev = price
        self._gains.append(max(change, 0.0))
        self._losses.append(max(-change, 0.0))
        if len(self._gains) < self.period:
            return None
        avg_gain = sum(self._gains) / self.period
        avg_loss = sum(self._losses) / self.period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - 100.0 / (1.0 + rs)


class RsiReversion(Strategy):
    """Mean-reversion su RSI: compra in ipervenduto, vende in ipercomprato.
    Emette un segnale solo all'ingresso nella zona, non a ogni tick."""

    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        self._rsi = Rsi(period)
        self.oversold = oversold
        self.overbought = overbought
        self._zone: str | None = None

    def signal(self, price: float) -> str:
        r = self._rsi.update(price)
        if r is None:
            return "flat"
        if r <= self.oversold:
            if self._zone != "os":
                self._zone = "os"
                return "buy"
        elif r >= self.overbought:
            if self._zone != "ob":
                self._zone = "ob"
                return "sell"
        else:
            self._zone = None  # tornato in zona neutra: si riarma
        return "flat"


class TrendRsi(Strategy):
    """Strategia filtrata dal trend: opera solo NEL verso del trend (prezzo vs
    SMA lenta) e usa l'RSI per l'ingresso in pullback. Piu' conservativa: niente
    controtendenza. Un buon default 'serio' rispetto al semplice crossover."""

    def __init__(self, trend: int = 50, period: int = 14,
                 oversold: float = 35, overbought: float = 65):
        self._slow: deque[float] = deque(maxlen=trend)
        self._rsi = Rsi(period)
        self.oversold = oversold
        self.overbought = overbought
        self._armed: str | None = None

    def signal(self, price: float) -> str:
        self._slow.append(price)
        r = self._rsi.update(price)
        if r is None or len(self._slow) < self._slow.maxlen:
            return "flat"
        sma = sum(self._slow) / len(self._slow)
        uptrend = price > sma
        if uptrend and r <= self.oversold and self._armed != "buy":
            self._armed = "buy"
            return "buy"
        if (not uptrend) and r >= self.overbought and self._armed != "sell":
            self._armed = "sell"
            return "sell"
        if self.oversold < r < self.overbought:
            self._armed = None  # rsi neutro: si riarma
        return "flat"
