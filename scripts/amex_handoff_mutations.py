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
    Missing either slide is a no-op for that slide (partial handoffs ok).
    """
    out = handoff  # caller may pass an already-copied dict
    try:
        s13 = _slide(out, _S13)
    except KeyError:
        s13 = None
    if s13 is not None:
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

    try:
        s14 = _slide(out, _S14)
    except KeyError:
        s14 = None
    if s14 is not None:
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


# Issue #158 — PDF physical page / deck slide 28 multi_panel pane titles.
# v10 handoff put dollar stack totals in tile top_total pseudo-titles.
_S28 = 28
_S28_SUBTITLE = "$ in billions"
_S28_TILES = (
    ("Funding Mix", ["$210", "$219"]),
    ("Deposit Programs", ["$151", "$157"]),
)


def apply_issue_158_slide28_pane_titles(handoff: dict[str, Any]) -> dict[str, Any]:
    """Drop slide-28 top_total pseudo-titles; add pane subtitles.

    Keeps Funding Mix / Deposit Programs as pane headings (via label),
    explicit stack_total_labels as the only dollar totals, and the #138
    FDIC side_callout + exterior segment names unchanged. Does not remove
    legitimate top_total on other slides.
    """
    out = handoff
    try:
        s28 = _slide(out, _S28)
    except KeyError:
        return out
    if str(s28.get("layout_type") or "") != "multi_panel":
        return out
    vs = s28.get("visual_spec") or {}
    pv = vs.get("primary_visual") if isinstance(vs, dict) else None
    tiles = pv.get("tiles") if isinstance(pv, dict) else None
    if not isinstance(tiles, list):
        return out
    known = {name for name, _ in _S28_TILES}
    for tile in tiles:
        if not isinstance(tile, dict) or str(tile.get("kind") or "") != "chart":
            continue
        label = str(tile.get("label") or tile.get("heading") or "").strip()
        # Only the two funding board panes; leave unrelated multi_panel tiles.
        if label not in known and str(tile.get("heading") or "").strip() not in known:
            continue
        tile.pop("top_total", None)
        tile["subtitle"] = _S28_SUBTITLE
        # Prefer stable label heading; do not invent parallel keys if label set.
        if not str(tile.get("label") or "").strip() and str(
            tile.get("heading") or ""
        ).strip():
            tile["label"] = str(tile["heading"]).strip()
        cfg = tile.get("chart_config")
        if not isinstance(cfg, dict):
            cfg = {}
            tile["chart_config"] = cfg
        # Preserve existing stack_total_labels when present; fill known defaults.
        if not cfg.get("stack_total_labels"):
            for name, totals in _S28_TILES:
                if label == name or str(tile.get("heading") or "").strip() == name:
                    cfg["stack_totals"] = True
                    cfg["stack_total_labels"] = list(totals)
                    break
    return out


def apply_all(handoff: dict[str, Any]) -> dict[str, Any]:
    """Apply every bounded Amex handoff mutation known to this module."""
    out = apply_issue_148_bar_semantics(handoff)
    return apply_issue_158_slide28_pane_titles(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="Source handoff JSON")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Destination handoff JSON (issues #148/#158 mutations applied)",
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
