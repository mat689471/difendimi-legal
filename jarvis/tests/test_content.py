"""Test della pipeline contenuti e della validazione config."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from jarvis.content import build_props, prepare, social_package


def test_build_props_riempie_i_default():
    props = build_props({"hook": "Multa ingiusta?"})
    assert props["captions"][0] == "Multa ingiusta?"
    # gli altri restano ai default
    assert props["brand"] == "⚖️ DIFENDIMI"
    assert props["captions"][3] == ""  # slot features sempre vuoto
    assert len(props["captions"]) == 7


def test_build_props_mappa_lo_schema_narrativo():
    brief = {
        "hook": "H", "agitate": "A", "solution": "S",
        "testimonial": "T", "offer": "O", "cta": "C",
    }
    caps = build_props(brief)["captions"]
    assert [caps[0], caps[1], caps[2], caps[4], caps[5], caps[6]] == ["H", "A", "S", "T", "O", "C"]


def test_social_package_contiene_hashtag_e_cta():
    brief = {"title": "Titolo", "hashtags": "#a #b"}
    props = build_props(brief)
    pkg = social_package(brief, props)
    assert "Titolo" in pkg
    assert "#a #b" in pkg
    assert props["ctaBadge"] in pkg


def test_prepare_scrive_props_e_social(tmp_path, monkeypatch):
    import jarvis.content.pipeline as pl
    monkeypatch.setattr(pl, "REMOTION", tmp_path)
    out = pl.prepare({"name": "Test Video!", "hook": "Ciao"})
    assert out.slug == "test-video"
    assert out.props_path.exists()
    assert out.social_path.exists()
    data = json.loads(out.props_path.read_text(encoding="utf-8"))
    assert data["captions"][0] == "Ciao"
    assert "remotion render" in out.render_command
    assert "DifendimiViral" in out.render_command


def test_config_non_valida_solleva(tmp_path):
    from jarvis.agent import Jarvis
    cfg = tmp_path / "config.yaml"
    cfg.write_text("autonomy: turbo\n", encoding="utf-8")
    with pytest.raises(ValueError):
        Jarvis.from_config(str(cfg))
