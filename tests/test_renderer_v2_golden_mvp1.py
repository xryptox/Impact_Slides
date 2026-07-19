"""SC-GOLDEN-1 / SC-OFFLINE-1 — charts + disclosure, self-contained.

Spec: wiki/SCOPE_renderer_v2_mvp1.md
"""
from __future__ import annotations

import json
from pathlib import Path

from impact_slides.renderer_v2 import render_deck
from impact_slides.renderer_v2.manifest import remote_fetch_urls, validate_html

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "renderer_v2"
GOLDEN = FIXTURES / "golden_mvp1_handoff.json"

# Optional human-review export (gitignored path is fine; also under fixtures).
REVIEW_DIR = Path(__file__).resolve().parents[1] / "output" / "golden_mvp1"


def test_golden_handoff_exists():
    assert GOLDEN.is_file()
    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    slides = data.get("slides") or []
    assert len(slides) >= 6


def test_sc_golden_1_charts_and_disclosure_offline(tmp_path: Path):
    out = tmp_path / "out"
    result = render_deck(GOLDEN, out, strict=True)
    html_path = out / "presentation.html"
    html = html_path.read_text(encoding="utf-8")
    run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))

    # Delivery / offline policy
    assert result.get("delivery") == "self-contained" or run_meta.get("delivery") == "self-contained"
    assert remote_fetch_urls(html) == []
    assert validate_html(html, delivery="self-contained") == []

    # Charts half (P3)
    assert "charts" in run_meta.get("features_enabled", [])
    assert "charts" in (run_meta.get("assets_inlined") or [])
    assert 'data-chartjs="1"' in html
    assert "chartjs-config" in html
    assert "initCharts" in html
    # At least bar + line type markers in configs
    assert '"type": "bar"' in html or '"type":"bar"' in html
    assert '"type": "line"' in html or '"type":"line"' in html
    assert '"animation": false' in html or '"animation":false' in html

    # Disclosure half (P5) — all three patterns
    assert "gl-disclosure" in html
    assert 'data-disclosure="detail"' in html or "gl-disclosure-detail" in html
    assert "accordion" in html.lower()
    assert "gl-disclosure-tabs" in html or 'data-disclosure="tabs"' in html
    # No Alpine / Swiper library hooks for disclosure
    assert "alpinejs" not in html.lower()
    assert "x-data" not in html
    assert "swiper-bundle" not in html.lower()
    assert "new Swiper" not in html

    # Layout markers from golden handoff
    assert 'data-layout="grouped_bar_chart"' in html
    assert 'data-layout="line_chart"' in html
    assert 'data-layout="combo_chart"' in html


def test_sc_golden_1_export_review_copy():
    """Write a durable presentation.html under output/golden_mvp1 for human review."""
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    result = render_deck(GOLDEN, REVIEW_DIR, strict=True)
    html_path = REVIEW_DIR / "presentation.html"
    assert html_path.is_file()
    html = html_path.read_text(encoding="utf-8")
    assert remote_fetch_urls(html) == []
    assert html_path.stat().st_size > 100_000
    # Keep run_meta next to it for inspection
    assert (REVIEW_DIR / "run_meta.json").is_file()
    assert result.get("html_bytes", 0) > 100_000
