"""Comparison, split, before/after layout recipes."""
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

from .shared import _bullets_html, _circle_pair_svg, _content, _fact_html, _proof_html, _so_what, _source_names, _table_inset, _table_matrix, argument_kicker, pair_comparison, right_panel_model
from .metrics import render_metric



def render_pill_comparison(slide, total, notes, active=False):
    """Freestanding pill statement columns (#74/F4, grown in #91/F4+).

    Exterior row-label rail + one fully separated rounded column *shell* per
    data column (Q1'26 / Q1'25 / YoY) — the IR statement house style, not
    pill headers over a spreadsheet body. Shells are white paper with
    full-width navy header caps; the last column keeps YoY emphasis via
    bold navy cells. Composes with the key_stats inset gutter (#73/T12).
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
    inset = _table_inset(_sv_content(slide).get("key_stats") or [])
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



def render_before_after(slide, total, notes, active=False):
    """Side-by-side before/after comparison using diagram primitives."""
    from ...diagram.builder import before_after_scene

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
