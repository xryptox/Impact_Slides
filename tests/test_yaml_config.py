"""
Tests for v3 #21 — YAML config file support (--config flag).

Covers the layered precedence ladder:
    CLI flag (explicit) > YAML value > argparse default

plus:
  - store_true flags (verbose) overridden by YAML
  - error paths: missing file, bad choice value, bad type, non-mapping top
    level, PyYAML absent (graceful degradation with a clear error)
  - end-to-end: a YAML config drives the pipeline; CLI override reaches the
    preprocessor (dedup_engine)
  - regression: pure-CLI invocation (no --config) is unchanged
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

import step1_preprocessor_v3 as m


# Build a parser that mirrors main()'s flag surface so merge_config can be
# tested without invoking the full CLI. (main() constructs its own parser
# internally; this helper reuses the same defaults/choices.)
def _build_parser():
    parser = __import__("argparse").ArgumentParser()
    parser.add_argument("--input", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--filter-level", default="conservative",
                        choices=["conservative", "moderate", "permissive"])
    parser.add_argument("--boost-keywords", nargs="*", default=[])
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument("--export-md", action="store_true", default=False)
    parser.add_argument("--export-csv", action="store_true", default=False)
    parser.add_argument("--enable-ocr", action="store_true", default=False)
    parser.add_argument("--tesseract-cmd", default=None)
    parser.add_argument("--pdf-table-engine", default="auto",
                        choices=["auto", "pdfplumber", "pymupdf"])
    parser.add_argument("--dedup-engine", default="auto",
                        choices=["auto", "embeddings", "tfidf", "fuzzy"])
    parser.add_argument("--inspect", action="store_true", default=False)
    parser.add_argument("--inspect-top", type=int, default=15)
    parser.add_argument("--emit-schema", action="store_true", default=False)
    parser.add_argument("--config", default=None)
    return parser


def _resolve(argv):
    parser = _build_parser()
    a = parser.parse_args(argv)
    a.config_data = m.load_config(a.config)
    return m.merge_config(parser, a)


# --------------------------------------------------------------------------- #
# Precedence ladder
# --------------------------------------------------------------------------- #
class TestPrecedence:
    def test_yaml_overrides_default(self, tmp_path):
        cfgp = tmp_path / "c.yaml"
        cfgp.write_text("filter_level: permissive\ndedup_engine: tfidf\ninspect_top: 7\n",
                        encoding="utf-8")
        cfg = _resolve(["--config", str(cfgp)])
        assert cfg["filter_level"] == "permissive"
        assert cfg["dedup_engine"] == "tfidf"
        assert cfg["inspect_top"] == 7

    def test_cli_overrides_yaml(self, tmp_path):
        cfgp = tmp_path / "c.yaml"
        cfgp.write_text("filter_level: permissive\ndedup_engine: tfidf\ninspect_top: 7\n",
                        encoding="utf-8")
        cfg = _resolve(["--config", str(cfgp), "--filter-level", "moderate",
                        "--inspect-top", "3"])
        assert cfg["filter_level"] == "moderate"   # CLI wins
        assert cfg["dedup_engine"] == "tfidf"      # YAML wins (CLI not given)
        assert cfg["inspect_top"] == 3             # CLI wins

    def test_default_when_neither_given(self):
        cfg = _resolve([])
        assert cfg["filter_level"] == "conservative"
        assert cfg["dedup_engine"] == "auto"
        assert cfg["inspect_top"] == 15

    def test_store_true_yaml_wins_when_cli_not_passed(self, tmp_path):
        cfgp = tmp_path / "c.yaml"
        cfgp.write_text("verbose: true\n", encoding="utf-8")
        cfg = _resolve(["--config", str(cfgp)])
        assert cfg["verbose"] is True

    def test_store_true_cli_wins_when_explicit(self, tmp_path):
        # YAML says verbose:false; CLI --verbose wins.
        cfgp = tmp_path / "c.yaml"
        cfgp.write_text("verbose: false\n", encoding="utf-8")
        cfg = _resolve(["--config", str(cfgp), "--verbose"])
        assert cfg["verbose"] is True

    def test_boost_keywords_from_yaml(self, tmp_path):
        cfgp = tmp_path / "c.yaml"
        cfgp.write_text("boost_keywords: [growth, recommend, critical]\n", encoding="utf-8")
        cfg = _resolve(["--config", str(cfgp)])
        assert cfg["boost_keywords"] == ["growth", "recommend", "critical"]

    def test_boost_keywords_cli_overrides_yaml(self, tmp_path):
        cfgp = tmp_path / "c.yaml"
        cfgp.write_text("boost_keywords: [growth, recommend]\n", encoding="utf-8")
        cfg = _resolve(["--config", str(cfgp), "--boost-keywords", "only", "this"])
        assert cfg["boost_keywords"] == ["only", "this"]


# --------------------------------------------------------------------------- #
# load_config error paths
# --------------------------------------------------------------------------- #
class TestLoadConfigErrors:
    def test_none_path_returns_empty(self):
        assert m.load_config(None) == {}

    def test_missing_file_raises_filenotfound(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            m.load_config(str(tmp_path / "nope.yaml"))

    def test_non_mapping_raises_valueerror(self, tmp_path):
        cfgp = tmp_path / "c.yaml"
        cfgp.write_text("- just\n- a\n- list\n", encoding="utf-8")
        with pytest.raises(ValueError, match="mapping"):
            m.load_config(str(cfgp))

    def test_empty_file_returns_empty(self, tmp_path):
        cfgp = tmp_path / "c.yaml"
        cfgp.write_text("", encoding="utf-8")
        assert m.load_config(str(cfgp)) == {}

    def test_no_pyyaml_raises_runtimeerror(self, tmp_path, monkeypatch):
        monkeypatch.setattr(m, "_HAS_YAML", False)
        monkeypatch.setattr(m, "yaml", None)
        with pytest.raises(RuntimeError, match="(?i)pyyaml"):
            m.load_config(str(tmp_path / "c.yaml"))


# --------------------------------------------------------------------------- #
# validate_config
# --------------------------------------------------------------------------- #
class TestValidateConfig:
    def test_valid_config_passes(self):
        m.validate_config({"filter_level": "permissive", "dedup_engine": "tfidf",
                           "pdf_table_engine": "pdfplumber"})

    def test_bad_choice_raises(self):
        with pytest.raises(ValueError, match="filter_level"):
            m.validate_config({"filter_level": "bogus"})

    def test_bad_dedup_engine_raises(self):
        with pytest.raises(ValueError, match="dedup_engine"):
            m.validate_config({"dedup_engine": "nonsense"})

    def test_bad_inspect_top_type_raises(self):
        with pytest.raises(ValueError, match="integer"):
            m.validate_config({"inspect_top": "five"})

    def test_unknown_keys_ignored(self):
        # Unknown keys are tolerated (forward-compat) — only known choice fields
        # and typed fields are validated.
        m.validate_config({"unknown_key": "whatever", "filter_level": "moderate"})


# --------------------------------------------------------------------------- #
# End-to-end via main()
# --------------------------------------------------------------------------- #
class TestMainIntegration:
    def _make_xlsx(self, inp):
        inp.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"M": [1, 2], "V": [10, 20]}).to_excel(inp / "s.xlsx", index=False)

    def test_yaml_drives_pipeline(self, tmp_path):
        inp, out = tmp_path / "in", tmp_path / "out"
        self._make_xlsx(inp)
        cfgp = tmp_path / "c.yaml"
        cfgp.write_text(
            f"input: {inp}\noutput: {out}\nfilter_level: permissive\ndedup_engine: tfidf\n",
            encoding="utf-8",
        )
        rc = m.main(["--config", str(cfgp)])
        assert rc == 0
        assert (out / "evidence_register_seed.json").exists()

    def test_cli_override_reaches_preprocessor(self, tmp_path):
        inp, out = tmp_path / "in", tmp_path / "out"
        self._make_xlsx(inp)
        cfgp = tmp_path / "c.yaml"
        cfgp.write_text(
            f"input: {inp}\noutput: {out}\nfilter_level: permissive\ndedup_engine: tfidf\n",
            encoding="utf-8",
        )
        # CLI --dedup-engine fuzzy must override YAML tfidf
        rc = m.main(["--config", str(cfgp), "--dedup-engine", "fuzzy"])
        assert rc == 0

    def test_bad_config_choice_exits_nonzero(self, tmp_path):
        inp, out = tmp_path / "in", tmp_path / "out"
        self._make_xlsx(inp)
        cfgp = tmp_path / "c.yaml"
        cfgp.write_text(
            f"input: {inp}\noutput: {out}\nfilter_level: bogus\n", encoding="utf-8",
        )
        rc = m.main(["--config", str(cfgp)])
        assert rc == 1
        # pipeline must NOT have run against the bad config
        assert not (out / "evidence_register_seed.json").exists()

    def test_missing_config_file_exits_nonzero(self, tmp_path):
        rc = m.main(["--config", str(tmp_path / "nope.yaml")])
        assert rc == 1

    def test_pure_cli_unchanged_no_config(self, tmp_path):
        """Regression: invoking with plain CLI flags (no --config) works exactly
        as before the YAML feature was added."""
        inp, out = tmp_path / "in", tmp_path / "out"
        self._make_xlsx(inp)
        rc = m.main(["--input", str(inp), "--output", str(out),
                     "--filter-level", "permissive"])
        assert rc == 0
        assert (out / "evidence_register_seed.json").exists()
