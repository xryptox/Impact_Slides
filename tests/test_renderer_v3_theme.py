"""Renderer v3 boardroom_amex theme manifest (#177).

Seams under test:
- one Python manifest supplies CSS / Chart.js / SVG tokens
- role-qualified palette is contrast-safe; painters carry no raw theme hex
- chart plot/body surfaces are transparent + flat; generated CSS drift fails
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import render_deck
from impact_slides.renderer_v3.theme import (
    THEME_ID,
    contrast_ratio,
    css_custom_properties,
    default_series_keys,
    generate_theme_css,
    line_style_keys,
    marker_keys,
    palette_keys,
    resolve_color,
    resolve_series_colors,
)
from impact_slides.renderer_v3.theme_export import check_theme, theme_css_path, write_theme

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/minimal_cover_narrative_cover.json"
THEME_CSS = ROOT / "impact_slides/renderer_v3/theme/boardroom_amex.tokens.css"
V3_PY = ROOT / "impact_slides/renderer_v3"

# Hex only allowed inside the theme module (and its generated CSS artifact).
_HEX_RE = re.compile(r"#[0-9A-Fa-f]{3,8}\b")
_PAINTER_ALLOW_NAMES = frozenset({"theme_export.py"})
_PAINTER_ALLOW_DIRS = frozenset({"theme"})


def _write_handoff(tmp: Path) -> Path:
    path = tmp / "handoff.json"
    path.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    return path


# ---------------------------------------------------------------------------
# Manifest surface
# ---------------------------------------------------------------------------


def test_theme_id_is_boardroom_amex():
    assert THEME_ID == "boardroom_amex"


def test_palette_keys_match_d130_d131():
    keys = palette_keys()
    assert "navy" in keys
    assert "primary_blue" in keys
    assert "sky_blue" in keys
    assert "success" in keys
    assert "neutral" in keys
    assert "warning" in keys
    assert "white" in keys


def test_identity_keys_pass_text_contrast_on_white():
    """D131: series-identity keys pass 4.5:1 on the transparent white body."""
    white = resolve_color("white", role="surface")
    for key in ("navy", "primary_blue", "success", "neutral", "warning"):
        ink = resolve_color(key, role="series_identity")
        assert contrast_ratio(ink, white) >= 4.5, (key, ink, contrast_ratio(ink, white))


def test_neutral_is_accessible_muted_ink():
    assert resolve_color("neutral", role="series_identity").lower() == "#63666a"


def test_sky_blue_cannot_identify_a_series():
    with pytest.raises(ValueError, match="role"):
        resolve_color("sky_blue", role="series_identity")
    # fill on dark/outlined surfaces remains valid
    assert resolve_color("sky_blue", role="fill").lower() == "#80c8ff"


def test_white_restricted_to_dark_surfaces():
    with pytest.raises(ValueError, match="role"):
        resolve_color("white", role="series_identity")
    assert resolve_color("white", role="text_on_dark").lower() == "#ffffff"


def test_default_series_cycles_follow_d43():
    assert default_series_keys("line")[0] == "navy"
    assert default_series_keys("bar")[0] == "primary_blue"
    # only identity-safe keys
    for family in ("line", "bar"):
        for key in default_series_keys(family):
            resolve_color(key, role="series_identity")
            assert key != "sky_blue"
            assert key != "white"


def test_resolve_series_colors_returns_hex_from_manifest():
    colors = resolve_series_colors("bar", count=3)
    assert colors == [
        resolve_color("primary_blue", role="series_identity"),
        resolve_color("navy", role="series_identity"),
        resolve_color("success", role="series_identity"),
    ]
    # Chart.js + SVG share the same resolved list
    assert all(c.startswith("#") and len(c) == 7 for c in colors)


def test_line_style_and_marker_keys_are_closed():
    assert line_style_keys() == ("solid", "dashed", "dotted", "dash_dot")
    assert marker_keys() == ("circle", "square", "triangle", "diamond")


def test_css_tokens_cover_semantic_layers():
    css = css_custom_properties()
    # color / font / spacing / border / typography
    for name in (
        "--color-navy",
        "--color-primary-blue",
        "--color-panel",
        "--color-panel-border",
        "--font-body",
        "--font-display",
        "--space-md",
        "--border-width-hairline",
        "--radius-card",
        "--text-title",
        "--text-body",
    ):
        assert name in css
    # no legacy aliases in the public layer (D129)
    assert "--navy:" not in css
    assert "--blue:" not in css
    assert "--panel:" not in css


def test_generated_css_declares_transparent_flat_chart_surfaces():
    css = generate_theme_css()
    assert ".chart-plot" in css and ".chart-body" in css
    # transparent + flat (D5/D6)
    block = css[css.index(".chart-plot") : css.index(".chart-plot") + 280]
    assert "background: transparent" in block
    assert "border: none" in block
    assert "box-shadow: none" in block
    assert "border-radius: 0" in block


def test_committed_theme_css_matches_manifest():
    expected = generate_theme_css()
    assert THEME_CSS.is_file()
    actual = THEME_CSS.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert actual == expected


def test_theme_export_check_cli():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "impact_slides.renderer_v3.theme_export",
            "--check",
            "--root",
            str(ROOT),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_theme_drift_detected(tmp_path: Path):
    dest = tmp_path / "impact_slides/renderer_v3/theme"
    dest.mkdir(parents=True)
    (dest / "boardroom_amex.tokens.css").write_text("/* stale */\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        check_theme(tmp_path)


def test_write_theme_round_trip(tmp_path: Path):
    path = write_theme(tmp_path)
    assert path == theme_css_path(tmp_path)
    assert path.read_text(encoding="utf-8") == generate_theme_css()


def test_presentation_html_uses_theme_tokens_not_raw_hex(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"
    render_deck(handoff, out)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert f'theme-id" content="{THEME_ID}"' in html or f'theme-id" content=\'{THEME_ID}\'' in html
    # injected generated token block
    assert "--color-navy:" in html
    assert "var(--color-navy)" in html
    assert "var(--font-body)" in html
    assert "var(--color-surface)" in html
    # no raw theme hex outside the generated :root token block values
    # (token declarations necessarily contain hex — painters must use var())
    style_end = html.index("</style>")
    style = html[:style_end]
    # strip :root { ... } token declarations, then assert no remaining hex
    stripped = re.sub(r":root\s*\{[^}]*\}", "", style, count=1, flags=re.S)
    assert not _HEX_RE.search(stripped), stripped


def test_schema_v1_painters_contain_no_raw_theme_hex():
    """Production painters (everything except theme.*) hold no theme hex (D129)."""
    offenders: list[str] = []
    for path in sorted(V3_PY.rglob("*.py")):
        if path.name in _PAINTER_ALLOW_NAMES:
            continue
        if any(part in _PAINTER_ALLOW_DIRS for part in path.parts):
            continue
        if path.name.startswith("test_"):
            continue
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if _HEX_RE.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{i}:{line.strip()}")
    assert offenders == []
