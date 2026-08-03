"""Screenshot each deck slide at 1920x1080 and build side-by-side vs PDF rasters."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright


def activate(page, i: int) -> None:
    page.evaluate(
        """(i) => {
        document.querySelectorAll('section.slide').forEach(s => s.classList.remove('active'));
        const ss = document.querySelectorAll('section.slide');
        if (ss[i]) ss[i].classList.add('active');
    }""",
        i,
    )
    page.wait_for_timeout(900)


def main() -> int:
    html = Path(sys.argv[1] if len(sys.argv) > 1 else "simulation/amex_q1_2026/passes/pass_01/output/presentation.html")
    pass_dir = html.parent.parent
    shot_dir = pass_dir / "screenshots"
    sbs_dir = pass_dir / "side_by_side"
    pdf_dir = Path("simulation/amex_q1_2026/extracted")
    shot_dir.mkdir(parents=True, exist_ok=True)
    sbs_dir.mkdir(parents=True, exist_ok=True)

    n = int(sys.argv[2]) if len(sys.argv) > 2 else 44
    # optional focus list
    focus = None
    if len(sys.argv) > 3:
        focus = [int(x) for x in sys.argv[3].split(",")]

    url = html.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(400)

        indices = focus if focus is not None else list(range(n))
        for i in indices:
            activate(page, i)
            dest = shot_dir / f"html_slide_{i:02d}.png"
            page.screenshot(path=str(dest), full_page=False)
            print("shot", dest.name)

            pdf_path = pdf_dir / f"pdf_page_{i:02d}.png"
            if pdf_path.exists():
                pdf = Image.open(pdf_path).convert("RGB")
                html_im = Image.open(dest).convert("RGB")
                # match heights
                target_h = 540
                def resize_h(im, h):
                    w = int(im.width * (h / im.height))
                    return im.resize((w, h), Image.Resampling.LANCZOS)
                pdf_r = resize_h(pdf, target_h)
                html_r = resize_h(html_im, target_h)
                gap = 8
                label_h = 28
                canvas = Image.new(
                    "RGB",
                    (pdf_r.width + html_r.width + gap, target_h + label_h),
                    (245, 245, 245),
                )
                d = ImageDraw.Draw(canvas)
                try:
                    font = ImageFont.truetype("arial.ttf", 16)
                except Exception:
                    font = ImageFont.load_default()
                d.text((4, 4), f"PDF p{i+1} / slide {i:02d}", fill=(0, 0, 0), font=font)
                d.text((pdf_r.width + gap + 4, 4), f"HTML slide {i:02d}", fill=(0, 0, 0), font=font)
                canvas.paste(pdf_r, (0, label_h))
                canvas.paste(html_r, (pdf_r.width + gap, label_h))
                out = sbs_dir / f"compare_{i:02d}.png"
                canvas.save(out, optimize=True)
                print("sbs", out.name)
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
