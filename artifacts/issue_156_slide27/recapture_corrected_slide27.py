"""Capture archived v10 and corrected Amex slide 27 with #146's ready gate."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

from amex_handoff_mutations import apply_issue_156_slide27_scenarios  # noqa: E402
from simulation_probe import wait_for_paint_ready_charts  # noqa: E402
from impact_slides.renderer_v2 import render_deck  # noqa: E402

SOURCE = Path(
    r"C:/Users/Ag1Le/Documents/Impact_Slides-gnhf-worktrees/"
    r"objective-produce-an-74065a/simulation/amex_q1_2026/"
    r"passes/pass_01/handoff.json"
)
OUT = Path(__file__).resolve().parent


def _capture(handoff: dict, name: str) -> dict:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        deck = root / "handoff.json"
        deck.write_text(json.dumps(handoff), encoding="utf-8")
        output = root / "output"
        render_deck(deck, output, strict=False)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.goto((output / "presentation.html").resolve().as_uri())
            row = wait_for_paint_ready_charts(page, 27, "dual_chart")
            png = OUT / name
            page.screenshot(path=str(png), full_page=False)
            browser.close()
    return {"charts": row["charts"], "png": png.relative_to(ROOT).as_posix()}


def main() -> int:
    if not SOURCE.is_file():
        print(f"missing archived handoff: {SOURCE}", file=sys.stderr)
        return 2
    original = json.loads(SOURCE.read_text(encoding="utf-8"))
    corrected = json.loads(SOURCE.read_text(encoding="utf-8"))
    apply_issue_156_slide27_scenarios(corrected)
    captures = {
        "archived_v10": _capture(original, "archived_v10_slide27_paint_ready.png"),
        "corrected": _capture(corrected, "corrected_slide27_paint_ready.png"),
    }
    (OUT / "recapture_report.json").write_text(
        json.dumps(
            {
                "viewport": [1920, 1080],
                "source_handoff": str(SOURCE),
                "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                "slide": 27,
                "layout": "dual_chart",
                "captures": captures,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
