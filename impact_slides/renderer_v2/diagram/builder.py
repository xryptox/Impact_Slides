"""Higher-level diagram scene builders using primitive macros.

Each function accepts a slide mapping and returns an inline SVG string.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from . import annotation_callout, arrow_connector, group_boundary, node_box


def _rows(slide: Mapping[str, Any]) -> list[list[str]]:
    """Extract 2-D string rows from visual_spec.primary_visual.steps_or_data."""
    vs = slide.get("visual_spec") or {}
    if not isinstance(vs, dict):
        return []
    pv = vs.get("primary_visual") or {}
    if not isinstance(pv, dict):
        return []
    data = pv.get("steps_or_data") or []
    rows: list[list[str]] = []
    for row in data:
        if isinstance(row, (list, tuple)):
            rows.append([str(c).strip() for c in row])
        elif isinstance(row, str) and "|" in row:
            rows.append([p.strip() for p in row.split("|")])
        elif isinstance(row, str):
            rows.append([row.strip()])
    return rows


def _svg_open() -> str:
    return '<svg class="diagram-canvas" viewBox="0 0 900 480" xmlns="http://www.w3.org/2000/svg">'


def _svg_close() -> str:
    return "</svg>"


# ---------------------------------------------------------------------------
# 1. System Architecture
# ---------------------------------------------------------------------------

def system_architecture_scene(slide: Mapping[str, Any]) -> str:
    """Render layered nodes inside group boundaries with vertical arrows."""
    rows = _rows(slide)
    if not rows:
        return '<div class="diagram-empty gl-card">No architecture data</div>'

    # Collect layers (first column) and nodes per layer
    layers: dict[str, list[dict]] = {}
    for row in rows:
        layer = row[0] if len(row) > 2 else "System"
        label = row[1] if len(row) > 1 else row[0]
        sub = row[2] if len(row) > 2 else ""
        layers.setdefault(layer, []).append({"label": label, "sublabel": sub})

    layer_names = list(layers.keys())[:3]
    node_w, node_h = 160, 50
    layer_h = 130
    layer_gap = 50
    start_y = 20
    svg_parts = [_svg_open()]
    arrows: list[str] = []

    for li, name in enumerate(layer_names):
        y = start_y + li * (layer_h + layer_gap)
        nodes = layers[name][:3]
        group_w = len(nodes) * 180 + 40
        group_x = max(20, (900 - group_w) / 2)

        svg_parts.append(group_boundary(group_x, y, group_w, layer_h, label=name))

        for ni, n in enumerate(nodes):
            nx = group_x + 20 + ni * 180
            ny = y + 45
            svg_parts.append(f'<g transform="translate({nx}, {ny})">')
            svg_parts.append(
                node_box(n["label"], sublabel=n["sublabel"], width=node_w, height=node_h)
            )
            svg_parts.append("</g>")

            # Vertical arrow to next layer (same column)
            if li < len(layer_names) - 1:
                from_x = nx + node_w / 2
                from_y = ny + node_h
                to_y = start_y + (li + 1) * (layer_h + layer_gap) + 45
                arrows.append(arrow_connector(from_x, from_y, from_x, to_y))

    svg_parts.extend(arrows)
    svg_parts.append(_svg_close())
    return "".join(svg_parts)


# ---------------------------------------------------------------------------
# 2. Data Flow Diagram
# ---------------------------------------------------------------------------

def data_flow_scene(slide: Mapping[str, Any]) -> str:
    """Render horizontal pipeline of nodes inside optional stage groups."""
    rows = _rows(slide)
    if not rows:
        return '<div class="diagram-empty gl-card">No pipeline data</div>'

    # Rows: [stage_name, node_label, sublabel]
    stages: dict[str, list[dict]] = {}
    for row in rows:
        stage = row[0] if len(row) > 2 else "Stage"
        label = row[1] if len(row) > 1 else row[0]
        sub = row[2] if len(row) > 2 else ""
        stages.setdefault(stage, []).append({"label": label, "sublabel": sub})

    stage_names = list(stages.keys())[:4]
    node_w, node_h = 150, 48
    stage_w = 200
    stage_h = 180
    start_x = 30
    start_y = 60
    gap_x = 40
    svg_parts = [_svg_open()]

    for si, name in enumerate(stage_names):
        x = start_x + si * (stage_w + gap_x)
        nodes = stages[name][:2]
        svg_parts.append(group_boundary(x, start_y, stage_w, stage_h, label=name))

        for ni, n in enumerate(nodes):
            ny = start_y + 40 + ni * 70
            nx = x + 25
            svg_parts.append(f'<g transform="translate({nx}, {ny})">')
            svg_parts.append(
                node_box(n["label"], sublabel=n["sublabel"], width=node_w, height=node_h)
            )
            svg_parts.append("</g>")

        # Horizontal arrow to next stage
        if si < len(stage_names) - 1:
            from_x = x + stage_w
            from_y = start_y + stage_h / 2
            to_x = start_x + (si + 1) * (stage_w + gap_x)
            to_y = from_y
            svg_parts.append(arrow_connector(from_x, from_y, to_x, to_y))

    svg_parts.append(_svg_close())
    return "".join(svg_parts)


# ---------------------------------------------------------------------------
# 3. Causal Loop
# ---------------------------------------------------------------------------

def causal_loop_scene(slide: Mapping[str, Any]) -> str:
    """Render feedback-loop nodes in a ring with curved arrows."""
    rows = _rows(slide)
    if not rows:
        return '<div class="diagram-empty gl-card">No loop data</div>'

    nodes = []
    for row in rows:
        label = row[0]
        arrow_dir = row[1] if len(row) > 1 else "→"
        nodes.append({"label": label, "dir": arrow_dir})
    nodes = nodes[:6]

    cx, cy = 450, 240
    radius = 160
    node_w, node_h = 140, 44
    svg_parts = [_svg_open()]

    # Place nodes on a circle
    positions: list[tuple[float, float]] = []
    n = len(nodes)
    for i, node in enumerate(nodes):
        angle = -math.pi / 2 + (2 * math.pi * i / n)
        nx = cx + radius * math.cos(angle) - node_w / 2
        ny = cy + radius * math.sin(angle) - node_h / 2
        positions.append((nx, ny))
        svg_parts.append(f'<g transform="translate({nx:.0f}, {ny:.0f})">')
        svg_parts.append(node_box(node["label"], width=node_w, height=node_h))
        svg_parts.append("</g>")

    # Curved arrows between consecutive nodes
    for i in range(n):
        x1 = positions[i][0] + node_w / 2
        y1 = positions[i][1] + node_h / 2
        x2 = positions[(i + 1) % n][0] + node_w / 2
        y2 = positions[(i + 1) % n][1] + node_h / 2
        svg_parts.append(arrow_connector(x1, y1, x2, y2, curved=True))

    svg_parts.append(_svg_close())
    return "".join(svg_parts)


# ---------------------------------------------------------------------------
# 4. Before / After
# ---------------------------------------------------------------------------

def before_after_scene(slide: Mapping[str, Any]) -> str:
    """Render side-by-side before/after comparison with transition arrow."""
    c = slide.get("content") or {}
    if not isinstance(c, dict):
        c = {}
    bullets = [str(b).strip() for b in (c.get("bullets") or []) if str(b).strip()]

    # Default items if no bullets
    before_items = bullets[:3] or ["Before state A", "Before state B"]
    after_items = bullets[3:6] or ["After state A", "After state B"]

    svg_parts = [_svg_open()]
    half_w = 400
    start_y = 80

    # Before group
    svg_parts.append(
        group_boundary(30, 60, half_w, 340, label="Before", fill="color-surface-soft")
    )
    for i, item in enumerate(before_items[:4]):
        y = start_y + i * 70
        svg_parts.append(f'<g transform="translate(80, {y})">')
        svg_parts.append(node_box(item, width=300, height=50, fill="color-surface"))
        svg_parts.append("</g>")

    # Transition arrow in the middle
    arrow_y = 240
    svg_parts.append(arrow_connector(440, arrow_y, 480, arrow_y, color="color-accent"))

    # After group
    svg_parts.append(
        group_boundary(500, 60, half_w, 340, label="After", fill="color-surface-soft")
    )
    for i, item in enumerate(after_items[:4]):
        y = start_y + i * 70
        svg_parts.append(f'<g transform="translate(550, {y})">')
        svg_parts.append(node_box(item, width=300, height=50, fill="color-surface"))
        svg_parts.append("</g>")

    svg_parts.append(_svg_close())
    return "".join(svg_parts)
