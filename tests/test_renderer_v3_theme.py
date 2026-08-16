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
# Hex only allowed inside the generated :root token declarations.
_HEX_RE = re.compile(r"#[0-9A-Fa-f]{3,8}\b")


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
    """D131: text-safe identity keys pass 4.5:1 on the transparent white body."""
    white = resolve_color("white", role="surface")
    for key in ("navy", "primary_blue", "success", "neutral", "warning"):
        ink = resolve_color(key, role="series_identity")
        assert contrast_ratio(ink, white) >= 4.5, (key, ink, contrast_ratio(ink, white))
    # sky_blue is a fill-identity accent (#248); not a text-on-white key.
    assert contrast_ratio(
        resolve_color("sky_blue", role="series_identity"), white
    ) < 4.5


def test_neutral_is_accessible_muted_ink():
    assert resolve_color("neutral", role="series_identity").lower() == "#63666a"


def test_sky_blue_identifies_a_series_as_fill_accent():
    """#248: sky_blue is the light default-cycle accent (not text-on-white)."""
    assert resolve_color("sky_blue", role="series_identity").lower() == "#80c8ff"
    assert resolve_color("sky_blue", role="fill").lower() == "#80c8ff"


def test_ink_faint_is_not_authorized_for_text_on_light():
    with pytest.raises(ValueError, match="role"):
        resolve_color("ink_faint", role="text_on_light")
    assert resolve_color("ink_faint", role="fill").lower() == "#929292"


def test_white_restricted_to_dark_surfaces():
    with pytest.raises(ValueError, match="role"):
        resolve_color("white", role="series_identity")
    assert resolve_color("white", role="text_on_dark").lower() == "#ffffff"


def test_default_series_cycles_follow_d43():
    assert default_series_keys("line") == (
        "navy", "primary_blue", "sky_blue", "neutral", "warning"
    )
    assert default_series_keys("bar") == (
        "primary_blue", "navy", "sky_blue", "neutral", "warning"
    )
    assert default_series_keys("combo") == default_series_keys("bar")
    for family in ("line", "bar"):
        for key in default_series_keys(family):
            resolve_color(key, role="series_identity")
            assert key != "success"
            assert key != "white"


def test_resolve_series_colors_returns_hex_from_manifest():
    colors = resolve_series_colors("bar", count=3)
    assert colors == [
        resolve_color("primary_blue", role="series_identity"),
        resolve_color("navy", role="series_identity"),
        resolve_color("sky_blue", role="series_identity"),
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




def test_css_color_tokens_match_palette():
    """Color custom properties must resolve from the palette, not a second hex table."""
    css = css_custom_properties()
    assert css["--color-navy"].lower() == resolve_color("navy", role="series_identity")
    assert css["--color-primary-blue"].lower() == resolve_color(
        "primary_blue", role="series_identity"
    )
    assert css["--color-neutral"].lower() == resolve_color("neutral", role="series_identity")
    assert css["--color-band"].lower() == resolve_color("navy", role="band")
    assert css["--color-band-ink"].lower() == resolve_color("white", role="text_on_dark")
    assert css["--color-panel"].lower() == resolve_color("panel", role="surface")
    # band ink on band: contrast-safe (D42/D66)
    assert contrast_ratio(css["--color-band-ink"], css["--color-band"]) >= 4.5


def test_chart_js_and_svg_tokens_share_resolved_colors():
    from impact_slides.renderer_v3.theme import chart_js_tokens, svg_tokens

    assert chart_js_tokens() == svg_tokens()
    bag = chart_js_tokens()
    assert bag["plot_background"] == bag["body_background"] == "transparent"
    assert bag["series"]["line"][0] == resolve_color("navy", role="series_identity")
    assert bag["series"]["bar"][0] == resolve_color(
        "primary_blue", role="series_identity"
    )


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

