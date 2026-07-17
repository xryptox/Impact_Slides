"""Higher-level diagram scene builders using primitive macros.

Each function accepts a slide mapping and returns an inline SVG string.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from . import annotation_callout, arrow_connector, group_boundary, node_box
from ..strip import esc


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


# ---------------------------------------------------------------------------
# 5. Decision Tree
# ---------------------------------------------------------------------------

def decision_tree_scene(slide: Mapping[str, Any]) -> str:
    """Render a binary/ternary branching tree with diamond decision nodes."""
    rows = _rows(slide)
    if not rows:
        return '<div class="diagram-empty gl-card">No tree data</div>'

    nodes = []
    for row in rows:
        label = row[0]
        node_type = row[1] if len(row) > 1 else "node"
        nodes.append({"label": label, "type": node_type})
    nodes = nodes[:7]

    svg_parts = [_svg_open()]
    node_w, node_h = 160, 56
    diamond_size = 44
    level_h = 120
    start_y = 50
    cx = 450

    # Proper binary tree placement: root alone on level 0, two children on
    # level 1, up to four grandchildren on level 2, etc.
    positions: list[tuple[float, float]] = []
    n = len(nodes)
    for i, node in enumerate(nodes):
        if i == 0:
            level, pos_in_level, nodes_in_level = 0, 0, 1
        else:
            level = int(math.floor(math.log2(i + 1)))
            pos_in_level = i - (2 ** level - 1)
            nodes_in_level = 2 ** level
        # Spread nodes evenly across the level, centred on cx
        span = min(700, 200 * nodes_in_level)
        if nodes_in_level == 1:
            x = cx - node_w / 2
        else:
            x = cx - span / 2 + pos_in_level * (span / (nodes_in_level - 1)) - node_w / 2
        y = start_y + level * level_h
        positions.append((x, y))

        if node["type"] == "decision":
            # Diamond shape — size grows with label length so text fits
            label = node["label"]
            # Wrap long labels into two lines at a word boundary near the middle
            words = label.split()
            if len(label) > 16 and len(words) >= 2:
                mid = len(words) // 2
                line1, line2 = " ".join(words[:mid]), " ".join(words[mid:])
            else:
                line1, line2 = label, ""
            d_size = max(diamond_size, 10 + max(len(line1), len(line2)) * 4)
            dx = x + node_w / 2
            dy = y + node_h / 2
            svg_parts.append(
                f'<polygon points="{dx},{dy - d_size} {dx + d_size},{dy} '
                f'{dx},{dy + d_size} {dx - d_size},{dy}" '
                f'fill="var(--color-surface)" stroke="var(--color-primary)" stroke-width="2"/>'
            )
            if line2:
                svg_parts.append(
                    f'<text x="{dx}" y="{dy - 8}" text-anchor="middle" dominant-baseline="middle" '
                    f'font-size="11" fill="var(--color-ink)">{esc(line1)}</text>'
                )
                svg_parts.append(
                    f'<text x="{dx}" y="{dy + 8}" text-anchor="middle" dominant-baseline="middle" '
                    f'font-size="11" fill="var(--color-ink)">{esc(line2)}</text>'
                )
            else:
                svg_parts.append(
                    f'<text x="{dx}" y="{dy}" text-anchor="middle" dominant-baseline="middle" '
                    f'font-size="11" fill="var(--color-ink)">{esc(line1)}</text>'
                )
        else:
            svg_parts.append(f'<g transform="translate({x}, {y})">')
            svg_parts.append(node_box(node["label"], width=node_w, height=node_h))
            svg_parts.append("</g>")

    # Elbow connectors from parent to children
    for i in range(n - 1):
        parent_idx = i // 2
        if parent_idx >= len(positions):
            continue
        px = positions[parent_idx][0] + node_w / 2
        # Use actual diamond size for decision nodes so connectors start at the edge
        parent = nodes[parent_idx]
        if parent["type"] == "decision":
            plabel = parent["label"]
            pwords = plabel.split()
            if len(plabel) > 16 and len(pwords) >= 2:
                pline1 = " ".join(pwords[: len(pwords) // 2])
                pline2 = " ".join(pwords[len(pwords) // 2 :])
            else:
                pline1, pline2 = plabel, ""
            p_d_size = max(diamond_size, 10 + max(len(pline1), len(pline2)) * 4)
            py = positions[parent_idx][1] + p_d_size
        else:
            py = positions[parent_idx][1] + node_h
        cx_pos = positions[i + 1][0] + node_w / 2
        cy_pos = positions[i + 1][1]
        # Elbow: down then across
        mid_y = (py + cy_pos) / 2
        svg_parts.append(
            f'<polyline points="{px},{py} {px},{mid_y} {cx_pos},{mid_y} {cx_pos},{cy_pos}" '
            f'fill="none" stroke="var(--color-accent)" stroke-width="2" marker-end="url(#arrowhead)"/>'
        )

    svg_parts.append(_svg_close())
    return "".join(svg_parts)


# ---------------------------------------------------------------------------
# 6. Hierarchy Tree
# ---------------------------------------------------------------------------

def hierarchy_tree_scene(slide: Mapping[str, Any]) -> str:
    """Render a parent-child hierarchy using nested group boundaries."""
    rows = _rows(slide)
    if not rows:
        return '<div class="diagram-empty gl-card">No hierarchy data</div>'

    # Rows: [parent, child, sublabel]
    groups: dict[str, list[dict]] = {}
    for row in rows:
        parent = row[0] if len(row) > 1 else "Root"
        label = row[1] if len(row) > 1 else row[0]
        sub = row[2] if len(row) > 2 else ""
        groups.setdefault(parent, []).append({"label": label, "sublabel": sub})

    group_names = list(groups.keys())[:4]
    node_w, node_h = 130, 44
    group_w = 200
    group_h = 160
    start_x = 30
    start_y = 60
    gap_x = 40
    svg_parts = [_svg_open()]

    arrows: list[str] = []
    for gi, name in enumerate(group_names):
        x = start_x + gi * (group_w + gap_x)
        nodes = groups[name][:3]
        svg_parts.append(group_boundary(x, start_y, group_w, group_h, label=name))
        for ni, n in enumerate(nodes):
            ny = start_y + 40 + ni * 50
            nx = x + 35
            svg_parts.append(f'<g transform="translate({nx}, {ny})">')
            svg_parts.append(node_box(n["label"], sublabel=n["sublabel"], width=node_w, height=node_h))
            svg_parts.append("</g>")

        # Horizontal arrow to next group
        if gi < len(group_names) - 1:
            from_x = x + group_w
            from_y = start_y + group_h / 2
            to_x = start_x + (gi + 1) * (group_w + gap_x)
            to_y = from_y
            arrows.append(arrow_connector(from_x, from_y, to_x, to_y))

    svg_parts.extend(arrows)
    svg_parts.append(_svg_close())
    return "".join(svg_parts)


# ---------------------------------------------------------------------------
# 7. Ecosystem Map
# ---------------------------------------------------------------------------

def ecosystem_map_scene(slide: Mapping[str, Any]) -> str:
    """Render a stakeholder web with nodes and labeled connections."""
    rows = _rows(slide)
    if not rows:
        return '<div class="diagram-empty gl-card">No ecosystem data</div>'

    # Rows: [node_label, connection_label, target_node]
    nodes: dict[str, dict] = {}
    connections: list[tuple[str, str, str]] = []
    for row in rows:
        label = row[0]
        conn = row[1] if len(row) > 1 else ""
        target = row[2] if len(row) > 2 else ""
        nodes.setdefault(label, {"label": label})
        if target:
            nodes.setdefault(target, {"label": target})
            connections.append((label, conn, target))

    node_list = list(nodes.keys())[:8]
    cx, cy = 450, 240
    radius = 180
    node_w, node_h = 120, 40
    svg_parts = [_svg_open()]

    positions: dict[str, tuple[float, float]] = {}
    n = len(node_list)
    for i, label in enumerate(node_list):
        angle = -math.pi / 2 + (2 * math.pi * i / n)
        nx = cx + radius * math.cos(angle) - node_w / 2
        ny = cy + radius * math.sin(angle) - node_h / 2
        positions[label] = (nx, ny)
        svg_parts.append(f'<g transform="translate({nx:.0f}, {ny:.0f})">')
        svg_parts.append(node_box(label, width=node_w, height=node_h))
        svg_parts.append("</g>")

    # Connections
    for src, label, tgt in connections:
        if src not in positions or tgt not in positions:
            continue
        sx = positions[src][0] + node_w / 2
        sy = positions[src][1] + node_h / 2
        tx = positions[tgt][0] + node_w / 2
        ty = positions[tgt][1] + node_h / 2
        svg_parts.append(arrow_connector(sx, sy, tx, ty))
        # Label at midpoint
        mx = (sx + tx) / 2
        my = (sy + ty) / 2
        svg_parts.append(
            f'<text x="{mx}" y="{my}" text-anchor="middle" font-size="11" '
            f'fill="var(--color-ink-muted)">{esc(label)}</text>'
        )

    svg_parts.append(_svg_close())
    return "".join(svg_parts)
