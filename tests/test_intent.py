"""
Intent / specification tests for step1_preprocessor_v2_full.py.

Goal of the codebase (per Best Hybrid Workflow.md): seed source-backed insights
from PPTX/Excel/PDF/DOCX into a PRIORITY-ORDERED Evidence Register that the
Impact Slide Analyst GPT treats as "source of truth", with evidence mapped to
the Why -> What -> How -> Now narrative framework and Evidence IDs preserved.

These tests verify the *intent* (the contract the Analyst relies on), not just
internal mechanics:
  - every claim is source-backed & traceable (no fabrication)
  - the register is priority-ordered and the ranking is meaningful
  - useful insights are retained; noise is filtered; filter levels are monotonic
  - evidence is mapped to the Why/What/How/Now framework (incl. the "Now" gap)
  - cross-file relationships are surfaced
  - the handoff files the Analyst needs are all present
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import pytest

import step1_preprocessor_v2_full as m

FRAMEWORK_STAGES = {"Why", "What", "How", "Now"}


# --------------------------------------------------------------------------- #
# Rich scenario fixture: a realistic mixed input that exercises every source
# --------------------------------------------------------------------------- #
@pytest.fixture()
def rich_scenario(make_excel, make_pptx, tmp_workspace):
    """Build Excel + PPTX (chart, table, conclusion) + text PDF, run the
    preprocessor, and return (out_dir, scenario) where `scenario` holds the
    known ground-truth values we later assert against (no-fabrication checks)."""
    import fitz

    inp = tmp_workspace / "input"
    inp.mkdir(parents=True, exist_ok=True)
    out = tmp_workspace / "output"

    # --- Excel: useful cols + noise cols (system col + identifier) ---
    make_excel(name="sales.xlsx", df=pd.DataFrame({
        "S.No": list(range(1, 9)),                      # identifier -> filtered
        "Region": ["North", "South", "East", "West"] * 2,
        "Revenue": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700],
        "created_at": pd.date_range("2024-01-01", periods=8),  # system col -> filtered
    }))

    # --- PPTX with chart, table, and a conclusion slide ---
    make_pptx(name="deck.pptx", slides=[
        {"title": "Q3 Impact Review"},
        {"title": "Revenue by Quarter",
         "chart": {"title": "Revenue", "categories": ["Q1", "Q2"],
                   "series": {"Revenue": [100.0, 200.0]}}},
        {"title": "Regional Table",
         "table": [["Region", "Revenue"], ["North", "1000"]]},
        {"title": "Key Recommendations",
         "body": "• Recommendation: Expand North operations by 40%\n"
                 "• Next step: launch in Q4\n"
                 "• Call to action: invest now"},
    ])

    # --- Text PDF with insight language ---
    pdf_path = inp / "brief.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72),
                     "This quarter showed significant growth. We recommend expansion. "
                     "Record revenue reached a new high. Key risk: supply constraint.")
    doc.save(pdf_path)
    doc.close()

    p = m.ImpactSlidePreprocessorV2(input_path=str(inp), output_dir=str(out),
                                    filter_level="permissive")
    p.run()

    scenario = {
        "out": out,
        "input_files": {"sales.xlsx", "deck.pptx", "brief.pdf"},
        "chart_categories": ["Q1", "Q2"],
        "chart_series": {"Revenue": [100.0, 200.0]},
        "table_cells": ["Region", "Revenue", "North", "1000"],
        "conclusion_title": "Key Recommendations",
        "pdf_phrase": "significant growth",
    }
    return scenario


def _register(scenario):
    return json.load(open(Path(scenario["out"]) / "evidence_register_seed.json"))


# --------------------------------------------------------------------------- #
# A. Source-of-truth / traceability contract
# --------------------------------------------------------------------------- #
class TestSourceBacked:
    def test_every_evidence_has_required_handoff_fields(self, rich_scenario):
        """Analyst needs: evidence_id, source_file, source_location,
        insight_type, text, priority_score, suggested_narrative_use."""
        for ev in _register(rich_scenario):
            for k in ("evidence_id", "source_file", "source_location",
                      "insight_type", "text", "priority_score",
                      "suggested_narrative_use"):
                assert k in ev, f"{ev.get('evidence_id')} missing {k}"

    def test_every_source_file_is_a_real_input(self, rich_scenario):
        real = rich_scenario["input_files"]
        for ev in _register(rich_scenario):
            # cross_file_metric spans multiple files; its related_files must all
            # be real inputs. Single-source evidence must itself be a real input.
            if ev["insight_type"] == "cross_file_metric":
                for f in ev.get("related_files", []):
                    assert f in real, f"cross-file evidence references unknown file {f!r}"
            else:
                assert ev["source_file"] in real, \
                    f"evidence references unknown file {ev['source_file']!r}"

    def test_source_location_is_non_empty(self, rich_scenario):
        for ev in _register(rich_scenario):
            assert ev["source_location"], \
                f"{ev['evidence_id']} has empty source_location"

    def test_evidence_ids_unique_and_well_formed(self, rich_scenario):
        ids = [e["evidence_id"] for e in _register(rich_scenario)]
        assert len(ids) == len(set(ids)), "duplicate evidence_id"
        assert all(re.fullmatch(r"E\d{4}", i) for i in ids), \
            "evidence_id must be E#### (Analyst preserves these)"


# --------------------------------------------------------------------------- #
# B. Priority ordering is real and meaningful
# --------------------------------------------------------------------------- #
class TestPriorityOrdering:
    def test_register_is_sorted_descending(self, rich_scenario):
        scores = [e["priority_score"] for e in _register(rich_scenario)]
        assert scores == sorted(scores, reverse=True)

    def test_data_rich_beats_section_or_title(self, rich_scenario):
        ev = _register(rich_scenario)
        data = [e for e in ev if e["insight_type"] in ("chart_insight", "chart_data_insight")]
        low = [e for e in ev if e["insight_type"] == "section_divider"]
        if data and low:
            assert data[0]["priority_score"] > low[0]["priority_score"]

    def test_conclusion_bullets_rank_above_section_dividers(self, rich_scenario):
        ev = _register(rich_scenario)
        bullets = [e for e in ev if e["insight_type"] == "bullet_insight"]
        sections = [e for e in ev if e["insight_type"] == "section_divider"]
        if bullets and sections:
            assert min(b["priority_score"] for b in bullets) > \
                   max(s["priority_score"] for s in sections)

    def test_insight_language_boosts_pdf_priority(self, rich_scenario):
        ev = _register(rich_scenario)
        pdf = [e for e in ev if "pdf" in e["insight_type"]]
        assert pdf, "expected PDF evidence"
        # The PDF text contains 'recommend'/'significant'/'record' -> high priority
        assert max(e["priority_score"] for e in pdf) >= 0.78


# --------------------------------------------------------------------------- #
# C. No fabrication — evidence text is traceable to source content
# --------------------------------------------------------------------------- #
class TestNoFabrication:
    def test_chart_data_values_match_source(self, rich_scenario):
        ev = [e for e in _register(rich_scenario) if e["insight_type"] == "chart_data_insight"]
        assert ev, "expected chart_data_insight evidence"
        # Every emitted value must be one we actually put in the chart
        all_vals = set()
        for vs in rich_scenario["chart_series"].values():
            all_vals.update(str(v) for v in vs)
        for e in ev:
            # text format: "Q1: 100.0 (Revenue)" — at least one source value present
            assert any(v in e["text"] for v in all_vals), e["text"]

    def test_chart_categories_match_source(self, rich_scenario):
        ev = [e for e in _register(rich_scenario) if e["insight_type"] == "chart_data_insight"]
        cats_seen = {e["text"].split(":")[0] for e in ev}
        assert cats_seen.issubset(set(rich_scenario["chart_categories"]))

    def test_table_cells_match_source(self, rich_scenario):
        ev = [e for e in _register(rich_scenario) if e["insight_type"] == "table_cell"]
        assert ev, "expected table_cell evidence"
        emitted = " ".join(e["text"] for e in ev)
        for cell in rich_scenario["table_cells"]:
            assert cell in emitted, f"source cell {cell!r} not reflected in evidence"

    def test_pdf_evidence_text_derived_from_source(self, rich_scenario):
        ev = [e for e in _register(rich_scenario) if "pdf" in e["insight_type"]]
        assert ev
        # The evidence text is a prefix of real page text -> not fabricated
        assert any("growth" in e["text"].lower() for e in ev)

    def test_evidence_does_not_invent_files(self, rich_scenario):
        """No evidence may reference a file that wasn't an input."""
        real = rich_scenario["input_files"]
        for ev in _register(rich_scenario):
            if ev["insight_type"] == "cross_file_metric":
                assert set(ev.get("related_files", [])).issubset(real)
            else:
                assert ev["source_file"] in real


# --------------------------------------------------------------------------- #
# D. Useful insight retention + noise filtering
# --------------------------------------------------------------------------- #
class TestRetentionAndFiltering:
    def test_useful_insights_survive_permissive(self, rich_scenario):
        types = {e["insight_type"] for e in _register(rich_scenario)}
        # These are the high-value seed categories the Analyst needs
        assert "chart_data_insight" in types
        assert "table_cell" in types
        assert "bullet_insight" in types

    def test_identifier_and_system_columns_filtered(self, make_preprocessor, make_excel):
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_excel(df=pd.DataFrame({
            "S.No": list(range(1, 11)),
            "created_at": pd.date_range("2024-01-01", periods=10),
            "Revenue": [i * 100 for i in range(1, 11)],
        }))
        p.run()
        ev = json.load(open(out / "evidence_register_seed.json"))
        text_blob = " ".join(e["text"] for e in ev).lower()
        # Identifier & system columns must NOT appear as evidence columns
        assert "s.no" not in text_blob
        assert "created_at" not in text_blob
        # but the real business column should
        assert "revenue" in text_blob

    def test_metric_incrementing_by_one_is_retained(self, make_preprocessor, make_excel):
        """Regression: a real metric that happens to increment by exactly 1
        must NOT be misfiltered as an identifier column. Previously the
        +1 sequential-diff heuristic dropped it; now it survives as evidence."""
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_excel(df=pd.DataFrame({
            "Region": ["North", "South", "East", "West", "North", "South", "East", "West"],
            "Units": [1, 2, 3, 4, 5, 6, 7, 8],   # +1 sequential metric
        }))
        p.run()
        ev = json.load(open(out / "evidence_register_seed.json"))
        assert any(e["column_name"] == "Units" for e in ev
                   if e.get("insight_type") == "numeric_range"), \
            "metric 'Units' incrementing by 1 must be retained, not filtered as an ID"

    def test_filter_levels_are_monotonic(self, make_preprocessor, make_excel):
        """permissive >= moderate >= conservative in evidence count."""
        make_excel(df=pd.DataFrame({
            "Region": ["N", "S", "E", "W", "N", "S", "E", "W"],
            "Revenue": [100, 200, 150, 300, 250, 180, 220, 310],
            "Notes": [f"free text {i}" for i in range(8)],  # high cardinality
        }))

        def run(level):
            # fresh preprocessor per level, same input file
            p, _, out = make_preprocessor(filter_level=level)
            p.run()
            return len(json.load(open(out / "evidence_register_seed.json")))

        n_perm = run("permissive")
        n_mod = run("moderate")
        n_cons = run("conservative")
        assert n_perm >= n_mod >= n_cons


# --------------------------------------------------------------------------- #
# E. Why -> What -> How -> Now framework mapping
# --------------------------------------------------------------------------- #
class TestFrameworkMapping:
    def test_narrative_use_subset_of_framework(self, rich_scenario):
        for ev in _register(rich_scenario):
            use = set(ev["suggested_narrative_use"])
            assert use.issubset(FRAMEWORK_STAGES), \
                f"{ev['evidence_id']} uses non-framework stages {use - FRAMEWORK_STAGES}"

    def test_conclusion_evidence_is_tagged_with_now(self, rich_scenario):
        """GAP-UNDER-TEST: conclusion / recommendation / next-step / call-to-action
        content must feed the 'Now' stage of the Why->What->How->Now structure.
        Currently the code never assigns 'Now'."""
        ev = _register(rich_scenario)
        conclusion_ev = [e for e in ev
                         if e["insight_type"] == "bullet_insight"
                         or "Key Recommendations" in e.get("text", "")]
        assert conclusion_ev, "expected conclusion-derived evidence"
        now_tagged = [e for e in conclusion_ev if "Now" in e["suggested_narrative_use"]]
        assert now_tagged, "conclusion/recommendation evidence must map to the 'Now' stage"

    def test_numeric_data_evidence_maps_to_what_or_how(self, rich_scenario):
        ev = _register(rich_scenario)
        data = [e for e in ev if e["insight_type"] in
                ("chart_data_insight", "numeric_range", "table_cell")]
        for e in data:
            assert set(e["suggested_narrative_use"]) & {"What", "How"}


# --------------------------------------------------------------------------- #
# F. Cross-file relationship surfacing
# --------------------------------------------------------------------------- #
class TestCrossFile:
    def test_shared_entity_surfaced_across_excel_and_pptx(self, make_preprocessor,
                                                          make_excel, make_pptx):
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_excel(df=pd.DataFrame({"Region": ["North", "South", "East", "West"] * 2,
                                    "Revenue": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700]}))
        make_pptx(slides=[
            {"title": "Regional Review"},
            {"title": "North Region Performance",
             "body": "North region grew strongly this quarter. North delivered record "
                     "revenue and outperformed every other region across all key metrics."},
        ])
        p.run()
        ev = json.load(open(out / "evidence_register_seed.json"))
        cross = [e for e in ev if e["insight_type"] == "cross_file_metric"]
        assert cross, "expected a cross-file relationship for shared entity 'North'"
        # cross-file evidence must be source-backed with real filenames
        for c in cross:
            assert c.get("related_files"), "cross-file evidence must list related files"


# --------------------------------------------------------------------------- #
# G. Handoff contract — files the Analyst GPT consumes
# --------------------------------------------------------------------------- #
class TestAnalystHandoff:
    def test_required_output_files_present(self, rich_scenario):
        out = Path(rich_scenario["out"])
        for name in ("file_inventory.json", "excel_profile.json",
                     "evidence_register_seed.json", "preprocessor_summary.md"):
            assert (out / name).exists(), f"missing handoff file {name}"

    def test_pptx_profile_present_when_pptx_input(self, rich_scenario):
        assert (Path(rich_scenario["out"]) / "pptx_profile.json").exists()

    def test_register_is_valid_json_list(self, rich_scenario):
        data = _register(rich_scenario)
        assert isinstance(data, list) and data

    def test_summary_report_lists_evidence_count(self, rich_scenario):
        report = (Path(rich_scenario["out"]) / "preprocessor_summary.md").read_text()
        assert "Evidence Register" in report
        assert "Total evidence entries" in report


# --------------------------------------------------------------------------- #
# H. Scanned-PDF insight retention (OCR path must retain useful content)
# --------------------------------------------------------------------------- #
class TestScannedPdfRetention:
    def test_ocr_retains_scanned_insight_for_analyst(self, real_scanned_pdf, tmp_workspace):
        if not m.pytesseract:
            pytest.skip("pytesseract not installed")
        # confirm tesseract binary is reachable
        pp = m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_x")
        pp._ocr_available = None
        if not pp._ensure_tesseract():
            pytest.skip("Tesseract binary not available")

        import shutil
        inp = tmp_workspace / "input"
        out = tmp_workspace / "output"
        inp.mkdir(parents=True, exist_ok=True)
        shutil.copy(real_scanned_pdf, inp / "scan.pdf")
        p = m.ImpactSlidePreprocessorV2(input_path=str(inp), output_dir=str(out),
                                        filter_level="permissive")
        p.enable_ocr = True
        p._ocr_available = None
        p.tesseract_cmd = None
        p.run()
        ev = json.load(open(out / "evidence_register_seed.json"))
        ocr_ev = [e for e in ev if e.get("ocr_used")]
        assert ocr_ev, "OCR must retain scanned-page insights for the Analyst"
        # retained OCR evidence is source-backed
        for e in ocr_ev:
            assert e["source_file"] == "scan.pdf"
            assert e["source_location"].startswith("Page")
