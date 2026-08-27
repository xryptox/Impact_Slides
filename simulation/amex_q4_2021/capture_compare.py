"""Q4 2021 PDF vs renderer_v3 capture: 1920x1080 halves, 3840x1080 SBS."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from simulation_probe import ProbeError, measured_tick_styles, wait_for_paint_ready_charts

PDF = Path(r"C:/Users/Ag1Le/Downloads/Q4-2021-Earnings-Presentation.pdf")
SHA = "8e113208a6df838861fc06cdbfb82514f01f43c42a21e02005801f8fdf545e21"
HANDOFF = Path(__file__).with_name("handoff_v1.json")
HTML = Path(__file__).parent / "passes" / "pass_01" / "renderer_v3_out" / "presentation.html"
OUT = Path(__file__).parent / "passes" / "pass_01" / "compare"
CHART_LAYOUTS = {"single_chart", "dual_chart", "chart_hero_dual"}
W, H = 1920, 1080


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_png(path: Path, size: tuple[int, int]) -> None:
    with Image.open(path) as im:
        if im.size != size:
            raise SystemExit(f"{path} size {im.size} != {size}")


def rasterize_pdf(pdf_dir: Path, n_pages: int) -> None:
    import fitz

    doc = fitz.open(PDF)
    if doc.page_count != n_pages:
        raise SystemExit(f"PDF pages {doc.page_count} != {n_pages}")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    for i in range(n_pages):
        page = doc[i]
        rect = page.rect
        mat = fitz.Matrix(W / rect.width, H / rect.height)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        dest = pdf_dir / f"slide_{i + 1:02d}.png"
        pix.save(str(dest))
        if pix.width != W or pix.height != H:
            Image.open(dest).resize((W, H), Image.Resampling.LANCZOS).save(dest)
        assert_png(dest, (W, H))
    doc.close()


def identity_from_page(page) -> list[dict]:
    rows = page.evaluate(
        """() => {
          const nodes = [...document.querySelectorAll('section.slide')];
          return nodes.map((el) => ({
            slide_number: Number(el.getAttribute('data-slide-number')),
            layout: el.getAttribute('data-layout') || '',
          }));
        }"""
    )
    nums = [r["slide_number"] for r in rows]
    if sorted(nums) != list(range(1, 54)) or len(set(nums)) != 53:
        raise SystemExit(f"HTML identity failed: {nums!r}")
    return rows


def capture_html(html_dir: Path, layouts: dict[int, str]) -> dict:
    html_dir.mkdir(parents=True, exist_ok=True)
    console: list[dict] = []
    per_slide: dict[int, dict] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=1,
        )
        page = context.new_page()
        page.on(
            "console",
            lambda msg: console.append(
                {"type": msg.type, "text": msg.text, "slide": None}
            )
            if msg.type in {"error", "warning"}
            else None,
        )
        page.on(
            "pageerror",
            lambda exc: console.append({"type": "pageerror", "text": str(exc), "slide": None}),
        )
        page.goto(HTML.resolve().as_uri(), wait_until="load")
        page.add_style_tag(
            content="html::-webkit-scrollbar,body::-webkit-scrollbar{width:0!important;height:0!important}"
        )
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
        html_rows = identity_from_page(page)
        for row in html_rows:
            n = int(row["slide_number"])
            if row["layout"] != layouts[n]:
                raise SystemExit(
                    f"layout mismatch slide {n}: html={row['layout']!r} handoff={layouts[n]!r}"
                )
        for n in range(1, 54):
            layout = layouts[n]
            page.evaluate(
                """(sn) => {
                  const el = document.querySelector(
                    'section.slide[data-slide-number="' + sn + '"]'
                  );
                  el.scrollIntoView({block: 'start', inline: 'nearest'});
                }""",
                n,
            )
            ready = wait_for_paint_ready_charts(page, n, layout)
            ticks = None
            if layout in CHART_LAYOUTS:
                try:
                    ticks = measured_tick_styles(page, n, layout)
                    ticks = {
                        "tick_count": ticks["tick_count"],
                        "min_font_size_px": ticks["min_font_size_px"],
                        "min_font_weight": ticks["min_font_weight"],
                    }
                except ProbeError as exc:
                    ticks = {"error": str(exc)}
            loc = page.locator(f'section.slide[data-slide-number="{n}"]')
            dest = html_dir / f"slide_{n:02d}.png"
            loc.screenshot(path=str(dest), animations="disabled")
            assert_png(dest, (W, H))
            per_slide[n] = {
                "layout_type": layout,
                "chart_count": ready.get("chart_count", 0),
                "charts": ready.get("charts") or [],
                "ticks": ticks,
            }
        browser.close()
    return {"console": console, "slides": per_slide}


def make_sbs(pdf_dir: Path, html_dir: Path, sbs_dir: Path) -> None:
    sbs_dir.mkdir(parents=True, exist_ok=True)
    for n in range(1, 54):
        name = f"slide_{n:02d}.png"
        pdf = Image.open(pdf_dir / name).convert("RGB")
        html = Image.open(html_dir / name).convert("RGB")
        if pdf.size != (W, H) or html.size != (W, H):
            raise SystemExit(f"half size fail {n}: {pdf.size} {html.size}")
        out = Image.new("RGB", (W * 2, H))
        out.paste(pdf, (0, 0))
        out.paste(html, (W, 0))
        dest = sbs_dir / name
        out.save(dest, "PNG")
        assert_png(dest, (W * 2, H))


def contact_sheet(sbs_dir: Path, layouts: dict[int, str], dest: Path) -> None:
    cols, tw, th, label_h = 6, 640, 180, 28
    rows = (53 + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + label_h)), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    for i in range(53):
        n = i + 1
        r, c = divmod(i, cols)
        tile = Image.open(sbs_dir / f"slide_{n:02d}.png").resize(
            (tw, th), Image.Resampling.BILINEAR
        )
        y = r * (th + label_h)
        sheet.paste(tile, (c * tw, y + label_h))
        draw.text(
            (c * tw + 6, y + 6),
            f"p{n:02d}  layout={layouts[n]}  pdf_index={n - 1}",
            fill=(0, 0, 0),
            font=font,
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest, "PNG")


def main() -> None:
    if sha256(PDF) != SHA:
        raise SystemExit("PDF SHA-256 mismatch")
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
    slides = handoff["slides"]
    if len(slides) != 53:
        raise SystemExit(f"handoff slides {len(slides)} != 53")
    layouts = {int(s["slide_number"]): s["layout_type"] for s in slides}
    if sorted(layouts) != list(range(1, 54)):
        raise SystemExit(f"handoff slide numbers {sorted(layouts)}")
    if not HTML.is_file():
        raise SystemExit(f"missing {HTML}")

    pdf_dir, html_dir, sbs_dir = OUT / "pdf", OUT / "html", OUT / "sbs"
    OUT.mkdir(parents=True, exist_ok=True)
    rasterize_pdf(pdf_dir, 53)
    cap = capture_html(html_dir, layouts)
    make_sbs(pdf_dir, html_dir, sbs_dir)
    contact_sheet(sbs_dir, layouts, OUT / "contact_sheet.png")

    rows = []
    for n in range(1, 54):
        name = f"slide_{n:02d}.png"
        info = cap["slides"][n]
        rows.append(
            {
                "slide_number": n,
                "layout_type": layouts[n],
                "pdf_index": n - 1,
                "physical_page": n,
                "pdf_png": str((pdf_dir / name).as_posix()),
                "html_png": str((html_dir / name).as_posix()),
                "sbs_png": str((sbs_dir / name).as_posix()),
                "pdf_size": [W, H],
                "html_size": [W, H],
                "sbs_size": [W * 2, H],
                "chart_count": info["chart_count"],
                "ticks": info["ticks"],
                "classification": None,
            }
        )
    manifest = {
        "source_pdf": str(PDF.as_posix()),
        "source_sha256": SHA,
        "pdf_pages": 53,
        "html_path": str(HTML.as_posix()),
        "viewport": {"width": W, "height": H, "deviceScaleFactor": 1},
        "console": cap["console"],
        "slides": rows,
    }
    (OUT / "comparison_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    missing = [
        p
        for n in range(1, 54)
        for p in (
            pdf_dir / f"slide_{n:02d}.png",
            html_dir / f"slide_{n:02d}.png",
            sbs_dir / f"slide_{n:02d}.png",
        )
        if not p.is_file()
    ]
    if missing:
        raise SystemExit(f"missing artifacts: {missing}")
    print(f"ok 53 pdf/html/sbs under {OUT}")


if __name__ == "__main__":
    main()
