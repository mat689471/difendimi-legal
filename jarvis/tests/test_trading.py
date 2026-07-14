"""Test del modulo trading: limiti hard, kill switch, gate live, P&L paper."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from jarvis.core import AuditLog, KillSwitch
from jarvis.trading import (
    Order, PaperBroker, RiskConfig, RiskManager, TradingEngine, SmaCrossover,
    RsiReversion, TrendRsi, size_for_risk,
)


def _engine(tmp_path, config: RiskConfig, confirmer=lambda t, r: False):
    audit = AuditLog(tmp_path / "trading.jsonl")
    ks = KillSwitch(str(tmp_path / "STOP"))
    ks.disengage()
    broker = PaperBroker(starting_balance=10_000)
    risk = RiskManager(config)
    return TradingEngine(broker, risk, audit, ks, confirmer), broker, ks


# --- P&L paper ---------------------------------------------------------------

def test_paper_pnl_buy():
    broker = PaperBroker()
    broker.set_point_value("EURUSD", 10.0)
    pos = broker.open(Order("EURUSD", "buy", 1.0, price=100.0))
    pnl = broker.close(pos.id, price=105.0)
    assert pnl == (105 - 100) * 1 * 1.0 * 10.0  # 50.0

def test_paper_pnl_sell():
    broker = PaperBroker()
    pos = broker.open(Order("EURUSD", "sell", 2.0, price=100.0))
    pnl = broker.close(pos.id, price=98.0)
    assert pnl == (98 - 100) * -1 * 2.0 * 1.0  # +4.0


# --- limiti hard -------------------------------------------------------------

def test_rifiuta_volume_eccessivo(tmp_path):
    eng, _, _ = _engine(tmp_path, RiskConfig(mode="paper", max_volume_per_order=0.10))
    assert eng.place_order(Order("EURUSD", "buy", 0.50, price=1.0)) is None

def test_rifiuta_simbolo_non_in_whitelist(tmp_path):
    eng, _, _ = _engine(tmp_path, RiskConfig(mode="paper", allowed_symbols=["EURUSD"]))
    assert eng.place_order(Order("BTCUSD", "buy", 0.10, price=1.0)) is None

def test_rifiuta_troppe_posizioni(tmp_path):
    eng, _, _ = _engine(tmp_path, RiskConfig(mode="paper", max_open_positions=1, max_total_volume=99))
    assert eng.place_order(Order("EURUSD", "buy", 0.10, price=1.0)) is not None
    assert eng.place_order(Order("EURUSD", "buy", 0.10, price=1.0)) is None

def test_stop_su_perdita_giornaliera(tmp_path):
    eng, broker, _ = _engine(tmp_path, RiskConfig(mode="paper", max_daily_loss=5, max_total_volume=99))
    broker.set_point_value("EURUSD", 1.0)
    pos = eng.place_order(Order("EURUSD", "buy", 0.10, price=100.0))
    eng.close_position(pos.id, price=0.0)  # perdita di 10 (> limite 5)
    # ora oltre soglia -> nuovi ordini bloccati
    assert eng.place_order(Order("EURUSD", "buy", 0.10, price=100.0)) is None


# --- kill switch e gate live -------------------------------------------------

def test_kill_switch_blocca_ordini(tmp_path):
    eng, _, ks = _engine(tmp_path, RiskConfig(mode="paper"))
    ks.engage("test")
    assert eng.place_order(Order("EURUSD", "buy", 0.10, price=1.0)) is None

def test_live_bloccato_senza_allow_live(tmp_path):
    eng, _, _ = _engine(tmp_path, RiskConfig(mode="live", allow_live=False))
    assert eng.place_order(Order("EURUSD", "buy", 0.10, price=1.0)) is None

def test_live_richiede_conferma(tmp_path):
    # allow_live ma conferma negata -> niente ordine
    eng, _, _ = _engine(tmp_path, RiskConfig(mode="live", allow_live=True), confirmer=lambda t, r: False)
    assert eng.place_order(Order("EURUSD", "buy", 0.10, price=1.0)) is None
    # conferma accettata -> ordine passa
    eng2, _, _ = _engine(tmp_path, RiskConfig(mode="live", allow_live=True), confirmer=lambda t, r: True)
    assert eng2.place_order(Order("EURUSD", "buy", 0.10, price=1.0)) is not None


# --- strategia ---------------------------------------------------------------

def test_sma_emette_solo_sui_crossover():
    strat = SmaCrossover(fast=2, slow=4)
    prices = [1, 2, 3, 4, 5, 4, 3, 2, 1]
    signals = [strat.signal(p) for p in prices]
    # niente segnali finche' la finestra lenta non e' piena
    assert signals[0] == "flat" and signals[1] == "flat" and signals[2] == "flat"
    # deve comparire almeno un buy e un sell nel percorso su-e-giu'
    assert "buy" in signals and "sell" in signals


# --- stop-loss / take-profit -------------------------------------------------

def test_buy_chiude_su_stop_loss(tmp_path):
    eng, broker, _ = _engine(tmp_path, RiskConfig(mode="paper"))
    broker.set_point_value("EURUSD", 1.0)
    eng.place_order(Order("EURUSD", "buy", 0.10, price=100.0, sl=98.0, tp=105.0))
    # prezzo scende sotto lo stop -> chiusura automatica in perdita
    triggered = eng.update_market("EURUSD", 97.5)
    assert triggered and triggered[0][1] == "sl"
    assert broker.positions() == []
    assert eng.risk.realized_pnl_today < 0

def test_sell_chiude_su_take_profit(tmp_path):
    eng, broker, _ = _engine(tmp_path, RiskConfig(mode="paper"))
    broker.set_point_value("EURUSD", 1.0)
    eng.place_order(Order("EURUSD", "sell", 0.10, price=100.0, sl=102.0, tp=95.0))
    triggered = eng.update_market("EURUSD", 94.0)  # scende: profitto per lo short
    assert triggered and triggered[0][1] == "tp"
    assert eng.risk.realized_pnl_today > 0

def test_sl_tp_non_scatta_dentro_range(tmp_path):
    eng, broker, _ = _engine(tmp_path, RiskConfig(mode="paper"))
    eng.place_order(Order("EURUSD", "buy", 0.10, price=100.0, sl=98.0, tp=105.0))
    assert eng.update_market("EURUSD", 101.0) == []
    assert len(broker.positions()) == 1


# --- position sizing ---------------------------------------------------------

def test_size_for_risk():
    # rischio 1% di 10000 = 100; distanza stop 2, point_value 10 -> 100/(2*10) = 5.0
    assert size_for_risk(10_000, 0.01, entry=100, stop=98, point_value=10) == 5.0

def test_size_for_risk_stop_nullo_da_zero():
    assert size_for_risk(10_000, 0.01, entry=100, stop=100, point_value=10) == 0.0

def test_size_for_risk_rispetta_il_massimo():
    assert size_for_risk(10_000, 0.10, entry=100, stop=99, point_value=10, max_volume=1.0) == 1.0


# --- strategie RSI -----------------------------------------------------------

def test_rsi_reversion_compra_in_ipervenduto_e_vende_in_ipercomprato():
    strat = RsiReversion(period=3, oversold=30, overbought=70)
    down = [strat.signal(p) for p in [100, 98, 96, 94, 92, 90]]
    assert "buy" in down          # discesa costante -> RSI basso -> buy
    up = [strat.signal(p) for p in [92, 95, 98, 101, 104, 107]]
    assert "sell" in up           # risalita costante -> RSI alto -> sell

def test_trend_rsi_non_va_controtrend():
    # discesa costante: trend giu', RSI basso. TrendRsi NON deve comprare
    # controtendenza (compra solo se prezzo sopra la SMA).
    strat = TrendRsi(trend=5, period=3, oversold=35, overbought=65)
    signals = [strat.signal(p) for p in [110, 108, 106, 104, 102, 100, 98, 96]]
    assert "buy" not in signals
