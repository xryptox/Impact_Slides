"""Shared slide field accessors — one walk for visual_spec / content leaves.

``primary_visual`` is the guarded ``visual_spec → primary_visual`` walk shared
by steps, visual type, and any future leaf. Callers import this module; it
must not import ``layout/`` (sits below it, same level as ``layouts.py``).
"""
from __future__ import annotations

from typing import Any, Mapping


def primary_visual(slide: Mapping[str, Any]) -> dict[str, Any]:
    """Guarded ``visual_spec.primary_visual``; ``{}`` on any miss."""
    vs = slide.get("visual_spec") or {}
    if not isinstance(vs, dict):
        return {}
    pv = vs.get("primary_visual") or {}
    return pv if isinstance(pv, dict) else {}


def steps(slide: Mapping[str, Any]) -> list[Any]:
    """``primary_visual.steps_or_data`` as a list, else ``[]``."""
    steps_raw = primary_visual(slide).get("steps_or_data")
    return list(steps_raw) if isinstance(steps_raw, list) else []


def visual_type(slide: Mapping[str, Any]) -> str:
    """``primary_visual.type``, lowered/stripped; ``""`` on miss."""
    return str(primary_visual(slide).get("type") or "").lower().strip()


def content(slide: Mapping[str, Any]) -> dict[str, Any]:
    """``slide["content"]`` if a dict, else ``{}``."""
    c = slide.get("content") or {}
    return c if isinstance(c, dict) else {}
