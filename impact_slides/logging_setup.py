"""Centralized logging setup (v3 #23) + read-only git provenance helpers.

Extracted from the monolith. The logger factory is backend-flexible:
structlog when available (structured key-value logs), stdlib logging otherwise,
exposed through a single kwarg-style API (``log.info("msg", key=value)``).

Git helpers are read-only — they never commit, stage, or push; they only read
``.git/refs`` to stamp "which code produced this output?" into run_metadata.json.
"""
from __future__ import annotations

import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

try:
    import structlog
    _HAS_STRUCTLOG = True
except ImportError:  # pragma: no cover - graceful degradation
    structlog = None
    _HAS_STRUCTLOG = False


def git_commit() -> Optional[str]:
    """Short commit hash if running inside a git worktree, else None.
    Read-only: runs `git rev-parse --short HEAD` and returns the result. Never
    commits/stages/pushes. Returns None if git is absent or not a repo."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=str(Path(__file__).parent),
            timeout=5,
        )
        return out.decode().strip() or None
    except Exception:
        return None


def git_dirty() -> Optional[bool]:
    """True if the working tree has uncommitted edits (so the run isn't a
    clean reproduction of the recorded commit). None if git unavailable.
    Read-only: `git diff --quiet` exits non-zero when there are uncommitted
    changes. Never commits/stages/pushes."""
    try:
        rc = subprocess.call(
            ["git", "diff", "--quiet"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(Path(__file__).parent),
            timeout=5,
        )
        return rc != 0  # non-zero => working tree differs from commit
    except Exception:
        return None


_LOG = None  # singleton logger for the preprocessor instance


class _StdlibLogAdapter:
    """Thin adapter over stdlib logging so call sites can use the structlog-style
    kwarg API (log.info("msg", key=value, ...)) even when structlog isn't
    installed. Extra kwargs are folded into the message as key=value pairs."""

    def __init__(self, stdlib_logger, base_ctx: dict):
        self._log = stdlib_logger
        self._ctx = dict(base_ctx)
        self._file_logger = None

    def bind(self, **kwargs):
        new = _StdlibLogAdapter(self._log, {**self._ctx, **kwargs})
        new._file_logger = self._file_logger
        return new

    def _emit(self, level, event, kwargs):
        merged = {**self._ctx, **kwargs}
        extra = " ".join(f"{k}={v!r}" for k, v in merged.items())
        msg = f"{event}" + (f" {extra}" if extra else "")
        self._log.log(level, msg)
        if self._file_logger is not None:
            self._file_logger.log(level, msg)

    def debug(self, event, **kw):   self._emit(logging.DEBUG, event, kw)
    def info(self, event, **kw):    self._emit(logging.INFO, event, kw)
    def warning(self, event, **kw): self._emit(logging.WARNING, event, kw)
    def error(self, event, **kw):   self._emit(logging.ERROR, event, kw)
    def exception(self, event, **kw): self._emit(logging.ERROR, event, kw)


def _structlog_console_renderer():
    """Pick a console renderer: colors in a TTY, plain text under capture
    (pytest redirects) so string assertions keep working."""
    try:
        if sys.stderr.isatty():
            return structlog.dev.ConsoleRenderer(colors=True)
        return structlog.dev.ConsoleRenderer(colors=False)
    except Exception:
        return structlog.dev.ConsoleRenderer(colors=False)


def get_logger(name: str = "preprocessor", log_file: Optional[Path] = None,
               verbose: bool = False, run_id: Optional[str] = None,
               version: str = "0.0.0"):
    """Build (or return the cached) preprocessor logger.

    Sinks:
      - console: human-readable, leveled (INFO by default, DEBUG if verbose)
      - log_file: machine-readable, full-fidelity (DEBUG+), JSON-lines with
        structlog or plain timestamped lines with stdlib

    Run-wide context (version, commit, run_id) is bound once so every log
    line is self-describing for reproducibility.
    """
    global _LOG
    if _LOG is not None:
        return _LOG

    run_id = run_id or time.strftime("%Y%m%dT%H%M%S")
    base_ctx = {
        "version": version,
        "commit": git_commit(),
        "run_id": run_id,
    }

    if _HAS_STRUCTLOG:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                _structlog_console_renderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                logging.DEBUG if verbose else logging.INFO),
            logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
            cache_logger_on_first_use=True,
        )
        log = structlog.get_logger(name).bind(**base_ctx)
    else:
        # stdlib logging doesn't accept arbitrary kwargs like structlog. Wrap
        # it in a thin adapter so call sites can use the same kwarg API
        # (log.info("msg", file=..., duration=...) regardless of backend.
        stdlib_log = logging.getLogger(name)
        stdlib_log.setLevel(logging.DEBUG)
        stdlib_log.propagate = False
        if not stdlib_log.handlers:
            ch = logging.StreamHandler(sys.stderr)
            ch.setLevel(logging.DEBUG if verbose else logging.INFO)
            ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            stdlib_log.addHandler(ch)
        log = _StdlibLogAdapter(stdlib_log, base_ctx)

    # File handler — machine-readable, full-fidelity. Attached to the stdlib
    # logger underneath both backends so the file is readable everywhere.
    if log_file is not None:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        stdlib_name = name
        fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        ))
        file_logger = logging.getLogger(stdlib_name + ".file")
        file_logger.setLevel(logging.DEBUG)
        file_logger.propagate = False
        # Clear any handlers from a previous get_logger() call so each run
        # writes to its own run.log (the stdlib logger is a singleton, but
        # the FileHandler must point at THIS run's output dir).
        for h in list(file_logger.handlers):
            file_logger.removeHandler(h)
            h.close()
        file_logger.addHandler(fh)
        log._file_logger = file_logger

    _LOG = log
    return log
