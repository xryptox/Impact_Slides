"""Diagram and freeform layout recipes."""
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

from .shared import _so_what, _source_names



def render_system_architecture(slide, total, notes, active=False):
    """Layered node graph using diagram primitives."""
    from ...diagram.builder import system_architecture_scene

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
    from ...diagram.builder import data_flow_scene

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
    from ...diagram.builder import causal_loop_scene

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



# ---------------------------------------------------------------------------
# Wave 4a — Diagram layouts (Tree, Hierarchy, Ecosystem)
# ---------------------------------------------------------------------------

def render_decision_tree(slide, total, notes, active=False):
    """Decision tree with diamond decision nodes and elbow connectors."""
    from ...diagram.builder import decision_tree_scene

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
    from ...diagram.builder import hierarchy_tree_scene

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
    from ...diagram.builder import ecosystem_map_scene

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



def render_freeform(slide, total, notes, active=False):
    """Phase 7: named-area visual_spec.grid body inside standard gl-slide shell."""
    from ..freeform import render_freeform_main

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
