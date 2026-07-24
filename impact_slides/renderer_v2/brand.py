"""Named brand mark/seal asset pack (#93/R3).

First-class vendored lockups selectable by name from the handoff
(``content.brand_mark``) instead of every author inventing a generic
``brand_mark_svg``. Assets are original, generic, token-parameterizable
(``currentColor``) — no third-party trademarks.
"""
from __future__ import annotations

from pathlib import Path

BRAND_DIR = Path(__file__).resolve().parent / "assets" / "brand"

# Explicit allowlist — unknown names fail closed (ValueError).
NAMED_MARKS = frozenset({"seal_lockup"})


def load_brand_mark(name: str) -> str:
    """Return the inline SVG string for a named vendored mark.

    Raises ValueError for unknown names (fail closed — never fetch or
    invent marks at render time) and FileNotFoundError if a registered
    asset is missing from the inventory.
    """
    key = (name or "").strip()
    if key not in NAMED_MARKS:
        raise ValueError(
            f"unknown brand_mark {name!r}: expected one of {sorted(NAMED_MARKS)} "
            f"or supply content.brand_mark_svg directly"
        )
    path = BRAND_DIR / f"{key}.svg"
    if not path.is_file():
        raise FileNotFoundError(
            f"registered brand mark {key!r} missing at {path} — "
            f"restore the vendored asset under assets/brand/"
        )
    svg = path.read_text(encoding="utf-8").strip()
    # Strip any XML prolog; the asset is vendored and trusted.
    if svg.startswith("<?xml"):
        svg = svg.split("?>", 1)[-1].strip()
    return svg
