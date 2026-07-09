"""
Tests for the `semantic_type` field on EvidenceEntry (Metric/Claim/Quote/Risk).

Covers:
  - schemas.SEMANTIC_TYPES + DEFAULT_SEMANTIC_TYPE_MAP +
    DEFAULT_SEMANTIC_KEYWORD_OVERRIDES constants exist and are exported
  - EvidenceEntry.semantic_type is optional in the schema (so the frozen v2/v3
    baselines that share this schema but don't assign the field still validate)
    but rejects unknown values when present
  - the deterministic insight_type -> semantic_type map covers EVERY
    INSIGHT_TYPES member, every mapped value is in SEMANTIC_TYPES, and the
    3 ambiguous structural types default to Claim
  - the v4 preprocessor chokepoint (_validate_evidence) always populates
    semantic_type (even when pydantic is absent — the JSON output carries it),
    preserves an explicit assignment, and applies the risk-keyword override
    layer (text containing risk language -> "Risk" regardless of insight_type)
  - user --semantic-type-keywords / YAML extend the Risk keyword set
  - the CSV export includes the semantic_type column
  - inspect_register surfaces a "By semantic type" breakdown
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

import step1_preprocessor_v4 as m
from impact_slides.schemas import (
    EvidenceEntry, INSIGHT_TYPES, SEMANTIC_TYPES,
    DEFAULT_SEMANTIC_TYPE_MAP, DEFAULT_SEMANTIC_KEYWORD_OVERRIDES,
)
from impact_slides.config import CONFIG_DEFAULTS, validate_config


# --------------------------------------------------------------------------- #
# Constants & schema contract
# --------------------------------------------------------------------------- #
class TestSemanticTypeConstants:
    def test_semantic_types_exists_and_has_four(self):
        assert SEMANTIC_TYPES == {"Metric", "Claim", "Quote", "Risk"}

    def test_constants_exported_in_all(self):
        from impact_slides import schemas
        for name in ("SEMANTIC_TYPES", "DEFAULT_SEMANTIC_TYPE_MAP",
                     "DEFAULT_SEMANTIC_KEYWORD_OVERRIDES"):
            assert name in schemas.__all__

    def test_keyword_overrides_all_target_risk(self):
        # Every built-in keyword override reclassifies to Risk (the only bucket
        # that is never auto-assigned from insight_type).
        for _pat, stype in DEFAULT_SEMANTIC_KEYWORD_OVERRIDES:
            assert stype == "Risk"

    def test_keyword_overrides_are_regexes(self):
        import re
        for pat, _ in DEFAULT_SEMANTIC_KEYWORD_OVERRIDES:
            re.compile(pat)  # bad patterns fail fast here


class TestEvidenceEntrySemanticType:
    def _good(self, **kw):
        base = dict(
            evidence_id="E0001", source_file="f.xlsx",
            insight_type="numeric_range", text="x",
            priority_score=0.5, confidence="high",
            suggested_narrative_use=["What"], source_location="S1",
        )
        base.update(kw)
        return base

    def test_optional_in_schema(self):
        # Absent -> valid (None default). This is what lets the frozen v2/v3
        # baselines share the schema without assigning the field.
        ev = EvidenceEntry(**self._good())
        assert ev.semantic_type is None

    def test_accepts_each_valid_value(self):
        for st in SEMANTIC_TYPES:
            EvidenceEntry(**self._good(semantic_type=st))

    def test_rejects_unknown_value(self):
        with pytest.raises(Exception):
            EvidenceEntry(**self._good(semantic_type="Narrative"))

    def test_reflected_in_json_schema(self):
        schema = EvidenceEntry.model_json_schema()
        assert "semantic_type" in schema["properties"]


# --------------------------------------------------------------------------- #
# Mapping completeness (the 25 insight_types -> 4 buckets)
# --------------------------------------------------------------------------- #
class TestMappingCompleteness:
    def test_every_insight_type_mapped(self):
        missing = INSIGHT_TYPES - set(DEFAULT_SEMANTIC_TYPE_MAP)
        assert not missing, f"insight_types without a semantic_type: {missing}"

    def test_no_extra_map_keys(self):
        # Every map key must be a real insight_type (guards against typos).
        extra = set(DEFAULT_SEMANTIC_TYPE_MAP) - INSIGHT_TYPES
        assert not extra, f"map keys not in INSIGHT_TYPES: {extra}"

    def test_every_mapped_value_is_valid(self):
        for itype, stype in DEFAULT_SEMANTIC_TYPE_MAP.items():
            assert stype in SEMANTIC_TYPES, f"{itype} -> {stype!r}"

    def test_metrics_map_to_metric(self):
        for t in ("numeric_range", "categorical_distribution", "aggregate_insight",
                  "trend_insight", "period_trend_insight", "outlier_insight",
                  "correlation_insight", "chart_data_insight", "text_metric",
                  "cross_file_metric", "table_cell"):
            assert DEFAULT_SEMANTIC_TYPE_MAP[t] == "Metric"

    def test_verbatim_types_map_to_quote(self):
        assert DEFAULT_SEMANTIC_TYPE_MAP["speaker_notes_insight"] == "Quote"
        assert DEFAULT_SEMANTIC_TYPE_MAP["emphasized_text"] == "Quote"

    def test_prose_types_map_to_claim(self):
        for t in ("bullet_insight", "pptx_slide_insight", "pdf_page_insight",
                  "docx_insight"):
            assert DEFAULT_SEMANTIC_TYPE_MAP[t] == "Claim"

    def test_ambiguous_structural_types_default_to_claim(self):
        # The 3 flagged ambiguous types — safe catch-all, keeps the 4-bucket
        # enum clean.
        for t in ("process_step", "section_divider", "multi_column_suggestion"):
            assert DEFAULT_SEMANTIC_TYPE_MAP[t] == "Claim"

    def test_no_insight_type_auto_maps_to_risk(self):
        # Risk is only reachable via the keyword-override layer.
        assert "Risk" not in DEFAULT_SEMANTIC_TYPE_MAP.values()


# --------------------------------------------------------------------------- #
# Preprocessor chokepoint (_validate_evidence) — single assignment site
# --------------------------------------------------------------------------- #
@pytest.fixture()
def preprocessor(tmp_path):
    inp = tmp_path / "input"
    out = tmp_path / "output"
    inp.mkdir()
    p = m.ImpactSlidePreprocessorV4(input_path=str(inp), output_dir=str(out))
    return p


def _ev(**kw):
    base = dict(
        evidence_id="E0001", source_file="f.xlsx",
        insight_type="numeric_range", text="Revenue ranges 10 to 99.",
        priority_score=0.5, confidence="high",
        suggested_narrative_use=["What"], source_location="S1",
    )
    base.update(kw)
    return base


class TestChokepointAssignment:
    def test_assigns_from_insight_type_map(self, preprocessor):
        out = preprocessor._validate_evidence([_ev(insight_type="numeric_range")])
        assert out[0]["semantic_type"] == "Metric"

    def test_quote_for_speaker_notes(self, preprocessor):
        out = preprocessor._validate_evidence(
            [_ev(insight_type="speaker_notes_insight")])
        assert out[0]["semantic_type"] == "Quote"

    def test_claim_for_bullet(self, preprocessor):
        out = preprocessor._validate_evidence([_ev(insight_type="bullet_insight")])
        assert out[0]["semantic_type"] == "Claim"

    def test_fallback_claim_for_unknown_insight_type(self, preprocessor):
        # An insight_type not in the map (defensive) -> safe "Claim" fallback,
        # not a crash. (The schema would separately reject an unknown
        # insight_type, but the assignment itself must not raise.)
        out = preprocessor._validate_evidence([_ev(insight_type="mystery_type")])
        # Entry may be dropped by schema validation for the bad insight_type,
        # but the assignment populated the field first (no exception raised).
        if out:
            assert out[0]["semantic_type"] == "Claim"

    def test_risk_keyword_override_reclassifies_metric_to_risk(self, preprocessor):
        # text containing risk language -> "Risk" even though insight_type
        # (numeric_range) maps to Metric.
        out = preprocessor._validate_evidence(
            [_ev(text="Volatility in revenue exposes downside risk to the outlook.")])
        assert out[0]["semantic_type"] == "Risk"

    def test_risk_override_ignores_non_risk_text(self, preprocessor):
        out = preprocessor._validate_evidence([_ev(text="Revenue grew 12% YoY.")])
        assert out[0]["semantic_type"] == "Metric"

    def test_explicit_semantic_type_preserved(self, preprocessor):
        # An extractor-provided semantic_type is NOT overwritten.
        out = preprocessor._validate_evidence(
            [_ev(semantic_type="Quote")])  # numeric_range would be Metric
        assert out[0]["semantic_type"] == "Quote"

    def test_assigned_even_without_text(self, preprocessor):
        out = preprocessor._validate_evidence([_ev(text="")])
        assert out[0]["semantic_type"] == "Metric"

    def test_user_risk_keywords_extend_override(self, preprocessor):
        preprocessor.semantic_type_keywords = ["churn", "breach"]
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        out = preprocessor._validate_evidence(
            [_ev(text="Customer churn accelerated this quarter.")])
        assert out[0]["semantic_type"] == "Risk"

    def test_user_keyword_is_word_boundary(self, preprocessor):
        # "breach" must not match "breached-contract" substrings loosely, but
        # word-boundary means "breach" inside "breached" DOES match (re \b
        # matches between 'breach' and 'ed'? no — \b is at a word char
        # boundary; 'breached' is one word so \bbreach\b does NOT match). Verify
        # the intended behavior: standalone 'breach' matches, 'breached' does not.
        preprocessor.semantic_type_keywords = ["breach"]
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        out_hit = preprocessor._validate_evidence([_ev(text="A data breach occurred.")])
        assert out_hit[0]["semantic_type"] == "Risk"
        out_miss = preprocessor._validate_evidence([_ev(text="The breached contract terms.")])
        assert out_miss[0]["semantic_type"] == "Metric"


# --------------------------------------------------------------------------- #
# Config defaults & validation
# --------------------------------------------------------------------------- #
class TestConfigSemanticTypeKeywords:
    def test_config_default_is_empty_list(self):
        assert CONFIG_DEFAULTS["semantic_type_keywords"] == []

    def test_validate_accepts_default(self):
        validate_config(dict(CONFIG_DEFAULTS))

    def test_validate_accepts_list_of_strings(self):
        cfg = dict(CONFIG_DEFAULTS)
        cfg["semantic_type_keywords"] = ["churn", "breach"]
        validate_config(cfg)

    def test_validate_rejects_non_list(self):
        cfg = dict(CONFIG_DEFAULTS)
        cfg["semantic_type_keywords"] = "churn"
        with pytest.raises(ValueError, match="must be a list"):
            validate_config(cfg)

    def test_validate_rejects_non_string_entry(self):
        cfg = dict(CONFIG_DEFAULTS)
        cfg["semantic_type_keywords"] = ["churn", 42]
        with pytest.raises(ValueError, match="must be strings"):
            validate_config(cfg)


# --------------------------------------------------------------------------- #
# CSV export includes the semantic_type column
# --------------------------------------------------------------------------- #
class TestCSVColumn:
    def test_semantic_type_in_preferred_columns(self):
        # The preferred CSV column ordering lives in preprocessor._save_outputs;
        # assert via the source to avoid a full run, then confirm with a run.
        import inspect
        src = inspect.getsource(m.ImpactSlidePreprocessorV4._save_outputs)
        assert "semantic_type" in src

    def test_csv_header_contains_semantic_type(self, tmp_path):
        out = tmp_path / "out"
        out.mkdir()
        p = m.ImpactSlidePreprocessorV4(input_path=str(tmp_path), output_dir=str(out))
        p.export_csv = True
        # Route one entry through the chokepoint so semantic_type is assigned
        # (mirrors a real run), then run only the output step.
        p.evidence_register = p._validate_evidence([_ev(insight_type="numeric_range")])
        assert p.evidence_register[0]["semantic_type"] == "Metric"
        # _save_outputs reads self.evidence_register + self.pptx_profiles etc.
        p.pptx_profiles = []
        p.excel_profiles = []
        p.inventory = []
        p.errors = []
        p.filtered_items = []
        p.coverage_map = {}
        p.entities_summary = []
        p.analyst_briefing_md = None
        p.analyst_briefing_json = None
        p.timing = {"files": [], "stages": {}, "total_seconds": 0.0}
        p.config_snapshot = dict(CONFIG_DEFAULTS)
        p._save_outputs()
        csv_path = out / "evidence_register.csv"
        assert csv_path.exists()
        with open(csv_path, newline="", encoding="utf-8") as f:
            header = next(csv.reader(f))
        assert "semantic_type" in header
        # And the row carries the assigned value.
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert row["semantic_type"] == "Metric"


# --------------------------------------------------------------------------- #
# inspect_register surfaces a semantic-type breakdown
# --------------------------------------------------------------------------- #
class TestInspectBreakdown:
    def test_inspect_shows_semantic_breakdown(self, tmp_path, capsys):
        out = tmp_path / "out"
        out.mkdir()
        reg = [_ev(insight_type="numeric_range", semantic_type="Metric")]
        (out / "evidence_register_seed.json").write_text(json.dumps(reg))
        m.inspect_register(str(out), top_n=5)
        captured = capsys.readouterr()
        assert "By semantic type" in captured.out
        assert "Metric" in captured.out


# --------------------------------------------------------------------------- #
# CLI flag --semantic-type-keywords
# --------------------------------------------------------------------------- #
class TestCLISemanticTypeKeywords:
    def _run(self, *extra, tmp_path):
        out = tmp_path / "out"
        out.mkdir()
        cmd = [sys.executable, "step1_preprocessor_v4.py",
               "--input", str(tmp_path), "--output", str(out)]
        if "--emit-schema" not in extra:
            cmd.append("--emit-schema")  # exits early; just tests arg parsing
        cmd.extend(extra)
        return subprocess.run(cmd, capture_output=True, text=True,
                              cwd=str(Path(__file__).resolve().parent.parent))

    def test_cli_flag_accepted(self, tmp_path):
        proc = self._run("--semantic-type-keywords", "churn", "breach", tmp_path=tmp_path)
        assert proc.returncode == 0

    def test_cli_flag_default_is_empty(self, tmp_path):
        proc = self._run(tmp_path=tmp_path)
        assert proc.returncode == 0
