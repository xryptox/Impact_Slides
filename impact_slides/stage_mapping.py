"""Why/What/How/Now stage-mapping default tables (v3 #24).

These four tables are the single source of truth that replaces ~20 scattered
hardcoded ``suggested_narrative_use`` literals. Users can override any layer
via the ``stage_rules`` YAML config key.

  1. ``DEFAULT_INSIGHT_TYPE_STAGES``  — insight_type -> stages
  2. ``DEFAULT_KEYWORD_STAGE_OVERRIDES`` — text-regex -> stages (post-assignment
     override; first match wins)
  3. ``DEFAULT_SLIDE_TYPE_KEYWORDS`` / ``DEFAULT_SLIDE_TYPE_STAGES`` —
     slide-title keyword -> slide type, and slide type -> stages
  4. ``DEFAULT_CONCLUSION_BULLET_STAGES`` — conclusion-bullet override

The build/validate/lookup logic (``build_stage_rules`` / ``validate_stage_rules``
/ ``stages_for``) lives on the preprocessor trunk for now (Phase 2 will extract
it here). This module currently holds only the *data*.
"""
from __future__ import annotations

from typing import Dict, List

# Layer 1: default insight_type -> stages.
DEFAULT_INSIGHT_TYPE_STAGES: Dict[str, List[str]] = {
    "numeric_range":            ["What", "How"],
    "categorical_distribution": ["Why", "What"],
    "category_by_metric_suggestion": ["How", "What"],
    "trend_insight":            ["How", "What", "Why"],
    "period_trend_insight":    ["How", "What", "Why"],
    "outlier_insight":         ["What", "How"],
    "correlation_insight":    ["How", "What"],
    "aggregate_insight":        ["How", "What"],
    "multi_column_suggestion":  ["How", "What"],
    "chart_insight":            ["How", "What"],
    "chart_data_insight":       ["How", "What"],
    "table_cell":               ["What"],
    "table_insight":            ["What", "Why"],
    "text_metric":              ["How", "What"],
    "process_step":            ["How", "What"],
    "speaker_notes_insight":    ["How", "Why"],
    "emphasized_text":          ["What", "How"],
    "section_divider":          ["What"],
    "pdf_page_insight":         ["What"],
    "pdf_ocr_page_insight":     ["What"],
    "pdf_table_insight":        ["What"],
    "pdf_table_cell":           ["What"],
    "docx_insight":             ["What"],
    "cross_file_metric":        ["How", "Why"],
    "bullet_insight":           ["What", "Why"],
}

# Layer 2: default text-keyword -> stages overrides (first match wins).
# Applied AFTER the insight-type lookup so a user can redirect any evidence by
# its text regardless of insight_type. Empty by default — the conclusion-bullet
# "Now" logic is handled in build_evidence_register via slide_type, not here.
DEFAULT_KEYWORD_STAGE_OVERRIDES: List = []

# Layer 3a: slide-title keyword -> slide type (extends classify_slide).
DEFAULT_SLIDE_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "conclusion": ["summary", "conclusion", "key takeaway", "recommendation",
                   "next step", "call to action", "key findings", "action plan"],
    "agenda":     ["agenda", "overview", "contents", "table of contents", "roadmap"],
    "section":    ["section", "part ", "chapter", "module"],
    "thank_you":  ["thank you", "thanks", "q&a", "questions", "contact"],
    "comparison": ["vs", "versus", "comparison", "compare", "before", "after"],
}

# Layer 3b: slide type -> stages (overrides recommended_evidence_types).
DEFAULT_SLIDE_TYPE_STAGES: Dict[str, List[str]] = {
    "title":            ["What", "Why"],
    "agenda":           ["What", "Why"],
    "section":          ["What"],
    "thank_you":        ["What"],
    "conclusion":       ["What", "How", "Why", "Now"],
    "data_mixed":        ["How", "What"],
    "data_chart":       ["How", "What"],
    "data_table":       ["What", "Why"],
    "diagram_process":  ["How", "What"],
    "comparison":       ["What", "Why"],
    "quote_callout":    ["What", "Why"],
    "content_insight":  ["What", "Why"],
    "content_light":    ["What", "Why"],
    "low_value":        ["What"],
}

# Conclusion-bullet stage override: bullets from conclusion slides get "Now".
DEFAULT_CONCLUSION_BULLET_STAGES: List[str] = ["Now", "What", "Why"]
