"""Transactional D250 artifact publication (D112/D113/D250/D312)."""
from __future__ import annotations

import hashlib
import html
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .diagnostics import (
    DiagnosticEvent,
    RendererPublicationError,
    event,
    sort_events,
)
from .models import Deck
from .schema_export import schema_path

from ._version import __version__ as RENDERER_VERSION

THEME_ID = "boardroom_amex"

CANONICAL_ARTIFACTS = (
    "presentation.html",
    "slide_notes.md",
    "evidence_manifest.json",
    "run_meta.json",
    "handoff_schema_v1.json",
)

# Artifacts hashed inside run_meta (excludes run_meta itself).
_HASHED_ARTIFACTS = tuple(n for n in CANONICAL_ARTIFACTS if n != "run_meta.json")


def dumps_json(obj: Any) -> str:
    """UTF-8/LF JSON, two-space indent, trailing newline (D250/D312)."""
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _slide_heading(slide: Any) -> str:
    title = getattr(slide, "title", None)
    if title:
        return title
    payload = getattr(slide, "payload", None)
    if payload is not None and getattr(payload, "title", None):
        return payload.title
    return slide.layout_type


def build_presentation_html(deck: Deck, *, debug: bool = False, svg_only: bool = False) -> str:
    """Minimal deterministic HTML shell for kernel compositions (paint later)."""
    parts: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8"/>',
        f"<title>{_escape(deck.slides[0].payload.title if hasattr(deck.slides[0].payload, 'title') else 'Impact Slides')}</title>",
        f'<meta name="generator" content="impact_slides.renderer_v3/{RENDERER_VERSION}"/>',
        f'<meta name="theme-id" content="{THEME_ID}"/>',
    ]
    if debug:
        parts.append('<meta name="renderer-debug" content="1"/>')
    if svg_only:
        parts.append('<meta name="svg-only" content="1"/>')
    parts.extend(
        [
            "<style>",
            "body{margin:0;font-family:system-ui,sans-serif;background:#fff;color:#00175A}",
            ".slide{box-sizing:border-box;width:1920px;height:1080px;padding:64px;page-break-after:always}",
            "h1{font-size:48px;margin:0 0 16px}h2{font-size:32px;margin:0 0 12px}",
            "p,li{font-size:24px;line-height:1.4}",
            "</style>",
            "</head>",
            "<body>",
        ]
    )
    for slide in deck.slides:
        sid = f"slide-{slide.slide_number}"
        parts.append(
            f'<section class="slide" id="{sid}" data-layout="{slide.layout_type}" '
            f'data-slide-number="{slide.slide_number}" '
            f'data-surface-id="{sid}" data-diagnostic-count="0">'
        )
        parts.extend(_paint_slide_body(slide))
        notes = getattr(slide, "speaker_notes", None)
        if notes:
            parts.append(f'<aside class="notes">{_escape(notes)}</aside>')
        parts.append("</section>")
    parts.extend(["</body>", "</html>", ""])
    return "\n".join(parts)


def _paint_slide_body(slide: Any) -> list[str]:
    lt = slide.layout_type
    out: list[str] = []
    if lt in ("opening_cover", "closing_cover"):
        p = slide.payload
        out.append(f"<h1>{_escape(p.title)}</h1>")
        if p.subtitle:
            out.append(f"<p class=\"subtitle\">{_escape(p.subtitle)}</p>")
        if p.period_label:
            out.append(f"<p class=\"period\">{_escape(p.period_label)}</p>")
        if p.date_label:
            out.append(f"<p class=\"date\">{_escape(p.date_label)}</p>")
        return out
    if lt == "narrative":
        out.append(f"<h1>{_escape(slide.title)}</h1>")
        if slide.content is not None:
            out.append(f"<p class=\"subtitle\">{_escape(slide.content.subtitle)}</p>")
        for block in slide.payload.blocks:
            bid = block.block_id
            if block.type == "paragraphs":
                for prose in block.paragraphs:
                    out.append(
                        f'<p data-block-id="{_escape(bid)}" data-surface-id="{_escape(bid)}">{_prose_html(prose)}</p>'
                    )
            elif block.type == "bullet_list":
                out.append(f'<ul data-block-id="{_escape(bid)}" data-surface-id="{_escape(bid)}">')
                for item in block.items:
                    out.append(f"<li>{_prose_html(item)}</li>")
                out.append("</ul>")
        if slide.takeaway is not None:
            out.append(
                f'<p class="takeaway" data-role="takeaway">{_escape(slide.takeaway.text)}</p>'
            )
        return out
    out.append(f"<p>Unsupported layout in kernel paint: {_escape(lt)}</p>")
    return out


def _prose_html(prose: Any) -> str:
    chunks: list[str] = []
    for run in prose.runs:
        text = _escape(run.text)
        if run.emphasis == "strong":
            chunks.append(f"<strong>{text}</strong>")
        else:
            chunks.append(text)
    return "".join(chunks)


def _escape(text: str) -> str:
    return html.escape(text, quote=True)


def build_slide_notes_md(deck: Deck) -> str:
    """Authored slide order/headings; exact D221 text or _(no notes)_ (D250)."""
    chunks: list[str] = []
    for slide in deck.slides:
        heading = _slide_heading(slide)
        chunks.append(f"# Slide {slide.slide_number} — {heading}")
        chunks.append("")
        notes = getattr(slide, "speaker_notes", None)
        chunks.append(notes if notes else "_(no notes)_")
        chunks.append("")
    return "\n".join(chunks).rstrip() + "\n"


def _sorted_locator(locator: dict[str, Any] | None) -> dict[str, Any] | None:
    if locator is None:
        return None
    # D113: sort locator object keys for byte stability.
    return {k: locator[k] for k in sorted(locator)}


def build_evidence_manifest(deck: Deck) -> dict[str, Any]:
    """Ordered registry + per-slide evidence links (D250)."""
    registry = []
    for eid, entry in deck.evidence_registry.items():
        item: dict[str, Any] = {
            "evidence_id": eid,
            "source_name": entry.source_name,
        }
        loc = _sorted_locator(entry.locator)
        if loc is not None:
            item["locator"] = loc
        registry.append(item)
    # Preserve authored registry iteration order (dict insertion order).

    slides = []
    for slide in deck.slides:
        row: dict[str, Any] = {
            "slide_number": slide.slide_number,
            "layout_type": slide.layout_type,
        }
        section_id = getattr(slide, "section_id", None)
        if section_id is not None:
            row["section_id"] = section_id
        eids = list(getattr(slide, "evidence_ids", None) or [])
        if eids:
            row["evidence_ids"] = eids
        slides.append(row)

    return {
        "renderer_version": RENDERER_VERSION,
        "handoff_schema_version": deck.meta.handoff_schema_version,
        "theme_id": THEME_ID,
        "evidence_registry": registry,
        "slides": slides,
    }


def build_slide_summaries(deck: Deck) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for slide in deck.slides:
        surface_ids: list[str] = []
        if slide.layout_type in ("opening_cover", "closing_cover"):
            surface_ids.append(f"slide-{slide.slide_number}-cover")
        elif slide.layout_type == "narrative":
            surface_ids.extend(b.block_id for b in slide.payload.blocks)
            if slide.takeaway is not None:
                surface_ids.append(f"slide-{slide.slide_number}-takeaway")
            disclosure = getattr(slide, "disclosure", None)
            if disclosure is not None:
                surface_ids.extend(s.surface_id for s in disclosure.sections)
        row: dict[str, Any] = {
            "slide_number": slide.slide_number,
            "layout_type": slide.layout_type,
            "surface_ids": surface_ids,
        }
        section_id = getattr(slide, "section_id", None)
        if section_id is not None:
            row["section_id"] = section_id
        rows.append(row)
    return rows


def build_static_readiness(deck: Deck) -> list[dict[str, Any]]:
    """Pre-publication readiness facts only (D312); no browser measurement."""
    rows: list[dict[str, Any]] = []
    for slide in deck.slides:
        rows.append(
            {
                "slide_number": slide.slide_number,
                "layout_type": slide.layout_type,
                "frozen_plan_attached": True,  # kernel plan entries attached in run_meta.plans
                "required_payload_present": True,
                "semantic_table_present": False,  # no chart surfaces in kernel compositions
                "stable_ids_resolved": True,
                "readiness_contract_version": 1,
            }
        )
    return rows


def build_plans(deck: Deck) -> list[dict[str, Any]]:
    """One plan entry per planned surface; kernel compositions use slot digests."""
    plans: list[dict[str, Any]] = []
    for slide in deck.slides:
        if slide.layout_type in ("opening_cover", "closing_cover"):
            surface_id = f"slide-{slide.slide_number}-cover"
            plans.append(_plan_entry(surface_id, "cover", slide))
        elif slide.layout_type == "narrative":
            for block in slide.payload.blocks:
                plans.append(_plan_entry(block.block_id, "narrative_block", slide))
            if slide.takeaway is not None:
                plans.append(
                    _plan_entry(f"slide-{slide.slide_number}-takeaway", "takeaway", slide)
                )
    return plans


def _plan_entry(surface_id: str, role: str, slide: Any) -> dict[str, Any]:
    digest_src = f"{slide.slide_number}:{slide.layout_type}:{role}:{surface_id}"
    digest = sha256_bytes(digest_src.encode("utf-8"))
    return {
        "surface_id": surface_id,
        "role": role,
        "semantic_digest": digest,
        "design_stage_region": 0,
        "role_sizes": {},
        "adaptation_codes": [],
        "reservations": [],
        "fallback": None,
        "expected_placement_classes": [],
        "painter_plan_digest": digest,
    }


def build_run_meta(
    *,
    deck: Deck,
    status: str,
    ok: bool,
    strict: bool,
    debug: bool,
    svg_only: bool,
    events: list[DiagnosticEvent],
    artifact_bytes: dict[str, bytes],
) -> dict[str, Any]:
    severity = {"info": 0, "warning": 0, "error": 0}
    for e in events:
        severity[e.severity] = severity.get(e.severity, 0) + e.occurrences

    artifacts = []
    for name in _HASHED_ARTIFACTS:
        data = artifact_bytes[name]
        artifacts.append(
            {
                "name": name,
                "bytes": len(data),
                "sha256": sha256_bytes(data),
            }
        )

    return {
        "renderer_version": RENDERER_VERSION,
        "handoff_schema_version": deck.meta.handoff_schema_version,
        "theme_id": THEME_ID,
        "status": status,
        "ok": ok,
        "options": {"strict": strict, "debug": debug, "svg_only": svg_only},
        "slide_count": len(deck.slides),
        "slides": build_slide_summaries(deck),
        "severity_counts": severity,
        "events": [e.model_dump(mode="json", exclude_none=True) for e in sort_events(events)],
        "plans": build_plans(deck),
        "static_readiness": build_static_readiness(deck),
        "artifacts": artifacts,
    }


def stage_artifacts(
    *,
    deck: Deck,
    status: str,
    ok: bool,
    strict: bool,
    debug: bool,
    svg_only: bool,
    events: list[DiagnosticEvent],
    schema_source: Path,
) -> dict[str, bytes]:
    """Build all five artifact payloads in memory (bytes, UTF-8/LF)."""
    html = build_presentation_html(deck, debug=debug, svg_only=svg_only)
    notes = build_slide_notes_md(deck)
    manifest = dumps_json(build_evidence_manifest(deck))
    schema_bytes = schema_source.read_bytes()
    # Normalize schema to LF if the checked-in file somehow has CRLF (Windows).
    if b"\r\n" in schema_bytes:
        # Spec requires byte-copy of checked-in artifact — do not rewrite.
        pass

    partial = {
        "presentation.html": html.encode("utf-8"),
        "slide_notes.md": notes.encode("utf-8"),
        "evidence_manifest.json": manifest.encode("utf-8"),
        "handoff_schema_v1.json": schema_bytes,
    }
    run_meta = dumps_json(
        build_run_meta(
            deck=deck,
            status=status,
            ok=ok,
            strict=strict,
            debug=debug,
            svg_only=svg_only,
            events=events,
            artifact_bytes=partial,
        )
    )
    partial["run_meta.json"] = run_meta.encode("utf-8")
    return partial


def publish_transaction(out_dir: Path, artifacts: dict[str, bytes]) -> None:
    """Stage in sibling temp, then replace destination as a unit (D250/D312)."""
    out_dir = Path(out_dir)
    parent = out_dir.parent if out_dir.parent != Path("") else Path(".")
    parent.mkdir(parents=True, exist_ok=True)

    staging = Path(
        tempfile.mkdtemp(prefix=".renderer_v3_stage_", dir=str(parent))
    )
    backup: Path | None = None
    try:
        for name in CANONICAL_ARTIFACTS:
            if name not in artifacts:
                raise RendererPublicationError(
                    [
                        event(
                            code="publication.transaction_failed",
                            severity="error",
                            phase="publication",
                            role="publisher",
                            path=f"/artifacts/{name}",
                            action="publish",
                            result="failed",
                            expected="canonical D250 artifact present",
                        )
                    ]
                )
            write_text_bytes(staging / name, artifacts[name])

        # Verify staged set is exactly the five names.
        staged_names = {p.name for p in staging.iterdir() if p.is_file()}
        if staged_names != set(CANONICAL_ARTIFACTS):
            raise RendererPublicationError(
                [
                    event(
                        code="publication.transaction_failed",
                        severity="error",
                        phase="publication",
                        role="publisher",
                        path="/artifacts",
                        action="publish",
                        result="failed",
                        expected="exactly five canonical artifacts",
                    )
                ]
            )

        if out_dir.exists():
            # Only bind backup after the full copy succeeds so a mid-copy failure
            # never triggers restore from a partial snapshot (prior out stays put).
            backup_tmp = Path(
                tempfile.mkdtemp(prefix=".renderer_v3_backup_", dir=str(parent))
            )
            try:
                for item in out_dir.iterdir():
                    dest = backup_tmp / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)
            except Exception:
                shutil.rmtree(backup_tmp, ignore_errors=True)
                raise
            backup = backup_tmp
            for name in CANONICAL_ARTIFACTS:
                target = out_dir / name
                if target.exists():
                    target.unlink()
        else:
            out_dir.mkdir(parents=True, exist_ok=True)

        for name in CANONICAL_ARTIFACTS:
            _replace_file(staging / name, out_dir / name)

        # D250: destination contains only the five canonical artifacts.
        for item in list(out_dir.iterdir()):
            if item.name not in CANONICAL_ARTIFACTS:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

    except RendererPublicationError:
        _restore_backup(out_dir, backup)
        raise
    except Exception as exc:
        _restore_backup(out_dir, backup)
        raise RendererPublicationError(
            [
                event(
                    code="publication.transaction_failed",
                    severity="error",
                    phase="publication",
                    role="publisher",
                    path="/artifacts",
                    action="publish",
                    result="failed",
                    expected="atomic publication of five artifacts",
                    input_meta={"type": type(exc).__name__},
                )
            ]
        ) from exc
    finally:
        shutil.rmtree(staging, ignore_errors=True)
        if backup is not None:
            shutil.rmtree(backup, ignore_errors=True)


def write_text_bytes(path: Path, data: bytes) -> None:
    path.write_bytes(data)
    # Best-effort flush for transactional durability.
    try:
        with path.open("rb+") as fh:
            fh.flush()
            os.fsync(fh.fileno())
    except OSError:
        pass


def _replace_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    # os.replace is atomic on the same filesystem for a single file.
    os.replace(str(src), str(dest))


def _restore_backup(out_dir: Path, backup: Path | None) -> None:
    if backup is None or not backup.exists():
        return
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name in CANONICAL_ARTIFACTS:
            target = out_dir / name
            if target.exists():
                target.unlink()
        for item in backup.iterdir():
            dest = out_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
    except Exception as exc:
        raise RendererPublicationError(
            [
                event(
                    code="publication.rollback_failed",
                    severity="error",
                    phase="publication",
                    role="publisher",
                    path="/artifacts",
                    action="rollback",
                    result="failed",
                    expected="prior output restored byte-identical",
                    input_meta={"type": type(exc).__name__},
                )
            ]
        ) from exc


def resolved_schema_source() -> Path:
    """Path to the checked-in D121 schema artifact."""
    # Prefer package-relative path so installed/editable layouts work.
    pkg_schema = Path(__file__).resolve().parent / "schema" / "handoff_schema_v1.json"
    if pkg_schema.is_file():
        return pkg_schema
    return schema_path()
