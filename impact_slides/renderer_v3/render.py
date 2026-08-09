"""Public render_deck API — validate, stage, publish (D125/D249/D250/D312)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

RENDERER_VERSION = "3.0.0"
from .diagnostics import (
    RendererConfigurationError,
    RendererPublicationError,
    RendererValidationError,
    event,
)
from .publish import (
    THEME_ID,
    publish_transaction,
    resolved_schema_source,
    stage_artifacts,
)
from .validate import validate_handoff

SELF_CONTAINED: Final = "self-contained"


def render_deck(
    handoff_path: str | Path,
    out_dir: str | Path,
    *,
    seed_path: str | Path | None = None,
    debug: bool = False,
    strict: bool = True,
    theme: Any = None,
    chrome_level: Any = None,
    delivery: str = SELF_CONTAINED,
    force_features: list[str] | None = None,
    suppress_features: list[str] | None = None,
) -> dict[str, Any]:
    """Render a schema-v1 handoff into the five canonical artifacts.

    Strict is the default. Failed calls raise a typed renderer error and leave
    prior output byte-identical. Successful returns include operational paths
    plus clean/degraded status (D112/D249/D250).
    """
    svg_only = _resolve_options(
        seed_path=seed_path,
        debug=debug,
        theme=theme,
        chrome_level=chrome_level,
        delivery=delivery,
        force_features=force_features,
        suppress_features=suppress_features,
    )

    handoff_path = Path(handoff_path)
    out = Path(out_dir)

    try:
        raw_text = handoff_path.read_text(encoding="utf-8")
        raw = json.loads(raw_text)
    except FileNotFoundError:
        raise RendererConfigurationError(
            [
                event(
                    code="validation.configuration",
                    severity="error",
                    phase="validation",
                    role="caller",
                    path="/handoff_path",
                    action="reject",
                    result="failed",
                    expected="existing handoff JSON path",
                    input_meta={"type": "missing"},
                )
            ],
            handoff_schema_version=None,
            renderer_version=RENDERER_VERSION,
        ) from None
    except json.JSONDecodeError as exc:
        raise RendererValidationError(
            [
                event(
                    code="validation.type",
                    severity="error",
                    phase="validation",
                    role="deck",
                    path="/",
                    action="reject",
                    result="failed",
                    expected="JSON object deck envelope",
                    input_meta={"type": "json_decode_error"},
                )
            ],
            handoff_schema_version=None,
            renderer_version=RENDERER_VERSION,
        ) from exc

    # validate_handoff raises RendererValidationError on failure — no writes yet.
    result = validate_handoff(raw, strict=strict)
    events = list(result.events)
    degraded = bool(result.repaired) or any(
        e.severity in ("warning", "error") for e in events
    )
    status = "degraded" if degraded else "clean"
    ok = not degraded

    schema_src = resolved_schema_source()
    if not schema_src.is_file():
        raise RendererPublicationError(
            [
                event(
                    code="publication.transaction_failed",
                    severity="error",
                    phase="publication",
                    role="publisher",
                    path="/handoff_schema_v1.json",
                    action="publish",
                    result="failed",
                    expected="checked-in D121 schema artifact",
                )
            ],
            handoff_schema_version=result.deck.meta.handoff_schema_version,
            renderer_version=RENDERER_VERSION,
        )

    artifacts = stage_artifacts(
        deck=result.deck,
        status=status,
        ok=ok,
        strict=strict,
        debug=bool(debug),
        svg_only=svg_only,
        events=events,
        schema_source=schema_src,
    )
    publish_transaction(out, artifacts)

    # D249: stable diagnostic codes only (not free-form validator strings).
    codes = sorted({e.code for e in events if e.severity in ("error", "warning")})

    severity = {"info": 0, "warning": 0, "error": 0}
    for e in events:
        severity[e.severity] = severity.get(e.severity, 0) + e.occurrences

    return {
        "out_dir": str(out),
        "presentation": str(out / "presentation.html"),
        "slide_notes": str(out / "slide_notes.md"),
        "evidence_manifest": str(out / "evidence_manifest.json"),
        "run_meta": str(out / "run_meta.json"),
        "handoff_schema": str(out / "handoff_schema_v1.json"),
        "status": status,
        "ok": ok,
        "renderer_version": RENDERER_VERSION,
        "handoff_schema_version": result.deck.meta.handoff_schema_version,
        "theme_id": THEME_ID,
        "slide_count": len(result.deck.slides),
        "severity_counts": severity,
        "errors": codes,
    }


def _resolve_options(
    *,
    seed_path: Any,
    debug: Any,
    theme: Any,
    chrome_level: Any,
    delivery: Any,
    force_features: Any,
    suppress_features: Any,
) -> bool:
    """Accept only the narrow D249 configuration; return svg_only flag."""
    problems: list[tuple[str, str]] = []

    if seed_path is not None:
        problems.append(("/seed_path", "seed_path must be None"))
    if theme is not None:
        problems.append(("/theme", "theme must be None"))
    if chrome_level is not None:
        problems.append(("/chrome_level", "chrome_level must be None"))
    if delivery != SELF_CONTAINED:
        problems.append(("/delivery", f"delivery must be {SELF_CONTAINED!r}"))
    if force_features not in (None, [], ()):
        problems.append(("/force_features", "force_features must be absent or empty"))
    if not isinstance(debug, bool):
        problems.append(("/debug", "debug must be bool"))

    svg_only = False
    if suppress_features in (None, [], ()):
        svg_only = False
    elif list(suppress_features) == ["charts"]:
        svg_only = True
    else:
        problems.append(
            ("/suppress_features", "suppress_features must be absent, empty, or ['charts']")
        )

    if problems:
        events = [
            event(
                code="validation.configuration",
                severity="error",
                phase="validation",
                role="caller",
                path=path,
                action="reject",
                result="failed",
                expected=expected,
            )
            for path, expected in problems
        ]
        raise RendererConfigurationError(
            events,
            handoff_schema_version=None,
            renderer_version=RENDERER_VERSION,
        )
    return svg_only
