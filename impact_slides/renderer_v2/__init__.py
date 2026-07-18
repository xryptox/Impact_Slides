"""Impact Slide Renderer v2 — Boardroom + Grid Design System.

Deterministic Python path that paints ``builder_handoff.json`` into a single
self-contained 1920×1080 HTML deck using shared ``gl-*`` primitives.

Delivery is **self-contained by default** (vendored fonts embedded; works
offline / VPN). ``--use-cdn`` is a development-only escape hatch — see
``impact_slides/renderer_v2/assets/THIRD_PARTY.md`` and
``wiki/SPEC_renderer_v2_p0_self_contained.md``.

Public API:
    from impact_slides.renderer_v2 import render_deck
"""
from __future__ import annotations

__version__ = "2.0.0"

from .cli import render_deck

__all__ = ["render_deck", "__version__"]
