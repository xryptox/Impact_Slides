"""
Pydantic schemas for the Impact Slide Preprocessor v3 outputs.

These models are the single source of truth for the contracts the preprocessor
writes to disk and the Impact Slide Analyst GPT (Step 2) consumes. Defining
them here means:

  - the schema can't drift out of sync between the README, the Python code,
    and the Analyst GPT prompt (they all derive from these classes);
  - the preprocessor validates every entry before writing it (a malformed
    entry becomes a processing_errors.json record instead of silent bad data);
  - EvidenceEntry.model_json_schema() produces a precise JSON Schema that can
    be embedded directly into the Analyst GPT instructions.

Run `python step1_preprocessor_v3.py --emit-schema` to (re)generate
`evidence_schema.json` from these models.
"""
from __future__ import annotations

from typing import List, Optional, Any, Dict

from pydantic import BaseModel, ConfigDict, Field

# --------------------------------------------------------------------------- #
# Enumerations (kept as plain strings via Literal-free validation so that
# adding a new type is a one-line change here). Listed explicitly so unknown
# values are rejected at validation time.
# --------------------------------------------------------------------------- #
INSIGHT_TYPES = {
    "numeric_range",
    "categorical_distribution",
    "multi_column_suggestion",
    "pptx_slide_insight",
    "chart_insight",
    "chart_data_insight",
    "table_cell",
    "table_insight",
    "text_metric",
    "bullet_insight",
    "process_step",
    "speaker_notes_insight",
    "emphasized_text",
    "section_divider",
    "pdf_page_insight",
    "pdf_ocr_page_insight",
    "pdf_table_insight",
    "pdf_table_cell",
    "docx_insight",
    "trend_insight",
    "aggregate_insight",
    "outlier_insight",
    "correlation_insight",
    "period_trend_insight",
    "cross_file_metric",
}

EXTRACTION_METHODS = {
    "computed", "chart_data", "numeric_range", "categorical",
    "table_cell", "text_layer", "ocr", "bullet", "paragraph",
    "cross_file", "classifier", "unknown",
}

CONFIDENCE_LEVELS = {"high", "medium", "low"}
NARRATIVE_STAGES = {"Why", "What", "How", "Now"}


def _validate_in(value: str, allowed: set, field_name: str) -> str:
    if value not in allowed:
        raise ValueError(
            f"{field_name}={value!r} is not one of the allowed values {sorted(allowed)}"
        )
    return value


# --------------------------------------------------------------------------- #
# Core contract: one evidence entry
# --------------------------------------------------------------------------- #
class EvidenceEntry(BaseModel):
    """A single source-backed insight in the Evidence Register.

    The Analyst GPT treats a list of these as its 'source of truth' and must
    preserve `evidence_id` values. Every field that has a constrained value
    set is validated; extra fields the preprocessor may attach
    (boosted_by_rule, related_files, pptx_classification, group_by,
    metric_value, metric_type, table_cell) are allowed through unchanged.
    """
    model_config = ConfigDict(extra="allow")

    evidence_id: str = Field(pattern=r"^E\d{4}$",
                             description="Unique ID preserved by the Analyst GPT.")
    source_file: str = Field(description="Real input file this insight came from.")
    insight_type: str = Field(description="One of the known insight types.")
    text: str = Field(description="Human-readable insight text.")
    priority_score: float = Field(ge=0.0, le=1.0,
                                  description="Priority 0–1; register is sorted descending.")
    confidence: str = Field(description="Reliability level (high | medium | low).")
    suggested_narrative_use: List[str] = Field(
        description="Subset of the Why/What/How/Now framework stages.")
    source_location: str = Field(description="Sheet / Slide N / Page N / Cross-file.")

    # Optional, common fields
    sheet_name: Optional[str] = None
    column_name: Optional[str] = None
    extraction_method: Optional[str] = None
    ocr_used: Optional[bool] = None
    # v3 #20: semantic dedup provenance — when a near-duplicate is merged into
    # this surviving entry, the dropped entry's source file(s) and evidence id(s)
    # are recorded here so source provenance is preserved.
    dedup_merged_sources: Optional[List[str]] = None
    dedup_merged_ids: Optional[List[str]] = None

    # --- validators -------------------------------------------------------- #
    @classmethod
    def _validate_insight_type(cls, v: str) -> str:
        return _validate_in(v, INSIGHT_TYPES, "insight_type")

    @classmethod
    def _validate_extraction_method(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _validate_in(v, EXTRACTION_METHODS, "extraction_method")

    @classmethod
    def _validate_confidence(cls, v: str) -> str:
        return _validate_in(v, CONFIDENCE_LEVELS, "confidence")

    @classmethod
    def _validate_stages(cls, v: List[str]) -> List[str]:
        for s in v:
            _validate_in(s, NARRATIVE_STAGES, "suggested_narrative_use")
        return v

    # Pydantic v2 field validators (plain functions to avoid decorator import).
    from pydantic import field_validator
    _v_insight = field_validator("insight_type")(_validate_insight_type)
    _v_method = field_validator("extraction_method")(_validate_extraction_method)
    _v_conf = field_validator("confidence")(_validate_confidence)
    _v_stages = field_validator("suggested_narrative_use")(_validate_stages)


# --------------------------------------------------------------------------- #
# Supporting contracts
# --------------------------------------------------------------------------- #
class FileInventoryItem(BaseModel):
    """One row of file_inventory.json."""
    model_config = ConfigDict(extra="allow")
    file_id: str
    file_name: str
    absolute_path: str
    category: str
    access_status: str


class CoverageMap(BaseModel):
    """coverage_map.json — where evidence is thin before the GPT reasons."""
    model_config = ConfigDict(extra="allow")
    total_evidence: int = Field(ge=0)
    by_narrative_stage: Dict[str, int]
    stages_with_no_evidence: List[str]
    by_source_file: Dict[str, int]
    by_insight_type: Dict[str, int]
    avg_priority: float = Field(ge=0.0, le=1.0)


class EntitiesSummaryItem(BaseModel):
    """One row of entities_summary.json (top values for one categorical column)."""
    model_config = ConfigDict(extra="allow")
    source_file: str
    sheet: str
    column: str
    top_values: List[Dict[str, Any]]


__all__ = [
    "EvidenceEntry", "FileInventoryItem", "CoverageMap", "EntitiesSummaryItem",
    "INSIGHT_TYPES", "EXTRACTION_METHODS", "CONFIDENCE_LEVELS", "NARRATIVE_STAGES",
]
