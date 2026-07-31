"""Process and timeline layout recipes."""
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

from .shared import _CLOSED_LOOP, _content, _sequential_grid, _so_what, _source_names, _vs_steps, apply_timeline_year_overrides, split_step_copy



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



def render_circular_process(slide, total, notes, active=False):
    """Circular improvement loop with curved arrows between nodes."""
    from ...diagram.builder import causal_loop_scene

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
