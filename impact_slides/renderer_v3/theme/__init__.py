"""Canonical boardroom_amex theme manifest (D127–D133).

One Python source of truth for semantic CSS custom properties and the
resolved Chart.js / SVG color values. Generated CSS is checked for drift
via ``python -m impact_slides.renderer_v3.theme_export --check``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

THEME_ID = "boardroom_amex"

ColorRole = Literal[
    "series_identity",
    "fill",
    "text_on_dark",
    "text_on_light",
    "surface",
    "border",
    "band",
]


@dataclass(frozen=True, slots=True)
class PaletteEntry:
    """One approved palette key with role gates (D130/D131)."""

    key: str
    hex: str
    roles: frozenset[str]


# Canonical Amex hex values (uppercase storage; resolve_color returns lowercase).
_PALETTE: tuple[PaletteEntry, ...] = (
    PaletteEntry("navy", "#00175A", frozenset({
        "series_identity", "fill", "text_on_light", "band", "border",
    })),
    PaletteEntry("primary_blue", "#006FCF", frozenset({
        "series_identity", "fill", "text_on_light", "border",
    })),
    PaletteEntry("sky_blue", "#80C8FF", frozenset({
        "fill",  # non-text fill only (D131)
    })),
    PaletteEntry("success", "#0A7D55", frozenset({
        "series_identity", "fill", "text_on_light",
    })),
    PaletteEntry("neutral", "#63666A", frozenset({
        "series_identity", "fill", "text_on_light",
    })),
    PaletteEntry("warning", "#B35900", frozenset({
        "series_identity", "fill", "text_on_light",
    })),
    PaletteEntry("white", "#FFFFFF", frozenset({
        "text_on_dark", "surface",
    })),
    PaletteEntry("ink", "#53565A", frozenset({
        "text_on_light", "fill",
    })),
    PaletteEntry("ink_faint", "#929292", frozenset({
        "fill",
    })),
    PaletteEntry("panel", "#EEF0F0", frozenset({
        "surface", "fill",
    })),
    PaletteEntry("panel_border", "#D8DCE3", frozenset({
        "border",
    })),
    PaletteEntry("grid", "#E0E4EA", frozenset({
        "border", "fill",
    })),
    PaletteEntry("surface", "#FFFFFF", frozenset({
        "surface",
    })),
    PaletteEntry("surface_soft", "#F8F8F8", frozenset({
        "surface", "fill",
    })),
    PaletteEntry("stage", "#0B0F1A", frozenset({
        "surface", "band",
    })),
)

_BY_KEY: Mapping[str, PaletteEntry] = {e.key: e for e in _PALETTE}

# D43 default series cycles — identity-safe keys only (D131).
_LINE_SERIES_KEYS: tuple[str, ...] = (
    "navy", "primary_blue", "success", "neutral", "warning",
)
_BAR_SERIES_KEYS: tuple[str, ...] = (
    "primary_blue", "navy", "success", "neutral", "warning",
)

_LINE_STYLE_KEYS: tuple[str, ...] = ("solid", "dashed", "dotted", "dash_dot")
_MARKER_KEYS: tuple[str, ...] = ("circle", "square", "triangle", "diamond")

def _hex(key: str) -> str:
    return _BY_KEY[key].hex


# Semantic CSS custom properties (D129). Color values derive from _PALETTE only.
_CSS_TOKENS: tuple[tuple[str, str], ...] = (
    # fonts
    ("--font-display", '"Source Sans 3", sans-serif'),
    ("--font-body", '"Source Sans 3", "IBM Plex Sans", sans-serif'),
    ("--font-num", '"IBM Plex Sans", "Source Sans 3", sans-serif'),
    # colors (semantic --color-* only) — hex from _PALETTE
    ("--color-navy", _hex("navy")),
    ("--color-primary-blue", _hex("primary_blue")),
    ("--color-sky-blue", _hex("sky_blue")),
    ("--color-success", _hex("success")),
    ("--color-neutral", _hex("neutral")),
    ("--color-warning", _hex("warning")),
    ("--color-ink", _hex("ink")),
    ("--color-ink-faint", _hex("ink_faint")),
    ("--color-ink-on-dark", _hex("white")),
    ("--color-white", _hex("white")),
    ("--color-surface", _hex("surface")),
    ("--color-surface-soft", _hex("surface_soft")),
    ("--color-panel", _hex("panel")),
    ("--color-panel-border", _hex("panel_border")),
    ("--color-grid", _hex("grid")),
    ("--color-rule", _hex("navy")),
    ("--color-stage", _hex("stage")),
    ("--color-band", _hex("navy")),
    ("--color-band-ink", _hex("white")),
    ("--color-chart-plot", "transparent"),
    ("--color-chart-body", "transparent"),
    # spacing
    ("--space-xs", "8px"),
    ("--space-sm", "12px"),
    ("--space-md", "20px"),
    ("--space-lg", "28px"),
    ("--space-xl", "32px"),
    ("--space-2xl", "48px"),
    ("--space-3xl", "96px"),
    ("--space-pad-x", "96px"),
    ("--space-pad-top", "56px"),
    ("--space-pad-bottom", "48px"),
    # borders / radii (card chrome only — charts stay flat)
    ("--border-width-hairline", "1px"),
    ("--radius-sm", "8px"),
    ("--radius-md", "14px"),
    ("--radius-lg", "20px"),
    ("--radius-card", "16px"),
    # typography scale
    ("--text-xs", "14px"),
    ("--text-sm", "14px"),
    ("--text-body", "22px"),
    ("--text-lead", "22px"),
    ("--text-insight", "26px"),
    ("--text-title", "56px"),
    ("--text-display", "72px"),
    ("--text-kpi", "70px"),
    ("--font-weight-body", "400"),
    ("--font-weight-emphasis", "600"),
    ("--font-weight-title", "700"),
)


def palette_keys() -> tuple[str, ...]:
    return tuple(_BY_KEY.keys())


def line_style_keys() -> tuple[str, ...]:
    return _LINE_STYLE_KEYS


def marker_keys() -> tuple[str, ...]:
    return _MARKER_KEYS


def default_series_keys(family: str) -> tuple[str, ...]:
    fam = (family or "").strip().lower()
    if fam in ("line", "trend", "area"):
        return _LINE_SERIES_KEYS
    # combo uses bar cycle as the shared multi-series palette (D99/D132).
    if fam in (
        "bar",
        "column",
        "stacked_bar",
        "grouped_bar",
        "horizontal_bar",
        "combo",
    ):
        return _BAR_SERIES_KEYS
    raise ValueError(f"unknown chart family for series cycle: {family!r}")


def resolve_color(key: str, *, role: ColorRole | str) -> str:
    """Resolve a palette key to canonical lowercase hex if ``role`` is allowed."""
    entry = _BY_KEY.get(key)
    if entry is None:
        raise ValueError(f"unknown palette key: {key!r}")
    if role not in entry.roles:
        raise ValueError(
            f"palette key {key!r} does not allow role {role!r}; "
            f"allowed={sorted(entry.roles)}"
        )
    return entry.hex.lower()


def resolve_series_colors(family: str, *, count: int) -> list[str]:
    """Resolved Chart.js/SVG series colors for ``count`` series (D43/D132)."""
    if count < 0:
        raise ValueError("count must be >= 0")
    keys = default_series_keys(family)
    out: list[str] = []
    for i in range(count):
        out.append(resolve_color(keys[i % len(keys)], role="series_identity"))
    return out


def css_custom_properties() -> dict[str, str]:
    """Semantic token map used by HTML painters (D129)."""
    return dict(_CSS_TOKENS)


def generate_theme_css() -> str:
    """UTF-8/LF CSS artifact generated from the manifest (D129)."""
    lines = [
        "/* Generated from impact_slides.renderer_v3.theme — do not edit. */",
        f"/* theme_id: {THEME_ID} */",
        ":root {",
    ]
    for name, value in _CSS_TOKENS:
        lines.append(f"  {name}: {value};")
    lines.extend(
        [
            "}",
            "",
            "/* D5/D6 — chart plot/body surfaces are transparent and flat. */",
            ".chart-plot,",
            ".chart-body {",
            "  background: transparent;",
            "  border: none;",
            "  box-shadow: none;",
            "  border-radius: 0;",
            "}",
            "",
            "/* D66/D67 — named card chrome uses panel + hairline border. */",
            ".card-panel {",
            "  background: var(--color-panel);",
            "  border: var(--border-width-hairline) solid var(--color-panel-border);",
            "  border-radius: var(--radius-card);",
            "}",
            "",
            "/* D42 — structural title/header bands use dark navy + white ink. */",
            ".band-title,",
            ".band-table-header {",
            "  background: var(--color-band);",
            "  color: var(--color-band-ink);",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG 2.x contrast ratio between two hex colors."""
    return ( _rel_luminance(fg) + 0.05 ) / ( _rel_luminance(bg) + 0.05 ) if _rel_luminance(fg) >= _rel_luminance(bg) else ( _rel_luminance(bg) + 0.05 ) / ( _rel_luminance(fg) + 0.05 )


def _rel_luminance(hex_color: str) -> float:
    r, g, b = _hex_to_rgb(hex_color)
    def chan(c: float) -> float:
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) != 6:
        raise ValueError(f"invalid hex color: {hex_color!r}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def chart_js_tokens() -> dict[str, object]:
    """Resolved token bag for Chart.js painters (no CSS vars)."""
    return {
        "theme_id": THEME_ID,
        "colors": {k: resolve_color(k, role=_preferred_role(k)) for k in _BY_KEY},
        "series": {
            "line": list(resolve_series_colors("line", count=len(_LINE_SERIES_KEYS))),
            "bar": list(resolve_series_colors("bar", count=len(_BAR_SERIES_KEYS))),
        },
        "line_styles": list(_LINE_STYLE_KEYS),
        "markers": list(_MARKER_KEYS),
        "plot_background": "transparent",
        "body_background": "transparent",
    }


svg_tokens = chart_js_tokens  # same resolved bag for both painters (D129/D57)

def _preferred_role(key: str) -> str:
    entry = _BY_KEY[key]
    for role in (
        "series_identity",
        "text_on_light",
        "text_on_dark",
        "fill",
        "surface",
        "border",
        "band",
    ):
        if role in entry.roles:
            return role
    raise ValueError(f"palette key {key!r} has no roles")


