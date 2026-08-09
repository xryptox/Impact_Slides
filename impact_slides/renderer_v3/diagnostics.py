"""D309/D310 diagnostic events and typed failure reports."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["info", "warning", "error"]
Phase = Literal["validation", "repair", "plan", "paint", "readiness", "publication"]

# Closed catalog subset used by the schema-v1 kernel (D310).
VALIDATION_CODES = frozenset(
    {
        "validation.schema_version",
        "validation.configuration",
        "validation.required",
        "validation.unknown_field",
        "validation.inapplicable_field",
        "validation.type",
        "validation.value",
        "validation.cardinality",
        "validation.identity",
        "validation.reference",
        "validation.structure",
        "validation.conflict",
        "validation.fit",
        "validation.accessibility",
    }
)
REPAIR_CODES = frozenset(
    {
        "repair.schema_version_assumed",
        "repair.field_dropped",
        "repair.item_dropped",
        "repair.reference_dropped",
        "repair.id_generated",
        "repair.position_repaired",
        "repair.value_to_missing",
        "repair.value_canonicalized",
        "repair.prose_flattened",
        "repair.format_dropped",
        "repair.domain_replaced",
        "repair.axis_restored",
        "repair.policy_defaulted",
        "repair.color_substituted",
        "repair.sync_disabled",
        "repair.structure_flattened",
        "repair.chrome_omitted",
        "repair.locator_dropped",
    }
)
# Kernel emits validation + repair only; plan/paint codes arrive with those phases.
CLOSED_CODES = VALIDATION_CODES | REPAIR_CODES
DiagnosticCode = Literal[
    "validation.schema_version",
    "validation.configuration",
    "validation.required",
    "validation.unknown_field",
    "validation.inapplicable_field",
    "validation.type",
    "validation.value",
    "validation.cardinality",
    "validation.identity",
    "validation.reference",
    "validation.structure",
    "validation.conflict",
    "validation.fit",
    "validation.accessibility",
    "repair.schema_version_assumed",
    "repair.field_dropped",
    "repair.item_dropped",
    "repair.reference_dropped",
    "repair.id_generated",
    "repair.position_repaired",
    "repair.value_to_missing",
    "repair.value_canonicalized",
    "repair.prose_flattened",
    "repair.format_dropped",
    "repair.domain_replaced",
    "repair.axis_restored",
    "repair.policy_defaulted",
    "repair.color_substituted",
    "repair.sync_disabled",
    "repair.structure_flattened",
    "repair.chrome_omitted",
    "repair.locator_dropped",
]

ActionName = Literal[
    "assume_schema_v1",
    "drop_field",
    "drop_item",
    "drop_reference",
    "drop_optional_fact",
    "generate_positional_id",
    "pad_trailing_null",
    "drop_surplus_tail",
    "replace_with_missing",
    "collapse_equal_range",
    "flatten_prose_runs",
    "drop_format",
    "replace_domain",
    "restore_category_axis",
    "default_typography",
    "default_display",
    "substitute_theme_color",
    "disable_sync",
    "accept",
    "reject",
    "measure",
    "select_candidate",
    "reserve",
    "reallocate",
    "deduplicate",
    "suppress",
    "paint",
    "check_readiness",
    "publish",
    "rollback",
]
ResultName = Literal[
    "accepted",
    "failed",
    "canonicalized",
    "dropped",
    "missing",
    "generated",
    "defaulted",
    "substituted",
    "flattened",
    "independent",
    "relocated",
    "suppressed",
    "deduplicated",
    "fallback_semantic_table",
    "fallback_sequential",
    "fallback_complete_surface",
    "fallback_unresolved",
    "ready",
    "published",
    "rolled_back",
]


class DiagnosticAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: ActionName


class DiagnosticResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: ResultName


class DiagnosticExpected(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contract: str


class DiagnosticEvent(BaseModel):
    """One closed D309 diagnostic event."""

    model_config = ConfigDict(extra="forbid")
    code: DiagnosticCode
    severity: Severity
    phase: Phase
    role: str
    path: str
    action: DiagnosticAction
    result: DiagnosticResult
    occurrences: int = Field(default=1, ge=1)
    slide_number: Optional[int] = None
    layout_type: Optional[str] = None
    surface_id: Optional[str] = None
    expected: Optional[DiagnosticExpected] = None
    input: Optional[dict[str, Any]] = None


def event(
    *,
    code: DiagnosticCode,
    severity: Severity,
    phase: Phase,
    role: str,
    path: str,
    action: ActionName,
    result: ResultName,
    slide_number: int | None = None,
    layout_type: str | None = None,
    surface_id: str | None = None,
    expected: str | None = None,
    input_meta: dict[str, Any] | None = None,
    occurrences: int = 1,
) -> DiagnosticEvent:
    if code not in CLOSED_CODES:
        raise ValueError(f"diagnostic code not in closed catalog: {code!r}")
    return DiagnosticEvent(
        code=code,
        severity=severity,
        phase=phase,
        role=role,
        path=path,
        action=DiagnosticAction(name=action),
        result=DiagnosticResult(name=result),
        occurrences=occurrences,
        slide_number=slide_number,
        layout_type=layout_type,
        surface_id=surface_id,
        expected=DiagnosticExpected(contract=expected) if expected else None,
        input=input_meta,
    )


class RendererValidationError(Exception):
    """Handoff/schema validation failed before planning or publication (D312)."""

    def __init__(
        self,
        events: list[DiagnosticEvent],
        *,
        handoff_schema_version: int | None = 1,
        renderer_version: str = "3.0.0",
    ) -> None:
        self.status = "failed"
        self.ok = False
        self.renderer_version = renderer_version
        self.handoff_schema_version = handoff_schema_version
        self.events = list(events)
        self.severity_counts = _severity_counts(self.events)
        super().__init__(self._summary())

    def _summary(self) -> str:
        n = self.severity_counts.get("error", 0)
        return f"renderer validation failed with {n} error(s)"

    def to_report(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "ok": self.ok,
            "renderer_version": self.renderer_version,
            "handoff_schema_version": self.handoff_schema_version,
            "severity_counts": dict(self.severity_counts),
            "events": [e.model_dump(exclude_none=True) for e in self.events],
        }


def _severity_counts(events: list[DiagnosticEvent]) -> dict[str, int]:
    counts = {"info": 0, "warning": 0, "error": 0}
    for e in events:
        counts[e.severity] = counts.get(e.severity, 0) + e.occurrences
    return counts


def sort_events(events: list[DiagnosticEvent]) -> list[DiagnosticEvent]:
    """D309 deterministic order."""
    phase_order = {
        "validation": 0,
        "repair": 1,
        "plan": 2,
        "paint": 3,
        "readiness": 4,
        "publication": 5,
    }

    def key(e: DiagnosticEvent) -> tuple:
        return (
            phase_order.get(e.phase, 99),
            e.slide_number is not None,
            e.slide_number if e.slide_number is not None else -1,
            e.surface_id or "",
            e.role,
            e.path,
            e.code,
            e.action.name,
            e.result.name,
        )

    return sorted(events, key=key)


def merge_duplicate_events(events: list[DiagnosticEvent]) -> list[DiagnosticEvent]:
    """Coalesce identical events by incrementing occurrences (D309)."""
    buckets: dict[tuple, DiagnosticEvent] = {}
    order: list[tuple] = []
    for e in events:
        ident = (
            e.phase,
            e.slide_number,
            e.layout_type,
            e.surface_id,
            e.role,
            e.path,
            e.code,
            e.action.name,
            e.result.name,
        )
        if ident in buckets:
            prev = buckets[ident]
            buckets[ident] = prev.model_copy(
                update={"occurrences": prev.occurrences + e.occurrences}
            )
        else:
            buckets[ident] = e
            order.append(ident)
    return [buckets[k] for k in order]
