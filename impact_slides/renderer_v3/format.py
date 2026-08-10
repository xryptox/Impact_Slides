"""Decimal-safe number formatting (D70/D77/D78/D103/D213/D214/D293)."""
from __future__ import annotations

import decimal
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Literal, Mapping

from .models import NumberFormat, SemanticValue

# Visible missing token + accessible name (D103/D78).
MISSING_VISIBLE = "\u2014"  # em dash
MISSING_ACCESSIBLE = "Missing"

_UNIT_VISIBLE: dict[str, tuple[str, str]] = {
    # unit -> (prefix, suffix) — placement is intrinsic (D293).
    "usd": ("$", ""),
    "percent": ("", "%"),
    "percentage_points": ("", " pp"),
    "basis_points": ("", " bps"),
}
_UNIT_ACCESSIBLE: dict[str, str] = {
    "usd": "US dollars",
    "percent": "percent",
    "percentage_points": "percentage points",
    "basis_points": "basis points",
}


@dataclass(frozen=True)
class FormattedValue:
    """One preformatted fact shared by paint and accessibility."""

    visible: str
    accessible: str
    role: Literal["number", "text", "missing", "range"]
    align: Literal["left", "right"]


def format_semantic_value(
    value: SemanticValue | Any,
    formats: Mapping[str, NumberFormat],
) -> FormattedValue:
    """Format one D213 tagged value through the deck registry."""
    kind = getattr(value, "type", None)
    if kind == "missing":
        return FormattedValue(
            visible=MISSING_VISIBLE,
            accessible=MISSING_ACCESSIBLE,
            role="missing",
            align="right",
        )
    if kind == "text":
        text = value.text
        return FormattedValue(visible=text, accessible=text, role="text", align="left")
    if kind == "number":
        fmt = formats[value.format_id]
        vis, acc = _format_number(value.value, fmt)
        return FormattedValue(visible=vis, accessible=acc, role="number", align="right")
    if kind == "range":
        fmt = formats[value.format_id]
        lo_v, lo_a = _format_number(value.lower, fmt)
        hi_v, hi_a = _format_number(value.upper, fmt)
        return FormattedValue(
            visible=f"{lo_v}\u2013{hi_v}",
            accessible=f"{lo_a} to {hi_a}",
            role="range",
            align="right",
        )
    raise TypeError(f"unsupported semantic value: {type(value)!r}")


def _format_number(raw: str, fmt: NumberFormat) -> tuple[str, str]:
    """Scale, round half-away-from-zero, unit, negative style (D77/D293)."""
    try:
        amount = Decimal(raw)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid canonical decimal {raw!r}") from exc

    scale = Decimal(fmt.value_scale) if fmt.value_scale is not None else Decimal(1)
    precision = (
        len(amount.as_tuple().digits)
        + len(scale.as_tuple().digits)
        + fmt.value_decimals
        + 6
    )
    try:
        with decimal.localcontext() as ctx:
            ctx.prec = precision
            scaled = amount * scale
            quant = Decimal(1).scaleb(-fmt.value_decimals)  # 10 ** -decimals
            # Half away from zero: quantize with ROUND_HALF_UP on the absolute
            # value, then re-apply sign. ROUND_HALF_UP is half-away for positives.
            negative = scaled < 0
            rounded = abs(scaled).quantize(quant, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"cannot format canonical decimal {raw!r}") from exc
    if rounded == 0:
        negative = False  # rounded zero is unsigned (D293)

    int_part, _, frac = f"{rounded:f}".partition(".")
    int_grouped = _group_thousands(int_part)
    if fmt.value_decimals > 0:
        frac = (frac + "0" * fmt.value_decimals)[: fmt.value_decimals]
        core = f"{int_grouped}.{frac}"
    else:
        core = int_grouped

    prefix, suffix = ("", "")
    accessible_unit = ""
    if fmt.unit is not None:
        prefix, suffix = _UNIT_VISIBLE[fmt.unit]
        accessible_unit = _UNIT_ACCESSIBLE[fmt.unit]

    signed_core = core
    if negative:
        if fmt.negative_style == "parentheses":
            # Whole-quantity negative style wraps unit+magnitude (D293).
            visible = f"({prefix}{core}{suffix})"
            accessible = f"negative {core}{(' ' + accessible_unit) if accessible_unit else ''}".rstrip()
            return visible, accessible
        signed_core = f"-{core}"

    visible = f"{prefix}{signed_core}{suffix}"
    if negative:
        accessible = f"negative {core}"
    else:
        accessible = core
    if accessible_unit:
        accessible = f"{accessible} {accessible_unit}"
    return visible, accessible


def _group_thousands(digits: str) -> str:
    if len(digits) <= 3:
        return digits
    parts: list[str] = []
    while digits:
        parts.append(digits[-3:])
        digits = digits[:-3]
    return ",".join(reversed(parts))



