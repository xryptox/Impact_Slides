"""
Template: run the preprocessor's quality contracts against YOUR own source files.

Drop any Excel / PPTX / PDF / DOCX files into a folder, point this test at it,
and the suite will validate that the preprocessor produces a well-formed,
source-backed, priority-ordered Evidence Register from your files — the same
contracts the Analyst GPT relies on.

USAGE
-----
1. Put your files in a folder, e.g.  C:/Users/Ag1Le/Documents/my_files/
2. Set the folder one of two ways:
     a) env var:   set MY_FILES=C:/Users/Ag1Le/Documents/my_files
     b) edit the MY_FILES_DIR constant below.
3. Run:
     python -m pytest tests/test_my_files.py -v

WHAT IT CHECKS (generic, works on any input)
--------------------------------------------
- run() does not crash
- all expected handoff JSON files are produced
- evidence_register_seed.json is a valid, non-empty list
- every evidence is source-backed (real file + non-empty source_location)
- evidence IDs are unique and well-formed (E####)
- register is sorted by priority descending
- suggested_narrative_use values are within the Why/What/How/Now framework
- numeric cross-file false positives are not flooding the register
- noisy table cells (IPs/URLs/user-agents) are not at the very top

NOTE: This is a smoke/contract test, not a correctness oracle — it can't know
whether your *specific* insights are "right", only that the structure the
Analyst needs is sound. To inspect actual insight quality, open
evidence_register_seed.json and preprocessor_summary.md in the output folder
(the test prints where they were written).
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

import step1_preprocessor_v2_full as m

# ---- Point this at your own folder of source files ----------------------- #
MY_FILES_DIR = Path(os.environ.get(
    "MY_FILES",
    r"C:\Users\Ag1Le\Documents\my_files",   # <- or edit this path directly
))
# -------------------------------------------------------------------------- #

FRAMEWORK_STAGES = {"Why", "What", "How", "Now"}
NOISE_MARKERS = ("222.127", "Mozilla", "HTTP/1.1", "GET /")


def _have_files():
    return MY_FILES_DIR.is_dir() and any(MY_FILES_DIR.iterdir())


@pytest.fixture(scope="module")
def my_register(tmp_path_factory):
    if not _have_files():
        pytest.skip(f"no source files found in {MY_FILES_DIR} "
                    f"(set MY_FILES env var or edit MY_FILES_DIR in this test)")
    out = tmp_path_factory.mktemp("my_files_out")
    print(f"\n[my_files] input:  {MY_FILES_DIR}")
    print(f"[my_files] output: {out}")
    p = m.ImpactSlidePreprocessorV2(input_path=str(MY_FILES_DIR), output_dir=str(out),
                                    filter_level="permissive")
    p.run()
    return out, json.load(open(out / "evidence_register_seed.json"))


# --------------------------------------------------------------------------- #
# Core contracts
# --------------------------------------------------------------------------- #
class TestMyFiles:
    def test_runs_without_error_and_emits_handoff_files(self, my_register):
        out, ev = my_register
        for name in ("file_inventory.json", "evidence_register_seed.json",
                     "preprocessor_summary.md"):
            assert (out / name).exists(), f"missing handoff file {name}"

    def test_register_is_nonempty_list(self, my_register):
        _, ev = my_register
        assert isinstance(ev, list) and len(ev) > 0, "no evidence produced from your files"

    def test_evidence_source_backed(self, my_register):
        _, ev = my_register
        for e in ev:
            assert e.get("source_file"), f"{e.get('evidence_id')} has no source_file"
            assert e.get("source_location"), f"{e.get('evidence_id')} has no source_location"

    def test_evidence_ids_unique_and_well_formed(self, my_register):
        import re
        _, ev = my_register
        ids = [e["evidence_id"] for e in ev]
        assert len(ids) == len(set(ids))
        assert all(re.fullmatch(r"E\d{4}", i) for i in ids)

    def test_register_priority_sorted(self, my_register):
        _, ev = my_register
        scores = [e["priority_score"] for e in ev]
        assert scores == sorted(scores, reverse=True)

    def test_narrative_use_within_framework(self, my_register):
        _, ev = my_register
        for e in ev:
            use = set(e["suggested_narrative_use"])
            assert use.issubset(FRAMEWORK_STAGES), \
                f"{e['evidence_id']} uses non-framework stage(s) {use - FRAMEWORK_STAGES}"

    def test_no_numeric_cross_file_flooding(self, my_register):
        """Bare-integer cross-file matches (the bug #11a false-positive pattern)
        should not dominate the register even on unknown files."""
        _, ev = my_register
        numeric_cross = [e for e in ev
                         if e["insight_type"] == "cross_file_metric"
                         and "Numeric value" in e["text"]]
        assert len(numeric_cross) <= 3, \
            f"{len(numeric_cross)} numeric cross-file entries — possible false positives"

    def test_noise_not_at_top(self, my_register):
        """IP/URL/user-agent table cells must not be the highest-priority evidence."""
        _, ev = my_register
        for e in ev[:5]:
            assert not any(n in e["text"] for n in NOISE_MARKERS), \
                f"noise in top 5: {e['evidence_id']} {e['text'][:60]}"
