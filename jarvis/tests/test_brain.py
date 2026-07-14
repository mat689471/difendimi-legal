"""Test del Cervello: capisce l'intento, agisce, e resta sotto sicurezza."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from jarvis.agent import Jarvis
from jarvis.brain import Brain, KeywordPlanner
from jarvis.guardian import Guardian


@pytest.fixture
def brain(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"autonomy: auto\n"
        f"stop_sentinel: {tmp_path}/STOP\n"
        f"audit_path: {tmp_path}/audit.jsonl\n",
        encoding="utf-8",
    )
    return Brain(jarvis=Jarvis.from_config(str(cfg), confirmer=lambda c, r: False),
                 guardian=Guardian())


# --- comprensione dell'intento ----------------------------------------------

def test_riconosce_gli_intenti(brain):
    assert brain._route("fermati")[0] == "stop"
    assert brain._route("riprendi")[0] == "start"
    assert brain._route("come stai?")[0] == "status"
    assert brain._route("come va il trading?")[0] == "trading"
    assert brain._route("esegui df -h") == ("system", "df -h")
    i, arg = brain._route("crea un video sui ricorsi per multe")
    assert i == "content" and "ricorsi" in arg
    assert brain._route("ciao")[0] == "help"


# --- azioni ------------------------------------------------------------------

def test_esegue_comando_di_sistema(brain):
    r = brain.handle("esegui echo cervello-ok")
    assert r.intent == "system"
    assert "cervello-ok" in r.text

def test_stop_poi_comando_bloccato(brain):
    brain.handle("fermati")
    assert brain.jarvis.killswitch.is_engaged()
    r = brain.handle("esegui echo x")
    assert r.data["executed"] is False

def test_content_prepara_i_file(brain, tmp_path, monkeypatch):
    import jarvis.content.pipeline as pl
    monkeypatch.setattr(pl, "REMOTION", tmp_path / "remotion")
    r = brain.handle("crea un video sui diritti del cittadino")
    assert r.intent == "content"
    assert Path(r.data["props"]).exists()
    assert Path(r.data["social"]).exists()

def test_help_su_frase_ignota(brain):
    r = brain.handle("raccontami una barzelletta")
    assert r.intent == "help"
    assert "Posso" in r.text


def test_conversazione_usa_il_responder_se_presente(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(f"autonomy: auto\nstop_sentinel: {tmp_path}/STOP\naudit_path: {tmp_path}/a.jsonl\n",
                   encoding="utf-8")

    class FakeResponder:
        def available(self): return True
        def reply(self, message): return "Con piacere, signore: ecco la mia risposta."

    b = Brain(jarvis=Jarvis.from_config(str(cfg), confirmer=lambda c, r: False),
              guardian=Guardian(), responder=FakeResponder())
    r = b.handle("cosa ne pensi del meteo?")
    assert r.intent == "chat"
    assert "signore" in r.text


# --- guardiano integrato -----------------------------------------------------

def test_guardiano_avvisa_su_comando_irreversibile_di_notte(brain):
    r = brain.handle("esegui rm -rf /etc", now=datetime(2026, 7, 14, 3, 0))
    keys = {a.key for a in r.advisories}
    assert "notte_irreversibile" in keys
    # e comunque il comando catastrofico non viene eseguito (confirmer nega)
    assert r.data["executed"] is False


# --- pianificatore + plan_and_do --------------------------------------------

def test_keyword_planner_singolo_passo():
    assert KeywordPlanner().plan("esegui ls") == ["esegui ls"]

def test_plan_and_do_esegue_i_passi(brain):
    class FakePlanner:
        def plan(self, goal):
            return ["esegui echo uno", "esegui echo due"]
    replies = brain.plan_and_do("qualcosa", planner=FakePlanner())
    assert len(replies) == 2
    assert "uno" in replies[0].text and "due" in replies[1].text

def test_plan_and_do_si_ferma_sul_kill_switch(brain):
    brain.jarvis.killswitch.engage("test")
    class FakePlanner:
        def plan(self, goal):
            return ["esegui echo uno", "esegui echo due"]
    replies = brain.plan_and_do("qualcosa", planner=FakePlanner())
    assert replies[0].intent == "stop"
