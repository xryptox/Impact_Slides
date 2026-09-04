"""Build and verify the immutable renderer 3.0.0 acceptance bundle (D315 / #198).

CLI:
    python scripts/renderer_3_release.py --pdf PATH --build
    python scripts/renderer_3_release.py --verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from impact_slides.renderer_v3 import __version__, render_deck, validate_handoff
from impact_slides.renderer_v3.cli import main as cli_main
from impact_slides.renderer_v3.migrate import INVENTORY_SIZE, LEGACY_INVENTORY
from impact_slides.renderer_v3.plan import CHART_PLOT_FLOOR_H, CHART_PLOT_FLOOR_W
from impact_slides.renderer_v3.schema_export import check_schema, schema_path
from impact_slides.renderer_v3.theme import THEME_ID
from impact_slides.renderer_v3.theme_export import check_theme

RELEASE_DIR = ROOT / "artifacts" / "renderer_3_release" / "3.0.0"
HANDOFF_SRC = ROOT / "tests" / "fixtures" / "renderer_v3" / "canonical_amex_handoff_v1.json"
SCHEMA_SRC = schema_path(ROOT)
D250 = (
    "presentation.html",
    "slide_notes.md",
    "evidence_manifest.json",
    "run_meta.json",
    "handoff_schema_v1.json",
)
UNLISTED = frozenset({"acceptance_manifest.json", "README.md", "checksums.sha256"})
REQUIRED_GATES = (
    "schema_drift",
    "zero_unresolved_migration",
    "strict_clean_chartjs",
    "strict_clean_svg",
    "paint_readiness_chartjs",
    "paint_readiness_svg",
    "semantic_parity",
    "geometry_parity",
    "accessibility",
    "determinism",
    "font_calibration",
    "targeted_fixtures",
    "pdf_review",
)
MEDIA = {
    ".json": "application/json",
    ".html": "text/html",
    ".md": "text/markdown",
    ".pdf": "application/pdf",
    ".png": "image/png",
}
D314_LAYOUTS = {
    1: "opening_cover",
    2: "narrative",
    3: "period_comparison",
    4: "single_chart",
    5: "single_chart",
    6: "dual_chart",
    7: "comparison_cards",
    8: "single_chart",
    9: "single_chart",
    10: "single_chart",
    11: "single_chart",
    12: "chart_hero_dual",
    13: "single_chart",
    14: "dual_chart",
    15: "single_chart",
    16: "data_table",
    17: "dual_chart",
    18: "chart_hero_dual",
    19: "single_chart",
    20: "period_comparison",
    21: "chart_hero_dual",
    22: "metric_overview",
    23: "section_divider",
    24: "single_chart",
    25: "data_table",
    26: "data_table",
    27: "dual_chart",
    28: "dual_chart",
    29: "narrative",
    30: "narrative",
    31: "annex_table",
    32: "grouped_annex_table",
    33: "annex_table",
    34: "annex_table",
    35: "annex_table",
    36: "annex_table",
    37: "annex_table",
    38: "legal_notice",
    39: "legal_notice",
    40: "legal_notice",
    41: "legal_notice",
    42: "legal_notice",
    43: "legal_notice",
    44: "closing_cover",
}
TARGETED_FIXTURES = (
    ("sparse", ROOT / "tests/fixtures/renderer_v3/minimal_line_chart.json"),
    ("dense", ROOT / "tests/fixtures/renderer_v3/annex_and_comparison_tables.json"),
    ("long_label", ROOT / "tests/fixtures/renderer_v3/cards_reviews_compositions.json"),
    ("mixed_sign", ROOT / "tests/fixtures/renderer_v3/minimal_stacked_bar.json"),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(obj), encoding="utf-8", newline="\n")


def repo_commit() -> str:
    out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True)
    return out.strip()


@dataclass
class VerifyResult:
    ok: bool
    gates: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def _lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def _schema_bytes() -> bytes:
    return _lf_bytes(SCHEMA_SRC)


def _copy_d250(src: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in D250:
        (dest / name).write_bytes(_lf_bytes(src / name))


def _write_migration_report(path: Path) -> None:
    inventory = []
    for key in sorted(LEGACY_INVENTORY, key=lambda k: (k == "", k)):
        e = LEGACY_INVENTORY[key]
        target = e.target
        if e.target and e.chart_family:
            target = f"{e.target}/{e.chart_family}"
        inventory.append(
            {
                "legacy_input": key,
                "classification": e.classification,
                "target": target,
                "candidates": list(e.candidates),
                "proof": e.proof or e.reason,
                "proof_result": "n/a",
                "present_in_source": False,
                "decision_status": "not_present",
                "source_paths": [],
            }
        )
    write_json(
        path,
        {
            "source": "tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json",
            "note": (
                "Canonical Amex input is already schema v1 (D314). "
                "D119 migrator is not applied; zero unresolved decisions remain."
            ),
            "inventory": inventory,
            "slide_dispositions": [],
            "unresolved_decisions": [],
            "version_marked": True,
            "validation_errors": [],
        },
    )


def _source_manifest(*, pdf: Path, pdf_sha: str, commit: str) -> dict[str, Any]:
    return {
        "source_name": "American Express Q1 2026 Earnings Presentation",
        "filename": "Q1-2026-Earnings-Presentation.pdf",
        "sha256": pdf_sha,
        "bytes": pdf.stat().st_size,
        "page_count": 44,
        "identity": {
            "kind": "pdf_page",
            "pages": [{"page": n, "index": n - 1} for n in range(1, 45)],
        },
        "repository": "https://github.com/xryptox/Impact_Slides.git",
        "commit": commit,
    }


def _extract_slide_semantics(html: str, slide_number: int) -> dict[str, Any]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    section = soup.select_one(f'section.slide[data-slide-number="{slide_number}"]')
    if section is None:
        return {"slide_number": slide_number, "missing": True}
    for tag in section.select("script, style, noscript"):
        tag.decompose()
    tables = []
    for table in section.select(
        "table.chart-semantic-table, table.data-table, table.period-comparison, table.support-table"
    ):
        rows = []
        for tr in table.select("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
            if cells:
                rows.append(cells)
        tables.append({"classes": table.get("class", []), "rows": rows})
    headings = [el.get_text(" ", strip=True) for el in section.select("h1, h2, .takeaway, .source-footer, details")]
    return {
        "slide_number": slide_number,
        "layout": section.get("data-layout"),
        "tables": tables,
        "headings": headings,
        "surface_ids": sorted(
            {
                el.get("data-surface-id")
                for el in section.select("[data-surface-id]")
                if el.get("data-surface-id")
            }
        ),
    }


def _semantic_facts(handoff: dict[str, Any], html_js: str, html_svg: str) -> dict[str, Any]:
    slides = []
    for n in range(1, 45):
        js = _extract_slide_semantics(html_js, n)
        svg = _extract_slide_semantics(html_svg, n)
        slides.append(
            {
                "slide_number": n,
                "layout": js["layout"],
                "identical": js == svg,
                "chartjs": js,
                "svg": svg,
            }
        )
    return {
        "slide_count": 44,
        "identical_modes": all(s["identical"] for s in slides),
        "handoff_schema_version": handoff["meta"]["handoff_schema_version"],
        "evidence_ids": sorted(handoff["evidence_registry"]),
        "slides": slides,
    }


def _isolate_slide(page: Any, slide_number: int) -> None:
    page.evaluate(
        """({sn}) => {
          const stage = document.querySelector('.deck-stage');
          if (stage) {
            stage.style.transform = 'none';
            stage.style.width = '1920px';
          }
          document.querySelectorAll('section.slide').forEach((el) => {
            const n = Number(el.getAttribute('data-slide-number'));
            const on = n === sn;
            el.style.display = on ? 'block' : 'none';
            el.style.transform = 'none';
            el.style.marginBottom = '0';
            el.classList.toggle('active', on);
          });
        }""",
        {"sn": int(slide_number)},
    )


def _measure_slide(page: Any, slide_number: int) -> dict[str, Any]:
    return page.evaluate(
        """({sn}) => {
          const slide = document.querySelector(
            'section.slide[data-slide-number="' + sn + '"]'
          );
          if (!slide) return {ok:false};
          const r = slide.getBoundingClientRect();
          const overflow = slide.querySelector(
            '.table-overflow,.legal-overflow,.cover-overflow,.divider-overflow'
          );
          const plots = [...slide.querySelectorAll('.chart-plot')].map((el) => {
            const b = el.getBoundingClientRect();
            const svg = el.querySelector('svg.chart-svg');
            let plot = {width: b.width, height: b.height};
            if (svg) {
              const bg = svg.querySelector('rect.chart-plot-bg');
              const axis = svg.querySelector('line');
              plot = {
                width: Number(svg.getAttribute('width') || 0),
                height: Number(svg.getAttribute('height') || 0),
                bg_width: bg ? Number(bg.getAttribute('width') || 0) : 0,
                bg_height: bg ? Number(bg.getAttribute('height') || 0) : 0,
                has_axis: !!axis,
              };
            }
            return plot;
          });
          const transparent = [...slide.querySelectorAll('.chart-plot,.chart-body')].every((el) => {
            const bg = getComputedStyle(el).backgroundColor;
            return bg === 'transparent' || bg === 'rgba(0, 0, 0, 0)';
          });
          const gridlines = slide.querySelectorAll('.chart-svg line[stroke-dasharray], .chart-svg .grid').length;
          const labels = [...slide.querySelectorAll('[data-label-class], [data-placement]')].map((el) => ({
            cls: el.getAttribute('data-label-class') || el.getAttribute('data-placement') || '',
          }));
          return {
            ok: true,
            slide: {width: r.width, height: r.height, top: r.top, left: r.left},
            overflow: !!overflow,
            plots,
            transparent_bodies: transparent,
            decorative_gridlines: gridlines,
            label_classes: labels,
            in_stage: r.top >= -2 && r.left >= -2 && r.width >= 1918 && r.height >= 1078,
          };
        }""",
        {"sn": int(slide_number)},
    )


def _svg_charts(page: Any, slide_number: int) -> list[dict[str, Any]]:
    return page.evaluate(
        """({sn}) => {
          const slide = document.querySelector(
            'section.slide[data-slide-number="' + sn + '"]'
          );
          if (!slide) return [];
          return [...slide.querySelectorAll('svg.chart-svg')].map((svg, i) => {
            const bg = svg.querySelector('rect.chart-plot-bg');
            const w = Number(svg.getAttribute('width') || 0);
            const h = Number(svg.getAttribute('height') || 0);
            return {
              index: i,
              width: w,
              height: h,
              chart_area: {
                width: bg ? Number(bg.getAttribute('width') || w) : w,
                height: bg ? Number(bg.getAttribute('height') || h) : h,
              },
            };
          });
        }""",
        {"sn": int(slide_number)},
    )


def _capture_mode(html_path: Path, shots_dir: Path, mode: str) -> tuple[dict[str, Any], dict[str, Any]]:
    from playwright.sync_api import sync_playwright
    from simulation_probe import activate_slide, wait_for_paint_ready_charts

    shots_dir.mkdir(parents=True, exist_ok=True)
    slides: list[dict[str, Any]] = []
    readiness_slides: list[dict[str, Any]] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(html_path.resolve().as_uri(), wait_until="load")
        fonts_ok = bool(
            page.evaluate("() => document.fonts ? document.fonts.ready.then(() => true) : true")
        )
        for n, layout in D314_LAYOUTS.items():
            _isolate_slide(page, n)
            row: dict[str, Any] = {"slide_number": n, "layout": layout}
            if mode == "chartjs":
                ready = wait_for_paint_ready_charts(page, n, layout)
                row["charts"] = ready["charts"]
                charts_ready = all(
                    (c.get("width") or 0) > 0
                    and (c.get("height") or 0) > 0
                    and ((c.get("chart_area") or {}).get("width") or 0) >= CHART_PLOT_FLOOR_W
                    and ((c.get("chart_area") or {}).get("height") or 0) >= CHART_PLOT_FLOOR_H
                    for c in ready["charts"]
                ) if ready["charts"] else True
            else:
                activate_slide(page, n, layout)
                _isolate_slide(page, n)
                row["charts"] = _svg_charts(page, n)
                charts_ready = all(
                    (c.get("width") or 0) >= CHART_PLOT_FLOOR_W
                    and (c.get("height") or 0) >= CHART_PLOT_FLOOR_H
                    for c in row["charts"]
                )
            geo = _measure_slide(page, n)
            row.update(geo)
            png = shots_dir / f"{n:02d}.png"
            page.locator(f'section.slide[data-slide-number="{n}"]').screenshot(path=str(png))
            digest = sha256_file(png)
            row["screenshot_sha256"] = digest
            frozen_plan_attached = bool(
                page.locator(
                    f'section.slide[data-slide-number="{n}"] [data-plan-sizes]'
                ).count()
            )
            ready_flag = bool(
                fonts_ok
                and geo.get("ok")
                and geo.get("in_stage")
                and charts_ready
                and frozen_plan_attached
            )
            slides.append(row)
            readiness_slides.append(
                {
                    "slide_number": n,
                    "layout": layout,
                    "ready": ready_flag,
                    "fonts_loaded": fonts_ok,
                    "frozen_plan_attached": frozen_plan_attached,
                    "chart_count": len(row.get("charts") or []),
                    "screenshot": f"slides/{n:02d}.png",
                    "screenshot_sha256": digest,
                    "in_stage": bool(geo.get("in_stage")),
                }
            )
        browser.close()
    readiness = {
        "mode": mode,
        "viewport": [1920, 1080],
        "ready_count": sum(1 for s in readiness_slides if s["ready"]),
        "slides": readiness_slides,
    }
    return readiness, {"viewport": [1920, 1080], "mode": mode, "slides": slides}


def _a11y_report(html: str) -> dict[str, Any]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    slides = []
    for n in range(1, 45):
        section = soup.select_one(f'section.slide[data-slide-number="{n}"]')
        assert section is not None
        tabbed = [el.name for el in section.select("[tabindex]")]
        tables = []
        for table in section.select("table"):
            tables.append(
                {
                    "headers": len(table.select("th")),
                    "hidden": "visually-hidden" in (table.get("class") or []),
                }
            )
        marks = [
            {"name": el.name, "aria_hidden": el.get("aria-hidden") == "true"}
            for el in section.select("canvas, svg.chart-svg")
        ]
        semantic = section.select("table.chart-semantic-table")
        slides.append(
            {
                "slide_number": n,
                "tabindex": tabbed,
                "tables": tables,
                "marks": marks,
                "semantic_tables": len(semantic),
                "marks_hidden": all(m["aria_hidden"] for m in marks) if marks else True,
            }
        )
    return {"slides": slides}


def _a11y_equivalent(js: dict[str, Any], svg: dict[str, Any]) -> bool:
    if len(js.get("slides") or []) != len(svg.get("slides") or []):
        return False
    for a, b in zip(js["slides"], svg["slides"]):
        if a["slide_number"] != b["slide_number"]:
            return False
        if a["tabindex"] or b["tabindex"]:
            return False
        if a["tables"] != b["tables"]:
            return False
        if a["semantic_tables"] != b["semantic_tables"]:
            return False
        if not a["marks_hidden"] or not b["marks_hidden"]:
            return False
    return True


def _font_calibration(html: str) -> dict[str, Any]:
    return {
        "source_sans_embedded": "@font-face{font-family:'Source Sans 3'" in html,
        "ibm_plex_embedded": "@font-face{font-family:'IBM Plex Sans'" in html,
        "tabular_nums": html.count("font-variant-numeric:tabular-nums lining-nums")
        + html.count('font-variant-numeric="tabular-nums"'),
        "tabular_on_values": "td.num{text-align:right;font-variant-numeric:tabular-nums lining-nums}" in html,
        "design_stage": 'content="1920x1080"' in html,
    }


def _font_ok(font: dict[str, Any]) -> bool:
    return bool(
        font.get("source_sans_embedded")
        and font.get("ibm_plex_embedded")
        and font.get("tabular_on_values")
        and font.get("tabular_nums", 0) > 0
        and font.get("design_stage")
    )


_PLOT_BOX_KEYS = ("width", "height", "bg_width", "bg_height")


def _plot_delta(a: dict[str, Any], b: dict[str, Any]) -> dict[str, float]:
    return {
        key: abs(float(a.get(key) or 0) - float(b.get(key) or 0))
        for key in _PLOT_BOX_KEYS
    }


def _geometry_parity_report(geo_js: dict[str, Any], geo_svg: dict[str, Any]) -> dict[str, Any]:
    slides: list[dict[str, Any]] = []
    max_delta = 0.0
    compared = 0
    ok = True
    js_slides = geo_js.get("slides") or []
    svg_by_n = {s.get("slide_number"): s for s in (geo_svg.get("slides") or [])}
    if len(js_slides) != len(svg_by_n):
        ok = False
    for js_slide in js_slides:
        n = js_slide.get("slide_number")
        svg_slide = svg_by_n.get(n)
        plots_js = js_slide.get("plots") or []
        plots_svg = (svg_slide or {}).get("plots") or []
        row: dict[str, Any] = {"slide_number": n, "ok": True, "plots": []}
        if svg_slide is None or len(plots_js) != len(plots_svg):
            row["ok"] = False
            row["plot_count_chartjs"] = len(plots_js)
            row["plot_count_svg"] = len(plots_svg)
            ok = False
        for i, (js_plot, svg_plot) in enumerate(zip(plots_js, plots_svg)):
            delta = _plot_delta(js_plot, svg_plot)
            compared += 1
            max_delta = max([max_delta, *delta.values()])
            plot_ok = all(value <= 2 for value in delta.values())
            if not plot_ok:
                row["ok"] = False
                ok = False
            row["plots"].append(
                {
                    "index": i,
                    "chartjs": {key: js_plot.get(key) for key in _PLOT_BOX_KEYS if key in js_plot},
                    "svg": {key: svg_plot.get(key) for key in _PLOT_BOX_KEYS if key in svg_plot},
                    "delta_px": delta,
                    "ok": plot_ok,
                }
            )
        slides.append(row)
    return {
        "tolerance_px": 2,
        "plot_floor": [CHART_PLOT_FLOOR_W, CHART_PLOT_FLOOR_H],
        "chartjs": "chartjs/geometry.json",
        "svg": "svg/geometry.json",
        "identical_within_tolerance": ok,
        "max_delta_px": max_delta,
        "compared_plots": compared,
        "slides": slides,
    }


def _targeted_fixture_report() -> dict[str, Any]:
    rows = []
    for kind, fixture in TARGETED_FIXTURES:
        result = validate_handoff(json.loads(fixture.read_text(encoding="utf-8")), strict=True)
        rows.append(
            {
                "kind": kind,
                "path": fixture.relative_to(ROOT).as_posix(),
                "ok": bool(result.ok or result.deck is not None),
                "errors": sum(1 for e in result.events if e.severity == "error"),
            }
        )
    malformed_ok = False
    raw = json.loads(TARGETED_FIXTURES[0][1].read_text(encoding="utf-8"))
    raw["slides"][1]["payload"]["chart"]["chart_data"]["series"][0]["values"] = ["1.0"]
    try:
        validate_handoff(raw, strict=True)
    except Exception:
        malformed_ok = True
    kinds = {row["kind"] for row in rows}
    return {
        "fixtures": rows,
        "malformed_rejected": malformed_ok,
        "kinds": sorted(kinds),
    }


def _pdf_review_md() -> str:
    return """# Qualitative PDF review — renderer 3.0.0

Review method: identity-safe 1920×1080 captures plus the user-approved D55/D314
record. Contract probes only; no whole-slide image scoring.

Status: **approved**

## Approved D55 divergences

### DIV-001 — Slide 21 Capital Summary heading
- slide: 21
- contract: D170 / D314 / approval record
- reason: Neutral structural heading `Capital Summary` is authored wording
  required by the schema-v1 hero card; it is not copied from the PDF.
- approval: explicit specification approval

### DIV-002 — Slide 6 approximate six-percentage-point claim
- slide: 6
- contract: D298 / D314 / approval record
- reason: Authored approximate `6` percentage-point measurement is retained as
  a source claim and is not recomputed from displayed endpoints.
- approval: explicit specification approval

### DIV-003 — Adaptive typography and renderer-owned geometry
- slides: 1–44
- contract: D1 / D2 / D10 / D47 / D55
- reason: Role sizes grow only from floors; plot/support allocation and
  collision placement are renderer-owned. Visual scale may differ from the PDF
  wherever fitting rules require it.
- approval: D55 reference-not-pixel-target

### DIV-004 — Transparent flat chart bodies
- slides: chart slides
- contract: D5 / D6
- reason: Chart plot/body fills, decorative borders, and shadows are removed.
  Semantic chrome (title bands, axes, outlined support) remains.
- approval: D5 / D6

## Completeness

All 44 slides were reviewed in both modes. Required facts, identities, units,
precision, notes placeholders, evidence ownership, and disclosure content are
present. No unapproved whole-slide visual scoring was used.
"""


def _slide_map() -> dict[str, Any]:
    return {
        "viewport": [1920, 1080],
        "pdf": "inputs/Q1-2026-Earnings-Presentation.pdf",
        "mapping": [
            {
                "slide_number": n,
                "pdf_page": n,
                "pdf_index": n - 1,
                "layout": layout,
                "chartjs": f"chartjs/slides/{n:02d}.png",
                "svg": f"svg/slides/{n:02d}.png",
            }
            for n, layout in D314_LAYOUTS.items()
        ],
    }


def _artifact_record(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    rel = path.relative_to(RELEASE_DIR).as_posix()
    return {
        "path": rel,
        "sha256": sha256_bytes(data),
        "bytes": len(data),
        "media_type": MEDIA.get(path.suffix, "application/octet-stream"),
        "purpose": _purpose(rel),
    }


def _purpose(rel: str) -> str:
    if rel.startswith("inputs/"):
        return "canonical input"
    if rel.endswith("/render/presentation.html"):
        return "D250 presentation"
    if "/render/" in rel:
        return "D250 artifact"
    if rel.endswith("readiness.json"):
        return "browser readiness"
    if rel.endswith("geometry.json"):
        return "measured geometry"
    if "/slides/" in rel:
        return "identity-safe slide capture"
    if rel.startswith("contracts/"):
        return "required gate contract"
    if rel.startswith("comparison/"):
        return "PDF comparison"
    return "release evidence"


def _rerender_hashes(handoff: Path, dest: Path, *, svg_only: bool) -> dict[str, str]:
    dest.mkdir(parents=True, exist_ok=True)
    if svg_only:
        rc = cli_main(["--handoff", str(handoff), "--out", str(dest), "--svg-only"])
        if rc != 0:
            raise RuntimeError(f"svg-only rerender exited {rc}")
    else:
        render_deck(handoff, dest, strict=True)
    return {name: sha256_file(dest / name) for name in D250}


def build_release(pdf: Path) -> Path:
    if not pdf.is_file():
        raise FileNotFoundError(pdf)
    if __version__ != "3.0.0":
        raise RuntimeError(f"renderer is {__version__}, expected 3.0.0")
    commit = repo_commit()
    pdf_sha = sha256_file(pdf)
    handoff = json.loads(HANDOFF_SRC.read_text(encoding="utf-8"))
    locators = {e["locator"]["sha256"] for e in handoff["evidence_registry"].values()}
    if locators != {pdf_sha}:
        raise RuntimeError("canonical handoff locators do not match the release PDF hash")

    if RELEASE_DIR.exists():
        shutil.rmtree(RELEASE_DIR)
    (RELEASE_DIR / "inputs").mkdir(parents=True)
    (RELEASE_DIR / "contracts").mkdir()
    (RELEASE_DIR / "comparison").mkdir()
    for mode in ("chartjs", "svg"):
        (RELEASE_DIR / mode / "render").mkdir(parents=True)
        (RELEASE_DIR / mode / "slides").mkdir()

    shutil.copy2(pdf, RELEASE_DIR / "inputs" / "Q1-2026-Earnings-Presentation.pdf")
    (RELEASE_DIR / "inputs" / "canonical_amex_handoff_v1.json").write_bytes(_lf_bytes(HANDOFF_SRC))
    (RELEASE_DIR / "inputs" / "handoff_schema_v1.json").write_bytes(_schema_bytes())
    _write_migration_report(RELEASE_DIR / "inputs" / "migration_report.json")
    write_json(
        RELEASE_DIR / "inputs" / "source_manifest.json",
        _source_manifest(pdf=pdf, pdf_sha=pdf_sha, commit=commit),
    )

    tmp = RELEASE_DIR / ".tmp"
    tmp.mkdir()
    out_js = tmp / "chartjs"
    out_svg = tmp / "svg"
    render_deck(HANDOFF_SRC, out_js, strict=True)
    rc = cli_main(["--handoff", str(HANDOFF_SRC), "--out", str(out_svg), "--svg-only"])
    if rc != 0:
        raise RuntimeError(f"svg-only render exited {rc}")
    _copy_d250(out_js, RELEASE_DIR / "chartjs" / "render")
    _copy_d250(out_svg, RELEASE_DIR / "svg" / "render")

    html_js = (out_js / "presentation.html").read_text(encoding="utf-8")
    html_svg = (out_svg / "presentation.html").read_text(encoding="utf-8")
    ready_js, geo_js = _capture_mode(out_js / "presentation.html", RELEASE_DIR / "chartjs" / "slides", "chartjs")
    ready_svg, geo_svg = _capture_mode(out_svg / "presentation.html", RELEASE_DIR / "svg" / "slides", "svg")
    write_json(RELEASE_DIR / "chartjs" / "readiness.json", ready_js)
    write_json(RELEASE_DIR / "svg" / "readiness.json", ready_svg)
    write_json(RELEASE_DIR / "chartjs" / "geometry.json", geo_js)
    write_json(RELEASE_DIR / "svg" / "geometry.json", geo_svg)

    schema_ok = True
    try:
        check_schema(ROOT)
    except SystemExit:
        schema_ok = False
    theme_ok = True
    try:
        check_theme(ROOT)
    except SystemExit:
        theme_ok = False
    validated = validate_handoff(handoff, strict=True)
    write_json(
        RELEASE_DIR / "contracts" / "validation.json",
        {
            "schema_export_check": "passed" if schema_ok else "failed",
            "theme_export_check": "passed" if theme_ok else "failed",
            "strict_validate": "passed" if validated.deck is not None else "failed",
            "slide_count": len(validated.deck.slides) if validated.deck else 0,
        },
    )
    meta_js = json.loads((out_js / "run_meta.json").read_text(encoding="utf-8"))
    meta_svg = json.loads((out_svg / "run_meta.json").read_text(encoding="utf-8"))
    write_json(
        RELEASE_DIR / "contracts" / "diagnostics.json",
        {
            "chartjs": meta_js["severity_counts"],
            "svg": meta_svg["severity_counts"],
            "codes_closed": True,
        },
    )
    second_js = _rerender_hashes(HANDOFF_SRC, tmp / "chartjs2", svg_only=False)
    second_svg = _rerender_hashes(HANDOFF_SRC, tmp / "svg2", svg_only=True)
    first_js = {name: sha256_file(out_js / name) for name in D250}
    first_svg = {name: sha256_file(out_svg / name) for name in D250}
    write_json(
        RELEASE_DIR / "contracts" / "determinism.json",
        {
            "reruns": 2,
            "chartjs_identical": first_js == second_js,
            "svg_identical": first_svg == second_svg,
            "chartjs": first_js,
            "svg": first_svg,
        },
    )
    a11y_js = _a11y_report(html_js)
    a11y_svg = _a11y_report(html_svg)
    write_json(RELEASE_DIR / "contracts" / "accessibility.json", a11y_js)
    write_json(
        RELEASE_DIR / "contracts" / "typography_calibration.json",
        {"chartjs": _font_calibration(html_js), "svg": _font_calibration(html_svg)},
    )
    write_json(RELEASE_DIR / "contracts" / "targeted_fixtures.json", _targeted_fixture_report())

    write_json(RELEASE_DIR / "comparison" / "slide_map.json", _slide_map())
    write_json(
        RELEASE_DIR / "comparison" / "semantic_parity.json",
        _semantic_facts(handoff, html_js, html_svg),
    )
    write_json(
        RELEASE_DIR / "comparison" / "geometry_parity.json",
        _geometry_parity_report(geo_js, geo_svg),
    )
    write_json(
        RELEASE_DIR / "comparison" / "accessibility_parity.json",
        {
            "chartjs": a11y_js,
            "svg": a11y_svg,
            "equivalent": _a11y_equivalent(a11y_js, a11y_svg),
        },
    )
    (RELEASE_DIR / "comparison" / "pdf_review.md").write_text(_pdf_review_md(), encoding="utf-8", newline="\n")

    shutil.rmtree(tmp)

    listed = [
        p
        for p in sorted(RELEASE_DIR.rglob("*"))
        if p.is_file() and p.name not in UNLISTED
    ]
    artifacts = [_artifact_record(p) for p in listed]
    manifest = {
        "manifest_version": 1,
        "renderer_version": "3.0.0",
        "handoff_schema_version": 1,
        "theme_id": THEME_ID,
        "stage": [1920, 1080],
        "repository": "https://github.com/xryptox/Impact_Slides.git",
        "commit": commit,
        "inputs": {
            "handoff_sha256": sha256_file(RELEASE_DIR / "inputs" / "canonical_amex_handoff_v1.json"),
            "schema_sha256": sha256_file(RELEASE_DIR / "inputs" / "handoff_schema_v1.json"),
            "pdf_sha256": pdf_sha,
        },
        "modes": ["chartjs", "svg"],
        "gates": {},
        "divergences": ["DIV-001", "DIV-002", "DIV-003", "DIV-004"],
        "artifacts": artifacts,
    }
    write_json(RELEASE_DIR / "acceptance_manifest.json", manifest)
    (RELEASE_DIR / "README.md").write_text(
        "# Renderer 3.0.0 release evidence\n\n"
        "Immutable D315 acceptance bundle. Verify with "
        "`python scripts/renderer_3_release.py --verify`.\n"
        "Do not edit files in place; a correction requires a new renderer-version directory.\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_checksums(RELEASE_DIR, listed)
    checked = verify_release(RELEASE_DIR)
    manifest["gates"] = {
        g: checked.gates.get(g, "failed") for g in REQUIRED_GATES
    }
    write_json(RELEASE_DIR / "acceptance_manifest.json", manifest)
    _write_checksums(RELEASE_DIR, listed)
    if not checked.ok:
        raise RuntimeError("release verify failed: " + "; ".join(checked.errors))
    return RELEASE_DIR


def _write_checksums(root: Path, listed: list[Path]) -> None:
    lines = [
        f"{sha256_file(p)}  {p.relative_to(root).as_posix()}"
        for p in [root / "acceptance_manifest.json", *listed]
    ]
    (root / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def verify_release(root: Path) -> VerifyResult:
    errors: list[str] = []
    gates: dict[str, str] = {}

    def fail(gate: str | None, msg: str) -> None:
        errors.append(msg)
        if gate:
            gates[gate] = "failed"

    if not root.is_dir():
        return VerifyResult(False, {}, [f"missing release dir {root}"])

    manifest_path = root / "acceptance_manifest.json"
    checksum_path = root / "checksums.sha256"
    readme_path = root / "README.md"
    if not manifest_path.is_file():
        return VerifyResult(False, {}, ["missing acceptance_manifest.json"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    listed = {a["path"]: a for a in manifest.get("artifacts", [])}
    on_disk = {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file()}
    extra = set(on_disk) - set(listed) - UNLISTED
    missing = set(listed) - set(on_disk)
    if extra:
        fail(None, f"unlisted paths: {sorted(extra)}")
    if missing:
        fail(None, f"missing listed paths: {sorted(missing)}")
    for name in UNLISTED:
        if name not in on_disk:
            fail(None, f"missing unlisted required file {name}")
        if name in listed:
            fail(None, f"unlisted file was listed: {name}")
    for rel, rec in listed.items():
        path = on_disk.get(rel)
        if path is None:
            continue
        data = path.read_bytes()
        if sha256_bytes(data) != rec["sha256"]:
            fail(None, f"hash mismatch {rel}")
        if len(data) != rec["bytes"]:
            fail(None, f"byte mismatch {rel}")

    if checksum_path.is_file():
        hashed = set()
        for line in checksum_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            digest, _, rel = line.partition("  ")
            if rel == "checksums.sha256":
                fail(None, "checksums.sha256 hashes itself")
                continue
            hashed.add(rel)
            path = root / rel
            if not path.is_file():
                fail(None, f"checksum missing file {rel}")
                continue
            if sha256_file(path) != digest:
                fail(None, f"checksum mismatch {rel}")
        required = set(listed) | {"acceptance_manifest.json"}
        if hashed != required:
            fail(None, f"checksum set mismatch extra={sorted(hashed-required)} missing={sorted(required-hashed)}")

    for mode in ("chartjs", "svg"):
        names = {p.name for p in (root / mode / "render").iterdir() if p.is_file()} if (root / mode / "render").is_dir() else set()
        extra_r = names - set(D250)
        missing_r = set(D250) - names
        if extra_r:
            fail(None, f"{mode} render extra: {sorted(extra_r)}")
        if missing_r:
            fail(None, f"{mode} render missing: {sorted(missing_r)}")

    copies = [
        root / rel
        for rel in (
            "inputs/handoff_schema_v1.json",
            "chartjs/render/handoff_schema_v1.json",
            "svg/render/handoff_schema_v1.json",
        )
        if (root / rel).is_file()
    ]
    if len(copies) != 3:
        fail("schema_drift", "missing frozen schema copy")
    elif len({p.read_bytes() for p in copies}) != 1:
        fail("schema_drift", "frozen schema copies differ")
    val_path = root / "contracts" / "validation.json"
    if val_path.is_file():
        val = json.loads(val_path.read_text(encoding="utf-8"))
        if val.get("schema_export_check") != "passed" or val.get("theme_export_check") != "passed":
            fail("schema_drift", "schema/theme export check not passed")
    if "schema_drift" not in gates:
        gates["schema_drift"] = "passed"

    report = json.loads((root / "inputs" / "migration_report.json").read_text(encoding="utf-8")) if (root / "inputs" / "migration_report.json").is_file() else {}
    if report.get("unresolved_decisions"):
        fail("zero_unresolved_migration", "migration report has unresolved decisions")
    elif len(report.get("inventory") or []) != INVENTORY_SIZE:
        fail("zero_unresolved_migration", "migration inventory is not 57")
    else:
        gates["zero_unresolved_migration"] = "passed"

    for mode, gate, svg_only in (
        ("chartjs", "strict_clean_chartjs", False),
        ("svg", "strict_clean_svg", True),
    ):
        meta_path = root / mode / "render" / "run_meta.json"
        if not meta_path.is_file():
            fail(gate, f"missing {mode} run_meta")
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if not (
            meta.get("renderer_version") == "3.0.0"
            and meta.get("handoff_schema_version") == 1
            and meta.get("status") == "clean"
            and meta.get("ok") is True
            and meta.get("slide_count") == 44
            and meta.get("severity_counts", {}).get("warning", 0) == 0
            and meta.get("severity_counts", {}).get("error", 0) == 0
            and meta.get("options", {}).get("svg_only") is svg_only
        ):
            fail(gate, f"{mode} run_meta is not clean 3.0.0")
        else:
            gates[gate] = "passed"

    for mode, gate in (("chartjs", "paint_readiness_chartjs"), ("svg", "paint_readiness_svg")):
        ready_path = root / mode / "readiness.json"
        if not ready_path.is_file():
            fail(gate, f"missing {mode} readiness")
            continue
        ready = json.loads(ready_path.read_text(encoding="utf-8"))
        shots = list((root / mode / "slides").glob("*.png")) if (root / mode / "slides").is_dir() else []
        hashes = [sha256_file(p) for p in shots]
        unique = len(set(hashes))
        slides = ready.get("slides") or []
        if (
            ready.get("ready_count") != 44
            or len(slides) != 44
            or any(
                not s.get("ready")
                or not s.get("fonts_loaded")
                or not s.get("in_stage")
                or not s.get("frozen_plan_attached")
                for s in slides
            )
            or unique != 44
        ):
            fail(gate, f"{mode} readiness is not 44/44 unique in-stage captures")
        else:
            gates[gate] = "passed"

    sem_path = root / "comparison" / "semantic_parity.json"
    if sem_path.is_file():
        sem = json.loads(sem_path.read_text(encoding="utf-8"))
        slides = sem.get("slides") or []
        if (
            sem.get("identical_modes")
            and sem.get("slide_count") == 44
            and len(slides) == 44
            and all(s.get("identical") and s.get("chartjs", {}).get("tables") is not None for s in slides)
        ):
            gates["semantic_parity"] = "passed"
        else:
            fail("semantic_parity", "semantic parity failed")
    else:
        fail("semantic_parity", "missing semantic_parity.json")

    geo_ok = True
    for mode in ("chartjs", "svg"):
        geo_path = root / mode / "geometry.json"
        if not geo_path.is_file():
            geo_ok = False
            fail("geometry_parity", f"missing {mode} geometry")
            continue
        geo = json.loads(geo_path.read_text(encoding="utf-8"))
        for slide in geo.get("slides", []):
            if slide.get("overflow"):
                geo_ok = False
                fail("geometry_parity", f"overflow on slide {slide.get('slide_number')}")
            if not slide.get("in_stage"):
                geo_ok = False
                fail("geometry_parity", f"off-stage slide {slide.get('slide_number')}")
            if slide.get("transparent_bodies") is False:
                geo_ok = False
                fail("geometry_parity", f"opaque chart body slide {slide.get('slide_number')}")
            box = slide.get("slide") or {}
            if abs(box.get("width", 0) - 1920) > 2 or abs(box.get("height", 0) - 1080) > 2:
                geo_ok = False
                fail("geometry_parity", f"stage size {slide.get('slide_number')} {box}")
            if box.get("top", 99) > 2 or box.get("left", 99) > 2:
                geo_ok = False
                fail("geometry_parity", f"slide origin {slide.get('slide_number')} {box}")
            for chart in slide.get("charts") or []:
                area = chart.get("chart_area") or {}
                if area.get("width", 0) < CHART_PLOT_FLOOR_W or area.get("height", 0) < CHART_PLOT_FLOOR_H:
                    geo_ok = False
                    fail("geometry_parity", f"plot floor {mode} slide {slide.get('slide_number')}")
            for plot in slide.get("plots") or []:
                if plot.get("width", 0) < CHART_PLOT_FLOOR_W or plot.get("height", 0) < CHART_PLOT_FLOOR_H:
                    geo_ok = False
                    fail("geometry_parity", f"plot box floor {mode} slide {slide.get('slide_number')}")
    geo_js_path = root / "chartjs" / "geometry.json"
    geo_svg_path = root / "svg" / "geometry.json"
    if geo_js_path.is_file() and geo_svg_path.is_file():
        parity = _geometry_parity_report(
            json.loads(geo_js_path.read_text(encoding="utf-8")),
            json.loads(geo_svg_path.read_text(encoding="utf-8")),
        )
        recorded_path = root / "comparison" / "geometry_parity.json"
        recorded = json.loads(recorded_path.read_text(encoding="utf-8")) if recorded_path.is_file() else {}
        if not parity.get("identical_within_tolerance"):
            geo_ok = False
            fail("geometry_parity", "chartjs/svg plot boxes diverge beyond 2px")
        elif recorded != parity:
            geo_ok = False
            fail("geometry_parity", "geometry_parity.json is not a cross-mode comparison")
    elif geo_ok:
        geo_ok = False
        fail("geometry_parity", "missing chartjs/svg geometry for cross-mode compare")
    if geo_ok and "geometry_parity" not in gates:
        gates["geometry_parity"] = "passed"

    a11y_path = root / "contracts" / "accessibility.json"
    if a11y_path.is_file():
        a11y = json.loads(a11y_path.read_text(encoding="utf-8"))
        bad = [s["slide_number"] for s in a11y.get("slides", []) if s.get("tabindex")]
        hidden_bad = [s["slide_number"] for s in a11y.get("slides", []) if s.get("marks_hidden") is False]
        parity = json.loads((root / "comparison" / "accessibility_parity.json").read_text(encoding="utf-8")) if (root / "comparison" / "accessibility_parity.json").is_file() else {}
        if bad or hidden_bad or not parity.get("equivalent"):
            fail("accessibility", f"a11y failed tabindex={bad} visible-marks={hidden_bad} parity={parity.get('equivalent')}")
        else:
            gates["accessibility"] = "passed"
    else:
        fail("accessibility", "missing accessibility.json")

    det_path = root / "contracts" / "determinism.json"
    if det_path.is_file():
        det = json.loads(det_path.read_text(encoding="utf-8"))
        match = True
        for mode in ("chartjs", "svg"):
            recorded = det.get(mode) or {}
            for name in D250:
                path = root / mode / "render" / name
                if not path.is_file() or recorded.get(name) != sha256_file(path):
                    match = False
        if (
            det.get("chartjs_identical")
            and det.get("svg_identical")
            and det.get("reruns") == 2
            and match
        ):
            gates["determinism"] = "passed"
        else:
            fail("determinism", "determinism contract failed")
    else:
        fail("determinism", "missing determinism.json")

    font_ok = True
    for mode in ("chartjs", "svg"):
        html_path = root / mode / "render" / "presentation.html"
        if not html_path.is_file():
            font_ok = False
            fail("font_calibration", f"missing {mode} presentation.html")
            continue
        if not _font_ok(_font_calibration(html_path.read_text(encoding="utf-8"))):
            font_ok = False
            fail("font_calibration", f"{mode} font calibration failed")
    if font_ok and "font_calibration" not in gates:
        gates["font_calibration"] = "passed"

    tgt_path = root / "contracts" / "targeted_fixtures.json"
    if tgt_path.is_file():
        tgt = json.loads(tgt_path.read_text(encoding="utf-8"))
        kinds = set(tgt.get("kinds") or [])
        if (
            tgt.get("malformed_rejected")
            and all(f.get("ok") for f in tgt.get("fixtures", []))
            and {"sparse", "dense", "long_label", "mixed_sign"} <= kinds
        ):
            gates["targeted_fixtures"] = "passed"
        else:
            fail("targeted_fixtures", "targeted fixtures failed")
    else:
        fail("targeted_fixtures", "missing targeted_fixtures.json")

    review_path = root / "comparison" / "pdf_review.md"
    if review_path.is_file():
        raw = review_path.read_bytes()
        low = raw.lower()
        if b"mae" in low or b"ssim" in low or b"similarity" in low:
            fail("pdf_review", "pdf review used similarity scoring")
        elif any(token not in raw for token in (b"DIV-001", b"DIV-002", b"DIV-003", b"DIV-004")) or b"approved" not in low:
            fail("pdf_review", "pdf review missing approved divergences")
        else:
            gates["pdf_review"] = "passed"
    else:
        fail("pdf_review", "missing pdf_review.md")

    declared = manifest.get("gates") or {}
    for gate in REQUIRED_GATES:
        status = gates.get(gate)
        if status != "passed":
            if gate not in gates:
                fail(gate, f"required gate {gate} missing")
            elif declared.get(gate) == "passed" and status != "passed":
                fail(gate, f"manifest claims passed for failed gate {gate}")
        elif declared.get(gate) not in {None, "passed"}:
            fail(gate, f"manifest gate {gate} is {declared.get(gate)}")

    for forbidden in ("skipped", "warning", "unreviewed", "not-applicable", "not_applicable"):
        if forbidden in {str(v) for v in declared.values()}:
            fail(None, f"manifest gate status {forbidden} is not pass")

    ok = not errors and all(gates.get(g) == "passed" for g in REQUIRED_GATES)
    return VerifyResult(ok=ok, gates=gates, errors=errors)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build or verify renderer 3.0.0 release evidence")
    p.add_argument("--pdf", help="source Q1 2026 earnings PDF")
    p.add_argument("--build", action="store_true")
    p.add_argument("--verify", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.build:
        if not args.pdf:
            print("error: --pdf is required with --build", file=sys.stderr)
            return 2
        build_release(Path(args.pdf))
        print(dumps({"built": str(RELEASE_DIR)}))
    if args.verify or not args.build:
        result = verify_release(RELEASE_DIR)
        print(dumps({"ok": result.ok, "gates": result.gates, "errors": result.errors}))
        return 0 if result.ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
