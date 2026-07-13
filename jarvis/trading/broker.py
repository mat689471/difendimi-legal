"""Astrazione del broker + broker simulato (paper).

Il resto del modulo non sa se dietro c'e' un conto simulato, un conto demo
reale o (un giorno) un conto live: parla solo con l'interfaccia Broker. Cosi'
si prova tutto in sicurezza col PaperBroker, e si passa al reale cambiando
implementazione, non logica.

NB: il modello di P&L del PaperBroker e' volutamente semplice
(pnl = (prezzo - ingresso) * volume * point_value). Serve a esercitare risk
manager ed engine, non a replicare la contabilita' esatta di un broker.
"""

from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Order:
    symbol: str
    side: str          # "buy" | "sell"
    volume: float      # lotti
    price: float | None = None  # per il paper: prezzo di fill


@dataclass
class Position:
    id: int
    symbol: str
    side: str
    volume: float
    entry_price: float
    current_price: float
    point_value: float = 1.0

    @property
    def unrealized_pnl(self) -> float:
        direction = 1 if self.side == "buy" else -1
        return (self.current_price - self.entry_price) * direction * self.volume * self.point_value


class Broker(ABC):
    @abstractmethod
    def open(self, order: Order) -> Position: ...

    @abstractmethod
    def close(self, position_id: int, price: float | None = None) -> float:
        """Chiude una posizione e ritorna il P&L realizzato."""

    @abstractmethod
    def positions(self) -> list[Position]: ...

    @abstractmethod
    def equity(self) -> float: ...


class PaperBroker(Broker):
    """Broker simulato, deterministico, adatto ai test e alla modalita' paper."""

    def __init__(self, starting_balance: float = 10_000.0):
        self.balance = starting_balance
        self._positions: dict[int, Position] = {}
        self._ids = itertools.count(1)
        self._point_values: dict[str, float] = {}

    def set_point_value(self, symbol: str, value: float) -> None:
        self._point_values[symbol] = value

    def open(self, order: Order) -> Position:
        if order.price is None:
            raise ValueError("PaperBroker richiede un prezzo di fill nell'ordine")
        pos = Position(
            id=next(self._ids),
            symbol=order.symbol,
            side=order.side,
            volume=order.volume,
            entry_price=order.price,
            current_price=order.price,
            point_value=self._point_values.get(order.symbol, 1.0),
        )
        self._positions[pos.id] = pos
        return pos

    def mark(self, symbol: str, price: float) -> None:
        """Aggiorna il prezzo corrente delle posizioni su un simbolo."""
        for pos in self._positions.values():
            if pos.symbol == symbol:
                pos.current_price = price

    def close(self, position_id: int, price: float | None = None) -> float:
        pos = self._positions.pop(position_id)
        if price is not None:
            pos.current_price = price
        pnl = pos.unrealized_pnl
        self.balance += pnl
        return pnl

    def positions(self) -> list[Position]:
        return list(self._positions.values())

    def equity(self) -> float:
        return self.balance + sum(p.unrealized_pnl for p in self._positions.values())
