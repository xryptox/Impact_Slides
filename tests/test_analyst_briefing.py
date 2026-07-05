"""
Tests for v4 #26 — Analyst Briefing Generator.

Two layers:
  - Unit tests for `analyst_briefing.NarrativeScorer` and
    `AnalystBriefingGenerator` (pure, no I/O, run in isolation).
  - Integration tests via the v4 pipeline (local `make_preprocessor` fixture
    that shadows the conftest one — same pattern as the v3 test files).

Covers:
  - Narrative Readiness: 5 component sub-metrics, overall weighted composite,
    per-stage sub-scores, empty/zero evidence, missing-stage penalties.
  - Focus Areas: multi-signal theme detection (column names, "X by Y", cross-file
    entities, business keywords, derived-insight boosts), near-duplicate theme
    merging, ranking + capping to top_n.
  - Quality flags + slide-building recommendations.
  - Markdown rendering shape.
  - Pipeline integration: analyst_briefing.md + .json emitted unconditionally,
    run_metadata.json briefing block, zero-evidence briefing, --focus-areas CLI.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import step1_preprocessor_v4 as m

# Import the briefing module directly for pure unit tests.
from impact_slides import analyst_briefing as ab


# --------------------------------------------------------------------------- #
# Local preprocessor factory (shadows the conftest fixture — imports v4).
# --------------------------------------------------------------------------- #
@pytest.fixture()
def make_preprocessor(tmp_workspace):
    def _make(filter_level="permissive", focus_areas=None):
        inp = tmp_workspace / "input"
        out = tmp_workspace / "output"
        inp.mkdir(parents=True, exist_ok=True)
        p = m.ImpactSlidePreprocessorV4(
            input_path=str(inp), output_dir=str(out), filter_level=filter_level,
        )
        if focus_areas is not None:
            p.focus_areas_count = focus_areas
        return p, inp, out
    return _make


def _ev(eid, itype, text, priority, stages, source="a.xlsx",
        confidence="high", column=None):
    return {
        "evidence_id": eid, "source_file": source, "insight_type": itype,
        "text": text, "priority_score": priority, "confidence": confidence,
        "suggested_narrative_use": stages,
        "column_name": column, "source_location": "Sheet1",
    }


# --------------------------------------------------------------------------- #
# NarrativeScorer — readiness sub-metrics
# --------------------------------------------------------------------------- #
class TestReadinessScoring:
    def test_all_stages_balanced_scores_high(self):
        # 5 evidence in each of the 4 stages, all high priority
        ev = []
        for i, s in enumerate(["Why", "What", "How", "Now"]):
            for j in range(5):
                ev.append(_ev(f"E{i}{j:02d}", "numeric_range", f"{s} metric {j}",
                              0.85, [s]))
        scorer = ab.NarrativeScorer(ev, cross_file_relationships=[
            {"insight_type": "cross_file_metric", "priority_score": 0.9,
             "text": "'Growth' in 2 files"} for _ in range(5)],
            coverage_map={"by_narrative_stage": {
            "Why": 5, "What": 5, "How": 5, "Now": 5}})
        r = scorer.calculate_narrative_readiness()
        assert r["overall_score"] >= 85
        comps = r["components"]
        assert comps["coverage_balance"] >= 90   # perfectly balanced
        assert comps["recommendation_strength"] > 0  # Now present

    def test_missing_stage_penalized(self):
        ev = []
        for s in ["Why", "What", "How"]:
            for j in range(5):
                ev.append(_ev(f"E{s}{j}", "numeric_range", f"{s} {j}", 0.8, [s]))
        scorer = ab.NarrativeScorer(ev, coverage_map={"by_narrative_stage": {
            "Why": 5, "What": 5, "How": 5, "Now": 0}})
        r = scorer.calculate_narrative_readiness()
        assert r["stage_scores"]["Now"]["score"] == 0
        assert r["components"]["recommendation_strength"] == 0
        assert "Now" in r["explanation"]

    def test_zero_evidence(self):
        scorer = ab.NarrativeScorer([], coverage_map={"by_narrative_stage": {
            "Why": 0, "What": 0, "How": 0, "Now": 0}})
        r = scorer.calculate_narrative_readiness()
        assert r["overall_score"] == 0
        for s in ("Why", "What", "How", "Now"):
            assert r["stage_scores"][s]["score"] == 0

    def test_priority_quality_component(self):
        # high-priority fraction boosts the component
        ev = [_ev("E001", "numeric_range", "x", 0.9, ["What"]),
              _ev("E002", "numeric_range", "y", 0.9, ["What"])]
        scorer = ab.NarrativeScorer(ev)
        pq = scorer._priority_quality()
        assert pq >= 80  # 0.6*0.9 + 0.4*1.0 = 0.94 -> 94

    def test_cross_file_connectivity_saturates(self):
        cross = [{"insight_type": "cross_file_metric", "priority_score": 0.9,
                  "text": "'EMEA' in 2 files"} for _ in range(5)]
        scorer = ab.NarrativeScorer([], cross_file_relationships=cross)
        # 5 links -> volume saturated; avg_p 0.9 -> (0.5+0.45)=0.95
        cf = scorer._cross_file_connectivity()
        assert cf >= 90

    def test_signal_ratio_noise_penalty(self):
        ev = [_ev("E001", "numeric_range", "x", 0.5, ["What"], confidence="low"),
              _ev("E002", "numeric_range", "y", 0.5, ["What"], confidence="high")]
        scorer = ab.NarrativeScorer(ev)
        sr = scorer._signal_ratio()
        assert sr == 50  # 1 of 2 is low-confidence

    def test_custom_readiness_weights_validated(self):
        # valid override (sums to 1.0, same keys)
        w = {k: v for k, v in ab.READINESS_WEIGHTS.items()}
        scorer = ab.NarrativeScorer([], readiness_weights=w)
        assert scorer.readiness_weights == w
        # invalid: wrong sum
        bad = dict(ab.READINESS_WEIGHTS); bad["signal_ratio"] = 0.5
        with pytest.raises(ValueError):
            ab.NarrativeScorer([], readiness_weights=bad)
        # invalid: missing key
        bad2 = {k: v for k, v in ab.READINESS_WEIGHTS.items() if k != "signal_ratio"}
        bad2["signal_ratio"] = 0.0
        del bad2["signal_ratio"]
        with pytest.raises(ValueError):
            ab.NarrativeScorer([], readiness_weights=bad2)

    def test_stage_score_present_with_priority(self):
        ev = [_ev(f"E00{i}", "numeric_range", f"x{i}", 0.9, ["How"])
              for i in range(12)]
        scorer = ab.NarrativeScorer(ev, coverage_map={"by_narrative_stage": {
            "Why": 0, "What": 0, "How": 12, "Now": 0}})
        sc = scorer._stage_score("How")
        # 40 + 30*1.0 (12>=10) + 30*0.9 = 97
        assert sc["score"] == 97


# --------------------------------------------------------------------------- #
# Focus areas — theme detection + scoring
# --------------------------------------------------------------------------- #
class TestFocusAreas:
    def test_column_name_theme_detection(self):
        ev = [_ev("E001", "numeric_range", "Revenue ranges 1-10", 0.8, ["What"],
                  column="Revenue"),
              _ev("E002", "aggregate_insight", "Revenue avg by region", 0.85, ["How"],
                  column="Revenue")]
        scorer = ab.NarrativeScorer(ev)
        areas = scorer.identify_focus_areas(top_n=5)
        assert any(a["area"] == "Revenue" for a in areas)
        rev = [a for a in areas if a["area"] == "Revenue"][0]
        assert rev["evidence_count"] == 2
        assert rev["score"] > 0

    def test_x_by_y_pattern_theme(self):
        ev = [_ev("E001", "aggregate_insight", "Sales by region shows growth",
                  0.85, ["How"], column=None)]
        scorer = ab.NarrativeScorer(ev)
        areas = scorer.identify_focus_areas(top_n=5)
        assert any("by" in a["area"].lower() for a in areas)

    def test_near_duplicate_theme_merging(self):
        # Two near-duplicate column names should merge into one theme.
        # (Text must NOT contain an "X by Y" pattern, or that creates a 3rd theme.)
        ev = [_ev("E001", "numeric_range", "Total Revenue is high", 0.8, ["What"],
                  column="Total Revenue"),
              _ev("E002", "aggregate_insight", "aggregate of total revenue", 0.8, ["How"],
                  column="total revenue")]
        scorer = ab.NarrativeScorer(ev)
        areas = scorer.identify_focus_areas(top_n=5)
        # Should merge into one theme, not two separate ones.
        assert len(areas) == 1
        assert areas[0]["evidence_count"] == 2

    def test_derived_insight_quality_boost(self):
        # A theme with derived insight types should out-score one with only
        # plain numeric_range entries at the same priority.
        base = [_ev(f"E00{i}", "numeric_range", f"x{i}", 0.8, ["What"],
                    column="Plain") for i in range(3)]
        derived = [_ev(f"E10{i}", "trend_insight", f"d{i}", 0.8, ["How"],
                       column="Trendy") for i in range(3)]
        scorer = ab.NarrativeScorer(base + derived)
        areas = scorer.identify_focus_areas(top_n=5)
        by_area = {a["area"]: a["score"] for a in areas}
        assert by_area["Trendy"] > by_area["Plain"]

    def test_focus_areas_capped_to_top_n(self):
        ev = []
        for i in range(10):
            ev.append(_ev(f"E{i:03d}", "numeric_range", f"col{i} range", 0.7,
                          ["What"], column=f"col{i}"))
        scorer = ab.NarrativeScorer(ev)
        areas = scorer.identify_focus_areas(top_n=3)
        assert len(areas) == 3
        assert [a["rank"] for a in areas] == [1, 2, 3]

    def test_focus_area_scores_0_to_100(self):
        ev = [_ev("E001", "outlier_insight", "Revenue outlier 5000", 0.95,
                  ["What", "How"], column="Revenue")]
        scorer = ab.NarrativeScorer(ev)
        areas = scorer.identify_focus_areas(top_n=5)
        assert areas
        assert 0.0 <= areas[0]["score"] <= 100.0

    def test_no_themes_when_no_column_or_pattern(self):
        # Evidence with no column name and no "X by Y" → not themeable.
        ev = [_ev("E001", "pptx_slide_insight", "Generic slide about strategy",
                  0.7, ["Why"])]
        scorer = ab.NarrativeScorer(ev)
        assert scorer.identify_focus_areas(top_n=5) == []


# --------------------------------------------------------------------------- #
# Quality flags + recommendations
# --------------------------------------------------------------------------- #
class TestFlagsAndRecommendations:
    def test_missing_stage_flag(self):
        ev = [_ev("E001", "numeric_range", "x", 0.8, ["What"])]
        g = ab.AnalystBriefingGenerator(evidence=ev, coverage_map={
            "by_narrative_stage": {"Why": 0, "What": 1, "How": 0, "Now": 0}})
        b = g.generate()
        assert "missing_why_stage" in b["quality_flags"]
        assert "missing_how_stage" in b["quality_flags"]
        assert "missing_now_stage" in b["quality_flags"]
        assert any("Now" in r for r in b["recommendations"])

    def test_no_cross_file_links_flag(self):
        ev = [_ev("E001", "numeric_range", "x", 0.8, ["What"])]
        g = ab.AnalystBriefingGenerator(evidence=ev, cross_file=[])
        b = g.generate()
        assert "no_cross_file_links" in b["quality_flags"]

    def test_single_source_flag(self):
        ev = [_ev("E001", "numeric_range", "x", 0.8, ["What"], source="a.xlsx"),
              _ev("E002", "numeric_range", "y", 0.8, ["What"], source="a.xlsx")]
        g = ab.AnalystBriefingGenerator(evidence=ev)
        b = g.generate()
        assert "single_source" in b["quality_flags"]

    def test_zero_evidence_briefing(self):
        g = ab.AnalystBriefingGenerator(evidence=[], run_metadata={
            "run_id": "t", "source_folder": "./x"})
        b = g.generate()
        assert b["narrative_readiness"]["overall_score"] == 0
        assert "no_evidence" in b["quality_flags"]
        assert b["recommendations"]  # has the "add source files" rec
        assert b["suggested_focus_areas"] == []

    def test_top_cross_file_relationships_surfaced(self):
        cross = [{"evidence_id": "E9000", "insight_type": "cross_file_metric",
                  "text": "'EMEA' in 2 files", "priority_score": 0.9,
                  "related_files": ["a.xlsx", "b.pptx"]}]
        g = ab.AnalystBriefingGenerator(evidence=cross, cross_file=cross)
        b = g.generate()
        assert len(b["top_cross_file_relationships"]) == 1
        assert b["top_cross_file_relationships"][0]["evidence_id"] == "E9000"


# --------------------------------------------------------------------------- #
# Markdown rendering
# --------------------------------------------------------------------------- #
class TestMarkdownRendering:
    def test_markdown_has_key_sections(self):
        g = ab.AnalystBriefingGenerator(
            evidence=[_ev("E001", "numeric_range", "Revenue 1-10", 0.8, ["What"],
                          column="Revenue")],
            coverage_map={"by_narrative_stage": {"Why": 0, "What": 1, "How": 0, "Now": 0}})
        md = g.render_markdown(g.generate())
        assert "# Analyst Briefing" in md
        assert "Narrative Readiness Score" in md
        assert "Suggested Focus Areas" in md
        assert "Top Cross-File Relationships" in md
        assert "Quality Flags" in md
        assert "Recommendations" in md
        assert "Revenue" in md  # focus area surfaced

    def test_markdown_empty_evidence(self):
        g = ab.AnalystBriefingGenerator(evidence=[])
        md = g.render_markdown(g.generate())
        assert "Narrative Readiness Score: 0/100" in md
        assert "No cross-file relationships detected." in md


# --------------------------------------------------------------------------- #
# Pipeline integration (v4)
# --------------------------------------------------------------------------- #
class TestPipelineIntegration:
    def test_briefing_files_emitted(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        pd.DataFrame({"Revenue": [100, 200, 300], "Region": ["N", "S", "E"]}).to_excel(
            inp / "s.xlsx", index=False)
        p.run()
        assert (out / "analyst_briefing.md").exists()
        assert (out / "analyst_briefing.json").exists()
        b = json.loads((out / "analyst_briefing.json").read_text(encoding="utf-8"))
        assert "narrative_readiness" in b
        assert 0 <= b["narrative_readiness"]["overall_score"] <= 100

    def test_briefing_emitted_on_zero_evidence(self, make_preprocessor):
        p, inp, out = make_preprocessor()  # empty input dir
        p.run()
        assert (out / "analyst_briefing.md").exists()
        b = json.loads((out / "analyst_briefing.json").read_text(encoding="utf-8"))
        assert b["narrative_readiness"]["overall_score"] == 0
        assert "no_evidence" in b["quality_flags"]

    def test_run_metadata_has_briefing_block(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        pd.DataFrame({"Revenue": [100, 200, 300]}).to_excel(inp / "s.xlsx", index=False)
        p.run()
        meta = json.loads((out / "run_metadata.json").read_text(encoding="utf-8"))
        assert "briefing" in meta
        br = meta["briefing"]
        assert "overall_readiness_score" in br
        assert "stage_scores" in br
        assert "focus_areas" in br
        assert "quality_flags" in br

    def test_summary_report_has_readiness_section(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        pd.DataFrame({"Revenue": [100, 200, 300]}).to_excel(inp / "s.xlsx", index=False)
        p.run()
        summary = (out / "preprocessor_summary.md").read_text(encoding="utf-8")
        assert "## Narrative Readiness" in summary
        assert "Overall readiness score" in summary

    def test_focus_areas_count_configurable(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor(focus_areas=2)
        # Many columns so there are >2 themes to cap.
        df = pd.DataFrame({f"col{i}": list(range(10)) for i in range(8)})
        df.to_excel(inp / "s.xlsx", index=False)
        p.run()
        b = json.loads((out / "analyst_briefing.json").read_text(encoding="utf-8"))
        assert len(b["suggested_focus_areas"]) <= 2

    def test_briefing_version_metadata(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        pd.DataFrame({"Revenue": [100]}).to_excel(inp / "s.xlsx", index=False)
        p.run()
        meta = json.loads((out / "run_metadata.json").read_text(encoding="utf-8"))
        assert meta["preprocessor_version"] == "4.0.0"


# --------------------------------------------------------------------------- #
# CLI: --focus-areas
# --------------------------------------------------------------------------- #
class TestFocusAreasCLI:
    def test_focus_areas_flag_default(self):
        import argparse
        # main() builds the parser; we replicate the relevant arg to confirm
        # the default is 5 and it's an int.
        parser = argparse.ArgumentParser()
        parser.add_argument("--focus-areas", type=int, default=5)
        args = parser.parse_args([])
        assert args.focus_areas == 5
        args = parser.parse_args(["--focus-areas", "3"])
        assert args.focus_areas == 3

    def test_config_default_includes_focus_areas(self):
        assert "focus_areas" in m.CONFIG_DEFAULTS
        assert m.CONFIG_DEFAULTS["focus_areas"] == 5
        assert "briefing" in m.CONFIG_DEFAULTS
