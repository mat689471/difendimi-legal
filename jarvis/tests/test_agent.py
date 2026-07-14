"""Test dell'Agente Contenuti: genera pezzi diversi e coerenti dal brand."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from jarvis.content.agent import Brand, ContentAgent, IdeaGenerator


def _brand():
    return Brand(
        name="studio-test", display="⚖️ TEST",
        topics=["la multa", "il licenziamento", "l'eredità"],
        features=["✅ A", "✅ B"], offer="Gratis 🎁", cta="Chiama ⚖️",
        cta_badge="📲 WhatsApp", hashtags_base="#test",
    )


def test_genera_il_numero_richiesto_di_brief():
    briefs = IdeaGenerator().briefs(_brand(), 5)
    assert len(briefs) == 5


def test_i_pezzi_sono_diversi_tra_loro():
    briefs = IdeaGenerator().briefs(_brand(), 5)
    hooks = [b["hook"] for b in briefs]
    assert len(set(hooks)) == 5  # tutti gli hook diversi


def test_ruota_angolazioni_e_argomenti():
    briefs = IdeaGenerator().briefs(_brand(), 3)
    angles = [b["_angle"] for b in briefs]
    topics = [b["_topic"] for b in briefs]
    assert len(set(angles)) == 3
    assert len(set(topics)) == 3


def test_brand_from_dict():
    b = Brand.from_dict(json.loads(
        Path("jarvis/content/brand.example.json").read_text(encoding="utf-8")))
    assert b.name == "studio-rossi"
    assert len(b.topics) == 5


def test_produce_scrive_props_social_e_manifest(tmp_path, monkeypatch):
    import jarvis.content.pipeline as pl
    import jarvis.content.agent as ag
    monkeypatch.setattr(pl, "REMOTION", tmp_path)
    monkeypatch.setattr(ag, "REMOTION", tmp_path)

    pieces = ContentAgent().produce(_brand(), count=3)
    assert len(pieces) == 3
    for p in pieces:
        assert Path(p.props).exists()
        assert Path(p.social).exists()
    manifest = tmp_path / "out" / "studio-test" / "manifest.json"
    assert manifest.exists()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert len(data) == 3


def test_audit_registra_ogni_pezzo(tmp_path, monkeypatch):
    import jarvis.content.pipeline as pl
    import jarvis.content.agent as ag
    from jarvis.core import AuditLog
    monkeypatch.setattr(pl, "REMOTION", tmp_path)
    monkeypatch.setattr(ag, "REMOTION", tmp_path)

    audit = AuditLog(tmp_path / "audit.jsonl")
    ContentAgent(audit=audit).produce(_brand(), count=2)
    events = [e for e in audit.tail(50) if e["event"] == "content_generated"]
    assert len(events) == 2
