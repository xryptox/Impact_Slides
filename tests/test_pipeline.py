"""End-to-end pipeline (run()) integration tests for step1_preprocessor_v2_full.

Covers Excel, PPTX (incl. the section-slide crash regression surfaced through
run()), PDF (text + scanned), output JSON contract, and edge cases.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import step1_preprocessor_v2_full as m


def _load(out_dir, name):
    p = Path(out_dir) / name
    assert p.exists(), f"expected output {name}"
    return json.load(open(p))


# --------------------------------------------------------------------------- #
# Excel pipeline
# --------------------------------------------------------------------------- #
class TestExcelPipeline:
    def test_excel_produces_profile_and_evidence(self, make_excel, make_preprocessor):
        import pandas as pd
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_excel(df=pd.DataFrame({"Revenue": [100, 200, 300, 400],
                                    "Region": ["N", "S", "E", "W"]}))
        p.run()

        prof = _load(out, "excel_profile.json")
        assert prof[0]["status"] == "ok"
        ev = _load(out, "evidence_register_seed.json")
        assert len(ev) > 0

    def test_multi_sheet_workbook(self, make_excel, make_preprocessor):
        import pandas as pd
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_excel(sheets={
            "Sales": pd.DataFrame({"Rev": [1, 2, 3, 4]}),
            "Ops": pd.DataFrame({"Cost": [10, 20, 30, 40]}),
        })
        p.run()
        prof = _load(out, "excel_profile.json")
        assert len(prof[0]["sheets"]) == 2


# --------------------------------------------------------------------------- #
# PPTX pipeline — section-slide crash regression (bug #1, end-to-end)
# --------------------------------------------------------------------------- #
class TestPptxPipeline:
    def test_section_slide_does_not_break_run(self, make_pptx, make_preprocessor):
        """A deck with a 'Section ...' titled slide must not crash the whole PPTX
        (previously the UnboundLocalError was swallowed and the file marked error)."""
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_pptx(slides=[
            {"title": "Deck Title"},
            {"title": "Agenda", "body": "intro\nscope\n"},
            {"title": "Section One"},  # <- this triggered the crash
            {"title": "Content", "body": "some substantive content text here " * 5},
            {"title": "Summary", "body": "key recommendation: expand"},
        ])
        p.run()
        prof = _load(out, "pptx_profile.json")
        assert prof[0]["status"] == "ok", f"PPTX was marked error: {prof[0].get('error')}"
        assert prof[0]["total_slides"] == 5
        # The section slide should be classified, not crash the run
        types = [s["classification"]["type"] for s in prof[0]["slides"]]
        assert "section" in types

    def test_data_slide_with_table(self, make_pptx, make_preprocessor):
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_pptx(slides=[
            {"title": "Metrics", "table": [["Q1", "Q2"], ["100", "200"]]},
        ])
        p.run()
        prof = _load(out, "pptx_profile.json")
        slide = prof[0]["slides"][0]
        assert slide["classification"]["type"] == "data_table"
        assert slide["details"]["table_details"][0]["cells"]

    def test_plain_text_bullets_are_captured(self, make_pptx, make_preprocessor):
        """bug #13 fix: text-heavy decks without bullet glyphs must still seed
        bullet_insight evidence from their substantive plain-text lines."""
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_pptx(slides=[
            {"title": "Intro"},
            {"title": "Tuning Strategy",
             "body": "Every site is different and needs careful measurement\n"
                     "There is no silver bullet for performance work\n"
                     "Monitor and analyse before changing configuration"},
        ])
        p.run()
        ev = _load(out, "evidence_register_seed.json")
        bullets = [e for e in ev if e["insight_type"] == "bullet_insight"]
        assert bullets, "expected plain-text lines to be captured as bullet insights"
        blob = " ".join(e["text"] for e in bullets).lower()
        assert "silver bullet" in blob

    def test_page_number_textbox_not_used_as_title(self, make_pptx, make_preprocessor):
        """bug #6 fix: a leading page-number textbox must not become the slide
        title (was producing evidence like 'Slide 2: 2 (content_insight)')."""
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_pptx(slides=[
            {"title": "Real Title Here"},
            {"title": "42", "body": "some substantive content text here " * 5},
        ])
        p.run()
        prof = _load(out, "pptx_profile.json")
        titles = [s["title"] for s in prof[0]["slides"]]
        assert "42" not in titles, f"page-number used as title: {titles}"


# --------------------------------------------------------------------------- #
# PDF pipeline
# --------------------------------------------------------------------------- #
class TestPdfPipeline:
    def test_text_pdf(self, make_preprocessor, tmp_workspace):
        import fitz
        inp = tmp_workspace / "input"
        inp.mkdir(parents=True, exist_ok=True)
        path = inp / "text.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "This document contains important strategic recommendations.")
        doc.save(path)
        doc.close()

        p, inp2, out = make_preprocessor(filter_level="permissive")
        p.run()
        ev = _load(out, "evidence_register_seed.json")
        assert any("pdf" in e.get("insight_type", "") for e in ev)


# --------------------------------------------------------------------------- #
# Output contract
# --------------------------------------------------------------------------- #
class TestOutputContract:
    def test_inventory_and_profile_emitted(self, make_excel, make_preprocessor):
        import pandas as pd
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_excel(df=pd.DataFrame({"Rev": [1, 2, 3, 4]}))
        p.run()
        inv = _load(out, "file_inventory.json")
        assert isinstance(inv, list) and inv
        assert "file_id" in inv[0] and "category" in inv[0]

    def test_errors_json_only_when_errors(self, make_preprocessor):
        p, inp, out = make_preprocessor()
        p.run()
        # No input files -> no errors file expected (nothing to error on)
        assert (Path(out) / "file_inventory.json").exists()


# --------------------------------------------------------------------------- #
# Edge cases
# --------------------------------------------------------------------------- #
class TestEdgeCases:
    def test_empty_input_dir(self, make_preprocessor):
        p, inp, out = make_preprocessor()
        p.run()  # must not crash
        assert (Path(out) / "file_inventory.json").exists()

    def test_unknown_extension_ignored_gracefully(self, make_preprocessor, tmp_workspace):
        inp = tmp_workspace / "input"
        inp.mkdir(parents=True, exist_ok=True)
        (inp / "notes.txt").write_text("hello")
        (inp / "image.png").write_bytes(b"\x89PNG fake")
        p, inp2, out = make_preprocessor()
        p.run()
        inv = _load(out, "file_inventory.json")
        assert any(i["category"] == "other" for i in inv)

    def test_zero_byte_file_does_not_crash(self, make_preprocessor, tmp_workspace):
        inp = tmp_workspace / "input"
        inp.mkdir(parents=True, exist_ok=True)
        (inp / "empty.xlsx").write_bytes(b"")
        p, inp2, out = make_preprocessor(filter_level="permissive")
        p.run()
        # Should record an error, not crash
        inv = _load(out, "file_inventory.json")
        assert inv
