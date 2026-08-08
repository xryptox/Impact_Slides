# scripts

## Purpose

Repo tooling invoked by agents and CI — not product runtime.

## Ownership

- `gen_layout_index.py` — builds/checks `wiki/renderer_v2_LAYOUTS.md`
- `simulation_probe.py` — Playwright helpers for simulation geometry probes (#137 identity, #146 paint-ready charts)
- `amex_handoff_mutations.py` — bounded Amex handoff authoring fixes applied before a fidelity pass (#148 slides 13–14 bars/pane order; #156 slide 27 three scenarios / Q1'25–Q1'28 / source note / E0270 PDF citation; #157 slides 33–37 annex matrices; #158 slide 28 pane subtitles / drop pseudo `top_total`); does not change renderer defaults. CLI: `python scripts/amex_handoff_mutations.py IN.json -o OUT.json`
- Ad-hoc helpers (`render_slide_shot.py`, shell sims)
- `run_amex_simulation_v9.sh` — historical isolated SuperGrok 4.5 GNHF launcher for the measure-only Amex v9 baseline
- `run_amex_simulation_v10.sh` — isolated SuperGrok 4.5 GNHF launcher for the v10 closed-ticket revalidation plus full 44-page PDF↔HTML comparison; its temporary GNHF home must not replace `~/.gnhf/config.yml`

## Local Contracts

- Layout index search is pure Python over `git ls-files` (no ripgrep dependency)
- Fixture column ignores `.html`/`.htm` (full-deck baselines embed every `.layout-*` class and false-hit many layouts); handoff JSON is the fixture signal
- `--check` must stay CI-green; regenerate when registry, recipes, or test references change
- Do not commit `TASK_*.md` briefs (gitignored)
- Simulation probes address slides by `data-slide-number` + expected `data-layout` only (via `simulation_probe.py`); zero selector matches and missing painted Chart.js `$datalabels` models are probe failures, never successful empty observations. Both Amex launcher prompts carry that identity/datalabel contract. Screenshot callers use `wait_for_paint_ready_charts` (instance + nonzero size + chartArea + dataset elements, held across one rAF) — never `Chart.getChart` alone or a fixed sleep; the v10 launcher prompt requires it before chart-slide screenshots (#146).
- V10 full comparison artifacts map HTML slide N to PyMuPDF index N-1 / physical PDF page N, preserve 1920×1080 pixels per source/rendered half, and are qualitative evidence only: no MAE, similarity percentage, pixel-diff score, or heatmap.
- Next Amex fidelity pass must run `amex_handoff_mutations.apply_all` (or the CLI) on the copied baseline handoff before render so slides 13–14 keep grouped/dual vertical bars and PDF pane order, slide 27 keeps three source scenarios through Q1'28, its SAAR note, and E0270 PDF citation, slides 33–37 keep complete annex matrices, and slide 28 drops pseudo `top_total` in favor of pane `$ in billions` subtitles + `stack_total_labels`; preserve the mutated handoff under the simulation pass as evidence. Contracts: `tests/test_amex_s13_s14_handoff_contract.py`, `tests/test_amex_s27_scenarios.py`, `tests/test_amex_annex_33_37_handoff.py`, `tests/test_amex_s28_handoff_contract.py`.

## Work Guidance

- One-shot migration scripts: run, delete, or leave uncommitted unless reused

## Verification

- `python scripts/gen_layout_index.py --check`
- `pytest -q tests/test_gen_layout_index.py`
- `pytest -q tests/test_simulation_probe_contract.py` (Playwright; skipped in CI when not installed)
- `pytest -q tests/test_amex_s13_s14_handoff_contract.py` (#148 handoff bar/pane contract)
- `pytest -q tests/test_amex_s27_scenarios.py` (#156 slide-27 source scenarios / paint-ready contract)
- `pytest -q tests/test_amex_annex_33_37_handoff.py` (#157 annex matrix restore contract)
- `pytest -q tests/test_amex_s28_handoff_contract.py tests/test_multi_panel_pane_headings.py` (#158 slide-28 pane titles)

## Child DOX Index

- No child AGENTS.md.
