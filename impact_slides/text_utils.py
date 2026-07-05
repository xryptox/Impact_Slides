"""Text + Excel value utilities (pure helpers, no module state).

Extracted from the monolith so evidence-construction call sites can read the
helpers in a single, small module instead of paginating the 4,400-line
preprocessor file. No internal dependencies.
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Optional

import pandas as pd

# v3 #6 / #9: provenance + reliability-based confidence.
# Each evidence entry gets an `extraction_method` (how the insight was derived)
# and a confidence level keyed to the reliability of that method, so the
# Analyst GPT can weight computed/chart data higher than OCR'd text.
_METHOD_RELIABILITY = {
    # method           -> confidence
    "computed":        "high",   # trend / aggregate — derived from raw data
    "chart_data":      "high",   # numeric values read from a chart series
    "numeric_range":   "high",   # min/max computed from a column
    "categorical":     "high",   # distribution computed from a column
    "table_cell":      "medium", # a cell value (may be example noise)
    "text_layer":      "high",   # PDF native text layer
    "ocr":             "medium", # Tesseract OCR (prone to artifacts)
    "bullet":          "medium", # a slide bullet line
    "paragraph":       "medium", # a docx paragraph
    "cross_file":      "medium", # inferred relationship
    "classifier":      "medium", # slide-classification derived
    "unknown":         "medium",
}


def clean_text(text: Any) -> str:
    if pd.isna(text):
        return ""
    return str(text).strip()


def get_column_letter(col_idx: int) -> str:
    result = ""
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        result = chr(65 + remainder) + result
    return result


def excel_addr(row: int, col: int) -> str:
    return f"{get_column_letter(col)}{row}"


def safe_stat(values: Iterable[float], fn) -> Optional[float]:
    vals = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    if not vals:
        return None
    try:
        return round(float(fn(vals)), 4)
    except Exception:
        return None


def compact_value(v: Any) -> Any:
    if pd.isna(v):
        return None
    if isinstance(v, float):
        return round(v, 4)
    return v


def confidence_for_method(method: str) -> str:
    """Return the reliability-based confidence for an extraction method."""
    return _METHOD_RELIABILITY.get(method, _METHOD_RELIABILITY["unknown"])
