"""Impact Slide Renderer v2 — Boardroom + Grid Design System.

Deterministic Python path that paints ``builder_handoff.json`` into a single
self-contained 1920×1080 HTML deck using shared ``gl-*`` primitives.

Public API:
    from impact_slides.renderer_v2 import render_deck
"""
from __future__ import annotations

__version__ = "2.0.0"

from .cli import render_deck

__all__ = ["render_deck", "__version__"]
