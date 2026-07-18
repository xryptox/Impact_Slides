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
        from impact_slides.renderer_v2 import render_deck

        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)

        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert run_meta["delivery"] == "self-contained"

        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert _deck_meta(html)["delivery"] == "self-contained"

    def test_cdn_delivery_recorded(self, tmp_path):
        from impact_slides.renderer_v2 import render_deck

        out = tmp_path / "out"
        render_deck(MINI, out, strict=False, delivery="cdn")

        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert run_meta["delivery"] == "cdn"

        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert _deck_meta(html)["delivery"] == "cdn"

    def test_invalid_delivery_rejected(self, tmp_path):
        from impact_slides.renderer_v2 import render_deck

        with pytest.raises(ValueError, match="delivery"):
            render_deck(MINI, tmp_path / "out", strict=False, delivery="bogus")

    def test_cli_rejects_conflicting_flags(self, tmp_path):
        from impact_slides.renderer_v2.cli import main

        with pytest.raises(SystemExit) as exc:
            main([
                "--handoff", str(MINI),
                "--out", str(tmp_path / "out"),
                "--self-contained",
                "--use-cdn",
            ])
        assert exc.value.code != 0

    def test_cli_use_cdn_flag(self, tmp_path):
        from impact_slides.renderer_v2.cli import main

        out = tmp_path / "out"
        rc = main(["--handoff", str(MINI), "--out", str(out), "--use-cdn"])
        assert rc == 0
        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert run_meta["delivery"] == "cdn"

    def test_cli_self_contained_flag(self, tmp_path):
        from impact_slides.renderer_v2.cli import main

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
        from impact_slides.renderer_v2.lib_inliner import iter_core_assets

        assets = iter_core_assets()
        assert assets, "expected at least one core asset"
        for asset in assets:
            assert asset.asset_id
            assert asset.kind in {"font", "css", "js"}

    def test_self_contained_head_has_no_remote_fetch(self):
        from impact_slides.renderer_v2.lib_inliner import (
            DeliveryMode,
            build_head_assets,
        )

        bundle = build_head_assets(DeliveryMode.SELF_CONTAINED)
        assert "https://" not in bundle.head_html
        assert "http://" not in bundle.head_html

    def test_cdn_head_includes_google_fonts(self):
        from impact_slides.renderer_v2.lib_inliner import (
            DeliveryMode,
            build_head_assets,
        )

        bundle = build_head_assets(DeliveryMode.CDN)
        assert "fonts.googleapis.com" in bundle.head_html

    def test_bundle_meta_records_mode_and_bytes(self):
        from impact_slides.renderer_v2.lib_inliner import (
            DeliveryMode,
            build_head_assets,
        )

        bundle = build_head_assets(DeliveryMode.SELF_CONTAINED)
        assert bundle.meta["mode"] == "self-contained"
        assert "bytes_inlined" in bundle.meta
        assert isinstance(bundle.meta["assets"], list)

    def test_unknown_feature_id_warns(self, capsys):
        from impact_slides.renderer_v2.lib_inliner import (
            DeliveryMode,
            build_head_assets,
        )

        build_head_assets(DeliveryMode.SELF_CONTAINED, feature_ids=["bogus-lib"])
        assert "bogus-lib" in capsys.readouterr().err

    def test_reserved_feature_ids_do_not_warn_unknown(self, capsys):
        from impact_slides.renderer_v2.lib_inliner import (
            DeliveryMode,
            build_head_assets,
        )

        build_head_assets(
            DeliveryMode.SELF_CONTAINED,
            feature_ids=["charts", "mermaid", "alpine", "swiper", "icons"],
        )
        assert "unknown" not in capsys.readouterr().err.lower()


class TestShellAssets:
    def test_default_render_has_no_google_fonts(self, tmp_path):
        from impact_slides.renderer_v2 import render_deck

        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "fonts.googleapis.com" not in html

    def test_cdn_render_keeps_google_fonts(self, tmp_path):
        from impact_slides.renderer_v2 import render_deck

        out = tmp_path / "out"
        render_deck(MINI, out, strict=False, delivery="cdn")
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "fonts.googleapis.com" in html

    def test_assets_inlined_recorded_in_deck_meta(self, tmp_path):
        from impact_slides.renderer_v2 import render_deck

        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert isinstance(_deck_meta(html)["assets_inlined"], list)
