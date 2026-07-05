"""Cross-file entity matching helpers (v3 #17–#19).

Abbreviation expansion + fuzzy matching + word-boundary detection, so
business-deck entities are linked even when phrased differently across files
(e.g. "US" <-> "United States", "North America" <-> "North",
"EMEA" <-> "Europe, Middle East, Africa").

Pure module: depends only on `text_utils.clean_text` and `dedup._text_similarity`.
The orchestration (`_find_cross_file_relationships`) stays on the trunk because
it reads `self.excel_profiles`, `self.boost_keywords`, `self._stages_for`, and
writes `self._entity_mention_stats`.
"""
from __future__ import annotations

import re

from .text_utils import clean_text
from .dedup import _text_similarity

# Bidirectional abbreviation table (lowercase). Each entry maps a short form
# to its expansion(s); the matcher treats both directions as the same entity.
_ABBREVIATIONS = {
    "us": ["united states", "usa", "u.s.", "u.s.a."],
    "uk": ["united kingdom", "u.k.", "britain", "great britain"],
    "eu": ["european union", "e.u."],
    "emea": ["europe middle east africa", "europe, middle east, africa"],
    "apac": ["asia pacific", "asia-pacific"],
    "latam": ["latin america"],
    "na": ["north america"],
    "yoy": ["year over year", "year-over-year"],
    "qoq": ["quarter over quarter", "quarter-over-quarter"],
    "mom": ["month over month", "month-over-month"],
    "kpi": ["key performance indicator"],
    "roi": ["return on investment"],
    "cagr": ["compound annual growth rate"],
    "capex": ["capital expenditure", "capital expense"],
    "opex": ["operating expenditure", "operating expense"],
    "gaap": ["generally accepted accounting principles"],
}


def _entity_aliases(entity: str) -> set:
    """Return all aliases for an entity (itself + abbreviation expansions + the
    short form of any expansion it contains). Lowercased."""
    e = clean_text(entity).lower()
    if not e:
        return set()
    aliases = {e}
    # short form -> expansions
    if e in _ABBREVIATIONS:
        aliases.update(_ABBREVIATIONS[e])
    # if the entity *is* an expansion, add its short form
    for short, exps in _ABBREVIATIONS.items():
        if e in exps:
            aliases.add(short)
    # if the entity contains an expansion as a word, add the short form too
    # (e.g. "united states sales" -> also match "us")
    for short, exps in _ABBREVIATIONS.items():
        for exp in exps:
            if re.search(rf"\b{re.escape(exp)}\b", e):
                aliases.add(short)
    return aliases


def _entity_in_text(entity: str, text: str, fuzzy_threshold: float = 0.88) -> bool:
    """True if an entity is mentioned in text, using (1) abbreviation/alias
    expansion, (2) word-boundary substring match, and (3) optional fuzzy
    matching for near-spellings (rapidfuzz if available, else difflib)."""
    t = (text or "").lower()
    if not t:
        return False
    for alias in _entity_aliases(entity):
        a = clean_text(alias).lower()
        if not a:
            continue
        # word-boundary substring: robust for all lengths (not just <=4)
        if re.search(rf"\b{re.escape(a)}\b", t):
            return True
    # fuzzy: check each whitespace-delimited token span against the entity.
    # Only triggered for entities that look like single proper-noun tokens to
    # keep it cheap and avoid false positives on common words.
    e = clean_text(entity).lower()
    if len(e) >= 4 and " " not in e:
        for tok in re.findall(r"[a-z][a-z0-9.'-]+", t):
            if len(tok) < 4:
                continue
            if _text_similarity(e, tok) >= fuzzy_threshold:
                return True
    return False
