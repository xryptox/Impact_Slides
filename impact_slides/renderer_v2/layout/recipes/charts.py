"""Chart, dual-chart, icon-grid, multi-panel recipes."""
from __future__ import annotations

import re
import sys
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

from .shared import _content, _hero_stack, _so_what, _source_names, _visual_series_names, _vs_steps
from .metrics import render_metric
from ...charts.typography import chart_pane_title_html

# #136: Chart.js runtime re-pitch for plot-aligned support tables. Emitted
# inline only next to an aligned table (byte-inert when absent — #138 lesson).
# Static SVG contract attrs stay; this no-ops when Chart.js is not on the page.
_CHART_TABLE_ALIGN_JS = """
<script data-rv2-chart-table-align="1">
(function () {
  if (window.__rv2ChartTableAlignInstalled) return;
  window.__rv2ChartTableAlignInstalled = 1;
  function pageX(canvas, chart, tickX) {
    var r = canvas.getBoundingClientRect();
    var k = r.width / (chart.width || r.width || 1);
    return r.left + tickX * k;
  }
  function alignOne(wrap) {
    var col = wrap.closest('.chart-col');
    if (!col) return;
    var colR = col.getBoundingClientRect();
    if (!colR.width) return;
    var canvas = col.querySelector('canvas');
    if (!canvas || typeof Chart === 'undefined' || !Chart.getChart) return;
    var chart = Chart.getChart(canvas);
    if (!chart || !chart.scales || !chart.scales.x) return;
    var xScale = chart.scales.x;
    var isOutlined = wrap.classList.contains('chart-support-outlined');
    var n;
    if (isOutlined) {
      n = wrap.querySelectorAll('.chart-outlined-cell').length;
    } else {
      var cols = wrap.querySelectorAll('colgroup col');
      n = cols.length ? cols.length - 1 : 0;
    }
    if (n < 1) return;
    var ticks = [];
    for (var i = 0; i < n; i++) {
      var tx = (typeof xScale.getPixelForTick === 'function')
        ? xScale.getPixelForTick(i)
        : xScale.getPixelForValue(i);
      if (typeof tx !== 'number' || !isFinite(tx)) return;
      ticks.push(pageX(canvas, chart, tx));
    }
    var first = ticks[0], last = ticks[n - 1];
    var pitch = n === 1 ? (colR.width / 2) : (last - first) / (n - 1);
    if (!(pitch > 0)) return;
    var leftEdge = first - pitch / 2;
    var rightEdge = last + pitch / 2;
    var labelW = Math.max(0, leftEdge - colR.left);
    var wrapW = Math.max(pitch, rightEdge - colR.left);
    if (n > 1) wrapW = labelW + pitch * n;
    if (!(wrapW > 0)) return;
    wrap.style.width = (wrapW / colR.width * 100).toFixed(4) + '%';
    if (isOutlined) {
      var lab = wrap.querySelector('.chart-outlined-label');
      if (lab) {
        lab.style.flex = 'none';
        lab.style.width = (labelW / wrapW * 100).toFixed(4) + '%';
      }
      var cells = wrap.querySelectorAll('.chart-outlined-cell');
      var cw = (pitch / wrapW * 100).toFixed(4) + '%';
      for (var c = 0; c < cells.length; c++) {
        cells[c].style.flex = 'none';
        cells[c].style.width = cw;
      }
    } else {
      var cg = wrap.querySelectorAll('colgroup col');
      if (cg.length >= n + 1) {
        cg[0].style.width = (labelW / wrapW * 100).toFixed(4) + '%';
        var tw = (pitch / wrapW * 100).toFixed(4) + '%';
        for (var j = 1; j <= n; j++) cg[j].style.width = tw;
      }
    }
  }
  function alignAll() {
    var list = document.querySelectorAll('.chart-table-aligned');
    for (var i = 0; i < list.length; i++) alignOne(list[i]);
  }
  function boot() {
    alignAll();
    var n = 0;
    var t = setInterval(function () {
      alignAll();
      if (++n > 60) clearInterval(t);
    }, 50);
  }
  if (document.readyState === 'complete') boot();
  else window.addEventListener('load', boot);
  window.addEventListener('resize', alignAll);
  try {
    var mo = new MutationObserver(function () { alignAll(); });
    mo.observe(document.documentElement, {
      subtree: true, attributes: true, attributeFilter: ['class']
    });
  } catch (e) {}
})();
</script>
"""


def render_chart(slide, total, notes, active=False, *, use_chartjs: bool = False):
    from ...charts import build_chart_html, is_chart_layout

    layout = (slide.get("layout_type") or "grouped_bar_chart").lower()
    vs = slide.get("visual_spec") or {}
    pv = vs.get("primary_visual") or {}
    # R5-F/T11: on a single-series full-slide chart the slide title is the
    # heading, so a lone Chart.js legend swatch only restates it (the PDF
    # draws no swatch on single-series charts). Multi-series charts and
    # combo overlays keep their legend.
    if (
        isinstance(pv, Mapping)
        and len(_visual_series_names(pv)) == 1
        and not (vs.get("line_overlay") or pv.get("line_overlay"))
    ):
        slide = {
            **slide,
            "visual_spec": {
                **vs,
                "chart_config": {**(vs.get("chart_config") or {}), "show_legend": False},
            },
        }
        vs = slide["visual_spec"]
    chart_html = build_chart_html(slide, layout, use_chartjs=use_chartjs)
    secondary = vs.get("secondary_visual") or {}
    key_stats = _sv_content(slide).get("key_stats") or []

    # #100/N1: under-chart tables attach to any chart layout, not just
    # line_chart (PDF provision boards pair stacked bars with a reserve-rate
    # row). The plot-alignment path still only engages for label-matched
    # tables (see below).
    has_table = bool(secondary) and is_chart_layout(layout)
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
        from ...charts import chart_column_interval

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
            # Category labels from either supported primary form (#136):
            # mapping points use label/x; row-list data skips the header row
            # and takes the first cell of each data row.
            if raw_steps and all(isinstance(p, Mapping) for p in raw_steps):
                labels = [
                    str(p.get("label") or p.get("x") or "").strip()
                    for p in raw_steps
                ]
            elif (
                len(raw_steps) > 1
                and all(isinstance(p, (list, tuple)) and len(p) > 0 for p in raw_steps)
            ):
                labels = [str(r[0]).strip() for r in raw_steps[1:]]
            else:
                labels = []
            n = len(labels)
            aligned = (
                n > 0
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

            # N6: opt-in outlined-box skin (PDF provision boards: gray-stroked,
            # unfilled reserve-rate cells under each period column, period labels
            # already on the chart axis so the header row is dropped).
            # Declarative via secondary_visual.skin; absent -> today's table.
            skin = str(secondary.get("skin") or "").strip()
            if skin == "outlined_boxes":
                cells_html = ""
                for row in body:
                    for ci, c in enumerate(row):
                        cls_name = "chart-outlined-label" if ci == 0 else "chart-outlined-cell"
                        # outer slot carries the pitch-matched alignment width;
                        # the visible stroked box sits inside (PDF p15: cells
                        # are ~40% of the column pitch, centered, separated).
                        if aligned:
                            pct = label_w if ci == 0 else col_w
                            cells_html += (
                                f'<div class="{cls_name}" style="width:{pct:.2f}%">'
                                f'<span class="chart-outlined-box">{esc(c)}</span></div>'
                            )
                        else:
                            cells_html += (
                                f'<div class="{cls_name}">'
                                f'<span class="chart-outlined-box">{esc(c)}</span></div>'
                            )
                box_cls = "chart-support-outlined" + (" chart-table-aligned" if aligned else "")
                box_style = f' style="width:{table_w:.2f}%"' if aligned else ""
                tbl = f'<div class="{box_cls}"{box_style}{align_attrs}>{cells_html}</div>'
            else:
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
            # #136: Chart.js runtime re-pitch only when this table is aligned.
            align_js = _CHART_TABLE_ALIGN_JS if aligned else ""
            cls = " ".join(wrap_classes + (["chart-align-table"] if aligned else []))
            main = (
                f'<div class="chart-svg-wrap {cls}">'
                f'<div class="chart-col">{chart_html}{tbl}{align_js}</div></div>'
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
    from ...charts import _chart_config  # late import: charts -> layout cycle

    # chart_config normatively lives at visual_spec.primary_visual (#71/F15)
    cfg = _chart_config(slide)
    frame_cls = "chart-frame gl-card"
    frame_style = 'style="padding:18px 22px"'
    if cfg.get("surface") == "white":
        frame_cls += " chart-surface-white"
    if cfg.get("stage") == "flat":
        # R1 finish: stage=flat must flatten the FRAME card too — the wrap
        # alone left the gray Boardroom pad/shadow around the chart, while
        # the PDF sits the chart directly on the white canvas.
        frame_cls += " chart-frame-flat"
        frame_style = ""
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=f'<div class="{frame_cls}" {frame_style}>{main}</div>',
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class=layout,
        active=active,
        item_count=3,
    )



def render_dual_chart(slide, total, notes, active=False, *, use_chartjs: bool = False):
    """Two charts side by side (PDF p17: bar chart left, line chart right).

    visual_spec.primary_visual and visual_spec.secondary_visual each carry
    their own ``type`` + ``steps_or_data`` + optional per-pane ``label`` /
    ``chart_config`` / ``line_overlay``. Each pane is built through the
    standard chart pipeline; pane ``label`` (else single series name) renders
    as ``gl-tile-label``, and a redundant single-series legend is suppressed.
    """
    from ...charts import build_chart_html

    vs = slide.get("visual_spec") or {}
    from ...charts import _chart_config  # late import: charts -> layout cycle

    top_cfg = _chart_config(slide)
    panes: list[str] = []
    for key in ("primary_visual", "secondary_visual"):
        visual = vs.get(key)
        if not isinstance(visual, dict) or not visual:
            continue
        vt = str(visual.get("type") or "grouped_bar_chart").lower()
        # Pane heading (R5-F/T11): the PDF draws each pane's title as a
        # heading inside the card, above the plot. Source it from an
        # explicit per-pane ``label`` when authored, else from the pane's
        # single series name. Multi-series panes keep their Chart.js
        # legend (it distinguishes series — information, not chrome); a
        # single-series legend only restates the heading, so suppress it.
        names = _visual_series_names(visual)
        pane_cfg = dict(visual.get("chart_config") or {})
        # #139: recipe label wins; chart_config.title is fallback; single
        # series name last. One HTML-owned title — never duplicate internals.
        heading = strip_eids(str(visual.get("label") or ""))
        if not heading:
            heading = strip_eids(str(pane_cfg.get("title") or ""))
        if not heading and len(names) == 1:
            heading = names[0]
        if heading and len(names) <= 1 and not visual.get("line_overlay"):
            pane_cfg["show_legend"] = False
        sub_vs: dict[str, Any] = {
            "primary_visual": visual,
            "chart_config": pane_cfg,
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
        # #139: HTML-owned chart pane title (recipe heading wins).
        lbl = chart_pane_title_html(heading) if heading else ""
        # N10: each pane is its own rounded card (the PDF draws two separate
        # panels, not one shared enclosure). surface/stage modifiers apply
        # per pane, falling back to the slide-level chart_config.
        pane_cls = "dual-chart-pane chart-frame gl-card"
        if pane_cfg.get("surface", top_cfg.get("surface")) == "white":
            pane_cls += " chart-surface-white"
        if pane_cfg.get("stage", top_cfg.get("stage")) == "flat":
            pane_cls += " chart-frame-flat"
        panes.append(
            f'<div class="{pane_cls}">'
            f"{lbl}{build_chart_html(sub_slide, vt, use_chartjs=use_chartjs)}</div>"
        )
    main = f'<div class="gl-grid gl-grid-2 dual-chart">{"".join(panes)}</div>'
    main += insight_strip(_so_what(slide))
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="dual_chart",
        active=active,
        item_count=3,
    )



def render_chart_hero_dual(slide, total, notes, active=False, *, use_chartjs: bool = False):
    """Left chart card + right giant-% hero stack as peer cards (#75/F5).

    Hosts a Chart.js chart (charts feature) on the left and large hero-KPI
    callouts (from content.key_stats) on the right — the IR acquisitions
    pattern. Falls back to the SVG painter when charts are suppressed.
    """
    from ...charts import build_chart_html

    vs = slide.get("visual_spec") or {}
    pv = vs.get("primary_visual") or {}
    chart_html = ""
    if isinstance(pv, dict) and pv.get("type"):
        chart_html = build_chart_html(slide, str(pv.get("type")), use_chartjs=use_chartjs)
    hero = _hero_stack(_sv_content(slide).get("key_stats") or [])
    if not chart_html and not hero:
        return render_metric(slide, total, notes, active=active)
    # R4 (v8): the PDF chart panel carries an in-card title. Source it from an
    # explicit primary_visual label when authored (T11 convention); absent a
    # label nothing renders, so decks without one are unchanged.
    chart_title = ""
    if isinstance(pv, dict):
        chart_title = strip_eids(str(pv.get("label") or ""))
        if not chart_title:
            pv_cfg = pv.get("chart_config") if isinstance(pv.get("chart_config"), dict) else {}
            chart_title = strip_eids(str(pv_cfg.get("title") or ""))
    title_html = chart_pane_title_html(chart_title) if chart_title else ""
    main = (
        f'<div class="gl-areas-chart-hero">'
        f'<div class="gl-chart-hero-chart">{title_html}{chart_html or "<div class=\"chart-empty\">No chart</div>"}</div>'
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



def render_icon_grid(slide, total, notes, active=False):
    from ...charts import build_icon_grid_html

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



def render_multi_panel(slide, total, notes, active=False, *, use_chartjs: bool = False):
    """Multi-region / multi-chart board host (#80/F11). Renders each tile in
    visual_spec.primary_visual.tiles as a gl-* region: chart tiles embed a
    Chart.js chart (canonical path, reusing build_chart_html) beside metric
    tiles. Builds on the chart-embedding pattern proven by chart_hero_dual.
    """
    from ...charts import build_chart_html
    from ...charts.callouts import side_callout_active

    vs = slide.get("visual_spec") or {}
    pv = vs.get("primary_visual") or {}
    tiles = pv.get("tiles") if isinstance(pv, dict) else None
    if not isinstance(tiles, list) or not tiles:
        return render_metric(slide, total, notes, active=active)
    tile_count = sum(isinstance(tile, dict) for tile in tiles)
    cols = 2 if tile_count <= 4 else 3
    tile_width = (1920 - 2 * 96 - (cols - 1) * 18) / cols - 2 * 17
    parts = []
    for tile in tiles:
        if not isinstance(tile, dict):
            continue
        kind = str(tile.get("kind") or "metric")
        label = strip_eids(tile.get("label") or "")
        if kind == "chart":
            from ...charts.callouts import _build_side_callout_html

            chart_type = str(tile.get("chart_type") or "grouped_bar_chart")
            tile_cfg = tile.get("chart_config") or {}
            if not isinstance(tile_cfg, dict):
                tile_cfg = {}
            legend = tile.get("side_legend")
            has_side_legend = isinstance(legend, list) and bool(legend)
            # #138: host side_callout on the tile (PDF tile-local top 49.8px),
            # not the chart wrap whose top sits ~72px lower after totals/label.
            callout_requested = "side_callout" in tile_cfg
            callout_valid = side_callout_active(
                tile_cfg, chart_type, available_width=tile_width, warn=True
            )
            callout_on_tile = callout_valid
            if callout_on_tile and has_side_legend:
                print(
                    "[side_callout] omitted: tile side_legend occupies the exterior-name lane",
                    file=sys.stderr,
                )
                callout_on_tile = False
            paint_cfg = (
                {**tile_cfg, "_side_callout_external": True}
                if callout_on_tile
                else {k: v for k, v in tile_cfg.items() if k != "side_callout"}
                if callout_requested and callout_valid
                else tile_cfg
            )
            sub_slide = {
                **slide,
                "layout_type": chart_type,
                "visual_spec": {
                    "primary_visual": {
                        "type": chart_type,
                        "steps_or_data": tile.get("steps_or_data") or [],
                        "chart_config": paint_cfg,
                    }
                },
            }
            chart_html = build_chart_html(
                sub_slide, sub_slide["layout_type"], use_chartjs=use_chartjs
            )
            tile_skin = str(tile.get("tile_skin") or "").lower()
            tile_pad = 0 if tile_skin == "ir" else 16
            side_html = (
                _build_side_callout_html(
                    tile_cfg,
                    chart_type,
                    host="tile",
                    tile_pad_px=tile_pad,
                    available_width=tile_width,
                    warn=False,
                )
                if callout_requested and not has_side_legend
                else ""
            )
            # #139: chart tile heading uses shared pane-title class; metric
            # tiles below keep ordinary gl-tile-label.
            lbl = chart_pane_title_html(label) if label else ""
            # IR dual tall-card slots (#90/F11+): freestanding top total,
            # exterior side legend, badge callout. Only engaged when present,
            # so legacy tiles keep their existing chrome.
            top_total = strip_eids(tile.get("top_total") or "")
            # #138: side_callout supersedes the pill badge chrome on the same
            # tile, but the tile keeps its existing tall-card geometry.
            badge_text = strip_eids(tile.get("badge") or "")
            badge = "" if callout_on_tile else badge_text
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
            if top_total or badge or legend_html or badge_text:
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
                if tile_skin == "ir":
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
                        f"{badge_html}{side_html}{body}"
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
                        f"{badge_html}{side_html}{total_html}{lbl}{body}"
                        f"</div>"
                    )
            else:
                tile_style = ' style="position:relative"' if callout_on_tile else ""
                parts.append(
                    f'<div class="gl-tile gl-tile-chart"{tile_style}>{side_html}{lbl}{chart_html}</div>'
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
        item_count=len(parts),
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
