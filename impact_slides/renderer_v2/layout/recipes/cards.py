"""Evidence, insight, risk, recommendation card recipes."""
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

from .shared import _content, _so_what, _source_names



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
