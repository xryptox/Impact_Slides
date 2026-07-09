"""
Tests for the uniform max_text_length cap on evidence `text` fields (Option A).

Covers:
  - schemas.MAX_TEXT_LENGTH constant exists and is the canonical ceiling
  - EvidenceEntry.text enforces max_length=MAX_TEXT_LENGTH
  - config.max_text_length defaults to MAX_TEXT_LENGTH and is validated
  - the preprocessor truncates over-length text in _validate_evidence()
    (truncate, don't drop) — so the schema validator never sees a too-long text
  - per-extractor caps were removed (PDF/PPTX/DOCX store full text; the uniform
    cap is applied centrally)
  - CLI flag --max-text-length lowers the cap (cannot exceed the ceiling)
  - --emit-schema reflects max_length in the emitted JSON Schema
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import step1_preprocessor_v4 as m
from impact_slides.schemas import (
    EvidenceEntry, MAX_TEXT_LENGTH,
)
from impact_slides.config import CONFIG_DEFAULTS, validate_config


# --------------------------------------------------------------------------- #
# Constants & schema contract
# --------------------------------------------------------------------------- #
class TestMaxTextLengthConstant:
    def test_constant_exists_and_is_int(self):
        assert isinstance(MAX_TEXT_LENGTH, int)
        assert MAX_TEXT_LENGTH > 0

    def test_constant_is_800(self):
        # The agreed default per Option A.
        assert MAX_TEXT_LENGTH == 800

    def test_constant_exported_in_all(self):
        from impact_slides import schemas
        assert "MAX_TEXT_LENGTH" in schemas.__all__

    def test_schema_field_has_max_length(self):
        field = EvidenceEntry.model_fields["text"]
        # Pydantic v2 stores max_length metadata; check via json_schema.
        schema = EvidenceEntry.model_json_schema()
        assert schema["properties"]["text"]["maxLength"] == MAX_TEXT_LENGTH


class TestEvidenceEntryTextLength:
    def test_text_at_exactly_max_length_accepted(self):
        text = "x" * MAX_TEXT_LENGTH
        ev = EvidenceEntry(
            evidence_id="E0001", source_file="f.xlsx",
            insight_type="numeric_range", semantic_type="Metric", text=text,
            priority_score=0.5, confidence="high",
            suggested_narrative_use=["What"], source_location="S1",
        )
        assert len(ev.text) == MAX_TEXT_LENGTH

    def test_text_over_max_length_rejected(self):
        text = "x" * (MAX_TEXT_LENGTH + 1)
        with pytest.raises(Exception):
            EvidenceEntry(
                evidence_id="E0001", source_file="f.xlsx",
                insight_type="numeric_range", semantic_type="Metric", text=text,
                priority_score=0.5, confidence="high",
                suggested_narrative_use=["What"], source_location="S1",
            )


# --------------------------------------------------------------------------- #
# Config defaults & validation
# --------------------------------------------------------------------------- #
class TestConfigMaxTextLength:
    def test_config_default_matches_schema(self):
        assert CONFIG_DEFAULTS["max_text_length"] == MAX_TEXT_LENGTH

    def test_validate_accepts_default(self):
        validate_config(dict(CONFIG_DEFAULTS))

    def test_validate_accepts_lower_value(self):
        cfg = dict(CONFIG_DEFAULTS)
        cfg["max_text_length"] = 500
        validate_config(cfg)

    def test_validate_rejects_zero(self):
        cfg = dict(CONFIG_DEFAULTS)
        cfg["max_text_length"] = 0
        with pytest.raises(ValueError, match="positive integer"):
            validate_config(cfg)

    def test_validate_rejects_negative(self):
        cfg = dict(CONFIG_DEFAULTS)
        cfg["max_text_length"] = -10
        with pytest.raises(ValueError, match="positive integer"):
            validate_config(cfg)

    def test_validate_rejects_non_int(self):
        cfg = dict(CONFIG_DEFAULTS)
        cfg["max_text_length"] = "800"
        with pytest.raises(ValueError, match="positive integer"):
            validate_config(cfg)

    def test_validate_rejects_above_ceiling(self):
        cfg = dict(CONFIG_DEFAULTS)
        cfg["max_text_length"] = MAX_TEXT_LENGTH + 1
        with pytest.raises(ValueError, match="exceeds the schema ceiling"):
            validate_config(cfg)


# --------------------------------------------------------------------------- #
# Preprocessor truncation (truncate, don't drop)
# --------------------------------------------------------------------------- #
@pytest.fixture()
def preprocessor(tmp_path):
    inp = tmp_path / "input"
    out = tmp_path / "output"
    inp.mkdir()
    p = m.ImpactSlidePreprocessorV4(input_path=str(inp), output_dir=str(out))
    return p


class TestValidateEvidenceTruncation:
    def test_short_text_unchanged(self, preprocessor):
        ev = [{
            "evidence_id": "E0001", "source_file": "f.xlsx",
            "insight_type": "numeric_range", "text": "short text",
            "priority_score": 0.5, "confidence": "high",
            "suggested_narrative_use": ["What"], "source_location": "S1",
        }]
        result = preprocessor._validate_evidence(ev)
        assert result[0]["text"] == "short text"

    def test_long_text_truncated_to_cap(self, preprocessor):
        long_text = "A" * 1200
        ev = [{
            "evidence_id": "E0001", "source_file": "f.xlsx",
            "insight_type": "numeric_range", "text": long_text,
            "priority_score": 0.5, "confidence": "high",
            "suggested_narrative_use": ["What"], "source_location": "S1",
        }]
        result = preprocessor._validate_evidence(ev)
        assert len(result[0]["text"]) == MAX_TEXT_LENGTH
        # Last char is the ellipsis (U+2026)
        assert result[0]["text"][-1] == "\u2026"
        assert result[0]["text"][:MAX_TEXT_LENGTH - 1] == "A" * (MAX_TEXT_LENGTH - 1)

    def test_text_at_exactly_cap_not_truncated(self, preprocessor):
        text = "B" * MAX_TEXT_LENGTH
        ev = [{
            "evidence_id": "E0001", "source_file": "f.xlsx",
            "insight_type": "numeric_range", "text": text,
            "priority_score": 0.5, "confidence": "high",
            "suggested_narrative_use": ["What"], "source_location": "S1",
        }]
        result = preprocessor._validate_evidence(ev)
        assert result[0]["text"] == text  # unchanged — no ellipsis added
        assert len(result[0]["text"]) == MAX_TEXT_LENGTH

    def test_truncated_text_passes_schema_validation(self, preprocessor):
        """After truncation, the entry must pass EvidenceEntry validation
        (no schema rejection). This is the core 'truncate, don't drop' guarantee."""
        long_text = "C" * 2000
        ev = [{
            "evidence_id": "E0001", "source_file": "f.xlsx",
            "insight_type": "numeric_range", "text": long_text,
            "priority_score": 0.5, "confidence": "high",
            "suggested_narrative_use": ["What"], "source_location": "S1",
        }]
        result = preprocessor._validate_evidence(ev)
        # The entry survived (not dropped to errors).
        assert len(result) == 1
        # And it directly validates against the schema.
        EvidenceEntry(**result[0])

    def test_user_lowered_cap_applies(self, preprocessor):
        preprocessor.max_text_length = 300
        long_text = "D" * 1000
        ev = [{
            "evidence_id": "E0001", "source_file": "f.xlsx",
            "insight_type": "numeric_range", "text": long_text,
            "priority_score": 0.5, "confidence": "high",
            "suggested_narrative_use": ["What"], "source_location": "S1",
        }]
        result = preprocessor._validate_evidence(ev)
        assert len(result[0]["text"]) == 300
        assert result[0]["text"][-1] == "\u2026"

    def test_default_max_text_length_is_schema_constant(self, preprocessor):
        assert preprocessor.max_text_length == MAX_TEXT_LENGTH

    def test_non_string_text_not_truncated(self, preprocessor):
        """Defensive: if text is missing or not a string, truncation is skipped
        (no crash) and schema validation then drops the entry to errors."""
        ev = [{
            "evidence_id": "E0001", "source_file": "f.xlsx",
            "insight_type": "numeric_range", "text": None,
            "priority_score": 0.5, "confidence": "high",
            "suggested_narrative_use": ["What"], "source_location": "S1",
        }]
        result = preprocessor._validate_evidence(ev)
        # Truncation didn't crash; the entry was dropped by schema validation
        # (text=None is not a valid str) to processing_errors.
        assert result == []
        assert len(preprocessor.errors) == 1


# --------------------------------------------------------------------------- #
# CLI flag --max-text-length
# --------------------------------------------------------------------------- #
class TestCLIMaxTextLength:
    def _run(self, *extra, tmp_path):
        out = tmp_path / "out"
        out.mkdir()
        cmd = [sys.executable, "step1_preprocessor_v4.py",
               "--input", str(tmp_path), "--output", str(out)]
        # Skip actual run — just test arg parsing via --emit-schema which exits early.
        if "--emit-schema" not in extra:
            cmd.append("--emit-schema")
        cmd.extend(extra)
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              cwd=str(Path(__file__).resolve().parent.parent))
        return proc

    def test_cli_flag_accepted(self, tmp_path):
        proc = self._run("--max-text-length", "500", tmp_path=tmp_path)
        assert proc.returncode == 0
        schema = json.loads((tmp_path / "out" / "evidence_schema.json").read_text())
        # The emitted schema always shows the canonical ceiling.
        assert schema["properties"]["text"]["maxLength"] == MAX_TEXT_LENGTH

    def test_cli_flag_above_ceiling_rejected(self, tmp_path):
        proc = self._run("--max-text-length", str(MAX_TEXT_LENGTH + 100),
                         tmp_path=tmp_path)
        # Config validation fails fast → non-zero exit.
        assert proc.returncode != 0
        assert "exceeds the schema ceiling" in proc.stdout or "exceeds the schema ceiling" in proc.stderr

    def test_cli_flag_zero_rejected(self, tmp_path):
        proc = self._run("--max-text-length", "0", tmp_path=tmp_path)
        assert proc.returncode != 0
