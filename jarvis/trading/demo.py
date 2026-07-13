"""Demo eseguibile: strategia SMA su prezzi sintetici, in modalita' PAPER.

Mostra l'intero giro — segnale -> risk check -> esecuzione simulata -> P&L —
senza toccare un solo euro reale. Ogni ordine finisce nell'audit log.

    python -m jarvis.trading        # esegue questa demo
"""

from __future__ import annotations

import math
from pathlib import Path

from ..core import AuditLog, KillSwitch
from .broker import Order, PaperBroker
from .engine import TradingEngine
from .risk import RiskConfig, RiskManager
from .strategy import SmaCrossover

ROOT = Path(__file__).resolve().parent


def synthetic_prices(n: int = 120) -> list[float]:
    """Onda + deriva: abbastanza per far scattare qualche crossover."""
    return [100 + 5 * math.sin(i / 8) + i * 0.05 for i in range(n)]


def main() -> int:
    audit = AuditLog(ROOT.parent / "logs" / "trading.jsonl")
    killswitch = KillSwitch(str(ROOT.parent / "logs" / "STOP"))
    broker = PaperBroker(starting_balance=10_000)
    risk = RiskManager(RiskConfig(mode="paper", allowed_symbols=["EURUSD"], max_open_positions=1))
    engine = TradingEngine(broker, risk, audit, killswitch)
    strat = SmaCrossover(fast=5, slow=20)

    symbol = "EURUSD"
    broker.set_point_value(symbol, 10.0)
    open_pos = None

    print(f"{'prezzo':>8}  segnale  azione")
    for price in synthetic_prices():
        broker.mark(symbol, price)
        sig = strat.signal(price)
        if sig in ("buy", "sell"):
            if open_pos is not None:
                pnl = engine.close_position(open_pos.id, price)
                print(f"{price:8.2f}  {sig:7}  chiudo #{open_pos.id}  P&L {pnl:+.2f}")
                open_pos = None
            open_pos = engine.place_order(Order(symbol, sig, 0.10, price=price))
            if open_pos:
                print(f"{price:8.2f}  {sig:7}  apro   #{open_pos.id} @ {price:.2f}")

    if open_pos:
        engine.close_position(open_pos.id)

    snap = engine.snapshot()
    print("\n--- risultato (PAPER) ---")
    print(f"  modalita': {snap['mode']}")
    print(f"  equity finale: {snap['equity']:.2f} (iniziale 10000.00)")
    print(f"  P&L realizzato: {snap['realized_today']:+.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
