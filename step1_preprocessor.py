#!/usr/bin/env python3
"""Compatibility shim — canonical preprocessor is step1_preprocessor_v4.py.

Historical v1 implementation lives under wiki/legacy/step1_preprocessor.py.
Kept at repo root so existing tests (`import step1_preprocessor`) and docs keep working.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_LEGACY = Path(__file__).resolve().parent / "wiki" / "legacy" / "step1_preprocessor.py"
_spec = importlib.util.spec_from_file_location("step1_preprocessor", _LEGACY)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load legacy module from {_LEGACY}")
_mod = importlib.util.module_from_spec(_spec)
sys.modules[__name__] = _mod
sys.modules["step1_preprocessor"] = _mod
_spec.loader.exec_module(_mod)

if __name__ == "__main__":
    # Re-dispatch CLI if the legacy module exposes main-style prep via __main__
    import runpy
    runpy.run_path(str(_LEGACY), run_name="__main__")
