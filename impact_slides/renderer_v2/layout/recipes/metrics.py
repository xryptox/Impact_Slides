"""Metric/table/KPI/IR layout recipes."""
from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from ...slide_view import content as _sv_content
from ...slide_view import primary_visual as _sv_primary_visual
from ...slide_view import steps as _sv_steps
from ...charts.typography import _RENDER_STRICT, _warn
from ...strip import (
    banned_face_opener,
    chosen_dek,
    clean_quote_body,
    esc,
    parse_cite_from_quote,
    strip_eids,
)
from ..regions import gl_card, insight_strip, notes_aside, slide_shell, source_strip

from .shared import _content, _kpi_cards, _so_what, _source_names, _stat_label_value, _table_inset, _table_matrix, table_as_kpi



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
        layout_class="data_table",
        active=active,
        item_count=len(body),
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



# Fixed-stage content width and per-block readability floor. This mirrors the
# existing deterministic chart-host checks: handoffs have no runtime viewport.
GROUPED_ANNEX_HOST_WIDTH = 1728
GROUPED_ANNEX_READABLE_BLOCK_WIDTH = 560
_GROUPED_ANNEX_STYLE = """
<style data-grouped-annex="1">
.gl-grouped-annex { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:var(--gap-md); align-items:start; }
.gl-grouped-annex-1col { grid-template-columns:1fr; }
.gl-grouped-annex-block { min-width:0; }
.gl-grouped-annex-heading { margin:0 0 var(--space-2); color:var(--navy); font-family:var(--font-display); font-size:var(--fs-pill); font-weight:700; line-height:1.15; }
.gl-grouped-annex .table-frame { max-width:none; }
.gl-grouped-annex .annex-table .gl-annex-stub { width:52%; }
.gl-grouped-annex .annex-table th, .gl-grouped-annex .annex-table td { white-space:normal; }
.gl-grouped-annex .gl-annex-row-aggregate .gl-annex-stub { font-weight:700; }
.gl-grouped-annex .gl-annex-indent-1 { padding-left:var(--size-4); }
.gl-grouped-annex .gl-annex-indent-2 { padding-left:var(--size-6); }
.gl-grouped-annex .gl-annex-indent-3 { padding-left:var(--size-8); }
</style>
"""


def _annex_table_html(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    *,
    header_groups: Sequence[Mapping[str, Any]] | None = None,
    labelled_by: str | None = None,
    row_styles: Sequence[tuple[str, int]] | None = None,
    scoped_headers: bool = False,
) -> str:
    """Render the shared annex table surface used by ordinary and grouped blocks."""
    if header_groups:
        top_cells = ['<th class="gl-annex-stub" rowspan="2"></th>']
        for group in header_groups:
            # R5-H/T13: no index-parity banding — the PDF annex band is
            # uniformly navy; gl-annex-group-alt stays available for a
            # future semantic banding handoff, not column parity.
            top_cells.append(
                f'<th class="gl-annex-group" colspan="{int(group.get("span") or 1)}">'
                f'{esc(strip_eids(group.get("label") or ""))}</th>'
            )
        thead = "<tr>" + "".join(top_cells) + "</tr>"
        thead += "<tr>" + "".join(
            f'<th class="gl-annex-head">{esc(header)}</th>' for header in headers[1:]
        ) + "</tr>"
    else:
        scope = ' scope="col"' if scoped_headers else ""
        thead = "<tr>" + "".join(
            f'<th{scope} class="{"gl-annex-stub" if column == 0 else "gl-annex-head"}">{esc(header)}</th>'
            for column, header in enumerate(headers)
        ) + "</tr>"

    trs = []
    for row_index, row in enumerate(rows):
        style = row_styles[row_index] if row_styles else None
        role, indent = style if style else (None, 0)
        tds = []
        for column, cell in enumerate(row):
            if column == 0:
                cls = "gl-annex-stub" + (f" gl-annex-indent-{indent}" if style else "")
            else:
                cls = "gl-annex-cell num" if re.search(r"[\d$%]", cell or "") else "gl-annex-cell"
            tds.append(f'<td class="{cls}">{esc(cell)}</td>')
        while len(tds) < len(headers):
            tds.append('<td class="gl-annex-cell"></td>')
        row_class = f' class="gl-annex-row gl-annex-row-{esc(role)}"' if style else ""
        trs.append(f"<tr{row_class}>{''.join(tds)}</tr>")

    aria = f' aria-labelledby="{labelled_by}"' if labelled_by else ""
    return (
        f'<div class="gl-annex table-frame gl-card gl-annex-micro">'
        f'<table class="data-table annex-table"{aria}><thead>{thead}</thead>'
        f'<tbody>{"".join(trs)}</tbody></table></div>'
    )


def _grouped_annex_table(group: Mapping[str, Any], index: int) -> str:
    heading = strip_eids(group.get("heading") or "")
    rows = group.get("rows") or []
    heading_id = f"gl-grouped-annex-heading-{index}"
    table = _annex_table_html(
        group.get("headers") or [],
        [row.get("cells") or [] for row in rows],
        labelled_by=heading_id,
        row_styles=[(row.get("role") or "child", int(row.get("indent") or 0)) for row in rows],
        scoped_headers=True,
    )
    return (
        f'<section class="gl-grouped-annex-block">'
        f'<h3 class="gl-grouped-annex-heading" id="{heading_id}">{esc(heading)}</h3>'
        f"{table}</section>"
    )


def render_grouped_annex_table(slide, total, notes, active=False):
    """Render one or two peer annex matrices without flattening their identity."""
    groups = _sv_primary_visual(slide).get("groups")
    groups = groups if isinstance(groups, list) else []
    group_count = len(groups)
    required_width = GROUPED_ANNEX_READABLE_BLOCK_WIDTH * group_count
    stacked = group_count > 1 and GROUPED_ANNEX_HOST_WIDTH < required_width
    if stacked:
        msg = "grouped annex blocks cannot fit side by side at the annex readability floor"
        if _RENDER_STRICT.get():
            raise ValueError(msg)
        _warn(msg)
    blocks = "".join(_grouped_annex_table(group, i) for i, group in enumerate(groups))
    main = (
        f'{_GROUPED_ANNEX_STYLE}<div class="gl-grouped-annex gl-grouped-annex-{1 if stacked else group_count}col">'
        f'{blocks}</div>' + insight_strip(_so_what(slide))
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="grouped_annex_table",
        active=active,
        item_count=sum(len(group.get("rows") or []) for group in groups),
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
    pv = _sv_primary_visual(slide)
    header_groups = pv.get("header_groups") if isinstance(pv, dict) else None
    table = _annex_table_html(head, body, header_groups=header_groups)
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



def render_ir_bullet_sheet(slide, total, notes, active=False):
    """Centered title + full-width single-column bullet sheet with selective
    inline bold (#77/F7). Bullet text passes through rich_text (escape +
    ``**bold**``); unsafe markup is escaped (semi-trusted, fail closed).
    """
    from ...rich_text import rich_bullets

    bullets = rich_bullets(_sv_content(slide).get("bullets") or [])
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
    c = _sv_content(slide)
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
