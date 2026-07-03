"""
Tests for the v3 tiered semantic dedup (#20):

  - sentence-transformers embeddings tier (true semantic similarity; bridges
    synonyms / no-shared-vocabulary near-dups) — exercised via monkeypatched
    mock model since the real dependency is optional
  - pure-numpy TF-IDF + cosine tier (opt-in via --dedup-engine tfidf)
  - rapidfuzz char-similarity tier (the reliable auto fallback)
  - source provenance merging: dropped near-dups record their source_file +
    evidence_id on the surviving entry (dedup_merged_sources / dedup_merged_ids)
  - graceful degradation: auto falls back to fuzzy when embeddings unavailable
  - regression: existing lexical-rephrasing dedup still works in auto mode
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import step1_preprocessor_v3 as m


def _ev(eid, text, score=0.8, src="a.xlsx"):
    return {
        "evidence_id": eid,
        "insight_type": "bullet_insight",
        "text": text,
        "priority_score": score,
        "source_file": src,
        "suggested_narrative_use": ["What"],
    }


@pytest.fixture()
def make_preprocessor(tmp_workspace):
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
# Engine resolution + graceful degradation
# --------------------------------------------------------------------------- #
class TestEngineResolution:
    def test_auto_resolves_to_fuzzy_without_embeddings(self):
        eng = m._SemanticDedupEngine(["hello world", "foo bar"], engine="auto")
        # sentence-transformers not installed in this env -> fuzzy fallback
        assert eng.mode == "fuzzy"
        assert eng.threshold == 0.85

    def test_explicit_tfidf_resolves_to_tfidf(self):
        if m.np is None:
            pytest.skip("numpy unavailable")
        eng = m._SemanticDedupEngine(["revenue grew", "sales rose"], engine="tfidf")
        assert eng.mode == "tfidf"
        assert eng.threshold == 0.85  # conservative; see _SEM_THRESHOLD docstring

    def test_explicit_fuzzy_resolves_to_fuzzy(self):
        eng = m._SemanticDedupEngine(["x", "y"], engine="fuzzy")
        assert eng.mode == "fuzzy"
        assert eng.matrix is None  # on-demand, no precomputed matrix

    def test_dedup_engine_default(self, make_preprocessor):
        p, _, _ = make_preprocessor()
        assert p.dedup_engine == "auto"


# --------------------------------------------------------------------------- #
# Tier behavior
# --------------------------------------------------------------------------- #
class TestFuzzyTier:
    def test_lexical_rephrasing_collapses_auto(self):
        """auto mode (fuzzy fallback) still catches the lexical rephrasing that
        the v3 #10 test pinned — regression safety for the engine refactor."""
        pp = m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_x")
        evs = [
            _ev("E1", "Recommendation: expand North operations", 0.9),
            _ev("E2", "Recommend expanding North operations", 0.7, "b.pptx"),
            _ev("E3", "Totally different insight about revenue", 0.8, "c.xlsx"),
        ]
        out = pp._deduplicate_evidence(evs)
        assert len(out) == 2
        texts = [o["text"] for o in out]
        assert "Recommendation: expand North operations" in texts
        assert "Recommend expanding North operations" not in texts

    def test_distinct_insights_not_collapsed(self):
        pp = m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_x")
        evs = [
            _ev("E1", "Revenue grew strongly in Q3", 0.8),
            _ev("E2", "Profit margins declined in the south", 0.8, "b.pptx"),
        ]
        assert len(pp._deduplicate_evidence(evs)) == 2


class TestTfidfTier:
    def test_tfidf_does_not_over_merge_distinct_shared_keyword(self):
        """Two distinct insights sharing a common keyword ('revenue', 'region')
        but with opposite meaning (grew vs declined) must NOT merge under tfidf.
        This is the false-positive guard for the opt-in tier."""
        if m.np is None:
            pytest.skip("numpy unavailable")
        pp = m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_x")
        pp.dedup_engine = "tfidf"
        evs = [
            _ev("E1", "revenue grew in north region", 0.9),
            _ev("E2", "revenue declined in south region", 0.8, "b.pptx"),
            _ev("E3", "completely unrelated profit margin note", 0.7, "c.xlsx"),
        ]
        out = pp._deduplicate_evidence(evs)
        # all three distinct -> none merged
        assert len(out) == 3

    def test_tfidf_exact_repeat_collapses(self):
        """Identical text (perfect word overlap, cosine=1.0) still collapses."""
        if m.np is None:
            pytest.skip("numpy unavailable")
        pp = m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_x")
        pp.dedup_engine = "tfidf"
        evs = [
            _ev("E1", "quarterly revenue growth accelerated", 0.9),
            _ev("E2", "quarterly revenue growth accelerated", 0.7, "b.pptx"),
        ]
        out = pp._deduplicate_evidence(evs)
        # Pass 1 (exact normalized prefix) already collapses exact repeats, so
        # only one survives regardless of tier.
        assert len(out) == 1

    def test_tfidf_templated_distinct_metrics_not_merged(self):
        """Documents why tfidf is opt-in, not the auto default: templated
        insights sharing boilerplate + numeric values (e.g. two different
        columns with the same range) must NOT be merged. At the conservative
        0.85 threshold this distinct-metric pair stays separate."""
        if m.np is None:
            pytest.skip("numpy unavailable")
        pp = m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_x")
        pp.dedup_engine = "tfidf"
        evs = [
            _ev("E1", "January: 'Tax 5%' ranges from 0.6045 to 49.26.", 0.9),
            _ev("E2", "January: 'gross income' ranges from 0.6045 to 49.26.", 0.8, "b.pptx"),
        ]
        out = pp._deduplicate_evidence(evs)
        assert len(out) == 2  # distinct metrics preserved at conservative thr


# --------------------------------------------------------------------------- #
# Source provenance merging
# --------------------------------------------------------------------------- #
class TestSourceMerging:
    def test_merged_sources_recorded_on_survivor(self):
        pp = m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_x")
        evs = [
            _ev("E1", "Recommendation: expand North operations", 0.9, "a.xlsx"),
            _ev("E2", "Recommend expanding North operations", 0.7, "b.pptx"),
        ]
        out = pp._deduplicate_evidence(evs)
        assert len(out) == 1
        survivor = out[0]
        assert survivor["evidence_id"] == "E1"
        assert survivor["dedup_merged_sources"] == ["b.pptx"]
        assert survivor["dedup_merged_ids"] == ["E2"]

    def test_same_file_near_dup_not_added_to_merged_sources(self):
        """If both near-dups come from the same file, merged_sources stays empty
        (no self-referential source entry)."""
        pp = m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_x")
        evs = [
            _ev("E1", "Recommendation: expand North operations", 0.9, "a.xlsx"),
            _ev("E2", "Recommend expanding North operations", 0.7, "a.xlsx"),
        ]
        out = pp._deduplicate_evidence(evs)
        survivor = out[0]
        assert survivor.get("dedup_merged_sources", []) == []
        # but the dropped evidence_id is still recorded
        assert survivor["dedup_merged_ids"] == ["E2"]

    def test_three_way_merge_accumulates_sources(self):
        pp = m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_x")
        evs = [
            _ev("E1", "Recommendation: expand North operations", 0.9, "a.xlsx"),
            _ev("E2", "Recommend expanding North operations", 0.8, "b.pptx"),
            _ev("E3", "Recommend to expand North operations", 0.7, "c.docx"),
        ]
        out = pp._deduplicate_evidence(evs)
        survivor = out[0]
        assert survivor["evidence_id"] == "E1"
        assert set(survivor["dedup_merged_sources"]) == {"b.pptx", "c.docx"}
        assert set(survivor["dedup_merged_ids"]) == {"E2", "E3"}


# --------------------------------------------------------------------------- #
# Embeddings tier (mocked, since sentence-transformers is optional)
# --------------------------------------------------------------------------- #
class TestEmbeddingsTier:
    def test_embeddings_catches_semantic_near_dup_that_fuzzy_misses(self, monkeypatch):
        """The gap case: two sentences with NO shared vocabulary but the same
        meaning. Only embeddings catch this; fuzzy & tfidf miss it. We mock the
        sentence model to return controlled embeddings."""
        # Mock: encode maps known synonym pairs to the same vector.
        import numpy as np

        class _MockModel:
            def encode(self, texts, normalize_embeddings=True, convert_to_numpy=True):
                # "north america revenue grew 12%" and "us and canada sales up a
                # tenth" -> same vector (synonyms). Everything else -> unique.
                vmap = {
                    "north america revenue grew 12%": np.array([1.0, 0.0, 0.0]),
                    "us and canada sales up a tenth": np.array([1.0, 0.0, 0.0]),
                }
                out = []
                for t in texts:
                    out.append(vmap.get(t, np.random.default_rng(0).normal(size=3)))
                out = np.array(out)
                norms = np.linalg.norm(out, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                return out / norms

        monkeypatch.setattr(m, "_SENTENCE_MODEL", _MockModel())
        pp = m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_x")
        pp.dedup_engine = "embeddings"
        evs = [
            _ev("E1", "north america revenue grew 12%", 0.9, "a.xlsx"),
            _ev("E2", "us and canada sales up a tenth", 0.7, "b.pptx"),
            _ev("E3", "distinct unrelated profit note", 0.8, "c.xlsx"),
        ]
        out = pp._deduplicate_evidence(evs)
        # embeddings merge the synonym pair; fuzzy alone would keep all 3
        assert len(out) == 2
        survivor = next(o for o in out if o["evidence_id"] == "E1")
        assert survivor["dedup_merged_sources"] == ["b.pptx"]

    def test_embeddings_mode_or_fuzzy(self, monkeypatch):
        """In embeddings mode a lexical near-dup (high fuzzy, low embedding)
        is still caught via the OR fallback."""
        import numpy as np

        class _MockModel:
            def encode(self, texts, **kw):
                # give every text an orthogonal vector so embeddings never match
                n = len(texts)
                eye = np.eye(max(n, 3))[:n]
                return eye

        monkeypatch.setattr(m, "_SENTENCE_MODEL", _MockModel())
        pp = m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_x")
        pp.dedup_engine = "embeddings"
        evs = [
            _ev("E1", "Recommendation: expand North operations", 0.9),
            _ev("E2", "Recommend expanding North operations", 0.7, "b.pptx"),
        ]
        out = pp._deduplicate_evidence(evs)
        assert len(out) == 1  # caught by the fuzzy OR fallback


# --------------------------------------------------------------------------- #
# End-to-end pipeline + schema
# --------------------------------------------------------------------------- #
class TestPipelineIntegration:
    def test_dedup_engine_flag_wired(self, tmp_path):
        """--dedup-engine CLI flag is accepted and reaches the preprocessor."""
        import sys
        inp = tmp_path / "in"
        out = tmp_path / "out"
        inp.mkdir()
        # minimal xlsx so run() succeeds
        import pandas as pd
        pd.DataFrame({"M": [1, 2], "V": [10, 20]}).to_excel(inp / "s.xlsx", index=False)
        argv = ["--input", str(inp), "--output", str(out),
                "--filter-level", "permissive", "--dedup-engine", "tfidf"]
        m.main(argv)
        assert (out / "evidence_register_seed.json").exists()
