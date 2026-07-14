"""Risk manager: i limiti hard che proteggono il conto.

E' il cuore della sicurezza del trading. Nessun ordine passa senza il suo ok.
Blocca prima di eseguire — perche' nel trading, come nel resto di Jarvis, un
controllo che arriva dopo il danno non serve.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .broker import Broker, Order


@dataclass
class RiskConfig:
    mode: str = "paper"              # "paper" | "demo" | "live"
    allow_live: bool = False         # doppio interruttore: live richiede questo True
    max_volume_per_order: float = 0.10
    max_open_positions: int = 3
    max_total_volume: float = 0.30
    max_daily_loss: float = 200.0    # in valuta del conto; perdita giornaliera oltre cui si blocca
    allowed_symbols: list[str] | None = None  # None = qualsiasi


@dataclass
class RiskDecision:
    approved: bool
    reason: str
    needs_confirmation: bool = False


def size_for_risk(balance: float, risk_pct: float, entry: float, stop: float,
                  point_value: float, *, max_volume: float | None = None) -> float:
    """Dimensiona la posizione perche' la perdita allo stop sia ~ risk_pct del
    conto. Regola cardine del trading serio: non rischiare mai piu' di una
    piccola frazione per operazione.

        volume = (balance * risk_pct) / (distanza_stop * point_value)

    Ritorna 0 se lo stop coincide con l'ingresso (distanza nulla). Il volume
    e' arrotondato a 2 decimali e limitato da max_volume, se dato.
    """
    stop_distance = abs(entry - stop)
    if stop_distance == 0 or point_value <= 0 or risk_pct <= 0:
        return 0.0
    volume = (balance * risk_pct) / (stop_distance * point_value)
    volume = round(volume, 2)
    if max_volume is not None:
        volume = min(volume, max_volume)
    return volume


@dataclass
class RiskManager:
    config: RiskConfig
    realized_pnl_today: float = 0.0
    _blocked: bool = field(default=False, init=False)

    def register_realized(self, pnl: float) -> None:
        self.realized_pnl_today += pnl

    def reset_day(self) -> None:
        self.realized_pnl_today = 0.0
        self._blocked = False

    def check(self, order: Order, broker: Broker) -> RiskDecision:
        c = self.config

        if order.side not in ("buy", "sell"):
            return RiskDecision(False, f"lato ordine non valido: {order.side}")

        if order.volume <= 0:
            return RiskDecision(False, "volume non positivo")

        if c.allowed_symbols is not None and order.symbol not in c.allowed_symbols:
            return RiskDecision(False, f"simbolo non consentito: {order.symbol}")

        if order.volume > c.max_volume_per_order:
            return RiskDecision(False,
                f"volume {order.volume} oltre il massimo per ordine ({c.max_volume_per_order})")

        positions = broker.positions()
        if len(positions) >= c.max_open_positions:
            return RiskDecision(False,
                f"raggiunto il massimo di posizioni aperte ({c.max_open_positions})")

        total_volume = sum(p.volume for p in positions) + order.volume
        if total_volume > c.max_total_volume:
            return RiskDecision(False,
                f"volume totale {total_volume:.2f} oltre il massimo ({c.max_total_volume})")

        # Perdita giornaliera: se gia' oltre soglia, stop a nuovi ordini.
        if -self.realized_pnl_today >= c.max_daily_loss:
            return RiskDecision(False,
                f"perdita giornaliera {-self.realized_pnl_today:.2f} oltre il limite ({c.max_daily_loss}). Stop.")

        # live: consentito solo col doppio interruttore, e sempre con conferma umana.
        if c.mode == "live":
            if not c.allow_live:
                return RiskDecision(False,
                    "modalita' live disabilitata (allow_live=false). Soldi veri richiedono un'attivazione esplicita.")
            return RiskDecision(True, "ok (live: richiede conferma)", needs_confirmation=True)

        return RiskDecision(True, "ok")
