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
