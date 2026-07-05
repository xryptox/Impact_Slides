"""Column / value heuristics: identifier detection, system-column detection,
noise-cell detection, sheet-time-rank, and unique-column-name construction.

Extracted from the monolith. Depends only on `text_utils` (clean_text,
get_column_letter) and pandas.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, List, Optional

import pandas as pd

from .text_utils import clean_text, get_column_letter

# v3: time-order detection for spreadsheet sheets. Used to decide whether
# per-sheet numeric ranges can be connected into a trend across time.
_MONTH_RE = re.compile(r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*',
                       re.IGNORECASE)
_QUARTER_RE = re.compile(r'^q[1-4]\b', re.IGNORECASE)
_YEAR_RE = re.compile(r'^(19|20)\d{2}\b')


def sheet_time_rank(sheet_name: str) -> Optional[int]:
    """Return a sortable integer rank for a sheet that looks time-ordered
    (month / quarter / year), else None. Months rank 1..12, quarters 1..4
    (×100), years as their numeric value (×10000). Two sheets that both rank
    non-None are considered part of one time series."""
    s = clean_text(sheet_name).lower()
    if not s:
        return None
    m = _MONTH_RE.match(s)
    if m:
        return {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}[m.group(1)]
    q = _QUARTER_RE.match(s)
    if q:
        return int(q.group(0)[1]) * 100
    y = _YEAR_RE.match(s)
    if y:
        return int(y.group(0)) * 10000
    return None


def _parse_numeric_token(token: str) -> Optional[float]:
    """Parse a numeric value out of a finding text like 'ranges from 10.53 to 99.96.'"""
    nums = re.findall(r'-?\d+(?:\.\d+)?', token or "")
    if nums:
        try:
            return float(nums[0])
        except ValueError:
            return None
    return None


def make_unique_columns(values: List[Any]) -> List[str]:
    cols = []
    counts: Dict[str, int] = defaultdict(int)
    for idx, value in enumerate(values, 1):
        base = clean_text(value) or f"Column {get_column_letter(idx)}"
        base = base[:80]
        counts[base] += 1
        cols.append(base if counts[base] == 1 else f"{base}_{counts[base]}")
    return cols


def is_likely_identifier_column(col_name: str, series: pd.Series) -> bool:
    """Detect common ID / Serial Number columns.

    Two signals are used:
      1. The column name matches common identifier names (S.No, ID, Serial,
         Row, Key, Index, Number, Seq, UUID, GUID) -> identifier (strong signal).
      2. The column is unnamed/generic AND its values form a contiguous
         ascending integer row index (1..N or 0..N-1) -> identifier.

    A sequential-by-1 numeric column with a real business name (e.g. a metric
    that happens to increment by exactly 1) is NOT treated as an identifier,
    so genuine business data is not misfiltered. Likewise a descending-by-1
    sequence is not treated as an ID on its own (rare for IDs, common for
    metrics/rankings).
    """
    col_lower = clean_text(col_name).lower()
    id_patterns = [r'\bs\.?no\.?\b', r'\bserial\b', r'\bseq\b', r'\brow\b',
                   r'\bid\b', r'\bkey\b', r'\bindex\b', r'\bnumber\b', r'\buuid\b', r'\bguid\b']
    if any(re.search(p, col_lower) for p in id_patterns):
        return True

    # Only infer an identifier from the *value* pattern when the column is
    # unnamed/generic. A named business column that increments by 1 is almost
    # always a real metric, not an ID.
    is_generic_name = (not col_lower) or col_lower.startswith("column ")
    if not is_generic_name:
        return False

    numeric = pd.to_numeric(series, errors="coerce")
    if not (numeric.notna().all() and len(numeric) > 1):
        return False

    # IDs are whole numbers.
    if not (numeric == numeric.astype("int64")).all():
        return False

    # Must be a contiguous ascending row index starting at 0 or 1: e.g.
    # 1,2,3,...,N  or  0,1,2,...,N-1. No gaps, no duplicates, no negatives.
    diffs = numeric.diff().dropna()
    min_val = int(numeric.min())
    max_val = int(numeric.max())
    is_row_index = (
        (diffs == 1).all()
        and min_val in (0, 1)
        and (max_val - min_val + 1) == len(numeric)
        and numeric.is_unique
    )
    return bool(is_row_index)


def is_generic_system_column(col_name: str) -> bool:
    """Detect common system/technical columns that are rarely useful in presentations."""
    col_lower = clean_text(col_name).lower()
    system_patterns = [
        r'created', r'modified', r'updated', r'last_', r'insert', r'delete',
        r'guid', r'uuid', r'hash', r'checksum', r'internal', r'system',
        r'flag', r'is_', r'has_', r'enabled', r'active_flag'
    ]
    return any(re.search(p, col_lower) for p in system_patterns)


# Patterns that mark a PPTX table cell as technical noise rather than a
# business insight. Used by the table-cell priority scorer to stop IPs / URLs /
# user-agents / HTTP requests from outranking real evidence.
_NOISE_CELL_PATTERNS = [
    re.compile(r'^\d{1,3}(?:\.\d{1,3}){3}$'),                       # IPv4 address
    re.compile(r'^[0-9a-fA-F]{0,4}(?::[0-9a-fA-F]{0,4}){2,7}$'),    # IPv6-ish
    re.compile(r'^https?://', re.IGNORECASE),                       # URL
    re.compile(r'^www\.', re.IGNORECASE),                           # URL
    re.compile(r'\.(?:html?|php|cgi|jpg|jpeg|png|gif|css|js|pdf)(?:\?|$)', re.IGNORECASE),  # file path / asset
    re.compile(r'^(?:GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\s+', re.IGNORECASE),            # HTTP request line
    re.compile(r'Mozilla|Gecko|AppleWebKit|Trident|Firefox|Chrome|Safari|MSIE', re.IGNORECASE),  # user-agent
    re.compile(r'^\[\d{1,2}/[A-Za-z]{3}/\d{4}'),                    # CLF log timestamp [09/Apr/2008:07:46:54 +0000]
    re.compile(r'^/(?:[\w.-]+/)+[\w.-]*$'),                         # unix-style path
    re.compile(r'^[A-Za-z]:\\', re.IGNORECASE),                    # windows path
]


def _looks_like_noise_cell(val: str) -> bool:
    """Return True if a table-cell value looks like technical noise (IP, URL,
    user-agent, file path, HTTP request, log timestamp) rather than a business
    insight. Such cells are demoted in priority so they don't outrank real
    evidence."""
    v = (val or "").strip()
    if not v or len(v) > 300:
        return False
    return any(p.search(v) for p in _NOISE_CELL_PATTERNS)
