# scripts

## Purpose

Repo tooling invoked by agents and CI — not product runtime.

## Ownership

- `gen_layout_index.py` — builds/checks `wiki/renderer_v2_LAYOUTS.md`
- `simulation_probe.py` — Playwright helpers for simulation geometry probes (#137 identity, #146 paint-ready charts, #233 DP-6 design ledger: computed tick font-size/weight + furniture presence, #249 DP-6 extensions: stub ratio / support chrome / series palette / metric-value floor / bar occupancy)
- `build_canonical_amex_v1.py` — rebuilds `tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json` (D314/#196/#226/#227/#228/#225/#229/#230/#248/#258) from corrected fixtures + worksheet; not a production migrator; pins the D315 release-PDF SHA-256 into evidence locators; #226 writes s4/s19 `annotations` + category-aligned `support_table` and s5/s9/s10 independent support tables from the v2 secondary tables; #227 writes s6 left-chart `+ ~6 percentage points` annotation, s8 lodging `metric_strip` (3,400+ / 300+ / $600 / $550), and s15 reserve-rate `outlined_support` plus authored stack totals; #228 writes s12 three-band NCA `stacked_bar` (UCS / Commercial / ICS totaling ~3.x) and keeps the existing pane headings; #225 pins s11 Transaction Growth `domain.kind=fixed` 0–15; #229 writes s17 `usd_1` + CAGR `measurements` + Qualification disclosure and s18 `usd_1` + boxed YoY labels + PDF driver-card rows; #258 authors s17 dated pane headings + slide subtitle + `pane_title` identity; #230 writes s21 stacked combo shares line 702→682 + exact ROE row, s24 six growth bars + group braces + `$486B` + %-of-total boxes, and s28 FDIC callout + on-stack % and $ totals; #248 authors s6 Q3'25 `Refresh`, s8 `10x` + FHR+THC `primary_blue` / UCS Lodging `sky_blue`, s15 Q2–Q4 2.9% + write-offs `primary_blue` / reserve `sky_blue`, and s28 navy/blue/sky/gray stacks
- `renderer_3_release.py` — builds/verifies `artifacts/renderer_3_release/3.0.0/` (D315/#198); `--build` needs the tracked Q1 2026 PDF + Playwright and writes LF text (handoff + D250 copies normalized); `--verify` is hash/gate-only. Do not `--build` 3.0.0 after live corpus backfills (owner: `artifacts/renderer_3_release/AGENTS.md`).
- `amex_handoff_mutations.py` — bounded Amex handoff authoring fixes applied before a fidelity pass (#148 slides 13–14 bars/pane order; #154 slide 24 growth bars, groups, support row, and reporting note; #155 slide 21 capital-return combo + ROE support row + right KPIs; #156 slide 27 three scenarios / Q1'25–Q1'28 / source note / E0026 PDF citation; #157 slides 33–37 annex matrices; #159 slide 32 grouped peer annex tables; #158 slide 28 pane subtitles / drop pseudo `top_total`); does not change renderer defaults. CLI: `python scripts/amex_handoff_mutations.py IN.json -o OUT.json`
- `../artifacts/issue_156_slide27/` — #156 source-evidence E0026 and reproducible archived-v10/corrected 1920×1080 paint-ready recaptures.
- Ad-hoc helpers (`render_slide_shot.py`, shell sims)
- `run_amex_simulation_v9.sh` — historical isolated SuperGrok 4.5 GNHF launcher for the measure-only Amex v9 baseline
- `run_amex_simulation_v10.sh` — historical isolated SuperGrok 4.5 GNHF launcher for the v10 closed-ticket revalidation plus full 44-page PDF↔HTML comparison
- `run_amex_simulation_v11.sh` — historical isolated Grok Latest GNHF launcher for complete-deck observation after #136–#159; applies the canonical handoff mutations, revalidates every closed ticket, and produces a fresh 44-page PDF↔HTML residual ledger without changing renderer code
- `run_amex_simulation_v12.sh` — historical isolated SuperGrok 4.5 (high thinking) GNHF launcher for the first 44-page PDF↔renderer_v3 side-by-side baseline; renders the canonical D314 schema-v1 corpus strict (no mutation pass), captures stacked-deck screenshots at exact 1920×1080, and produces a qualitative ledger plus v2→v3 delta without changing renderer code; its temporary GNHF home must not replace `~/.gnhf/config.yml`
- `run_amex_simulation_v13.sh` — historical isolated SuperGrok 4.5 (high thinking) GNHF launcher for the 44-page PDF↔renderer_v3 re-run with the DP-6 design ledger; same isolated-home / strict-corpus / 1920×1080 / no-image-scoring contract as v12, plus `measured_tick_styles`, `furniture_presence`, and #249 extension probe rows in the manifest and a v12→v13 delta; its temporary GNHF home must not replace `~/.gnhf/config.yml`
- `run_amex_simulation_v14.sh` — current isolated SuperGrok 4.5 (high thinking) GNHF launcher for the 44-page PDF↔renderer_v3 re-run validating the post-v13 renderer fixes (#246 stub-slack cap + sparse bar occupancy, #247 category-support chrome, #248 sky-blue palette + KPI metric floor + line-label contrast); same isolated-home / strict-corpus / 1920×1080 / no-image-scoring contract as v13, DP-6 + #249 extension probes, and a v13→v14 delta (the v13 report was never merged to main; the prompt reads it from commit `ea541bf` via `git show`); the user triggers the sim separately; its temporary GNHF home must not replace `~/.gnhf/config.yml`

## Local Contracts

- Layout index search is pure Python over `git ls-files` (no ripgrep dependency)
- Fixture column ignores `.html`/`.htm` (full-deck baselines embed every `.layout-*` class and false-hit many layouts); handoff JSON is the fixture signal
- `--check` must stay CI-green; regenerate when registry, recipes, or test references change
- Do not commit `TASK_*.md` briefs (gitignored)
- Simulation probes address slides by `data-slide-number` + expected `data-layout` only (via `simulation_probe.py`); zero selector matches and missing painted Chart.js `$datalabels` models are probe failures, never successful empty observations. The v9–v11 launcher prompts carry that identity/datalabel contract; the v12 prompt keeps identity + paint readiness but drops `painted_datalabel_lines` because renderer_v3 has no chartjs-plugin-datalabels state (labels paint via its own context_labels/annotations/measurements chrome). The v13 prompt keeps that contract and adds DP-6 design-ledger probes: `measured_tick_styles` (computed tick font-size ≥ 20px, font-weight ≥ 600), `furniture_presence` from `DESIGN_LEDGER_FURNITURE` (zero matches = failure), and the #249 extensions (`measured_stub_ratio` on `DESIGN_LEDGER_STUB_RATIO_SLIDES`, `measured_support_chrome` on s4/s19, `measured_series_palette` on s24/s28, `measured_metric_value_styles` on s8/s12, `measured_bar_occupancy` on s28). Screenshot callers use `wait_for_paint_ready_charts` (instance + nonzero size + chartArea + dataset elements, held across one rAF) — never `Chart.getChart` alone or a fixed sleep; the v10+ launcher prompts require it before chart-slide screenshots (#146). renderer_v3 decks are stacked scroll decks (no active-class/hash navigation, fit script scales by viewport), so v12/v13 capture at an exact 1920×1080 viewport via scroll + element screenshots. The v14 prompt keeps the entire v13 probe contract unchanged and retargets the delta to v13→v14.
- V10 full comparison artifacts map HTML slide N to PyMuPDF index N-1 / physical PDF page N, preserve 1920×1080 pixels per source/rendered half, and are qualitative evidence only: no MAE, similarity percentage, pixel-diff score, or heatmap.
- renderer_v2 fidelity passes must run `amex_handoff_mutations.apply_all` (or the CLI) on the copied baseline handoff before render so slides 13–14 keep grouped/dual vertical bars and PDF pane order; slide 21 keeps the stacked capital-return combo with shares line, stack totals, ROE support row, and right summary KPIs; slide 24 keeps six growth bars, semantic groups, aligned support row, and FX-adjusted reporting note; slide 27 keeps three source scenarios through Q1'28, its SAAR note, and E0026 PDF citation; slide 32 keeps Commercial Services and International Card Services as separate peer annex tables; slides 33–37 keep complete annex matrices; and slide 28 drops pseudo `top_total` in favor of pane `$ in billions` subtitles + `stack_total_labels`; preserve the mutated handoff under the simulation pass as evidence. renderer_v3 passes skip mutations: the canonical corpus (`build_canonical_amex_v1.py` output) already bakes these corrections in — live v3 corpus furniture for slides 4/5/6/8/9/10/12/15/17/18/19/21/24/28 (leap-year callouts + support tables; s6 elbow + Refresh; s8 KPI strip + 10x; s12 three-band NCA stack; s15 reserve-rate 2.9% + authored colors; s17 $B + CAGR rule + qualification disclosure + dated pane headings; s18 $ NII + YoY boxes + driver rows; s21 shares line + exact ROE; s24 braces + `$486B` + %-of-total boxes; s28 FDIC + navy/blue/sky/gray stacks) is rebuilt there, not via the v2 mutation CLI. Contracts: `tests/test_amex_s13_s14_handoff_contract.py`, `tests/test_amex_s21_capital_handoff_contract.py`, `tests/test_amex_s24_growth_handoff_contract.py`, `tests/test_amex_s27_scenarios.py`, `tests/test_grouped_annex_table.py`, `tests/test_amex_annex_33_37_handoff.py`, `tests/test_amex_s28_handoff_contract.py`, `tests/test_amex_s4_s5_s9_s10_s19_callout_support.py`, `tests/test_amex_s6_s8_s15_furniture.py`, `tests/test_amex_s12_nca_stack.py`, `tests/test_amex_s17_s18_furniture.py`, `tests/test_amex_s21_s24_s28_furniture.py`.

## Work Guidance

- One-shot migration scripts: run, delete, or leave uncommitted unless reused

## Verification

- `python scripts/gen_layout_index.py --check`
- `pytest -q tests/test_gen_layout_index.py`
- `pytest -q tests/test_simulation_probe_contract.py` (Playwright; skipped in CI when not installed)
- `pytest -q tests/test_amex_s13_s14_handoff_contract.py` (#148 handoff bar/pane contract)
- `pytest -q tests/test_amex_s21_capital_handoff_contract.py` (#155 capital-return combo + ROE support + right KPIs)
- `pytest -q tests/test_amex_s24_growth_handoff_contract.py` (#154 growth-bar + support-row contract)
- `pytest -q tests/test_amex_s27_scenarios.py` (#156 slide-27 source scenarios / paint-ready contract)
- `pytest -q tests/test_amex_annex_33_37_handoff.py` (#157 annex matrix restore contract)
- `pytest -q tests/test_grouped_annex_table.py` (#159 slide-32 grouped peer annex contract)
- `pytest -q tests/test_amex_s28_handoff_contract.py tests/test_multi_panel_pane_headings.py` (#158 slide-28 pane titles)
- `pytest -q tests/test_amex_s4_s5_s9_s10_s19_callout_support.py` (#226 live-corpus callouts + support tables)
- `pytest -q tests/test_amex_s6_s8_s15_furniture.py` (#227/#248 s6 elbow + Refresh; s8 KPI strip + 10x; s15 reserve-rate 2.9%)
- `pytest -q tests/test_amex_s12_nca_stack.py` (#228 s12 three-band NCA stack)
- `pytest -q tests/test_amex_s17_s18_furniture.py` (#229/#258 s17 $B + CAGR + qualification + dated pane headings; s18 $ NII + YoY boxes + driver rows)
- `pytest -q tests/test_amex_s21_s24_s28_furniture.py` (#230/#248 s21 shares line + ROE; s24 braces + $486B + %-of-total; s28 FDIC + navy/blue/sky/gray stacks)
- `python scripts/renderer_3_release.py --verify`
- `pytest -q tests/test_renderer_v3_release_evidence.py` (#198 / D315)

## Child DOX Index

- No child AGENTS.md.
