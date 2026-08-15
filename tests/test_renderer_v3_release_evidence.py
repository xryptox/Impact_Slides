"""Renderer v3 3.0.0 release evidence (#198 / D105–D109/D113/D126/D248/D250/D309–D312/D315).

Seams:
- committed ``artifacts/renderer_3_release/3.0.0/`` tree
- ``scripts/renderer_3_release.py`` verify (hash-pin, exact file set, required gates)
- live re-render of both modes matches committed D250 bytes
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

from impact_slides.renderer_v3 import render_deck
from impact_slides.renderer_v3.cli import main as cli_main

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from renderer_3_release import (  # noqa: E402
    D250,
    RELEASE_DIR,
    REQUIRED_GATES,
    UNLISTED,
    _copy_d250,
    _lf_bytes,
    verify_release,
)

HANDOFF = ROOT / "tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json"
SCHEMA = ROOT / "impact_slides/renderer_v3/schema/handoff_schema_v1.json"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_release_dir_verifies_clean() -> None:
    result = verify_release(RELEASE_DIR)
    assert result.ok, result.errors
    assert result.errors == []
    assert set(result.gates) == set(REQUIRED_GATES)
    assert all(v == "passed" for v in result.gates.values())


def test_manifest_checksums_and_unlisted_set() -> None:
    manifest = json.loads((RELEASE_DIR / "acceptance_manifest.json").read_text(encoding="utf-8"))
    listed = {a["path"] for a in manifest["artifacts"]}
    assert UNLISTED.isdisjoint(listed)
    on_disk = {
        p.relative_to(RELEASE_DIR).as_posix()
        for p in RELEASE_DIR.rglob("*")
        if p.is_file()
    }
    assert on_disk - listed == UNLISTED
    assert listed <= on_disk
    for name in UNLISTED:
        assert (RELEASE_DIR / name).is_file()


def test_each_render_root_is_exactly_d250() -> None:
    for mode in ("chartjs", "svg"):
        names = {p.name for p in (RELEASE_DIR / mode / "render").iterdir() if p.is_file()}
        assert names == set(D250)


def test_schema_bytes_match_across_inputs_and_renders() -> None:
    checked = SCHEMA.read_bytes().replace(b"\r\n", b"\n")
    copies = [
        RELEASE_DIR / "inputs" / "handoff_schema_v1.json",
        RELEASE_DIR / "chartjs" / "render" / "handoff_schema_v1.json",
        RELEASE_DIR / "svg" / "render" / "handoff_schema_v1.json",
    ]
    for path in copies:
        assert path.read_bytes() == checked


def test_both_run_metas_are_clean_300() -> None:
    for mode, svg_only in (("chartjs", False), ("svg", True)):
        meta = json.loads((RELEASE_DIR / mode / "render" / "run_meta.json").read_text(encoding="utf-8"))
        assert meta["renderer_version"] == "3.0.0"
        assert meta["handoff_schema_version"] == 1
        assert meta["theme_id"] == "boardroom_amex"
        assert meta["status"] == "clean"
        assert meta["ok"] is True
        assert meta["slide_count"] == 44
        assert meta["severity_counts"]["warning"] == 0
        assert meta["severity_counts"]["error"] == 0
        assert meta["options"]["strict"] is True
        assert meta["options"]["svg_only"] is svg_only


def test_live_rerender_matches_committed_d250(tmp_path: Path) -> None:
    src = RELEASE_DIR / "inputs" / "canonical_amex_handoff_v1.json"
    out_js = tmp_path / "chartjs"
    out_svg = tmp_path / "svg"
    render_deck(src, out_js, strict=True)
    assert cli_main(["--handoff", str(src), "--out", str(out_svg), "--svg-only"]) == 0
    for mode, out in (("chartjs", out_js), ("svg", out_svg)):
        for name in D250:
            committed = (RELEASE_DIR / mode / "render" / name).read_bytes()
            assert _sha((out / name).read_bytes()) == _sha(committed), (mode, name)


def test_pdf_review_has_approved_divergences_without_similarity() -> None:
    text = (RELEASE_DIR / "comparison" / "pdf_review.md").read_bytes()
    assert b"MAE" not in text
    assert b"SSIM" not in text
    assert b"similarity" not in text.lower()
    body = text.decode("utf-8")
    assert "DIV-001" in body
    assert "Capital Summary" in body
    assert "approved" in body.lower()


def test_mutation_extra_unlisted_file_fails(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(RELEASE_DIR, dest)
    (dest / "chartjs" / "extra.json").write_text("{}\n", encoding="utf-8")
    result = verify_release(dest)
    assert result.ok is False
    assert any("unlisted" in e for e in result.errors)


def test_mutation_missing_listed_file_fails(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(RELEASE_DIR, dest)
    (dest / "comparison" / "slide_map.json").unlink()
    result = verify_release(dest)
    assert result.ok is False
    assert any("missing" in e for e in result.errors)


def test_mutation_similarity_score_in_review_fails(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(RELEASE_DIR, dest)
    review = dest / "comparison" / "pdf_review.md"
    review.write_bytes(review.read_bytes() + b"\nSSIM 0.99\n")
    result = verify_release(dest)
    assert result.ok is False
    assert any("similarity" in e or "SSIM" in e for e in result.errors)


def test_mutation_sixth_render_file_fails(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(RELEASE_DIR, dest)
    (dest / "svg" / "render" / "notes.txt").write_text("x\n", encoding="utf-8")
    result = verify_release(dest)
    assert result.ok is False


def test_mutation_determinism_hash_fails(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(RELEASE_DIR, dest)
    det_path = dest / "contracts" / "determinism.json"
    det = json.loads(det_path.read_text(encoding="utf-8"))
    det["chartjs"]["presentation.html"] = "0" * 64
    det_path.write_text(json.dumps(det, indent=2) + "\n", encoding="utf-8")
    result = verify_release(dest)
    assert result.ok is False
    assert result.gates.get("determinism") == "failed"


def test_mutation_duplicate_screenshots_fail(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(RELEASE_DIR, dest)
    src = dest / "chartjs" / "slides" / "01.png"
    for n in range(2, 45):
        shutil.copy2(src, dest / "chartjs" / "slides" / f"{n:02d}.png")
    result = verify_release(dest)
    assert result.ok is False
    assert result.gates.get("paint_readiness_chartjs") == "failed"


def test_mutation_zero_plot_on_chart_slide_fails(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(RELEASE_DIR, dest)
    geo_path = dest / "chartjs" / "geometry.json"
    geo = json.loads(geo_path.read_text(encoding="utf-8"))
    for slide in geo["slides"]:
        if slide.get("charts"):
            slide["charts"][0]["chart_area"] = {"width": 0, "height": 0}
            break
    geo_path.write_text(json.dumps(geo, indent=2) + "\n", encoding="utf-8")
    result = verify_release(dest)
    assert result.ok is False
    assert any("plot" in e or "floor" in e or "geometry" in e for e in result.errors)


def test_mutation_cross_mode_plot_width_fails(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(RELEASE_DIR, dest)
    geo_path = dest / "chartjs" / "geometry.json"
    geo = json.loads(geo_path.read_text(encoding="utf-8"))
    for slide in geo["slides"]:
        if slide.get("plots"):
            slide["plots"][0]["width"] = 400
            break
    geo_path.write_text(json.dumps(geo, indent=2) + "\n", encoding="utf-8")
    result = verify_release(dest)
    assert result.ok is False
    assert result.gates.get("geometry_parity") == "failed"


def test_mutation_missing_frozen_plan_fails(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(RELEASE_DIR, dest)
    ready_path = dest / "chartjs" / "readiness.json"
    ready = json.loads(ready_path.read_text(encoding="utf-8"))
    ready["slides"][0]["frozen_plan_attached"] = False
    ready_path.write_text(json.dumps(ready, indent=2) + "\n", encoding="utf-8")
    result = verify_release(dest)
    assert result.ok is False
    assert result.gates.get("paint_readiness_chartjs") == "failed"


def test_mutation_missing_div_002_fails(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(RELEASE_DIR, dest)
    review = dest / "comparison" / "pdf_review.md"
    review.write_bytes(review.read_bytes().replace(b"DIV-002", b"DIV-xxx"))
    result = verify_release(dest)
    assert result.ok is False
    assert result.gates.get("pdf_review") == "failed"


def test_mutation_svg_font_face_fails(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(RELEASE_DIR, dest)
    html = dest / "svg" / "render" / "presentation.html"
    html.write_text(
        html.read_text(encoding="utf-8").replace(
            "@font-face{font-family:'Source Sans 3'",
            "@font-face{font-family:'Not Source Sans'",
        ),
        encoding="utf-8",
    )
    result = verify_release(dest)
    assert result.ok is False
    assert result.gates.get("font_calibration") == "failed"


def test_handoff_locators_pin_release_pdf() -> None:
    pdf = RELEASE_DIR / "inputs" / "Q1-2026-Earnings-Presentation.pdf"
    digest = _sha(pdf.read_bytes())
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
    locators = {e["locator"]["sha256"] for e in handoff["evidence_registry"].values()}
    assert locators == {digest}
    pinned = json.loads((RELEASE_DIR / "inputs" / "canonical_amex_handoff_v1.json").read_text(encoding="utf-8"))
    pinned_locators = {e["locator"]["sha256"] for e in pinned["evidence_registry"].values()}
    assert pinned_locators == {digest}


def test_handoff_and_d250_copies_normalize_crlf(tmp_path: Path) -> None:
    crlf = b'{"ok": true}\r\n'
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()
    for name in D250:
        (src / name).write_bytes(crlf)
    assert _lf_bytes(src / D250[0]) == b'{"ok": true}\n'
    _copy_d250(src, dest)
    for name in D250:
        assert (dest / name).read_bytes() == b'{"ok": true}\n'
