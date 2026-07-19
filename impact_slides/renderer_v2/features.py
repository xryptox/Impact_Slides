"""Feature detection and resolution for renderer_v2 (P1).

Pure handoff inspection → known feature ids. No I/O, no paint.

Spec: wiki/SPEC_renderer_v2_p1_feature_size_gating.md
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from .charts import is_chart_layout
from .lib_inliner import KNOWN_FEATURES
from .layout.dispatch import resolve_layout

# Advisory soft-warn threshold for full presentation.html size (UTF-8 bytes).
ADVISORY_HTML_BYTES = 2_000_000


def _visual_types(slide: Mapping[str, Any]) -> list[str]:
    """Collect layout-like type strings from a slide (top-level + nested)."""
    found: list[str] = []
    lt = str(slide.get("layout_type") or "").lower().strip()
    if lt:
        found.append(lt)
    try:
        resolved = resolve_layout(slide)
        if resolved:
            found.append(str(resolved).lower().strip())
    except Exception:
        pass

    vs = slide.get("visual_spec") or {}
    if isinstance(vs, dict):
        for key in ("primary_visual", "secondary_visual"):
            vis = vs.get(key)
            if isinstance(vis, dict):
                t = str(vis.get("type") or "").lower().strip()
                if t:
                    found.append(t)
                # multi_panel tiles may embed charts (chart_type per tile)
                tiles = vis.get("tiles")
                if isinstance(tiles, list):
                    for tile in tiles:
                        if not isinstance(tile, dict):
                            continue
                        ct = str(tile.get("chart_type") or tile.get("type") or "").lower().strip()
                        if ct:
                            found.append(ct)
        # Freeform / grid areas may carry chart types
        grid = vs.get("grid")
        if isinstance(grid, dict):
            areas = grid.get("areas") or grid.get("items") or []
            if isinstance(areas, list):
                for area in areas:
                    if not isinstance(area, dict):
                        continue
                    t = str(area.get("type") or area.get("layout_type") or "").lower().strip()
                    if t:
                        found.append(t)
                    inner = area.get("visual") or area.get("primary_visual") or {}
                    if isinstance(inner, dict):
                        t2 = str(inner.get("type") or "").lower().strip()
                        if t2:
                            found.append(t2)
    return found


def _slide_needs_charts(slide: Mapping[str, Any]) -> bool:
    types = _visual_types(slide)
    if any(is_chart_layout(t) for t in types):
        return True
    # dual_chart always hosts chart panes
    if any(t == "dual_chart" for t in types):
        return True
    return False


def detect_features(handoff: Mapping[str, Any]) -> frozenset[str]:
    """Return known feature ids required by a normalized handoff.

    MVP1: only ``charts`` is auto-enabled (via chart layouts).
    ``mermaid`` / ``alpine`` / ``swiper`` / ``icons`` remain off until those
    themes define markers (stubs).
    """
    enabled: set[str] = set()
    slides = handoff.get("slides") or []
    if not isinstance(slides, list):
        return frozenset()
    for slide in slides:
        if not isinstance(slide, Mapping):
            continue
        if _slide_needs_charts(slide):
            enabled.add("charts")
            break
    # Only known ids ever leave this function
    return frozenset(fid for fid in enabled if fid in KNOWN_FEATURES)


def resolve_features(
    handoff: Mapping[str, Any],
    *,
    force: Iterable[str] = (),
    suppress: Iterable[str] = (),
) -> frozenset[str]:
    """Detect features then apply force/suppress.

    Precedence: **suppress beats force beats detect**.
    Unknown ids in force or suppress raise ``ValueError`` (fail closed).
    """
    force_set = {str(x).strip() for x in force if str(x).strip()}
    suppress_set = {str(x).strip() for x in suppress if str(x).strip()}

    unknown = sorted((force_set | suppress_set) - KNOWN_FEATURES)
    if unknown:
        raise ValueError(
            "unknown feature id(s): "
            + ", ".join(unknown)
            + f" (known: {', '.join(sorted(KNOWN_FEATURES))})"
        )

    detected = set(detect_features(handoff))
    enabled = (detected | force_set) - suppress_set
    return frozenset(enabled)
