"""Contract tests for renderer_v2 self-contained delivery foundation (P0).

Spec: wiki/SPEC_renderer_v2_p0_self_contained.md
Seams under test (pre-agreed in spec §4/§7):
  - render_deck(..., delivery=...) public API
  - CLI flags --self-contained / --use-cdn (mutually exclusive)
  - lib_inliner.build_head_assets / iter_core_assets
  - remote_fetch_urls / validate_html(delivery=...)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

import impact_slides.renderer_v2.lib_inliner as lib_inliner
from impact_slides.renderer_v2 import render_deck
from impact_slides.renderer_v2.cli import main
from impact_slides.renderer_v2.lib_inliner import (
    FONTS_DIR,
    FONT_MANIFEST,
    DeliveryMode,
    FontFace,
    build_head_assets,
    iter_core_assets,
)
from impact_slides.renderer_v2.manifest import remote_fetch_urls, validate_html

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "renderer_v2"
MINI = FIXTURES / "mini_handoff.json"


def _deck_meta(html: str) -> dict:
    m = re.search(
        r'<script type="application/json" id="DECK_META">(.*?)</script>',
        html,
        re.S,
    )
    assert m, "DECK_META script block missing"
    return json.loads(m.group(1))


# ---------------------------------------------------------------------------
# P0.1 — delivery mode plumbing
# ---------------------------------------------------------------------------

class TestDeliveryPlumbing:
    def test_default_delivery_is_self_contained(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)

        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert run_meta["delivery"] == "self-contained"

        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert _deck_meta(html)["delivery"] == "self-contained"

    def test_cdn_delivery_recorded(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False, delivery="cdn")

        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert run_meta["delivery"] == "cdn"

        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert _deck_meta(html)["delivery"] == "cdn"

    def test_assets_inlined_recorded_in_run_meta(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)

        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert "font-boardroom" in run_meta["assets_inlined"]

    def test_invalid_delivery_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="delivery"):
            render_deck(MINI, tmp_path / "out", strict=False, delivery="bogus")

    def test_cli_rejects_conflicting_flags(self, tmp_path):
        with pytest.raises(SystemExit) as exc:
            main([
                "--handoff", str(MINI),
                "--out", str(tmp_path / "out"),
                "--self-contained",
                "--use-cdn",
            ])
        assert exc.value.code != 0

    def test_cli_use_cdn_flag(self, tmp_path):
        out = tmp_path / "out"
        rc = main(["--handoff", str(MINI), "--out", str(out), "--use-cdn"])
        assert rc == 0
        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert run_meta["delivery"] == "cdn"

    def test_cli_self_contained_flag(self, tmp_path):
        out = tmp_path / "out"
        rc = main(["--handoff", str(MINI), "--out", str(out), "--self-contained"])
        assert rc == 0
        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert run_meta["delivery"] == "self-contained"


# ---------------------------------------------------------------------------
# P0.2 — lib_inliner + assets layout
# ---------------------------------------------------------------------------

class TestLibInliner:
    def test_core_assets_resolve(self):
        assets = iter_core_assets()
        assert assets, "expected at least one core asset"
        for asset in assets:
            assert asset.asset_id
            assert asset.kind in {"font", "css", "js"}

    def test_self_contained_head_has_no_remote_fetch(self):
        bundle = build_head_assets(DeliveryMode.SELF_CONTAINED)
        assert "https://" not in bundle.head_html
        assert "http://" not in bundle.head_html

    def test_cdn_head_includes_google_fonts(self):
        bundle = build_head_assets(DeliveryMode.CDN)
        assert "fonts.googleapis.com" in bundle.head_html

    def test_bundle_meta_records_mode_and_bytes(self):
        bundle = build_head_assets(DeliveryMode.SELF_CONTAINED)
        assert bundle.meta["mode"] == "self-contained"
        assert "bytes_inlined" in bundle.meta
        assert isinstance(bundle.meta["assets"], list)

    def test_unknown_feature_id_warns(self, capsys):
        build_head_assets(DeliveryMode.SELF_CONTAINED, feature_ids=["bogus-lib"])
        assert "bogus-lib" in capsys.readouterr().err

    def test_reserved_feature_ids_do_not_warn_unknown(self, capsys):
        build_head_assets(
            DeliveryMode.SELF_CONTAINED,
            feature_ids=["charts", "mermaid", "alpine", "swiper", "icons"],
        )
        assert "unknown" not in capsys.readouterr().err.lower()


class TestShellAssets:
    def test_default_render_has_no_google_fonts(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "fonts.googleapis.com" not in html

    def test_cdn_render_keeps_google_fonts(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False, delivery="cdn")
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "fonts.googleapis.com" in html

    def test_assets_inlined_recorded_in_deck_meta(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert isinstance(_deck_meta(html)["assets_inlined"], list)


# ---------------------------------------------------------------------------
# P0.3 — vendored Boardroom fonts
# ---------------------------------------------------------------------------

class TestVendoredFonts:
    def test_manifest_covers_boardroom_families(self):
        families = {f.family for f in FONT_MANIFEST}
        assert "Source Sans 3" in families
        assert "IBM Plex Sans" in families

    def test_vendored_font_files_and_licenses_exist(self):
        assert FONT_MANIFEST, "FONT_MANIFEST must list vendored faces"
        for face in FONT_MANIFEST:
            assert (FONTS_DIR / face.filename).is_file(), face.filename
        assert (FONTS_DIR / "SOURCE_SANS_3_LICENSE.txt").is_file()
        assert (FONTS_DIR / "IBM_PLEX_SANS_LICENSE.txt").is_file()

    def test_self_contained_embeds_font_face_data_urls(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "@font-face" in html
        assert "data:font/woff2;base64," in html
        assert 'font-family: "Source Sans 3"' in html
        assert 'font-family: "IBM Plex Sans"' in html
        assert "fonts.googleapis.com" not in html

    def test_cdn_mode_does_not_embed_woff2(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False, delivery="cdn")
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "data:font/woff2;base64," not in html
        assert "fonts.googleapis.com" in html

    def test_missing_font_asset_fails_self_contained(self, monkeypatch):
        bogus = FontFace(
            family="Bogus Sans",
            weight="400",
            style="normal",
            filename="definitely-not-there.woff2",
        )
        monkeypatch.setattr(lib_inliner, "FONT_MANIFEST", (bogus,))
        with pytest.raises(FileNotFoundError, match="self-contained"):
            lib_inliner.build_head_assets(lib_inliner.DeliveryMode.SELF_CONTAINED)


# ---------------------------------------------------------------------------
# P0.4 — remote URL validation (SC-REG-1)
# ---------------------------------------------------------------------------

class TestRemoteFetchUrls:
    def test_detects_stylesheet_link(self):
        html = '<link href="https://fonts.googleapis.com/css2?family=X" rel="stylesheet">'
        assert remote_fetch_urls(html) == ["https://fonts.googleapis.com/css2?family=X"]

    def test_detects_script_src(self):
        html = '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'
        assert remote_fetch_urls(html) == ["https://cdn.jsdelivr.net/npm/chart.js"]

    def test_detects_css_import(self):
        html = '<style>@import url("https://example.com/x.css");</style>'
        assert remote_fetch_urls(html) == ["https://example.com/x.css"]

    def test_detects_remote_font_url(self):
        html = "@font-face { src: url('https://example.com/f.woff2') format('woff2'); }"
        assert remote_fetch_urls(html) == ["https://example.com/f.woff2"]

    def test_detects_protocol_relative(self):
        html = '<link href="//fonts.googleapis.com/css2?family=X" rel="stylesheet">'
        assert remote_fetch_urls(html) == ["//fonts.googleapis.com/css2?family=X"]

    def test_ignores_svg_xmlns(self):
        html = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">'
            '<foreignObject><div xmlns="http://www.w3.org/1999/xhtml">x</div>'
            "</foreignObject></svg>"
        )
        assert remote_fetch_urls(html) == []

    def test_ignores_data_urls(self):
        html = "@font-face { src: url(data:font/woff2;base64,AAAA) format('woff2'); }"
        assert remote_fetch_urls(html) == []

    def test_dedupes_repeated_urls(self):
        html = (
            '<script src="https://cdn.example.com/a.js"></script>'
            '<script src="https://cdn.example.com/a.js"></script>'
        )
        assert remote_fetch_urls(html) == ["https://cdn.example.com/a.js"]

    def test_detects_img_src(self):
        html = '<img src="https://cdn.example.com/x.png" alt="x">'
        assert remote_fetch_urls(html) == ["https://cdn.example.com/x.png"]

    def test_detects_iframe_src(self):
        html = '<iframe src="https://example.com/embed"></iframe>'
        assert remote_fetch_urls(html) == ["https://example.com/embed"]

    def test_detects_video_and_source(self):
        html = (
            '<video src="https://cdn.example.com/a.mp4">'
            '<source src="https://cdn.example.com/b.webm" type="video/webm">'
            "</video>"
        )
        assert remote_fetch_urls(html) == [
            "https://cdn.example.com/a.mp4",
            "https://cdn.example.com/b.webm",
        ]

    def test_detects_srcset_candidates(self):
        html = (
            '<img srcset="https://cdn.example.com/a.png 1x, '
            'https://cdn.example.com/b.png 2x" alt="x">'
        )
        urls = remote_fetch_urls(html)
        assert "https://cdn.example.com/a.png" in urls
        assert "https://cdn.example.com/b.png" in urls


class TestValidateHtmlDelivery:
    _POISONED = (
        "<!DOCTYPE html><html><head>"
        '<link href="https://fonts.googleapis.com/css2?family=X" rel="stylesheet">'
        "</head><body>#00175a #006fcf BoardroomEarnings gl-slide deck-stage "
        "fitStage</body></html>"
    )

    def test_self_contained_flags_remote_stylesheet(self):
        errs = validate_html(self._POISONED, delivery="self-contained")
        assert any("fonts.googleapis.com" in e for e in errs)

    def test_default_delivery_is_self_contained(self):
        errs = validate_html(self._POISONED)
        assert any("fonts.googleapis.com" in e for e in errs)

    def test_cdn_mode_skips_remote_check(self):
        errs = validate_html(self._POISONED, delivery="cdn")
        assert not any("remote" in e.lower() or "fonts.googleapis" in e for e in errs)

    def test_default_render_passes_remote_check(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert remote_fetch_urls(html) == []
