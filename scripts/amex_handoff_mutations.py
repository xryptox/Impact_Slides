"""Bounded Amex handoff mutations applied before a fidelity simulation pass.

These correct authoring defects in archived handoffs. They do **not** change
renderer defaults. Each mutation is issue-scoped and idempotent.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

# Issue #148 — PDF physical pages / deck slides 13–14.
# v10 handoff requested line marks and swapped credit-pane semantics.
_S13 = 13
_S14 = 14

_S13_STEPS = [
    {"label": "Q1'25", "values": {"Total Balances": 7, "Billed Business": 6}},
    {"label": "Q2'25", "values": {"Total Balances": 6, "Billed Business": 7}},
    {"label": "Q3'25", "values": {"Total Balances": 7, "Billed Business": 8}},
    {"label": "Q4'25", "values": {"Total Balances": 7, "Billed Business": 8}},
    {"label": "Q1'26", "values": {"Total Balances": 7, "Billed Business": 9}},
]

_S14_LEFT_STEPS = [
    {"label": "Q1'25", "value": 1.3},
    {"label": "Q2'25", "value": 1.3},
    {"label": "Q3'25", "value": 1.3},
    {"label": "Q4'25", "value": 1.3},
    {"label": "Q1'26", "value": 1.3},
]

_S14_RIGHT_STEPS = [
    {"label": "Q1'25", "value": 2.1},
    {"label": "Q2'25", "value": 2.0},
    {"label": "Q3'25", "value": 1.9},
    {"label": "Q4'25", "value": 2.1},
    {"label": "Q1'26", "value": 2.0},
]


def _slide(handoff: dict[str, Any], number: int) -> dict[str, Any]:
    for s in handoff.get("slides") or []:
        if int(s.get("slide_number", -1)) == number:
            return s
    raise KeyError(f"handoff missing slide_number={number}")


def apply_issue_148_bar_semantics(handoff: dict[str, Any]) -> dict[str, Any]:
    """Restore vertical bars + PDF pane order on Amex slides 13 and 14.

    - Slide 13: grouped vertical bar chart (Total Balances / Billed Business).
    - Slide 14: dual_chart of vertical bars; left = 30+ Days Past Due (~1.3%),
      right = Net Write-Off Rates (~2%).
    """
    out = handoff  # caller may pass an already-copied dict
    s13 = _slide(out, _S13)
    s13["layout_type"] = "grouped_bar_chart"
    s13["visual_spec"] = {
        "primary_visual": {
            "type": "grouped_bar_chart",
            "steps_or_data": deepcopy(_S13_STEPS),
            "chart_config": {
                "series_names": ["Total Balances", "Billed Business"],
                "series_colors": ["#00175A", "#006FCF"],
                "y_axis_min": 0,
                "y_axis_max": 15,
                "y_axis_ticks": [0, 5, 10, 15],
                "y_axis_unit": "%",
                "y_axis_label": "%",
            },
        }
    }
    s13["speaker_notes"] = "Grouped vertical bars: balances vs billed business."

    s14 = _slide(out, _S14)
    s14["layout_type"] = "dual_chart"
    s14["content"] = dict(s14.get("content") or {})
    s14["content"]["subtitle"] = "30+ days past due and net write-off rates"
    s14["visual_spec"] = {
        "primary_visual": {
            "type": "grouped_bar_chart",
            "heading": "30+ Days Past Due",
            "steps_or_data": deepcopy(_S14_LEFT_STEPS),
            "chart_config": {
                "series_names": ["30+ Days Past Due"],
                "series_colors": ["#00175A"],
                "y_axis_min": 0,
                "y_axis_max": 3,
                "y_axis_unit": "%",
            },
        },
        "secondary_visual": {
            "type": "grouped_bar_chart",
            "heading": "Net Write-Off Rates",
            "steps_or_data": deepcopy(_S14_RIGHT_STEPS),
            "chart_config": {
                "series_names": ["Net Write-Off Rates"],
                "series_colors": ["#006FCF"],
                "y_axis_min": 0,
                "y_axis_max": 3,
                "y_axis_unit": "%",
            },
        },
    }
    s14["speaker_notes"] = (
        "PDF pane order: 30+ DPD left (~1.3%), net write-offs right (~2%)."
    )
    return out


def apply_all(handoff: dict[str, Any]) -> dict[str, Any]:
    """Apply every bounded Amex handoff mutation known to this module."""
    return apply_issue_148_bar_semantics(handoff)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="Source handoff JSON")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Destination handoff JSON (issue #148 bars applied)",
    )
    args = p.parse_args(argv)
    data = json.loads(args.input.read_text(encoding="utf-8"))
    apply_all(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
