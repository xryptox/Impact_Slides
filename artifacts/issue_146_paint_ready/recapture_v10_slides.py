"""Re-capture archived v10 slides 9/12/27 with paint-ready wait (#146)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from simulation_probe import wait_for_paint_ready_charts  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

HTML = Path(
    r"C:/Users/Ag1Le/Documents/Impact_Slides-gnhf-worktrees/"
    r"objective-produce-an-74065a/simulation/amex_q1_2026/"
    r"passes/pass_01/output/presentation.html"
)
OUT = Path(__file__).resolve().parent

TARGETS = [
    (9, "line_chart"),
    (12, "chart_hero_dual"),
    (27, "dual_chart"),
]


def main() -> int:
    if not HTML.is_file():
        print("missing archived html", HTML, file=sys.stderr)
        return 2
    report = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(HTML.resolve().as_uri(), wait_until="networkidle")
        for sn, layout in TARGETS:
            row = wait_for_paint_ready_charts(page, sn, layout, timeout_ms=10000)
            dest = OUT / f"html_slide{sn:02d}_{layout}_paint_ready.png"
            page.screenshot(path=str(dest), full_page=False)
            charts = row["charts"]
            assert charts, (sn, row)
            for c in charts:
                assert c["width"] > 0 and c["height"] > 0, c
                ca = c["chart_area"]
                assert ca["width"] > 0 and ca["height"] > 0, c
            rel = dest.relative_to(ROOT).as_posix()
            report.append(
                {"slide": sn, "layout": layout, "charts": charts, "png": rel}
            )
            print("OK", sn, layout, charts)
        browser.close()
    (OUT / "recapture_report.json").write_text(
        json.dumps(
            {"viewport": [1920, 1080], "source_html": str(HTML), "rows": report},
            indent=2,
        ),
        encoding="utf-8",
    )
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
