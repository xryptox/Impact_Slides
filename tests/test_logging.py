"""
Tests for v3 #23 — centralized logging + run_metadata.json.

Covers:
  - get_logger() factory: stdlib fallback works without structlog; levels
    (debug/info/warning/error) emit correctly; kwargs folded into messages
  - run.log file written with timestamped leveled lines
  - run_metadata.json always emitted with version, git, run_id, timing,
    config snapshot, optional-deps inventory, counts
  - git helpers: read-only, return commit/dirty (or None outside a repo)
  - config snapshot flows from merge_config (#21) into run_metadata
  - error files produce ERROR-level log lines + the errors count in metadata
"""
from __future__ import annotations

import json
import logging
from io import StringIO
from contextlib import redirect_stderr
from pathlib import Path

import pandas as pd
import pytest

import step1_preprocessor_v3 as m


@pytest.fixture()
def make_preprocessor(tmp_workspace):
    """Build a v3 preprocessor (overrides conftest's v2 fixture)."""
    def _make(filter_level="permissive"):
        inp = tmp_workspace / "input"
        out = tmp_workspace / "output"
        inp.mkdir(parents=True, exist_ok=True)
        p = m.ImpactSlidePreprocessorV2(
            input_path=str(inp), output_dir=str(out), filter_level=filter_level,
        )
        return p, inp, out
    return _make


# --------------------------------------------------------------------------- #
# Version + git helpers
# --------------------------------------------------------------------------- #
class TestProvenance:
    def test_version_constant_exists(self):
        assert m.__version__ == "3.0.0"

    def test_git_commit_returns_string_or_none(self):
        c = m.git_commit()
        assert c is None or (isinstance(c, str) and len(c) >= 6)

    def test_git_dirty_returns_bool_or_none(self):
        d = m.git_dirty()
        assert d is None or isinstance(d, bool)

    def test_git_helpers_read_only(self, tmp_path):
        """Running git_commit/git_dirty must not stage, commit, or push anything.
        Verify by checking git status is unchanged after calling them."""
        import subprocess
        before = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=str(Path(m.__file__).parent),
        ).decode()
        m.git_commit()
        m.git_dirty()
        after = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=str(Path(m.__file__).parent),
        ).decode()
        assert before == after, "git helpers modified the working tree state"


# --------------------------------------------------------------------------- #
# Logger factory
# --------------------------------------------------------------------------- #
class TestLoggerFactory:
    def setup_method(self):
        # reset the singleton so each test gets a fresh logger
        m._LOG = None

    def test_get_logger_returns_logger(self):
        log = m.get_logger()
        assert log is not None
        assert hasattr(log, "info") and hasattr(log, "error")

    def test_logger_emits_info(self, caplog):
        log = m.get_logger(verbose=True)
        with caplog.at_level(logging.DEBUG, logger="preprocessor"):
            log.info("test_event", key="value")
        assert "test_event" in caplog.text
        assert "value" in caplog.text

    def test_logger_emits_warning_and_error(self, caplog):
        log = m.get_logger(verbose=True)
        with caplog.at_level(logging.DEBUG, logger="preprocessor"):
            log.warning("warn_event")
            log.error("err_event")
        assert "warn_event" in caplog.text
        assert "err_event" in caplog.text
        assert "WARNING" in caplog.text
        assert "ERROR" in caplog.text

    def test_logger_writes_run_log_file(self, tmp_path):
        m._LOG = None
        log = m.get_logger(log_file=tmp_path / "run.log", verbose=True)
        log.info("file_test", stage="unit")
        # flush handlers
        for h in logging.getLogger("preprocessor.file").handlers:
            h.flush()
        content = (tmp_path / "run.log").read_text()
        assert "file_test" in content
        assert "INFO" in content
        assert "stage=" in content

    def test_logger_binds_context(self, caplog):
        """bound context (version, commit, run_id) appears on every line."""
        m._LOG = None
        log = m.get_logger(verbose=True, run_id="TEST_RUN_ID")
        with caplog.at_level(logging.DEBUG, logger="preprocessor"):
            log.info("context_test")
        assert "TEST_RUN_ID" in caplog.text
        assert m.__version__ in caplog.text


# --------------------------------------------------------------------------- #
# run_metadata.json
# --------------------------------------------------------------------------- #
class TestRunMetadata:
    def test_run_metadata_always_emitted(self, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}))
        p.run()
        meta_path = out / "run_metadata.json"
        assert meta_path.exists()
        meta = json.loads(meta_path.read_text())
        # required fields
        assert meta["preprocessor_version"] == m.__version__
        assert "git" in meta and "commit" in meta["git"] and "dirty" in meta["git"]
        assert "run_id" in meta
        assert "started_at" in meta and "finished_at" in meta
        assert meta["total_seconds"] > 0
        assert "timing" in meta and "stages" in meta["timing"]
        assert meta["timing"]["total_seconds"] > 0

    def test_run_metadata_counts(self, make_excel, make_pptx, make_preprocessor):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}), name="a.xlsx")
        make_pptx(slides=[{"title": "T", "body": "body"}], name="d.pptx")
        p.run()
        meta = json.loads((out / "run_metadata.json").read_text())
        assert meta["counts"]["files_discovered"] == 2
        assert meta["counts"]["files_processed"] == 2
        assert meta["counts"]["evidence_entries"] == len(p.evidence_register)
        assert meta["counts"]["errors"] == 0

    def test_run_metadata_optional_deps_inventory(self, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}))
        p.run()
        meta = json.loads((out / "run_metadata.json").read_text())
        deps = meta["environment"]["optional_deps"]
        # each optional dep is a bool
        for dep, present in deps.items():
            assert isinstance(present, bool), f"{dep} not a bool: {present}"
        # structlog may be absent; pydantic/fitz should be present in test env
        assert deps["fitz_pymupdf"] is True
        assert deps["structlog"] == m._HAS_STRUCTLOG

    def test_run_metadata_config_snapshot(self, make_excel, make_preprocessor):
        """The resolved config (from #21 merge_config) is captured so the
        exact options that produced this output are recorded."""
        p, inp, out = make_preprocessor()
        p.config_snapshot = {
            "filter_level": "permissive",
            "dedup_engine": "tfidf",
            "boost_keywords": ["growth"],
        }
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}))
        p.run()
        meta = json.loads((out / "run_metadata.json").read_text())
        assert meta["config"]["filter_level"] == "permissive"
        assert meta["config"]["dedup_engine"] == "tfidf"
        assert meta["config"]["boost_keywords"] == ["growth"]

    def test_run_metadata_environment(self, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}))
        p.run()
        meta = json.loads((out / "run_metadata.json").read_text())
        env = meta["environment"]
        assert "python_version" in env and env["python_version"]
        assert "platform" in env and env["platform"]

    def test_run_metadata_finished_after_started(self, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}))
        p.run()
        meta = json.loads((out / "run_metadata.json").read_text())
        assert meta["started_at"] <= meta["finished_at"]


# --------------------------------------------------------------------------- #
# run.log file
# --------------------------------------------------------------------------- #
class TestRunLogFile:
    def test_run_log_created(self, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}))
        p.run()
        assert (out / "run.log").exists()

    def test_run_log_contains_pipeline_events(self, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}), name="data.xlsx")
        p.run()
        content = (out / "run.log").read_text()
        assert "pipeline_start" in content
        assert "files_discovered" in content
        assert "spreadsheet_processed" in content
        assert "data.xlsx" in content
        assert "pipeline_complete" in content
        assert "run_metadata_emitted" in content

    def test_run_log_has_timestamps_and_levels(self, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}))
        p.run()
        content = (out / "run.log").read_text()
        # each line has a timestamp + level
        lines = [l for l in content.splitlines() if l.strip()]
        assert lines
        for line in lines:
            assert "|" in line
            assert "INFO" in line or "WARNING" in line or "ERROR" in line or "DEBUG" in line


# --------------------------------------------------------------------------- #
# Error logging
# --------------------------------------------------------------------------- #
class TestErrorLogging:
    def test_error_file_produces_error_log_line(self, make_excel, make_preprocessor, monkeypatch):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}), name="good.xlsx")

        def boom(path):
            return {"status": "error", "file": str(path), "error": "synthetic"}

        monkeypatch.setattr(p, "extract_pptx", boom)
        from pptx import Presentation
        Presentation().save(inp / "d.pptx")
        p.run()
        content = (out / "run.log").read_text()
        assert "pptx_failed" in content
        assert "ERROR" in content
        meta = json.loads((out / "run_metadata.json").read_text())
        assert meta["counts"]["errors"] >= 1
