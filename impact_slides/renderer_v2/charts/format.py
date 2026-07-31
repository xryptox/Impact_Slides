"""Chart number formatting, palette, and scale helpers."""
from __future__ import annotations

import math
from typing import Any, Mapping



# MVP Chart.js interactive set (P3). Other chart layouts stay on SVG/pack.
# Boardroom series palette (semantic/brand — not Chart.js candy defaults).
_BOARDROOM_SERIES = (
    "#006fcf",  # blue / accent
    "#00175a",  # navy
    "#0a7d55",  # accent-2 success
    "#53565a",  # ink
    "#80c8ff",  # blue-sky
)


# Brand hex literals for JSON chart configs — mirror tokens.css (JSON can't
# consume CSS vars). Keep these as the single address for palette drift.
_NAVY = "#00175a"

_NAVY_SOFT = "#16294d"

_WHITE = "#ffffff"



def _series_color(index: int) -> str:
    return _BOARDROOM_SERIES[index % len(_BOARDROOM_SERIES)]



# ----------------------------------------------------------------------
# Internal vertical bar charts (grouped + stacked)
# ----------------------------------------------------------------------

# Default series palette as literal hex (mirrors tokens.css --navy/--blue/
# --blue-sky/--ink-muted). These flow into Chart.js JSON configs where CSS
# custom properties never resolve — a var(--...) string paints black on canvas.
# Hex is equally valid in the SVG fallback painters, so both paths agree.
# ponytail: theme overrides of --navy (F13) won't tint default-palette charts;
# resolve from theme tokens if/when a handoff-native theme ships.
_BAR_SERIES_COLORS = [
    "#00175a",
    "#006fcf",
    "#80c8ff",
    "#63666a",
]



def _series_colors(cfg: Mapping[str, Any]) -> list[str]:
    """Series color palette: chart_config.series_colors or the defaults."""
    custom = cfg.get("series_colors")
    if isinstance(custom, (list, tuple)) and custom:
        return [str(c) for c in custom if c] or list(_BAR_SERIES_COLORS)
    return list(_BAR_SERIES_COLORS)



def _fmt_unit(v: float, unit: str, pos: str = "suffix") -> str:
    """Format a value with its unit.

    Currency shorthand: a unit starting with ``$`` renders as a prefix
    (``$`` -> ``$1.6``, ``$B`` -> ``$1.6B``) regardless of ``pos``.
    """
    if not unit:
        return f"{v:g}"
    if pos == "prefix":
        return f"{unit}{v:g}"
    if unit.startswith("$"):
        return f"${v:g}{unit[1:]}"
    return f"{v:g}{unit}"



def _bar_num(v: Any) -> float | None:
    try:
        return float(str(v).replace("%", "").replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return None



def _fmt_value_label(v: float, unit: str = "", pos: str = "") -> str:
    """Value label with unit. Currency-style units prefix ($1,251);
    percent-style suffix (72%). Negatives parenthesized with the unit
    inside (($73), IR). ``pos`` (y_axis_unit_position) overrides the
    default (prefix unless the unit ends with ``%``).

    Shared by the stacked, grouped-bar, and SVG bar label paths (T14) —
    the fourth instance of a declared key honoured on only some paths.

    Compound currency units SPLIT around the number ($0.9B, $1,223M): the
    symbol leads and the magnitude suffix trails, which is how ``_fmt_bar``
    has always painted axis ticks. Treating the unit as atomic would give
    ``$B0.9`` and, worse, disagree with the ticks on the very same chart.

    Number formatting follows the axis-tick rule (``:g`` under 1000, comma
    thousands above) rather than the stacked path's former ``.1f``. The two
    only ever disagreed on fractional values >= 1000, where the old stacked
    rule dropped the thousands comma (``$1275.5`` vs ``$1,276``); no shipped
    deck carries such a value. Small magnitudes now keep their precision
    (0.05 stays 0.05 instead of rounding to 0.1).
    """
    neg = v < 0
    a = abs(v)
    n = f"{a:,.0f}" if a >= 1000 else f"{a:g}"
    if not unit:
        core = n
    elif unit.startswith("$"):
        # "$" -> $12 · "$B" -> $12B (symbol leads, magnitude trails).
        # An explicit suffix request still wins: pos="suffix" -> 12$.
        core = f"{n}{unit}" if pos == "suffix" else f"${n}{unit[1:]}"
    elif pos == "prefix":
        core = f"{unit}{n}"
    else:
        # Non-currency units trail by default (72%, 9bps).
        core = f"{n}{unit}"
    return f"({core})" if neg else core



def _fmt_bar(v: float, unit: str = "") -> str:
    """Axis-tick label. Shares :func:`_fmt_value_label`'s unit placement and
    magnitude rules so ticks and value labels on the same chart can never
    disagree (T14).

    Ticks differ from value labels in one respect: a negative tick keeps a
    plain signed number rather than IR parentheses. The sign sits where it
    always has — inside a currency prefix (``$-73``), which looks odd but is
    long-standing axis output and not this ticket's to change.
    """
    s = f"{v:,.0f}" if abs(v) >= 1000 else f"{v:g}"
    if not unit:
        return s
    if unit.startswith("$"):
        return f"${s}{unit[1:]}"
    return f"{s}{unit}"



def _fmt_chart_num(v: float) -> str:
    """Compact whole-preferring number for chart labels."""
    if abs(v - round(v)) < 1e-6:
        return f"{int(round(v))}"
    if abs(v) >= 100:
        return f"{v:.0f}"
    return f"{v:.1f}".rstrip("0").rstrip(".")



def _nice_max(raw: float) -> float:
    if raw <= 0:
        return 1.0
    exp = math.floor(math.log10(raw))
    base = 10**exp
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if raw <= m * base:
            return float(m * base)
    return float(10 * base)



def _nice_step(raw: float) -> float:
    """Round a tick step to a clean 1/2/2.5/5 number."""
    if raw <= 0:
        return 1.0
    exp = math.floor(math.log10(raw))
    base = 10**exp
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * base:
            return float(m * base)
    return float(10 * base)
