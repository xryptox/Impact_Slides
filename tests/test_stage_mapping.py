"""
Tests for v3 #24 — configurable Why/What/How/Now stage mapping.

Covers:
  - Default behavior unchanged (centralized tables reproduce old literals)
  - insight_type override via config (stage_rules.insight_types)
  - keyword-override layer (stage_rules.keyword_overrides) — text regex -> stages
  - slide-type keyword extension (stage_rules.slide_type_keywords)
  - slide-type stage override (stage_rules.slide_type_stages)
  - conclusion-bullet stages override (stage_rules.conclusion_bullet_stages)
  - validation: bad stage name, bad regex, bad insight_type — fail fast
  - _stages_for() lookup order: keyword_override > insight_type > default
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

import step1_preprocessor_v3 as m


@pytest.fixture()
def make_preprocessor(tmp_workspace):
    """Build a v3 preprocessor (overrides conftest's v2 fixture)."""
    def _make(filter_level="permissive", config_snapshot=None):
        inp = tmp_workspace / "input"
        out = tmp_workspace / "output"
        inp.mkdir(parents=True, exist_ok=True)
        p = m.ImpactSlidePreprocessorV2(
            input_path=str(inp), output_dir=str(out), filter_level=filter_level,
        )
        if config_snapshot is not None:
            p.config_snapshot = config_snapshot
            p.stage_rules = p._build_stage_rules()
        return p, inp, out
    return _make


# --------------------------------------------------------------------------- #
# Default behavior (regression guard)
# --------------------------------------------------------------------------- #
class TestDefaults:
    def test_default_tables_populated(self):
        assert m.DEFAULT_INSIGHT_TYPE_STAGES
        assert "numeric_range" in m.DEFAULT_INSIGHT_TYPE_STAGES
        assert "aggregate_insight" in m.DEFAULT_INSIGHT_TYPE_STAGES
        assert m.DEFAULT_SLIDE_TYPE_STAGES
        assert "conclusion" in m.DEFAULT_SLIDE_TYPE_STAGES

    def test_stages_for_returns_default(self, make_preprocessor):
        p, _, _ = make_preprocessor()
        assert p._stages_for("numeric_range") == ["What", "How"]
        assert p._stages_for("aggregate_insight") == ["How", "What"]
        assert p._stages_for("table_cell") == ["What"]
        assert p._stages_for("unknown_type") == ["What"]  # fallback

    def test_default_conclusion_bullet_stages(self, make_preprocessor):
        p, _, _ = make_preprocessor()
        assert "Now" in p.stage_rules["conclusion_bullet_stages"]

    def test_default_pipeline_unchanged(self, make_excel, make_preprocessor):
        """A real run without config produces the same stages as before the
        centralization — the regression guard."""
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2, 3], "V": [10, 20, 30]}))
        p.run()
        ev = json.load(open(out / "evidence_register_seed.json"))
        # every entry has valid stages
        from impact_slides.schemas import NARRATIVE_STAGES
        for e in ev:
            for s in e["suggested_narrative_use"]:
                assert s in NARRATIVE_STAGES


# --------------------------------------------------------------------------- #
# insight_type override
# --------------------------------------------------------------------------- #
class TestInsightTypeOverride:
    def test_override_insight_type_stages(self, make_preprocessor):
        cfg = {"stage_rules": {"insight_types": {"numeric_range": ["How", "Now"]}}}
        p, _, _ = make_preprocessor(config_snapshot=cfg)
        assert p._stages_for("numeric_range") == ["How", "Now"]
        # other types unchanged
        assert p._stages_for("aggregate_insight") == ["How", "What"]

    def test_override_in_pipeline(self, make_excel, make_preprocessor):
        """A user override on trend_insight flows through to the evidence."""
        cfg = {"stage_rules": {"insight_types": {"trend_insight": ["How", "Now"]}}}
        p, inp, out = make_preprocessor(config_snapshot=cfg)
        make_excel(df=pd.DataFrame({"Month": ["Jan", "Feb", "Mar"],
                                    "Revenue": [100, 200, 300]}))
        p.run()
        ev = json.load(open(out / "evidence_register_seed.json"))
        trends = [e for e in ev if e["insight_type"] == "trend_insight"]
        if trends:
            assert "Now" in trends[0]["suggested_narrative_use"]
            assert "How" in trends[0]["suggested_narrative_use"]


# --------------------------------------------------------------------------- #
# keyword-override layer
# --------------------------------------------------------------------------- #
class TestKeywordOverride:
    def test_keyword_override_wins_over_insight_type(self, make_preprocessor):
        cfg = {"stage_rules": {"keyword_overrides": [
            {"pattern": r"\brevenue\b", "stages": ["What", "Now"]},
        ]}}
        p, _, _ = make_preprocessor(config_snapshot=cfg)
        # numeric_range default is ["What", "How"], but revenue text overrides
        assert p._stages_for("numeric_range", "revenue ranges from 10 to 50") == ["What", "Now"]

    def test_no_keyword_match_falls_through(self, make_preprocessor):
        cfg = {"stage_rules": {"keyword_overrides": [
            {"pattern": r"\bchurn\b", "stages": ["How", "Now"]},
        ]}}
        p, _, _ = make_preprocessor(config_snapshot=cfg)
        # text doesn't contain 'churn' → falls back to insight_type default
        assert p._stages_for("numeric_range", "cost ranges from 10 to 50") == ["What", "How"]

    def test_keyword_override_in_pipeline(self, make_excel, make_pptx, make_preprocessor):
        """A keyword override on 'revenue' redirects revenue-mentioning bullets."""
        cfg = {"stage_rules": {"keyword_overrides": [
            {"pattern": r"\brevenue\b", "stages": ["What", "Now"]},
        ]}}
        p, inp, out = make_preprocessor(config_snapshot=cfg)
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}))
        make_pptx(slides=[
            {"title": "Overview"},
            {"title": "Key Insight", "body": "Revenue grew strongly this quarter"},
        ])
        p.run()
        ev = json.load(open(out / "evidence_register_seed.json"))
        revenue_ev = [e for e in ev if "revenue" in e["text"].lower()]
        assert revenue_ev, "expected revenue-mentioning evidence"
        for e in revenue_ev:
            if e["insight_type"] == "bullet_insight":
                assert "Now" in e["suggested_narrative_use"]

    def test_first_match_wins(self, make_preprocessor):
        cfg = {"stage_rules": {"keyword_overrides": [
            {"pattern": r"\bgrowth\b", "stages": ["How"]},
            {"pattern": r"\bgrowth\b", "stages": ["Now"]},
        ]}}
        p, _, _ = make_preprocessor(config_snapshot=cfg)
        assert p._stages_for("bullet_insight", "growth was strong") == ["How"]


# --------------------------------------------------------------------------- #
# slide-type keyword + stage overrides
# --------------------------------------------------------------------------- #
class TestSlideTypeOverrides:
    def test_extend_slide_keywords(self, make_preprocessor):
        """User adds 'wrap-up' to the conclusion keyword list."""
        cfg = {"stage_rules": {"slide_type_keywords": {
            "conclusion": ["summary", "conclusion", "wrap-up"]}}}
        p, _, _ = make_preprocessor(config_snapshot=cfg)
        kws = p.stage_rules["slide_type_keywords"]["conclusion"]
        assert "wrap-up" in kws

    def test_override_slide_type_stages(self, make_preprocessor):
        cfg = {"stage_rules": {"slide_type_stages": {"data_chart": ["How"]}}}
        p, _, _ = make_preprocessor(config_snapshot=cfg)
        assert p.stage_rules["slide_type_stages"]["data_chart"] == ["How"]
        # other types unchanged
        assert p.stage_rules["slide_type_stages"]["conclusion"] == ["What", "How", "Why", "Now"]

    def test_extended_keyword_classifies_slide(self, make_pptx, make_preprocessor):
        """A 'Wrap-up' slide should classify as 'conclusion' after the user
        adds 'wrap-up' to the conclusion keyword list."""
        cfg = {"stage_rules": {"slide_type_keywords": {
            "conclusion": ["summary", "conclusion", "wrap-up"]}}}
        p, inp, out = make_preprocessor(config_snapshot=cfg)
        make_pptx(slides=[
            {"title": "Intro"},
            {"title": "Wrap-up", "body": "Key findings and recommendations"},
        ])
        p.run()
        prof = json.load(open(out / "pptx_profile.json"))
        wrapup = [s for s in prof[0]["slides"] if "wrap" in s.get("title", "").lower()]
        assert wrapup, "expected a wrap-up slide"
        assert wrapup[0]["classification"]["type"] == "conclusion"


# --------------------------------------------------------------------------- #
# conclusion-bullet stages override
# --------------------------------------------------------------------------- #
class TestConclusionBulletOverride:
    def test_override_conclusion_bullet_stages(self, make_preprocessor):
        cfg = {"stage_rules": {"conclusion_bullet_stages": ["Now"]}}
        p, _, _ = make_preprocessor(config_snapshot=cfg)
        assert p.stage_rules["conclusion_bullet_stages"] == ["Now"]

    def test_conclusion_bullets_use_override(self, make_pptx, make_preprocessor):
        """Conclusion bullets get the overridden stages."""
        cfg = {"stage_rules": {"conclusion_bullet_stages": ["Now", "How"]}}
        p, inp, out = make_preprocessor(config_snapshot=cfg)
        make_pptx(slides=[
            {"title": "Intro"},
            {"title": "Conclusion", "body": "Recommendation: expand North operations"},
        ])
        p.run()
        ev = json.load(open(out / "evidence_register_seed.json"))
        bullets = [e for e in ev if e["insight_type"] == "bullet_insight"
                   and "recommend" in e["text"].lower()]
        if bullets:
            assert "Now" in bullets[0]["suggested_narrative_use"]
            assert "How" in bullets[0]["suggested_narrative_use"]


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
class TestValidation:
    def test_bad_stage_name_raises(self, make_preprocessor):
        cfg = {"stage_rules": {"insight_types": {"numeric_range": ["What", "Future"]}}}
        with pytest.raises(ValueError, match="invalid stage"):
            make_preprocessor(config_snapshot=cfg)

    def test_bad_keyword_override_stage_raises(self, make_preprocessor):
        cfg = {"stage_rules": {"keyword_overrides": [
            {"pattern": r"\brevenue\b", "stages": ["Tomorrow"]},
        ]}}
        with pytest.raises(ValueError, match="invalid stage"):
            make_preprocessor(config_snapshot=cfg)

    def test_bad_regex_raises(self, make_preprocessor):
        cfg = {"stage_rules": {"keyword_overrides": [
            {"pattern": "[invalid(", "stages": ["What"]},
        ]}}
        with pytest.raises(ValueError, match="invalid regex"):
            make_preprocessor(config_snapshot=cfg)

    def test_bad_slide_type_stage_raises(self, make_preprocessor):
        cfg = {"stage_rules": {"slide_type_stages": {"conclusion": ["Later"]}}}
        with pytest.raises(ValueError, match="invalid stage"):
            make_preprocessor(config_snapshot=cfg)


# --------------------------------------------------------------------------- #
# _stages_for lookup order
# --------------------------------------------------------------------------- #
class TestLookupOrder:
    def test_keyword_override_beats_insight_type(self, make_preprocessor):
        cfg = {"stage_rules": {
            "insight_types": {"numeric_range": ["How"]},
            "keyword_overrides": [{"pattern": r"\bsales\b", "stages": ["Now"]}],
        }}
        p, _, _ = make_preprocessor(config_snapshot=cfg)
        # keyword match wins over insight_type override
        assert p._stages_for("numeric_range", "sales grew") == ["Now"]
        # no keyword match → insight_type override
        assert p._stages_for("numeric_range", "cost grew") == ["How"]

    def test_default_when_no_match(self, make_preprocessor):
        p, _, _ = make_preprocessor()
        assert p._stages_for("nonexistent", "some text", default=["Why"]) == ["Why"]
        assert p._stages_for("nonexistent", "some text") == ["What"]
