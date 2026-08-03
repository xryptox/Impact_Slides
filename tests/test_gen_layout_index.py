"""Guards for scripts/gen_layout_index.py.

The layout index is a CI gate, so the generator must not depend on tooling that
may be absent. It used to shell out to ``rg`` and treat FileNotFoundError as "no
matches", which made a missing binary indistinguishable from a stale index and
would have let a regeneration overwrite a correct index with empty columns (#130).
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "gen_layout_index.py"


def _load():
    spec = importlib.util.spec_from_file_location("gen_layout_index", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestNoRipgrepDependency:
    def test_source_does_not_invoke_rg(self):
        """A pure-Python search cannot regress to shelling out unnoticed."""
        src = SCRIPT.read_text(encoding="utf-8")
        assert '"rg"' not in src and "'rg'" not in src

    def test_search_works_without_rg_on_path(self, monkeypatch):
        """The generated index must be identical with ripgrep unavailable.

        Guards the #130 failure mode directly: if the search silently degrades,
        the test/fixture columns empty out and this comparison fails.
        """
        mod = _load()
        expected = mod.build()

        real_run = subprocess.run

        def no_rg(cmd, *a, **kw):
            if cmd and cmd[0] == "rg":
                raise FileNotFoundError("rg")
            return real_run(cmd, *a, **kw)

        monkeypatch.setattr(subprocess, "run", no_rg)
        mod2 = _load()
        assert mod2.build() == expected

    def test_finds_real_references(self):
        """Sanity: the search returns hits, so the check above is not vacuous."""
        mod = _load()
        hits = mod._rg_files("gl-kpi", "tests")
        assert hits, "expected gl-kpi to be referenced under tests/"
        assert any("test_" in h for h in hits)

    def test_word_boundary_not_substring(self):
        """Word-boundary, not substring -- the reason the original used ``rg -w``.

        A bare layout name would otherwise match this very file and pollute the
        generated index, so the probes below are deliberately not real names.
        """
        mod = _load()
        # Probes are assembled at runtime: a literal here would match this very
        # file and make the assertions fail (and pollute the generated index).
        absent = "zz" + "_no_such_term_" + "qq"
        assert mod._rg_files(absent, "tests") == []
        # "gl-kpi" exists under tests/; a proper substring of it must not match.
        assert mod._rg_files("gl-kpi"[1:-1], "tests") == [], "substring leaked"

    def test_untracked_files_are_excluded(self):
        """Tracked-only mirrors rg's .gitignore behaviour; an ignored fixture
        must not appear or the index would differ between checkouts."""
        mod = _load()
        for hit in mod._rg_files("gl-kpi", "tests"):
            proc = subprocess.run(
                ["git", "ls-files", "--error-unmatch", hit],
                cwd=REPO,
                capture_output=True,
            )
            assert proc.returncode == 0, f"{hit} is not tracked by git"


class TestCheckGate:
    def test_check_passes_on_current_tree(self):
        """The committed index is current; --check is the CI gate."""
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
