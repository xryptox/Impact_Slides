"""Offline legacy→schema-v1 migration tool (D119/D313/D316) — #195."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import migrate
from impact_slides.renderer_v3.migrate import (
    INVENTORY_SIZE,
    LEGACY_INVENTORY,
    migrate_handoff,
)


def _write(tmp: Path, name: str, payload: dict) -> Path:
    path = tmp / name
    path.write_text(json.dumps(payload), encoding="utf-8", newline="\n")
    return path


def _legacy_envelope(slides: list[dict], **presentation) -> dict:
    return {
        "presentation": {
            "title": presentation.get("title", "Legacy Deck"),
            "subtitle": presentation.get("subtitle", ""),
        },
        "slides": slides,
    }


def test_inventory_has_exactly_57_unique_inputs():
    assert INVENTORY_SIZE == 57
    assert len(LEGACY_INVENTORY) == 57
    assert len(set(LEGACY_INVENTORY)) == 57
    classes = {e.classification for e in LEGACY_INVENTORY.values()}
    assert classes == {"deterministic", "human", "removed_sentinel"}
    assert sum(1 for e in LEGACY_INVENTORY.values() if e.classification == "deterministic") == 37
    assert sum(1 for e in LEGACY_INVENTORY.values() if e.classification == "human") == 17
    assert sum(1 for e in LEGACY_INVENTORY.values() if e.classification == "removed_sentinel") == 3
    # D313 "separate slides" is prose only — not a single composition target token.
    cwm = LEGACY_INVENTORY["comparison_with_metrics"]
    assert cwm.candidates == ("comparison_cards", "metric_overview")
    assert "separate_slides" not in cwm.candidates


def test_check_writes_nothing_and_sources_untouched(tmp_path: Path):
    src = _write(
        tmp_path,
        "in.json",
        _legacy_envelope(
            [
                {
                    "slide_number": 1,
                    "layout_type": "title_or_opening",
                    "title": "Hello",
                    "speaker_notes": "Open.",
                }
            ]
        ),
    )
    before = src.read_bytes()
    out = tmp_path / "out"
    out.mkdir()
    result = migrate_handoff(src, out_dir=out, check=True)
    assert src.read_bytes() == before
    assert list(out.iterdir()) == []
    assert result.wrote is False
    assert any(d.legacy_input == "title_or_opening" for d in result.unresolved)


def test_report_covers_all_57_and_each_slide_one_disposition(tmp_path: Path):
    src = _write(
        tmp_path,
        "in.json",
        _legacy_envelope(
            [
                {
                    "slide_number": 1,
                    "layout_type": "ir_bullet_sheet",
                    "title": "Highlights",
                    "section": "Overview",
                    "content": {
                        "bullets": ["One fact", "Two fact"],
                        "body_text": "Lead paragraph.",
                    },
                    "speaker_notes": "Stay on the bullets.",
                },
                {
                    "slide_number": 2,
                    "layout_type": "brand_cover",
                    "title": "Close",
                    "speaker_notes": "End.",
                },
                {
                    "slide_number": 3,
                    "layout_type": "default",
                    "title": "Mystery",
                    "speaker_notes": "Needs a composition.",
                },
            ]
        ),
    )
    result = migrate_handoff(src, out_dir=tmp_path / "out", check=True)
    assert len(result.inventory_report) == 57
    assert {row["legacy_input"] for row in result.inventory_report} == set(LEGACY_INVENTORY)
    assert len(result.slide_dispositions) == 3
    assert {d.slide_number for d in result.slide_dispositions} == {1, 2, 3}
    # ir_bullet_sheet can convert; brand_cover and sentinel stay unresolved
    by_n = {d.slide_number: d for d in result.slide_dispositions}
    assert by_n[1].status == "resolved"
    assert by_n[1].target == "narrative"
    assert by_n[2].status == "unresolved"
    assert by_n[3].status == "unresolved"


def test_failed_proof_becomes_unresolved_not_guess(tmp_path: Path):
    """Deterministic target exists, but incomplete matrix must not invent cells."""
    src = _write(
        tmp_path,
        "in.json",
        _legacy_envelope(
            [
                {
                    "slide_number": 1,
                    "layout_type": "data_table",
                    "title": "Broken table",
                    "section": "Overview",
                    "visual_spec": {
                        "primary_visual": {
                            "type": "data_table",
                            "steps_or_data": [["Only", "Header"]],  # no body rows
                        }
                    },
                    "speaker_notes": "Table is incomplete.",
                }
            ]
        ),
    )
    result = migrate_handoff(src, out_dir=tmp_path / "out", check=True)
    d = result.slide_dispositions[0]
    assert d.status == "unresolved"
    assert d.target == "data_table"
    assert d.classification == "deterministic"
    assert any("proof" in u.reason.lower() or "matrix" in u.reason.lower() for u in result.unresolved)


def test_v1_marker_withheld_until_clean(tmp_path: Path):
    src = _write(
        tmp_path,
        "in.json",
        _legacy_envelope(
            [
                {
                    "slide_number": 1,
                    "layout_type": "title_or_opening",
                    "title": "Ambiguous cover",
                    "speaker_notes": "Human must pick opening vs closing.",
                }
            ]
        ),
    )
    out = tmp_path / "out"
    result = migrate_handoff(src, out_dir=out, check=False)
    assert result.unresolved
    assert result.version_marked is False
    # May write report; must not write a schema-v1-marked handoff.
    handoff_paths = list(out.glob("*.json"))
    for p in handoff_paths:
        if p.name == "migration_report.json":
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        meta = data.get("meta") or {}
        assert meta.get("handoff_schema_version") != 1


def test_clean_narrative_migration_marks_v1_and_validates(tmp_path: Path):
    src = _write(
        tmp_path,
        "in.json",
        _legacy_envelope(
            [
                {
                    "slide_number": 1,
                    "layout_type": "ir_bullet_sheet",
                    "title": "Business Highlights",
                    "section": "Overview",
                    "content": {
                        "body_text": "Revenue held flat against plan.",
                        "bullets": [
                            "Cost actions landed on schedule.",
                            "Pipeline coverage remains above target.",
                        ],
                        "so_what": "Stay the course on cost.",
                    },
                    "speaker_notes": "Open with the flat-revenue frame.",
                    "evidence_sources": [
                        {"id": "src-board-pack", "source_file": "board.pdf", "source_name": "Board pack"}
                    ],
                }
            ]
        ),
    )
    out = tmp_path / "out"
    result = migrate_handoff(src, out_dir=out, check=False)
    assert result.unresolved == []
    assert result.version_marked is True
    assert result.ok is True
    candidate_path = out / "handoff_v1.json"
    assert candidate_path.is_file()
    cand = json.loads(candidate_path.read_text(encoding="utf-8"))
    assert cand["meta"]["handoff_schema_version"] == 1
    assert cand["slides"][0]["layout_type"] == "narrative"
    assert src.read_text(encoding="utf-8").find("handoff_schema_version") == -1
    # Source bytes unchanged beyond read
    assert "ir_bullet_sheet" in src.read_text(encoding="utf-8")


def test_check_fails_when_unresolved(tmp_path: Path):
    src = _write(
        tmp_path,
        "in.json",
        _legacy_envelope(
            [
                {
                    "slide_number": 1,
                    "layout_type": "multi_panel",
                    "title": "Panels",
                    "speaker_notes": "Ambiguous.",
                }
            ]
        ),
    )
    result = migrate_handoff(src, out_dir=tmp_path / "out", check=True)
    assert result.ok is False
    assert result.exit_code != 0


def test_dense_data_table_converts(tmp_path: Path):
    src = _write(
        tmp_path,
        "in.json",
        _legacy_envelope(
            [
                {
                    "slide_number": 1,
                    "layout_type": "table",  # alias
                    "title": "Segment performance",
                    "section": "Overview",
                    "visual_spec": {
                        "primary_visual": {
                            "type": "data_table",
                            "steps_or_data": [
                                ["Metric", "Revenue", "Note"],
                                ["Cards", "100", "Core"],
                                ["ICS", "50", "Watch"],
                            ],
                        }
                    },
                    "speaker_notes": "Cards lead.",
                }
            ]
        ),
    )
    result = migrate_handoff(src, out_dir=tmp_path / "out", check=False)
    assert result.unresolved == []
    assert result.version_marked is True
    slide = result.candidate["slides"][0]
    assert slide["layout_type"] == "data_table"
    table = slide["payload"]["table"]
    assert len(table["columns"]) == 2
    assert len(table["rows"]) == 2
    assert table["rows"][0]["cells"]["revenue"]["type"] == "text"


def test_authored_disclosure_is_preserved(tmp_path: Path):
    """Legacy disclosure panels must map into v1 slide.disclosure (not dropped)."""
    src = _write(
        tmp_path,
        "in.json",
        _legacy_envelope(
            [
                {
                    "slide_number": 1,
                    "layout_type": "annex_table",
                    "title": "Annex A",
                    "section": "Annex",
                    "visual_spec": {
                        "primary_visual": {
                            "type": "annex_table",
                            "steps_or_data": [
                                ["Metric", "Value"],
                                ["Revenue", "100"],
                            ],
                        }
                    },
                    "disclosure": {
                        "pattern": "detail",
                        "panels": [
                            {
                                "title": "FX-adjusted note",
                                "body": "* See Slide 3 for FX-adjusted information.",
                            }
                        ],
                    },
                    "speaker_notes": "Footnote stays.",
                },
                {
                    "slide_number": 2,
                    "layout_type": "ir_bullet_sheet",
                    "title": "Notes",
                    "section": "Annex",
                    "content": {"bullets": ["Only bullet"]},
                    "disclosure": {
                        "pattern": "detail",
                        "panels": [
                            {
                                "title": "Statistical Tables reference",
                                "body": "Refer to the Statistical Tables.",
                            }
                        ],
                    },
                    "speaker_notes": "Cite tables.",
                },
            ]
        ),
    )
    result = migrate_handoff(src, out_dir=tmp_path / "out", check=False)
    assert result.unresolved == []
    assert result.version_marked is True
    annex, narrative = result.candidate["slides"]
    assert annex["layout_type"] == "annex_table"
    assert "disclosure" in annex
    assert annex["disclosure"]["sections"][0]["title"] == "FX-adjusted note"
    assert "FX-adjusted" in annex["disclosure"]["sections"][0]["items"][0]["text"]
    assert narrative["layout_type"] == "narrative"
    assert narrative["disclosure"]["sections"][0]["title"] == "Statistical Tables reference"


def _annex_slide(number: int, title: str, panel_title: str) -> dict:
    return {
        "slide_number": number,
        "layout_type": "annex_table",
        "title": title,
        "section": "Annex",
        "visual_spec": {
            "primary_visual": {
                "type": "annex_table",
                "steps_or_data": [
                    ["Metric", "Value"],
                    ["Revenue", "100"],
                ],
            }
        },
        "disclosure": {
            "pattern": "detail",
            "panels": [{"title": panel_title, "body": "FX-adjusted figures."}],
        },
    }


def test_repeated_disclosure_titles_get_deck_unique_surface_ids(tmp_path: Path):
    src = _write(
        tmp_path,
        "in.json",
        _legacy_envelope(
            [_annex_slide(1, "Annex A", "FX-adjusted note"), _annex_slide(2, "Annex B", "FX-adjusted note")]
        ),
    )
    result = migrate_handoff(src, out_dir=tmp_path / "out", check=False)
    assert result.unresolved == []
    assert result.version_marked is True
    slides = result.candidate["slides"]
    ids = [s["disclosure"]["sections"][0]["surface_id"] for s in slides]
    assert ids[0] == "fx-adjusted-note"
    assert ids[1] == "fx-adjusted-note-2"
    assert all(s["disclosure"]["sections"][0]["title"] == "FX-adjusted note" for s in slides)


def test_corpus_repeated_fx_note_deck_marks_v1():
    src = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "renderer_v2"
        / "amex_annex_33_37_restored_handoff.json"
    )
    result = migrate_handoff(src, check=True)
    assert result.version_marked is True
    slides = result.candidate["slides"]
    ids = [s["disclosure"]["sections"][0]["surface_id"] for s in slides]
    assert len(ids) == len(set(ids)) == 5
    assert ids[0] == "fx-adjusted-note"
    assert all(s["disclosure"]["sections"][0]["title"] == "FX-adjusted note" for s in slides)


def test_unused_number_formats_not_copied(tmp_path: Path):
    deck = _legacy_envelope(
        [
            {
                "slide_number": 1,
                "layout_type": "line_chart",
                "title": "Trend",
                "section": "S",
                "visual_spec": {
                    "primary_visual": {
                        "type": "chart",
                        "surface_id": "rev-trend",
                        "chart_data": {
                            "categories": [
                                {"category_id": "q1", "label": "Q1"},
                                {"category_id": "q2", "label": "Q2"},
                            ],
                            "series": [
                                {"series_id": "revenue", "name": "Revenue", "values": ["1.0", "2.0"]}
                            ],
                        },
                        "value_axes": {
                            "primary": {
                                "visible": True,
                                "format_id": "pct-1",
                                "domain": {"kind": "generated"},
                            }
                        },
                        "category_axis": {"visible": True},
                    }
                },
            }
        ]
    )
    deck["number_formats"] = {
        "pct-1": {"value_decimals": 1, "negative_style": "minus"},
        "orphan-format": {"value_decimals": 0, "negative_style": "minus"},
    }
    src = _write(tmp_path, "in.json", deck)
    result = migrate_handoff(src, out_dir=tmp_path / "out", check=False)
    assert result.unresolved == []
    assert result.version_marked is True
    assert list(result.candidate["number_formats"]) == ["pct-1"]


def test_cli_check_and_migrate(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    src = _write(
        tmp_path,
        "in.json",
        _legacy_envelope(
            [
                {
                    "slide_number": 1,
                    "layout_type": "ir_bullet_sheet",
                    "title": "Notes",
                    "section": "A",
                    "content": {"bullets": ["Only bullet"]},
                    "speaker_notes": "Say the bullet.",
                }
            ]
        ),
    )
    out = tmp_path / "out"
    code = migrate.main(["--handoff", str(src), "--out", str(out), "--check"])
    assert code == 0
    assert list(out.iterdir()) == [] if out.exists() else True
    code = migrate.main(["--handoff", str(src), "--out", str(out)])
    assert code == 0
    assert (out / "handoff_v1.json").is_file()
    assert (out / "migration_report.json").is_file()


def test_grouped_annex_more_than_two_peers_fails_proof(tmp_path: Path):
    src = _write(
        tmp_path,
        "in.json",
        _legacy_envelope(
            [
                {
                    "slide_number": 1,
                    "layout_type": "grouped_annex_table",
                    "title": "Annex matrices",
                    "speaker_notes": "Three peers cannot satisfy proof.",
                    "visual_spec": {
                        "tables": [
                            {
                                "heading": f"Peer {n}",
                                "steps_or_data": [
                                    ["Metric", "FY24"],
                                    [f"Row {n}", "100"],
                                ],
                            }
                            for n in range(1, 4)
                        ]
                    },
                }
            ]
        ),
    )
    result = migrate_handoff(src, out_dir=tmp_path / "out", check=True)
    d = result.slide_dispositions[0]
    assert d.status == "unresolved"
    assert d.target == "grouped_annex_table"
    assert d.proof_result == "failed"
    assert any(
        u.path == "/slides/0/visual_spec"
        and u.legacy_input == "grouped_annex_table"
        and "one or two" in u.reason
        for u in result.unresolved
    )


def test_section_divider_requires_registered_section(tmp_path: Path):
    src = _write(
        tmp_path,
        "in.json",
        _legacy_envelope(
            [
                {
                    "slide_number": 1,
                    "layout_type": "section_divider",
                    "section": "Ghost",
                    "speaker_notes": "No slide authors this section.",
                },
                {
                    "slide_number": 2,
                    "layout_type": "section_divider",
                    "section": "Overview",
                    "speaker_notes": "Authored section follows.",
                },
                {
                    "slide_number": 3,
                    "layout_type": "ir_bullet_sheet",
                    "title": "Highlights",
                    "section": "Overview",
                    "content": {"bullets": ["One fact"]},
                    "speaker_notes": "Say the bullet.",
                },
            ]
        ),
    )
    result = migrate_handoff(src, out_dir=tmp_path / "out", check=True)
    by_n = {d.slide_number: d for d in result.slide_dispositions}
    assert by_n[1].status == "unresolved"
    assert by_n[1].target == "section_divider"
    assert by_n[1].proof_result == "failed"
    assert any(
        u.path == "/slides/0/section"
        and u.legacy_input == "section_divider"
        and "registered section" in u.reason
        for u in result.unresolved
    )
    # Divider naming a section authored by a non-divider slide resolves.
    assert by_n[2].status == "resolved"
    assert by_n[2].target == "section_divider"
    assert by_n[3].status == "resolved"


def test_reused_out_dir_replaces_stale_handoff_artifacts(tmp_path: Path):
    clean_src = _write(
        tmp_path,
        "clean.json",
        _legacy_envelope(
            [
                {
                    "slide_number": 1,
                    "layout_type": "ir_bullet_sheet",
                    "title": "Highlights",
                    "section": "Overview",
                    "content": {"bullets": ["One fact"]},
                    "speaker_notes": "Say the bullet.",
                }
            ]
        ),
    )
    unclean_src = _write(
        tmp_path,
        "unclean.json",
        _legacy_envelope(
            [
                {
                    "slide_number": 1,
                    "layout_type": "title_or_opening",
                    "title": "Ambiguous cover",
                    "speaker_notes": "Human must choose.",
                }
            ]
        ),
    )
    out = tmp_path / "out"

    migrate_handoff(clean_src, out_dir=out, check=False)
    assert {p.name for p in out.iterdir()} == {"handoff_v1.json", "migration_report.json"}

    result = migrate_handoff(unclean_src, out_dir=out, check=False)
    assert result.version_marked is False
    assert {p.name for p in out.iterdir()} == {
        "handoff_candidate.json",
        "migration_report.json",
    }

    result = migrate_handoff(clean_src, out_dir=out, check=False)
    assert result.version_marked is True
    assert {p.name for p in out.iterdir()} == {"handoff_v1.json", "migration_report.json"}


def test_no_hidden_production_path():
    """Importing render/validate must not pull in the migrate module (D119)."""
    code = (
        "import sys\n"
        "import impact_slides.renderer_v3.render\n"
        "import impact_slides.renderer_v3.validate\n"
        "assert 'impact_slides.renderer_v3.migrate' not in sys.modules\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
