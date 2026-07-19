"""P1 feature detection, gating, overrides, and size soft-warn.

Spec: wiki/SPEC_renderer_v2_p1_feature_size_gating.md
Seams: detect_features / resolve_features, render_deck metadata, CLI overrides.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

import impact_slides.renderer_v2.features as features_mod
from impact_slides.renderer_v2 import render_deck
from impact_slides.renderer_v2.cli import main
from impact_slides.renderer_v2.features import detect_features, resolve_features

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "renderer_v2"
MINI = FIXTURES / "mini_handoff.json"


def _deck_meta(html: str) -> dict:
    m = re.search(
        r'<script type="application/json" id="DECK_META">(.*?)</script>',
        html,
        re.S,
    )
    assert m, "DECK_META script block missing"
    return json.loads(m.group(1))


def _non_chart_handoff() -> dict:
    return {
        "title": "No Charts",
        "readiness_score": 0.9,
        "quality_flags": [],
        "slides": [
            {
                "slide_number": 1,
                "layout_type": "title_or_opening",
                "title": "Hello",
                "content": {"headline": "No charts here"},
                "speaker_notes": "Notes.",
            }
        ],
    }


def _chart_handoff() -> dict:
    return {
        "title": "With Charts",
        "readiness_score": 0.9,
        "quality_flags": [],
        "slides": [
            {
                "slide_number": 1,
                "layout_type": "grouped_bar_chart",
                "title": "Bars",
                "content": {"so_what": "Growth"},
                "visual_spec": {
                    "primary_visual": {
                        "type": "grouped_bar_chart",
                        "steps_or_data": [
                            {"label": "A", "value": 10},
                            {"label": "B", "value": 20},
                        ],
                    }
                },
                "speaker_notes": "Notes.",
            }
        ],
    }


# ---------------------------------------------------------------------------
# P1.1 — pure detection
# ---------------------------------------------------------------------------

class TestDetectFeatures:
    def test_returns_frozenset_of_known_ids_only(self):
        feats = detect_features(_chart_handoff())
        assert isinstance(feats, frozenset)
        assert feats <= frozenset({"charts", "mermaid", "alpine", "swiper", "icons"})

    def test_chart_layout_enables_charts(self):
        assert "charts" in detect_features(_chart_handoff())

    def test_non_chart_handoff_no_charts(self):
        assert "charts" not in detect_features(_non_chart_handoff())

    def test_mini_fixture_enables_charts(self):
        handoff = json.loads(MINI.read_text(encoding="utf-8"))
        assert "charts" in detect_features(handoff)

    def test_nested_primary_visual_chart_type(self):
        h = _non_chart_handoff()
        h["slides"][0]["layout_type"] = "other"
        h["slides"][0]["visual_spec"] = {
            "primary_visual": {"type": "line_chart", "steps_or_data": []}
        }
        assert "charts" in detect_features(h)

    def test_dual_chart_enables_charts(self):
        h = _non_chart_handoff()
        h["slides"][0]["layout_type"] = "dual_chart"
        assert "charts" in detect_features(h)

    def test_mvp1_stubs_never_auto_enabled(self):
        feats = detect_features(_chart_handoff())
        for fid in ("mermaid", "alpine", "swiper", "icons"):
            assert fid not in feats

    def test_empty_slides(self):
        assert detect_features({"slides": []}) == frozenset()


# ---------------------------------------------------------------------------
# P1.2 — plumb through render_deck
# ---------------------------------------------------------------------------

class TestRenderFeaturesMeta:
    def test_mini_run_meta_includes_charts(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert "charts" in run_meta["features_enabled"]
        assert run_meta["features_enabled"] == sorted(run_meta["features_enabled"])

    def test_mini_deck_meta_includes_charts(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "charts" in _deck_meta(html)["features_enabled"]

    def test_non_chart_omits_charts(self, tmp_path):
        handoff = tmp_path / "h.json"
        handoff.write_text(json.dumps(_non_chart_handoff()), encoding="utf-8")
        out = tmp_path / "out"
        render_deck(handoff, out, strict=False)
        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert "charts" not in run_meta["features_enabled"]
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "charts" not in _deck_meta(html)["features_enabled"]
        assert "fonts.googleapis.com" not in html


# ---------------------------------------------------------------------------
# P1.3 — force / suppress
# ---------------------------------------------------------------------------

class TestFeatureOverrides:
    def test_suppress_beats_detect(self):
        feats = resolve_features(_chart_handoff(), suppress=["charts"])
        assert "charts" not in feats

    def test_force_beats_detect(self):
        feats = resolve_features(_non_chart_handoff(), force=["charts"])
        assert "charts" in feats

    def test_suppress_beats_force(self):
        feats = resolve_features(
            _non_chart_handoff(), force=["charts"], suppress=["charts"]
        )
        assert "charts" not in feats

    def test_unknown_force_fails_closed(self):
        with pytest.raises(ValueError, match="unknown feature"):
            resolve_features(_non_chart_handoff(), force=["not-a-feature"])

    def test_unknown_suppress_fails_closed(self):
        with pytest.raises(ValueError, match="unknown feature"):
            resolve_features(_non_chart_handoff(), suppress=["nope"])

    def test_render_suppress_charts(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False, suppress_features=["charts"])
        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert "charts" not in run_meta["features_enabled"]

    def test_render_force_charts(self, tmp_path):
        handoff = tmp_path / "h.json"
        handoff.write_text(json.dumps(_non_chart_handoff()), encoding="utf-8")
        out = tmp_path / "out"
        render_deck(handoff, out, strict=False, force_features=["charts"])
        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert "charts" in run_meta["features_enabled"]

    def test_cli_force_feature(self, tmp_path):
        handoff = tmp_path / "h.json"
        handoff.write_text(json.dumps(_non_chart_handoff()), encoding="utf-8")
        out = tmp_path / "out"
        rc = main([
            "--handoff", str(handoff),
            "--out", str(out),
            "--force-feature", "charts",
        ])
        assert rc == 0
        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert "charts" in run_meta["features_enabled"]

    def test_cli_suppress_feature(self, tmp_path):
        out = tmp_path / "out"
        rc = main([
            "--handoff", str(MINI),
            "--out", str(out),
            "--suppress-feature", "charts",
        ])
        assert rc == 0
        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert "charts" not in run_meta["features_enabled"]

    def test_cli_unknown_force_fails(self, tmp_path):
        out = tmp_path / "out"
        rc = main([
            "--handoff", str(MINI),
            "--out", str(out),
            "--force-feature", "bogus",
        ])
        assert rc != 0


# ---------------------------------------------------------------------------
# P1.4 — size report + soft-warn
# ---------------------------------------------------------------------------

class TestSizeReport:
    def test_run_meta_records_html_bytes(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        html = (out / "presentation.html").read_bytes()
        assert run_meta["html_bytes"] == len(html)
        assert run_meta["html_bytes"] > 0

    def test_soft_warn_when_over_threshold(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(features_mod, "ADVISORY_HTML_BYTES", 1)
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        err = capsys.readouterr().err
        assert "size" in err.lower() or "bytes" in err.lower()
        assert "1" in err

    def test_soft_warn_does_not_fail_render(self, tmp_path, monkeypatch):
        monkeypatch.setattr(features_mod, "ADVISORY_HTML_BYTES", 1)
        out = tmp_path / "out"
        result = render_deck(MINI, out, strict=False)
        assert result["ok"] or result["presentation"]
        assert (out / "presentation.html").is_file()
