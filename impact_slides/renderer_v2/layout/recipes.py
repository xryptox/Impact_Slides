"""Boardroom layout recipes composed from gl-* primitives."""
from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from ..strip import (
    banned_face_opener,
    chosen_dek,
    clean_quote_body,
    esc,
    parse_cite_from_quote,
    strip_eids,
)
from .regions import gl_card, insight_strip, notes_aside, slide_shell, source_strip

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
    c = slide.get("content") or {}
    return c if isinstance(c, dict) else {}


def _vs_steps(slide: Mapping[str, Any]) -> list[Any]:
    vs = slide.get("visual_spec") or {}
    if not isinstance(vs, dict):
        return []
    pv = vs.get("primary_visual") or {}
    if not isinstance(pv, dict):
        return []
    steps = pv.get("steps_or_data")
    return list(steps) if isinstance(steps, list) else []


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
    """Floating key_stats inset for table slides (#73/F9).

    Renders each supplied stat as a navy callout card floated beside the
    table, so VCE-style insets compose into the data_table stage instead of
    being dropped. Returns empty string when no usable stats are supplied.
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


# ================== RECIPES ==================

def render_title(slide, total, notes, active=False):
    pres_goal = strip_eids(_content(slide).get("headline") or "")
    dek = chosen_dek(slide) or pres_goal
    title = strip_eids(slide.get("title") or "Presentation")
    kicker = strip_eids(slide.get("section") or "")
    kicker_html = ""
    if kicker and kicker.lower() not in ("why", "what", "how", "now"):
        kicker_html = f'<div class="kicker">{esc(kicker)}</div>'
    dek_html = f'<p class="headline">{esc(dek)}</p>' if dek else ""
    main = (
        '<div class="gl-areas-cover cover-inner">'
        '<div class="gl-band-navy">'
        '<div class="title-stack">'
        f"{kicker_html}"
        f"<h1>{esc(title)}</h1>"
        f"{dek_html}"
        "</div></div>"
        '<div class="gl-band-blue"><div class="title-footer">'
        '<span class="cover-date">Boardroom Earnings</span></div></div>'
        "</div>"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=title,
        dek="",
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        layout_class="title_or_opening",
        active=active,
        cover=True,
    )


def render_split(slide, total, notes, active=False):
    c = _content(slide)
    bullets = [strip_eids(b) for b in (c.get("bullets") or []) if strip_eids(b)]
    lead = strip_eids(c.get("body_text") or "")
    packing = (slide.get("packing_mode") or "argument-led").lower()
    sow = _so_what(slide)
    if packing == "argument-led" and not sow and lead:
        # promote body to insight when so_what empty
        sow = lead
        lead = ""
    model = right_panel_model(slide)
    arg_hat = argument_kicker(slide)
    proof_hat = model["hat"] if packing.startswith("argument") else model["hat"]

    if model["kind"] == "fact":
        right_body = _fact_html(model["items"])
        right = gl_card(proof_hat, right_body, "fact-panel")
    elif model["kind"] == "proof":
        right = gl_card(proof_hat, _proof_html(model["items"]), "proof-panel")
    else:
        right = gl_card(
            proof_hat,
            '<svg class="icon icon-lg" viewBox="0 0 24 24" aria-hidden="true"><use href="#ic-layers"/></svg>',
            "icon-only",
        )

    left = gl_card(arg_hat, _bullets_html(bullets) or "<p>_(no argument spine)_</p>", "arg-panel")
    lead_html = f'<p class="lead-band gl-lead-text gl-lead">{esc(lead)}</p>' if lead else '<div class="gl-lead"></div>'
    main = (
        f'<div class="gl-areas-split">'
        f"{lead_html}"
        f'<div class="gl-arg">{left}</div>'
        f'<div class="gl-proof">{right}</div>'
        f"</div>"
        f"{insight_strip(sow)}"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="split_text_visual",
        active=active,
        item_count=max(len(bullets), len(model.get("items") or [])),
    )


def render_metric(slide, total, notes, active=False):
    c = _content(slide)
    stats = c.get("key_stats") or []
    # fallback: steps as label/value
    if not stats:
        rows = _table_matrix(slide)
        body = rows[1:] if rows and rows[0][0].lower() in ("metric", "label") else rows
        stats = [{"label": r[0], "value": r[1] if len(r) > 1 else ""} for r in body if r]
    n = min(len(stats), 6)
    if n == 4:
        cols = "gl-grid-dense-2x2"
        layout = "metric dense-2x2"
    elif n <= 3:
        cols = f"gl-grid-{max(n, 1)}" if n != 1 else "gl-grid"
        layout = "metric"
    else:
        cols = "gl-grid-3"
        layout = "metric"
    main = (
        f'<div class="gl-areas-metric layout-metric {layout}">'
        f'<div class="gl-stats">{_kpi_cards(stats, cols_class=cols)}</div>'
        f'<div class="gl-insight">{insight_strip(_so_what(slide))}</div>'
        f"</div>"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="metric_dashboard",
        active=active,
        item_count=n,
    )


def render_table(slide, total, notes, active=False):
    rows = _table_matrix(slide)
    if not rows:
        # try key_stats
        return render_metric(slide, total, notes, active=active)
    if table_as_kpi(rows):
        body = rows[1:] if rows[0] and rows[0][0].lower() in ("metric", "name", "label", "item") else rows
        stats = [{"label": r[0], "value": r[1] if len(r) > 1 else ""} for r in body]
        n = len(stats)
        cols = "gl-grid-dense-2x2" if n == 4 else ("gl-grid-3" if n >= 5 else f"gl-grid-{max(n,1)}")
        if n == 1:
            cols = "gl-grid"
        main = (
            f'<div class="gl-areas-metric layout-table-as-kpi">'
            f'<div class="gl-stats">{_kpi_cards(stats, cols_class=cols)}</div>'
            f'<div class="gl-insight">{insight_strip(_so_what(slide))}</div>'
            f"</div>"
        )
        return slide_shell(
            number=int(slide["slide_number"]),
            total=total,
            title=strip_eids(slide.get("title") or ""),
            dek=chosen_dek(slide),
            main_html=main,
            notes_html=notes_aside(int(slide["slide_number"]), notes),
            footer_html=source_strip(_source_names(slide)),
            layout_class="data_table",
            active=active,
            item_count=n,
        )
    # true table
    head = rows[0]
    body = rows[1:] if len(rows) > 1 else []
    th = "".join(f"<th>{esc(h)}</th>" for h in head)
    trs = []
    for r in body:
        tds = []
        for i, cell in enumerate(r):
            cls = ' class="num"' if i == len(r) - 1 and re.search(r"[\d$%]", cell or "") else ""
            tds.append(f"<td{cls}>{esc(cell)}</td>")
        # pad
        while len(tds) < len(head):
            tds.append("<td></td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    table = (
        f'<div class="table-frame gl-card" style="padding:0">'
        f'<table class="data-table"><thead><tr>{th}</tr></thead>'
        f'<tbody>{"".join(trs)}</tbody></table></div>'
    )
    inset = _table_inset((slide.get("content") or {}).get("key_stats") or [])
    if inset:
        main = (
            f'<div class="gl-areas-table-inset">'
            f'<div class="gl-inset-stage">{inset}</div>'
            f'<div class="gl-inset-table">{table}</div>'
            f"</div>" + insight_strip(_so_what(slide))
        )
    else:
        main = table + insight_strip(_so_what(slide))
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="data_table",
        active=active,
        item_count=len(body),
    )


def render_pill_comparison(slide, total, notes, active=False):
    """Freestanding pill statement columns (#74/F4, grown in #91/F4+).

    Exterior row-label rail + one fully separated rounded column *shell* per
    data column (Q1'26 / Q1'25 / YoY) — the IR statement house style, not
    pill headers over a spreadsheet body. The last column keeps YoY
    emphasis at the shell level. Composes with the floating key_stats
    inset (#73).
    """
    rows = _table_matrix(slide)
    if not rows:
        return render_metric(slide, total, notes, active=active)
    head = rows[0]
    body = rows[1:] if len(rows) > 1 else []
    n_cols = len(head)
    # Exterior label rail: blank head slot, then one stub per body row.
    label_cells = ['<div class="gl-pill-stub gl-pill-head-empty"></div>']
    for r in body:
        label_cells.append(f'<div class="gl-pill-stub">{esc(r[0] if r else "")}</div>')
    labels_rail = f'<div class="gl-pill-labels">{"".join(label_cells)}</div>'
    # One freestanding rounded shell per data column.
    shells = []
    for ci in range(1, n_cols):
        is_last = ci == n_cols - 1
        shell_cls = "gl-pill-shell gl-pill-shell-yoy" if is_last else "gl-pill-shell"
        cell_cls = "gl-pill-cell gl-pill-cell-yoy" if is_last else "gl-pill-cell"
        cells = [f'<div class="gl-pill-head">{esc(head[ci])}</div>']
        for r in body:
            cell = r[ci] if ci < len(r) else ""
            cells.append(f'<div class="{cell_cls}">{esc(cell)}</div>')
        shells.append(f'<div class="{shell_cls}">{"".join(cells)}</div>')
    table = (
        f'<div class="gl-pill gl-pill-free gl-card">'
        f"{labels_rail}"
        f'{"".join(shells)}'
        f"</div>"
    )
    inset = _table_inset((slide.get("content") or {}).get("key_stats") or [])
    if inset:
        main = (
            f'<div class="gl-areas-table-inset">'
            f'<div class="gl-inset-stage">{inset}</div>'
            f'<div class="gl-inset-table">{table}</div>'
            f"</div>" + insight_strip(_so_what(slide))
        )
    else:
        main = table + insight_strip(_so_what(slide))
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="pill_comparison",
        active=active,
        item_count=len(body),
    )


def _hero_stack(stats: Sequence[Any]) -> str:
    """Right-hand giant % callout stack for chart_hero_dual (#75/F5)."""
    cards = []
    for st in stats[:4]:
        nv = _stat_label_value(st)
        if not nv:
            continue
        lab, val = nv
        cards.append(
            f'<div class="gl-hero card">'
            f'<div class="gl-hero-value">{esc(val)}</div>'
            f'<div class="gl-hero-label">{esc(lab)}</div>'
            f"</div>"
        )
    if not cards:
        return ""
    return f'<div class="gl-hero-stack">{"".join(cards)}</div>'


def render_chart_hero_dual(slide, total, notes, active=False, *, use_chartjs: bool = False):
    """Left chart card + right giant-% hero stack as peer cards (#75/F5).

    Hosts a Chart.js chart (charts feature) on the left and large hero-KPI
    callouts (from content.key_stats) on the right — the IR acquisitions
    pattern. Falls back to the SVG painter when charts are suppressed.
    """
    from ..charts import build_chart_html

    vs = slide.get("visual_spec") or {}
    pv = vs.get("primary_visual") or {}
    chart_html = ""
    if isinstance(pv, dict) and pv.get("type"):
        chart_html = build_chart_html(slide, str(pv.get("type")), use_chartjs=use_chartjs)
    hero = _hero_stack((slide.get("content") or {}).get("key_stats") or [])
    if not chart_html and not hero:
        return render_metric(slide, total, notes, active=active)
    main = (
        f'<div class="gl-areas-chart-hero">'
        f'<div class="gl-chart-hero-chart">{chart_html or "<div class=\"chart-empty\">No chart</div>"}</div>'
        f'<div class="gl-chart-hero-stack">{hero}</div>'
        f"</div>" + insight_strip(_so_what(slide))
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="chart_hero_dual",
        active=active,
        item_count=2,
    )


def render_ir_bullet_sheet(slide, total, notes, active=False):
    """Centered title + full-width single-column bullet sheet with selective
    inline bold (#77/F7). Bullet text passes through rich_text (escape +
    ``**bold**``); unsafe markup is escaped (semi-trusted, fail closed).
    """
    from ..rich_text import rich_bullets

    bullets = rich_bullets((slide.get("content") or {}).get("bullets") or [])
    if not bullets:
        return render_metric(slide, total, notes, active=active)
    items = "".join(f'<li class="gl-ir-bullet">{b}</li>' for b in bullets)
    main = (
        f'<div class="gl-areas-ir-bullets">'
        f'<ul class="gl-ir-bullets">{items}</ul>'
        f"</div>" + insight_strip(_so_what(slide))
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="ir_bullet_sheet",
        active=active,
        item_count=len(bullets),
    )


def render_guidance_statement_card(slide, total, notes, active=False):
    """Single bordered card, navy title bar, underlined label→value rows,
    footnote pedestal (#78/F8). IR guidance statement chrome; content comes
    from content.key_stats (label→value rows) and content.so_what / bullets
    for footnotes. Reuses Boardroom tokens.
    """
    c = slide.get("content") or {}
    stats = c.get("key_stats") or []
    rows = []
    for st in stats[:4]:
        nv = _stat_label_value(st)
        if not nv:
            continue
        lab, val = nv
        rows.append(
            f'<div class="gl-guid-row">'
            f'<span class="gl-guid-label">{esc(lab)}</span>'
            f'<span class="gl-guid-value">{esc(val)}</span>'
            f"</div>"
        )
    if not rows:
        return render_metric(slide, total, notes, active=active)
    footnotes = [strip_eids(b) for b in (c.get("bullets") or []) if strip_eids(b)][:3]
    foot_html = ""
    if footnotes:
        foot_items = "".join(f'<div class="gl-guid-foot">{esc(f)}</div>' for f in footnotes)
        foot_html = f'<div class="gl-guid-footnotes">{foot_items}</div>'
    bar_title = strip_eids(c.get("subtitle") or slide.get("title") or "Guidance")
    main = (
        f'<div class="gl-areas-guidance">'
        f'<div class="gl-guidance card">'
        f'<div class="gl-guid-bar">{esc(bar_title)}</div>'
        f'<div class="gl-guid-body">{"".join(rows)}</div>'
        f"</div>"
        f"{foot_html}"
        f"</div>"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="guidance_statement_card",
        active=active,
        item_count=len(rows),
    )


def render_brand_cover(slide, total, notes, active=False, *, divider: bool = False):
    """Full-bleed two-tone brand cover / divider with an inlined brand-mark
    lockup (#76/F6). Brand-parameterizable via content.brand_mark_svg (an
    inline SVG string, data-URL'd so self-contained decks need no fetch) and
    content.brand_tone. Generic — not Amex-hardcoded.
    """
    import base64

    from ..brand import load_brand_mark

    c = slide.get("content") or {}
    mark_name = strip_eids(c.get("brand_mark") or "")
    mark_svg = c.get("brand_mark_svg")
    subtitle = strip_eids(c.get("subtitle") or "")
    tone = strip_eids(c.get("brand_tone") or "two-tone")
    mark_html = ""
    if mark_name:
        # Named vendored seal/lockup (#93/R3): inline SVG, currentColor-toned.
        # Unknown names fail closed inside load_brand_mark.
        named = load_brand_mark(mark_name)
        mark_html = (
            f'<span class="gl-brand-mark gl-brand-mark-named" '
            f'data-mark="{esc(mark_name)}">{named}</span>'
        )
    elif isinstance(mark_svg, str) and mark_svg.strip().startswith("<svg"):
        # Inline as a data URL so the deck stays self-contained (no remote fetch).
        b64 = base64.b64encode(mark_svg.encode("utf-8")).decode("ascii")
        mark_html = (
            f'<img class="gl-brand-mark" alt="brand mark" '
            f'src="data:image/svg+xml;base64,{b64}"/>'
        )
    role = "divider" if divider else "cover"
    layout = "brand_divider" if divider else "brand_cover"
    title = strip_eids(slide.get("title") or "")
    sub_html = f'<div class="gl-brand-sub">{esc(subtitle)}</div>' if subtitle else ""
    main = (
        f'<div class="gl-brand gl-brand-{role} gl-brand-two-tone" data-tone="{esc(tone)}">'
        f"{mark_html}"
        f'<div class="gl-brand-title">{esc(title)}</div>'
        f"{sub_html}"
        f"</div>"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=title,
        dek="",
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html="",
        layout_class=layout,
        active=active,
        item_count=1,
    )


def render_annex_table(slide, total, notes, active=False):
    """Dense widescreen annex table (#81/F12): stub column + many data
    columns, multi-level headers, micro type, full-width within the Fixed
    Stage. Reuses the data_table surface with annex density; not a new
    table component family.
    """
    rows = _table_matrix(slide)
    if not rows:
        return render_metric(slide, total, notes, active=active)
    head = rows[0]
    body = rows[1:] if len(rows) > 1 else []
    # Multi-level headers (#81/F12): visual_spec.primary_visual.header_groups is
    # [{label, span}] spanning the data columns (stub is a rowspan=2 cell).
    vs = slide.get("visual_spec") or {}
    pv = vs.get("primary_visual") or {}
    header_groups = pv.get("header_groups") if isinstance(pv, dict) else None
    thead_rows = []
    if isinstance(header_groups, list) and header_groups:
        top_cells = [f'<th class="gl-annex-stub" rowspan="2"></th>']
        for gi, g in enumerate(header_groups):
            if isinstance(g, dict):
                # F12+ (#94): alternating group banding for IR annex precision.
                band = " gl-annex-group-alt" if gi % 2 else ""
                top_cells.append(
                    f'<th class="gl-annex-group{band}" colspan="{int(g.get("span") or 1)}">{esc(strip_eids(g.get("label") or ""))}</th>'
                )
        thead_rows.append("<tr>" + "".join(top_cells) + "</tr>")
        sub_cells = "".join(
            f'<th class="gl-annex-head">{esc(h)}</th>' for h in head[1:]
        )
        thead_rows.append("<tr>" + sub_cells + "</tr>")
        thead = "".join(thead_rows)
    else:
        thead = "<tr>" + "".join(
            f'<th class="{"gl-annex-stub" if i == 0 else "gl-annex-head"}">{esc(h)}</th>'
            for i, h in enumerate(head)
        ) + "</tr>"
    trs = []
    for r in body:
        tds = []
        for i, cell in enumerate(r):
            cls = "gl-annex-stub" if i == 0 else ("gl-annex-cell num" if re.search(r"[\d$%]", cell or "") else "gl-annex-cell")
            tds.append(f'<td class="{cls}">{esc(cell)}</td>')
        while len(tds) < len(head):
            tds.append('<td class="gl-annex-cell"></td>')
        trs.append("<tr>" + "".join(tds) + "</tr>")
    table = (
        f'<div class="gl-annex table-frame gl-card gl-annex-micro">'
        f'<table class="data-table annex-table"><thead>{thead}</thead>'
        f'<tbody>{"".join(trs)}</tbody></table></div>'
    )
    main = table + insight_strip(_so_what(slide))
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="annex_table",
        active=active,
        item_count=len(body),
    )


def render_multi_panel(slide, total, notes, active=False, *, use_chartjs: bool = False):
    """Multi-region / multi-chart board host (#80/F11). Renders each tile in
    visual_spec.primary_visual.tiles as a gl-* region: chart tiles embed a
    Chart.js chart (canonical path, reusing build_chart_html) beside metric
    tiles. Builds on the chart-embedding pattern proven by chart_hero_dual.
    """
    from ..charts import build_chart_html

    vs = slide.get("visual_spec") or {}
    pv = vs.get("primary_visual") or {}
    tiles = pv.get("tiles") if isinstance(pv, dict) else None
    if not isinstance(tiles, list) or not tiles:
        return render_metric(slide, total, notes, active=active)
    parts = []
    for tile in tiles:
        if not isinstance(tile, dict):
            continue
        kind = str(tile.get("kind") or "metric")
        label = strip_eids(tile.get("label") or "")
        if kind == "chart":
            sub_slide = {
                **slide,
                "layout_type": str(tile.get("chart_type") or "grouped_bar_chart"),
                "visual_spec": {
                    "primary_visual": {
                        "type": str(tile.get("chart_type") or "grouped_bar_chart"),
                        "steps_or_data": tile.get("steps_or_data") or [],
                        "chart_config": tile.get("chart_config") or {},
                    }
                },
            }
            chart_html = build_chart_html(
                sub_slide, sub_slide["layout_type"], use_chartjs=use_chartjs
            )
            lbl = f'<div class="gl-tile-label">{esc(label)}</div>' if label else ""
            # IR dual tall-card slots (#90/F11+): freestanding top total,
            # exterior side legend, badge callout. Only engaged when present,
            # so legacy tiles keep their existing chrome.
            top_total = strip_eids(tile.get("top_total") or "")
            badge = strip_eids(tile.get("badge") or "")
            legend = tile.get("side_legend")
            legend_html = ""
            if isinstance(legend, list) and legend:
                items = []
                for entry in legend:
                    if isinstance(entry, dict):
                        txt = strip_eids(entry.get("label") or "")
                        swatch = strip_eids(entry.get("color") or "")
                    else:
                        txt, swatch = strip_eids(entry), ""
                    if not txt:
                        continue
                    sw = (
                        f'<span class="gl-tile-swatch" style="background:{esc(swatch)}"></span>'
                        if swatch
                        else ""
                    )
                    items.append(f'<li class="gl-tile-legend-item">{sw}{esc(txt)}</li>')
                if items:
                    legend_html = f'<ul class="gl-tile-legend">{"".join(items)}</ul>'
            if top_total or badge or legend_html:
                badge_html = (
                    f'<span class="gl-tile-badge">{esc(badge)}</span>' if badge else ""
                )
                if legend_html:
                    body = (
                        f'<div class="gl-tile-body">'
                        f'<div class="gl-tile-chart-area">{chart_html}</div>'
                        f"{legend_html}"
                        f"</div>"
                    )
                else:
                    body = chart_html
                # #99/F11+: opt-in IR navy skin — header band hosts the top
                # total + tile label; Boardroom default skin unchanged.
                if str(tile.get("tile_skin") or "").lower() == "ir":
                    head_total = (
                        f'<span class="gl-tile-ir-total">{esc(top_total)}</span>'
                        if top_total
                        else ""
                    )
                    head_lbl = (
                        f'<span class="gl-tile-ir-title">{esc(label)}</span>'
                        if label
                        else ""
                    )
                    parts.append(
                        f'<div class="gl-tile gl-tile-chart gl-tile-tall gl-tile-ir">'
                        f'<div class="gl-tile-ir-head">{head_total}{head_lbl}</div>'
                        f"{badge_html}{body}"
                        f"</div>"
                    )
                else:
                    total_html = (
                        f'<div class="gl-tile-top-total">{esc(top_total)}</div>'
                        if top_total
                        else ""
                    )
                    parts.append(
                        f'<div class="gl-tile gl-tile-chart gl-tile-tall">'
                        f"{badge_html}{total_html}{lbl}{body}"
                        f"</div>"
                    )
            else:
                parts.append(
                    f'<div class="gl-tile gl-tile-chart">{lbl}{chart_html}</div>'
                )
        else:
            val = strip_eids(tile.get("value") or "")
            parts.append(
                f'<div class="gl-tile gl-tile-metric">'
                f'<div class="gl-tile-metric-value">{esc(val)}</div>'
                f'<div class="gl-tile-label">{esc(label)}</div>'
                f"</div>"
            )
    if not parts:
        return render_metric(slide, total, notes, active=active)
    n = len(parts)
    cols = 2 if n <= 4 else 3
    main = (
        f'<div class="gl-multi-panel gl-multi-panel-{cols}col">'
        f'{"".join(parts)}'
        f"</div>" + insight_strip(_so_what(slide))
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="multi_panel",
        active=active,
        item_count=n,
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


def render_process(slide, total, notes, active=False, vertical: bool | None = None):
    layout = (slide.get("layout_type") or "").lower()
    steps_raw = []
    for st in _vs_steps(slide):
        if isinstance(st, str):
            steps_raw.append(strip_eids(st))
        elif isinstance(st, dict):
            steps_raw.append(strip_eids(st.get("title") or st.get("text") or st.get("label") or ""))
        elif isinstance(st, (list, tuple)):
            steps_raw.append(strip_eids(" — ".join(str(x) for x in st if x)))
    steps_raw = [s for s in steps_raw if s]
    if layout in ("timeline", "roadmap"):
        steps_raw = apply_timeline_year_overrides(slide.get("title") or "", steps_raw)
    if vertical is None:
        vertical = layout in ("timeline", "roadmap") and len(steps_raw) == 4

    outcome = None
    cards_src = list(steps_raw)
    if not vertical and len(cards_src) >= 4 and _CLOSED_LOOP.search(cards_src[-1] or ""):
        outcome = cards_src[-1]
        cards_src = cards_src[:-1]

    flow = _sequential_grid(cards_src, vertical=vertical)
    if outcome:
        ok, ot = split_step_copy(outcome)
        flow += (
            f'<div class="process-outcome gl-process-outcome">'
            f'<div class="badge">{len(cards_src)+1:02d}</div>'
            f'<div class="kicker">{esc(ok or "Closed-loop")}</div>'
            f'<div class="text">{esc(ot or outcome)}</div></div>'
        )
    main = flow + insight_strip(_so_what(slide))
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class=layout or "full_process_flow",
        active=active,
        item_count=len(cards_src) + (1 if outcome else 0),
    )


def render_evidence_cards(slide, total, notes, active=False):
    """Adaptive evidence card grid (2/3/4 columns by item count)."""
    c = _content(slide)

    # Gather evidence items: evidence_sources, then supporting_points, then bullets
    items: list[dict[str, str]] = []
    for item in (slide.get("evidence_sources") or []):
        if isinstance(item, dict):
            label = strip_eids(
                item.get("source_file") or item.get("file") or item.get("id") or ""
            )
            eid = strip_eids(item.get("id") or item.get("evidence_id") or "")
            if label:
                items.append({"label": label, "value": eid})
        elif isinstance(item, str):
            if "." in item:
                items.append({"label": item, "value": ""})

    if not items:
        for line in (
            c.get("supporting_points") or c.get("bullets") or []
        ):
            line = strip_eids(line)
            if not line:
                continue
            if ":" in line:
                k, _, v = line.partition(":")
                items.append({"label": k.strip(), "value": v.strip()})
            else:
                items.append({"label": line, "value": ""})

    n = min(len(items), 8)
    if n == 4:
        cols_class = "gl-grid-dense-2x2"
    elif n >= 5:
        cols_class = "gl-grid-3"
    elif n == 3:
        cols_class = "gl-grid-3"
    else:
        cols_class = f"gl-grid-{max(n, 1)}"

    cards = []
    for it in items[:8]:
        val_html = f'<div class="evidence-value">{esc(it["value"])}</div>' if it["value"] else ""
        cards.append(
            f'<div class="gl-card evidence-card">'
            f'<div class="evidence-label">{esc(it["label"])}</div>'
            f"{val_html}</div>"
        )

    if not cards:
        cards = [
            '<div class="gl-card evidence-card">'
            '<div class="evidence-label">No evidence</div></div>'
        ]

    main = (
        f'<div class="gl-grid {cols_class} evidence-grid layout-evidence-cards">'
        f'{"".join(cards)}'
        f"</div>"
        f"{insight_strip(_so_what(slide))}"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="evidence_cards",
        active=active,
        item_count=n,
    )


def render_data_table_with_insight(slide, total, notes, active=False):
    """Data table with an insight strip below it."""
    rows = _table_matrix(slide)
    if not rows:
        return render_table(slide, total, notes, active=active)

    if table_as_kpi(rows):
        # Table is KPI-like; render as metric_row_with_breakdown instead
        body = rows[1:] if rows[0] and rows[0][0].lower() in ("metric", "name", "label", "item") else rows
        stats = [{"label": r[0], "value": r[1] if len(r) > 1 else ""} for r in body]
        n = len(stats)
        cols_class = "gl-grid-dense-2x2" if n == 4 else ("gl-grid-3" if n >= 3 else f"gl-grid-{max(n,1)}")
        main = (
            f'<div class="gl-areas-metric layout-data-table-insight">'
            f'<div class="gl-grid {cols_class} gl-stats">{_kpi_cards(stats, cols_class="gl-grid")}</div>'
            f'<div class="gl-insight">{insight_strip(_so_what(slide))}</div>'
            f"</div>"
        )
    else:
        # True table with insight strip
        head = rows[0]
        body = rows[1:] if len(rows) > 1 else []
        th = "".join(f"<th>{esc(h)}</th>" for h in head)
        trs = []
        for r in body:
            tds = []
            for i, cell in enumerate(r):
                cls = ' class="num"' if i == len(r) - 1 and re.search(r"[\d$%]", cell or "") else ""
                tds.append(f"<td{cls}>{esc(cell)}</td>")
            while len(tds) < len(head):
                tds.append("<td></td>")
            trs.append("<tr>" + "".join(tds) + "</tr>")
        table_html = (
            f'<div class="table-frame gl-card" style="padding:0">'
            f'<table class="data-table"><thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(trs)}</tbody></table></div>'
        )
        main = table_html + insight_strip(_so_what(slide))

    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="data_table_with_insight",
        active=active,
        item_count=len(body) if not table_as_kpi(rows) else len(body) - 1,
    )


def render_comparison_with_metrics(slide, total, notes, active=False):
    """Comparison cards with a metric strip below."""
    pairs = pair_comparison(slide)
    cards = []
    for head, body in pairs:
        if not head and not body:
            continue
        cards.append(
            f'<article class="comparison-card risk">'
            f'<div class="card-head">{esc(head)}</div>'
            f'<div class="card-body"><p>{esc(body)}</p></div>'
            f"</article>"
        )

    # Metric strip from key_stats
    c = _content(slide)
    stats = c.get("key_stats") or []
    metric_strip = ""
    if stats:
        tiles = ""
        for s in stats[:4]:
            if isinstance(s, dict):
                tiles += (
                    f'<div class="metric-tile">'
                    f'<div class="metric-value">{esc(s.get("value", ""))}</div>'
                    f'<div class="metric-label">{esc(s.get("label", ""))}</div></div>'
                )
        if tiles:
            metric_strip = f'<div class="metric-strip gl-grid gl-grid-4">{tiles}</div>'

    main = (
        f'<div class="comparison-grid gl-grid gl-grid-2 layout-comparison-with-metrics">'
        f'{"".join(cards)}'
        f'</div>'
        f"{metric_strip}"
        f"{insight_strip(_so_what(slide))}"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="comparison_with_metrics",
        active=active,
        item_count=len(cards),
    )


def render_comparison(slide, total, notes, active=False):
    pairs = pair_comparison(slide)
    vs = slide.get("visual_spec") or {}
    circle_data = vs.get("circle_data") or []
    cards = []
    for ci, (head, body) in enumerate(pairs):
        if not head and not body:
            continue
        # never invent house closer
        if body.lower().startswith("keep this open through close"):
            body = ""
        circle_html = ""
        if ci < len(circle_data) and isinstance(circle_data[ci], dict):
            cd = circle_data[ci]
            circle_html = _circle_pair_svg(
                value_before=float(cd.get("value_before", 0)),
                value_after=float(cd.get("value_after", 0)),
                max_value=float(cd.get("max_value", 100)),
                unit=cd.get("unit", "%"),
                label="",
            )
        cards.append(
            f'<article class="comparison-card card risk">'
            f'<div class="card-head">{esc(head)}</div>'
            f'{circle_html}'
            f'<div class="card-body"><p>{esc(body)}</p></div>'
            f"</article>"
        )
    main = f'<div class="comparison-grid gl-grid gl-grid-2 layout-comparison">{"".join(cards)}</div>'
    main += insight_strip(_so_what(slide))
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="comparison_grid",
        active=active,
        item_count=len(cards),
    )


def render_quote(slide, total, notes, active=False):
    steps = _vs_steps(slide)
    quotes = []
    for st in steps:
        if isinstance(st, dict):
            text = st.get("text") or st.get("quote") or st.get("body") or ""
            attr = st.get("attribution") or st.get("cite") or ""
            body = clean_quote_body(text)
            cite = parse_cite_from_quote(text, attr)
            if body:
                quotes.append((body, cite))
        elif isinstance(st, str):
            body = clean_quote_body(st)
            cite = parse_cite_from_quote(st)
            if body:
                quotes.append((body, cite))
    if not quotes:
        body = clean_quote_body(_content(slide).get("body_text") or _content(slide).get("headline") or "")
        if body:
            quotes.append((body, ""))

    sow = _so_what(slide)
    n = len(quotes)
    if n >= 2:
        cards = []
        for body, cite in quotes[:3]:
            cite_html = f"<cite>{esc(cite)}</cite>" if cite else ""
            cards.append(
                f'<article class="quote-card card">'
                f"<blockquote>{esc(body)}</blockquote>{cite_html}</article>"
            )
        main = f'<div class="gl-areas-quote-stack quote-layout--stack">{"".join(cards)}</div>'
    else:
        body, cite = quotes[0] if quotes else ("", "")
        cite_html = f"<cite>{esc(cite)}</cite>" if cite else ""
        insight = f'<div class="quote-insight">{esc(sow)}</div>' if sow else ""
        main = (
            f'<div class="quote-layout--single">'
            f'<article class="quote-card card"><blockquote>{esc(body)}</blockquote>{cite_html}</article>'
            f"{insight}"
            f"</div>"
        )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        layout_class="quote_card",
        active=active,
        item_count=n,
    )


def render_icon_grid(slide, total, notes, active=False):
    from ..charts import build_icon_grid_html

    main = build_icon_grid_html(slide)
    main += insight_strip(_so_what(slide))
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        layout_class="icon_grid",
        active=active,
        item_count=4,
    )


def render_chart(slide, total, notes, active=False, *, use_chartjs: bool = False):
    from ..charts import build_chart_html

    layout = (slide.get("layout_type") or "grouped_bar_chart").lower()
    chart_html = build_chart_html(slide, layout, use_chartjs=use_chartjs)
    vs = slide.get("visual_spec") or {}
    secondary = vs.get("secondary_visual") or {}
    key_stats = (slide.get("content") or {}).get("key_stats") or []

    has_table = bool(secondary) and layout == "line_chart"
    has_stats = bool(key_stats)

    # When supporting elements share the slide, shrink the chart SVG so the
    # table / metric strip stay inside the 1920x1080 stage (PDF pattern:
    # chart ~60%, supporting element ~40%).
    wrap_classes: list[str] = []
    if has_table:
        wrap_classes.append("chart-split")
    if has_stats:
        wrap_classes.append("chart-with-stats")
    if wrap_classes:
        cls = " ".join(wrap_classes)
        main = f'<div class="chart-svg-wrap {cls}">{chart_html}</div>'
    else:
        main = chart_html

    # Supporting data table below chart (e.g., line chart + table)
    if has_table:
        from ..charts import chart_column_interval

        sec_steps = secondary.get("steps_or_data") or []
        table_rows: list[list[str]] = []
        for st in sec_steps:
            if isinstance(st, (list, tuple)):
                table_rows.append([strip_eids(str(x)) for x in st])
            elif isinstance(st, str) and "|" in st:
                table_rows.append([strip_eids(x) for x in st.split("|")])
        if table_rows:
            header = table_rows[0]
            body = table_rows[1:]

            # --- Plot alignment (spatial composition contract, #36) --------
            # When the table's header cells match the chart's category labels
            # 1:1, each value column is centered under its chart category and
            # the table shares the SVG's width context (PDF house style).
            primary = vs.get("primary_visual") or {}
            raw_steps = primary.get("steps_or_data") or []
            labels = [
                str(p.get("label") or p.get("x") or "").strip()
                for p in raw_steps
                if isinstance(p, Mapping)
            ]
            n = len(labels)
            aligned = (
                n > 0
                and len(raw_steps) == n
                and all(len(r) == n + 1 for r in table_rows)
                and [c.strip() for c in header[1:]] == labels
            )
            if aligned:
                left, right, width = chart_column_interval(layout, n)
                # colgroup percentages of the table's own width; the table
                # spans [0, right] of the shared SVG width context, so an
                # absolute column center (pct * table_w) must equal the
                # category point's cx / width — the alignment invariant.
                table_w = right / width * 100
                label_w = left / right * 100  # label col as % of table width
                col_w = (right - left) / n / right * 100
                colgroup = (
                    "<colgroup>"
                    f'<col style="width:{label_w:.2f}%">'
                    + f'<col style="width:{col_w:.2f}%">' * n
                    + "</colgroup>"
                )
                # expose the mapped SVG interval for geometric verification
                align_attrs = (
                    f' data-align-left="{left:.1f}" data-align-right="{right:.1f}"'
                    f' data-align-width="{width:.1f}"'
                )
            else:
                colgroup = ""
                align_attrs = ""

            tbl_cls = "chart-support-table" + (" chart-table-aligned" if aligned else "")
            tbl_style = f' style="width:{table_w:.2f}%"' if aligned else ""
            tbl = f'<table class="{tbl_cls}"{tbl_style}{align_attrs}>{colgroup}<thead><tr>'
            tbl += "".join(f"<th>{esc(h)}</th>" for h in header)
            tbl += "</tr></thead><tbody>"
            for row in body:
                tbl += "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>"
            tbl += "</tbody></table>"
            # Width sharing is UNCONDITIONAL (#40): every support table lives
            # inside the chart's width context (.chart-col), whether or not
            # its columns align with chart categories. Column alignment
            # (colgroup) remains conditional on the header/category match.
            cls = " ".join(wrap_classes + (["chart-align-table"] if aligned else []))
            main = (
                f'<div class="chart-svg-wrap {cls}">'
                f'<div class="chart-col">{chart_html}{tbl}</div></div>'
            )
    # Metric strip from key_stats (PDF pattern: chart + KPI row below)
    if has_stats:
        tiles = ""
        for s in key_stats[:6]:
            if isinstance(s, dict):
                tiles += (
                    f'<div class="metric-tile">'
                    f'<div class="metric-value">{esc(str(s.get("value", "")))}</div>'
                    f'<div class="metric-label">{esc(str(s.get("label", "")))}</div></div>'
                )
        if tiles:
            n = min(len(key_stats), 6)
            main += f'<div class="metric-strip chart-metric-strip gl-grid gl-grid-{n}">{tiles}</div>'
    main += insight_strip(_so_what(slide))
    cfg = vs.get("chart_config") or {}
    frame_cls = "chart-frame gl-card"
    if cfg.get("surface") == "white":
        frame_cls += " chart-surface-white"
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=f'<div class="{frame_cls}" style="padding:18px 22px">{main}</div>',
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class=layout,
        active=active,
        item_count=3,
    )


def render_dual_chart(slide, total, notes, active=False, *, use_chartjs: bool = False):
    """Two charts side by side (PDF p17: bar chart left, line chart right).

    visual_spec.primary_visual and visual_spec.secondary_visual each carry
    their own ``type`` + ``steps_or_data`` + optional per-pane
    ``chart_config`` / ``line_overlay``. Each pane is built through the
    standard chart pipeline (internal builders, pack fallback).
    """
    from ..charts import build_chart_html

    vs = slide.get("visual_spec") or {}
    panes: list[str] = []
    for key in ("primary_visual", "secondary_visual"):
        visual = vs.get(key)
        if not isinstance(visual, dict) or not visual:
            continue
        vt = str(visual.get("type") or "grouped_bar_chart").lower()
        sub_vs: dict[str, Any] = {
            "primary_visual": visual,
            "chart_config": visual.get("chart_config") or {},
        }
        if visual.get("line_overlay"):
            sub_vs["line_overlay"] = visual["line_overlay"]
        if visual.get("annotation"):
            sub_vs["annotation"] = visual["annotation"]
        sub_slide = {
            "slide_number": slide.get("slide_number", 1),
            "title": slide.get("title", ""),
            "layout_type": vt,
            "content": {},
            "visual_spec": sub_vs,
            "evidence_sources": slide.get("evidence_sources") or [],
        }
        panes.append(
            f'<div class="dual-chart-pane">'
            f"{build_chart_html(sub_slide, vt, use_chartjs=use_chartjs)}</div>"
        )
    main = f'<div class="gl-grid gl-grid-2 dual-chart">{"".join(panes)}</div>'
    main += insight_strip(_so_what(slide))
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=f'<div class="chart-frame gl-card" style="padding:18px 22px">{main}</div>',
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="dual_chart",
        active=active,
        item_count=3,
    )


def render_metric_row_with_breakdown(slide, total, notes, active=False):
    """KPI row with a breakdown/detail band below each metric."""
    c = _content(slide)
    stats = c.get("key_stats") or []
    if not stats:
        rows = _table_matrix(slide)
        body = rows[1:] if rows and rows[0][0].lower() in ("metric", "label") else rows
        stats = [{"label": r[0], "value": r[1] if len(r) > 1 else "", "source": r[2] if len(r) > 2 else ""} for r in body if r]

    n = min(len(stats), 6)
    cols_class = "gl-grid-dense-2x2" if n == 4 else ("gl-grid-3" if n >= 3 else f"gl-grid-{max(n,1)}")

    cards = []
    for st in stats[:6]:
        if isinstance(st, dict):
            lab = strip_eids(st.get("label") or "")
            val = strip_eids(st.get("value") or "")
            src = strip_eids(st.get("source") or "")
        elif isinstance(st, (list, tuple)) and len(st) >= 2:
            lab, val, src = strip_eids(st[0]), strip_eids(st[1]), strip_eids(st[2] if len(st) > 2 else "")
        else:
            continue
        if not lab and not val:
            continue

        src_html = f'<div class="kpi-source">{esc(src)}</div>' if src else ""
        cards.append(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">{esc(lab)}</div>'
            f'<div class="kpi-value">{esc(val)}</div>'
            f"{src_html}</div>"
        )

    if not cards:
        return render_metric(slide, total, notes, active=active)

    # Breakdown band: supporting_points as a compact table strip
    supporting = [strip_eids(b) for b in (c.get("supporting_points") or []) if strip_eids(b)]
    bullets = [strip_eids(b) for b in (c.get("bullets") or []) if strip_eids(b)]
    breakdown_rows = supporting or bullets

    breakdown_html = ""
    if breakdown_rows:
        rows_html = []
        for row in breakdown_rows[:8]:
            if ":" in row:
                k, _, v = row.partition(":")
                rows_html.append(
                    f'<div class="breakdown-row">'
                    f'<span class="breakdown-key">{esc(k.strip())}</span>'
                    f'<span class="breakdown-val">{esc(v.strip())}</span></div>'
                )
            else:
                rows_html.append(f'<div class="breakdown-row breakdown-plain">{esc(row)}</div>')
        breakdown_html = (
            f'<div class="gl-card breakdown-card">'
            f'<h3 class="gl-card-hat">Breakdown</h3>'
            f'<div class="breakdown-list">{"".join(rows_html)}</div></div>'
        )

    main = (
        f'<div class="gl-areas-metric layout-metric-row">'
        f'<div class="gl-grid {cols_class} gl-stats">{"".join(cards)}</div>'
        f"{breakdown_html}"
        f"{insight_strip(_so_what(slide))}"
        f"</div>"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="metric_row_with_breakdown",
        active=active,
        item_count=n,
    )


def render_insight_with_evidence(slide, total, notes, active=False):
    """Hero insight statement with supporting evidence cards in a grid below."""
    c = _content(slide)
    insight = strip_eids(c.get("so_what") or c.get("headline") or "")
    if not insight or banned_face_opener(insight):
        insight = ""

    # Evidence sources or supporting_points as cards
    evidence: list[dict] = []
    for item in (slide.get("evidence_sources") or []):
        if isinstance(item, dict):
            src = strip_eids(item.get("source_file") or item.get("file") or item.get("id") or "")
            eid = strip_eids(item.get("id") or item.get("evidence_id") or "")
            if src:
                evidence.append({"label": src, "value": eid})
        elif isinstance(item, str):
            if "." in item:
                evidence.append({"label": item, "value": ""})

    supporting = [strip_eids(b) for b in (c.get("supporting_points") or []) if strip_eids(b)]
    bullets = [strip_eids(b) for b in (c.get("bullets") or []) if strip_eids(b)]

    if not evidence and (supporting or bullets):
        for item in (supporting or bullets)[:6]:
            if ":" in item:
                k, _, v = item.partition(":")
                evidence.append({"label": k.strip(), "value": v.strip()})
            else:
                evidence.append({"label": item, "value": ""})

    n = len(evidence)
    cols_class = "gl-grid-dense-2x2" if n == 4 else ("gl-grid-3" if n >= 3 else "gl-grid-2")

    insight_html = (
        f'<div class="gl-card insight-hero">'
        f'<div class="insight-hero-text">{esc(insight)}</div></div>'
        if insight
        else ""
    )

    evidence_cards = []
    for ev in evidence[:6]:
        val_html = f'<div class="evidence-value">{esc(ev["value"])}</div>' if ev.get("value") else ""
        evidence_cards.append(
            f'<div class="gl-card evidence-card">'
            f'<div class="evidence-label">{esc(ev["label"])}</div>'
            f"{val_html}</div>"
        )

    evidence_html = ""
    if evidence_cards:
        evidence_html = f'<div class="gl-grid {cols_class} evidence-grid">{"".join(evidence_cards)}</div>'

    main = (
        f'<div class="layout-insight-evidence">'
        f"{insight_html}"
        f"{evidence_html}"
        f"</div>"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="insight_with_evidence",
        active=active,
        item_count=n,
    )


def render_priority_matrix(slide, total, notes, active=False):
    """2×2 priority/impact matrix as a grid of quadrant cards."""
    steps = _vs_steps(slide)
    c = _content(slide)
    bullets = [strip_eids(b) for b in (c.get("bullets") or []) if strip_eids(b)]

    # Parse steps into quadrant items: expected [high_p_high_i, high_p_low_i, low_p_high_i, low_p_low_i]
    quadrant_data: list[list[str]] = [[], [], [], []]
    quadrant_labels = ["High Priority / High Impact", "High Priority / Lower Impact", "Lower Priority / High Impact", "Lower Priority / Lower Impact"]

    if len(steps) >= 4 and all(isinstance(s, (list, tuple)) and len(s) >= 2 for s in steps[:4]):
        for i, row in enumerate(steps[:4]):
            quadrant_data[i] = [strip_eids(x) for x in row[1:] if strip_eids(x)]
            label_raw = strip_eids(row[0]) if row else ""
            if label_raw:
                quadrant_labels[i] = label_raw
    else:
        # Fallback: distribute bullets into 4 quadrants
        for i, b in enumerate(bullets[:4]):
            quadrant_data[i % 4].append(b)

    quadrant_cards = []
    for i, (label, items) in enumerate(zip(quadrant_labels, quadrant_data)):
        items_html = "".join(f'<li>{esc(x)}</li>' for x in items) if items else "<li>—</li>"
        quadrant_cards.append(
            f'<div class="gl-card priority-quadrant quadrant-{i}">'
            f'<h3 class="gl-card-hat">{esc(label)}</h3>'
            f'<ul class="priority-list">{items_html}</ul></div>'
        )

    main = (
        f'<div class="gl-grid gl-grid-dense-2x2 layout-priority-matrix">'
        f'{"".join(quadrant_cards)}'
        f"</div>"
        f"{insight_strip(_so_what(slide))}"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="priority_matrix",
        active=active,
        item_count=len(quadrant_cards),
    )


def render_system_architecture(slide, total, notes, active=False):
    """Layered node graph using diagram primitives."""
    from ..diagram.builder import system_architecture_scene

    diagram = system_architecture_scene(slide)
    main = (
        f'<div class="gl-areas-diagram layout-system-architecture">'
        f'<div class="diagram-wrap">{diagram}</div>'
        f"{insight_strip(_so_what(slide))}"
        f"</div>"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="system_architecture",
        active=active,
        item_count=3,
    )


def render_data_flow_diagram(slide, total, notes, active=False):
    """Horizontal data pipeline using diagram primitives."""
    from ..diagram.builder import data_flow_scene

    diagram = data_flow_scene(slide)
    main = (
        f'<div class="gl-areas-diagram layout-data-flow">'
        f'<div class="diagram-wrap">{diagram}</div>'
        f"{insight_strip(_so_what(slide))}"
        f"</div>"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="data_flow_diagram",
        active=active,
        item_count=4,
    )


def render_causal_loop(slide, total, notes, active=False):
    """Circular feedback loop using diagram primitives."""
    from ..diagram.builder import causal_loop_scene

    diagram = causal_loop_scene(slide)
    main = (
        f'<div class="gl-areas-diagram layout-causal-loop">'
        f'<div class="diagram-wrap">{diagram}</div>'
        f"{insight_strip(_so_what(slide))}"
        f"</div>"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="causal_loop",
        active=active,
        item_count=4,
    )


def render_before_after(slide, total, notes, active=False):
    """Side-by-side before/after comparison using diagram primitives."""
    from ..diagram.builder import before_after_scene

    diagram = before_after_scene(slide)
    main = (
        f'<div class="gl-areas-diagram layout-before-after">'
        f'<div class="diagram-wrap">{diagram}</div>'
        f"{insight_strip(_so_what(slide))}"
        f"</div>"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="before_after",
        active=active,
        item_count=2,
    )


def render_freeform(slide, total, notes, active=False):
    """Phase 7: named-area visual_spec.grid body inside standard gl-slide shell."""
    from .freeform import render_freeform_main

    main = render_freeform_main(slide)
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="freeform_grid",
        active=active,
        item_count=3,
    )


# ---------------------------------------------------------------------------
# Wave 3a — Strategic & Structural layouts
# ---------------------------------------------------------------------------

def render_risk_opportunity(slide, total, notes, active=False):
    """Two-column risks vs. opportunities with color-coded cards."""
    c = _content(slide)
    risks = [strip_eids(b) for b in (c.get("risks") or c.get("bullets") or []) if strip_eids(b)][:4]
    opportunities = [strip_eids(b) for b in (c.get("opportunities") or c.get("supporting_points") or []) if strip_eids(b)][:4]
    risk_cards = ""
    for r in risks:
        risk_cards += f'<div class="risk-card card">{esc(r)}</div>'
    opp_cards = ""
    for o in opportunities:
        opp_cards += f'<div class="opportunity-card card">{esc(o)}</div>'
    main = (
        f'<div class="gl-grid gl-grid-2 layout-risk-opportunity">'
        f'<div class="risk-column">'
        f'<h3 class="column-head">Risks</h3>'
        f'<div class="gl-grid">{risk_cards}</div></div>'
        f'<div class="opportunity-column">'
        f'<h3 class="column-head">Opportunities</h3>'
        f'<div class="gl-grid">{opp_cards}</div></div>'
        f'</div>'
        f'{insight_strip(_so_what(slide))}'
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="risk_opportunity",
        active=active,
        item_count=len(risks) + len(opportunities),
    )


def render_recommendation_with_rationale(slide, total, notes, active=False):
    """Strong recommendation header + evidence card grid."""
    c = _content(slide)
    recommendation = strip_eids(c.get("recommendation") or c.get("headline") or "")
    evidence = [strip_eids(b) for b in (c.get("supporting_points") or c.get("bullets") or []) if strip_eids(b)][:6]
    cards = ""
    for e in evidence:
        cards += f'<div class="evidence-card card">{esc(e)}</div>'
    cols = "gl-grid-3" if len(evidence) >= 3 else f"gl-grid-{max(len(evidence), 1)}"
    main = (
        f'<div class="layout-recommendation">'
        f'<div class="recommendation-head">{esc(recommendation)}</div>'
        f'<div class="gl-grid {cols}">{cards}</div>'
        f'</div>'
        f'{insight_strip(_so_what(slide))}'
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="recommendation_with_rationale",
        active=active,
        item_count=len(evidence),
    )


def render_section_divider(slide, total, notes, active=False):
    """Low-density section break with message and accent line."""
    c = _content(slide)
    message = strip_eids(c.get("headline") or c.get("body_text") or slide.get("title") or "")
    subtitle = strip_eids(c.get("subtitle") or "")
    sub_html = f'<p class="section-subtitle">{esc(subtitle)}</p>' if subtitle else ""
    main = (
        f'<div class="layout-section-divider">'
        f'<div class="accent-line"></div>'
        f'<h2 class="section-message">{esc(message)}</h2>'
        f'{sub_html}'
        f'</div>'
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek="",  # subtitle already rendered in the centered divider body
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="section_divider",
        active=active,
        item_count=1,
    )


def render_before_after_detailed(slide, total, notes, active=False):
    """Extended before/after with numbered narrative steps."""
    c = _content(slide)
    before = strip_eids(c.get("before") or "")
    after = strip_eids(c.get("after") or "")
    steps = [strip_eids(b) for b in (c.get("steps") or c.get("bullets") or []) if strip_eids(b)][:4]
    step_html = ""
    for i, s in enumerate(steps, 1):
        step_html += f'<div class="transformation-step"><span class="step-num">{i}</span>{esc(s)}</div>'
    main = (
        f'<div class="gl-grid gl-grid-2 layout-before-after-detailed">'
        f'<div class="before-panel card">'
        f'<h3 class="panel-label">Before</h3><p>{esc(before)}</p></div>'
        f'<div class="after-panel card">'
        f'<h3 class="panel-label">After</h3><p>{esc(after)}</p></div>'
        f'</div>'
        f'<div class="transformation-steps">{step_html}</div>'
        f'{insight_strip(_so_what(slide))}'
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="before_after_detailed",
        active=active,
        item_count=len(steps) + 2,
    )


# ---------------------------------------------------------------------------
# Wave 3b — Data, Comparison & Process layouts
# ---------------------------------------------------------------------------

def render_kpi_trend_cards(slide, total, notes, active=False):
    """KPI grid with mini trend indicators (arrow up/down)."""
    c = _content(slide)
    stats = c.get("key_stats") or []
    if not stats:
        rows = _table_matrix(slide)
        body = rows[1:] if rows and rows[0][0].lower() in ("metric", "label") else rows
        stats = [{"label": r[0], "value": r[1] if len(r) > 1 else ""} for r in body if r]
    cards = []
    for s in stats[:6]:
        if isinstance(s, dict):
            lab = strip_eids(s.get("label") or "")
            val = strip_eids(s.get("value") or "")
            trend = s.get("trend", "")
            trend_icon = "▲" if trend == "up" else ("▼" if trend == "down" else "—")
        elif isinstance(s, (list, tuple)) and len(s) >= 2:
            lab, val = strip_eids(s[0]), strip_eids(s[1])
            trend_icon = "—"
        else:
            continue
        cards.append(
            f'<div class="kpi-trend-card card">'
            f'<div class="kpi-label">{esc(lab)}</div>'
            f'<div class="kpi-value">{esc(val)} <span class="trend">{trend_icon}</span></div>'
            f'</div>'
        )
    n = len(cards)
    cols = "gl-grid-3" if n >= 3 else f"gl-grid-{max(n, 1)}"
    if n == 1:
        cols = "gl-grid"
    main = (
        f'<div class="gl-grid {cols} layout-kpi-trend">'
        f'{"".join(cards)}'
        f'</div>'
        f'{insight_strip(_so_what(slide))}'
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="kpi_trend_cards",
        active=active,
        item_count=n,
    )


def render_three_column_comparison(slide, total, notes, active=False):
    """Three-way comparison cards in a .grid-3 layout."""
    c = _content(slide)
    items = [strip_eids(b) for b in (c.get("bullets") or []) if strip_eids(b)][:3]
    # Check for circle pair data
    vs = slide.get("visual_spec") or {}
    circle_data = vs.get("circle_data") or []
    cards = []
    for i, it in enumerate(items, 1):
        circle_html = ""
        col_label = f"Option {i}"
        if i <= len(circle_data) and isinstance(circle_data[i - 1], dict):
            cd = circle_data[i - 1]
            col_label = cd.get("label", col_label)
            circle_html = _circle_pair_svg(
                value_before=float(cd.get("value_before", 0)),
                value_after=float(cd.get("value_after", 0)),
                max_value=float(cd.get("max_value", 100)),
                unit=cd.get("unit", "%"),
                label="",
            )
        cards.append(
            f'<div class="comparison-col card">'
            f'<h3 class="col-label">{esc(col_label)}</h3>'
            f'{circle_html}'
            f'<p>{esc(it)}</p></div>'
        )
    while len(cards) < 3:
        cards.append(f'<div class="comparison-col card"><p>_(empty)_</p></div>')
    main = (
        f'<div class="gl-grid gl-grid-3 layout-three-col">'
        f'{"".join(cards)}'
        f'</div>'
        f'{insight_strip(_so_what(slide))}'
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="three_column_comparison",
        active=active,
        item_count=len(items),
    )


def render_horizontal_process(slide, total, notes, active=False):
    """Horizontal process flow with SVG arrow connectors between grid steps."""
    c = _content(slide)
    steps = [strip_eids(b) for b in (c.get("bullets") or []) if strip_eids(b)][:5]
    items = []
    arrows = []
    n = len(steps)
    for i, s in enumerate(steps, 1):
        items.append(
            f'<div class="process-step card">'
            f'<div class="step-num">{i}</div>'
            f'<div class="step-text">{esc(s)}</div></div>'
        )
        if i < n:
            arrows.append(
                f'<div class="process-arrow">'
                f'<svg viewBox="0 0 24 24" width="24" height="24">'
                f'<path d="M5 12h14M12 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2"/>'
                f'</svg></div>'
            )
    # Interleave steps and arrows
    interleaved = []
    for i, item in enumerate(items):
        interleaved.append(item)
        if i < len(arrows):
            interleaved.append(arrows[i])
    main = (
        f'<div class="gl-grid gl-grid-auto layout-horizontal-process" '
        f'style="--step-count:{n}">'
        f'{"".join(interleaved)}'
        f'</div>'
        f'{insight_strip(_so_what(slide))}'
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="horizontal_process",
        active=active,
        item_count=n,
    )


# ---------------------------------------------------------------------------
# Wave 4a — Diagram layouts (Tree, Hierarchy, Ecosystem)
# ---------------------------------------------------------------------------

def render_decision_tree(slide, total, notes, active=False):
    """Decision tree with diamond decision nodes and elbow connectors."""
    from ..diagram.builder import decision_tree_scene

    main = f'<div class="gl-areas-diagram layout-decision-tree">{decision_tree_scene(slide)}</div>'
    main += insight_strip(_so_what(slide))
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="decision_tree",
        active=active,
        item_count=3,
    )


def render_hierarchy_tree(slide, total, notes, active=False):
    """Parent-child hierarchy using nested group boundaries."""
    from ..diagram.builder import hierarchy_tree_scene

    main = f'<div class="gl-areas-diagram layout-hierarchy-tree">{hierarchy_tree_scene(slide)}</div>'
    main += insight_strip(_so_what(slide))
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="hierarchy_tree",
        active=active,
        item_count=3,
    )


def render_ecosystem_map(slide, total, notes, active=False):
    """Stakeholder web with nodes and labeled connections."""
    from ..diagram.builder import ecosystem_map_scene

    main = f'<div class="gl-areas-diagram layout-ecosystem-map">{ecosystem_map_scene(slide)}</div>'
    main += insight_strip(_so_what(slide))
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="ecosystem_map",
        active=active,
        item_count=4,
    )


# ---------------------------------------------------------------------------
# Wave 4b — Process, Deep Dive & Circular layouts
# ---------------------------------------------------------------------------

def render_process_with_decisions(slide, total, notes, active=False):
    """Linear process with diamond decision nodes inserted between steps."""
    c = _content(slide)
    steps = [strip_eids(b) for b in (c.get("steps") or c.get("bullets") or []) if strip_eids(b)][:6]
    decisions = [strip_eids(b) for b in (c.get("decisions") or []) if strip_eids(b)][:3]
    items = []
    for i, s in enumerate(steps, 1):
        items.append(
            f'<div class="process-step card">'
            f'<div class="step-num">{i}</div>'
            f'<div class="step-text">{esc(s)}</div></div>'
        )
        if i <= len(decisions):
            items.append(
                f'<div class="decision-node card">'
                f'<div class="decision-diamond">◊</div>'
                f'<div class="decision-label">{esc(decisions[i - 1])}</div></div>'
            )
    n = len(steps)
    main = (
        f'<div class="gl-grid gl-grid-auto layout-process-decisions">'
        f'{"".join(items)}'
        f'</div>'
        f'{insight_strip(_so_what(slide))}'
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="process_with_decisions",
        active=active,
        item_count=n + len(decisions),
    )


def render_source_deep_dive(slide, total, notes, active=False):
    """Dense appendix grid for evidence sources."""
    c = _content(slide)
    sources = []
    for item in (slide.get("evidence_sources") or []):
        if isinstance(item, dict):
            label = strip_eids(item.get("source_file") or item.get("file") or item.get("id") or "")
            summary = strip_eids(item.get("summary") or item.get("body") or "")
            eid = strip_eids(item.get("evidence_id") or "")
        elif isinstance(item, str):
            label = strip_eids(item)
            summary, eid = "", ""
        else:
            continue
        if label:
            sources.append({"label": label, "summary": summary, "eid": eid})
    if not sources:
        bullets = [strip_eids(b) for b in (c.get("bullets") or []) if strip_eids(b)]
        sources = [{"label": b, "summary": "", "eid": ""} for b in bullets]
    cards = []
    for s in sources[:8]:
        eid_html = f'<div class="source-eid">{esc(s["eid"])}</div>' if s["eid"] else ""
        sum_html = f'<p>{esc(s["summary"])}</p>' if s["summary"] else ""
        cards.append(
            f'<div class="source-card card">'
            f'<h4 class="source-label">{esc(s["label"])}</h4>'
            f'{sum_html}{eid_html}</div>'
        )
    n = len(cards)
    cols = "gl-grid-4" if n >= 4 else f"gl-grid-{max(n, 1)}"
    if n == 1:
        cols = "gl-grid"
    main = (
        f'<div class="gl-grid {cols} layout-source-deep-dive">'
        f'{"".join(cards)}'
        f'</div>'
        f'{insight_strip(_so_what(slide))}'
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="source_deep_dive",
        active=active,
        item_count=n,
    )


def render_circular_process(slide, total, notes, active=False):
    """Circular improvement loop with curved arrows between nodes."""
    from ..diagram.builder import causal_loop_scene

    main = f'<div class="gl-areas-diagram layout-circular-process">{causal_loop_scene(slide)}</div>'
    main += insight_strip(_so_what(slide))
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="circular_process",
        active=active,
        item_count=4,
    )

