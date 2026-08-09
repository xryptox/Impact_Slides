"""Renderer v3 deterministic artifact publication (#176).

Seams under test:
- render_deck / python -m impact_slides.renderer_v3 → five D250 artifacts
- clean / degraded / failed status, typed errors, CLI exit codes (D112)
- byte-identical equivalent renders; failed runs leave prior output untouched
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import (
    RendererConfigurationError,
    RendererPublicationError,
    RendererValidationError,
    __version__,
    render_deck,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/minimal_cover_narrative_cover.json"
SCHEMA = ROOT / "impact_slides/renderer_v3/schema/handoff_schema_v1.json"

CANONICAL = frozenset(
    {
        "presentation.html",
        "slide_notes.md",
        "evidence_manifest.json",
        "run_meta.json",
        "handoff_schema_v1.json",
    }
)


def _write_handoff(tmp: Path, raw: dict | None = None) -> Path:
    path = tmp / "handoff.json"
    data = raw if raw is not None else json.loads(FIXTURE.read_text(encoding="utf-8"))
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def _file_map(out: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(out.iterdir()) if p.is_file()}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Happy path — five canonical artifacts
# ---------------------------------------------------------------------------


def test_render_deck_publishes_exactly_five_artifacts(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"
    result = render_deck(handoff, out)

    names = {p.name for p in out.iterdir()}
    assert names == CANONICAL
    assert result["status"] == "clean"
    assert result["ok"] is True
    assert result["renderer_version"] == __version__ == "3.0.0"
    assert result["handoff_schema_version"] == 1
    assert result["severity_counts"] == {"info": 0, "warning": 0, "error": 0}
    assert result["errors"] == []
    for key in (
        "presentation",
        "slide_notes",
        "evidence_manifest",
        "run_meta",
        "handoff_schema",
    ):
        assert Path(result[key]).is_file()
        assert Path(result[key]).parent == out


def test_schema_artifact_is_byte_copy_of_checked_in(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"
    render_deck(handoff, out)
    assert (out / "handoff_schema_v1.json").read_bytes() == SCHEMA.read_bytes()


def test_artifacts_are_utf8_lf_with_trailing_newline(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"
    render_deck(handoff, out)
    for name in CANONICAL:
        raw = (out / name).read_bytes()
        assert b"\r\n" not in raw
        assert raw.endswith(b"\n")
        raw.decode("utf-8")


def test_run_meta_is_closed_deterministic_shape(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"
    render_deck(handoff, out)
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert list(meta.keys()) == [
        "renderer_version",
        "handoff_schema_version",
        "theme_id",
        "status",
        "ok",
        "options",
        "slide_count",
        "slides",
        "severity_counts",
        "events",
        "plans",
        "static_readiness",
        "artifacts",
    ]
    assert meta["theme_id"] == "boardroom_amex"
    assert meta["status"] == "clean"
    assert meta["ok"] is True
    assert meta["options"] == {"strict": True, "debug": False, "svg_only": False}
    assert meta["slide_count"] == 3
    assert [s["layout_type"] for s in meta["slides"]] == [
        "opening_cover",
        "narrative",
        "closing_cover",
    ]
    art_names = {a["name"] for a in meta["artifacts"]}
    assert art_names == CANONICAL - {"run_meta.json"}
    for a in meta["artifacts"]:
        assert set(a) == {"name", "bytes", "sha256"}
        assert a["bytes"] == len((out / a["name"]).read_bytes())
        assert a["sha256"] == _sha((out / a["name"]).read_bytes())


def test_notes_preserve_exact_text_or_placeholder(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"
    render_deck(handoff, out)
    notes = (out / "slide_notes.md").read_text(encoding="utf-8")
    assert "# Slide 1 — Impact Review" in notes
    assert "_(no notes)_" in notes
    assert (
        "Open with the flat-revenue frame; do not restate the cover." in notes
    )
    assert "# Slide 2 — Where we stand" in notes
    assert "# Slide 3 — Discussion" in notes


def test_equivalent_renders_are_byte_identical(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    render_deck(handoff, out_a)
    render_deck(handoff, out_b)
    assert _file_map(out_a) == _file_map(out_b)


# ---------------------------------------------------------------------------
# Failed / degraded / configuration
# ---------------------------------------------------------------------------


def test_strict_failure_publishes_nothing_and_preserves_prior(tmp_path: Path):
    handoff_ok = _write_handoff(tmp_path)
    out = tmp_path / "out"
    render_deck(handoff_ok, out)
    prior = _file_map(out)

    bad = json.loads(FIXTURE.read_text(encoding="utf-8"))
    bad["extra_top"] = 1
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps(bad) + "\n", encoding="utf-8")

    with pytest.raises(RendererValidationError) as ei:
        render_deck(bad_path, out)
    assert ei.value.status == "failed"
    assert ei.value.ok is False
    assert any(e.code == "validation.unknown_field" for e in ei.value.events)
    assert _file_map(out) == prior
    assert set(_file_map(out)) == CANONICAL


def test_failed_run_never_creates_out_dir_files(tmp_path: Path):
    bad = json.loads(FIXTURE.read_text(encoding="utf-8"))
    bad["meta"]["handoff_schema_version"] = 2
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps(bad) + "\n", encoding="utf-8")
    out = tmp_path / "fresh_out"
    with pytest.raises(RendererValidationError):
        render_deck(bad_path, out)
    assert not out.exists() or list(out.iterdir()) == []


def test_non_strict_degraded_publishes_all_five(tmp_path: Path):
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    raw["slides"][1]["unknown_hint"] = True
    handoff = _write_handoff(tmp_path, raw)
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    assert result["status"] == "degraded"
    assert result["ok"] is False
    assert "repair.field_dropped" in result["errors"] or result["severity_counts"][
        "warning"
    ] >= 1
    assert {p.name for p in out.iterdir()} == CANONICAL
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "degraded"
    assert meta["ok"] is False
    assert meta["options"]["strict"] is False
    assert any(e["code"] == "repair.field_dropped" for e in meta["events"])


def test_rejected_configuration_raises_without_touching_out(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    marker = out / "keep_me.txt"
    marker.write_text("prior\n", encoding="utf-8")
    with pytest.raises(RendererConfigurationError) as ei:
        render_deck(handoff, out, theme={"navy": "#000"})
    assert ei.value.status == "failed"
    assert list(out.iterdir()) == [marker]
    assert marker.read_text(encoding="utf-8") == "prior\n"


def test_seed_path_rejected(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    with pytest.raises(RendererConfigurationError):
        render_deck(handoff, tmp_path / "out", seed_path=tmp_path / "seed.json")


def test_svg_only_via_suppress_features(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"
    result = render_deck(handoff, out, suppress_features=["charts"])
    assert result["status"] == "clean"
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["options"]["svg_only"] is True


def test_force_features_rejected(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    with pytest.raises(RendererConfigurationError):
        render_deck(handoff, tmp_path / "out", force_features=["charts"])


# ---------------------------------------------------------------------------
# CLI exit codes (D112)
# ---------------------------------------------------------------------------


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "impact_slides.renderer_v3", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_clean_exits_0(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"
    proc = _run_cli("--handoff", str(handoff), "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    assert {p.name for p in out.iterdir()} == CANONICAL


def test_cli_failed_exits_1(tmp_path: Path):
    bad = json.loads(FIXTURE.read_text(encoding="utf-8"))
    bad["extra"] = 1
    handoff = _write_handoff(tmp_path, bad)
    out = tmp_path / "out"
    proc = _run_cli("--handoff", str(handoff), "--out", str(out))
    assert proc.returncode == 1
    assert not out.exists() or list(out.iterdir()) == []


def test_cli_degraded_exits_2(tmp_path: Path):
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    raw["zzz"] = 1
    handoff = _write_handoff(tmp_path, raw)
    out = tmp_path / "out"
    proc = _run_cli("--handoff", str(handoff), "--out", str(out), "--no-strict")
    assert proc.returncode == 2, proc.stderr
    assert {p.name for p in out.iterdir()} == CANONICAL


def test_cli_svg_only_flag(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"
    proc = _run_cli("--handoff", str(handoff), "--out", str(out), "--svg-only")
    assert proc.returncode == 0, proc.stderr
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["options"]["svg_only"] is True


# ---------------------------------------------------------------------------
# Mutation traps
# ---------------------------------------------------------------------------


def test_missing_schema_source_fails_before_publish(tmp_path: Path, monkeypatch):
    """Publication must require the checked-in D121 schema bytes."""
    import impact_slides.renderer_v3.render as rnd

    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"
    missing = tmp_path / "nope.json"
    monkeypatch.setattr(rnd, "resolved_schema_source", lambda: missing)
    with pytest.raises(RendererPublicationError) as ei:
        render_deck(handoff, out)
    assert any(e.code == "publication.transaction_failed" for e in ei.value.events)
    assert not out.exists() or list(out.iterdir()) == []


def test_published_schema_matches_checked_in_bytes(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"
    render_deck(handoff, out)
    assert (out / "handoff_schema_v1.json").read_bytes() == SCHEMA.read_bytes()


def test_no_extra_artifacts_or_temps_left_behind(tmp_path: Path):
    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"
    render_deck(handoff, out)
    parent_extras = [
        p.name
        for p in tmp_path.iterdir()
        if p.name not in {"handoff.json", "out"} and not p.name.startswith(".")
    ]
    # staging temps cleaned; only handoff input + out remain among user paths
    assert "out" in {p.name for p in tmp_path.iterdir()}
    assert not any("tmp" in n.lower() or n.startswith(".") for n in parent_extras)
    assert {p.name for p in out.iterdir()} == CANONICAL



def test_unreadable_handoff_is_typed_configuration_error(tmp_path: Path, monkeypatch):
    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"

    def boom(self, *args, **kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(Path, "read_text", boom)
    with pytest.raises(RendererConfigurationError) as ei:
        render_deck(handoff, out)
    assert any(e.code == "validation.configuration" for e in ei.value.events)


def test_non_utf8_handoff_is_typed_validation_error(tmp_path: Path):
    handoff = tmp_path / "bad.json"
    handoff.write_bytes(bytes([0xFF, 0xFE]) + b" not utf8")
    out = tmp_path / "out"
    with pytest.raises(RendererValidationError) as ei:
        render_deck(handoff, out)
    assert any(e.code == "validation.type" for e in ei.value.events)


def test_backup_bind_only_after_full_copy(tmp_path: Path, monkeypatch):
    """Mid-backup copy failure must not restore from a partial backup."""
    import impact_slides.renderer_v3.publish as pub

    handoff = _write_handoff(tmp_path)
    out = tmp_path / "out"
    render_deck(handoff, out)
    prior = _file_map(out)

    calls = {"n": 0}
    real_copy2 = pub.shutil.copy2

    def flaky_copy2(src, dst, *a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("simulated backup copy failure")
        return real_copy2(src, dst, *a, **k)

    monkeypatch.setattr(pub.shutil, "copy2", flaky_copy2)
    with pytest.raises(RendererPublicationError):
        render_deck(handoff, out)
    assert _file_map(out) == prior


def test_package_export_includes_render_deck():
    import impact_slides.renderer_v3 as pkg

    assert hasattr(pkg, "render_deck")
    assert "render_deck" in pkg.__all__
