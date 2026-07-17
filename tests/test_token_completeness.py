"""Audit semantic-tokens.css for token completeness per plan §3.3.1."""

import re
from pathlib import Path


def _load_token_file() -> str:
    base = Path(__file__).parent.parent / "impact_slides" / "renderer_v2" / "css"
    return (base / "semantic-tokens.css").read_text(encoding="utf-8")


def _extract_token_names(css: str) -> set[str]:
    """Parse CSS custom property definitions."""
    names = set()
    for line in css.splitlines():
        line = line.strip()
        if line.startswith("--") and ":" in line:
            name = line.split(":", 1)[0].strip()
            names.add(name)
    return names


EXPECTED_TOKENS = {
    # Typography
    "--font-display",
    "--font-body",
    "--font-sans",
    "--font-num",
    "--font-mono",
    # Color palette
    "--color-primary",
    "--color-primary-deep",
    "--color-primary-mid",
    "--color-accent",
    "--color-accent-light",
    "--color-accent-2",
    "--color-warn",
    "--color-ink",
    "--color-ink-soft",
    "--color-ink-muted",
    "--color-ink-faint",
    "--color-ink-on-primary",
    "--color-surface",
    "--color-surface-soft",
    "--color-surface-alt",
    "--color-panel",
    "--color-panel-border",
    "--color-border",
    "--color-grid",
    "--color-rule",
    "--color-negative",
    # Spacing
    "--space-xs",
    "--space-sm",
    "--space-md",
    "--space-lg",
    "--space-xl",
    "--space-2xl",
    # Grid gaps
    "--grid-gap-sm",
    "--grid-gap-md",
    "--grid-gap-lg",
    # Radius
    "--radius-sm",
    "--radius-md",
    "--radius-lg",
    # Shadows
    "--shadow-sm",
    "--shadow-md",
    "--shadow-lg",
    # Stage
    "--slide-padding",
    # Typography scale
    "--text-xs",
    "--text-sm",
    "--text-base",
    "--text-lg",
    "--text-xl",
    "--text-2xl",
    "--text-display",
    "--text-title",
}


def test_all_expected_tokens_present():
    css = _load_token_file()
    found = _extract_token_names(css)
    missing = EXPECTED_TOKENS - found
    assert not missing, f"Missing tokens in semantic-tokens.css: {sorted(missing)}"


def test_no_hardcoded_hex_in_semantic_layer():
    """Semantic tokens should use var() fallbacks where possible.
    Brand-new semantic-only colors (--color-accent-2, --color-warn) are
    allowed as literals since no boardroom token maps to them yet.
    """
    css = _load_token_file()
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}")
    offenders = []
    ALLOW_LITERAL = {"--color-accent-2", "--color-warn"}
    for line in css.splitlines():
        line = line.strip()
        if not line.startswith("--"):
            continue
        if ":" not in line:
            continue
        token_name = line.split(":", 1)[0].strip()
        value = line.split(":", 1)[1]
        # Remove var(...) wrappers for check
        value_no_var = re.sub(r"var\([^)]*\)", "", value)
        matches = hex_pattern.findall(value_no_var)
        if matches and token_name not in ALLOW_LITERAL:
            offenders.append((line, matches))
    assert not offenders, f"Hard-coded hex values found in semantic tokens: {offenders}"


def test_semantic_tokens_load_through_shell():
    """shell.py load_css() should include semantic-tokens.css in the bundle."""
    from impact_slides.renderer_v2.shell import load_css

    css = load_css()
    assert "--color-primary:" in css
    assert "--font-mono:" in css
    assert "--space-2xl:" in css
    assert "--shadow-sm:" in css
    assert "--grid-gap-md:" in css
    assert "--slide-padding:" in css
