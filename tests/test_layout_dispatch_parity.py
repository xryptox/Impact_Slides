"""Dispatch registry parity — every LAYOUT_RECIPES key routes to its recipe.

The old harness patched ``recipes.render_*`` and inspected which mock ran.
That works against an if-ladder (name resolved at call time) but not against
LAYOUT_RECIPES, which binds callables at import time. Patch the registry.
"""
from __future__ import annotations

import functools
import inspect
from unittest.mock import MagicMock

from impact_slides.renderer_v2.layout import dispatch
from impact_slides.renderer_v2.layout.dispatch import (
    LAYOUT_RECIPES,
    _PASSES_CHARTJS,
    render_slide,
)


def _base_name(fn) -> str:
    target = fn.func if isinstance(fn, functools.partial) else fn
    return target.__name__


def test_every_layout_routes_to_its_recipe():
    """Each registry key calls the recipe it maps to (unwrap partials)."""
    original = dict(LAYOUT_RECIPES)
    try:
        for lt, fn in original.items():
            mock = MagicMock(return_value=f"<!--{lt}-->")
            if isinstance(fn, functools.partial):
                # Keep bound kwargs (e.g. divider=True).
                dispatch.LAYOUT_RECIPES[lt] = functools.partial(mock, **fn.keywords)
            else:
                dispatch.LAYOUT_RECIPES[lt] = mock

            slide = {"slide_number": 1, "layout_type": lt, "title": lt, "content": {}}
            render_slide(slide, total=1, notes="")
            assert mock.called, f"{lt} ({_base_name(fn)}): recipe not called"
            if isinstance(fn, functools.partial) and fn.keywords:
                _, kwargs = mock.call_args
                for k, v in fn.keywords.items():
                    assert kwargs.get(k) == v, f"{lt}: missing bound kwarg {k}={v}"
    finally:
        dispatch.LAYOUT_RECIPES.clear()
        dispatch.LAYOUT_RECIPES.update(original)


def test_passes_chartjs_matches_recipe_signatures():
    """_PASSES_CHARTJS must equal layouts whose recipe accepts use_chartjs=."""
    accepts: set[str] = set()
    for lt, fn in LAYOUT_RECIPES.items():
        target = fn.func if isinstance(fn, functools.partial) else fn
        if "use_chartjs" in inspect.signature(target).parameters:
            accepts.add(lt)
    assert _PASSES_CHARTJS == frozenset(accepts)
