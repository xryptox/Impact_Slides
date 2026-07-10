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


# --------------------------------------------------------------------------- #
# v4: content-aware Quote / Metric detection layers (--semantic-detection)
# --------------------------------------------------------------------------- #
from impact_slides.schemas import (
    SEMANTIC_DETECTION_LEVELS, SEMANTIC_DETECTION_PROSE_TYPES,
    DEFAULT_SEMANTIC_QUOTE_PATTERNS, DEFAULT_SEMANTIC_METRIC_PATTERNS,
)


class TestSemanticDetectionConstants:
    def test_levels_are_four(self):
        assert SEMANTIC_DETECTION_LEVELS == ("off", "loose", "default", "strict")

    def test_constants_exported_in_all(self):
        from impact_slides import schemas
        for name in ("SEMANTIC_DETECTION_LEVELS", "SEMANTIC_DETECTION_PROSE_TYPES",
                     "DEFAULT_SEMANTIC_QUOTE_PATTERNS", "DEFAULT_SEMANTIC_METRIC_PATTERNS"):
            assert name in schemas.__all__

    def test_prose_types_exclude_pptx_in_default_and_strict(self):
        # Point 3 (option 3b): pptx_slide_insight excluded from default/strict.
        for level in ("default", "strict"):
            assert "pptx_slide_insight" not in SEMANTIC_DETECTION_PROSE_TYPES[level]
            assert "bullet_insight" in SEMANTIC_DETECTION_PROSE_TYPES[level]

    def test_prose_types_include_pptx_in_loose(self):
        assert "pptx_slide_insight" in SEMANTIC_DETECTION_PROSE_TYPES["loose"]

    def test_all_quote_patterns_target_quote(self):
        import re
        for level in ("loose", "default", "strict"):
            for pat, stype in DEFAULT_SEMANTIC_QUOTE_PATTERNS[level]:
                assert stype == "Quote"
                re.compile(pat)  # bad patterns fail fast

    def test_all_metric_patterns_target_metric(self):
        import re
        for level in ("loose", "default", "strict"):
            for pat, stype in DEFAULT_SEMANTIC_METRIC_PATTERNS[level]:
                assert stype == "Metric"
                re.compile(pat)

    def test_strict_has_fewer_patterns_than_default(self):
        # strict drops the long-block quote heuristic (no attribution).
        assert len(DEFAULT_SEMANTIC_QUOTE_PATTERNS["strict"]) \
            < len(DEFAULT_SEMANTIC_QUOTE_PATTERNS["default"])

    def test_loose_has_more_metric_patterns_than_default(self):
        # loose adds bare-large-currency + KPI+digit.
        assert len(DEFAULT_SEMANTIC_METRIC_PATTERNS["loose"]) \
            > len(DEFAULT_SEMANTIC_METRIC_PATTERNS["default"])


class TestQuoteDetection:
    """Layer 2: attribution-gated Quote detection on prose insight_types."""
    def _p(self, preprocessor):
        preprocessor.semantic_detection = "default"
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        return preprocessor

    def test_curly_quote_with_attribution_becomes_quote(self, preprocessor):
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="docx_insight",
            text="\u201cdining is one of the most important ways we connect,\u201d said Marquez.")])
        assert out[0]["semantic_type"] == "Quote"

    def test_straight_quote_with_attribution_becomes_quote(self, preprocessor):
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="docx_insight",
            text='"dining is core to how we live," said Marquez.')])
        assert out[0]["semantic_type"] == "Quote"

    def test_colon_then_quote_becomes_quote(self, preprocessor):
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="pdf_page_insight",
            text='Squeri said: "This acquisition creates real value."')])
        assert out[0]["semantic_type"] == "Quote"

    def test_long_quoted_block_becomes_quote_default(self, preprocessor):
        # default has a long-block heuristic (>=60 chars) without attribution.
        p = self._p(preprocessor)
        long_quote = ('\u201cWe believe this acquisition creates a once-in-a-'
                      'generation opportunity to redefine how diners discover '
                      'restaurants and run businesses across the globe.\u201d')
        out = p._validate_evidence([_ev(
            insight_type="docx_insight", text=long_quote)])
        assert out[0]["semantic_type"] == "Quote"

    def test_scare_quote_stays_claim(self, preprocessor):
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="docx_insight",
            text='the \u201cbest\u201d option for diners is here.')])
        assert out[0]["semantic_type"] == "Claim"

    def test_short_quote_without_attribution_stays_claim(self, preprocessor):
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="docx_insight",
            text='He called it \u201cfine\u201d and moved on.')])
        assert out[0]["semantic_type"] == "Claim"

    def test_strict_requires_attribution_no_long_block(self, preprocessor):
        # strict drops the long-block heuristic, so a long quote WITHOUT
        # attribution stays Claim.
        preprocessor.semantic_detection = "strict"
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        long_quote = ('\u201cWe believe this acquisition creates a once-in-a-'
                      'generation opportunity to redefine how diners discover '
                      'restaurants and run businesses across the globe.\u201d')
        out = preprocessor._validate_evidence([_ev(
            insight_type="docx_insight", text=long_quote)])
        assert out[0]["semantic_type"] == "Claim"

    def test_quote_layer_skips_pptx_in_default(self, preprocessor):
        # Point 3 (3b): pptx_slide_insight is NOT in the default prose set, so
        # a quoted span on a slide stays Claim until the Builder overrides.
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="pptx_slide_insight",
            text='\u201cWe are building the future of dining,\u201d said Squeri.')])
        assert out[0]["semantic_type"] == "Claim"

    def test_quote_layer_includes_pptx_in_loose(self, preprocessor):
        preprocessor.semantic_detection = "loose"
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        out = preprocessor._validate_evidence([_ev(
            insight_type="pptx_slide_insight",
            text='\u201cWe are building the future of dining,\u201d said Squeri.')])
        assert out[0]["semantic_type"] == "Quote"


class TestLegalDefinitionFalsePositives:
    """Regression guard: contract defined terms (EX-10.1 / 8-K filings) must NOT
    be tagged Quote. The preprocessor runs on legal corpora; the quote-detection
    layers must distinguish speech attribution from legal definition verbs."""
    def _p(self, preprocessor):
        preprocessor.semantic_detection = "default"
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        return preprocessor

    def test_means_definition_stays_claim(self, preprocessor):
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="pdf_page_insight",
            text='\u201cBusiness Day\u201d means any day other than a Saturday, Sunday.')])
        assert out[0]["semantic_type"] == "Claim"

    def test_has_the_meaning_definition_stays_claim(self, preprocessor):
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="pdf_page_insight",
            text='\u201cReplacement Marks\u201d has the meaning set forth in Section 6.13(f).')])
        assert out[0]["semantic_type"] == "Claim"

    def test_shall_mean_definition_stays_claim(self, preprocessor):
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="pdf_page_insight",
            text='\u201cAgreement\u201d shall mean this Equity Purchase Agreement.')])
        assert out[0]["semantic_type"] == "Claim"

    def test_as_defined_definition_stays_claim(self, preprocessor):
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="pdf_page_insight",
            text='\u201cSeller\u201d as defined in Section 1.1 above.')])
        assert out[0]["semantic_type"] == "Claim"

    def test_section_reference_colon_quote_stays_claim(self, preprocessor):
        # `Section 6.21: \u201cReport\u201d has the meaning...` — colon+quote
        # must not fire the colon-then-quote heuristic.
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="pdf_page_insight",
            text='Section 6.21: \u201cReport\u201d has the meaning set forth in Section 6.21(a)(i).')])
        assert out[0]["semantic_type"] == "Claim"

    def test_legal_definition_body_span_stays_claim(self, preprocessor):
        # The long-block heuristic used to fire on the text BETWEEN two
        # consecutive defined terms (a close->open quote span of definition
        # body). Must stay Claim.
        p = self._p(preprocessor)
        text = ('\u201cRestricted Cash\u201d means any cash or cash equivalent that is '
                'subject to restrictions or limitations on use or distribution '
                'by Law, contract or otherwise, and that constitutes \u201crestricted '
                'cash\u201d in accordance with applicable accounting standards.')
        out = p._validate_evidence([_ev(
            insight_type="pdf_page_insight", text=text)])
        assert out[0]["semantic_type"] == "Claim"

    def test_person_name_does_not_match_lowercase_words(self, preprocessor):
        # The core bug: [A-Z][a-z]+\s+[A-Z][a-z]+ compiled with IGNORECASE
        # matched any two words (e.g. "has the"), turning every legal defined
        # term into a Quote. Now case-sensitive, so lowercase "has the" after
        # a quoted term stays Claim.
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="pdf_page_insight",
            text='\u201cCompany Products\u201d has the meaning set forth in this Agreement.')])
        assert out[0]["semantic_type"] == "Claim"

    def test_real_speech_quote_still_works_in_legal_corpus_context(self, preprocessor):
        # Positive control: a real attributed quote MUST still be Quote even on
        # a pdf_page_insight (the same insight_type as the legal defs above).
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="pdf_page_insight",
            text='\u201cThis acquisition creates real value for shareholders,\u201d said Stephen Squeri, Chairman and CEO.')])
        assert out[0]["semantic_type"] == "Quote"

    def test_real_colon_quote_still_works(self, preprocessor):
        # Positive control: colon-then-real-speech-quote still fires.
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="pdf_page_insight",
            text='Marquez said: \u201cDining is core to how we live, work, and travel.\u201d')])
        assert out[0]["semantic_type"] == "Quote"


class TestMetricDetection:
    """Layer 3: magnitude-gated Metric detection on prose insight_types."""
    def _p(self, preprocessor):
        preprocessor.semantic_detection = "default"
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        return preprocessor

    def test_currency_magnitude_becomes_metric(self, preprocessor):
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="docx_insight",
            text="TheFork LTM revenue was $232M.")])
        assert out[0]["semantic_type"] == "Metric"

    def test_currency_grouped_thousands_becomes_metric(self, preprocessor):
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="docx_insight",
            text="Deal value of $700,000,000 all cash.")])
        assert out[0]["semantic_type"] == "Metric"

    def test_percentage_becomes_metric(self, preprocessor):
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="docx_insight",
            text="Growth of 23% year over year.")])
        assert out[0]["semantic_type"] == "Metric"

    def test_bare_magnitude_becomes_metric(self, preprocessor):
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="docx_insight",
            text="adj EBITDA of 28 million euros.")])
        assert out[0]["semantic_type"] == "Metric"

    def test_does_not_fire_on_bare_range(self, preprocessor):
        # REGRESSION GUARD: the _ev() default text "Revenue ranges 10 to 99."
        # has no currency / % / magnitude word, so it must stay Claim. Do NOT
        # loosen the Metric regexes to match bare "X to Y" ranges, or this
        # (and test_claim_for_bullet) silently flips to Metric.
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="bullet_insight",
            text="Revenue ranges 10 to 99.")])
        assert out[0]["semantic_type"] == "Claim"

    def test_does_not_fire_on_small_integer(self, preprocessor):
        p = self._p(preprocessor)
        out = p._validate_evidence([_ev(
            insight_type="docx_insight",
            text="We considered 3 options for the deal.")])
        assert out[0]["semantic_type"] == "Claim"

    def test_strict_rejects_bare_percentage(self, preprocessor):
        # strict requires a KPI word near the %; bare "23%" stays Claim.
        preprocessor.semantic_detection = "strict"
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        out = preprocessor._validate_evidence([_ev(
            insight_type="docx_insight",
            text="Growth of 23% year over year.")])
        assert out[0]["semantic_type"] == "Claim"

    def test_strict_accepts_kpi_percentage(self, preprocessor):
        preprocessor.semantic_detection = "strict"
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        out = preprocessor._validate_evidence([_ev(
            insight_type="docx_insight",
            text="Revenue growth of 23% year over year.")])
        assert out[0]["semantic_type"] == "Metric"

    def test_loose_fires_on_bare_large_currency(self, preprocessor):
        # loose adds bare-large-currency (>=4 digits) without a magnitude word.
        preprocessor.semantic_detection = "loose"
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        out = preprocessor._validate_evidence([_ev(
            insight_type="docx_insight",
            text="The deal was worth $7000 in fees.")])
        assert out[0]["semantic_type"] == "Metric"


class TestDetectionPrecedence:
    """Layer ordering: Risk > Quote > Metric > map > Claim."""
    def test_risk_beats_quote(self, preprocessor):
        # Point 2: a quoted risk statement -> Risk (layer 1 wins over layer 2).
        preprocessor.semantic_detection = "default"
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        out = preprocessor._validate_evidence([_ev(
            insight_type="docx_insight",
            text='\u201cWe face significant risk and volatility in the market,\u201d said the CEO.')])
        assert out[0]["semantic_type"] == "Risk"

    def test_quote_beats_metric(self, preprocessor):
        # Point 1: a quoted sentence containing a number -> Quote (layer 2 wins
        # over layer 3) because attribution is the rarer, stronger signal.
        preprocessor.semantic_detection = "default"
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        out = preprocessor._validate_evidence([_ev(
            insight_type="docx_insight",
            text='\u201cThis is a $700M opportunity for us,\u201d said Squeri.')])
        assert out[0]["semantic_type"] == "Quote"

    def test_metric_layer_skips_non_prose_insight_types(self, preprocessor):
        # numeric_range is already Metric in the map; the content layers must NOT
        # re-classify it (scope guard). It stays Metric via the map regardless
        # of text content.
        preprocessor.semantic_detection = "default"
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        out = preprocessor._validate_evidence([_ev(
            insight_type="numeric_range",
            text="plain text with no numbers here")])
        assert out[0]["semantic_type"] == "Metric"


class TestSemanticDetectionOff:
    """--semantic-detection off disables both content layers (escape hatch)."""
    def test_off_disables_quote_detection(self, preprocessor):
        preprocessor.semantic_detection = "off"
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        out = preprocessor._validate_evidence([_ev(
            insight_type="docx_insight",
            text='\u201cdining is core to how we live,\u201d said Marquez.')])
        assert out[0]["semantic_type"] == "Claim"

    def test_off_disables_metric_detection(self, preprocessor):
        preprocessor.semantic_detection = "off"
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        out = preprocessor._validate_evidence([_ev(
            insight_type="docx_insight",
            text="TheFork revenue was $232M.")])
        assert out[0]["semantic_type"] == "Claim"

    def test_off_still_applies_risk_keyword_override(self, preprocessor):
        # The Risk keyword-override layer is independent of this knob.
        preprocessor.semantic_detection = "off"
        preprocessor.semantic_type_rules = preprocessor._build_semantic_type_rules()
        out = preprocessor._validate_evidence([_ev(
            insight_type="docx_insight",
            text="Volatility exposes downside risk to the outlook.")])
        assert out[0]["semantic_type"] == "Risk"

    def test_off_empty_prose_types(self, preprocessor):
        preprocessor.semantic_detection = "off"
        rules = preprocessor._build_semantic_type_rules()
        assert rules["prose_types"] == frozenset()
        assert rules["compiled_quote_patterns"] == []
        assert rules["compiled_metric_patterns"] == []


class TestConfigSemanticDetection:
    def test_config_default_is_default(self):
        assert CONFIG_DEFAULTS["semantic_detection"] == "default"

    def test_validate_accepts_each_level(self):
        for level in ("off", "loose", "default", "strict"):
            cfg = dict(CONFIG_DEFAULTS)
            cfg["semantic_detection"] = level
            validate_config(cfg)

    def test_validate_rejects_unknown_level(self):
        cfg = dict(CONFIG_DEFAULTS)
        cfg["semantic_detection"] = "aggressive"
        with pytest.raises(ValueError, match="semantic_detection"):
            validate_config(cfg)


class TestCLISemanticDetection:
    def _run(self, *extra, tmp_path):
        out = tmp_path / "out"
        out.mkdir()
        cmd = [sys.executable, "step1_preprocessor_v4.py",
               "--input", str(tmp_path), "--output", str(out),
               "--emit-schema"]  # exits early; just tests arg parsing
        cmd.extend(extra)
        return subprocess.run(cmd, capture_output=True, text=True,
                              cwd=str(Path(__file__).resolve().parent.parent))

    def test_cli_accepts_default(self, tmp_path):
        proc = self._run("--semantic-detection", "default", tmp_path=tmp_path)
        assert proc.returncode == 0

    def test_cli_accepts_strict(self, tmp_path):
        proc = self._run("--semantic-detection", "strict", tmp_path=tmp_path)
        assert proc.returncode == 0

    def test_cli_accepts_off(self, tmp_path):
        proc = self._run("--semantic-detection", "off", tmp_path=tmp_path)
        assert proc.returncode == 0

    def test_cli_rejects_unknown_level(self, tmp_path):
        proc = self._run("--semantic-detection", "aggressive", tmp_path=tmp_path)
        assert proc.returncode != 0
