"""
Regression tests for step1_preprocessor_v3.py — the five insight-quality
enhancements over v2:

  #1  trend / delta insights across time-ordered spreadsheet sheets
  #2  cross-sheet consolidation of repeated numeric ranges
  #3  per-bullet insight-language ranking (no more flat-0.75 bullet scores)
  #4  coverage map (Why/What/How/Now + per-source) emitted as a handoff file
  #5  computed group-by aggregate insights (not just suggestions)
  #6  extraction_method provenance on every evidence
  #7  CSV export of the full field set
  #8  per (source_file, insight_type) caps so one source can't flood
  #9  reliability-based confidence (computed/chart high, OCR/bullet medium)
  #10 semantic near-dup dedup (rephrasings collapse)
  #11 PPTX navigation/section-header text filtered out of bullets
  #12 top-entities summary (per Excel categorical column) handoff file

Plus the inherited v2 contracts (source-backing, priority sorting, framework
mapping, no cross-file flooding, no noise at top) still hold.

Real-data tests use the downloaded files in realworld_test/input/ and skip if
absent; synthetic tests build minimal fixtures so they run anywhere.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import pytest

import step1_preprocessor_v3 as m

REAL_DIR = Path(r"C:\Users\Ag1Le\Documents\realworld_test\input")
XLSX = REAL_DIR / "supermarket_sales.xlsx"
PPTX = REAL_DIR / "Performance.pptx"


def _have_real_files():
    return XLSX.is_file() and PPTX.is_file()


@pytest.fixture()
def make_preprocessor(tmp_workspace):
    """Override of conftest's fixture that builds a v3 preprocessor (same tmp
    workspace, same input/output layout) so v3 tests run against v3 code."""
    def _make(filter_level="moderate", boost_keywords=None, enable_ocr=False):
        inp = tmp_workspace / "input"
        out = tmp_workspace / "output"
        inp.mkdir(parents=True, exist_ok=True)
        p = m.ImpactSlidePreprocessorV2(
            input_path=str(inp),
            output_dir=str(out),
            filter_level=filter_level,
            boost_keywords=boost_keywords or [],
        )
        p.enable_ocr = enable_ocr
        return p, inp, out
    return _make


@pytest.fixture(scope="module")
def real_run(tmp_path_factory):
    if not _have_real_files():
        pytest.skip("real-world test files not downloaded")
    out = tmp_path_factory.mktemp("v3_real_out")
    p = m.ImpactSlidePreprocessorV2(input_path=str(REAL_DIR), output_dir=str(out),
                                    filter_level="permissive")
    p.run()
    return out


def _ev(out):
    return json.load(open(out / "evidence_register_seed.json"))


# --------------------------------------------------------------------------- #
# New module-level helpers (sheet_time_rank, insight_priority_boost)
# --------------------------------------------------------------------------- #
class TestSheetTimeRank:
    @pytest.mark.parametrize("name,rank", [
        ("January", 1), ("February", 2), ("Mar", 3), ("december", 12),
        ("Q1", 100), ("Q4", 400), ("2023", 20230000), ("2024 Sales", 20240000),
    ])
    def test_time_ordered(self, name, rank):
        assert m.sheet_time_rank(name) == rank

    @pytest.mark.parametrize("name", ["Sheet1", "Data", "Summary", "Raw", ""])
    def test_not_time_ordered(self, name):
        assert m.sheet_time_rank(name) is None


class TestInsightPriorityBoost:
    def test_no_keywords_no_boost(self):
        assert m.insight_priority_boost("set up monitoring tools", 0.75) == 0.75

    def test_insight_keywords_boost_proportionally(self):
        assert m.insight_priority_boost("Recommendation: expand", 0.75) > 0.75
        # 5 insight keywords -> max boost, capped at 0.98
        assert m.insight_priority_boost("critical significant growth risk decline", 0.75) == 0.98

    def test_cap_at_098(self):
        assert m.insight_priority_boost("recommend critical significant growth risk", 0.95) == 0.98


# --------------------------------------------------------------------------- #
# #1 + #2 — trends + cross-sheet consolidation (synthetic)
# --------------------------------------------------------------------------- #
class TestTrendAndConsolidation:
    def _make_time_workbook(self, make_excel):
        # 3 monthly sheets with a rising 'Revenue' column -> trend should fire
        make_excel(sheets={
            "January": pd.DataFrame({"Region": ["N", "S", "E", "W"],
                                     "Revenue": [100, 110, 120, 130]}),
            "February": pd.DataFrame({"Region": ["N", "S", "E", "W"],
                                      "Revenue": [150, 160, 170, 180]}),
            "March": pd.DataFrame({"Region": ["N", "S", "E", "W"],
                                   "Revenue": [200, 210, 220, 230]}),
        })

    def test_trend_insight_emitted_for_time_ordered_sheets(self, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor(filter_level="permissive")
        self._make_time_workbook(make_excel)
        p.run()
        ev = _ev(out)
        trends = [e for e in ev if e["insight_type"] == "trend_insight"]
        assert trends, "expected trend_insight for rising Revenue across Jan/Feb/Mar"
        rev_trend = [t for t in trends if t.get("column_name") == "Revenue"]
        assert rev_trend, "expected a Revenue trend"
        assert "increase" in rev_trend[0]["text"].lower()
        # trend is high-priority What/How/Why evidence
        assert rev_trend[0]["priority_score"] >= 0.85
        assert "How" in rev_trend[0]["suggested_narrative_use"]

    def test_cross_sheet_ranges_consolidated(self, make_excel, make_preprocessor):
        """Previously 3 sheets -> 3 near-identical 'Revenue ranges from...' entries.
        Now the trend subsumes them into 1 representative range + 1 trend."""
        p, inp, out = make_preprocessor(filter_level="permissive")
        self._make_time_workbook(make_excel)
        p.run()
        ev = _ev(out)
        rev_ranges = [e for e in ev
                      if e["insight_type"] == "numeric_range"
                      and e.get("column_name") == "Revenue"]
        assert len(rev_ranges) <= 1, \
            f"Revenue ranges should be consolidated to ≤1, got {len(rev_ranges)}"

    def test_non_time_sheets_not_consolidated(self, make_excel, make_preprocessor):
        """Without time-ordered sheet names, no trend fires and per-sheet ranges remain."""
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_excel(sheets={
            "North": pd.DataFrame({"Revenue": [100, 200, 300]}),
            "South": pd.DataFrame({"Revenue": [400, 500, 600]}),
        })
        p.run()
        ev = _ev(out)
        assert not [e for e in ev if e["insight_type"] == "trend_insight"]


# --------------------------------------------------------------------------- #
# #3 — per-bullet insight ranking (synthetic)
# --------------------------------------------------------------------------- #
class TestPerBulletRanking:
    def test_insight_bullets_outrank_generic_ones(self, make_pptx, make_preprocessor):
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_pptx(slides=[
            {"title": "Intro"},
            {"title": "Key Recommendations",
             "body": "• Recommendation: expand North operations\n"
                     "• Critical risk: supply constraint\n"
                     "• Set up monitoring tools"},  # generic, no insight language
        ])
        p.run()
        ev = _ev(out)
        bullets = [e for e in ev if e["insight_type"] == "bullet_insight"]
        assert len(bullets) >= 3
        by_text = {e["text"]: e["priority_score"] for e in bullets}
        rec = by_text.get("Recommendation: expand North operations", 0)
        risk = by_text.get("Critical risk: supply constraint", 0)
        generic = by_text.get("Set up monitoring tools", 1)
        assert rec > generic, "insight bullet should outrank generic bullet"
        assert risk > generic
        # and they no longer share a single flat score
        assert len(set(by_text.values())) >= 2


# --------------------------------------------------------------------------- #
# #4 — coverage map (synthetic + real)
# --------------------------------------------------------------------------- #
class TestCoverageMap:
    def test_coverage_map_file_emitted(self, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_excel(df=pd.DataFrame({"Region": ["N", "S"] * 4, "Revenue": [1, 2] * 4}))
        p.run()
        cm = json.load(open(out / "coverage_map.json"))
        assert cm["total_evidence"] > 0
        assert set(cm["by_narrative_stage"]) == {"Why", "What", "How", "Now"}
        assert "by_source_file" in cm
        assert "avg_priority" in cm

    def test_coverage_map_flags_missing_stage(self, make_pptx, make_preprocessor):
        """A deck with no conclusion/recommendation content should flag 'Now' missing."""
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_pptx(slides=[{"title": "Intro"}, {"title": "Facts", "body": "some data here " * 5}])
        p.run()
        cm = json.load(open(out / "coverage_map.json"))
        assert "Now" in cm["stages_with_no_evidence"]


# --------------------------------------------------------------------------- #
# #5 — computed aggregate insights (synthetic)
# --------------------------------------------------------------------------- #
class TestAggregateInsights:
    def test_aggregate_emitted_for_numeric_by_categorical(self, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_excel(df=pd.DataFrame({
            "Branch": ["A", "B", "A", "B", "A", "B"],
            "Revenue": [100, 200, 150, 250, 120, 300],
        }))
        p.run()
        ev = _ev(out)
        aggs = [e for e in ev if e["insight_type"] == "aggregate_insight"]
        assert aggs, "expected a group-by aggregate insight"
        rev_agg = [a for a in aggs if a.get("column_name") == "Revenue"]
        assert rev_agg
        # text must contain actual per-group totals (A=..., B=...)
        assert "A=" in rev_agg[0]["text"] and "B=" in rev_agg[0]["text"]
        assert rev_agg[0]["priority_score"] >= 0.80


# --------------------------------------------------------------------------- #
# Real-world regressions (uses downloaded files; skips if absent)
# --------------------------------------------------------------------------- #
class TestRealWorldV3:
    def test_trends_present_on_supermarket_workbook(self, real_run):
        ev = _ev(real_run)
        trends = [e for e in ev if e["insight_type"] == "trend_insight"]
        assert trends, "expected trend insights across Jan/Feb/Mar sheets"
        # Total should show a trend
        assert any(t.get("column_name") == "Total" for t in trends)

    def test_numeric_ranges_consolidated_vs_v2(self, real_run):
        """v2 produced 23 numeric_range entries (7 cols × 3 sheets + dupes).
        v3 consolidates trend columns so far fewer remain."""
        ev = _ev(real_run)
        nr = [e for e in ev if e["insight_type"] == "numeric_range"]
        # 7 columns had trends; only the non-trend / representative ones remain
        assert len(nr) < 10, f"expected heavy consolidation, got {len(nr)} ranges"

    def test_aggregate_insights_present_on_supermarket(self, real_run):
        ev = _ev(real_run)
        aggs = [e for e in ev if e["insight_type"] == "aggregate_insight"]
        assert aggs, "expected group-by aggregates (e.g. Revenue by Branch)"

    def test_coverage_map_file_present_and_complete(self, real_run):
        cm = json.load(open(real_run / "coverage_map.json"))
        assert cm["total_evidence"] > 50  # caps reduce count; still substantial
        assert set(cm["by_narrative_stage"]) == {"Why", "What", "How", "Now"}
        assert "supermarket_sales.xlsx" in cm["by_source_file"]

    def test_inherited_contracts_hold(self, real_run):
        """v2 contracts still hold: source-backed, sorted, unique IDs, framework-mapped."""
        ev = _ev(real_run)
        for e in ev:
            assert e.get("source_file") and e.get("source_location")
            assert set(e["suggested_narrative_use"]).issubset({"Why", "What", "How", "Now"})
        ids = [e["evidence_id"] for e in ev]
        assert len(ids) == len(set(ids))
        assert all(re.fullmatch(r"E\d{4}", i) for i in ids)
        scores = [e["priority_score"] for e in ev]
        assert scores == sorted(scores, reverse=True)

    def test_no_noise_at_top(self, real_run):
        ev = _ev(real_run)
        for e in ev[:5]:
            for n in ("222.127", "Mozilla", "HTTP/1.1", "GET /"):
                assert n not in e["text"]


# --------------------------------------------------------------------------- #
# #6 — extraction_method provenance (synthetic + real)
# --------------------------------------------------------------------------- #
class TestProvenance:
    def test_every_evidence_has_method(self, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_excel(df=pd.DataFrame({"Region": ["N", "S"] * 4, "Revenue": [1, 2] * 4}))
        p.run()
        ev = _ev(out)
        assert ev
        for e in ev:
            assert "extraction_method" in e
            assert e["extraction_method"] in {
                "computed", "chart_data", "numeric_range", "categorical",
                "table_cell", "text_layer", "ocr", "bullet", "paragraph",
                "cross_file", "classifier", "unknown"}

    def test_trend_and_aggregate_are_computed(self, real_run):
        ev = _ev(real_run)
        for e in ev:
            if e["insight_type"] in ("trend_insight", "aggregate_insight"):
                assert e["extraction_method"] == "computed"


# --------------------------------------------------------------------------- #
# #7 — CSV export full field set
# --------------------------------------------------------------------------- #
class TestCsvExport:
    def test_csv_has_full_field_set(self, make_excel, make_preprocessor):
        import csv
        p, inp, out = make_preprocessor(filter_level="permissive")
        p.export_csv = True
        make_excel(df=pd.DataFrame({"Region": ["N", "S"] * 4, "Revenue": [1, 2] * 4}))
        p.run()
        with open(out / "evidence_register.csv") as f:
            header = next(csv.reader(f))
        # key fields that v2's CSV dropped must now be present
        for field in ("evidence_id", "source_file", "column_name",
                      "extraction_method", "confidence", "suggested_narrative_use",
                      "source_location"):
            assert field in header, f"CSV missing {field}"


# --------------------------------------------------------------------------- #
# #8 — per (source, type) caps
# --------------------------------------------------------------------------- #
class TestPerTypeCaps:
    def test_bullets_capped(self, make_pptx, make_preprocessor):
        """A deck with many bullets on one slide must cap bullet_insight entries."""
        p, inp, out = make_preprocessor(filter_level="permissive")
        # 30 distinct substantive lines on one content slide
        body = "\n".join(f"Insight point number {i} about growth and revenue" for i in range(30))
        make_pptx(slides=[{"title": "Intro"}, {"title": "Findings", "body": body}])
        p.run()
        ev = _ev(out)
        n = sum(1 for e in ev if e["insight_type"] == "bullet_insight")
        assert n <= 20, f"bullet_insight should be capped at 20, got {n}"

    def test_caps_keep_highest_priority(self, make_pptx, make_preprocessor):
        p, inp, out = make_preprocessor(filter_level="permissive")
        body = ("• Recommendation: critical growth action\n"
                + "\n".join(f"Generic point number {i} here" for i in range(25)))
        make_pptx(slides=[{"title": "Intro"}, {"title": "Findings", "body": body}])
        p.run()
        ev = _ev(out)
        bullets = [e for e in ev if e["insight_type"] == "bullet_insight"]
        # the insight-bearing bullet must survive the cap
        assert any("Recommendation" in e["text"] for e in bullets)


# --------------------------------------------------------------------------- #
# #9 — reliability-based confidence
# --------------------------------------------------------------------------- #
class TestConfidenceModel:
    def test_computed_is_high_bullet_is_medium(self, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_excel(sheets={
            "January": pd.DataFrame({"Region": ["N", "S", "E", "W"], "Revenue": [1, 2, 3, 4]}),
            "February": pd.DataFrame({"Region": ["N", "S", "E", "W"], "Revenue": [5, 6, 7, 8]}),
            "March": pd.DataFrame({"Region": ["N", "S", "E", "W"], "Revenue": [9, 10, 11, 12]}),
        })
        p.run()
        ev = _ev(out)
        for e in ev:
            if e["extraction_method"] == "computed":
                assert e["confidence"] == "high"
            if e["extraction_method"] == "numeric_range":
                assert e["confidence"] == "high"

    def test_confidence_for_method_helper(self):
        assert m.confidence_for_method("computed") == "high"
        assert m.confidence_for_method("chart_data") == "high"
        assert m.confidence_for_method("ocr") == "medium"
        assert m.confidence_for_method("bullet") == "medium"
        assert m.confidence_for_method("unknown") == "medium"


# --------------------------------------------------------------------------- #
# #10 — semantic near-dup dedup
# --------------------------------------------------------------------------- #
class TestSemanticDedup:
    def test_rephrasings_collapse(self):
        pp = m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_x")
        evs = [
            {"evidence_id": "E1", "insight_type": "bullet_insight",
             "text": "Recommendation: expand North operations", "priority_score": 0.9,
             "suggested_narrative_use": ["Now"]},
            {"evidence_id": "E2", "insight_type": "bullet_insight",
             "text": "Recommend expanding North operations", "priority_score": 0.7,
             "suggested_narrative_use": ["Now"]},
            {"evidence_id": "E3", "insight_type": "bullet_insight",
             "text": "Totally different insight about revenue", "priority_score": 0.8,
             "suggested_narrative_use": ["What"]},
        ]
        out = pp._deduplicate_evidence(evs)
        assert len(out) == 2
        texts = [o["text"] for o in out]
        assert "Recommendation: expand North operations" in texts  # higher prio kept
        assert "Recommend expanding North operations" not in texts  # near-dup dropped
        assert "Totally different insight about revenue" in texts   # distinct kept

    def test_distinct_insights_not_collapsed(self):
        pp = m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_x")
        evs = [
            {"evidence_id": "E1", "insight_type": "bullet_insight",
             "text": "Revenue grew strongly in Q3", "priority_score": 0.8,
             "suggested_narrative_use": ["What"]},
            {"evidence_id": "E2", "insight_type": "bullet_insight",
             "text": "Profit margins declined in the south", "priority_score": 0.8,
             "suggested_narrative_use": ["What"]},
        ]
        assert len(pp._deduplicate_evidence(evs)) == 2


# --------------------------------------------------------------------------- #
# #11 — PPTX navigation/section-header filtering
# --------------------------------------------------------------------------- #
class TestNavTextFilter:
    def test_repeated_footer_dropped_unique_insights_kept(self, make_pptx, make_preprocessor):
        p, inp, out = make_preprocessor(filter_level="permissive")
        slides = [{"title": "Intro"}]
        for i in range(6):
            slides.append({
                "title": f"Slide {i+1} Title",
                "body": ("Confidential Internal Use Only Do Not Distribute here\n"
                         f"Unique real insight number {i+1} about quarterly revenue growth"),
            })
        make_pptx(slides=slides)
        p.run()
        ev = _ev(out)
        blob = " ".join(e["text"] for e in ev)
        assert "Confidential Internal Use Only" not in blob  # repeated footer dropped
        assert "quarterly revenue growth" in blob             # unique insights kept


# --------------------------------------------------------------------------- #
# #12 — top-entities summary
# --------------------------------------------------------------------------- #
class TestEntitiesSummary:
    def test_entities_summary_file_emitted(self, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_excel(df=pd.DataFrame({"Branch": ["A", "B", "A", "B", "A", "C"],
                                    "Revenue": [1, 2, 3, 4, 5, 6]}))
        p.run()
        es = json.load(open(out / "entities_summary.json"))
        assert es
        branch = [e for e in es if e["column"] == "Branch"][0]
        assert branch["unique_count"] == 3
        values = [v["value"] for v in branch["top_values"]]
        assert "A" in values and "B" in values
        # share_pct sums to ~100
        assert abs(sum(v["share_pct"] for v in branch["top_values"]) - 100.0) < 1.0

    def test_entities_summary_on_real_supermarket(self, real_run):
        es = json.load(open(real_run / "entities_summary.json"))
        assert len(es) > 5
        cols = {e["column"] for e in es}
        assert "Branch" in cols or "City" in cols or "Product line" in cols
