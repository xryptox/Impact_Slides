"""Render a single slide from a handoff to a PNG (Playwright, 1920x1080).

Used for the round-3 fidelity done bar: each ticket posts a fresh
screenshot of the affected slide as issue evidence.

Usage:
    python scripts/render_slide_shot.py HANDOFF_JSON SLIDE_NUMBER OUT_PNG
        [--pdf PDF_PAGE_PNG]     # optional: emit side-by-side compare PNG
        [--full-deck]            # handoff already contains the full deck;
                                 # default: wrap the single slide in a 2-slide deck

Examples:
    python scripts/render_slide_shot.py sim/passes/pass_03/handoff.json 6 out.png --full-deck
    python scripts/render_slide_shot.py h.json 2 out.png --pdf extracted/pdf_page_05.png
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from impact_slides.renderer_v2 import render_deck  # noqa: E402

VIEW_W, VIEW_H = 1920, 1080


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("handoff", type=Path)
    ap.add_argument("slide_number", type=int, help="1-based slide number in the handoff")
    ap.add_argument("out_png", type=Path)
    ap.add_argument("--pdf", type=Path, default=None, help="PDF page PNG for side-by-side")
    ap.add_argument("--full-deck", action="store_true")
    args = ap.parse_args()

    handoff = json.loads(args.handoff.read_text(encoding="utf-8"))
    slides = handoff["slides"]
    target = next(
        (s for s in slides if int(s.get("slide_number") or 0) == args.slide_number), None
    )
    if target is None:
        print(f"slide_number {args.slide_number} not found in handoff", file=sys.stderr)
        return 2

    work = Path(tempfile.mkdtemp(prefix="slide_shot_"))
    if args.full_deck:
        deck_path = work / "handoff.json"
        deck_path.write_text(json.dumps(handoff), encoding="utf-8")
        slide_idx = slides.index(target)
    else:
        cover = {
            "slide_number": 1,
            "layout_type": "title_or_opening",
            "title": handoff.get("title") or "slide shot",
            "content": {},
            "speaker_notes": "slide_shot cover",
        }
        single = {**target, "slide_number": 2}
        deck_path = work / "handoff.json"
        deck_path.write_text(
            json.dumps({**handoff, "slides": [cover, single]}), encoding="utf-8"
        )
        slide_idx = 1

    out_dir = work / "out"
    render_deck(deck_path, out_dir, strict=False)
    html_path = out_dir / "presentation.html"

    args.out_png.parent.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": VIEW_W, "height": VIEW_H})
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.wait_for_timeout(1200)
        # Deck chrome hides inactive slides — force-activate the target.
        page.evaluate(
            """(idx) => {
              const all = document.querySelectorAll('.slide');
              all.forEach((s,j) => { s.classList.toggle('active', j===idx); });
              if (window.JumpToSlide) { try { window.JumpToSlide(idx); } catch(e){} }
              if (window.deck && window.deck.slide) { try { window.deck.slide(idx); } catch(e){} }
            }""",
            slide_idx,
        )
        page.wait_for_timeout(500)
        page.locator(".slide").nth(slide_idx).screenshot(path=str(args.out_png))
        browser.close()

    if args.pdf and args.pdf.exists():
        from PIL import Image, ImageDraw

        html_img = Image.open(args.out_png).convert("RGB")
        pdf_img = Image.open(args.pdf).convert("RGB")
        tw, th = 960, 540
        left = pdf_img.resize((tw, th), Image.Resampling.BILINEAR)
        right = html_img.resize((tw, th), Image.Resampling.BILINEAR)
        canvas = Image.new("RGB", (tw * 2 + 20, th + 40), (30, 30, 30))
        canvas.paste(left, (0, 40))
        canvas.paste(right, (tw + 20, 40))
        ImageDraw.Draw(canvas).text(
            (10, 10),
            f"slide {args.slide_number}  PDF (left) vs HTML (right)",
            fill=(240, 240, 240),
        )
        cmp_path = args.out_png.with_name(args.out_png.stem + "_compare.png")
        canvas.save(cmp_path)
        print(f"compare: {cmp_path}")

    print(f"shot: {args.out_png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
