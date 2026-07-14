"""Motore di trading: unisce broker, risk manager, audit e kill switch.

Ogni ordine passa da qui:
  1. kill switch  -> se armato, niente ordini;
  2. risk manager -> limiti hard (volume, posizioni, perdita giornaliera...);
  3. conferma     -> in modalita' live ogni ordine richiede il tuo ok;
  4. esecuzione   -> tramite il broker, con registrazione nell'audit log.

Riusa la stessa "scatola nera" e lo stesso freno d'emergenza del resto di
Jarvis: il trading non e' un'isola, vive sotto le stesse regole di sicurezza.
"""

from __future__ import annotations

from typing import Callable

from ..core import AuditLog, KillSwitch
from .broker import Broker, Order, Position
from .risk import RiskDecision, RiskManager

Confirmer = Callable[[str, str], bool]


def _deny(_cmd: str, _reason: str) -> bool:
    return False


class TradingEngine:
    def __init__(
        self,
        broker: Broker,
        risk: RiskManager,
        audit: AuditLog,
        killswitch: KillSwitch,
        confirmer: Confirmer = _deny,
    ):
        self.broker = broker
        self.risk = risk
        self.audit = audit
        self.killswitch = killswitch
        self.confirmer = confirmer

    def place_order(self, order: Order) -> Position | None:
        tag = f"{order.side} {order.volume} {order.symbol}"

        if self.killswitch.is_engaged():
            self.audit.record("trade_blocked", order=tag, note=f"kill switch ({self.killswitch.reason()})")
            return None

        decision: RiskDecision = self.risk.check(order, self.broker)
        if not decision.approved:
            self.audit.record("trade_rejected", order=tag, reason=decision.reason,
                              mode=self.risk.config.mode)
            return None

        if decision.needs_confirmation:
            self.audit.record("trade_confirm_requested", order=tag)
            if not self.confirmer(tag, "ORDINE LIVE (soldi veri)"):
                self.audit.record("trade_aborted", order=tag, note="conferma negata")
                return None

        pos = self.broker.open(order)
        self.audit.record("trade_opened", order=tag, position_id=pos.id,
                          entry=pos.entry_price, sl=pos.sl, tp=pos.tp,
                          mode=self.risk.config.mode)
        return pos

    def close_position(self, position_id: int, price: float | None = None,
                       reason: str = "manuale") -> float:
        pnl = self.broker.close(position_id, price)
        self.risk.register_realized(pnl)
        self.audit.record("trade_closed", position_id=position_id, pnl=round(pnl, 2),
                          reason=reason, realized_today=round(self.risk.realized_pnl_today, 2))
        return pnl

    def update_market(self, symbol: str, price: float) -> list[tuple[int, str]]:
        """Aggiorna il prezzo e chiude automaticamente le posizioni che hanno
        toccato stop-loss o take-profit, registrando P&L e audit. E' il modo
        corretto di 'far scorrere' il mercato: SL/TP passano dal rischio."""
        triggered = self.broker.mark(symbol, price)
        for pos_id, why in triggered:
            self.close_position(pos_id, price, reason=why)
        return triggered

    def snapshot(self) -> dict:
        return {
            "mode": self.risk.config.mode,
            "equity": round(self.broker.equity(), 2),
            "open_positions": len(self.broker.positions()),
            "realized_today": round(self.risk.realized_pnl_today, 2),
            "stopped": self.killswitch.is_engaged(),
        }
