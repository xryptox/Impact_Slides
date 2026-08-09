"""CLI for renderer_v3: render decks or manage the schema artifact (D125/D249)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .diagnostics import (
    RendererConfigurationError,
    RendererPublicationError,
    RendererValidationError,
)
from .render import render_deck
from .schema_export import main as schema_main


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m impact_slides.renderer_v3",
        description=(
            "Impact Slide Renderer v3 — schema-v1 deterministic deck publication. "
            "Default mode is strict self-contained render."
        ),
    )
    p.add_argument("--version", action="version", version=f"renderer_v3 {__version__}")

    sub = p.add_subparsers(dest="command")

    # schema subcommand keeps the #175 drift gate working.
    schema_p = sub.add_parser("schema", help="generate or check handoff JSON Schema")
    schema_p.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if committed schema drifts from models",
    )
    schema_p.add_argument(
        "--root",
        default=None,
        help="repository root (defaults to auto-detect)",
    )

    # Top-level render flags (D249): no CDN/theme/chrome/seed/arbitrary features.
    p.add_argument("--handoff", default=None, help="schema-v1 handoff JSON path")
    p.add_argument("--out", default=None, help="output directory")
    p.add_argument(
        "--no-strict",
        action="store_true",
        help="explicit non-strict recovery (degraded publication on repair)",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help="add deterministic inspection chrome only",
    )
    p.add_argument(
        "--svg-only",
        action="store_true",
        help="suppress Chart.js; SVG/static path (D248 test/dev selection)",
    )
    return p


def main(argv: Sequence[str] | None = None) -> int:
    argv_list = list(sys.argv[1:] if argv is None else argv)

    # Backward-compatible schema_export invocation:
    #   python -m impact_slides.renderer_v3.schema_export
    # and bare `--check` / no-args still route to schema tooling when no handoff.
    if argv_list and argv_list[0] == "schema":
        # Translate to schema_export main args.
        rest = argv_list[1:]
        return schema_main(rest)

    # Legacy: `python -m impact_slides.renderer_v3 --check` (schema only).
    if argv_list == ["--check"] or (
        argv_list
        and argv_list[0] == "--check"
        and "--handoff" not in argv_list
        and "--out" not in argv_list
    ):
        return schema_main(argv_list)

    if not argv_list:
        # Keep prior default: schema export write (used by local regen).
        return schema_main([])

    parser = build_parser()
    args = parser.parse_args(argv_list)

    if args.command == "schema":
        schema_argv: list[str] = []
        if args.check:
            schema_argv.append("--check")
        if args.root:
            schema_argv.extend(["--root", args.root])
        return schema_main(schema_argv)

    if not args.handoff or not args.out:
        parser.error("--handoff and --out are required to render")

    suppress = ["charts"] if args.svg_only else None
    try:
        result = render_deck(
            args.handoff,
            args.out,
            debug=bool(args.debug),
            strict=not bool(args.no_strict),
            suppress_features=suppress,
        )
    except RendererConfigurationError as exc:
        _print_failure(exc)
        return 1
    except RendererValidationError as exc:
        _print_failure(exc)
        return 1
    except RendererPublicationError as exc:
        _print_failure(exc)
        return 1

    if result["status"] == "degraded":
        _print_degraded(result)
        return 2
    return 0


def _print_failure(exc: RendererValidationError) -> None:
    """D309: one deterministic stderr line per warning/error (no free-form prose)."""
    for e in exc.to_report()["events"]:
        if e.get("severity") == "info":
            continue
        print(_diagnostic_line(e), file=sys.stderr)


def _print_degraded(result: dict) -> None:
    meta_path = result.get("run_meta")
    if not meta_path:
        return
    events = json.loads(Path(meta_path).read_text(encoding="utf-8")).get("events") or []
    for e in events:
        if e.get("severity") == "info":
            continue
        print(_diagnostic_line(e), file=sys.stderr)


def _diagnostic_line(e: dict) -> str:
    action = (e.get("action") or {}).get("name", "")
    result = (e.get("result") or {}).get("name", "")
    return (
        f"{e.get('severity')}	{e.get('code')}	{e.get('phase')}	"
        f"{e.get('path')}	{action}	{result}	occurrences={e.get('occurrences', 1)}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
