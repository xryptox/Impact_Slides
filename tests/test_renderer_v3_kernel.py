"""Schema-v1 canonical rendering kernel (#175).

Seams under test:
- validate_handoff → typed Deck (no raw-dict painting surface)
- allowlisted non-strict repairs only
- generated JSON Schema artifact drift gate
- package isolation from renderer_v2
"""
from __future__ import annotations

import importlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import (
    RendererValidationError,
    __version__,
    validate_handoff,
)
from impact_slides.renderer_v3.models import (
    ClosingCoverSlide,
    Deck,
    NarrativeSlide,
    OpeningCoverSlide,
)
from impact_slides.renderer_v3.schema_export import check_schema, generate_schema, schema_json

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/minimal_cover_narrative_cover.json"


def _minimal() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Happy path — canonical typed model
# ---------------------------------------------------------------------------


def test_version_is_3():
    assert __version__ == "3.0.0"


def test_minimal_deck_validates_to_typed_model():
    result = validate_handoff(_minimal(), strict=True)
    assert result.ok
    assert isinstance(result.deck, Deck)
    assert result.deck.meta.handoff_schema_version == 1
    assert len(result.deck.slides) == 3
    assert isinstance(result.deck.slides[0], OpeningCoverSlide)
    assert isinstance(result.deck.slides[1], NarrativeSlide)
    assert isinstance(result.deck.slides[2], ClosingCoverSlide)
    # D122: canonical model exposes typed payload, not raw dicts
    assert result.deck.slides[0].payload.title == "Impact Review"
    assert result.deck.slides[1].payload.blocks[0].block_id == "lead"
    assert result.events == []


def test_canonical_model_round_trips_without_raw_keys():
    deck = validate_handoff(_minimal(), strict=True).deck
    dumped = deck.model_dump(mode="json", exclude_none=True)
    assert set(dumped) == {
        "meta",
        "sections",
        "number_formats",
        "evidence_registry",
        "slides",
    }
    assert "visual_spec" not in json.dumps(dumped)
    assert "primary_visual" not in json.dumps(dumped)


# ---------------------------------------------------------------------------
# Aggregation + strict failure
# ---------------------------------------------------------------------------


def test_strict_aggregates_multiple_errors():
    raw = _minimal()
    raw["extra_top"] = 1
    raw["meta"]["tool"] = "gpt"
    raw["slides"][1]["unknown_hint"] = True
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(raw, strict=True)
    err = ei.value
    assert err.status == "failed"
    codes = {e.code for e in err.events}
    assert "validation.unknown_field" in codes
    # multiple unknown fields → multiple events, not fail-fast on first
    unknown_paths = [e.path for e in err.events if e.code == "validation.unknown_field"]
    assert len(unknown_paths) >= 2
    assert err.severity_counts["error"] >= 2


def test_strict_rejects_wrong_schema_version():
    raw = _minimal()
    raw["meta"]["handoff_schema_version"] = 2
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(raw, strict=True)
    assert any(e.code == "validation.schema_version" for e in ei.value.events)


def test_strict_rejects_unknown_composition():
    raw = _minimal()
    raw["slides"][1]["layout_type"] = "freeform_magic"
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(raw, strict=True)
    assert any(e.code == "validation.value" for e in ei.value.events)


def test_cover_forbids_root_title():
    raw = _minimal()
    raw["slides"][0]["title"] = "nope"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_opening_cover_must_be_first():
    raw = _minimal()
    # swap opening to middle by renumbering order
    slides = raw["slides"]
    raw["slides"] = [slides[1], slides[0], slides[2]]
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(raw, strict=True)
    texts = [
        (e.expected.contract if e.expected else "") + e.path + e.code
        for e in ei.value.events
    ]
    assert any("first" in t for t in texts)


def test_events_order_deterministically():
    raw = _minimal()
    raw["zzz"] = 1
    raw["aaa"] = 2
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(raw, strict=True)
    paths = [e.path for e in ei.value.events if e.code == "validation.unknown_field"]
    assert paths == sorted(paths)


# ---------------------------------------------------------------------------
# Non-strict allowlisted repairs
# ---------------------------------------------------------------------------


def test_nonstrict_drops_unknown_field_and_revalidates():
    raw = _minimal()
    raw["slides"][1]["packing_mode"] = "dense"
    result = validate_handoff(raw, strict=False)
    assert result.ok
    assert result.repaired
    assert not hasattr(result.deck.slides[1], "packing_mode")
    dumped = result.deck.model_dump(mode="json", exclude_none=True)
    assert "packing_mode" not in dumped["slides"][1]
    assert any(e.code == "repair.field_dropped" for e in result.events)
    # repaired model is fully valid as strict too (omit nulls per D212)
    again = validate_handoff(
        result.deck.model_dump(mode="json", exclude_none=True), strict=True
    )
    assert again.ok


def test_nonstrict_assumes_schema_version_when_meta_empty():
    raw = _minimal()
    raw["meta"] = {}
    result = validate_handoff(raw, strict=False)
    assert result.deck.meta.handoff_schema_version == 1
    assert any(e.code == "repair.schema_version_assumed" for e in result.events)


def test_nonstrict_does_not_assume_version_when_unknown_fields_present():
    raw = _minimal()
    raw["meta"] = {}
    raw["slides"][1]["packing_mode"] = "dense"
    # Unknown field blocks assume_schema_v1; drop may still repair the field,
    # but missing version without a clean assume remains a validation error.
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(raw, strict=False)
    codes = {e.code for e in ei.value.events}
    assert "repair.schema_version_assumed" not in codes
    assert "validation.schema_version" in codes or "validation.required" in codes


def test_null_placeholder_rejected():
    raw = _minimal()
    raw["slides"][1]["speaker_notes"] = None
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_nonstrict_does_not_invent_business_text():
    raw = _minimal()
    del raw["slides"][1]["title"]
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(raw, strict=False)
    assert any(e.code == "validation.required" for e in ei.value.events)
    # no repair invented a title
    assert not any(e.code == "repair.id_generated" for e in ei.value.events)


def test_strict_does_not_apply_repairs():
    raw = _minimal()
    raw["meta"] = {}
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(raw, strict=True)
    assert any(e.code == "validation.schema_version" for e in ei.value.events)
    assert not any(e.code.startswith("repair.") for e in ei.value.events)


# ---------------------------------------------------------------------------
# JSON Schema generation + drift
# ---------------------------------------------------------------------------


def test_json_schema_is_generated_from_models():
    schema = generate_schema()
    assert schema["title"]
    assert "properties" in schema or "$defs" in schema or "allOf" in schema
    # envelope keys present somewhere in the schema document
    dumped = json.dumps(schema)
    for key in ("meta", "sections", "number_formats", "evidence_registry", "slides"):
        assert key in dumped
    assert "handoff_schema_version" in dumped


def test_committed_schema_matches_models():
    check_schema(ROOT)


def test_schema_export_check_cli():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "impact_slides.renderer_v3.schema_export",
            "--check",
            "--root",
            str(ROOT),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_schema_drift_detected(tmp_path: Path):
    # copy repo schema path shape under tmp and mutate
    dest = tmp_path / "impact_slides/renderer_v3/schema"
    dest.mkdir(parents=True)
    (dest / "handoff_schema_v1.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        check_schema(tmp_path)


# ---------------------------------------------------------------------------
# Isolation from renderer_v2
# ---------------------------------------------------------------------------


def test_renderer_v3_import_does_not_load_renderer_v2():
    """Behavioral isolation: loading v3 must not pull v2 into sys.modules."""
    # Fresh interpreter so this import edge cannot stale-bind other tests'
    # module-level render_deck / monkeypatch targets (see publish suite).
    script = (
        "import importlib, sys; "
        "importlib.import_module('impact_slides.renderer_v3'); "
        "assert not any("
        "n == 'impact_slides.renderer_v2' or n.startswith('impact_slides.renderer_v2.') "
        "for n in sys.modules"
        ")"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_renderer_v2_untouched_by_v3_import():
    v2 = importlib.import_module("impact_slides.renderer_v2")
    before = getattr(v2, "__version__", None)
    importlib.import_module("impact_slides.renderer_v3")
    assert v2.__version__ == before == "2.0.0"


def test_bool_true_is_not_schema_version_one():
    raw = _minimal()
    raw["meta"]["handoff_schema_version"] = True
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


# ---------------------------------------------------------------------------
# Mutation / adversarial proofs
# ---------------------------------------------------------------------------


def test_mutation_dropping_discriminator_fails():
    raw = _minimal()
    del raw["slides"][1]["layout_type"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_mutation_duplicate_slide_number_fails():
    raw = _minimal()
    raw["slides"][2]["slide_number"] = 1
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(raw, strict=True)
    assert any(e.code in {"validation.identity", "validation.structure", "validation.value"} for e in ei.value.events)


def test_mutation_unused_evidence_fails():
    raw = _minimal()
    raw["evidence_registry"]["orphan"] = {"source_name": "Orphan"}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_mutation_footer_not_subset_fails():
    raw = _minimal()
    raw["evidence_registry"]["other"] = {"source_name": "Other"}
    # reference other only from footer (and need it used — add to evidence_ids of cover)
    raw["slides"][0]["evidence_ids"] = ["src-board-pack", "other"]
    raw["slides"][1]["source_footer"] = ["other"]  # not in slide 1 evidence_ids
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_raw_dict_not_attached_to_result():
    raw = _minimal()
    raw_id = id(raw)
    result = validate_handoff(raw, strict=True)
    assert id(result.deck) != raw_id
    assert not isinstance(result.deck, dict)


def test_fixture_file_is_strict_valid():
    assert FIXTURE.is_file()
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert validate_handoff(deepcopy(data), strict=True).ok


def test_schema_json_stable_helper():
    a = schema_json()
    b = schema_json()
    assert a == b
    assert a.endswith("\n")
