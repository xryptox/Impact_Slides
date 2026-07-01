"""Tests for the OCR path in extract_pdf / _ensure_tesseract.

Covers regressions for:
- bug #3: --enable-ocr was dead (run() called extract_pdf without use_ocr)
- bug #4: Tesseract binary never located / silent failure
- bug #5: ocr_used mis-reported (computed after OCR filled text)
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import step1_preprocessor_v2_full as m

TESSERACT_CANDIDATES = [
    shutil.which("tesseract"),
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
]


def _tesseract_available() -> bool:
    for c in TESSERACT_CANDIDATES:
        if c and Path(c).is_file():
            return True
    return False


HAS_TESSERACT = _tesseract_available()


@pytest.fixture()
def pp():
    p = m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_unused")
    return p


# --------------------------------------------------------------------------- #
# _ensure_tesseract (bug #4)
# --------------------------------------------------------------------------- #
class TestEnsureTesseract:
    def test_returns_bool_and_caches(self, pp):
        assert isinstance(pp._ensure_tesseract(), bool)
        # Second call returns cached value without re-detecting
        cached = pp._ocr_available
        assert pp._ensure_tesseract() is cached

    def test_explicit_cmd_honored(self, pp):
        """An explicit tesseract_cmd is forwarded to pytesseract and used."""
        if not HAS_TESSERACT:
            pytest.skip("Tesseract not installed on this machine")
        # find the real binary
        real = next((c for c in TESSERACT_CANDIDATES if c and Path(c).is_file()), None)
        pp._ocr_available = None
        pp.tesseract_cmd = real
        import pytesseract
        assert pp._ensure_tesseract() is True
        assert pytesseract.pytesseract.tesseract_cmd == real

    def test_bad_cmd_falls_back_gracefully(self, pp, monkeypatch):
        """A non-functional explicit cmd must not crash; if no fallback works, returns False."""
        import pytesseract
        # Force every version probe to fail so neither the explicit cmd nor any
        # fallback candidate can report a working Tesseract.
        monkeypatch.setattr(pytesseract, "get_tesseract_version",
                            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("nope")))
        pp._ocr_available = None
        pp.tesseract_cmd = "/definitely/not/tesseract"
        assert pp._ensure_tesseract() is False

    def test_returns_true_when_installed(self, pp):
        if not HAS_TESSERACT:
            pytest.skip("Tesseract not installed on this machine")
        import pytesseract
        pp._ocr_available = None
        pp.tesseract_cmd = None
        assert pp._ensure_tesseract() is True
        # The underlying pytesseract command must resolve to a working binary.
        pytesseract.get_tesseract_version()  # must not raise


# --------------------------------------------------------------------------- #
# extract_pdf: OCR behavior (bugs #3, #5)
# --------------------------------------------------------------------------- #
class TestExtractPdfOcr:
    def test_use_ocr_flag_off_does_not_ocr(self, pp, real_scanned_pdf):
        """Without use_ocr, scanned pages must yield empty text and ocr_used=False."""
        r = pp.extract_pdf(real_scanned_pdf, use_ocr=False)
        assert r["status"] == "ok"
        for page in r["pages"]:
            assert page["ocr_used"] is False
            assert page["text"] == ""

    @pytest.mark.skipif(not HAS_TESSERACT, reason="Tesseract not installed")
    def test_use_ocr_flag_on_recovers_text(self, pp, real_scanned_pdf):
        """bug #3 regression: --enable-ocr must actually trigger OCR on scanned pages."""
        pp._ocr_available = None
        pp.tesseract_cmd = None
        r = pp.extract_pdf(real_scanned_pdf, use_ocr=True)
        assert r["status"] == "ok"
        ocr_pages = [p for p in r["pages"] if p["ocr_used"]]
        assert ocr_pages, "expected at least one OCR'd page"
        for p in ocr_pages:
            assert len(p["text"]) > 30  # bug #5: text is actually populated

    @pytest.mark.skipif(not HAS_TESSERACT, reason="Tesseract not installed")
    def test_ocr_used_flag_reflects_actual_ocr(self, pp, real_scanned_pdf):
        """bug #5 regression: a successfully OCR'd page must report ocr_used=True."""
        pp._ocr_available = None
        pp.tesseract_cmd = None
        r = pp.extract_pdf(real_scanned_pdf, use_ocr=True)
        for p in r["pages"]:
            if len(p["text"]) > 30:
                assert p["ocr_used"] is True
            else:
                assert p["ocr_used"] is False

    def test_missing_tesseract_warns_not_crashes(self, pp, real_scanned_pdf, monkeypatch):
        """When OCR requested but Tesseract unavailable, must warn and skip — not crash."""
        monkeypatch.setattr(pp, "_ensure_tesseract", lambda: False)
        pp._ocr_available = False
        pp._ocr_warned = False
        r = pp.extract_pdf(real_scanned_pdf, use_ocr=True)
        assert r["status"] == "ok"
        # No crash; pages empty but present
        assert len(r["pages"]) > 0

    def test_text_pdf_not_ocrd_even_with_flag(self, pp, tmp_path):
        """A text-based PDF must not invoke OCR even when use_ocr=True."""
        import fitz
        path = tmp_path / "text.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "This is a real text layer, no OCR needed here.")
        doc.save(path)
        doc.close()
        if HAS_TESSERACT:
            pp._ocr_available = None
        r = pp.extract_pdf(path, use_ocr=True)
        for p in r["pages"]:
            assert p["ocr_used"] is False
            assert "real text layer" in p["text"]


# --------------------------------------------------------------------------- #
# End-to-end: the --enable-ocr flag flows through run() (bug #3 integration)
# --------------------------------------------------------------------------- #
class TestEnableOcrFlagFlowsThroughRun:
    @pytest.mark.skipif(not HAS_TESSERACT, reason="Tesseract not installed")
    def test_enable_ocr_produces_evidence_from_scanned_pdf(self, real_scanned_pdf, tmp_workspace):
        inp = tmp_workspace / "input"
        out = tmp_workspace / "output"
        inp.mkdir(parents=True, exist_ok=True)
        import shutil as _sh
        _sh.copy(real_scanned_pdf, inp / "scan.pdf")

        p = m.ImpactSlidePreprocessorV2(input_path=str(inp), output_dir=str(out),
                                        filter_level="permissive")
        p.enable_ocr = True
        p._ocr_available = None
        p.tesseract_cmd = None
        p.run()

        import json
        ev = json.load(open(out / "evidence_register_seed.json"))
        ocr_ev = [e for e in ev if e.get("ocr_used")]
        assert ocr_ev, "bug #3: --enable-ocr produced no OCR evidence"

    def test_disable_ocr_yields_no_evidence_from_scanned_pdf(self, real_scanned_pdf, tmp_workspace):
        inp = tmp_workspace / "input"
        out = tmp_workspace / "output"
        inp.mkdir(parents=True, exist_ok=True)
        import shutil as _sh
        _sh.copy(real_scanned_pdf, inp / "scan.pdf")

        p = m.ImpactSlidePreprocessorV2(input_path=str(inp), output_dir=str(out),
                                        filter_level="permissive")
        p.enable_ocr = False
        p.run()

        import json, os
        pth = out / "evidence_register_seed.json"
        n = len(json.load(open(pth))) if os.path.isfile(pth) else 0
        assert n == 0, "scanned PDF without OCR should yield no evidence"
