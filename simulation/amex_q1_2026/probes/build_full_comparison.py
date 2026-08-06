"""v10 full 44-page PDF↔HTML comparison at 1920×1080.

Uses scripts/simulation_probe.activate_slide (identity contract #137).
No image scores / MAE / similarity.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from simulation_probe import ProbeError, activate_slide  # noqa: E402

PDF_PATH = Path(r"C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf")
SIM = ROOT / "simulation" / "amex_q1_2026"
HTML_PATH = SIM / "passes" / "pass_01" / "output" / "presentation.html"
MAPPING_PATH = SIM / "page_slide_mapping.json"
OUT_PDF = SIM / "comparison" / "pdf"
OUT_HTML = SIM / "comparison" / "html"
OUT_SBS = SIM / "comparison" / "sbs"
MANIFEST = SIM / "comparison_manifest.json"
CONTACT = SIM / "comparison" / "contact_sheet.png"
W, H = 1920, 1080
HEADER_H = 36


def load_rows() -> list[dict]:
    data = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    rows = []
    for r in data["rows"]:
        # Prefer rendered HTML layout for activate_slide contract
        layout = r.get("html_layout") or r["expected_layout"]
        rows.append(
            {
                "slide_number": int(r["slide_number"]),
                "expected_layout": layout,
                "handoff_layout": r["expected_layout"],
                "pdf_page_index": int(r["pdf_page_index"]),
                "pdf_physical_page": int(r["pdf_physical_page"]),
                "title": r.get("title") or "",
            }
        )
    return rows


def rasterize_pdf(rows: list[dict]) -> None:
    OUT_PDF.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF_PATH)
    assert doc.page_count == 44, doc.page_count
    for r in rows:
        page = doc[r["pdf_page_index"]]
        sx = W / page.rect.width
        sy = H / page.rect.height
        mat = fitz.Matrix(sx, sy)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        assert pix.width == W and pix.height == H, (pix.width, pix.height)
        dest = OUT_PDF / (
            f"pdf_p{r['pdf_physical_page']:02d}"
            f"_idx{r['pdf_page_index']:02d}"
            f"_slide{r['slide_number']:02d}.png"
        )
        pix.save(str(dest))
        r["pdf_path"] = str(dest.relative_to(SIM)).replace("\\", "/")
        print("pdf", dest.name, pix.width, pix.height)
    doc.close()


def wait_slide_ready(page, slide_number: int, layout: str, timeout_ms: int = 8000) -> list[str]:
    """Wait for layout/Chart.js readiness after activation; return console-ish notes."""
    notes: list[str] = []
    # Charts: wait until every canvas on the slide has a Chart instance (or no canvas).
    js = """({sn}) => {
      const slide = document.querySelector(
        'section.slide[data-slide-number="' + sn + '"]'
      );
      if (!slide) return {ok: false, reason: 'missing'};
      const canvases = [...slide.querySelectorAll('canvas')];
      if (!canvases.length) return {ok: true, charts: 0};
      let ready = 0;
      for (const c of canvases) {
        let ch = null;
        if (typeof Chart !== 'undefined' && Chart.getChart) ch = Chart.getChart(c);
        ch = ch || c.__chart || c.chart || c.__fakeChart || null;
        if (ch) ready += 1;
      }
      return {ok: ready === canvases.length, charts: canvases.length, ready};
    }"""
    deadline = time.time() + timeout_ms / 1000
    last = None
    while time.time() < deadline:
        last = page.evaluate(js, {"sn": int(slide_number)})
        if last and last.get("ok"):
            return notes
        page.wait_for_timeout(100)
    notes.append(
        f"slide {slide_number} layout={layout} readiness timeout last={last}"
    )
    return notes


def screenshot_html(rows: list[dict]) -> list[str]:
    OUT_HTML.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    url = HTML_PATH.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        console_buf: list[str] = []

        def on_console(msg):
            try:
                console_buf.append(f"{msg.type}: {msg.text}")
            except Exception:
                pass

        page.on("console", on_console)
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(500)

        for r in rows:
            sn = r["slide_number"]
            layout = r["expected_layout"]
            console_buf.clear()
            try:
                activate_slide(page, sn, layout)
            except ProbeError as e:
                raise SystemExit(f"activate_slide failed slide={sn}: {e}") from e
            notes = wait_slide_ready(page, sn, layout)
            dest = OUT_HTML / (
                f"html_slide{sn:02d}"
                f"_layout-{layout}"
                f"_pdfidx{r['pdf_page_index']:02d}.png"
            )
            page.screenshot(path=str(dest), full_page=False)
            r["html_path"] = str(dest.relative_to(SIM)).replace("\\", "/")
            # attach any readiness / console warnings with identity
            slide_warns = [
                w for w in console_buf if w.startswith("warning") or "warn" in w.lower()
            ]
            if notes or slide_warns:
                warnings.append(
                    json.dumps(
                        {
                            "slide_number": sn,
                            "layout": layout,
                            "pdf_page_index": r["pdf_page_index"],
                            "pdf_physical_page": r["pdf_physical_page"],
                            "readiness": notes,
                            "console": slide_warns[:20],
                        }
                    )
                )
            print("html", dest.name)
        browser.close()
    return warnings


def make_sbs(rows: list[dict]) -> None:
    OUT_SBS.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
        font_sm = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
        font_sm = font

    for r in rows:
        pdf = Image.open(SIM / r["pdf_path"]).convert("RGB")
        html = Image.open(SIM / r["html_path"]).convert("RGB")
        assert pdf.size == (W, H), pdf.size
        assert html.size == (W, H), html.size
        gap = 8
        canvas = Image.new("RGB", (W * 2 + gap, H + HEADER_H), (32, 36, 48))
        d = ImageDraw.Draw(canvas)
        header = (
            f"PDF physical P{r['pdf_physical_page']} (index {r['pdf_page_index']}) "
            f"| HTML slide {r['slide_number']} | layout {r['expected_layout']}"
        )
        d.text((8, 8), header, fill=(240, 240, 240), font=font)
        d.text((8, 22), (r.get("title") or "")[:90], fill=(180, 190, 210), font=font_sm)
        canvas.paste(pdf, (0, HEADER_H))
        canvas.paste(html, (W + gap, HEADER_H))
        dest = OUT_SBS / (
            f"sbs_slide{r['slide_number']:02d}"
            f"_P{r['pdf_physical_page']:02d}"
            f"_idx{r['pdf_page_index']:02d}"
            f"_{r['expected_layout']}.png"
        )
        canvas.save(dest, optimize=True)
        r["sbs_path"] = str(dest.relative_to(SIM)).replace("\\", "/")
        print("sbs", dest.name)


def contact_sheet(rows: list[dict], cols: int = 4) -> None:
    thumbs = []
    tw, th = 480, 140  # half-width thumbnail of sbs header+strip
    for r in rows:
        im = Image.open(SIM / r["sbs_path"]).convert("RGB")
        # scale full sbs to thumb width
        scale = tw / im.width
        im = im.resize((tw, max(1, int(im.height * scale))), Image.Resampling.LANCZOS)
        # crop top strip for contact density
        im = im.crop((0, 0, tw, min(th, im.height)))
        if im.height < th:
            pad = Image.new("RGB", (tw, th), (20, 20, 20))
            pad.paste(im, (0, 0))
            im = pad
        thumbs.append(im)
    rows_n = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw + 8, rows_n * th + 8), (15, 15, 18))
    for i, im in enumerate(thumbs):
        x = (i % cols) * tw + 4
        y = (i // cols) * th + 4
        sheet.paste(im, (x, y))
    CONTACT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT, optimize=True)
    print("contact", CONTACT)


def write_manifest(rows: list[dict], warnings: list[str]) -> None:
    out_rows = []
    for r in rows:
        pdf_ok = (SIM / r["pdf_path"]).is_file()
        html_ok = (SIM / r["html_path"]).is_file()
        sbs_ok = (SIM / r["sbs_path"]).is_file()
        out_rows.append(
            {
                "slide_number": r["slide_number"],
                "expected_layout": r["expected_layout"],
                "handoff_layout": r["handoff_layout"],
                "pdf_page_index": r["pdf_page_index"],
                "pdf_physical_page": r["pdf_physical_page"],
                "title": r.get("title") or "",
                "pdf_path": r["pdf_path"],
                "html_path": r["html_path"],
                "sbs_path": r["sbs_path"],
                "artifacts_exist": bool(pdf_ok and html_ok and sbs_ok),
            }
        )
    payload = {
        "viewport": {"width": W, "height": H},
        "source_pdf": str(PDF_PATH),
        "html": str(HTML_PATH.relative_to(ROOT)).replace("\\", "/"),
        "n_slides": len(out_rows),
        "all_artifacts_present": all(x["artifacts_exist"] for x in out_rows),
        "contact_sheet": str(CONTACT.relative_to(SIM)).replace("\\", "/"),
        "warnings": warnings,
        "rows": out_rows,
    }
    MANIFEST.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("manifest", MANIFEST, "all_ok", payload["all_artifacts_present"])


def main() -> int:
    if not HTML_PATH.is_file():
        print("missing html", HTML_PATH, file=sys.stderr)
        return 2
    if not MAPPING_PATH.is_file():
        print("missing mapping", MAPPING_PATH, file=sys.stderr)
        return 2
    rows = load_rows()
    assert len(rows) == 44, len(rows)
    rasterize_pdf(rows)
    warnings = screenshot_html(rows)
    make_sbs(rows)
    contact_sheet(rows)
    write_manifest(rows, warnings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
