# scripts

## Purpose

Repo tooling invoked by agents and CI — not product runtime.

## Ownership

- `gen_layout_index.py` — builds/checks `wiki/renderer_v2_LAYOUTS.md`
- `simulation_probe.py` — Playwright helpers for simulation geometry probes (#137)
- Ad-hoc helpers (`render_slide_shot.py`, shell sims)
- `run_amex_simulation_v9.sh` — isolated SuperGrok 4.5 GNHF launcher for the measure-only Amex v9 baseline; its temporary GNHF home must not replace `~/.gnhf/config.yml`

## Local Contracts

- Layout index search is pure Python over `git ls-files` (no ripgrep dependency)
- `--check` must stay CI-green; regenerate when registry, recipes, or test references change
- Do not commit `TASK_*.md` briefs (gitignored)
- Simulation probes address slides by `data-slide-number` + expected `data-layout` only (via `simulation_probe.py`); zero selector matches and missing painted Chart.js `$datalabels` models are probe failures, never successful empty observations. Launcher prompt in `run_amex_simulation_v9.sh` carries the same contract.

## Work Guidance

- One-shot migration scripts: run, delete, or leave uncommitted unless reused

## Verification

- `python scripts/gen_layout_index.py --check`
- `pytest -q tests/test_gen_layout_index.py`
- `pytest -q tests/test_simulation_probe_contract.py` (Playwright; skipped in CI when not installed)

## Child DOX Index

- No child AGENTS.md.
