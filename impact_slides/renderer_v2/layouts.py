"""Single source of truth for ``layout_type`` vocabulary.

Before this module the catalog lived in four places — ``schemas.py`` Literals,
the ``dispatch.py`` if-ladder, ``charts._CHART_LAYOUTS`` / ``_CHARTJS_LAYOUTS``,
and ``load.COVER_LAYOUTS`` — so adding or renaming a layout meant four edits and
drift was silent. Everything importing from here keeps them in step.

``ALIASES`` maps accepted spellings onto their canonical layout. ``schemas.py``
has always validated ``metric`` and ``table`` (see
``tests/test_renderer_v2_validation.py``), but dispatch only matched the
canonical names, so an alias slide validated and then fell through to
``render_split`` — silently dropping ``key_stats``. Resolving aliases in one
place fixes that class of bug rather than the two known instances.
"""
from __future__ import annotations

# Layouts painted by the chart pack. ``icon_grid`` is a chart-pack layout but
# not a Chart.js one, hence its absence from CHARTJS_LAYOUTS below.
CHART_LAYOUTS = frozenset(
    {
        "grouped_bar_chart",
        "stacked_bar_chart",
        "horizontal_bar_chart",
        "waterfall_chart",
        "heatmap",
        "icon_grid",
        "line_chart",
        "combo_chart",
    }
)

# Chart layouts with a live Chart.js config; the rest fall back to inline SVG.
CHARTJS_LAYOUTS = frozenset(
    {
        "grouped_bar_chart",
        "stacked_bar_chart",
        "horizontal_bar_chart",
        "line_chart",
        "combo_chart",
    }
)

# Layouts that may legitimately occupy deck index 0 without normalize_handoff
# injecting a title_or_opening cover (#92/F6+).
COVER_LAYOUTS = frozenset({"title_or_opening", "brand_cover"})

# Accepted spelling -> canonical layout_type.
ALIASES = {
    "metric": "metric_dashboard",
    "table": "data_table",
    "cover": "title_or_opening",
}

# Sentinels meaning "no explicit layout" — callers infer from primary_visual.
UNSPECIFIED = frozenset({"", "default", "other"})

FALLBACK_LAYOUT = "split_text_visual"


def canonical(layout_type: str | None) -> str:
    """Normalise case/whitespace and resolve an alias to its canonical name.

    Returns ``""`` for unspecified layouts so callers can apply their own
    inference; unknown names pass through unchanged for the caller to reject.
    """
    lt = (layout_type or "").lower().strip()
    if lt in UNSPECIFIED:
        return ""
    return ALIASES.get(lt, lt)
