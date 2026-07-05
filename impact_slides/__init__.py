"""Impact Slide Preprocessor v4 — modular package.

This package is the modularized successor to the monolithic
``step1_preprocessor_v4.py``. The original entry point still works as a thin
shim that delegates here, so existing CLI usage and ``import
step1_preprocessor_v4`` are unchanged.

Submodules:
  - schemas            — Pydantic contracts (single source of truth for outputs)
  - analyst_briefing   — Narrative Readiness + Focus Area generator (v4 #26)
  - text_utils         — text/Excel value helpers
  - heuristics         — column/cell heuristics + sheet-time-rank
  - text_analysis      — insight-language detection + priority scoring
  - logging_setup      — centralized logger factory + git provenance
  - config             — YAML config resolution + validation
  - dedup              — tiered semantic dedup engine
  - stage_mapping      — Why/What/How/Now stage rules
  - cross_file         — cross-file entity matching
  - spreadsheet_extract / pptx_extract / pdf_extract / docx_extract
  - preprocessor       — the trunk (orchestrator + evidence builder)
  - cli                — argparse entry point + main()
"""
from __future__ import annotations

__version__ = "4.0.0"


def __getattr__(name):
    # Lazy import so the leaf modules (text_utils, heuristics, ...) are usable
    # without importing the heavy preprocessor trunk (which pulls in pandas +
    # every optional dependency). `ImpactSlidePreprocessor` resolves on demand.
    if name == "ImpactSlidePreprocessor":
        from .preprocessor import ImpactSlidePreprocessor as _P
        return _P
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ImpactSlidePreprocessor", "__version__"]
