"""Zero-dependency SVG diagram primitives for renderer_v2.

All functions return inline HTML/SVG strings using semantic tokens via
CSS custom properties.  No external deps.
"""
from __future__ import annotations

from typing import Optional

from ..strip import esc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _svg_icon(name: str) -> str:
    """Return a <use> reference to the sprite icon."""
    href = name if name.startswith("#") else (name if name.startswith("ic-") else f"ic-{name}")
    if not href.startswith("#"):
        href = "#" + href
    return (
        f'<svg class="node-icon" viewBox="0 0 24 24" aria-hidden="true">'
        f'<use href="{href}"/></svg>'
    )


def _style_token(name: str) -> str:
    """Reference a CSS custom property."""
    return f"var(--{name})"


# ---------------------------------------------------------------------------
# 1. Node Box
# ---------------------------------------------------------------------------

def node_box(
    label: str,
    *,
    sublabel: str = "",
    icon: Optional[str] = None,
    width: int = 160,
    height: int = 60,
    fill: str = "color-surface",
    stroke: str = "color-primary",
    rx: int = 8,
    font_size: int = 14,
) -> str:
    """Generate a rounded-rect node with optional icon and label."""
    icon_html = _svg_icon(icon) if icon else ""
    icon_x = 12
    text_cx = width / 2
    sublabel_y = 38
    label_y = 26 if sublabel else (height / 2 + font_size * 0.35)

    parts = [
        f'<g class="diagram-node">',
        f'<rect x="0" y="0" width="{width}" height="{height}"'
        f' rx="{rx}" fill="{_style_token(fill)}"'
        f' stroke="{_style_token(stroke)}" stroke-width="2"/>',
    ]
    if icon_html:
        parts.append(f'<g transform="translate({icon_x}, {(height - 24) // 2})">{icon_html}</g>')
    parts.append(
        f'<text x="{text_cx}" y="{label_y}" text-anchor="middle"'
        f' fill="{_style_token("color-ink")}" font-size="{font_size}px"'
        f' font-weight="600" font-family="{_style_token("font-body")}">'
        f'{esc(label)}</text>'
    )
    if sublabel:
        parts.append(
            f'<text x="{text_cx}" y="{sublabel_y}" text-anchor="middle"'
            f' fill="{_style_token("color-ink-muted")}" font-size="{font_size - 2}px"'
            f' font-family="{_style_token("font-body")}">'
            f'{esc(sublabel)}</text>'
        )
    parts.append("</g>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# 2. Arrow Connector
# ---------------------------------------------------------------------------

def arrow_connector(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    curved: bool = False,
    color: str = "color-accent",
    width: float = 2,
    head_size: float = 8,
    dashed: bool = False,
) -> str:
    """Generate an arrow line/path between two points."""
    dash = ' stroke-dasharray="6,4"' if dashed else ""

    dx = x2 - x1
    dy = y2 - y1
    angle = __import__("math").atan2(dy, dx)

    cos_a = __import__("math").cos(angle)
    sin_a = __import__("math").sin(angle)

    hx1 = x2 - head_size * cos_a - head_size * 0.5 * sin_a
    hy1 = y2 - head_size * sin_a + head_size * 0.5 * cos_a
    hx2 = x2 - head_size * cos_a + head_size * 0.5 * sin_a
    hy2 = y2 - head_size * sin_a - head_size * 0.5 * cos_a

    if curved:
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        ctrl_x = mx - dy * 0.2
        ctrl_y = my + dx * 0.2
        path = f'M {x1:.1f} {y1:.1f} Q {ctrl_x:.1f} {ctrl_y:.1f} {x2:.1f} {y2:.1f}'
    else:
        path = f'M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}'

    parts = [
        f'<g class="diagram-arrow">',
        f'<path d="{path}"'
        f' stroke="{_style_token(color)}" stroke-width="{width}"'
        f' fill="none" marker-end="none"{dash}/>',
        f'<polygon points="{x2:.1f},{y2:.1f} {hx1:.1f},{hy1:.1f} {hx2:.1f},{hy2:.1f}"'
        f' fill="{_style_token(color)}"/>',
        f'</g>',
    ]
    return "".join(parts)


# ---------------------------------------------------------------------------
# 3. Group Boundary
# ---------------------------------------------------------------------------

def group_boundary(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    label: str = "",
    stroke: str = "color-primary-mid",
    stroke_width: float = 1.5,
    stroke_dash: str = "8,4",
    fill: str = "color-surface-soft",
    rx: float = 12,
    font_size: int = 12,
) -> str:
    """Generate a dashed rounded-rect group boundary with optional label."""
    parts = [
        f'<g class="diagram-group">',
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}"',
        f' rx="{rx}" fill="{_style_token(fill)}" fill-opacity="0.35"',
        f' stroke="{_style_token(stroke)}" stroke-width="{stroke_width}"',
        f' stroke-dasharray="{stroke_dash}"/>',
    ]
    if label:
        parts.append(
            f'<text x="{x + 12:.1f}" y="{y + 20:.1f}"'
            f' fill="{_style_token(stroke)}" font-size="{font_size}px"'
            f' font-weight="600" font-family="{_style_token("font-body")}">'
            f'{esc(label)}</text>'
        )
    parts.append("</g>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# 4. Annotation Callout
# ---------------------------------------------------------------------------

def annotation_callout(
    x: float,
    y: float,
    text: str,
    *,
    target_x: Optional[float] = None,
    target_y: Optional[float] = None,
    width: float = 200,
    fill: str = "color-accent",
    text_color: str = "color-ink-on-primary",
    font_size: int = 12,
    padding: float = 8,
    rx: float = 6,
) -> str:
    """Generate a positioned annotation with optional connector line."""
    inner = text.replace("\n", "<br/>")
    parts = []

    if target_x is not None and target_y is not None:
        parts.append(
            f'<line x1="{x:.1f}" y1="{y:.1f}"'
            f' x2="{target_x:.1f}" y2="{target_y:.1f}"'
            f' stroke="{_style_token("color-accent")}" stroke-width="1.5"'
            f' stroke-dasharray="4,2"/>'
        )

    parts.extend([
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="40"',
        f' rx="{rx}" fill="{_style_token(fill)}" fill-opacity="0.9"/>',
        f'<foreignObject x="{x + padding:.1f}" y="{y + padding:.1f}"',
        f' width="{width - padding * 2:.1f}" height="30">',
        f'<div xmlns="http://www.w3.org/1999/xhtml"',
        f' style="color:{_style_token(text_color)};font-size:{font_size}px;',
        f'font-family:{_style_token("font-body")};line-height:1.3;">',
        f'{esc(inner)}</div>',
        f'</foreignObject>',
    ])

    return f'<g class="diagram-annotation">{"".join(parts)}</g>'
