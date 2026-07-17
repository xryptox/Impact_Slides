"""Optional freeform ``visual_spec.grid`` named-area renderer (Phase 7).

Schema (Builder/Renderer optional extension)::

    "visual_spec": {
      "grid": {
        "template_areas": ["lead lead", "main aside"],
        "columns": "1.2fr 0.8fr",
        "rows": "auto 1fr",          # optional
        "gap": "22px",               # optional
        "slots": {
          "lead":  {"kind": "text", "field": "body_text"},
          "main":  {"kind": "bullets"},
          "aside": {"kind": "metric_stack"}
        }
      }
    }

Supported slot kinds:
  bullets | metric_stack | key_stats | proof | text | so_what | steps | insight | html
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from ..strip import esc, strip_eids
from .regions import insight_strip

_SAFE_CSS = re.compile(r"^[a-zA-Z0-9%.\sfrpxEmEm,#\-_/]+$")
_SLOT_NAME = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_-]{0,40}$")


def has_freeform_grid(slide: Mapping[str, Any]) -> bool:
    vs = slide.get("visual_spec")
    if not isinstance(vs, dict):
        return False
    grid = vs.get("grid")
    if not isinstance(grid, dict):
        return False
    areas = grid.get("template_areas")
    slots = grid.get("slots")
    return isinstance(areas, list) and len(areas) >= 1 and isinstance(slots, dict) and bool(slots)


def _sanitize_css_value(raw: str, default: str) -> str:
    s = (raw or "").strip()
    if not s or not _SAFE_CSS.match(s):
        return default
    # block url()/expression
    low = s.lower()
    if "url(" in low or "expression" in low or "javascript" in low:
        return default
    return s


def _slot_names_from_areas(areas: list[str]) -> set[str]:
    names: set[str] = set()
    for row in areas:
        for tok in str(row).split():
            if tok == ".":
                continue
            if _SLOT_NAME.match(tok):
                names.add(tok)
    return names


def _bullets_html(items: list[str], cap: int = 8) -> str:
    clean = [strip_eids(x) for x in items if strip_eids(x)][:cap]
    if not clean:
        return '<p class="gl-empty">—</p>'
    lis = "".join(f"<li><span>{esc(b)}</span></li>" for b in clean)
    return f'<ul class="bullet-list">{lis}</ul>'


def _metrics_html(stats: list[Any], cap: int = 6) -> str:
    cards = []
    for st in stats[:cap]:
        if isinstance(st, dict):
            lab = strip_eids(st.get("label") or "")
            val = strip_eids(st.get("value") or "")
        elif isinstance(st, (list, tuple)) and len(st) >= 2:
            lab, val = strip_eids(st[0]), strip_eids(st[1])
        else:
            continue
        if not lab and not val:
            continue
        cards.append(
            f'<div class="kpi-card" style="min-height:0;padding:16px 18px">'
            f'<div class="kpi-label" style="font-size:18px">{esc(lab)}</div>'
            f'<div class="kpi-value" style="font-size:36px">{esc(val)}</div>'
            f"</div>"
        )
    if not cards:
        return '<p class="gl-empty">—</p>'
    cols = "gl-grid-2" if len(cards) > 1 else "gl-grid"
    return f'<div class="gl-grid {cols}">{"".join(cards)}</div>'


def _steps_html(steps: list[Any]) -> str:
    items = []
    for i, st in enumerate(steps[:6], 1):
        if isinstance(st, str):
            text = strip_eids(st)
        elif isinstance(st, dict):
            text = strip_eids(st.get("title") or st.get("text") or st.get("label") or "")
        elif isinstance(st, (list, tuple)):
            text = strip_eids(" — ".join(str(x) for x in st if x))
        else:
            continue
        if not text:
            continue
        items.append(
            f'<article class="step-card" style="grid-template-columns:48px 1fr">'
            f'<div class="step-number" style="width:40px;height:40px;font-size:14px">{i:02d}</div>'
            f'<div class="step-text" style="font-size:20px">{esc(text)}</div>'
            f"</article>"
        )
    if not items:
        return '<p class="gl-empty">—</p>'
    return f'<div class="process-flow--vertical">{"".join(items)}</div>'


def _resolve_slot(
    slide: Mapping[str, Any],
    slot_cfg: Mapping[str, Any],
) -> str:
    kind = str(slot_cfg.get("kind") or "text").lower().strip()
    c = slide.get("content") if isinstance(slide.get("content"), dict) else {}
    vs = slide.get("visual_spec") if isinstance(slide.get("visual_spec"), dict) else {}
    pv = vs.get("primary_visual") if isinstance(vs.get("primary_visual"), dict) else {}
    steps = pv.get("steps_or_data") if isinstance(pv.get("steps_or_data"), list) else []

    if kind in ("bullets",):
        return _bullets_html(list(c.get("bullets") or []))

    if kind in ("metric_stack", "key_stats", "metrics"):
        stats = list(c.get("key_stats") or [])
        if not stats and steps:
            # treat 2-col steps as metrics
            stats = []
            for st in steps:
                if isinstance(st, (list, tuple)) and len(st) >= 2:
                    stats.append({"label": st[0], "value": st[1]})
        return _metrics_html(stats)

    if kind in ("proof", "supporting"):
        items = list(c.get("supporting_points") or [])
        if not items:
            items = [s for s in steps if isinstance(s, str)]
        return _bullets_html([strip_eids(x) for x in items], cap=6)

    if kind in ("steps", "process"):
        return _steps_html(list(steps))

    if kind in ("so_what", "insight"):
        text = strip_eids(c.get("so_what") or "")
        return insight_strip(text) if text else '<p class="gl-empty">—</p>'

    if kind == "html":
        # never allow raw HTML from builder — treat as text
        kind = "text"

    if kind in ("text", "body", "lead"):
        field = str(slot_cfg.get("field") or "body_text")
        if field in c:
            raw = c.get(field)
        else:
            raw = c.get("body_text") or c.get("headline") or ""
        if isinstance(raw, list):
            return _bullets_html([str(x) for x in raw])
        text = strip_eids(raw)
        return f'<p class="lead-band gl-lead-text">{esc(text)}</p>' if text else '<p class="gl-empty">—</p>'

    # literal value on slot
    if slot_cfg.get("text"):
        return f'<p class="lead-band">{esc(strip_eids(slot_cfg.get("text")))}</p>'

    return '<p class="gl-empty">—</p>'


def render_freeform_main(slide: Mapping[str, Any]) -> str:
    """Return main-panel HTML for a slide that declares visual_spec.grid."""
    vs = slide.get("visual_spec") or {}
    grid = vs.get("grid") or {}
    areas = [str(r) for r in (grid.get("template_areas") or [])]
    slots_cfg = grid.get("slots") or {}
    columns = _sanitize_css_value(str(grid.get("columns") or "1fr 1fr"), "1fr 1fr")
    rows = _sanitize_css_value(str(grid.get("rows") or "auto"), "auto")
    gap = _sanitize_css_value(str(grid.get("gap") or "22px"), "22px")

    area_names = _slot_names_from_areas(areas)
    # CRITICAL: use single-quoted area tokens inside the HTML style="..." attribute.
    # Double quotes terminate the attribute early and collapse every slot into one pile.
    # CSS accepts both: grid-template-areas: 'lead lead' 'main aside'
    areas_css = " ".join("'" + row.replace("'", "") + "'" for row in areas)

    # Preserve declaration order (areas first) then any extras in slots_cfg
    ordered: list[str] = []
    for row in areas:
        for tok in str(row).split():
            if tok != "." and _SLOT_NAME.match(tok) and tok not in ordered:
                ordered.append(tok)
    for name in area_names:
        if name not in ordered:
            ordered.append(name)

    cells: list[str] = []
    for name in ordered:
        cfg = slots_cfg.get(name) or {}
        if not isinstance(cfg, dict):
            cfg = {"kind": "text", "text": str(cfg)}
        hat = strip_eids(cfg.get("hat") or cfg.get("title") or "")
        body = _resolve_slot(slide, cfg)
        if hat:
            inner = (
                f'<div class="gl-card">'
                f'<h3 class="gl-card-hat">{esc(hat)}</h3>'
                f'<div class="gl-card-body">{body}</div></div>'
            )
        else:
            inner = body
        cells.append(
            f'<div class="gl-slot gl-slot--{esc(name)}" '
            f'style="grid-area:{esc(name)};min-width:0;min-height:0">'
            f"{inner}</div>"
        )

    style = (
        f"--gl-ff-cols:{columns};"
        f"--gl-ff-rows:{rows};"
        f"--gl-ff-gap:{gap};"
        f"grid-template-columns:{columns};"
        f"grid-template-rows:{rows};"
        f"grid-template-areas:{areas_css};"
        f"gap:{gap};"
    )
    sow = ""
    c = slide.get("content") if isinstance(slide.get("content"), dict) else {}
    claimed = {
        str((slots_cfg.get(n) or {}).get("kind") or "").lower()
        for n in area_names
        if isinstance(slots_cfg.get(n), dict)
    }
    if "so_what" not in claimed and "insight" not in claimed:
        sow = insight_strip(strip_eids(c.get("so_what") or ""))

    # Do NOT also attach generic .gl-grid — its denser defaults fight freeform areas.
    return (
        f'<div class="gl-areas-freeform" style="{style}" data-freeform="1">'
        f'{"".join(cells)}</div>{sow}'
    )

