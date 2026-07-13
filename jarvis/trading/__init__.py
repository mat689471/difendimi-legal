"""Modulo trading di Jarvis: demo-first, limiti hard, umano sui soldi veri."""

from .broker import Broker, Order, PaperBroker, Position
from .engine import TradingEngine
from .risk import RiskConfig, RiskDecision, RiskManager
from .strategy import SmaCrossover, Strategy

__all__ = [
    "Broker", "Order", "PaperBroker", "Position",
    "TradingEngine", "RiskConfig", "RiskDecision", "RiskManager",
    "Strategy", "SmaCrossover",
]
