#!/usr/bin/env python3
"""Generate wiki/renderer_v2_LAYOUTS.md — the layout lookup table for agents.

One read of the generated file answers "where do I edit layout X, and which test
guards it", replacing a 4-6 call grep expedition across dispatch/recipes/tests.

Generated, never hand-written: a hand-maintained index becomes a fourth layout
catalog and drifts like the three it exists to replace.

Usage:
    python scripts/gen_layout_index.py            # write the file
    python scripts/gen_layout_index.py --check    # CI: fail if stale
    python scripts/gen_layout_index.py --stdout   # preview
"""
from __future__ import annotations

import argparse
import functools
import inspect
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

OUT = REPO / "wiki" / "renderer_v2_LAYOUTS.md"
DISPATCH = REPO / "impact_slides" / "renderer_v2" / "layout" / "dispatch.py"

# Layout names that are substrings of other layout names, so a bare text search
# reports false hits (metric -> metric_dashboard, table -> annex_table).
# Word-boundary search handles these; listed only to document the hazard.
_SUBSTRING_HAZARDS = {"metric", "table", "cover", "timeline"}


def _recipe_map() -> dict[str, object]:
    """layout_type -> recipe callable.

    Prefers ``LAYOUT_RECIPES`` (present after the registry refactor); falls back
    to parsing the if-ladder so this script is useful *before* that lands.
    """
    from impact_slides.renderer_v2.layout import dispatch

    registry = getattr(dispatch, "LAYOUT_RECIPES", None)
    if isinstance(registry, dict) and registry:
        return dict(registry)
    return _parse_ladder(dispatch)


def _parse_ladder(dispatch_mod) -> dict[str, object]:
    """Extract the mapping from the ``if lt == "x": return recipes.render_y`` ladder."""
    from impact_slides.renderer_v2.layout import recipes

    src = DISPATCH.read_text(encoding="utf-8")
    out: dict[str, object] = {}
    # Each branch: one or more layout literals, then the recipes.* call it returns.
    pattern = re.compile(
        r'lt\s+(?:==|in)\s+(?P<lits>"[^"]+"|\([^)]*\))'
        r'(?P<body>.*?)(?=\n    if |\n    pvt|\Z)',
        re.S,
    )
    for m in pattern.finditer(src):
        layouts = re.findall(r'"([a-z0-9_]+)"', m.group("lits"))
        # Take the LAST recipe call in the branch: the chart-family branch opens
        # with a nested `if lt == "icon_grid"` guard, so the first match would
        # mis-assign render_icon_grid to every bar/heatmap layout. icon_grid gets
        # its own branch later, so nothing is lost.
        calls = re.findall(r"recipes\.(render_[a-z0-9_]+)", m.group("body"))
        if not calls:
            continue
        fn = getattr(recipes, calls[-1], None)
        if fn is None:
            continue
        kwargs = dict(re.findall(r"(\w+)=(True|False)", m.group("body")))
        kwargs.pop("active", None)
        kwargs.pop("use_chartjs", None)
        for lt in layouts:
            if lt in ("", "default", "other"):  # alias sentinels, not layouts
                continue
            out[lt] = (
                functools.partial(fn, **{k: v == "True" for k, v in kwargs.items()})
                if kwargs
                else fn
            )
    # Chart layouts route through render_chart without an explicit branch.
    from impact_slides.renderer_v2 import charts

    for lt in sorted(getattr(charts, "_CHART_LAYOUTS", frozenset())):
        out.setdefault(lt, recipes.render_icon_grid if lt == "icon_grid" else recipes.render_chart)
    return out


def _location(fn) -> str:
    """``path:line`` for a callable, unwrapping functools.partial."""
    target = fn
    while isinstance(target, functools.partial):
        target = target.func
    target = inspect.unwrap(target)
    try:
        path = Path(inspect.getsourcefile(target) or "")
        line = inspect.getsourcelines(target)[1]
    except (TypeError, OSError):
        return "?"
    try:
        path = path.relative_to(REPO)
    except ValueError:
        pass
    return f"{path.as_posix()}:{line}"


@functools.lru_cache(maxsize=1)
def _tracked_files() -> tuple[str, ...]:
    """Git-tracked repo-relative posix paths.

    Tracked-only is what makes this match ripgrep's old behaviour: rg honours
    .gitignore, so untracked fixtures (e.g. the excluded visual_regression_deck
    handoffs) were never in its results either.
    """
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return tuple(p for p in proc.stdout.split("\0") if p.strip())


def _rg_files(term: str, *paths: str) -> list[str]:
    """Word-boundary file search. Returns repo-relative posix paths.

    Pure Python on purpose. This used to shell out to ``rg`` and swallow
    FileNotFoundError as "no matches", so on a machine without ripgrep every
    test/fixture column silently came up empty, --check reported the index as
    stale, and regenerating would have overwritten a correct index with a
    degraded one (#130). Verified to return byte-identical results to the old
    ``rg -l -w`` for all 49 layouts across tests/ and tests/fixtures/.
    """
    pattern = re.compile(rf"\b{re.escape(term)}\b")
    prefixes = tuple(p.rstrip("/") for p in paths)
    hits = []
    for rel in _tracked_files():
        if not any(rel == p or rel.startswith(p + "/") for p in prefixes):
            continue
        try:
            raw = (REPO / rel).read_bytes()
        except OSError:
            continue
        if b"\0" in raw[:8192]:  # binary, as rg skips
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if pattern.search(text):
            hits.append(Path(rel).as_posix())
    return sorted(hits)


def _fmt_refs(files: list[str], strip: str, limit: int = 3) -> str:
    if not files:
        return "—"
    names = [Path(f).name.replace(strip, "") for f in files]
    shown = ", ".join(f"`{n}`" for n in names[:limit])
    if len(names) > limit:
        shown += f" +{len(names) - limit}"
    return shown


def build() -> str:
    recipes_by_layout = _recipe_map()
    from impact_slides.renderer_v2.layout import dispatch

    mode = "registry" if getattr(dispatch, "LAYOUT_RECIPES", None) else "parsed if-ladder"

    rows = []
    for lt in sorted(recipes_by_layout):
        fn = recipes_by_layout[lt]
        base = fn.func if isinstance(fn, functools.partial) else fn
        bound = ""
        if isinstance(fn, functools.partial) and fn.keywords:
            bound = " " + ", ".join(f"`{k}={v}`" for k, v in fn.keywords.items())
        tests = _rg_files(lt, "tests")
        tests = [t for t in tests if "/fixtures/" not in t]
        # Full presentation .html baselines embed every `.layout-*` CSS class
        # (and other layout names), so word-search falsely associates one deck
        # with dozens of layouts. Handoff JSON remains the fixture signal.
        fixtures = [
            f
            for f in _rg_files(lt, "tests/fixtures")
            if not f.endswith((".html", ".htm"))
        ]
        rows.append(
            f"| `{lt}` | `{base.__name__}`{bound} | {_location(fn)} "
            f"| {_fmt_refs(fixtures, '')} | {_fmt_refs(tests, 'test_')} |"
        )

    untested = [
        lt
        for lt in sorted(recipes_by_layout)
        if not [t for t in _rg_files(lt, "tests") if "/fixtures/" not in t]
    ]

    lines = [
        "# Renderer v2 — Layout Index",
        "",
        "**Generated by `scripts/gen_layout_index.py`. Do not edit by hand.**",
        f"Source of truth: {mode}.",
        "",
        "Regenerate: `python scripts/gen_layout_index.py`",
        "",
        f"{len(recipes_by_layout)} layout types.",
        "",
        "| layout_type | recipe | source | fixture | tests |",
        "|---|---|---|---|---|",
        *rows,
        "",
        "## Layouts with no direct test reference",
        "",
        (", ".join(f"`{lt}`" for lt in untested) if untested else "None — every layout is referenced.")
        + "",
        "",
        "## Notes",
        "",
        "- Test/fixture columns use word-boundary search, because some layout names are",
        f"  substrings of others ({', '.join(sorted(_SUBSTRING_HAZARDS))}).",
        "- A file listed under tests references the layout name; it is not proof of a",
        "  dedicated assertion. Treat it as the place to look first.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 if the file is stale")
    ap.add_argument("--stdout", action="store_true", help="print instead of writing")
    args = ap.parse_args(argv)

    content = build()

    if args.stdout:
        # Windows consoles default to cp1252 and mangle the em dashes.
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
        print(content, end="")
        return 0
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != content:
            print(f"{OUT.relative_to(REPO).as_posix()} is stale — regenerate", file=sys.stderr)
            return 1
        print("layout index up to date")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(content, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
