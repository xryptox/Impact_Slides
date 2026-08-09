"""Allowlisted non-strict repairs (D123 / D311 kernel subset)."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from .diagnostics import DiagnosticEvent, event

RepairFn = Callable[[Any, list[DiagnosticEvent]], Any]


def assume_schema_v1(raw: Any, events: list[DiagnosticEvent]) -> Any:
    """Insert handoff_schema_version:1 when meta exists without version (D311)."""
    if not isinstance(raw, dict):
        return raw
    meta = raw.get("meta")
    if not isinstance(meta, dict):
        return raw
    if "handoff_schema_version" in meta:
        return raw
    # Only when no other top-level keys look legacy and meta is otherwise empty/minimal.
    legacy_markers = {
        "presentation",
        "theme",
        "config",
        "assets",
        "layout",
        "visual_spec",
    }
    if legacy_markers.intersection(raw):
        return raw
    if any(k != "handoff_schema_version" for k in meta):
        # meta has other unknown keys — not a clean assume
        return raw
    out = deepcopy(raw)
    out["meta"] = {**meta, "handoff_schema_version": 1}
    events.append(
        event(
            code="repair.schema_version_assumed",
            severity="warning",
            phase="repair",
            role="deck_meta",
            path="/meta/handoff_schema_version",
            action="assume_schema_v1",
            result="canonicalized",
            expected="meta.handoff_schema_version == 1",
        )
    )
    return out


def drop_unknown_fields(raw: Any, events: list[DiagnosticEvent]) -> Any:
    """Drop unknown fields on closed deck envelope and known slide shapes.

    Kernel allowlist only — never invents business content (D123).
    """
    if not isinstance(raw, dict):
        return raw
    out = deepcopy(raw)
    _drop_unknown_object(
        out,
        allowed={"meta", "sections", "number_formats", "evidence_registry", "slides"},
        path="",
        events=events,
        role="deck",
    )
    meta = out.get("meta")
    if isinstance(meta, dict):
        _drop_unknown_object(
            meta,
            allowed={"handoff_schema_version"},
            path="/meta",
            events=events,
            role="deck_meta",
        )
    sections = out.get("sections")
    if isinstance(sections, list):
        for i, sec in enumerate(sections):
            if isinstance(sec, dict):
                _drop_unknown_object(
                    sec,
                    allowed={"section_id", "label"},
                    path=f"/sections/{i}",
                    events=events,
                    role="section",
                )
    slides = out.get("slides")
    if isinstance(slides, list):
        for i, slide in enumerate(slides):
            if not isinstance(slide, dict):
                continue
            layout = slide.get("layout_type")
            common = {
                "slide_number",
                "layout_type",
                "payload",
                "speaker_notes",
                "evidence_ids",
            }
            if layout in ("opening_cover", "closing_cover"):
                allowed = common
            elif layout == "narrative":
                allowed = common | {
                    "section_id",
                    "title",
                    "content",
                    "takeaway",
                    "disclosure",
                    "source_footer",
                }
            else:
                # Unknown/unimplemented layout: only strip truly global noise keys
                allowed = common | {
                    "section_id",
                    "title",
                    "content",
                    "takeaway",
                    "disclosure",
                    "source_footer",
                }
            _drop_unknown_object(
                slide,
                allowed=allowed,
                path=f"/slides/{i}",
                events=events,
                role="slide",
                slide_number=slide.get("slide_number")
                if isinstance(slide.get("slide_number"), int)
                else None,
                layout_type=layout if isinstance(layout, str) else None,
            )
            payload = slide.get("payload")
            if isinstance(payload, dict) and layout in (
                "opening_cover",
                "closing_cover",
            ):
                _drop_unknown_object(
                    payload,
                    allowed={"title", "subtitle", "period_label", "date_label"},
                    path=f"/slides/{i}/payload",
                    events=events,
                    role="cover_payload",
                    slide_number=slide.get("slide_number")
                    if isinstance(slide.get("slide_number"), int)
                    else None,
                    layout_type=layout,
                )
            if isinstance(payload, dict) and layout == "narrative":
                _drop_unknown_object(
                    payload,
                    allowed={"blocks", "typography"},
                    path=f"/slides/{i}/payload",
                    events=events,
                    role="narrative_payload",
                    slide_number=slide.get("slide_number")
                    if isinstance(slide.get("slide_number"), int)
                    else None,
                    layout_type=layout,
                )
    return out


def _drop_unknown_object(
    obj: dict[str, Any],
    *,
    allowed: set[str],
    path: str,
    events: list[DiagnosticEvent],
    role: str,
    slide_number: int | None = None,
    layout_type: str | None = None,
) -> None:
    unknown = [k for k in list(obj.keys()) if k not in allowed]
    for key in unknown:
        del obj[key]
        events.append(
            event(
                code="repair.field_dropped",
                severity="warning",
                phase="repair",
                role=role,
                path=f"{path}/{key}" if path else f"/{key}",
                action="drop_field",
                result="dropped",
                slide_number=slide_number,
                layout_type=layout_type,
                expected=f"closed object fields: {sorted(allowed)}",
                input_meta={"field": key},
            )
        )


# Closed registry: name → transform (D123).
REPAIR_REGISTRY: dict[str, RepairFn] = {
    "assume_schema_v1": assume_schema_v1,
    "drop_unknown_fields": drop_unknown_fields,
}


def apply_allowlisted_repairs(raw: Any) -> tuple[Any, list[DiagnosticEvent]]:
    """Apply every kernel allowlisted repair in stable order; collect events."""
    events: list[DiagnosticEvent] = []
    current = raw
    for name in ("assume_schema_v1", "drop_unknown_fields"):
        current = REPAIR_REGISTRY[name](current, events)
    return current, events
