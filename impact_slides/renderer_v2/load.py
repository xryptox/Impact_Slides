"""Load builder handoff + seed; force slide-1 title; scrub face E####."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .strip import scrub_tree


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {p}")
    return data


def _slides_of(handoff: dict[str, Any]) -> list[dict[str, Any]]:
    slides = handoff.get("slides")
    if isinstance(slides, list) and slides:
        return slides
    # occasional alternate key
    plan = handoff.get("slide_update_plan")
    if isinstance(plan, list):
        return plan
    return []


def normalize_handoff(handoff: dict[str, Any]) -> dict[str, Any]:
    """Deep-copy handoff, scrub E####, force slide 1 to title_or_opening.

    If slide 1 was a semantic layout (e.g. quote_card), insert a cover from
    presentation meta and renumber so the semantic content remains visible.
    """
    data = deepcopy(handoff)
    data = scrub_tree(data)
    slides = list(_slides_of(data))
    if not slides:
        raise ValueError("builder handoff has no slides")

    # Sort / number
    for i, s in enumerate(slides, 1):
        s.setdefault("slide_number", i)

    first = slides[0]
    lt = (first.get("layout_type") or "").strip()
    if lt and lt != "title_or_opening":
        pres = data.get("presentation") or {}
        cover = {
            "slide_number": 1,
            "layout_type": "title_or_opening",
            "packing_mode": "cover-led",
            "title": pres.get("title") or first.get("title") or "Presentation",
            "section": first.get("section") or "Why",
            "purpose": pres.get("primary_goal") or first.get("purpose") or "",
            "audience_takeaway": first.get("audience_takeaway") or "",
            "content": {
                "headline": pres.get("primary_goal") or pres.get("subtitle") or "",
                "subtitle": pres.get("subtitle") or "",
                "bullets": [],
                "key_stats": [],
                "body_text": "",
                "so_what": "",
                "narrative_bridge": first.get("content", {}).get("narrative_bridge", "")
                if isinstance(first.get("content"), dict)
                else "",
            },
            "evidence_sources": first.get("evidence_sources") or [],
            "visual_spec": {"primary_visual": {"type": "other", "description": "", "steps_or_data": []}},
            "speaker_notes": first.get("speaker_notes") or "",
        }
        slides = [cover] + slides

    # Force layout on #1
    slides[0]["layout_type"] = "title_or_opening"
    slides[0].setdefault("packing_mode", "cover-led")

    # Renumber
    for i, s in enumerate(slides, 1):
        s["slide_number"] = i

    data["slides"] = slides
    return data


def present_meta(handoff: dict[str, Any]) -> dict[str, Any]:
    pres = handoff.get("presentation") or {}
    return {
        "title": pres.get("title") or "Impact Slides",
        "subtitle": pres.get("subtitle") or "",
        "audience": pres.get("audience") or "",
        "primary_goal": pres.get("primary_goal") or "",
        "readiness_score": pres.get("readiness_score"),
        "quality_flags": pres.get("quality_flags") or [],
        "style_preset": "BoardroomEarnings",
    }


def load_seed(path: str | Path | None) -> list[dict[str, Any]]:
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("evidence", "entries", "register", "items"):
            if isinstance(data.get(k), list):
                return data[k]
    return []
