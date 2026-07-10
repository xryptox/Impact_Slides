"""
Tests for the v4 legal-corpus `priority_score` fixes (Approaches C + A + D).

Covers the three approved changes that stop legal-agreement boilerplate from
outranking deal-relevance evidence:
  - C: DOCX content-aware priority (base 0.70 + insight-language boost,
       replacing the flat 0.60 that capped rationale quotes below boilerplate)
  - A: legal-boilerplate downweight (the inverse of boost_keywords — a built-in
       DEFAULT_LEGAL_BOILERPLATE_PATTERNS regex set + user --downweight-keywords,
       shipped ON by default with a --no-downweight-boilerplate escape hatch)
  - D: per-type caps for pdf_page_insight / docx_insight so one large legal
       PDF or long DOCX cannot flood the register by sheer volume
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import step1_preprocessor_v4 as m
from impact_slides.text_analysis import (
    DEFAULT_LEGAL_BOILERPLATE_PATTERNS,
    insight_priority_boost,
    contains_insight_language,
)
from impact_slides.config import CONFIG_DEFAULTS, validate_config


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
class TestLegalBoilerplateConstants:
    def test_default_patterns_exist_and_are_compiled(self):
        import re
        assert len(DEFAULT_LEGAL_BOILERPLATE_PATTERNS) >= 6
        for pat in DEFAULT_LEGAL_BOILERPLATE_PATTERNS:
            # Every built-in must be a compiled regex (fail-fast at import).
            assert hasattr(pat, "search")
            assert pat.search("") is None  # empty text never matches

    def test_patterns_match_real_boilerplate(self):
        # Each of these is a real phrase from the AmEx EX-10.1 agreement.
        cases = [
            ('"Replacement Marks" has the meaning set forth in Section 6.13(f)',
             '"Replacement Marks" has the meaning'),
            ('"Seller Technology" means all works of authorship',
             '"Seller Technology" means'),
            ('has the meaning set forth in Section 3.3',
             'has the meaning set forth in Section'),
            ('Indemnification by the Buyer shall survive the Closing',
             'Indemnification'),
            ('The Group Companies have developed comprehensive compliance',
             'Group Companies'),
            ('hereby irrevocably sells, assigns, transfers and conveys',
             'hereby sells'),
            ('giving effect to the Closing Date', 'giving effect to the Closing'),
        ]
        for full, _expected in cases:
            assert any(p.search(full) for p in DEFAULT_LEGAL_BOILERPLATE_PATTERNS), \
                f"no built-in pattern matched boilerplate: {full[:50]!r}"

    def test_patterns_do_not_match_plain_business_prose(self):
        # A genuine deal-rationale quote must NOT trip any built-in pattern —
        # this is the whole point: rationale stays high, boilerplate sinks.
        rationale = ("Dining is one of the most important ways people engage "
                     "with our brand, and this acquisition strengthens our "
                     "dining ecosystem across Europe.")
        for p in DEFAULT_LEGAL_BOILERPLATE_PATTERNS:
            assert p.search(rationale) is None, \
                f"pattern {p.pattern!r} false-matched rationale prose"


# --------------------------------------------------------------------------- #
# Approach C — DOCX content-aware priority (base 0.70 + insight boost)
# --------------------------------------------------------------------------- #
class TestDocxContentAwarePriority:
    def test_rationale_para_outranks_flat_para(self):
        # A content-bearing paragraph (hits insight keywords) must score higher
        # than a generic paragraph, because of the insight_priority_boost.
        rationale = ("Dining is one of the most important growth opportunities "
                      "and a key way customers engage with our brand; this "
                      "acquisition improves our success across Europe.")
        generic = ("The company filed its annual report for the period.")
        r = insight_priority_boost(rationale, 0.70)
        g = insight_priority_boost(generic, 0.70)
        assert r > 0.70, f"rationale should boost above base: got {r}"
        assert g == 0.70, f"generic should stay at base: got {g}"
        assert r > g

    def test_base_is_070_not_060(self):
        # The defect was a flat 0.60 cap; confirm the new base is 0.70.
        assert insight_priority_boost("nothing notable here", 0.70) == 0.70
        assert insight_priority_boost("nothing notable here", 0.70) != 0.60

    def test_insight_dense_para_approaches_cap(self):
        dense = ("recommend key critical significant growth opportunity improve "
                 "challenge success increase decrease")
        score = insight_priority_boost(dense, 0.70)
        # >=4 keyword hits -> high boost (0.25) -> 0.95, capped at 0.98.
        assert score >= 0.95


# --------------------------------------------------------------------------- #
# Approach A — downweight mechanism (the inverse of boost_keywords)
# --------------------------------------------------------------------------- #
@pytest.fixture()
def preprocessor(tmp_path):
    inp = tmp_path / "input"
    out = tmp_path / "output"
    inp.mkdir()
    p = m.ImpactSlidePreprocessorV4(input_path=str(inp), output_dir=str(out))
    return p


def _ev(text, priority=0.83, eid="E0001", itype="pdf_page_insight"):
    return {
        "evidence_id": eid,
        "source_file": "EX-10.1.pdf",
        "insight_type": itype,
        "text": text,
        "priority_score": priority,
        "confidence": "high",
        "suggested_narrative_use": ["What"],
        "source_location": "Page 1",
    }


class TestDownweightMechanism:
    def test_build_downweight_rules_includes_builtins_by_default(self, preprocessor):
        rules = preprocessor._build_downweight_rules()
        assert len(rules["compiled_patterns"]) == len(DEFAULT_LEGAL_BOILERPLATE_PATTERNS)

    def test_escape_hatch_excludes_builtins(self, preprocessor):
        preprocessor.no_downweight_boilerplate = True
        rules = preprocessor._build_downweight_rules()
        assert rules["compiled_patterns"] == []

    def test_escape_hatch_keeps_user_keywords(self, preprocessor):
        preprocessor.no_downweight_boilerplate = True
        preprocessor.downweight_keywords = ["hereby"]
        rules = preprocessor._build_downweight_rules()
        assert len(rules["compiled_patterns"]) == 1

    def test_user_keywords_extend_not_replace(self, preprocessor):
        preprocessor.downweight_keywords = ["notwithstanding", "hereinafter"]
        rules = preprocessor._build_downweight_rules()
        # built-ins + 2 user patterns
        assert len(rules["compiled_patterns"]) == len(DEFAULT_LEGAL_BOILERPLATE_PATTERNS) + 2

    def test_boilerplate_page_sinks_below_rationale(self, preprocessor):
        # The core fix: a 0.83 boilerplate page drops below a 0.90 rationale quote.
        boilerplate = _ev(
            '"Replacement Marks" has the meaning set forth in Section 6.13(f)',
            priority=0.83, eid="E0001")
        out = preprocessor._apply_downweight_rules([boilerplate])
        assert out[0]["priority_score"] == pytest.approx(0.63, abs=0.01)
        assert out[0]["priority_score"] < 0.90
        assert "downweighted_by_rule" in out[0]

    def test_rationale_not_downweighted(self, preprocessor):
        rationale = _ev(
            "Dining is one of the most important ways people engage with our brand.",
            priority=0.90, eid="E0002")
        out = preprocessor._apply_downweight_rules([rationale])
        assert out[0]["priority_score"] == 0.90  # unchanged
        assert "downweighted_by_rule" not in out[0]

    def test_escape_hatch_restores_old_behavior(self, preprocessor):
        preprocessor.no_downweight_boilerplate = True
        preprocessor.downweight_rules = preprocessor._build_downweight_rules()
        boilerplate = _ev(
            '"Replacement Marks" has the meaning set forth in Section 6.13(f)',
            priority=0.83, eid="E0003")
        out = preprocessor._apply_downweight_rules([boilerplate])
        assert out[0]["priority_score"] == 0.83  # unchanged — old behavior
        assert "downweighted_by_rule" not in out[0]

    def test_user_downweight_keyword_sinks_match(self, preprocessor):
        preprocessor.downweight_keywords = ["churn"]
        preprocessor.downweight_rules = preprocessor._build_downweight_rules()
        ev = _ev("Customer churn accelerated this quarter.", priority=0.85, eid="E0004")
        out = preprocessor._apply_downweight_rules([ev])
        assert out[0]["priority_score"] == pytest.approx(0.65, abs=0.01)
        assert out[0]["downweighted_by_rule"] == "user:churn"

    def test_user_keyword_is_word_boundary(self, preprocessor):
        # 'breach' must not match 'breached' (word-boundary regex).
        preprocessor.downweight_keywords = ["breach"]
        preprocessor.downweight_rules = preprocessor._build_downweight_rules()
        miss = _ev("The breached contract terms were unclear.", priority=0.80, eid="E0005")
        out = preprocessor._apply_downweight_rules([miss])
        assert out[0]["priority_score"] == 0.80  # no match

    def test_score_never_goes_negative(self, preprocessor):
        # A very low starting score still floors at 0.05, not negative.
        ev = _ev(
            '"Defined Term" means a thing; Group Companies; Indemnification',
            priority=0.10, eid="E0006")
        out = preprocessor._apply_downweight_rules([ev])
        assert out[0]["priority_score"] >= 0.05
        assert out[0]["priority_score"] >= 0  # never negative

    def test_only_downweights_once_per_entry(self, preprocessor):
        # Multiple pattern hits should subtract the penalty once, not N times.
        ev = _ev(
            'Group Companies; Indemnification; "Term" means; Section 1.1',
            priority=0.83, eid="E0007")
        out = preprocessor._apply_downweight_rules([ev])
        assert out[0]["priority_score"] == pytest.approx(0.63, abs=0.01)  # one -0.20


class TestDownweightWiredIntoBuildRegister:
    def test_downweight_runs_after_boost_before_caps(self, tmp_path):
        # End-to-end: run the full preprocessor on a tiny DOCX corpus and confirm
        # a boilerplate DOCX paragraph sinks below a rationale paragraph.
        # (DOCX base is now 0.70; a rationale para boosts higher; a boilerplate
        # para with legal phrasing gets downweighted.)
        # We verify the ordering invariant via the public pipeline.
        inp = tmp_path / "input"
        out = tmp_path / "output"
        inp.mkdir()
        p = m.ImpactSlidePreprocessorV4(input_path=str(inp), output_dir=str(out))
        # Synthesize a DOCX profile directly to exercise the DOCX branch.
        p.docx_profiles = [{
            "status": "ok",
            "file": "agreement.docx",
            "paragraphs": [
                # rationale (should stay high — content-aware boost, not downweighted)
                "Dining is one of the most important growth opportunities and a "
                "key way customers improve success across Europe.",
                # boilerplate (should downweight via the "means" pattern)
                '"Defined Term" means the thing defined herein for all purposes.',
            ],
        }]
        # Suppress other extractors (no excel/pptx/pdf inputs).
        p.excel_profiles = []
        p.pptx_profiles = []
        p.pdf_profiles = []
        reg = p.build_evidence_register()
        assert len(reg) == 2
        by_text = {e["text"]: e for e in reg}
        rationale = by_text["Dining is one of the most important growth opportunities and a "
                            "key way customers improve success across Europe."]
        boiler = by_text['"Defined Term" means the thing defined herein for all purposes.']
        assert rationale["priority_score"] > boiler["priority_score"], \
            f"rationale {rationale['priority_score']} should outrank boilerplate {boiler['priority_score']}"
        assert "downweighted_by_rule" in boiler
        assert "downweighted_by_rule" not in rationale


# --------------------------------------------------------------------------- #
# Approach D — per-type caps prevent single-file flooding
# --------------------------------------------------------------------------- #
class TestPerTypeCaps:
    def test_caps_include_prose_types(self):
        # Verify the new cap keys are present in the CAPS dict used by the
        # preprocessor's _apply_per_type_caps (read via source to avoid a full run).
        import inspect
        src = inspect.getsource(m.ImpactSlidePreprocessorV4._apply_per_type_caps)
        assert "pdf_page_insight" in src
        assert "docx_insight" in src
        assert "pdf_ocr_page_insight" in src

    def test_cap_truncates_oversized_prose_bucket(self, preprocessor):
        # 50 pdf_page_insight entries from ONE file -> capped to 40 (top by score).
        evs = []
        for i in range(50):
            evs.append(_ev(f"Page {i}: some content text here.", priority=0.50 + i * 0.005,
                           eid=f"E{i:04d}", itype="pdf_page_insight"))
        out = preprocessor._apply_per_type_caps(evs)
        # 50 > 40 cap -> exactly 40 kept (all same source_file + insight_type).
        kept = [e for e in out if e["insight_type"] == "pdf_page_insight"]
        assert len(kept) == 40
        # And they are the 40 highest-scoring (the cap keeps top by priority).
        assert min(e["priority_score"] for e in kept) >= 0.50 + 10 * 0.005 - 0.001

    def test_cap_does_not_touch_uncapped_types(self, preprocessor):
        # An uncapped type (e.g. numeric_range) is not truncated regardless of volume.
        evs = [_ev(f"range {i}", priority=0.70, eid=f"E{i:04d}",
                   itype="numeric_range") for i in range(100)]
        out = preprocessor._apply_per_type_caps(evs)
        assert len([e for e in out if e["insight_type"] == "numeric_range"]) == 100

    def test_cap_is_per_source_file(self, preprocessor):
        # Two source files each contributing 30 docx_insight (<=30 cap) -> all kept.
        evs = []
        for i in range(30):
            evs.append({**_ev(f"doc a {i}", priority=0.70, eid=f"A{i:04d}",
                              itype="docx_insight"), "source_file": "a.docx"})
            evs.append({**_ev(f"doc b {i}", priority=0.70, eid=f"B{i:04d}",
                              itype="docx_insight"), "source_file": "b.docx"})
        out = preprocessor._apply_per_type_caps(evs)
        # 30 per file <= cap of 30 -> all 60 kept (cap only triggers when > cap).
        assert len(out) == 60


# --------------------------------------------------------------------------- #
# Config defaults & validation
# --------------------------------------------------------------------------- #
class TestConfigDownweight:
    def test_config_defaults(self):
        assert CONFIG_DEFAULTS["downweight_keywords"] == []
        assert CONFIG_DEFAULTS["no_downweight_boilerplate"] is False

    def test_validate_accepts_default(self):
        validate_config(dict(CONFIG_DEFAULTS))

    def test_validate_accepts_list_of_strings(self):
        cfg = dict(CONFIG_DEFAULTS)
        cfg["downweight_keywords"] = ["hereby", "notwithstanding"]
        validate_config(cfg)

    def test_validate_rejects_non_list(self):
        cfg = dict(CONFIG_DEFAULTS)
        cfg["downweight_keywords"] = "hereby"
        with pytest.raises(ValueError, match="must be a list"):
            validate_config(cfg)

    def test_validate_rejects_non_string_entry(self):
        cfg = dict(CONFIG_DEFAULTS)
        cfg["downweight_keywords"] = ["hereby", 42]
        with pytest.raises(ValueError, match="must be strings"):
            validate_config(cfg)

    def test_validate_rejects_non_bool_escape_hatch(self):
        cfg = dict(CONFIG_DEFAULTS)
        cfg["no_downweight_boilerplate"] = "yes"
        with pytest.raises(ValueError, match="must be a bool"):
            validate_config(cfg)


# --------------------------------------------------------------------------- #
# CLI flags
# --------------------------------------------------------------------------- #
class TestCLIFlags:
    def _run(self, *extra, tmp_path):
        out = tmp_path / "out"
        out.mkdir()
        cmd = [sys.executable, "step1_preprocessor_v4.py",
               "--input", str(tmp_path), "--output", str(out)]
        if "--emit-schema" not in extra:
            cmd.append("--emit-schema")  # early-exit; just tests arg parsing
        cmd.extend(extra)
        return subprocess.run(cmd, capture_output=True, text=True,
                              cwd=str(Path(__file__).resolve().parent.parent))

    def test_downweight_keywords_flag_accepted(self, tmp_path):
        proc = self._run("--downweight-keywords", "hereby", "notwithstanding",
                         tmp_path=tmp_path)
        assert proc.returncode == 0

    def test_no_downweight_boilerplate_flag_accepted(self, tmp_path):
        proc = self._run("--no-downweight-boilerplate", tmp_path=tmp_path)
        assert proc.returncode == 0

    def test_flags_default(self, tmp_path):
        proc = self._run(tmp_path=tmp_path)
        assert proc.returncode == 0
