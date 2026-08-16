"""v13 renderer_v3 Amex full-deck comparison + DP-6 design ledger (observation only).

Strict contract:
- identity: 44 unique data-slide-number 1..44 matching corpus layout_type
- paint-ready via scripts/simulation_probe.wait_for_paint_ready_charts
- DP-6: measured_tick_styles + furniture_presence (DESIGN_LEDGER_FURNITURE)
- viewport 1920x1080, deviceScaleFactor 1 (fit scale = 1)
- isolate target section (lesson 32) then element screenshot 1920x1080
- PDF raster via PyMuPDF exactly 1920x1080
- SBS 3840x1080 PDF|HTML; no MAE/similarity/pixel scores
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import traceback
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from simulation_probe import (  # noqa: E402
    DESIGN_LEDGER_FURNITURE,
    ProbeError,
    furniture_presence,
    measured_tick_styles,
    wait_for_paint_ready_charts,
)

SIM = Path(__file__).resolve().parent
PASS = SIM / "passes" / "pass_01"
OUT = PASS / "renderer_v3_out"
HTML = OUT / "presentation.html"
HANDOFF = ROOT / "tests" / "fixtures" / "renderer_v3" / "canonical_amex_handoff_v1.json"
PDF_SRC = Path(r"C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf")

PDF_DIR = SIM / "pdf_pages"
HTML_DIR = SIM / "html_slides"
SBS_DIR = SIM / "side_by_side"
CONTACT = SIM / "contact_sheet.png"
MANIFEST = SIM / "comparison_manifest.json"
CAPTURE_LOG = SIM / "capture_log.json"

W, H = 1920, 1080
SBS_W = W * 2

CHART_LAYOUTS = frozenset(
    {"single_chart", "dual_chart", "chart_hero_dual"}
)


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_layouts() -> dict[int, str]:
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
    layouts: dict[int, str] = {}
    for s in handoff["slides"]:
        n = int(s["slide_number"])
        layouts[n] = str(s["layout_type"])
    if sorted(layouts) != list(range(1, 45)):
        raise SystemExit(f"corpus slide_numbers not 1..44: {sorted(layouts)}")
    return layouts


def rasterize_pdf(layouts: dict[int, str]) -> list[dict]:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF_SRC)
    if doc.page_count != 44:
        raise SystemExit(f"PDF page_count={doc.page_count}, expected 44")
    rows = []
    for i in range(44):
        sn = i + 1
        page = doc[i]
        rect = page.rect
        zoom_x = W / rect.width
        zoom_y = H / rect.height
        mat = fitz.Matrix(zoom_x, zoom_y)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        if pix.width != W or pix.height != H:
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img = img.resize((W, H), Image.Resampling.LANCZOS)
        else:
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        path = PDF_DIR / f"slide_{sn:02d}.png"
        img.save(path, "PNG")
        rows.append(
            {
                "slide_number": sn,
                "layout_type": layouts[sn],
                "pdf_index": i,
                "physical_page": sn,
                "path": str(path.relative_to(SIM)).replace("\\", "/"),
                "width": img.size[0],
                "height": img.size[1],
                "sha256": _sha256(path),
            }
        )
        print(f"pdf {sn:02d} {img.size}", flush=True)
    doc.close()
    return rows


def assert_html_identity(page, layouts: dict[int, str]) -> dict:
    info = page.evaluate(
        """() => {
          const nodes = [...document.querySelectorAll('section.slide')];
          const nums = nodes.map(n => n.getAttribute('data-slide-number'));
          const pairs = nodes.map(n => ({
            slide_number: Number(n.getAttribute('data-slide-number')),
            layout: n.getAttribute('data-layout') || '',
          }));
          return {
            count: nodes.length,
            nums,
            unique: [...new Set(nums)].length,
            pairs,
            stage: !!document.querySelector('.deck-stage'),
          };
        }"""
    )
    if info["count"] != 44 or info["unique"] != 44:
        raise SystemExit(f"HTML identity fail count/unique: {info}")
    nums = sorted(int(x) for x in info["nums"])
    if nums != list(range(1, 45)):
        raise SystemExit(f"HTML slide numbers not 1..44: {nums}")
    mismatches = []
    for p in info["pairs"]:
        sn = int(p["slide_number"])
        exp = layouts[sn]
        got = p["layout"]
        if got != exp:
            mismatches.append({"slide_number": sn, "expected": exp, "got": got})
    if mismatches:
        raise SystemExit(f"layout mismatches: {mismatches}")
    return info


def collect_design_ledger(page, sn: int, layout: str) -> dict:
    """DP-6 design ledger for one slide. ProbeError → ok:false row, not green invent."""
    if layout not in CHART_LAYOUTS:
        return {
            "slide_number": sn,
            "layout": layout,
            "ok": True,
            "ticks": None,
            "furniture": [],
            "tick_count": None,
            "min_font_size_px": None,
            "min_font_weight": None,
            "non_chart": True,
        }

    furniture_rows: list[dict] = []
    tick_info: dict | None = None
    errors: list[str] = []

    try:
        tick_info = measured_tick_styles(page, sn, layout)
    except ProbeError as exc:
        errors.append(f"ticks: {exc}")
        tick_info = None

    for spec in DESIGN_LEDGER_FURNITURE.get(sn, ()):
        sel = spec["selector"]
        exp = spec.get("expected_text")
        try:
            hit = furniture_presence(page, sn, layout, sel, expected_text=exp)
            furniture_rows.append(
                {
                    "selector": sel,
                    "expected_text": exp,
                    "count": hit.get("count", 0),
                    "ok": True,
                }
            )
        except ProbeError as exc:
            errors.append(f"furniture {sel!r}: {exc}")
            furniture_rows.append(
                {
                    "selector": sel,
                    "expected_text": exp,
                    "count": 0,
                    "ok": False,
                    "error": str(exc),
                }
            )

    # Chart slides listed in DESIGN_LEDGER_FURNITURE with zero expected rows still ok on ticks
    ok = tick_info is not None and all(r.get("ok") for r in furniture_rows) and not errors
    # If furniture expected and missing, ok false; if no furniture expected, ticks alone decide
    if sn in DESIGN_LEDGER_FURNITURE and not furniture_rows:
        ok = False
        errors.append("no furniture rows collected for expected slide")

    out: dict = {
        "slide_number": sn,
        "layout": layout,
        "ok": bool(ok),
        "furniture": furniture_rows,
        "errors": errors,
    }
    if tick_info is not None:
        out["tick_count"] = tick_info.get("tick_count")
        out["min_font_size_px"] = tick_info.get("min_font_size_px")
        out["min_font_weight"] = tick_info.get("min_font_weight")
        # keep compact tick sample (not full text dump)
        out["ticks"] = {
            "count": tick_info.get("tick_count"),
            "min_font_size_px": tick_info.get("min_font_size_px"),
            "min_font_weight": tick_info.get("min_font_weight"),
        }
    else:
        out["tick_count"] = 0
        out["min_font_size_px"] = None
        out["min_font_weight"] = None
        out["ticks"] = None
    return out


def isolate_and_screenshot(page, sn: int, out_path: Path) -> dict:
    """Hide siblings + reset stage transform (lesson 32), screenshot section."""
    box = page.evaluate(
        """(sn) => {
          const stage = document.querySelector('.deck-stage');
          if (stage) {
            stage.style.transform = 'none';
            stage.style.width = '1920px';
          }
          const slides = [...document.querySelectorAll('section.slide')];
          let target = null;
          for (const s of slides) {
            const n = Number(s.getAttribute('data-slide-number'));
            if (n === sn) {
              s.style.display = 'block';
              s.style.transform = 'none';
              s.style.marginBottom = '0';
              s.style.width = '1920px';
              s.style.height = '1080px';
              target = s;
            } else {
              s.style.display = 'none';
            }
          }
          if (!target) return null;
          target.scrollIntoView({block: 'start', inline: 'start'});
          const r = target.getBoundingClientRect();
          return {w: r.width, h: r.height, x: r.x, y: r.y};
        }""",
        sn,
    )
    if not box:
        raise ProbeError(f"slide {sn} missing for isolate")
    page.evaluate("() => new Promise((r) => requestAnimationFrame(() => r()))")
    loc = page.locator(f'section.slide[data-slide-number="{sn}"]')
    loc.screenshot(path=str(out_path), type="png")
    img = Image.open(out_path)
    return {
        "box": box,
        "png_size": list(img.size),
    }


def capture_html(layouts: dict[int, str]) -> tuple[list[dict], list[dict], list[dict]]:
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    errors: list[dict] = []
    design_ledgers: list[dict] = []
    console_errors: list[dict] = []

    uri = HTML.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=1,
        )
        page = context.new_page()

        def on_console(msg):
            if msg.type == "error":
                console_errors.append({"type": msg.type, "text": msg.text})

        page.on("console", on_console)
        page.goto(uri, wait_until="networkidle", timeout=120_000)
        page.evaluate(
            """() => {
              const s = document.querySelector('.deck-stage');
              if (s) { s.style.transform = 'none'; s.style.width = '1920px'; }
              document.querySelectorAll('section.slide').forEach(x => {
                x.style.transform = 'none';
                x.style.marginBottom = '0';
              });
            }"""
        )
        identity = assert_html_identity(page, layouts)
        print("identity ok", identity["count"], flush=True)

        for sn in range(1, 45):
            layout = layouts[sn]
            path = HTML_DIR / f"slide_{sn:02d}.png"
            row = {
                "slide_number": sn,
                "layout_type": layout,
                "pdf_index": sn - 1,
                "physical_page": sn,
                "path": str(path.relative_to(SIM)).replace("\\", "/"),
            }
            try:
                paint = wait_for_paint_ready_charts(page, sn, layout, timeout_ms=15000)
                # Design ledger AFTER paint-ready, BEFORE screenshot (ticks live in overlay)
                dled = collect_design_ledger(page, sn, layout)
                design_ledgers.append(dled)
                row["design_ledger"] = dled

                shot = isolate_and_screenshot(page, sn, path)
                img = Image.open(path)
                if img.size != (W, H):
                    img = img.resize((W, H), Image.Resampling.NEAREST)
                    img.save(path, "PNG")
                row.update(
                    {
                        "status": "ok" if dled.get("ok", True) or layout not in CHART_LAYOUTS else "design_ledger_fail",
                        "width": W,
                        "height": H,
                        "sha256": _sha256(path),
                        "chart_count": paint.get("chart_count", 0),
                        "charts": paint.get("charts", []),
                        "box": shot["box"],
                    }
                )
                # Capture still succeeds even if design ledger fails — record both
                if not dled.get("ok", True) and layout in CHART_LAYOUTS:
                    errors.append(
                        {
                            "slide_number": sn,
                            "layout_type": layout,
                            "pdf_index": sn - 1,
                            "physical_page": sn,
                            "error": "design_ledger_not_ok",
                            "design_ledger": dled,
                        }
                    )
                print(
                    f"html {sn:02d} {layout} charts={row['chart_count']} "
                    f"design_ok={dled.get('ok')} ticks={dled.get('tick_count')}",
                    flush=True,
                )
            except Exception as exc:
                err = {
                    "slide_number": sn,
                    "layout_type": layout,
                    "pdf_index": sn - 1,
                    "physical_page": sn,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
                errors.append(err)
                row["status"] = "capture_failure"
                row["error"] = str(exc)
                row["design_ledger"] = {
                    "slide_number": sn,
                    "layout": layout,
                    "ok": False,
                    "ticks": None,
                    "furniture": [],
                    "error": str(exc),
                    "capture_failure": True,
                }
                design_ledgers.append(row["design_ledger"])
                Image.new("RGB", (W, H), (40, 0, 0)).save(path, "PNG")
                row["width"] = W
                row["height"] = H
                row["sha256"] = _sha256(path)
                print(f"html {sn:02d} FAIL {exc}", flush=True)
            rows.append(row)

        browser.close()

    CAPTURE_LOG.write_text(
        json.dumps(
            {
                "console_errors": console_errors,
                "capture_errors": errors,
                "html_uri": uri,
                "design_ledgers": design_ledgers,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return rows, errors, design_ledgers


def make_sbs(pdf_rows: list[dict], html_rows: list[dict], layouts: dict[int, str]) -> list[dict]:
    SBS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    try:
        font_sm = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font_sm = ImageFont.load_default()

    for sn in range(1, 45):
        layout = layouts[sn]
        pdf_p = PDF_DIR / f"slide_{sn:02d}.png"
        html_p = HTML_DIR / f"slide_{sn:02d}.png"
        sbs_p = SBS_DIR / f"slide_{sn:02d}.png"
        left = Image.open(pdf_p).convert("RGB")
        right = Image.open(html_p).convert("RGB")
        if left.size != (W, H):
            left = left.resize((W, H), Image.Resampling.LANCZOS)
        if right.size != (W, H):
            right = right.resize((W, H), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (SBS_W, H), (255, 255, 255))
        canvas.paste(left, (0, 0))
        canvas.paste(right, (W, 0))
        draw = ImageDraw.Draw(canvas)
        label = f"S{sn:02d}  {layout}  PDF p{sn}/idx{sn-1}  |  renderer_v3 HTML"
        draw.rectangle((0, 0, SBS_W, 36), fill=(0, 23, 90))
        draw.text((12, 6), label, fill=(255, 255, 255), font=font_sm)
        draw.text((12, 40), "PDF (source)", fill=(0, 23, 90), font=font_sm)
        draw.text((W + 12, 40), "renderer_v3 HTML", fill=(0, 23, 90), font=font_sm)
        canvas.save(sbs_p, "PNG")
        rows.append(
            {
                "slide_number": sn,
                "layout_type": layout,
                "pdf_index": sn - 1,
                "physical_page": sn,
                "path": str(sbs_p.relative_to(SIM)).replace("\\", "/"),
                "width": SBS_W,
                "height": H,
                "sha256": _sha256(sbs_p),
                "pdf_path": str(pdf_p.relative_to(SIM)).replace("\\", "/"),
                "html_path": str(html_p.relative_to(SIM)).replace("\\", "/"),
            }
        )
        print(f"sbs {sn:02d}", flush=True)
    return rows


def make_contact_sheet(layouts: dict[int, str]) -> dict:
    cols, rows_n = 8, 6
    thumb_w, thumb_h = 480, 135
    sheet = Image.new("RGB", (cols * thumb_w, rows_n * (thumb_h + 24)), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
    for sn in range(1, 45):
        i = sn - 1
        r, c = divmod(i, cols)
        x = c * thumb_w
        y = r * (thumb_h + 24)
        sbs = Image.open(SBS_DIR / f"slide_{sn:02d}.png").convert("RGB")
        sbs.thumbnail((thumb_w - 4, thumb_h - 4), Image.Resampling.LANCZOS)
        ox = x + (thumb_w - sbs.size[0]) // 2
        oy = y + 18 + (thumb_h - 4 - sbs.size[1]) // 2
        sheet.paste(sbs, (ox, oy))
        draw.text(
            (x + 4, y + 2),
            f"S{sn:02d} {layouts[sn]}",
            fill=(0, 23, 90),
            font=font,
        )
    sheet.save(CONTACT, "PNG")
    return {
        "path": str(CONTACT.relative_to(SIM)).replace("\\", "/"),
        "width": sheet.size[0],
        "height": sheet.size[1],
        "sha256": _sha256(CONTACT),
    }


def main() -> int:
    layouts = load_layouts()
    meta = json.loads((OUT / "run_meta.json").read_text(encoding="utf-8"))
    print("run_meta status", meta.get("status"), "version", meta.get("renderer_version"))

    pdf_rows = rasterize_pdf(layouts)
    html_rows, html_errors, design_ledgers = capture_html(layouts)
    sbs_rows = make_sbs(pdf_rows, html_rows, layouts)
    contact = make_contact_sheet(layouts)

    missing = []
    for sn in range(1, 45):
        for d, name in (
            (PDF_DIR, f"slide_{sn:02d}.png"),
            (HTML_DIR, f"slide_{sn:02d}.png"),
            (SBS_DIR, f"slide_{sn:02d}.png"),
        ):
            p = d / name
            if not p.is_file():
                missing.append(str(p))
            else:
                im = Image.open(p)
                exp = (SBS_W, H) if d is SBS_DIR else (W, H)
                if im.size != exp:
                    missing.append(f"{p} size {im.size} != {exp}")

    # Hard require a design_ledger row per slide
    if len(design_ledgers) != 44:
        missing.append(f"design_ledgers count {len(design_ledgers)} != 44")
    for sn in range(1, 45):
        if not any(d.get("slide_number") == sn for d in design_ledgers):
            missing.append(f"missing design_ledger for slide {sn}")

    # Capture failures (true probe/screenshot) vs design-ledger fails
    true_capture_errors = [
        e for e in html_errors if e.get("error") != "design_ledger_not_ok"
    ]
    design_fail_slides = [
        e["slide_number"] for e in html_errors if e.get("error") == "design_ledger_not_ok"
    ]

    manifest = {
        "baseline": "v13",
        "renderer_version": meta.get("renderer_version"),
        "run_meta_status": meta.get("status"),
        "run_meta_ok": meta.get("ok"),
        "strict": (meta.get("options") or {}).get("strict"),
        "repository_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True
        ).strip(),
        "source_pdf": str(PDF_SRC),
        "source_pdf_sha256": _sha256(PDF_SRC),
        "handoff": str(HANDOFF.relative_to(ROOT)).replace("\\", "/"),
        "handoff_sha256": _sha256(HANDOFF),
        "viewport": [W, H],
        "device_scale_factor": 1,
        "slide_count": 44,
        "layouts": {str(k): v for k, v in layouts.items()},
        "pdf_pages": pdf_rows,
        "html_slides": html_rows,
        "side_by_side": sbs_rows,
        "design_ledgers": design_ledgers,
        "design_ledger_fail_slides": design_fail_slides,
        "contact_sheet": contact,
        "capture_errors": true_capture_errors,
        "design_ledger_errors": [
            e for e in html_errors if e.get("error") == "design_ledger_not_ok"
        ],
        "missing_or_bad_size": missing,
        "artifact_hashes": {
            name: _sha256(OUT / name)
            for name in (
                "presentation.html",
                "run_meta.json",
                "evidence_manifest.json",
                "handoff_schema_v1.json",
                "slide_notes.md",
            )
            if (OUT / name).is_file()
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("missing_or_bad_size", missing)
    print("true_capture_errors", len(true_capture_errors))
    print("design_ledger_fail_slides", design_fail_slides)
    print(
        "design_ok_count",
        sum(1 for d in design_ledgers if d.get("ok")),
        "/",
        len(design_ledgers),
    )
    print("manifest", MANIFEST)
    # Exit 0 if artifacts complete even if design ledger has reds (observation records them)
    return 1 if missing or true_capture_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
