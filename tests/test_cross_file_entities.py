"""
Tests for the v3 cross-file entity-matching enhancements:

  #17 abbreviation / alias expansion (US <-> United States, EMEA <-> expansion,
     YoY <-> year-over-year, …)
  #18 fuzzy matching + word-boundary for ALL keyword lengths (not just <=4),
     so near-spellings (Naypyitaw <-> Naypyidaw) and word-boundary safety
     (South does NOT match southbound) both work
  #19 per-entity "mentioned in N files" stats tracked and surfaced in the
     cross-file evidence text + the coverage map's entity_mentions block
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
    def _make(filter_level="permissive"):
        inp = tmp_workspace / "input"
        out = tmp_workspace / "output"
        inp.mkdir(parents=True, exist_ok=True)
        p = m.ImpactSlidePreprocessorV2(
            input_path=str(inp), output_dir=str(out), filter_level=filter_level,
        )
        return p, inp, out
    return _make


# --------------------------------------------------------------------------- #
# #17 abbreviation expansion
# --------------------------------------------------------------------------- #
class TestAbbreviationExpansion:
    @pytest.mark.parametrize("entity, text, expected", [
        ("US", "United States sales grew", True),
        ("US", "USA revenue", True),
        ("EU", "European Union members", True),
        ("EMEA", "europe middle east africa revenue", True),
        ("YoY", "year-over-year growth", True),
        ("APAC", "asia-pacific region", True),
        ("United States", "US sales", True),          # expansion -> short
        ("year over year", "YoY growth", True),       # expansion -> short
    ])
    def test_abbreviation_matches(self, entity, text, expected):
        assert m._entity_in_text(entity, text) is expected

    def test_abbreviation_no_false_positive(self):
        # 'us' should not match the pronoun 'us' mid-sentence loosely via fuzzy
        # (it WOULD match via word-boundary, which is correct — but a totally
        # unrelated entity should not match).
        assert m._entity_in_text("EMEA", "north america sales only") is False


# --------------------------------------------------------------------------- #
# #18 fuzzy matching + word-boundary for all lengths
# --------------------------------------------------------------------------- #
class TestFuzzyAndWordBoundary:
    def test_word_boundary_all_lengths(self):
        # 'South' (5 chars) must NOT match 'southbound' — previously only <=4
        # got word-boundary treatment.
        assert m._entity_in_text("South", "southbound traffic") is False
        assert m._entity_in_text("South", "the south region") is True

    def test_fuzzy_near_spelling(self):
        # 'Naypyitaw' vs 'Naypyidaw' (common alternate transliteration)
        assert m._entity_in_text("Naypyitaw", "Naypyidaw branch grew") is True

    def test_fuzzy_not_too_loose(self):
        # genuinely different entities must not fuzzy-match
        assert m._entity_in_text("Mandalay", "Yangon region") is False

    def test_multi_word_entity_word_boundary(self):
        assert m._entity_in_text("North America", "North America sales") is True
        assert m._entity_in_text("North America", "South America sales") is False


# --------------------------------------------------------------------------- #
# #19 per-entity mention stats
# --------------------------------------------------------------------------- #
class TestEntityMentionStats:
    def test_cross_file_evidence_mentions_file_count(self, make_excel, make_pptx, make_preprocessor):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"Region": ["North", "South", "East", "West"] * 2,
                                    "Revenue": [100, 200, 300, 400] * 2}))
        make_pptx(slides=[
            {"title": "Regional Review"},
            {"title": "North Region Performance",
             "body": "North region grew strongly this quarter across all key metrics"},
        ])
        p.run()
        ev = json.load(open(out / "evidence_register_seed.json"))
        cross = [e for e in ev if e["insight_type"] == "cross_file_metric"
                 and "mentioned in" in e["text"]]
        assert cross, "expected an entity cross-file entry"
        # text must report a file count (not the old hard-coded "in both ...")
        assert "mentioned in" in cross[0]["text"]
        assert "file(s)" in cross[0]["text"]

    def test_entity_mentions_in_coverage_map(self, make_excel, make_pptx, make_preprocessor):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"Region": ["North", "South", "East", "West"] * 2,
                                    "Revenue": [100, 200, 300, 400] * 2}))
        make_pptx(slides=[
            {"title": "Regional Review"},
            {"title": "North Region Performance",
             "body": "North region grew strongly this quarter"},
        ])
        p.run()
        cm = json.load(open(out / "coverage_map.json"))
        em = cm.get("entity_mentions", {})
        assert em, "expected entity_mentions in coverage map"
        north = em.get("north")
        assert north, "expected 'north' in entity_mentions"
        assert north["file_count"] >= 2
        assert north["in_excel"] is True
        assert north["in_pptx"] is True
        assert len(north["files"]) == north["file_count"]

    def test_abbreviation_links_files(self, make_excel, make_pptx, make_preprocessor):
        """An Excel categorical 'US' and a PPTX narrative 'United States' must
        be linked as the same entity via abbreviation expansion."""
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"Country": ["US", "UK", "US", "EU"],
                                    "Revenue": [100, 200, 300, 400]}))
        make_pptx(slides=[
            {"title": "Overview"},
            {"title": "United States Performance",
             "body": "United States revenue reached a record high this quarter"},
        ])
        p.run()
        ev = json.load(open(out / "evidence_register_seed.json"))
        cross = [e for e in ev if e["insight_type"] == "cross_file_metric"]
        assert cross, "expected US <-> United States to be linked"
        blob = " ".join(e["text"] for e in cross).lower()
        assert "us" in blob or "united states" in blob
