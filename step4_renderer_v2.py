#!/usr/bin/env python3
"""Thin shim — Impact Slide Renderer v2 (Boardroom + Grid Design System).

Usage:
  python step4_renderer_v2.py --handoff builder_handoff.json --out out_dir
  python -m impact_slides.renderer_v2 --handoff ... --out ...
"""
from __future__ import annotations

from impact_slides.renderer_v2.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
