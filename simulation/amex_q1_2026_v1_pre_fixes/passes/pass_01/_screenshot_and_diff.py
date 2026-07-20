"""Screenshot presentation.html slides and pixel-diff vs PDF page PNGs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, ImageStat
from playwright.sync_api import sync_playwright

PASS = Path(__file__).resolve().parent
OUT = PASS / "output"
SHOTS = PASS / "screenshots"
HTML = OUT / "presentation.html"
PDF_DIR = PASS.parent.parent / "extracted"
VIEW_W, VIEW_H = 1920, 1080


def ssim_approx(a: Image.Image, b: Image.Image) -> float:
    """Cheap structural-ish score via normalized MAE on downscaled luminance."""
    a_g = ImageOps.grayscale(a.resize((320, 180), Image.Resampling.BILINEAR))
    b_g = ImageOps.grayscale(b.resize((320, 180), Image.Resampling.BILINEAR))
    diff = ImageChops.difference(a_g, b_g)
    mae = ImageStat.Stat(diff).mean[0] / 255.0
    return max(0.0, 1.0 - mae)


def pixel_similarity(a: Image.Image, b: Image.Image) -> float:
    a_r = a.convert("RGB").resize((VIEW_W, VIEW_H), Image.Resampling.BILINEAR)
    b_r = b.convert("RGB").resize((VIEW_W, VIEW_H), Image.Resampling.BILINEAR)
    diff = ImageChops.difference(a_r, b_r)
    # mean channel error
    st = ImageStat.Stat(diff)
    mae = sum(st.mean) / (3 * 255.0)
    return max(0.0, 1.0 - mae)


def side_by_side(pdf: Image.Image, html: Image.Image, label: str, sim: float) -> Image.Image:
    tw, th = 960, 540
    left = pdf.convert("RGB").resize((tw, th), Image.Resampling.BILINEAR)
    right = html.convert("RGB").resize((tw, th), Image.Resampling.BILINEAR)
    canvas = Image.new("RGB", (tw * 2 + 20, th + 40), (30, 30, 30))
    canvas.paste(left, (0, 40))
    canvas.paste(right, (tw + 20, 40))
    draw = ImageDraw.Draw(canvas)
    draw.text((10, 10), f"{label}  PDF (left) vs HTML (right)  similarity={sim*100:.1f}%", fill=(240, 240, 240))
    return canvas


def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    if not HTML.exists():
        print("missing presentation.html", file=sys.stderr)
        sys.exit(1)

    uri = HTML.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": VIEW_W, "height": VIEW_H}, device_scale_factor=1)
        page.goto(uri, wait_until="networkidle", timeout=120_000)
        # Allow Chart.js paint
        page.wait_for_timeout(1500)

        slides = page.locator(".slide")
        n = slides.count()
        print(f"found {n} .slide elements")
        if n == 0:
            # fallback: sections
            slides = page.locator("section.slide, section[class*='slide'], .gl-slide")
            n = slides.count()
            print(f"fallback count {n}")

        # Discover structure once
        if n == 0:
            page.screenshot(path=str(SHOTS / "full_page_fallback.png"), full_page=True)
            html_snip = page.content()[:2000]
            (SHOTS / "dom_snip.html").write_text(html_snip, encoding="utf-8")
            print("no slides found")
            browser.close()
            sys.exit(2)

        results = []
        for i in range(n):
            el = slides.nth(i)
            # activate slide if deck uses active class
            page.evaluate(
                """(idx) => {
                  const all = document.querySelectorAll('.slide');
                  all.forEach((s,j) => {
                    s.classList.toggle('active', j===idx);
                    s.style.display = (j===idx ? '' : s.style.display);
                  });
                  // common boardroom pattern: data-index navigation
                  if (window.JumpToSlide) { try { window.JumpToSlide(idx); } catch(e){} }
                  if (window.deck && window.deck.slide) { try { window.deck.slide(idx); } catch(e){} }
                }""",
                i,
            )
            page.wait_for_timeout(200)
            shot_path = SHOTS / f"html_slide_{i:02d}.png"
            el.screenshot(path=str(shot_path))

            pdf_path = PDF_DIR / f"pdf_page_{i:02d}.png"
            if not pdf_path.exists():
                print(f"missing pdf {pdf_path}")
                continue
            pdf_im = Image.open(pdf_path)
            html_im = Image.open(shot_path)
            sim = pixel_similarity(pdf_im, html_im)
            ssim = ssim_approx(pdf_im, html_im)
            combo = side_by_side(pdf_im, html_im, f"slide {i:02d}", sim)
            combo_path = SHOTS / f"compare_{i:02d}.png"
            combo.save(combo_path)
            results.append(
                {
                    "index": i,
                    "similarity_pct": round(sim * 100, 2),
                    "ssim_approx_pct": round(ssim * 100, 2),
                    "html_shot": str(shot_path.name),
                    "compare": str(combo_path.name),
                    "pdf": str(pdf_path.name),
                }
            )
            print(f"slide {i:02d}: sim={sim*100:.1f}% ssim~={ssim*100:.1f}%")

        browser.close()

    # overall strip of first 12 compares into diff.png
    if results:
        thumbs = []
        for r in results[:12]:
            im = Image.open(SHOTS / r["compare"]).resize((640, 200), Image.Resampling.BILINEAR)
            thumbs.append(im)
        cols = 2
        rows = (len(thumbs) + cols - 1) // cols
        grid = Image.new("RGB", (640 * cols, 200 * rows), (20, 20, 20))
        for i, im in enumerate(thumbs):
            grid.paste(im, ((i % cols) * 640, (i // cols) * 200))
        grid.save(PASS / "diff.png")

    summary = {
        "pass": 1,
        "n_slides": len(results),
        "mean_similarity_pct": round(
            sum(r["similarity_pct"] for r in results) / max(1, len(results)), 2
        ),
        "mean_ssim_approx_pct": round(
            sum(r["ssim_approx_pct"] for r in results) / max(1, len(results)), 2
        ),
        "per_slide": results,
    }
    (PASS / "diff_scores.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("n_slides", "mean_similarity_pct", "mean_ssim_approx_pct")}, indent=2))


if __name__ == "__main__":
    main()
