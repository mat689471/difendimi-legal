"""Demo eseguibile: strategia trend-filtrata su RSI, in modalita' PAPER, con
stop-loss / take-profit e dimensionamento basato sul rischio.

Mostra l'intero giro di un trading serio ma senza un euro reale:
  segnale -> sizing sul rischio -> risk check -> esecuzione simulata
  -> SL/TP che chiudono in automatico -> P&L. Tutto nell'audit log.

    python -m jarvis.trading

Regola i parametri in cima. Nota: e' una DEMO didattica, non una strategia da
mettere su soldi veri cosi' com'e'.
"""

from __future__ import annotations

import math
from pathlib import Path

from ..core import AuditLog, KillSwitch
from .broker import Order, PaperBroker
from .engine import TradingEngine
from .risk import RiskConfig, RiskManager, size_for_risk
from .strategy import TrendRsi

ROOT = Path(__file__).resolve().parent

SYMBOL = "EURUSD"
POINT_VALUE = 10.0
RISK_PCT = 0.01     # rischio 1% del conto per operazione
SL_DIST = 2.5       # distanza stop-loss (unita' di prezzo)
TP_DIST = 5.0       # distanza take-profit (2 R)


def synthetic_prices(n: int = 220) -> list[float]:
    """Trend rialzista con pullback: sono le condizioni in cui una strategia
    trend-following ha senso. Su un mercato senza direzione verrebbe stoppata,
    ed e' giusto cosi' — il risultato dipende SEMPRE dalle condizioni di mercato."""
    return [100 + i * 0.35 + 5 * math.sin(i / 7) for i in range(n)]


def main() -> int:
    audit = AuditLog(ROOT.parent / "logs" / "trading.jsonl")
    killswitch = KillSwitch(str(ROOT.parent / "logs" / "STOP"))
    broker = PaperBroker(starting_balance=10_000)
    broker.set_point_value(SYMBOL, POINT_VALUE)
    risk = RiskManager(RiskConfig(
        mode="paper", allowed_symbols=[SYMBOL],
        max_open_positions=1, max_volume_per_order=1.0, max_total_volume=1.0,
        max_daily_loss=1_000,
    ))
    engine = TradingEngine(broker, risk, audit, killswitch)
    strat = TrendRsi(trend=30, period=14, oversold=35, overbought=65)

    open_id: int | None = None

    print(f"{'prezzo':>8}  {'segnale':7}  azione")
    for price in synthetic_prices():
        # 1. fai scorrere il mercato: SL/TP chiudono da soli
        for pos_id, why in engine.update_market(SYMBOL, price):
            if pos_id == open_id:
                print(f"{price:8.2f}  {why.upper():7}  chiusa #{pos_id} ({why})")
                open_id = None

        # 2. nuovo segnale (solo se siamo flat)
        sig = strat.signal(price)
        if sig in ("buy", "sell") and open_id is None:
            if sig == "buy":
                sl, tp = price - SL_DIST, price + TP_DIST
            else:
                sl, tp = price + SL_DIST, price - TP_DIST
            volume = size_for_risk(broker.balance, RISK_PCT, price, sl, POINT_VALUE,
                                   max_volume=risk.config.max_volume_per_order)
            pos = engine.place_order(Order(SYMBOL, sig, volume, price=price, sl=sl, tp=tp))
            if pos:
                open_id = pos.id
                print(f"{price:8.2f}  {sig:7}  apro #{pos.id} vol {volume:.2f} "
                      f"SL {sl:.1f} TP {tp:.1f}")

    if open_id is not None:
        engine.close_position(open_id)

    snap = engine.snapshot()
    print("\n--- risultato (PAPER) ---")
    print(f"  strategia: TrendRsi | rischio/op: {RISK_PCT:.0%} | SL {SL_DIST} / TP {TP_DIST}")
    print(f"  equity finale: {snap['equity']:.2f} (iniziale 10000.00)")
    print(f"  P&L realizzato: {snap['realized_today']:+.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
