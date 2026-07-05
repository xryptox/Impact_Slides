"""
Tests for the Pydantic schema contracts (schemas.py) and the v3 runtime
validation that guards the Evidence Register before it's written.

Covers:
  - EvidenceEntry accepts well-formed entries (including extra optional fields)
  - EvidenceEntry rejects: bad evidence_id, out-of-range priority, unknown
    insight_type, unknown extraction_method, unknown confidence, non-framework
    narrative stage
  - the preprocessor drops schema-invalid entries to processing_errors.json
    instead of writing them (the runtime guarantee)
  - --emit-schema produces a valid JSON Schema file
  - the real-world register validates against the schema
  - FileInventoryItem / CoverageMap / EntitiesSummaryItem contracts
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import step1_preprocessor_v3 as m
from impact_slides.schemas import (EvidenceEntry, FileInventoryItem, CoverageMap,
                     EntitiesSummaryItem, INSIGHT_TYPES, EXTRACTION_METHODS,
                     CONFIDENCE_LEVELS, NARRATIVE_STAGES)

REAL_DIR = Path(r"C:\Users\Ag1Le\Documents\realworld_test\input")


@pytest.fixture()
def make_preprocessor(tmp_workspace):
    """Build a v3 preprocessor (overrides conftest's v2 fixture)."""
    def _make(filter_level="moderate", boost_keywords=None, enable_ocr=False):
        inp = tmp_workspace / "input"
        out = tmp_workspace / "output"
        inp.mkdir(parents=True, exist_ok=True)
        p = m.ImpactSlidePreprocessorV2(
            input_path=str(inp), output_dir=str(out),
            filter_level=filter_level, boost_keywords=boost_keywords or [],
        )
        p.enable_ocr = enable_ocr
        return p, inp, out
    return _make


def _good_entry(**overrides):
    base = {
        "evidence_id": "E0001",
        "source_file": "data.xlsx",
        "insight_type": "numeric_range",
        "text": "Revenue ranges from 10 to 99.",
        "priority_score": 0.85,
        "confidence": "high",
        "suggested_narrative_use": ["What", "How"],
        "source_location": "Sheet1",
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# Acceptance
# --------------------------------------------------------------------------- #
class TestEvidenceEntryAccepts:
    def test_minimal_valid_entry(self):
        EvidenceEntry(**_good_entry())  # no exception

    def test_all_optional_fields(self):
        e = _good_entry(sheet_name="Jan", column_name="Revenue",
                        extraction_method="numeric_range", ocr_used=False,
                        related_files=["a.xlsx", "b.pptx"],
                        boosted_by_rule="recommend", metric_value="23%",
                        metric_type="percentage", table_cell=True,
                        pptx_classification={"type": "data_table"})
        ev = EvidenceEntry(**e)
        # extra fields pass through
        assert ev.related_files == ["a.xlsx", "b.pptx"]
        assert ev.boosted_by_rule == "recommend"

    def test_every_insight_type_accepted(self):
        for t in INSIGHT_TYPES:
            EvidenceEntry(**_good_entry(insight_type=t))

    def test_every_extraction_method_accepted(self):
        for meth in EXTRACTION_METHODS:
            EvidenceEntry(**_good_entry(extraction_method=meth))

    def test_every_confidence_level_accepted(self):
        for c in CONFIDENCE_LEVELS:
            EvidenceEntry(**_good_entry(confidence=c))


# --------------------------------------------------------------------------- #
# Rejection (the core new guarantee)
# --------------------------------------------------------------------------- #
class TestEvidenceEntryRejects:
    def test_bad_evidence_id(self):
        with pytest.raises(Exception):
            EvidenceEntry(**_good_entry(evidence_id="X999"))     # no E prefix
        with pytest.raises(Exception):
            EvidenceEntry(**_good_entry(evidence_id="E999"))     # only 3 digits

    def test_priority_out_of_range(self):
        with pytest.raises(Exception):
            EvidenceEntry(**_good_entry(priority_score=1.5))
        with pytest.raises(Exception):
            EvidenceEntry(**_good_entry(priority_score=-0.1))

    def test_unknown_insight_type(self):
        with pytest.raises(Exception):
            EvidenceEntry(**_good_entry(insight_type="not_a_real_type"))

    def test_unknown_extraction_method(self):
        with pytest.raises(Exception):
            EvidenceEntry(**_good_entry(extraction_method="guessed"))

    def test_unknown_confidence(self):
        with pytest.raises(Exception):
            EvidenceEntry(**_good_entry(confidence="very_high"))

    def test_non_framework_narrative_stage(self):
        with pytest.raises(Exception):
            EvidenceEntry(**_good_entry(suggested_narrative_use=["What", "Maybe"]))

    def test_missing_required_field(self):
        bad = _good_entry()
        del bad["source_location"]
        with pytest.raises(Exception):
            EvidenceEntry(**bad)


# --------------------------------------------------------------------------- #
# Runtime validation in the pipeline
# --------------------------------------------------------------------------- #
class TestRuntimeValidation:
    def test_invalid_entries_dropped_to_errors(self, tmp_workspace):
        """Schema-invalid entries are dropped and logged to processing_errors
        rather than written to the register."""
        if not m._HAS_PYDANTIC:
            pytest.skip("pydantic not installed")

        out = tmp_workspace / "output"
        out.mkdir(parents=True, exist_ok=True)
        p = m.ImpactSlidePreprocessorV2(input_path=".", output_dir=str(out),
                                        filter_level="permissive")
        good = _good_entry(evidence_id="E0001")
        bad_id = _good_entry(evidence_id="BAD_ID")              # violates E####
        bad_prio = _good_entry(evidence_id="E0002", priority_score=2.0)  # out of range
        bad_type = _good_entry(evidence_id="E0003", insight_type="bogus")  # unknown type

        kept = p._validate_evidence([good, bad_id, bad_prio, bad_type])

        assert len(kept) == 1
        assert kept[0]["evidence_id"] == "E0001"
        # all three violations were logged
        assert len(p.errors) == 3
        logged_ids = {e["evidence_id"] for e in p.errors}
        assert logged_ids == {"BAD_ID", "E0002", "E0003"}

    def test_schema_file_emitted_on_normal_run(self, make_excel, make_preprocessor):
        if not m._HAS_PYDANTIC:
            pytest.skip("pydantic not installed")
        import pandas as pd
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_excel(df=pd.DataFrame({"Region": ["N", "S"] * 4, "Revenue": [1, 2] * 4}))
        p.run()
        sch = json.load(open(out / "evidence_schema.json"))
        assert sch["title"] == "EvidenceEntry"
        assert "evidence_id" in sch["required"]


# --------------------------------------------------------------------------- #
# --emit-schema CLI mode
# --------------------------------------------------------------------------- #
class TestEmitSchemaCli:
    def test_emit_schema_writes_valid_json_schema(self, tmp_path):
        if not m._HAS_PYDANTIC:
            pytest.skip("pydantic not installed")
        repo = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, str(repo / "step1_preprocessor_v3.py"),
             "--emit-schema", "--output", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr
        sch = json.load(open(tmp_path / "evidence_schema.json"))
        assert sch["title"] == "EvidenceEntry"
        assert "priority_score" in sch["properties"]


# --------------------------------------------------------------------------- #
# Real-world register validates against the schema
# --------------------------------------------------------------------------- #
class TestRealWorldValidates:
    def test_real_register_passes_schema(self):
        reg = Path(r"C:\Users\Ag1Le\Documents\realworld_test\out_pyd\evidence_register_seed.json")
        if not reg.exists() or not m._HAS_PYDANTIC:
            pytest.skip("real-world output not present or pydantic missing")
        ev = json.load(open(reg))
        assert ev, "expected non-empty register"
        for e in ev:
            EvidenceEntry(**e)  # raises if any entry is malformed


# --------------------------------------------------------------------------- #
# Supporting contracts
# --------------------------------------------------------------------------- #
class TestSupportingModels:
    def test_file_inventory_item(self):
        FileInventoryItem(file_id="F0001", file_name="a.xlsx",
                          absolute_path="/tmp/a.xlsx", category="spreadsheet",
                          access_status="readable")

    def test_file_inventory_rejects_missing(self):
        with pytest.raises(Exception):
            FileInventoryItem(file_id="F0001", file_name="a.xlsx")  # missing fields

    def test_coverage_map(self):
        cm = CoverageMap(total_evidence=10,
                         by_narrative_stage={"Why": 5, "What": 10, "How": 3, "Now": 0},
                         stages_with_no_evidence=["Now"],
                         by_source_file={"a.xlsx": 10},
                         by_insight_type={"numeric_range": 5},
                         avg_priority=0.7)
        assert cm.total_evidence == 10

    def test_coverage_map_rejects_bad_avg(self):
        with pytest.raises(Exception):
            CoverageMap(total_evidence=0, by_narrative_stage={},
                        stages_with_no_evidence=[], by_source_file={},
                        by_insight_type={}, avg_priority=1.5)

    def test_entities_summary_item(self):
        EntitiesSummaryItem(source_file="a.xlsx", sheet="S1", column="Region",
                            top_values=[{"value": "N", "count": 5}])
