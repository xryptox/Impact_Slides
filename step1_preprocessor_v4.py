#!/usr/bin/env python3
"""Impact Slide Preprocessor v4 — thin shim (v4 Phase 4 refactor).

The implementation now lives in the ``impact_slides`` package:
  - ``impact_slides.preprocessor`` — the trunk class + module-level helpers
  - ``impact_slides.cli``          — ``main()``, ``test_preprocessor()``,
    ``inspect_register()``

This file remains so every existing ``import step1_preprocessor_v4`` and CLI
invocation (``python step1_preprocessor_v4.py --input ... --output ...``) keeps
working unchanged. Attribute access is forwarded to the package modules via
PEP 562 module ``__getattr__``, so the full namespace (the class, the helpers,
the tables, the optional-dep flags) is available without enumerating names.

If you are writing NEW code, prefer importing from the package directly:
    from impact_slides.preprocessor import ImpactSlidePreprocessorV4
    from impact_slides.cli import main
"""
from __future__ import annotations

import sys

# Eagerly import the trunk + cli so the package's public API and the CLI are
# available immediately. The leaves (text_utils, heuristics, ...) are imported
# transitively by preprocessor.py.
from impact_slides import preprocessor as _preprocessor
from impact_slides import cli as _cli

__version__ = _preprocessor.__version__


def main(argv=None):
    """CLI entry point — delegates to impact_slides.cli.main."""
    return _cli.main(argv)


def __getattr__(name):
    """PEP 562: forward any other attribute access to the trunk or cli module.

    This makes ``step1_preprocessor_v4.ImpactSlidePreprocessorV4``,
    ``step1_preprocessor_v4._SemanticDedupEngine``, ``step1_preprocessor_v4.clean_text``,
    ``step1_preprocessor_v4.CONFIG_DEFAULTS``, ``step1_preprocessor_v4.test_preprocessor``,
    ``step1_preprocessor_v4.inspect_register``, etc. all resolve to the package's
    definitions, so the 430-test suite (which does ``import step1_preprocessor_v4 as m``)
    keeps passing without a single edit.
    """
    if hasattr(_preprocessor, name):
        return getattr(_preprocessor, name)
    if hasattr(_cli, name):
        return getattr(_cli, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if __name__ == "__main__":
    sys.exit(main())
