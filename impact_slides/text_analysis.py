"""Text-analysis helpers: advanced metric extraction, insight-language
detection, insight-language priority boost, and evidence priority scoring.

Extracted from the monolith. No internal dependencies.
"""
from __future__ import annotations

import re
from typing import Dict, List


def extract_advanced_metrics(text: str) -> List[Dict[str, str]]:
    """
    Advanced metric extraction for PPTX text (Item 4.2).
    Returns list of {'value': str, 'context': str} dicts.
    """
    if not text:
        return []

    metrics = []
    # High-quality patterns for business metrics
    patterns = [
        # Percentage with direction and optional decimal
        (r'([\+\-]?\d+(?:\.\d+)?\s*%)', 'percentage'),
        # Currency amounts (supports $ € £ and K/M/B suffix)
        (r'([\$€£]\s*\d+(?:\.\d+)?\s*[KMB]?)', 'currency'),
        # Multipliers (x or ×)
        (r'(\d+(?:\.\d+)?\s*[×x])', 'multiplier'),
        # Simple ratios/ranges (e.g. 12-18%)
        (r'(\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?\s*%)', 'range'),
    ]

    lines = text.splitlines()
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        for pattern, mtype in patterns:
            for match in re.finditer(pattern, line_stripped):
                value = match.group(1).strip()
                # Store context (the full bullet/sentence)
                context = line_stripped[:120]
                metrics.append({
                    "value": value,
                    "type": mtype,
                    "context": context
                })
    return metrics[:10]  # safety cap


def contains_insight_language(text: str) -> float:
    """
    Returns a score 0-1 indicating how 'insightful' the text sounds.
    Used for Item 4.1 content prioritization.
    """
    if not text:
        return 0.0

    insight_keywords = [
        'recommend', 'recommendation', 'key', 'critical', 'significant',
        'record', 'highest', 'lowest', 'growth', 'decline', 'risk',
        'opportunity', 'important', 'major', 'strongest', 'weakest',
        'outperform', 'underperform', 'increase', 'decrease', 'expand',
        'reduce', 'improve', 'challenge', 'success', 'issue'
    ]

    text_lower = text.lower()
    count = sum(1 for kw in insight_keywords if kw in text_lower)
    # Normalize: more than 4 insight words = max score
    return min(1.0, count / 4.0)


# v3: insight-language priority boost for individual text fragments (bullets,
# paragraphs). Previously only whole slides were boosted; individual bullets all
# landed at a flat 0.75, so "Recommendation: expand" ranked equal to "LogLevel:...".
_INSIGHT_KEYWORDS = [
    'recommend', 'recommendation', 'key', 'critical', 'significant',
    'record', 'highest', 'lowest', 'growth', 'decline', 'risk',
    'opportunity', 'important', 'major', 'strongest', 'weakest',
    'outperform', 'underperform', 'increase', 'decrease', 'expand',
    'reduce', 'improve', 'challenge', 'success', 'issue', 'next step',
    'call to action', 'action plan', 'priority', 'target', 'goal',
]


def insight_priority_boost(text: str, base: float, low: float = 0.0,
                            high: float = 0.25, cap: float = 0.98) -> float:
    """Return base + a boost proportional to insight-language density.

    0 insight keywords -> no boost; >=4 -> ``high`` boost. Capped at ``cap``.
    Used per-bullet / per-paragraph so insight-bearing fragments outrank generic
    list items.
    """
    if not text:
        return base
    t = text.lower()
    count = sum(1 for kw in _INSIGHT_KEYWORDS if kw in t)
    boost = (min(count, 4) / 4.0) * high if count else low
    return round(min(cap, base + boost), 3)


# v4: legal-boilerplate detection patterns. Built-in regex set that
# matches definition/indemnity/reps-and-warranties phrasing common in M&A
# agreements and contracts, so such pages can be downweighted instead of
# dominating the register via the domain-blind `contains_insight_language()`
# heuristic (which fires on words like "risk"/"key"/"important" in legal
# context). The patterns are narrow by design (require the "X means" form,
# a Section reference, or canonical legal clauses) to avoid false-positives on
# ordinary business prose. Shipped ON by default; disabled via the CLI
# `--no-downweight-boilerplate` escape hatch. User substrings added via
# `--downweight-keywords` / YAML extend this set (compiled as word-boundary
# regexes) — mirror of the boost_keywords up-channel.
DEFAULT_LEGAL_BOILERPLATE_PATTERNS = [
    re.compile(r'"[^"]{1,60}"\s+(?:has\s+the\s+meaning|means)\b', re.IGNORECASE),
    re.compile(r'\bhas\s+the\s+meaning\s+set\s+forth\s+in\s+Section\b', re.IGNORECASE),
    re.compile(r'"[^"]{1,60}"\s+shall\s+have\s+the\s+meaning\b', re.IGNORECASE),
    re.compile(r'\bSection\s+\d+(?:\.\d+)+\b'),
    re.compile(r'\b(?:Indemnif\w*|indemnitee|indemnitor)\b', re.IGNORECASE),
    re.compile(r'\bGroup\s+Companies\b', re.IGNORECASE),
    re.compile(r'\bReps\s+and\s+Warranties\b', re.IGNORECASE),
    re.compile(r'\bSurvival\s+of\s+(?:the\s+)?Representations\b', re.IGNORECASE),
    re.compile(r'\bhereby\s+(?:\w+\s+){0,2}(?:sells|assigns|transfers|conveys)\b', re.IGNORECASE),
    re.compile(r'\bgiving\s+effect\s+to\s+the\s+Closing\b', re.IGNORECASE),
    re.compile(r'\bDispute\s+Notice\b', re.IGNORECASE),
    re.compile(r'\bClosing\s+Date\b', re.IGNORECASE),
]


def calculate_evidence_priority_score(
    column_name: str,
    column_type: str,
    is_identifier: bool = False,
    unique_ratio: float = 0.0,
    non_null_ratio: float = 1.0,
    has_business_name: bool = True
) -> float:
    """Calculate priority score for evidence (higher = more useful)."""
    if is_identifier:
        return 0.15

    score = 0.5
    if column_type == "numeric":
        score += 0.25
    elif column_type == "categorical":
        score += 0.20
    elif column_type == "date":
        score += 0.15

    if column_type == "categorical" and unique_ratio > 0.7:
        score -= 0.25
    if not has_business_name:
        score -= 0.15

    score += (non_null_ratio - 0.5) * 0.2
    return max(0.0, min(1.0, round(score, 3)))
