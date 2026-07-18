"""Centralized inliner for vendored third-party assets (P0 foundation).

Single owner (SC-MOD-1) for how renderer_v2 embeds external CSS/JS/fonts into
generated decks. First-party Boardroom CSS lives in ``css/`` and stays separate.

Spec: wiki/SPEC_renderer_v2_p0_self_contained.md
"""
from __future__ import annotations

from enum import Enum


class DeliveryMode(str, Enum):
    """How required third-party assets reach the generated deck."""

    SELF_CONTAINED = "self-contained"
    CDN = "cdn"


def coerce_delivery(value: "DeliveryMode | str | None") -> DeliveryMode:
    """Normalize a delivery value, rejecting anything unknown."""
    if value is None:
        return DeliveryMode.SELF_CONTAINED
    if isinstance(value, DeliveryMode):
        return value
    try:
        return DeliveryMode(str(value))
    except ValueError:
        raise ValueError(
            f"invalid delivery {value!r}: expected "
            f"'{DeliveryMode.SELF_CONTAINED.value}' or '{DeliveryMode.CDN.value}'"
        ) from None
