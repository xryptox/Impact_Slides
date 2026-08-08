"""Shared helpers for layout recipes (content accessors, kickers, tables)."""
from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from ...slide_view import content as _sv_content
from ...slide_view import steps as _sv_steps
from ...strip import (
    banned_face_opener,
    chosen_dek,
    clean_quote_body,
    esc,
    parse_cite_from_quote,
    strip_eids,
)
from ..regions import gl_card, insight_strip, notes_aside, slide_shell, source_strip


_DATE_LEAD = re.compile(
    r"^(?P<k>(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}"
    r"|H[12]\s+\d{4}|Q[1-4]\s+\d{4}|By\s+end\s+\d{4}|End\s+\d{4}|\d{4})"
    r"\s*[:\-–—]\s*(?P<rest>.+)$",
    re.I,
)

_END_YEAR = re.compile(
    r"^(?P<rest>.+?)\s+(?:before\s+)?end(?:\s+of)?\s+(?P<y>\d{4})\s*$",
    re.I,
)

_LABEL_COLON = re.compile(r"^(?P<k>[^:]{1,48})\s*:\s*(?P<rest>.+)$")

_CLOSED_LOOP = re.compile(
    r"closed[- ]loop|payments\s*\+\s*loyalty|circuit complete|completes the",
    re.I,
)

_REGIONISH = {
    "us", "usa", "uk", "eu", "europe", "global", "apac", "latam", "emea", "na", "emea/apac",
}



def _content(slide: Mapping[str, Any]) -> dict[str, Any]:
    return _sv_content(slide)



def _vs_steps(slide: Mapping[str, Any]) -> list[Any]:
    return _sv_steps(slide)



def _so_what(slide: Mapping[str, Any]) -> str:
    c = _content(slide)
    raw = strip_eids(c.get("so_what") or "")
    if not raw or banned_face_opener(raw):
        return ""
    return raw



def _source_names(slide: Mapping[str, Any]) -> list[str]:
    names: list[str] = []
    for item in slide.get("evidence_sources") or []:
        if isinstance(item, dict):
            n = item.get("source_file") or item.get("file") or ""
            if n:
                names.append(str(n))
        elif isinstance(item, str) and not re.fullmatch(r"E\d{4}", item, re.I):
            if "." in item:
                names.append(item)
    return names



# ---------- kickers ----------

def argument_kicker(slide: Mapping[str, Any]) -> str:
    blob = " ".join(
        str(x or "")
        for x in (
            slide.get("title"),
            _content(slide).get("headline"),
            slide.get("section"),
            slide.get("purpose"),
        )
    ).lower()
    rules = (
        (("integrat", "continuity"), "Why continuity"),
        (("advisor", "leadership", "operator", "ceo"), "Who to keep"),
        (("risk",), "Open risks"),
        (("analyst", "street", "research"), "What street says"),
        (("venue", "network", "map", "platform", "scale"), "The map"),
        (("dining", "experience", "growth", "engagement"), "The case"),
        (("deal", "cash", "$"), "The deal"),
    )
    for keys, label in rules:
        if any(k in blob for k in keys):
            return label
    sec = (slide.get("section") or "").lower()
    if sec == "how":
        return "How it works"
    if sec == "why":
        return "Why it matters"
    if sec == "now":
        return "What next"
    return "The case"



def panel_kicker(slide: Mapping[str, Any]) -> str:
    blob = " ".join(
        str(x or "")
        for x in (
            slide.get("title"),
            _content(slide).get("headline"),
            slide.get("section"),
        )
    ).lower()
    rules = (
        (("integrat", "continuity"), "What continuity buys"),
        (("leadership", "operator", "advisor"), "Who stays"),
        (("risk",), "What stays open"),
        (("street", "analyst"), "Street check"),
        (("map", "platform", "venue", "scale"), "How the maps join"),
        (("dining", "engagement", "engine"), "Where dining fits"),
        (("deal", "cash"), "What the check buys"),
    )
    for keys, label in rules:
        if any(k in blob for k in keys):
            return label
    sec = (slide.get("section") or "").lower()
    if sec == "how":
        return "How this lands"
    if sec == "why":
        return "What makes the case"
    if sec == "now":
        return "What to watch"
    return "In the evidence"



# ---------- timeline parse ----------

def split_step_copy(raw: Any) -> tuple[str, str]:
    s = strip_eids(raw)
    if not s:
        return "", ""
    m = _DATE_LEAD.match(s)
    if m:
        return m.group("k").strip(), m.group("rest").strip()
    m = _LABEL_COLON.match(s)
    if m and not m.group("k").lower() in ("http", "https"):
        return m.group("k").strip(), m.group("rest").strip()
    m = _END_YEAR.match(s)
    if m:
        return f"End {m.group('y')}", m.group("rest").strip()
    return "", s



def apply_timeline_year_overrides(title: str, steps: list[str]) -> list[str]:
    if "path to close" not in (title or "").lower():
        return steps
    # If no step has a year, inject framed windows
    if any(re.search(r"\d{4}", s) for s in steps):
        return steps
    defaults = ["H2 2026", "H2 2026", "H2 2026", "End 2026"]
    out = []
    for i, s in enumerate(steps):
        if ":" in s or re.search(r"\d{4}", s):
            out.append(s)
        else:
            prefix = defaults[i] if i < len(defaults) else "H2 2026"
            out.append(f"{prefix}: {s}")
    return out



# ---------- comparison pairing ----------

def pair_comparison(slide: Mapping[str, Any]) -> list[tuple[str, str]]:
    steps = _vs_steps(slide)
    bullets = [strip_eids(b) for b in (_content(slide).get("bullets") or []) if strip_eids(b)]
    pairs: list[tuple[str, str]] = []

    strings = []
    for st in steps:
        if isinstance(st, str):
            strings.append(strip_eids(st))
        elif isinstance(st, dict):
            h = strip_eids(st.get("title") or st.get("head") or st.get("label") or "")
            b = strip_eids(st.get("body") or st.get("text") or st.get("value") or "")
            if h or b:
                pairs.append((h or b, b if h else ""))
        elif isinstance(st, (list, tuple)) and st:
            pairs.append((strip_eids(st[0]), strip_eids(st[1]) if len(st) > 1 else ""))

    if pairs:
        return [(h, b) for h, b in pairs if h or b][:6]

    if strings:
        title_only = all(":" not in s for s in strings)
        if title_only and bullets:
            for i, s in enumerate(strings):
                body = bullets[i] if i < len(bullets) else ""
                pairs.append((s, body))
            return pairs[:6]
        for s in strings:
            if ":" in s:
                head, _, body = s.partition(":")
                pairs.append((head.strip(), body.strip()))
            else:
                pairs.append((s, ""))
        return pairs[:6]

    for b in bullets[:6]:
        if ":" in b:
            head, _, body = b.partition(":")
            pairs.append((head.strip(), body.strip()))
        else:
            pairs.append((b, ""))
    return pairs[:6]



# ---------- split right panel ----------

def _is_matrix(steps: list[Any]) -> bool:
    if len(steps) < 2:
        return False
    rows = [s for s in steps if isinstance(s, (list, tuple)) and len(s) >= 2]
    return len(rows) >= 2



def right_panel_model(slide: Mapping[str, Any]) -> dict[str, Any]:
    """Return {kind: fact|proof|icon, items: [...], hat: str}."""
    steps = _vs_steps(slide)
    c = _content(slide)
    bullets = [strip_eids(b) for b in (c.get("bullets") or []) if strip_eids(b)]
    supporting = [strip_eids(b) for b in (c.get("supporting_points") or []) if strip_eids(b)]
    hat = panel_kicker(slide)

    if _is_matrix(steps):
        header = None
        rows = []
        for i, row in enumerate(steps):
            if not isinstance(row, (list, tuple)) or len(row) < 2:
                continue
            cells = [strip_eids(x) for x in row[:2]]
            if i == 0 and any(x.lower() in ("platform", "region", "metric", "name") for x in cells):
                header = [x.lower() for x in cells]
                continue
            rows.append(cells)
        platform_first = True
        if header:
            platform_first = header[0] in ("platform", "name", "metric", "entity")
        items = []
        for a, b in rows[:4]:
            if platform_first:
                val, lab = a, b
            else:
                val, lab = b, a
            # regionish guard: never hero two identical regions with entity missing
            if a.lower() in _REGIONISH and b.lower() not in _REGIONISH:
                val, lab = b, a
            elif b.lower() in _REGIONISH and a.lower() not in _REGIONISH:
                val, lab = a, b
            items.append({"value": val, "label": lab})
        if len(items) >= 2:
            return {"kind": "fact", "items": items, "hat": hat}

    # proof lines
    proof: list[str] = []
    for src in (supporting, [s for s in steps if isinstance(s, str)]):
        for line in src:
            line = strip_eids(line)
            if not line:
                continue
            if any(near(line, b) for b in bullets):
                continue
            if line not in proof:
                proof.append(line)
        if len(proof) >= 2:
            break
    proof = proof[:4]
    if len(proof) >= 2:
        return {"kind": "proof", "items": proof, "hat": hat}
    return {"kind": "icon", "items": [], "hat": hat}



def near(a: str, b: str) -> bool:
    aa, bb = a.lower().strip(), b.lower().strip()
    return aa == bb or aa in bb or bb in aa



# ---------- shared builders ----------

def _bullets_html(bullets: Sequence[str], cap: int = 6) -> str:
    items = [strip_eids(b) for b in bullets if strip_eids(b)][:cap]
    if not items:
        return ""
    lis = "".join(f"<li><span>{esc(b)}</span></li>" for b in items)
    return f'<ul class="bullet-list">{lis}</ul>'



def _proof_html(items: Sequence[str]) -> str:
    lis = "".join(
        f'<li><svg class="icon icon-sm ic" viewBox="0 0 24 24" aria-hidden="true">'
        f'<use href="#ic-check"/></svg><span>{esc(x)}</span></li>'
        for x in items
    )
    return f'<ul class="proof-list">{lis}</ul>'



def _fact_html(items: Sequence[Mapping[str, str]]) -> str:
    tiles = "".join(
        f'<div class="fact-tile"><div class="fact-value">{esc(it["value"])}</div>'
        f'<div class="fact-label">{esc(it["label"])}</div></div>'
        for it in items
    )
    return f'<div class="fact-grid">{tiles}</div>'



def _kpi_cards(stats: Sequence[Any], *, cols_class: str) -> str:
    cards = []
    for st in stats[:6]:
        if isinstance(st, dict):
            lab = strip_eids(st.get("label") or "")
            val = strip_eids(st.get("value") or "")
            src = strip_eids(st.get("source") or "")
        elif isinstance(st, (list, tuple)) and len(st) >= 2:
            lab, val, src = strip_eids(st[0]), strip_eids(st[1]), ""
        else:
            continue
        if not lab and not val:
            continue
        src_html = f'<div class="kpi-source">{esc(src)}</div>' if src else ""
        cards.append(
            f'<div class="kpi-card card">'
            f'<div class="kpi-label">{esc(lab)}</div>'
            f'<div class="kpi-value">{esc(val)}</div>'
            f"{src_html}</div>"
        )
    if not cards:
        return '<div class="chart-empty">No metrics</div>'
    return f'<div class="gl-grid {cols_class}">{"".join(cards)}</div>'



def _stat_label_value(st: Any) -> tuple[str, str] | None:
    """Normalize a key_stats / stat-like entry to (label, value).

    Accepts a dict (label/value keys) or a 2-tuple/list; returns None for
    unusable entries. Single owner for the normalization that many
    stat-consuming recipes need (prevents shotgun surgery if the shape changes).
    """
    if isinstance(st, dict):
        lab = strip_eids(st.get("label") or "")
        val = strip_eids(st.get("value") or "")
    elif isinstance(st, (list, tuple)) and len(st) >= 2:
        lab, val = strip_eids(st[0]), strip_eids(st[1])
    else:
        return None
    if not lab and not val:
        return None
    return lab, val



def _table_inset(stats: Sequence[Any]) -> str:
    """key_stats inset cards for table slides (#73/F9, gutter via T12).

    Renders each supplied stat as a navy callout card. The host recipe wraps
    these in `.gl-areas-table-inset` so the inset reserves a right gutter and
    the table shrinks beside it (T12) — not absolute-over-content. Returns
    empty string when no usable stats are supplied.
    """
    cards = []
    for st in stats[:2]:
        nv = _stat_label_value(st)
        if not nv:
            continue
        lab, val = nv
        cards.append(
            f'<div class="gl-inset card" data-inset="1">'
            f'<div class="gl-inset-label">{esc(lab)}</div>'
            f'<div class="gl-inset-value">{esc(val)}</div>'
            f"</div>"
        )
    if not cards:
        return ""
    return f'<div class="gl-inset-wrap">{"".join(cards)}</div>'



def _circle_pair_svg(
    value_before: float,
    value_after: float,
    max_value: float,
    unit: str = "%",
    label: str = "",
) -> str:
    """Render paired proportional circles (before/after) as SVG.

    Outer circle = before (outlined), inner circle = after (filled).
    Radii proportional to values relative to max_value.
    """
    import math

    W, H = 140, 140
    cx, cy = W / 2, H / 2
    max_r = 55
    r_before = max(8, math.sqrt(value_before / max(max_value, 1)) * max_r)
    r_after = max(6, math.sqrt(value_after / max(max_value, 1)) * max_r)

    parts = [
        f'<svg class="circle-pair" viewBox="0 0 {W} {H}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;max-width:{W}px;height:auto">',
        # Outer circle (before) — outlined
        f'<circle cx="{cx}" cy="{cy}" r="{r_before:.1f}" '
        f'fill="none" stroke="var(--panel-border, #d8dce3)" stroke-width="2"/>',
        # Inner circle (after) — filled
        f'<circle cx="{cx}" cy="{cy}" r="{r_after:.1f}" '
        f'fill="var(--blue, #006fcf)" opacity="0.85"/>',
        # After value label
        f'<text x="{cx}" y="{cy + 5:.0f}" text-anchor="middle" '
        f'fill="#fff" font-size="16" font-weight="700" '
        f'font-family="var(--font-body, sans-serif)">'
        f"{value_after:g}{esc(unit)}</text>",
    ]
    # Before value label (above the outer circle)
    parts.append(
        f'<text x="{cx}" y="{cy - r_before - 8:.0f}" text-anchor="middle" '
        f'fill="var(--ink-muted, #63666a)" font-size="12" '
        f'font-family="var(--font-body, sans-serif)">'
        f"{value_before:g}{esc(unit)}</text>"
    )
    if label:
        parts.append(
            f'<text x="{cx}" y="{H - 4}" text-anchor="middle" '
            f'fill="var(--ink, #53565a)" font-size="13" font-weight="600" '
            f'font-family="var(--font-body, sans-serif)">{esc(label)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)



def _table_matrix(slide: Mapping[str, Any]) -> list[list[str]]:
    steps = _vs_steps(slide)
    rows: list[list[str]] = []
    for st in steps:
        if isinstance(st, (list, tuple)):
            rows.append([strip_eids(x) for x in st])
        elif isinstance(st, str) and "|" in st:
            rows.append([strip_eids(x) for x in st.split("|")])
        elif isinstance(st, str) and ":" in st:
            a, _, b = st.partition(":")
            rows.append([a.strip(), b.strip()])
    return rows



def table_as_kpi(rows: list[list[str]]) -> bool:
    if len(rows) < 2:
        return False
    # count body rows
    body = rows[1:] if rows and rows[0] and rows[0][0].lower() in ("metric", "name", "label", "item") else rows
    if not body:
        return False
    width = max(len(r) for r in body)
    return width <= 2 and 1 <= len(body) <= 6



def _hero_stack(stats: Sequence[Any]) -> str:
    """Right-hand giant % callout stack for chart_hero_dual (#75/F5)."""
    cards = []
    for st in stats[:4]:
        nv = _stat_label_value(st)
        if not nv:
            continue
        lab, val = nv
        # R4 finish: IR giant-% pairing — digits huge, the % unit visibly
        # smaller, narrated label beside (not below) the number.
        if val.endswith("%") and len(val) > 1:
            value_html = (
                f'<span class="gl-hero-value-num">{esc(val[:-1])}</span>'
                f'<span class="gl-hero-value-unit">%</span>'
            )
        else:
            value_html = esc(val)
        cards.append(
            f'<div class="gl-hero card">'
            f'<div class="gl-hero-value">{value_html}</div>'
            f'<div class="gl-hero-label">{esc(lab)}</div>'
            f"</div>"
        )
    if not cards:
        return ""
    return f'<div class="gl-hero-stack">{"".join(cards)}</div>'


_DRIVER_DIRS = frozenset({"up", "down", "flat"})
_DRIVER_TONES = frozenset({"positive", "negative", "neutral", "accent"})
# Right pane ~1/3 of 1920 content; two-line clamp budget for labels/details.
_DRIVER_TEXT_MAX_W = 280.0
_DRIVER_HEADING_MAX_W = 360.0
_DRIVER_FS = 16.0
_DRIVER_HEADING_FS = 20.0


def _driver_fit_text(
    text: str,
    *,
    font_size: float,
    max_width: float,
    field: str,
) -> str:
    """Keep one line when it fits; else wrap to 2 lines and ellipsize. Strict raises."""
    from ...charts.auto_typography import ellipsize, measure_text_width, wrap_label
    from ...charts.typography import _RENDER_STRICT, _warn

    raw = (text or "").strip()
    if not raw:
        return ""
    if measure_text_width(raw, font_size, font="source_sans_3", weight="semibold") <= max_width:
        return raw
    lines = wrap_label(raw, max_lines=2)
    fitted: list[str] = []
    overflow = False
    for line in lines:
        if measure_text_width(line, font_size, font="source_sans_3", weight="semibold") <= max_width:
            fitted.append(line)
            continue
        overflow = True
        fitted.append(ellipsize(line, font_size, max_width, font="source_sans_3"))
    rejoined = " ".join(x.replace("…", "") for x in fitted).strip()
    compact_src = " ".join(raw.split())
    compact_out = " ".join(rejoined.split())
    if compact_out != compact_src and not any("…" in x for x in fitted):
        overflow = True
        if fitted:
            fitted[-1] = ellipsize(fitted[-1], font_size, max_width, font="source_sans_3")
    if overflow:
        msg = f"driver_card {field} overflow"
        if _RENDER_STRICT.get():
            raise ValueError(msg)
        _warn(msg)
    return chr(10).join(fitted)


def normalize_driver_card(visual: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Validate/normalize secondary_visual driver_card; None → fall back."""
    from ...charts.typography import _RENDER_STRICT, _warn

    if not isinstance(visual, Mapping) or visual.get("type") != "driver_card":
        return None
    heading = strip_eids(str(visual.get("heading") or "")).strip()
    if not heading:
        msg = "driver_card missing heading"
        if _RENDER_STRICT.get():
            raise ValueError(msg)
        _warn(msg)
        return None
    raw_rows = visual.get("rows")
    if not isinstance(raw_rows, list):
        msg = "driver_card rows must be a list"
        if _RENDER_STRICT.get():
            raise ValueError(msg)
        _warn(msg)
        return None
    if len(raw_rows) > 6:
        msg = "driver_card supports at most 6 rows"
        if _RENDER_STRICT.get():
            raise ValueError(msg)
        _warn(msg)
        raw_rows = raw_rows[:6]
    rows: list[dict[str, Any]] = []
    for i, raw in enumerate(raw_rows):
        if not isinstance(raw, Mapping):
            msg = f"driver_card row {i} malformed"
            if _RENDER_STRICT.get():
                raise ValueError(msg)
            _warn(msg)
            continue
        label = strip_eids(str(raw.get("label") or "")).strip()
        value = strip_eids(str(raw.get("value") or "")).strip()
        if not label or not value:
            msg = f"driver_card row {i} missing label/value"
            if _RENDER_STRICT.get():
                raise ValueError(msg)
            _warn(msg)
            continue
        detail_raw = raw.get("detail")
        detail = (
            strip_eids(str(detail_raw)).strip()
            if detail_raw is not None and str(detail_raw).strip()
            else ""
        )
        direction = raw.get("direction")
        if direction is not None and direction != "":
            direction = str(direction).strip().lower()
            if direction not in _DRIVER_DIRS:
                msg = f"driver_card row {i} bad direction"
                if _RENDER_STRICT.get():
                    raise ValueError(msg)
                _warn(msg)
                continue
        else:
            direction = None
        tone = raw.get("tone")
        if tone is not None and tone != "":
            tone = str(tone).strip().lower()
            if tone not in _DRIVER_TONES:
                msg = f"driver_card row {i} bad tone"
                if _RENDER_STRICT.get():
                    raise ValueError(msg)
                _warn(msg)
                continue
        else:
            tone = None
        rows.append(
            {
                "label": label,
                "value": value,
                "detail": detail,
                "direction": direction,
                "tone": tone,
            }
        )
    if not rows:
        msg = "driver_card has no valid rows"
        if _RENDER_STRICT.get():
            raise ValueError(msg)
        _warn(msg)
        return None
    subtitle = strip_eids(str(visual.get("subtitle") or "")).strip()
    return {
        "type": "driver_card",
        "heading": heading,
        "subtitle": subtitle,
        "rows": rows,
    }


def _driver_card_html(visual: Mapping[str, Any] | None) -> str:
    """Render a normalized driver_card as right-pane HTML (#151)."""
    from ...charts.typography import chart_pane_headings_html

    card = normalize_driver_card(visual)
    if not card:
        return ""
    # Fit heading/subtitle to 2-line budget before #147 chrome (same wrap contract as rows).
    heading = _driver_fit_text(
        card["heading"],
        font_size=_DRIVER_HEADING_FS,
        max_width=_DRIVER_HEADING_MAX_W,
        field="heading",
    )
    subtitle = card.get("subtitle") or ""
    if subtitle:
        subtitle = _driver_fit_text(
            subtitle,
            font_size=14.0,
            max_width=_DRIVER_HEADING_MAX_W,
            field="subtitle",
        )
    # Reuse #147 pane chrome; preserve wrapped lines as <br>.
    chrome = chart_pane_headings_html(heading, subtitle).replace("\n", "<br>")
    row_html: list[str] = []
    for row in card["rows"]:
        label = _driver_fit_text(
            row["label"], font_size=_DRIVER_FS, max_width=_DRIVER_TEXT_MAX_W, field="label"
        )
        detail = row.get("detail") or ""
        detail_html = ""
        if detail:
            d = _driver_fit_text(
                detail, font_size=13.0, max_width=_DRIVER_TEXT_MAX_W, field="detail"
            )
            detail_html = (
                f'<div class="gl-driver-detail">{esc(d).replace(chr(10), "<br>")}</div>'
            )
        direction = row.get("direction")
        tone = row.get("tone") or "neutral"
        dir_cls = f" gl-driver-dir--{direction}" if direction else ""
        tone_cls = f" gl-driver-tone--{tone}"
        dir_html = ""
        aria_dir = ""
        if direction:
            dir_html = (
                f'<span class="gl-driver-dir{dir_cls}" data-direction="{esc(direction)}" '
                f'aria-hidden="true"></span>'
            )
            aria_dir = f", {direction}"
        aria = (
            f'{row["label"]}'
            + (f': {detail}' if detail else "")
            + f' {row["value"]}{aria_dir}'
        )
        # value then direction (right metric column reading order)
        row_html.append(
            f'<div class="gl-driver-row{tone_cls}" role="listitem" aria-label="{esc(aria)}">'
            f'<div class="gl-driver-copy">'
            f'<div class="gl-driver-label">{esc(label).replace(chr(10), "<br>")}</div>'
            f"{detail_html}"
            f"</div>"
            f'<div class="gl-driver-metric">'
            f'<span class="gl-driver-value">{esc(row["value"])}</span>'
            f"{dir_html}"
            f"</div>"
            f"</div>"
        )
    return (
        f'<div class="gl-driver-card" role="group" '
        f'aria-label="{esc(card["heading"])}">'
        f"{chrome}"
        f'<div class="gl-driver-rows" role="list">{"".join(row_html)}</div>'
        f"</div>"
    )



def _sequential_grid(
    items: list[str],
    *,
    vertical: bool = False,
    connector_style: str = "line",
) -> str:
    """Render a sequential grid of numbered step cards.

    Uses .grid primitives and .card for each step item.
    connector_style is 'line', 'arrow', or 'milestone' — currently only
    affects class naming, SVG connectors are handled by the caller.
    """
    cards = []
    for i, raw in enumerate(items[:6], 1):
        kicker, title = split_step_copy(raw)
        kicker_html = f'<div class="step-kicker">{esc(kicker)}</div>' if kicker else ""
        cards.append(
            f'<article class="step-card card{" step-card--vertical" if vertical else ""}">'
            f'<div class="step-number">{i:02d}</div>'
            f'<div class="step-body">{kicker_html}<div class="step-text">{esc(title)}</div></div>'
            f"</article>"
        )
    if vertical:
        return f'<div class="process-flow--vertical gl-areas-process-v">{"".join(cards)}</div>'
    return (
        f'<div class="process-flow--horizontal gl-areas-process-h" '
        f'style="--step-count:{max(len(cards),1)}">{"".join(cards)}</div>'
    )



def _is_series_num(v: Any) -> bool:
    try:
        float(str(v).replace("%", "").replace(",", "").replace("$", "").strip())
        return True
    except (ValueError, TypeError):
        return False



def _visual_series_names(visual: Mapping[str, Any]) -> list[str]:
    """Series names a chart will plot, from keys the Builder already emits:
    chart_config.series_names, or the header/body shape of steps_or_data.
    Mirrors charts._bar_matrix series detection so legend-suppression
    decisions match the series Chart.js actually draws. Unnamed series
    are empty strings — count is what matters.
    """
    cfg = visual.get("chart_config") or {}
    names = [
        strip_eids(str(n)) for n in cfg.get("series_names") or [] if str(n).strip()
    ]
    if names:
        return names
    steps = visual.get("steps_or_data") or []
    if not steps:
        return names
    if all(isinstance(x, (list, tuple)) for x in steps):
        rows_raw = [list(x) for x in steps]
        first = rows_raw[0]
        second = rows_raw[1] if len(rows_raw) > 1 else []
        has_header = (
            len(rows_raw) > 1
            and all(isinstance(c, str) for c in first[1:])
            and any(_is_series_num(c) for c in second[1:])
        )
        if has_header:
            return [strip_eids(str(c)) for c in first[1:] if str(c).strip()]
        width = max((len(r) - 1 for r in rows_raw), default=0)
        return [""] * max(width, 0)
    for row in steps:
        if isinstance(row, Mapping):
            vals = row.get("values")
            if isinstance(vals, Mapping) and vals:
                return [strip_eids(str(k)) for k in vals]
            if _is_series_num(row.get("value")):
                # Line multi-series: primary `value` plus series_2..N
                # (same keys _line_data / _chartjs_line_config plot).
                n = 1
                while f"series_{n + 1}" in row:
                    n += 1
                return [""] * n
            skip = {"label", "category", "name", "kind", "icon", "color"}
            flat = [
                strip_eids(str(k))
                for k, v in row.items()
                if k not in skip and _is_series_num(v)
            ]
            if flat:
                return flat
            n = 1
            while f"series_{n + 1}" in row:
                n += 1
            return [""] * n
    return names
