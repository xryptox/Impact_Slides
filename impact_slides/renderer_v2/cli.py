"""CLI + render_deck entry for Impact Slide Renderer v2."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from . import features as features_mod
from .features import resolve_features
from .lib_inliner import DeliveryMode, build_head_assets, coerce_delivery
from .load import load_json, load_seed, normalize_handoff, present_meta
from .schemas import validate_handoff
from .layout.dispatch import render_slide
from .manifest import (
    build_manifest,
    validate_html,
    write_manifest,
    write_slide_notes_md,
)
from .notes import build_spoken_notes
from .shell import wrap_deck


def render_deck(
    handoff_path: str | Path,
    out_dir: str | Path,
    *,
    seed_path: str | Path | None = None,
    debug: bool = False,
    strict: bool = True,
    theme: dict[str, str] | None = None,
    delivery: DeliveryMode | str = DeliveryMode.SELF_CONTAINED,
    force_features: list[str] | None = None,
    suppress_features: list[str] | None = None,
) -> dict[str, Any]:
    """Render a Builder handoff to presentation.html + notes + manifest.

    ``delivery`` selects how third-party assets reach the deck:
    ``"self-contained"`` (default, offline-safe) or ``"cdn"`` (dev-only).

    Features are auto-detected from the handoff; ``force_features`` /
    ``suppress_features`` override (suppress beats force beats detect).

    Returns a result dict with paths and validation errors.
    """
    delivery = coerce_delivery(delivery)
    handoff_path = Path(handoff_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    raw = load_json(handoff_path)
    handoff = normalize_handoff(raw)
    validated_slides, validation_errors = validate_handoff(handoff)
    if validation_errors:
        for err in validation_errors:
            print(f"[validation] {err}", file=sys.stderr)
    _ = load_seed(seed_path)
    meta = present_meta(handoff)
    slides = handoff["slides"]
    total = len(slides)

    features = resolve_features(
        handoff,
        force=force_features or (),
        suppress=suppress_features or (),
    )
    features_list = sorted(features)
    bundle = build_head_assets(delivery, feature_ids=features_list)

    # Coerce slides list to contain validated models (fallback already applied)
    validated_lookup = {s.slide_number: s for s in validated_slides}
    _ = validated_lookup  # may be used for diagnostics later

    notes_by_num: dict[int, str] = {}
    bodies: list[str] = []
    for i, slide in enumerate(slides):
        n = int(slide.get("slide_number") or i + 1)
        next_title = ""
        if i + 1 < total:
            next_title = str(slides[i + 1].get("title") or "")
        prose = build_spoken_notes(slide, next_title)
        notes_by_num[n] = prose
        bodies.append(
            render_slide(slide, total=total, notes=prose, active=(i == 0))
        )

    html = wrap_deck(
        bodies,
        meta=meta,
        debug=debug,
        theme=theme,
        delivery=delivery,
        bundle=bundle,
        features_enabled=features_list,
    )
    html_path = out / "presentation.html"
    html_path.write_text(html, encoding="utf-8")
    html_bytes = html_path.stat().st_size
    if html_bytes >= features_mod.ADVISORY_HTML_BYTES:
        print(
            f"[size] presentation.html is {html_bytes} bytes "
            f"(advisory threshold {features_mod.ADVISORY_HTML_BYTES}); "
            f"features={features_list}",
            file=sys.stderr,
        )

    notes_path = out / "slide_notes.md"
    write_slide_notes_md(notes_path, slides, notes_by_num)

    manifest = build_manifest(handoff, slides, source_name=handoff_path.name)
    man_path = out / "evidence_manifest.json"
    write_manifest(man_path, manifest)

    run_meta = {
        "generator": "impact_slides.renderer_v2",
        "version": __version__,
        "style_preset": "BoardroomEarnings",
        "handoff": str(handoff_path),
        "total_slides": total,
        "delivery": delivery.value,
        "assets_inlined": list(bundle.meta.get("assets") or []),
        "features_enabled": features_list,
        "html_bytes": html_bytes,
        "bytes_inlined": int(bundle.meta.get("bytes_inlined") or 0),
        "layouts": [s.get("layout_type") for s in slides],
    }
    (out / "run_meta.json").write_text(
        json.dumps(run_meta, indent=2) + "\n", encoding="utf-8"
    )

    errors = validate_html(html, delivery=delivery)
    result = {
        "out_dir": str(out),
        "presentation": str(html_path),
        "slide_notes": str(notes_path),
        "manifest": str(man_path),
        "total_slides": total,
        "features_enabled": features_list,
        "html_bytes": html_bytes,
        "errors": errors,
        "ok": not errors,
    }
    if strict and errors:
        raise SystemExit(
            "renderer_v2 validation failed:\n- " + "\n- ".join(errors)
        )
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m impact_slides.renderer_v2",
        description=(
            "Boardroom Gridlines Renderer v2 — deterministic HTML deck paint. "
            "Default output is self-contained (offline-safe); --use-cdn is dev-only."
        ),
    )
    p.add_argument("--handoff", required=True, help="builder_handoff.json path")
    p.add_argument("--out", required=True, help="output directory")
    p.add_argument("--seed", default=None, help="evidence_register_seed.json (optional)")
    p.add_argument("--debug", action="store_true", help="outline gl-* regions")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--self-contained",
        dest="delivery",
        action="store_const",
        const=DeliveryMode.SELF_CONTAINED,
        help="embed all required assets (default; offline-safe)",
    )
    mode.add_argument(
        "--use-cdn",
        dest="delivery",
        action="store_const",
        const=DeliveryMode.CDN,
        help="reference third-party assets via CDN (dev only; not for customer/VPN decks)",
    )
    p.set_defaults(delivery=DeliveryMode.SELF_CONTAINED)
    p.add_argument(
        "--force-feature",
        action="append",
        default=[],
        metavar="ID",
        help="force-enable a feature id (repeatable); known: charts, mermaid, alpine, swiper, icons",
    )
    p.add_argument(
        "--suppress-feature",
        action="append",
        default=[],
        metavar="ID",
        help="suppress a feature id even if detected (repeatable); beats --force-feature",
    )
    p.add_argument(
        "--no-strict",
        action="store_true",
        help="do not exit non-zero on validation errors",
    )
    p.add_argument("--version", action="version", version=f"renderer_v2 {__version__}")
    args = p.parse_args(argv)

    try:
        result = render_deck(
            args.handoff,
            args.out,
            seed_path=args.seed,
            debug=args.debug,
            strict=not args.no_strict,
            delivery=args.delivery,
            force_features=args.force_feature,
            suppress_features=args.suppress_feature,
        )
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
            return 1
        raise
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"OK -> {result['presentation']} ({result['total_slides']} slides)")
    if result["errors"]:
        for err in result["errors"]:
            print(f"  warn: {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
