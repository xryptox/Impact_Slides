"""Transactional D250 artifact publication (D112/D113/D250/D312)."""
from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .diagnostics import (
    DiagnosticEvent,
    RendererPublicationError,
    event,
    sort_events,
)
from .models import Deck
from .plan import DeckPlan
from .schema_export import schema_path
from .theme import THEME_ID, generate_theme_css

from ._version import __version__ as RENDERER_VERSION

CANONICAL_ARTIFACTS = (
    "presentation.html",
    "slide_notes.md",
    "evidence_manifest.json",
    "run_meta.json",
    "handoff_schema_v1.json",
)

# Artifacts hashed inside run_meta (excludes run_meta itself).
_HASHED_ARTIFACTS = tuple(n for n in CANONICAL_ARTIFACTS if n != "run_meta.json")


def dumps_json(obj: Any) -> str:
    """UTF-8/LF JSON, two-space indent, trailing newline (D250/D312)."""
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _slide_heading(slide: Any, sections: list[Any] | None = None) -> str:
    title = getattr(slide, "title", None)
    if title:
        return title
    payload = getattr(slide, "payload", None)
    if payload is not None and getattr(payload, "title", None):
        return payload.title
    if slide.layout_type == "section_divider":
        # D269: accessibility/notes wording from registry label, not id token.
        sec_id = payload.section_id
        if sections:
            for sec in sections:
                if sec.section_id == sec_id:
                    return sec.label
        return sec_id
    if slide.layout_type == "legal_notice":
        if payload.part == 1 and payload.title:
            return payload.title
        return "— continued"
    return slide.layout_type


def build_presentation_html(
    deck: Deck,
    *,
    debug: bool = False,
    svg_only: bool = False,
    deck_plan: DeckPlan | None = None,
    events: list[DiagnosticEvent] | None = None,
) -> str:
    """Minimal deterministic HTML shell for kernel compositions (paint later)."""
    plans_by_id = deck_plan.by_surface_id() if deck_plan is not None else {}
    events_by_surface = _events_by_surface(events or [])
    font_dir = Path(__file__).with_name("assets") / "fonts"
    source_sans = base64.b64encode((font_dir / "source-sans-3-latin.woff2").read_bytes()).decode("ascii")
    ibm_plex = base64.b64encode((font_dir / "ibm-plex-sans-latin.woff2").read_bytes()).decode("ascii")
    parts: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8"/>',
        f"<title>{_escape(_slide_heading(deck.slides[0], deck.sections))}</title>",
        f'<meta name="generator" content="impact_slides.renderer_v3/{RENDERER_VERSION}"/>',
        f'<meta name="theme-id" content="{THEME_ID}"/>',
        f'<meta name="design-stage" content="{1920}x{1080}"/>',
    ]
    if debug:
        parts.append('<meta name="renderer-debug" content="1"/>')
    if svg_only:
        parts.append('<meta name="svg-only" content="1"/>')
    parts.extend(
        [
            "<style>",
            f"@font-face{{font-family:'Source Sans 3';src:url(data:font/woff2;base64,{source_sans}) format('woff2');font-weight:200 900;font-style:normal}}",
            f"@font-face{{font-family:'IBM Plex Sans';src:url(data:font/woff2;base64,{ibm_plex}) format('woff2');font-weight:100 700;font-style:normal}}",
            generate_theme_css().rstrip("\n"),
            # Fixed 1920×1080 stage; viewport may scale the stage uniformly (D68).
            "html{width:100%;height:100%}",
            "body{margin:0;font-family:var(--font-body);background:var(--color-surface);color:var(--color-navy);overflow:auto}",
            ".deck-stage{width:1920px;transform-origin:top left}",
            ".slide{box-sizing:border-box;width:1920px;height:1080px;padding:var(--space-pad-top) var(--space-pad-x) var(--space-pad-bottom);transform-origin:top left;page-break-after:always}",
            "h1{font-size:var(--text-title);font-weight:var(--font-weight-title);margin:0 0 var(--space-sm)}",
            "h2{font-size:var(--text-insight);font-weight:var(--font-weight-title);margin:0 0 var(--space-sm)}",
            # Spacing constants must stay aligned with plan.BLOCK_MARGIN_Y.
            "p,ul{font-size:var(--text-body);line-height:1.4;margin:0 0 var(--space-sm);padding:0}",
            "li{margin:0;padding:0;margin-left:1.25em}",
            # Brand / divider / legal chrome (D223/D268/D269/D271) — renderer-owned.
            # Descendant selectors; frozen sizes still applied inline from plan role_sizes.
            ".cover{display:flex;flex-direction:column;justify-content:center;height:100%;gap:var(--space-sm)}",
            ".cover h1{font-size:var(--text-display);margin:0 0 var(--space-md)}",
            ".cover .subtitle,.cover .period,.cover .date{font-size:var(--text-body);margin:0}",
            ".cover-band{height:8px;background:var(--color-band);margin:0 0 var(--space-lg);flex:0 0 auto}",
            ".section-divider{display:flex;flex-direction:column;justify-content:center;height:100%}",
            ".section-divider .divider-meta{font-size:var(--text-body);letter-spacing:0.08em;text-transform:uppercase;margin:0 0 var(--space-sm);color:var(--color-primary-blue)}",
            ".section-divider h1{font-size:var(--text-title);margin:0}",
            ".section-divider .divider-rule{height:4px;width:120px;background:var(--color-band);margin:var(--space-md) 0 0}",
            ".legal-notice{height:100%;overflow:visible}",
            ".legal-notice h1,.legal-notice .legal-continued{margin:0 0 var(--space-md);font-weight:var(--font-weight-title)}",
            ".legal-notice .legal-body p{margin:0 0 var(--space-sm);white-space:pre-wrap}",
            ".legal-notice .legal-part{margin:var(--space-md) 0 0;color:var(--color-ink)}",
            ".legal-overflow,.cover-overflow,.divider-overflow{outline:var(--border-width-hairline) dashed var(--color-warning)}",
            ".takeaway{background:var(--color-panel);border:var(--border-width-hairline) solid var(--color-panel-border);padding:var(--space-sm) var(--space-md);margin-top:var(--space-md)}",
            ".takeaway-label{font-size:var(--text-xs);font-weight:var(--font-weight-emphasis);margin:0 0 var(--space-xs)}",
            # D173: notes stay off the visible slide; HTML/notes artifact stay exact.
            ".notes{display:none;white-space:pre-wrap}",
            ".disclosures summary{padding-left:1.25em}",
            # data_table (D8/D42/D104/D105/D183/D257)
            # Pads must match plan.TABLE_CELL_PAD_* (8+8 x, 6+6 y).
            "table.data-table{width:100%;border-collapse:collapse;table-layout:fixed;margin:0 0 var(--space-sm)}",
            "table.data-table th,table.data-table td{padding:6px 8px;border:var(--border-width-hairline) solid var(--color-rule);vertical-align:middle;font-weight:400}",
            "table.data-table thead th{background:var(--color-band);color:var(--color-band-ink);font-weight:var(--font-weight-emphasis)}",
            "table.data-table tbody td,table.data-table tbody th{background:transparent}",
            "table.data-table th.align-left,table.data-table td.align-left{text-align:left}",
            "table.data-table th.align-right,table.data-table td.align-right{text-align:right}",
            "table.data-table th.align-center,table.data-table td.align-center{text-align:center}",
            "table.data-table td.num,table.data-table th.num{font-variant-numeric:tabular-nums lining-nums}",
            "table.data-table th.stub,table.data-table td.stub{text-align:left;font-weight:var(--font-weight-emphasis)}",
            ".table-scale{font-size:var(--text-xs);margin:0 0 var(--space-sm);color:var(--color-navy)}",
            ".table-overflow{outline:var(--border-width-hairline) dashed var(--color-warning)}",
            "@media print{"
            "details:not([open])>summary~*{display:block}"
            "html,body{width:auto;height:auto;overflow:visible}"
            ".deck-stage{width:1920px!important;transform:none!important}"
            ".slide{width:1920px!important;height:1080px!important;transform:none!important;margin:0!important;page-break-after:always}"
            "}",
            "</style>",
            "</head>",
            "<body>",
            '<main class="deck-stage">',
        ]
    )
    for slide in deck.slides:
        sid = f"slide-{slide.slide_number}"
        slide_diag = _diag_attrs(events_by_surface.get(sid, []))
        parts.append(
            f'<section class="slide" id="{sid}" data-layout="{slide.layout_type}" '
            f'data-slide-number="{slide.slide_number}" '
            f'data-surface-id="{sid}" {slide_diag}>'
        )
        parts.extend(
            _paint_slide_body(
                slide,
                plans_by_id,
                events_by_surface,
                deck.evidence_registry,
                sections=deck.sections,
            )
        )
        notes = getattr(slide, "speaker_notes", None)
        if notes:
            parts.append(f'<aside class="notes">{_escape(notes)}</aside>')
        parts.append("</section>")
    parts.extend([
        "</main>",
        "<script>(()=>{const s=document.querySelector('.deck-stage'),a=[...s.children];const fit=()=>{const z=Math.min(innerWidth/1920,innerHeight/1080);s.style.width=`${1920*z}px`;a.forEach(x=>{x.style.transform=`scale(${z})`;x.style.marginBottom=`${1080*(z-1)}px`})};addEventListener('resize',fit);fit()})()</script>",
        "</body>",
        "</html>",
        "",
    ])
    return "\n".join(parts)


def _events_by_surface(
    events: list[DiagnosticEvent],
) -> dict[str, list[DiagnosticEvent]]:
    """Project plan/paint events onto surfaces by DiagnosticEvent.surface_id."""
    out: dict[str, list[DiagnosticEvent]] = {}
    for e in events:
        sid = e.surface_id
        if not sid:
            continue
        out.setdefault(sid, []).append(e)
    return out


def _diag_attrs(surface_events: list[DiagnosticEvent]) -> str:
    """Sorted unique diagnostic codes + true count for one surface (R178-004)."""
    codes = sorted({e.code for e in surface_events})
    return (
        f'data-diagnostic-codes="{_escape(",".join(codes))}" '
        f'data-diagnostic-count="{len(surface_events)}"'
    )


def _plan_attrs(
    sp: Any | None,
    events_by_surface: dict[str, list[DiagnosticEvent]] | None = None,
) -> str:
    """Compact D312 data-* diagnostics from a frozen surface plan."""
    events_by_surface = events_by_surface or {}
    if sp is None:
        return 'data-diagnostic-count="0"'
    sizes = ",".join(f"{k}:{sp.role_sizes[k]}" for k in sorted(sp.role_sizes))
    adap = ",".join(sp.adaptation_codes)
    diag = _diag_attrs(events_by_surface.get(sp.surface_id, []))
    bits = [
        f'data-surface-id="{_escape(sp.surface_id)}"',
        f'data-plan-sizes="{_escape(sizes)}"',
        f'data-plan-adaptations="{_escape(adap)}"',
        diag,
    ]
    return " ".join(bits)


def _style_font(px: int | None) -> str:
    if px is None:
        return ""
    return f' style="font-size:{px}px"'


def _paint_slide_body(
    slide: Any,
    plans_by_id: dict[str, Any],
    events_by_surface: dict[str, list[DiagnosticEvent]] | None = None,
    evidence_registry: dict[str, Any] | None = None,
    sections: list[Any] | None = None,
) -> list[str]:
    events_by_surface = events_by_surface or {}
    evidence_registry = evidence_registry or {}
    sections = sections or []
    lt = slide.layout_type
    out: list[str] = []
    sn = slide.slide_number
    if lt in ("opening_cover", "closing_cover"):
        p = slide.payload
        sp = plans_by_id.get(f"slide-{sn}-cover")
        title_px = sp.role_sizes.get("title") if sp else None
        sub_px = sp.role_sizes.get("subtitle") if sp else None
        meta_px = sp.role_sizes.get("meta") if sp else None
        overflow = " cover-overflow" if sp is not None and getattr(sp, "fallback", None) else ""
        out.append(
            f'<div class="cover{overflow}" {_plan_attrs(sp, events_by_surface)}>'  # one cover surface
        )
        out.append('<div class="cover-band" aria-hidden="true"></div>')
        out.append(f"<h1{_style_font(title_px)}>{_soft_break_html(p.title)}</h1>")
        if p.subtitle:
            out.append(
                f'<p class="subtitle"{_style_font(sub_px)}>{_soft_break_html(p.subtitle)}</p>'
            )
        if p.period_label:
            out.append(
                f'<p class="period"{_style_font(meta_px)}>{_soft_break_html(p.period_label)}</p>'
            )
        if p.date_label:
            out.append(
                f'<p class="date"{_style_font(meta_px)}>{_soft_break_html(p.date_label)}</p>'
            )
        out.append("</div>")
        return out
    if lt == "section_divider":
        sp = plans_by_id.get(f"slide-{sn}-divider")
        title_px = sp.role_sizes.get("title") if sp else None
        meta_px = sp.role_sizes.get("meta") if sp else None
        # Visible wording from D215 registry only — never authored override (D269).
        sec_id = slide.payload.section_id
        label = next((s.label for s in sections if s.section_id == sec_id), sec_id)
        ord_n = next(
            (i + 1 for i, s in enumerate(sections) if s.section_id == sec_id),
            1,
        )
        meta = f"Section {ord_n}"
        overflow = " divider-overflow" if sp is not None and getattr(sp, "fallback", None) else ""
        out.append(
            f'<div class="section-divider{overflow}" {_plan_attrs(sp, events_by_surface)} '
            f'data-section-id="{_escape(sec_id)}">'
        )
        out.append(
            f'<p class="divider-meta"{_style_font(meta_px)}>{_soft_break_html(meta)}</p>'
        )
        out.append(f"<h1{_style_font(title_px)}>{_soft_break_html(label)}</h1>")
        out.append('<div class="divider-rule" aria-hidden="true"></div>')
        out.append("</div>")
        return out
    if lt == "legal_notice":
        p = slide.payload
        sp = plans_by_id.get(f"slide-{sn}-legal")
        title_px = sp.role_sizes.get("title") if sp else None
        body_px = sp.role_sizes.get("body") if sp else None
        meta_px = sp.role_sizes.get("meta") if sp else None
        overflow = " legal-overflow" if sp is not None and getattr(sp, "fallback", None) else ""
        out.append(
            f'<div class="legal-notice{overflow}" {_plan_attrs(sp, events_by_surface)} '
            f'data-notice-id="{_escape(p.notice_id)}" data-part="{p.part}" '
            f'data-total-parts="{p.total_parts}">'
        )
        if p.part == 1:
            out.append(
                f"<h1{_style_font(title_px)}>{_soft_break_html(p.title or '')}</h1>"
            )
        else:
            # Renderer-owned continuation; no authored (cont.) title (D226/D271).
            out.append(
                f'<p class="legal-continued"{_style_font(title_px)} '
                f'aria-label="Part {p.part} of {p.total_parts}, continued">'
                f"{_soft_break_html('— continued')}</p>"
            )
        out.append('<div class="legal-body">')
        for para in p.paragraphs:
            # Exact paragraphs; only safe escaping + soft-break markers.
            out.append(f"<p{_style_font(body_px)}>{_soft_break_html(para)}</p>")
        out.append("</div>")
        # D271: visible part-of-total chrome is for continuation parts.
        if p.part > 1:
            out.append(
                f'<p class="legal-part"{_style_font(meta_px)}>'
                f"Part {p.part} of {p.total_parts}</p>"
            )
        out.append("</div>")
        return out
    if lt in ("narrative", "data_table"):
        title_sp = plans_by_id.get(f"slide-{sn}-title")
        title_px = title_sp.role_sizes.get("title") if title_sp else None
        out.append(
            f'<h1 {_plan_attrs(title_sp, events_by_surface)}{_style_font(title_px)}>{_soft_break_html(slide.title)}</h1>'
        )
        if slide.content is not None:
            sub_sp = plans_by_id.get(f"slide-{sn}-subtitle")
            sub_px = sub_sp.role_sizes.get("subtitle") if sub_sp else None
            out.append(
                f'<p class="subtitle" {_plan_attrs(sub_sp, events_by_surface)}{_style_font(sub_px)}>' 
                f"{_soft_break_html(slide.content.subtitle)}</p>"
            )
        if lt == "data_table":
            out.extend(_paint_data_table(slide, plans_by_id, events_by_surface))
        else:
            out.extend(_paint_narrative_blocks(slide, plans_by_id, events_by_surface))
        if slide.takeaway is not None:
            tsp = plans_by_id.get(f"slide-{sn}-takeaway")
            body_px = tsp.role_sizes.get("body") if tsp else None
            label_px = tsp.role_sizes.get("label") if tsp else None
            out.append(f'<aside class="takeaway" {_plan_attrs(tsp, events_by_surface)} role="note">')
            out.append(
                f'<p class="takeaway-label"{_style_font(label_px)}>Key takeaway</p>'
            )
            out.append(
                f'<p class="takeaway-text"{_style_font(body_px)}>' 
                f"{_soft_break_html(slide.takeaway.text)}</p>"
            )
            out.append("</aside>")
        if slide.disclosure is not None:
            out.append('<div class="disclosures">')
            for section in slide.disclosure.sections:
                dsp = plans_by_id.get(
                    f"slide-{sn}-disclosure-{section.surface_id}"
                )
                px = dsp.role_sizes.get("body") if dsp else None
                out.append(
                    f'<details id="slide-{sn}-{_escape(section.surface_id)}" '
                    f'{_plan_attrs(dsp, events_by_surface)}>'
                )
                out.append(
                    f"<summary{_style_font(px)}>{_soft_break_html(section.title)}</summary>"
                )
                in_list = False
                for item in section.items:
                    if item.kind == "bullet" and not in_list:
                        out.append(f"<ul{_style_font(px)}>")
                        in_list = True
                    elif item.kind == "paragraph" and in_list:
                        out.append("</ul>")
                        in_list = False
                    if item.kind == "bullet":
                        out.append(f"<li>{_soft_break_html(item.text)}</li>")
                    else:
                        out.append(f"<p{_style_font(px)}>{_soft_break_html(item.text)}</p>")
                if in_list:
                    out.append("</ul>")
                out.append("</details>")
            out.append("</div>")
        if slide.source_footer is not None:
            fsp = plans_by_id.get(f"slide-{sn}-source-footer")
            px = fsp.role_sizes.get("body") if fsp else None
            names = "; ".join(
                evidence_registry[eid].source_name for eid in slide.source_footer
            )
            out.append(
                f'<footer class="source-footer" {_plan_attrs(fsp, events_by_surface)}'
                f'{_style_font(px)}>Sources: {_soft_break_html(names)}</footer>'
            )
        return out
    out.append(f"<p>Unsupported layout in kernel paint: {_escape(lt)}</p>")
    return out


def _paint_narrative_blocks(
    slide: Any,
    plans_by_id: dict[str, Any],
    events_by_surface: dict[str, list[DiagnosticEvent]],
) -> list[str]:
    out: list[str] = []
    sn = slide.slide_number
    for block in slide.payload.blocks:
        bid = block.block_id
        surface_id = f"slide-{sn}-block-{bid}"
        bsp = plans_by_id.get(surface_id)
        body_px = bsp.role_sizes.get("body") if bsp else None
        attrs = _plan_attrs(bsp, events_by_surface)
        style = _style_font(body_px)
        if block.type == "paragraphs":
            out.append(
                f'<div class="paragraphs" data-block-id="{_escape(bid)}" {attrs}{style}>'
            )
            for prose in block.paragraphs:
                out.append(f"<p{style}>{_prose_html(prose)}</p>")
            out.append("</div>")
        elif block.type == "bullet_list":
            out.append(f'<ul data-block-id="{_escape(bid)}" {attrs}{style}>')
            for item in block.items:
                out.append(f"<li>{_prose_html(item)}</li>")
            out.append("</ul>")
    return out


def _paint_data_table(
    slide: Any,
    plans_by_id: dict[str, Any],
    events_by_surface: dict[str, list[DiagnosticEvent]],
) -> list[str]:
    """Paint one ordinary data_table from frozen plan (D69/D183/D255/D257)."""
    table = slide.payload.table
    sp = plans_by_id.get(table.surface_id)
    if sp is None or not getattr(sp, "table_paint", None):
        raise RuntimeError(
            f"missing frozen table_paint for surface {table.surface_id!r}"
        )
    paint = sp.table_paint
    px = sp.role_sizes.get("table")
    style = _style_font(px)
    out: list[str] = []
    attrs = _plan_attrs(sp, events_by_surface)
    overflow_cls = " table-overflow" if sp._overflow else ""

    headers = list(paint["display_headers"])
    row_labels = list(paint["display_row_labels"])
    full_headers = list(paint["header_full"])
    full_row_labels = list(paint["row_labels_full"])
    widths = list(paint.get("col_widths") or [])
    groups = paint.get("display_groups")
    col_ids = list(paint["col_ids"])
    col_aligns = list(paint.get("col_aligns") or ["right"] * len(col_ids))
    stub_hid = f"{table.surface_id}-h-stub"
    leaf_hids = [f"{table.surface_id}-h-{cid}" for cid in col_ids]
    group_hids: dict[str, str] = {}

    out.append(
        f'<table class="data-table{overflow_cls}" {attrs}{style} '
        f'data-table-surface="{_escape(table.surface_id)}">'
    )
    if widths:
        out.append("<colgroup>")
        for w in widths:
            out.append(f'<col style="width:{int(w)}px"/>')
        out.append("</colgroup>")
    out.append("<thead>")

    grouped_cols: set[str] = set()
    if groups:
        out.append("<tr>")
        out.append(
            f'<th id="{_escape(stub_hid)}" scope="col" rowspan="2" '
            f'class="band-table-header align-left stub" '
            f'title="{_escape(full_headers[0])}">{_soft_break_html(headers[0])}</th>'
        )
        covered: set[str] = set()
        i = 0
        while i < len(col_ids):
            cid = col_ids[i]
            if cid in covered:
                i += 1
                continue
            owner = next((g for g in groups if cid in g["column_ids"]), None)
            if owner is None:
                hid = leaf_hids[i]
                align = col_aligns[i]
                out.append(
                    f'<th id="{_escape(hid)}" scope="col" rowspan="2" '
                    f'class="band-table-header align-{align}" '
                    f'title="{_escape(full_headers[i + 1])}">'
                    f"{_soft_break_html(headers[i + 1])}</th>"
                )
                i += 1
                continue
            gid = owner["group_id"]
            ghid = f"{table.surface_id}-g-{gid}"
            group_hids[gid] = ghid
            for gc in owner["column_ids"]:
                covered.add(gc)
                grouped_cols.add(gc)
            out.append(
                f'<th id="{_escape(ghid)}" scope="colgroup" '
                f'colspan="{owner["colspan"]}" '
                f'class="band-table-header align-center" '
                f'title="{_escape(owner["label"])}">'
                f"{_soft_break_html(owner['display_label'])}</th>"
            )
            i += len(owner["column_ids"])
        out.append("</tr>")
        out.append("<tr>")
        for i, cid in enumerate(col_ids):
            if cid not in grouped_cols:
                continue
            hid = leaf_hids[i]
            align = col_aligns[i]
            out.append(
                f'<th id="{_escape(hid)}" scope="col" '
                f'class="band-table-header align-{align}" '
                f'title="{_escape(full_headers[i + 1])}">'
                f"{_soft_break_html(headers[i + 1])}</th>"
            )
        out.append("</tr>")
    else:
        out.append("<tr>")
        out.append(
            f'<th id="{_escape(stub_hid)}" scope="col" '
            f'class="band-table-header align-left stub" '
            f'title="{_escape(full_headers[0])}">{_soft_break_html(headers[0])}</th>'
        )
        for i, hid in enumerate(leaf_hids):
            align = col_aligns[i]
            out.append(
                f'<th id="{_escape(hid)}" scope="col" '
                f'class="band-table-header align-{align}" '
                f'title="{_escape(full_headers[i + 1])}">'
                f"{_soft_break_html(headers[i + 1])}</th>"
            )
        out.append("</tr>")
    out.append("</thead>")

    out.append("<tbody>")
    for r_i, row in enumerate(table.rows):
        out.append("<tr>")
        rid = f"{table.surface_id}-r-{row.row_id}"
        out.append(
            f'<th id="{_escape(rid)}" scope="row" class="stub align-left" '
            f'title="{_escape(full_row_labels[r_i])}">'
            f"{_soft_break_html(row_labels[r_i])}</th>"
        )
        for c_i, cid in enumerate(col_ids):
            visible = paint["cells_vis"][r_i][c_i]
            accessible = paint["cells_acc"][r_i][c_i]
            role = paint["cells_role"][r_i][c_i]
            align = paint["cells_align"][r_i][c_i]
            hrefs = [rid, leaf_hids[c_i]]
            if groups:
                owner = next((g for g in groups if cid in g["column_ids"]), None)
                if owner is not None:
                    ghid = group_hids.get(owner["group_id"]) or (
                        f"{table.surface_id}-g-{owner['group_id']}"
                    )
                    hrefs.insert(1, ghid)
            num_cls = " num" if role in ("number", "range", "missing") else ""
            aria = (
                f' aria-label="{_escape(accessible)}"'
                if accessible != visible
                else ""
            )
            out.append(
                f'<td headers="{_escape(" ".join(hrefs))}" '
                f'class="align-{align}{num_cls}"{aria}>'
                f"{_escape(visible)}</td>"
            )
        out.append("</tr>")
    out.append("</tbody>")
    out.append("</table>")

    scale_labels = paint.get("scale_labels") or []
    if scale_labels:
        out.append(
            f'<p class="table-scale"{style}>'
            f"{_escape('; '.join(scale_labels))}</p>"
        )
    return out


def _prose_html(prose: Any) -> str:
    chunks: list[str] = []
    runs = list(prose.runs)
    for i, run in enumerate(runs):
        text = _soft_break_html(run.text)
        if run.emphasis == "strong":
            chunks.append(f"<strong>{text}</strong>")
        else:
            chunks.append(text)
        # Plan joins runs before wrap; emit trailing <wbr> at soft-break run edges.
        nxt = runs[i + 1].text if i + 1 < len(runs) else ""
        if (
            run.text
            and run.text[-1] in _SOFT_BREAK_AFTER
            and nxt
            and not nxt[0].isspace()
        ):
            chunks.append("<wbr>")
    return "".join(chunks)


# Must match plan._wrap_tokens soft break set (R178-029 freeze/paint parity).
_SOFT_BREAK_AFTER = frozenset("-,:;.")


def _soft_break_html(text: str) -> str:
    """Escape text and insert <wbr> after plan soft-break punctuation."""
    if not text:
        return ""
    parts: list[str] = []
    n = len(text)
    for i, ch in enumerate(text):
        parts.append(html.escape(ch, quote=True))
        if ch in _SOFT_BREAK_AFTER and i + 1 < n and not text[i + 1].isspace():
            parts.append("<wbr>")
    return "".join(parts)


def _escape(text: str) -> str:
    return html.escape(text, quote=True)


def build_slide_notes_md(deck: Deck) -> str:
    """Authored slide order/headings; exact D221 text or _(no notes)_ (D250).

    Never trims notes content — only ensures the artifact ends with one LF.
    """
    chunks: list[str] = []
    for slide in deck.slides:
        heading = _slide_heading(slide, deck.sections)
        chunks.append(f"# Slide {slide.slide_number} — {heading}")
        chunks.append("")
        notes = getattr(slide, "speaker_notes", None)
        chunks.append(notes if notes else "_(no notes)_")
        chunks.append("")
    body = "\n".join(chunks)
    return body if body.endswith("\n") else body + "\n"


def _sorted_locator(locator: Any) -> Any:
    """D113/D216: recursively sort object keys; arrays order preserved, values walked."""
    if isinstance(locator, dict):
        return {k: _sorted_locator(locator[k]) for k in sorted(locator)}
    if isinstance(locator, list):
        return [_sorted_locator(item) for item in locator]
    return locator


def build_evidence_manifest(deck: Deck) -> dict[str, Any]:
    """Ordered registry + per-slide evidence links (D250)."""
    registry = []
    for eid, entry in deck.evidence_registry.items():
        item: dict[str, Any] = {
            "evidence_id": eid,
            "source_name": entry.source_name,
        }
        loc = _sorted_locator(entry.locator)
        if loc is not None:
            item["locator"] = loc
        registry.append(item)
    # Preserve authored registry iteration order (dict insertion order).

    slides = []
    for slide in deck.slides:
        row: dict[str, Any] = {
            "slide_number": slide.slide_number,
            "layout_type": slide.layout_type,
        }
        section_id = getattr(slide, "section_id", None)
        if section_id is not None:
            row["section_id"] = section_id
        eids = list(getattr(slide, "evidence_ids", None) or [])
        if eids:
            row["evidence_ids"] = eids
        slides.append(row)

    return {
        "renderer_version": RENDERER_VERSION,
        "handoff_schema_version": deck.meta.handoff_schema_version,
        "theme_id": THEME_ID,
        "evidence_registry": registry,
        "slides": slides,
    }


def build_slide_summaries(deck: Deck, deck_plan: DeckPlan | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    planned = deck_plan.by_surface_id() if deck_plan is not None else {}
    for slide in deck.slides:
        surface_ids: list[str] = []
        if slide.layout_type in ("opening_cover", "closing_cover"):
            surface_ids.append(f"slide-{slide.slide_number}-cover")
        elif slide.layout_type == "section_divider":
            surface_ids.append(f"slide-{slide.slide_number}-divider")
        elif slide.layout_type == "legal_notice":
            surface_ids.append(f"slide-{slide.slide_number}-legal")
        elif slide.layout_type in ("narrative", "data_table"):
            # Composition-slot order: title, subtitle, body/table, takeaway, disclosure.
            tid = f"slide-{slide.slide_number}-title"
            if tid in planned:
                surface_ids.append(tid)
            if slide.content is not None:
                surface_ids.append(f"slide-{slide.slide_number}-subtitle")
            if slide.layout_type == "narrative":
                surface_ids.extend(
                    f"slide-{slide.slide_number}-block-{b.block_id}"
                    for b in slide.payload.blocks
                )
            else:
                surface_ids.append(slide.payload.table.surface_id)
            if slide.takeaway is not None:
                surface_ids.append(f"slide-{slide.slide_number}-takeaway")
            disclosure = getattr(slide, "disclosure", None)
            if disclosure is not None:
                surface_ids.extend(
                    f"slide-{slide.slide_number}-disclosure-{s.surface_id}"
                    for s in disclosure.sections
                )
            if slide.source_footer is not None:
                surface_ids.append(f"slide-{slide.slide_number}-source-footer")
        row: dict[str, Any] = {
            "slide_number": slide.slide_number,
            "layout_type": slide.layout_type,
            "surface_ids": surface_ids,
        }
        section_id = getattr(slide, "section_id", None)
        if section_id is not None:
            row["section_id"] = section_id
        rows.append(row)
    return rows


def build_static_readiness(deck: Deck) -> list[dict[str, Any]]:
    """Pre-publication readiness facts only (D312); no browser measurement."""
    rows: list[dict[str, Any]] = []
    for slide in deck.slides:
        rows.append(
            {
                "slide_number": slide.slide_number,
                "layout_type": slide.layout_type,
                "frozen_plan_attached": True,  # kernel plan entries attached in run_meta.plans
                "required_payload_present": True,
                "semantic_table_present": False,  # no chart surfaces in kernel compositions
                "stable_ids_resolved": True,
                "readiness_contract_version": 1,
            }
        )
    return rows


def build_plans(deck: Deck, deck_plan: DeckPlan | None = None) -> list[dict[str, Any]]:
    """One plan entry per planned surface from the frozen deck plan (D69/D312)."""
    if deck_plan is not None:
        return deck_plan.public_plans()
    # Fallback stub only if called without a plan (should not happen in render_deck).
    return []


def build_run_meta(
    *,
    deck: Deck,
    status: str,
    ok: bool,
    strict: bool,
    debug: bool,
    svg_only: bool,
    events: list[DiagnosticEvent],
    artifact_bytes: dict[str, bytes],
    deck_plan: DeckPlan | None = None,
) -> dict[str, Any]:
    severity = {"info": 0, "warning": 0, "error": 0}
    for e in events:
        severity[e.severity] = severity.get(e.severity, 0) + e.occurrences

    artifacts = []
    for name in _HASHED_ARTIFACTS:
        data = artifact_bytes[name]
        artifacts.append(
            {
                "name": name,
                "bytes": len(data),
                "sha256": sha256_bytes(data),
            }
        )

    return {
        "renderer_version": RENDERER_VERSION,
        "handoff_schema_version": deck.meta.handoff_schema_version,
        "theme_id": THEME_ID,
        "status": status,
        "ok": ok,
        "options": {"strict": strict, "debug": debug, "svg_only": svg_only},
        "slide_count": len(deck.slides),
        "slides": build_slide_summaries(deck, deck_plan),
        "severity_counts": severity,
        "events": [e.model_dump(mode="json", exclude_none=True) for e in sort_events(events)],
        "plans": build_plans(deck, deck_plan),
        "static_readiness": build_static_readiness(deck),
        "artifacts": artifacts,
    }


def canonical_schema_bytes(schema_source: Path) -> bytes:
    """D121/D250 schema bytes: repository-canonical UTF-8/LF."""
    data = schema_source.read_bytes()
    # Working trees may checkout CRLF; publish the LF form of the git blob.
    if b"\r\n" in data:
        data = data.replace(b"\r\n", b"\n")
    return data


def stage_artifacts(
    *,
    deck: Deck,
    status: str,
    ok: bool,
    strict: bool,
    debug: bool,
    svg_only: bool,
    events: list[DiagnosticEvent],
    schema_source: Path,
    deck_plan: DeckPlan | None = None,
) -> dict[str, bytes]:
    """Build all five artifact payloads in memory (bytes, UTF-8/LF)."""
    html = build_presentation_html(
        deck,
        debug=debug,
        svg_only=svg_only,
        deck_plan=deck_plan,
        events=events,
    )
    notes = build_slide_notes_md(deck)
    manifest = dumps_json(build_evidence_manifest(deck))
    schema_bytes = canonical_schema_bytes(schema_source)

    partial = {
        "presentation.html": html.encode("utf-8"),
        "slide_notes.md": notes.encode("utf-8"),
        "evidence_manifest.json": manifest.encode("utf-8"),
        "handoff_schema_v1.json": schema_bytes,
    }
    run_meta = dumps_json(
        build_run_meta(
            deck=deck,
            status=status,
            ok=ok,
            strict=strict,
            debug=debug,
            svg_only=svg_only,
            events=events,
            artifact_bytes=partial,
            deck_plan=deck_plan,
        )
    )
    partial["run_meta.json"] = run_meta.encode("utf-8")
    return partial


def publish_transaction(out_dir: Path, artifacts: dict[str, bytes]) -> None:
    """Stage complete set, then directory-swap into destination (D250/D312)."""
    out_dir = Path(out_dir)
    parent = out_dir.parent if out_dir.parent != Path("") else Path(".")
    parent.mkdir(parents=True, exist_ok=True)

    staging = Path(
        tempfile.mkdtemp(prefix=".renderer_v3_stage_", dir=str(parent))
    )
    backup: Path | None = None
    retired: Path | None = None
    staging_pending = True
    preserve_backup = False
    try:
        for name in CANONICAL_ARTIFACTS:
            if name not in artifacts:
                raise RendererPublicationError(
                    [
                        event(
                            code="publication.transaction_failed",
                            severity="error",
                            phase="publication",
                            role="publisher",
                            path=f"/artifacts/{name}",
                            action="publish",
                            result="failed",
                            expected="canonical D250 artifact present",
                        )
                    ]
                )
            write_text_bytes(staging / name, artifacts[name])

        staged_names = {p.name for p in staging.iterdir() if p.is_file()}
        if staged_names != set(CANONICAL_ARTIFACTS):
            raise RendererPublicationError(
                [
                    event(
                        code="publication.transaction_failed",
                        severity="error",
                        phase="publication",
                        role="publisher",
                        path="/artifacts",
                        action="publish",
                        result="failed",
                        expected="exactly five canonical artifacts",
                    )
                ]
            )

        if out_dir.exists():
            # Bind backup only after the full copy succeeds (partial backup never used).
            backup_tmp = Path(
                tempfile.mkdtemp(prefix=".renderer_v3_backup_", dir=str(parent))
            )
            try:
                _copy_dir_contents(out_dir, backup_tmp)
            except Exception:
                shutil.rmtree(backup_tmp, ignore_errors=True)
                raise
            backup = backup_tmp

            retired = Path(
                tempfile.mkdtemp(prefix=".renderer_v3_retired_", dir=str(parent))
            )
            shutil.rmtree(retired)
            os.replace(str(out_dir), str(retired))

        os.replace(str(staging), str(out_dir))
        staging_pending = False

        if retired is not None:
            shutil.rmtree(retired, ignore_errors=True)
            retired = None

    except RendererPublicationError:
        try:
            _abort_publish(out_dir, retired, backup)
        except RendererPublicationError:
            preserve_backup = backup is not None and backup.exists()
            raise
        raise
    except Exception as exc:
        try:
            _abort_publish(out_dir, retired, backup)
        except RendererPublicationError:
            preserve_backup = backup is not None and backup.exists()
            raise
        raise RendererPublicationError(
            [
                event(
                    code="publication.transaction_failed",
                    severity="error",
                    phase="publication",
                    role="publisher",
                    path="/artifacts",
                    action="publish",
                    result="failed",
                    expected="atomic publication of five artifacts",
                    input_meta={"type": type(exc).__name__},
                )
            ]
        ) from exc
    finally:
        if staging_pending:
            shutil.rmtree(staging, ignore_errors=True)
        if retired is not None and retired.exists() and not preserve_backup:
            shutil.rmtree(retired, ignore_errors=True)
        if backup is not None and not preserve_backup:
            shutil.rmtree(backup, ignore_errors=True)


def write_text_bytes(path: Path, data: bytes) -> None:
    path.write_bytes(data)
    # Best-effort flush for transactional durability.
    try:
        with path.open("rb+") as fh:
            fh.flush()
            os.fsync(fh.fileno())
    except OSError:
        pass


def _copy_dir_contents(src: Path, dest: Path) -> None:
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def _abort_publish(
    out_dir: Path,
    retired: Path | None,
    backup: Path | None,
) -> None:
    """Restore prior output after a failed swap; raise rollback_failed if not."""
    try:
        if retired is not None and retired.exists():
            if out_dir.exists():
                shutil.rmtree(out_dir)
            os.replace(str(retired), str(out_dir))
            return
        # out never moved aside (or never existed): leave it alone.
        if out_dir.exists():
            return
        if backup is not None and backup.exists():
            _restore_backup(out_dir, backup)
    except RendererPublicationError:
        raise
    except Exception as exc:
        if backup is not None and backup.exists():
            _restore_backup(out_dir, backup)
            return
        raise RendererPublicationError(
            [
                event(
                    code="publication.rollback_failed",
                    severity="error",
                    phase="publication",
                    role="publisher",
                    path="/artifacts",
                    action="rollback",
                    result="failed",
                    expected="prior output restored byte-identical",
                    input_meta={"type": type(exc).__name__},
                )
            ]
        ) from exc


def _restore_backup(out_dir: Path, backup: Path | None) -> None:
    if backup is None or not backup.exists():
        return
    try:
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        _copy_dir_contents(backup, out_dir)
    except Exception as exc:
        raise RendererPublicationError(
            [
                event(
                    code="publication.rollback_failed",
                    severity="error",
                    phase="publication",
                    role="publisher",
                    path="/artifacts",
                    action="rollback",
                    result="failed",
                    expected="prior output restored byte-identical",
                    input_meta={"type": type(exc).__name__},
                )
            ]
        ) from exc


def resolved_schema_source() -> Path:
    """Path to the checked-in D121 schema artifact."""
    # Prefer package-relative path so installed/editable layouts work.
    pkg_schema = Path(__file__).resolve().parent / "schema" / "handoff_schema_v1.json"
    if pkg_schema.is_file():
        return pkg_schema
    return schema_path()
