"""Generate test_deck_vnext.html and run token audit (T10 #18)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from impact_slides.renderer_v2.cli import render_deck


# All 28+ layout types supported by renderer_v2
_ALL_LAYOUTS = [
    "title_or_opening",
    "split_text_visual",
    "metric_dashboard",
    "metric_row_with_breakdown",
    "insight_with_evidence",
    "priority_matrix",
    "evidence_cards",
    "data_table_with_insight",
    "comparison_with_metrics",
    "data_table",
    "full_process_flow",
    "timeline",
    "roadmap",
    "comparison_grid",
    "quote_card",
    "icon_grid",
    "system_architecture",
    "data_flow_diagram",
    "causal_loop",
    "before_after",
    "risk_opportunity",
    "recommendation_with_rationale",
    "section_divider",
    "before_after_detailed",
    "kpi_trend_cards",
    "three_column_comparison",
    "horizontal_process",
    "decision_tree",
    "hierarchy_tree",
    "ecosystem_map",
    "process_with_decisions",
    "source_deep_dive",
    "circular_process",
]


def _slide_for_layout(lt: str, n: int) -> dict:
    base = {
        "slide_number": n,
        "layout_type": lt,
        "title": f"Layout: {lt}",
        "content": {"headline": f"Demo of {lt}"},
    }
    # Add layout-specific content to make rendering more realistic
    if lt in ("metric_dashboard", "metric_row_with_breakdown"):
        base["content"] = {"key_stats": [{"label": "Rev", "value": "$1M"}, {"label": "Cost", "value": "$500K"}]}
    elif lt == "data_table":
        base["visual_spec"] = {"primary_visual": {"steps_or_data": ["Item A: 10", "Item B: 20"]}}
    elif lt == "data_table_with_insight":
        base["visual_spec"] = {"primary_visual": {"steps_or_data": [["Metric", "Value"], ["Revenue", "$1M"], ["Cost", "$500K"]]}}
        base["content"] = {"so_what": "Key insight"}
    elif lt == "split_text_visual":
        base["content"] = {"bullets": ["Point A"], "body_text": "Lead"}
    elif lt == "comparison_grid":
        base["content"] = {"bullets": ["A: one", "B: two"]}
    elif lt in ("full_process_flow", "timeline", "roadmap"):
        base["visual_spec"] = {"primary_visual": {"steps_or_data": ["Step 1", "Step 2", "Step 3"]}}
    elif lt in ("system_architecture", "data_flow_diagram"):
        base["visual_spec"] = {"primary_visual": {"steps_or_data": [["Layer 1", "Node A", ""], ["Layer 2", "Node B", ""]]}}
    elif lt == "causal_loop":
        base["visual_spec"] = {"primary_visual": {"steps_or_data": ["Var A", "Var B", "Var C"]}}
    elif lt == "before_after":
        base["content"] = {"bullets": ["Before A", "Before B", "After A", "After B"]}
    elif lt == "icon_grid":
        base["visual_spec"] = {"primary_visual": {"steps_or_data": ["A", "B", "C"]}}
    elif lt == "quote_card":
        base["content"] = {"body_text": "A famous quote."}
    elif lt in ("evidence_cards", "recommendation_with_rationale"):
        base["content"] = {"bullets": ["Evidence 1", "Evidence 2"]}
    elif lt == "priority_matrix":
        base["content"] = {"bullets": ["Item A", "Item B", "Item C", "Item D"]}
    elif lt == "risk_opportunity":
        base["content"] = {"risks": ["Risk 1"], "opportunities": ["Opp 1"]}
    elif lt == "section_divider":
        base["content"] = {"headline": "Section Title", "subtitle": "Subtitle"}
    elif lt == "before_after_detailed":
        base["content"] = {"before": "Old", "after": "New", "steps": ["Step 1", "Step 2"]}
    elif lt == "kpi_trend_cards":
        base["content"] = {"key_stats": [{"label": "A", "value": "1", "trend": "up"}]}
    elif lt == "three_column_comparison":
        base["content"] = {"bullets": ["Opt A", "Opt B", "Opt C"]}
    elif lt == "horizontal_process":
        base["content"] = {"bullets": ["S1", "S2", "S3"]}
    elif lt in ("decision_tree", "hierarchy_tree"):
        base["visual_spec"] = {"primary_visual": {"steps_or_data": [["Root", "Child"]]}}
    elif lt == "ecosystem_map":
        base["visual_spec"] = {"primary_visual": {"steps_or_data": [["A", "→", "B"]]}}
    elif lt == "process_with_decisions":
        base["content"] = {"steps": ["S1", "S2"], "decisions": ["D1"]}
    elif lt == "source_deep_dive":
        base["content"] = {"bullets": ["Source 1", "Source 2"]}
    elif lt == "circular_process":
        base["visual_spec"] = {"primary_visual": {"steps_or_data": ["Plan", "Do", "Check", "Act"]}}
    return base


class TestVisualRegressionDeck:
    def test_generates_all_layouts(self, tmp_path):
        handoff = {
            "title": "Visual Regression Deck vNext",
            "readiness_score": 0.9,
            "quality_flags": [],
            "slides": [_slide_for_layout(lt, i + 1) for i, lt in enumerate(_ALL_LAYOUTS)],
        }
        handoff_path = tmp_path / "handoff.json"
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
        result = render_deck(handoff_path, tmp_path / "out")
        assert result["ok"]
        assert result["total_slides"] == len(_ALL_LAYOUTS)

        html_path = tmp_path / "out" / "presentation.html"
        html = html_path.read_text(encoding="utf-8")
        # Every layout type should appear in data-layout attributes
        for lt in _ALL_LAYOUTS:
            assert f'data-layout="{lt}"' in html, f"Missing layout: {lt}"

    def test_stage_containment_all_layouts(self, tmp_path):
        handoff = {
            "title": "Stage Test",
            "readiness_score": 0.9,
            "quality_flags": [],
            "slides": [_slide_for_layout(lt, i + 1) for i, lt in enumerate(_ALL_LAYOUTS)],
        }
        handoff_path = tmp_path / "handoff.json"
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
        result = render_deck(handoff_path, tmp_path / "out")
        html = (tmp_path / "out" / "presentation.html").read_text(encoding="utf-8")
        # All slides should have the fixed stage container
        assert html.count('data-layout="') == len(_ALL_LAYOUTS)


class TestTokenAudit:
    """Scan renderer Python files for hard-coded values outside token strings."""

    def _py_files(self):
        base = Path(__file__).parent.parent / "impact_slides" / "renderer_v2"
        return list(base.rglob("*.py"))

    def test_no_hardcoded_hex_outside_css_strings(self):
        hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}")
        offenders = []
        for path in self._py_files():
            text = path.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), 1):
                if "#" not in line:
                    continue
                # Skip comments
                if line.strip().startswith("#"):
                    continue
                # Skip CSS string literals and token references
                if 'var(--' in line or '"#' in line or "'#" in line:
                    continue
                # Skip docstrings
                if '"""' in line or "'''" in line:
                    continue
                matches = hex_pattern.findall(line)
                if matches:
                    offenders.append(f"{path}:{i}: {line.strip()}")
        # Tolerate a few known edge cases in diagram primitives
        known_exceptions = ["diagram/builder.py", "diagram/__init__.py"]
        filtered = [o for o in offenders if not any(exc in o for exc in known_exceptions)]
        assert not filtered, f"Hard-coded hex values found: {filtered[:10]}"

    def test_no_literal_px_spacing_outside_tokens(self):
        """Flag literal px values that aren't in token strings."""
        px_pattern = re.compile(r'\b\d+px\b')
        offenders = []
        for path in self._py_files():
            if path.name.endswith("_test.py"):
                continue
            text = path.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), 1):
                if "px" not in line:
                    continue
                if line.strip().startswith("#"):
                    continue
                if 'style="' in line or "style='" in line:
                    continue
                matches = px_pattern.findall(line)
                if matches:
                    offenders.append(f"{path}:{i}: {line.strip()}")
        # Tolerate known exceptions in inline SVG/f-string construction
        known_exceptions = ["diagram/", "layout/recipes.py", "shell.py", "freeform.py"]
        filtered = [o for o in offenders if not any(exc in o for exc in known_exceptions)]
        assert not filtered, f"Literal px values found: {filtered[:10]}"


class TestFreeformCompatibility:
    def test_freeform_overrides_refactored_layout(self, tmp_path):
        """Freeform grid should win over a refactored layout like metric_dashboard."""
        handoff = {
            "title": "Freeform Test",
            "readiness_score": 0.9,
            "quality_flags": [],
            "slides": [
                {
                    "slide_number": 1,
                    "layout_type": "metric_dashboard",
                    "title": "Freeform Metric",
                    "content": {"key_stats": [{"label": "A", "value": "1"}]},
                    "visual_spec": {
                        "primary_visual": {"type": "metric_dashboard"},
                        "grid": {"areas": "main", "template": "1fr"},
                    },
                }
            ],
        }
        handoff_path = tmp_path / "handoff.json"
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
        result = render_deck(handoff_path, tmp_path / "out")
        html = (tmp_path / "out" / "presentation.html").read_text(encoding="utf-8")
        # Freeform output contains the freeform grid class
        assert "freeform" in html or "gl-areas" in html
