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
# Canonical limits (schema = single source of truth). config.py / cli.py /
# preprocessor.py all reference these so the contract can't drift out of sync.
# --------------------------------------------------------------------------- #
#: Maximum length (characters) of the `text` field on every EvidenceEntry.
#: Applied uniformly at validation time so the register stays compact and the
#: Analyst GPT token budget is predictable. Overridable via --max-text-length
#: / YAML, but the schema always enforces this as the hard ceiling.
MAX_TEXT_LENGTH = 800

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

# --------------------------------------------------------------------------- #
# v4: semantic_type — a GPT-friendly 4-bucket categorization (Metric/Claim/
# Quote/Risk) that sits alongside the 25-value insight_type. The preprocessor
# assigns it deterministically from insight_type (DEFAULT_SEMANTIC_TYPE_MAP)
# with a keyword-override layer (DEFAULT_SEMANTIC_KEYWORD_OVERRIDES) that
# reclassifies risk-language evidence to "Risk" regardless of insight_type.
# Mirrors the stage_mapping 3-layer pattern (data here, build/lookup on the
# trunk). Both tables derive from the schema so the README, code, and Analyst
# GPT prompt can't drift out of sync.
# --------------------------------------------------------------------------- #
SEMANTIC_TYPES = {"Metric", "Claim", "Quote", "Risk"}

#: Deterministic insight_type -> semantic_type map. Every INSIGHT_TYPES member
#: must appear here (enforced by tests). The three ambiguous structural types
#: (process_step, section_divider, multi_column_suggestion) default to Claim
#: (the safe catch-all — not a hard number, not a verbatim quote).
DEFAULT_SEMANTIC_TYPE_MAP: Dict[str, str] = {
    # --- Metric (hard numbers / computed stats / chart values) ---
    "numeric_range": "Metric",
    "categorical_distribution": "Metric",
    "aggregate_insight": "Metric",
    "trend_insight": "Metric",
    "period_trend_insight": "Metric",
    "outlier_insight": "Metric",
    "correlation_insight": "Metric",
    "chart_data_insight": "Metric",
    "chart_insight": "Metric",
    "text_metric": "Metric",
    "cross_file_metric": "Metric",
    "table_cell": "Metric",
    "table_insight": "Metric",
    "pdf_table_insight": "Metric",
    "pdf_table_cell": "Metric",
    # --- Claim (prose assertions / slide-level statements) ---
    "bullet_insight": "Claim",
    "pptx_slide_insight": "Claim",
    "pdf_page_insight": "Claim",
    "pdf_ocr_page_insight": "Claim",
    "docx_insight": "Claim",
    "process_step": "Claim",            # ambiguous -> safe catch-all
    "section_divider": "Claim",        # ambiguous -> safe catch-all
    "multi_column_suggestion": "Claim",# ambiguous (it's a suggestion) -> catch-all
    # --- Quote (verbatim speaker / emphasized text) ---
    "speaker_notes_insight": "Quote",
    "emphasized_text": "Quote",
}

#: Keyword-override layer: (regex_pattern, semantic_type) tuples, applied
#: AFTER the insight-type map (first match in `text` wins). Surfaces risk
#: language as "Risk" regardless of insight_type. Users extend this set via
#: the `semantic_type_keywords` config key (plain substrings -> word-boundary
#: regexes, all mapped to "Risk").
DEFAULT_SEMANTIC_KEYWORD_OVERRIDES: List = [
    (r"\brisks?\b|\bexposure\b|\bvolatil\w*\b|\bheadwind\w*\b|\bvulnerab\w*\b|\bdownside\b|\buncertain\w*\b", "Risk"),
]


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
    # v4: GPT-friendly 4-bucket category assigned by the preprocessor from
    # insight_type + a risk-keyword override layer. Optional in the SCHEMA
    # (default None) so the frozen v2/v3 regression baselines — which share
    # this schema but don't assign the field — still validate cleanly; the v4
    # chokepoint (_validate_evidence) always populates a real value, so every
    # v4-generated register the Analyst GPT consumes carries it.
    semantic_type: Optional[str] = Field(
        default=None,
        description="GPT-friendly category: one of "
                   f"{sorted(SEMANTIC_TYPES)}. Assigned by the v4 preprocessor "
                   "(insight_type map + risk-keyword override); preserved by the "
                   "Analyst GPT. None on legacy v2/v3 registers.")
    text: str = Field(max_length=MAX_TEXT_LENGTH,
                             description="Human-readable insight text (truncated to "
                                        f"{MAX_TEXT_LENGTH} chars by the preprocessor).")
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
    def _validate_semantic_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _validate_in(v, SEMANTIC_TYPES, "semantic_type")

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
    _v_semantic = field_validator("semantic_type")(_validate_semantic_type)
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


# --------------------------------------------------------------------------- #
# v4: Analyst Briefing contracts
# --------------------------------------------------------------------------- #
class StageScore(BaseModel):
    """Per-stage (Why/What/How/Now) readiness sub-score."""
    model_config = ConfigDict(extra="allow")
    stage: str
    score: int = Field(ge=0, le=100)
    evidence_count: int = Field(ge=0)
    avg_priority: float = Field(ge=0.0, le=1.0)
    note: Optional[str] = None


class NarrativeReadiness(BaseModel):
    """Composite Narrative Readiness Score (0-100) + per-stage breakdown."""
    model_config = ConfigDict(extra="allow")
    overall_score: int = Field(ge=0, le=100)
    components: Dict[str, float] = Field(
        description="5 component sub-scores (0-100): coverage_balance, "
                   "priority_quality, cross_file_connectivity, "
                   "recommendation_strength, signal_ratio.")
    stage_scores: Dict[str, StageScore]
    explanation: str


class FocusArea(BaseModel):
    """A ranked, multi-signal-scored business theme the analyst should focus on."""
    model_config = ConfigDict(extra="allow")
    rank: int = Field(ge=1)
    area: str
    score: float = Field(ge=0.0, le=100.0)
    reason: str
    evidence_count: int = Field(ge=0)
    dominant_stages: List[str]
    top_evidence_ids: List[str] = Field(default_factory=list)


class AnalystBriefing(BaseModel):
    """analyst_briefing.json — the condensed strategic handoff to Step 2."""
    model_config = ConfigDict(extra="allow")
    run_id: str
    source_folder: str
    total_evidence: int = Field(ge=0)
    average_priority: float = Field(ge=0.0, le=1.0)
    narrative_readiness: NarrativeReadiness
    top_cross_file_relationships: List[Dict[str, Any]]
    suggested_focus_areas: List[FocusArea]
    quality_flags: List[str]
    recommendations: List[str]


__all__ = [
    "EvidenceEntry", "FileInventoryItem", "CoverageMap", "EntitiesSummaryItem",
    "StageScore", "NarrativeReadiness", "FocusArea", "AnalystBriefing",
    "INSIGHT_TYPES", "EXTRACTION_METHODS", "CONFIDENCE_LEVELS", "NARRATIVE_STAGES",
    "MAX_TEXT_LENGTH",
    "SEMANTIC_TYPES", "DEFAULT_SEMANTIC_TYPE_MAP", "DEFAULT_SEMANTIC_KEYWORD_OVERRIDES",
]
