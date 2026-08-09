"""Validate raw handoff dicts into the canonical typed Deck (D120/D122)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from .diagnostics import (
    DiagnosticEvent,
    RendererValidationError,
    event,
    merge_duplicate_events,
    sort_events,
)
from .models import KERNEL_LAYOUTS, LAYOUT_TYPES, Deck
from .repairs import apply_allowlisted_repairs

_LAYOUT_SET = frozenset(LAYOUT_TYPES)


@dataclass
class ValidationResult:
    """Successful validation outcome: canonical model + diagnostics."""

    deck: Deck
    events: list[DiagnosticEvent] = field(default_factory=list)
    repaired: bool = False

    @property
    def ok(self) -> bool:
        return True


def validate_handoff(raw: Any, *, strict: bool = True) -> ValidationResult:
    """Validate a handoff into one canonical typed Deck.

    Strict: aggregate all detectable errors; raise RendererValidationError.
    Non-strict: apply allowlisted repairs only, revalidate, then succeed or fail.
    Painting must consume ``result.deck`` only — never the raw dict (D122).
    """
    events: list[DiagnosticEvent] = []

    if not isinstance(raw, dict):
        events.append(
            event(
                code="validation.type",
                severity="error",
                phase="validation",
                role="deck",
                path="/",
                action="reject",
                result="failed",
                expected="object deck envelope",
                input_meta={"type": type(raw).__name__},
            )
        )
        raise RendererValidationError(sort_events(events), handoff_schema_version=None)

    working = raw
    repaired = False
    if not strict:
        working, repair_events = apply_allowlisted_repairs(raw)
        if repair_events:
            repaired = True
            events.extend(repair_events)

    # Pre-model structural probes so we can aggregate without short-circuiting
    # on the first pydantic error alone.
    events.extend(_precheck(working))

    try:
        deck = Deck.model_validate(working)
    except ValidationError as exc:
        events.extend(_from_pydantic(exc, working))
        events = sort_events(merge_duplicate_events(events))
        # Keep only errors for the failure report when strict; repairs stay as warnings
        if strict or any(e.severity == "error" for e in events):
            # Drop pure-info; keep warnings+errors for report
            raise RendererValidationError(
                [e for e in events if e.severity in ("error", "warning")],
                handoff_schema_version=_peek_version(working),
            ) from None
        raise AssertionError("unreachable") from None

    # Post-validate: reject non-kernel layouts that somehow passed (none should)
    for s in deck.slides:
        if s.layout_type not in KERNEL_LAYOUTS:
            events.append(
                event(
                    code="validation.structure",
                    severity="error",
                    phase="validation",
                    role="slide",
                    path=f"/slides/{_slide_index(working, s.slide_number)}",
                    action="reject",
                    result="failed",
                    slide_number=s.slide_number,
                    layout_type=s.layout_type,
                    expected=f"kernel layouts: {sorted(KERNEL_LAYOUTS)}",
                )
            )

    errors = [e for e in events if e.severity == "error"]
    if errors:
        raise RendererValidationError(
            sort_events(merge_duplicate_events(events)),
            handoff_schema_version=deck.meta.handoff_schema_version,
        )

    # Successful path: strip validation errors that were repaired away — keep repairs.
    kept = [e for e in events if e.severity != "error"]
    return ValidationResult(
        deck=deck,
        events=sort_events(merge_duplicate_events(kept)),
        repaired=repaired,
    )


def _peek_version(raw: Any) -> int | None:
    if isinstance(raw, dict):
        meta = raw.get("meta")
        if isinstance(meta, dict):
            v = meta.get("handoff_schema_version")
            if isinstance(v, int):
                return v
    return None


def _slide_index(raw: Any, number: int) -> int:
    if isinstance(raw, dict) and isinstance(raw.get("slides"), list):
        for i, s in enumerate(raw["slides"]):
            if isinstance(s, dict) and s.get("slide_number") == number:
                return i
    return 0


def _precheck(raw: dict[str, Any]) -> list[DiagnosticEvent]:
    events: list[DiagnosticEvent] = []
    # Envelope keys
    required = {"meta", "sections", "number_formats", "evidence_registry", "slides"}
    for key in sorted(required - set(raw)):
        events.append(
            event(
                code="validation.required",
                severity="error",
                phase="validation",
                role="deck",
                path=f"/{key}",
                action="reject",
                result="failed",
                expected="required deck envelope field",
            )
        )
    for key in sorted(set(raw) - required):
        events.append(
            event(
                code="validation.unknown_field",
                severity="error",
                phase="validation",
                role="deck",
                path=f"/{key}",
                action="reject",
                result="failed",
                expected="closed deck envelope",
                input_meta={"field": key},
            )
        )

    meta = raw.get("meta")
    if isinstance(meta, dict):
        ver = meta.get("handoff_schema_version", _MISSING)
        if ver is _MISSING:
            events.append(
                event(
                    code="validation.schema_version",
                    severity="error",
                    phase="validation",
                    role="deck_meta",
                    path="/meta/handoff_schema_version",
                    action="reject",
                    result="failed",
                    expected="handoff_schema_version == 1",
                )
            )
        elif not isinstance(ver, int) or isinstance(ver, bool) or ver != 1:
            events.append(
                event(
                    code="validation.schema_version",
                    severity="error",
                    phase="validation",
                    role="deck_meta",
                    path="/meta/handoff_schema_version",
                    action="reject",
                    result="failed",
                    expected="handoff_schema_version == 1",
                    input_meta={
                        "type": type(ver).__name__,
                        "value": ver
                        if isinstance(ver, (int, str, bool)) or ver is None
                        else None,
                    },
                )
            )
        for key in sorted(set(meta) - {"handoff_schema_version"}):
            events.append(
                event(
                    code="validation.unknown_field",
                    severity="error",
                    phase="validation",
                    role="deck_meta",
                    path=f"/meta/{key}",
                    action="reject",
                    result="failed",
                    expected="meta contains only handoff_schema_version",
                    input_meta={"field": key},
                )
            )
    elif "meta" in raw:
        events.append(
            event(
                code="validation.type",
                severity="error",
                phase="validation",
                role="deck_meta",
                path="/meta",
                action="reject",
                result="failed",
                expected="object",
                input_meta={"type": type(meta).__name__},
            )
        )

    slides = raw.get("slides")
    if isinstance(slides, list):
        for i, slide in enumerate(slides):
            if not isinstance(slide, dict):
                events.append(
                    event(
                        code="validation.type",
                        severity="error",
                        phase="validation",
                        role="slide",
                        path=f"/slides/{i}",
                        action="reject",
                        result="failed",
                        expected="object",
                        input_meta={"type": type(slide).__name__},
                    )
                )
                continue
            layout = slide.get("layout_type")
            sn = slide.get("slide_number") if isinstance(slide.get("slide_number"), int) else None
            if layout is None:
                events.append(
                    event(
                        code="validation.required",
                        severity="error",
                        phase="validation",
                        role="slide",
                        path=f"/slides/{i}/layout_type",
                        action="reject",
                        result="failed",
                        slide_number=sn,
                        expected="layout_type discriminator",
                    )
                )
            elif layout not in _LAYOUT_SET:
                events.append(
                    event(
                        code="validation.value",
                        severity="error",
                        phase="validation",
                        role="slide",
                        path=f"/slides/{i}/layout_type",
                        action="reject",
                        result="failed",
                        slide_number=sn,
                        layout_type=str(layout) if isinstance(layout, str) else None,
                        expected="one of D210 closed composition vocabulary",
                        input_meta={
                            "type": type(layout).__name__,
                            "value": layout if isinstance(layout, (str, int, bool)) else None,
                        },
                    )
                )
            elif layout not in KERNEL_LAYOUTS:
                events.append(
                    event(
                        code="validation.structure",
                        severity="error",
                        phase="validation",
                        role="slide",
                        path=f"/slides/{i}/layout_type",
                        action="reject",
                        result="failed",
                        slide_number=sn,
                        layout_type=layout if isinstance(layout, str) else None,
                        expected=(
                            "kernel implements opening_cover, narrative, closing_cover; "
                            "other D210 compositions arrive in later tickets"
                        ),
                    )
                )
    elif "slides" in raw:
        events.append(
            event(
                code="validation.type",
                severity="error",
                phase="validation",
                role="deck",
                path="/slides",
                action="reject",
                result="failed",
                expected="non-empty array",
                input_meta={"type": type(slides).__name__},
            )
        )

    return events


_MISSING = object()


def _from_pydantic(exc: ValidationError, raw: dict[str, Any]) -> list[DiagnosticEvent]:
    events: list[DiagnosticEvent] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        path = _loc_to_path(loc)
        etype = err.get("type", "")
        msg = err.get("msg", "")
        code = _map_error_type(etype, msg, path)
        slide_number, layout_type = _slide_context(raw, loc)
        # Skip duplicates already raised by precheck for the same path+family
        events.append(
            event(
                code=code,
                severity="error",
                phase="validation",
                role=_role_for_path(path),
                path=path,
                action="reject",
                result="failed",
                slide_number=slide_number,
                layout_type=layout_type,
                expected=msg,
                input_meta=_safe_input(err.get("input")),
            )
        )
    return events


def _map_error_type(etype: str, msg: str, path: str) -> str:
    if "handoff_schema_version" in path or "schema_version" in etype:
        return "validation.schema_version"
    if etype == "extra_forbidden" or "Extra inputs" in msg:
        return "validation.unknown_field"
    if etype in {"missing", "missing_argument"}:
        return "validation.required"
    if etype.startswith("type_") or etype in {
        "bool_type",
        "int_type",
        "string_type",
        "list_type",
        "dict_type",
        "float_type",
        "model_type",
        "union_tag_invalid",
        "union_tag_not_found",
    }:
        return "validation.type"
    if etype in {
        "greater_than",
        "greater_than_equal",
        "less_than",
        "less_than_equal",
        "string_too_short",
        "string_too_long",
        "string_pattern_mismatch",
        "literal_error",
        "enum",
        "value_error",
    }:
        if "unique" in msg or "duplicate" in msg:
            return "validation.identity"
        if "unknown" in msg or "unresolved" in msg or "unused" in msg:
            return "validation.reference"
        if "order" in msg or "contiguous" in msg or "first" in msg or "last" in msg:
            return "validation.structure"
        return "validation.value"
    if etype == "too_short" or etype == "too_long":
        return "validation.cardinality"
    if "forbids" in msg or "inapplicable" in msg:
        return "validation.inapplicable_field"
    if "unique" in msg or "duplicate" in msg:
        return "validation.identity"
    if "unresolved" in msg or "unused" in msg or "unknown section" in msg:
        return "validation.reference"
    if "must be" in msg and ("first" in msg or "last" in msg or "order" in msg):
        return "validation.structure"
    return "validation.structure"


def _loc_to_path(loc: tuple[Any, ...]) -> str:
    parts: list[str] = []
    for p in loc:
        if isinstance(p, int):
            parts.append(str(p))
        else:
            # pydantic tagged-union injects the tag name as a loc segment — skip non-fields
            s = str(p)
            if s in KERNEL_LAYOUTS or s in _LAYOUT_SET:
                continue
            if s.startswith("function-") or s in {
                "tagged-union[OpeningCoverSlide,ClosingCoverSlide,NarrativeSlide]",
            }:
                continue
            parts.append(s)
    return "/" + "/".join(parts) if parts else "/"


def _role_for_path(path: str) -> str:
    if path.startswith("/meta"):
        return "deck_meta"
    if path.startswith("/sections"):
        return "section"
    if path.startswith("/number_formats"):
        return "number_format"
    if path.startswith("/evidence_registry"):
        return "evidence"
    if "/payload" in path:
        return "payload"
    if path.startswith("/slides"):
        return "slide"
    return "deck"


def _slide_context(
    raw: dict[str, Any], loc: tuple[Any, ...]
) -> tuple[int | None, str | None]:
    # loc like ('slides', 0, ...)
    if len(loc) >= 2 and loc[0] == "slides" and isinstance(loc[1], int):
        slides = raw.get("slides")
        if isinstance(slides, list) and 0 <= loc[1] < len(slides):
            s = slides[loc[1]]
            if isinstance(s, dict):
                sn = s.get("slide_number")
                lt = s.get("layout_type")
                return (
                    sn if isinstance(sn, int) else None,
                    lt if isinstance(lt, str) else None,
                )
    return None, None


def _safe_input(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    meta: dict[str, Any] = {"type": type(value).__name__}
    if isinstance(value, bool):
        meta["value"] = value
    elif isinstance(value, int) and not isinstance(value, bool):
        meta["value"] = value
    elif isinstance(value, float):
        meta["value"] = value
    elif isinstance(value, str):
        if len(value) <= 64 and value.isascii() and value.isprintable():
            # IDs / short tokens only — never long prose (D309)
            if len(value) <= 32:
                meta["value"] = value
            else:
                meta["length"] = len(value)
        else:
            meta["length"] = len(value)
    elif isinstance(value, (list, tuple, set)):
        meta["length"] = len(value)
    elif isinstance(value, dict):
        meta["length"] = len(value)
    return meta
