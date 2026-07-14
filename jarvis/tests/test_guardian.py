"""Test del Guardiano: la prudenza scatta quando serve, tace quando non serve."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from jarvis.guardian import Guardian, GuardianConfig


def _keys(advisories):
    return {a.key for a in advisories}


def test_tace_su_azione_ordinaria_di_giorno():
    g = Guardian()
    adv = g.observe(risk="SAFE", now=datetime(2026, 7, 14, 15, 0))
    assert adv == []


def test_avvisa_su_irreversibile_di_notte():
    g = Guardian()
    adv = g.observe(risk="CATASTROPHIC", now=datetime(2026, 7, 14, 3, 0))
    assert "notte_irreversibile" in _keys(adv)
    assert adv[0].level == "attenzione"


def test_irreversibile_di_giorno_non_scatta_lavviso_notturno():
    g = Guardian()
    adv = g.observe(risk="CATASTROPHIC", now=datetime(2026, 7, 14, 15, 0))
    assert "notte_irreversibile" not in _keys(adv)


def test_avvisa_sempre_su_denaro_reale():
    g = Guardian()
    adv = g.observe(risk="ELEVATED", real_money=True, now=datetime(2026, 7, 14, 15, 0))
    assert "denaro_reale" in _keys(adv)


def test_azioni_a_raffica():
    g = Guardian(GuardianConfig(rapid_count=5, rapid_window_sec=60))
    t = datetime(2026, 7, 14, 16, 0)
    seen = set()
    for i in range(6):
        seen |= _keys(g.observe(risk="SAFE", now=t + timedelta(seconds=i * 5)))
    assert "a_raffica" in seen


def test_raffica_non_scatta_se_azioni_distanziate():
    g = Guardian(GuardianConfig(rapid_count=5, rapid_window_sec=60))
    t = datetime(2026, 7, 14, 16, 0)
    seen = set()
    for i in range(6):
        seen |= _keys(g.observe(risk="SAFE", now=t + timedelta(seconds=i * 30)))  # 30s l'una
    assert "a_raffica" not in seen


def test_pausa_dopo_sessione_lunga_una_volta_sola():
    g = Guardian(GuardianConfig(session_break_minutes=120, cooldown_minutes=1))
    start = datetime(2026, 7, 14, 9, 0)
    g.observe(risk="SAFE", now=start)
    adv1 = g.observe(risk="SAFE", now=start + timedelta(hours=2, minutes=1))
    assert "pausa" in _keys(adv1)
    # non deve ripetere la pausa subito dopo
    adv2 = g.observe(risk="SAFE", now=start + timedelta(hours=2, minutes=2))
    assert "pausa" not in _keys(adv2)


def test_cooldown_evita_ripetizioni():
    g = Guardian(GuardianConfig(cooldown_minutes=30))
    t = datetime(2026, 7, 14, 3, 0)
    a1 = g.observe(risk="CATASTROPHIC", now=t)
    a2 = g.observe(risk="CATASTROPHIC", now=t + timedelta(minutes=5))  # entro il cooldown
    assert "notte_irreversibile" in _keys(a1)
    assert "notte_irreversibile" not in _keys(a2)
    # passato il cooldown, puo' riparlare
    a3 = g.observe(risk="CATASTROPHIC", now=t + timedelta(minutes=31))
    assert "notte_irreversibile" in _keys(a3)


def test_non_blocca_mai_restituisce_solo_consigli():
    # il Guardiano non ha modo di impedire: ritorna avvisi, non decisioni
    g = Guardian()
    adv = g.observe(risk="CATASTROPHIC", real_money=True, now=datetime(2026, 7, 14, 3, 0))
    assert all(a.level in ("info", "suggerimento", "attenzione") for a in adv)
