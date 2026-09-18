"""Recapture layout-stress linear slides at 1920x1080 after wrap packing."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT)]

from impact_slides.renderer_v3 import render_deck  # noqa: E402
from scripts.simulation_probe import activate_slide  # noqa: E402

HANDOFF = ROOT / "tests/fixtures/renderer_v3/linear_wrap_stress.json"
OUT = Path(__file__).resolve().parent
HTML_DIR = OUT / "html"
SLIDES = list(range(1, 7)) + list(range(11, 21)) + list(range(51, 61))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        out = Path(temp) / "out"
        result = render_deck(HANDOFF, out, strict=True)
        html = out / "presentation.html"
        meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        plans = {
            p["slide_number"]: p
            for p in meta["plans"]
            if p["role"] in {"process_flow", "timeline", "data_pipeline"}
        }
        captures = {}
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": 1920, "height": 1080}, device_scale_factor=1
            )
            page.goto(html.resolve().as_uri(), wait_until="load")
            page.evaluate(
                """() => {
                  const s = document.querySelector('.deck-stage');
                  if (!s) return;
                  s.style.width = '1920px';
                  s.style.transform = 'none';
                  [...s.children].forEach((x) => {
                    x.style.transform = 'none';
                    x.style.marginBottom = '0px';
                    x.style.width = '1920px';
                    x.style.height = '1080px';
                  });
                }"""
            )
            for n in SLIDES:
                plan = plans[n]
                activate_slide(page, n, plan["layout_type"])
                page.evaluate(
                    """(sn) => {
                      const el = document.querySelector(
                        'section.slide[data-slide-number="' + sn + '"]'
                      );
                      el.scrollIntoView({block: 'start', inline: 'nearest'});
                    }""",
                    n,
                )
                png = HTML_DIR / f"slide_{n:03d}.png"
                page.locator(
                    f'section.slide[data-slide-number="{n}"]'
                ).screenshot(path=str(png), animations="disabled")
                layout = page.evaluate(
                    """(n) => {
                      const el = document.querySelector(
                        'section.slide[data-slide-number="' + n + '"]'
                      );
                      const recipe = el.querySelector(
                        '.process-flow, .timeline, .data-pipeline'
                      );
                      const fallback = el.querySelector('.linear-fallback');
                      return {
                        layout: el.getAttribute('data-layout'),
                        recipe_class: recipe ? recipe.className : '',
                        fallback: Boolean(fallback),
                      };
                    }""",
                    n,
                )
                captures[str(n)] = {
                    "png": png.relative_to(ROOT).as_posix(),
                    "sha256": sha256(png),
                    "layout": layout["layout"],
                    "recipe_class": layout["recipe_class"],
                    "fallback": layout["fallback"],
                    "plan_fallback": plan.get("fallback"),
                    "role_sizes": plan.get("role_sizes"),
                }
            browser.close()
    (OUT / "recapture_report.json").write_text(
        json.dumps(
            {
                "viewport": [1920, 1080],
                "source_handoff": HANDOFF.relative_to(ROOT).as_posix(),
                "source_sha256": sha256(HANDOFF),
                "render_status": result["status"],
                "ok": result["ok"],
                "captures": captures,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
