"""Presenter-deliverable spoken notes (claim prose; bridge notes-only)."""
from __future__ import annotations

import re
from typing import Any, Mapping

from .strip import parse_cite_from_quote, strip_eids

_STAGE = re.compile(
    r"^(hold for|make the room feel|leave them with|setup beat|pressure:|"
    r"when we leave this slide|up next|this sets up|bridge:|story beat)",
    re.I,
)
_READINESS = re.compile(
    r"figures are directional under readiness|"
    r"readiness(?:\s+score)?\s*(?:is\s*)?\d+|"
    r"under readiness\s*\d+",
    re.I,
)
_EID = re.compile(r"\bE\d{4}\b")


def _clean_builder_notes(raw: str) -> str:
    s = strip_eids(raw or "")
    s = _READINESS.sub("", s)
    parts = []
    for sent in re.split(r"(?<=[.!?])\s+", s):
        t = sent.strip()
        if not t:
            continue
        if _STAGE.search(t):
            continue
        if _EID.search(t):
            t = _EID.sub("", t).strip(" ,;")
        if t:
            parts.append(t)
    return " ".join(parts).strip()


def _bridge_as_claim(bridge: str, next_title: str) -> str:
    b = strip_eids(bridge or "").strip()
    if not b:
        return ""
    if _STAGE.search(b) or _READINESS.search(b):
        return ""
    low = b.lower()
    if low.startswith(("next:", "this sets up", "up next", "when we leave")):
        # Convert to claim-ish open question if possible
        rest = re.sub(
            r"^(next:|this sets up(?: the next move:)?|up next:?|when we leave this slide,?)\s*",
            "",
            b,
            flags=re.I,
        ).strip()
        if rest and not rest.lower().startswith(next_title.lower()[:12] if next_title else "\0"):
            return rest[0].upper() + rest[1:] if rest else ""
        return ""
    if "keep this open through close" in low:
        return ""
    return b


def build_spoken_notes(slide: Mapping[str, Any], next_title: str = "") -> str:
    """3–5 claim sentences; ~40–100 words preferred."""
    content = slide.get("content") or {}
    packing = (slide.get("packing_mode") or "").lower()
    layout = (slide.get("layout_type") or "").lower()
    is_cover = (
        packing == "cover-led"
        or layout == "title_or_opening"
        or int(slide.get("slide_number") or 0) == 1
    )

    builder = _clean_builder_notes(str(slide.get("speaker_notes") or ""))
    takeaway = strip_eids(slide.get("audience_takeaway") or "")
    purpose = strip_eids(slide.get("purpose") or "")
    headline = strip_eids(content.get("headline") or slide.get("title") or "")
    so_what = strip_eids(content.get("so_what") or "")
    bridge = _bridge_as_claim(
        content.get("narrative_bridge") or slide.get("narrative_bridge") or "",
        next_title,
    )

    chunks: list[str] = []

    if is_cover:
        if builder and len(builder.split()) >= 12:
            return _cap_words(builder, 100)
        title = strip_eids(slide.get("title") or "this case")
        chunks.append(
            f"We're walking the investment committee through {title}."
        )
        if purpose:
            chunks.append(purpose if purpose.endswith(".") else purpose + ".")
        elif takeaway:
            chunks.append(takeaway if takeaway.endswith(".") else takeaway + ".")
        if so_what:
            chunks.append(so_what if so_what.endswith(".") else so_what + ".")
        return _cap_words(" ".join(chunks), 90)

    if builder and len(builder.split()) >= 18 and not _STAGE.search(builder):
        base = builder
        if bridge and bridge.lower() not in base.lower():
            base = base.rstrip(".") + ". " + (bridge if bridge.endswith(".") else bridge + ".")
        return _cap_words(base, 110)

    # Layout-aware assembly
    if layout == "quote_card":
        vs = slide.get("visual_spec") or {}
        pv = (vs.get("primary_visual") or {}) if isinstance(vs, dict) else {}
        steps = pv.get("steps_or_data") or []
        voices = []
        for st in steps[:3]:
            if isinstance(st, dict):
                cite = parse_cite_from_quote(st.get("text") or st.get("quote"), st.get("attribution"))
                if cite:
                    voices.append(cite.split(" — ")[0])
            elif isinstance(st, str) and "said " in st:
                cite = parse_cite_from_quote(st)
                if cite:
                    voices.append(cite.split(" — ")[0])
        if voices:
            chunks.append(
                "Three operators put the same thesis on the table: "
                + ", ".join(voices[:-1])
                + (" and " + voices[-1] if len(voices) > 1 else voices[0])
                + "."
            )
        else:
            chunks.append(headline + "." if headline and not headline.endswith(".") else headline or "Leaders frame the deal in their own words.")
        if takeaway:
            chunks.append(takeaway if takeaway.endswith(".") else takeaway + ".")
        if bridge:
            chunks.append(bridge if bridge.endswith(".") else bridge + ".")
        return _cap_words(" ".join(c for c in chunks if c), 110)

    if layout == "metric_dashboard" or layout == "data_table":
        stats = content.get("key_stats") or []
        nums = []
        for st in stats[:4]:
            if isinstance(st, dict):
                lab = strip_eids(st.get("label") or "")
                val = strip_eids(st.get("value") or "")
                if lab and val and lab.lower() not in ("metric", "value"):
                    nums.append(f"{val} on {lab}")
        open_ = headline or takeaway or "The markers are on the board."
        chunks.append(open_ if open_.endswith(".") else open_ + ".")
        if nums:
            chunks.append("The markers are " + "; ".join(nums) + ".")
        if so_what:
            chunks.append(so_what if so_what.endswith(".") else so_what + ".")
        elif takeaway and takeaway != open_:
            chunks.append(takeaway if takeaway.endswith(".") else takeaway + ".")
        if bridge:
            chunks.append(bridge if bridge.endswith(".") else bridge + ".")
        return _cap_words(" ".join(chunks), 110)

    # Default argument / sequence
    open_ = takeaway or headline or purpose or strip_eids(slide.get("title") or "")
    if open_:
        chunks.append(open_ if open_.endswith(".") else open_ + ".")
    bullets = content.get("bullets") or []
    if bullets:
        b0 = strip_eids(bullets[0])
        if b0 and b0.lower() not in (open_ or "").lower():
            chunks.append(b0 if b0.endswith(".") else b0 + ".")
    if so_what and so_what not in " ".join(chunks):
        chunks.append(so_what if so_what.endswith(".") else so_what + ".")
    if bridge:
        chunks.append(bridge if bridge.endswith(".") else bridge + ".")
    if len(chunks) < 2 and purpose:
        chunks.append(purpose if purpose.endswith(".") else purpose + ".")
    return _cap_words(" ".join(chunks), 110)


def _cap_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).rstrip(",;:") + "."
