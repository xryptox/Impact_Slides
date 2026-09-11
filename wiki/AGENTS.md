# wiki

## Purpose

Archive of historical prompts, plans, research, and specs. Not the live engineering contract.

## Ownership

- Historical and draft markdown under `wiki/`
- Reference snapshot: `DELEGATED_WORKFLOW_DETERMINISM.md` (non-binding assessment; live contract remains under `docs/agents/`)
- Research archive: `DELEGATED_WORKFLOW_TOKEN_AUDIT.md` (token-leak findings and fixes for the ticket-wave setup; live contract in root `AGENTS.md` + `docs/agents/delegated-delivery.md`)
- Final active specification: `SPEC_renderer_v3_full_deck_density_and_chart_fidelity.md` (user-approved renderer-v3/schema-v1 contract; implementation tickets may be derived from it; renderer_v2 remains legacy)
- Active parity specification: `SPEC_renderer_v3_pdf_design_parity.md` (proposed; v11→v12 design-regression root-cause analysis + DP-1..DP-7 typography/furniture/domain/verification/geometry contract and corpus backfill manifest for the 44-page Amex deck; extends the density spec; DP-6 helpers + v13 launcher shipped in #233; #249 extends DP-6 ledger probes; DP-7 stub-slack + sparse occupancy shipped in #246; observation sim still unrun; #247 records the category-aligned support chrome override; #270 paints unmarked legal continuations as `<p>` (marked stay lists); #256 accepted D167 hide_header + hairline body on remaining category-aligned fixtures; #269 retargets Amex s4/s19 to independent navy-header tables; #274 keeps independent `support-table` thead stubs on the navy band; #257 repeats the part-1 legal title and raises fixed legal type to 56/21; #260 authors s12/s15/s21 `stack_segments: show`; #268 authors s12 PDF hero KPI sentences; #272 remaps s15 reserve to `navy` and uncollides stack totals from segment labels; #255 records s4/s19 series identity, PDF ticks, s8 FHR step, Leap Year/G&S–T&E facts, and the s38 preamble; #254 records s24 `placement: above` groups + outlined %-of-total; #273 lands hero/`metric_overview` body at 27px with wrapping KPI labels; #271 folds s18 Volume/Margin into one driver label)
- Generated current index: `renderer_v2_LAYOUTS.md` (owned operationally by renderer_v2 + `scripts/gen_layout_index.py`)
- Operational learnings: `AGENT_LEARNINGS.md` (live document; updated after each wave; pointer in root `AGENTS.md`)

## Local Contracts

- Live agent entry remains root `AGENTS.md`, `CONTEXT.md`, `docs/agents/`, and code under `impact_slides/`
- `AGENT_LEARNINGS.md` is live and binding for delegated-wave work despite living in the archive; do not stale-mark it
- Stale docs carry `> **Superseded - historical...**` immediately under the H1 (see `README.md` policy)
- Do **not** mark without cause: live GPT prompts (`Impact Slide *`), `SPEC_renderer_v2_amex_fidelity_r6.md` (R6-A shipped #139; R6-C still open), current baseline gap docs (v16 is the next Q1 2026 observation report; v15 lives at commit `0f67fb3` and was never merged to main), Q4 2021 recipe-coverage report `baseline_q4_2021_RECIPE_COVERAGE.md` (Type A + Type B re-author through #293 s04 dual_chart + shared support; #315 s03 axis pin −40…20, interiors still Type A leftover; #318 re-authored s12 as stacked_bar with segment + stack-total labels and no Total Provision line; #296 accepted leftover s05 — no second labeled plot glyph; #297 accepted leftover s08 — 5 series exceeds line max 4 and interiors unlabeled; #298 accepted leftover s20 — unlabeled Value Injection hatch, no invented split dollars; #299 accepted leftover s26 — Q4'21-only vs-'19 endpoints and 5th Total T&E series; #300 accepted leftover s30 — unlabeled Unemployment/GDP scenario lines, no invented series; #301 accepted leftover s06/s07/s09/s25/s32 — unlabeled interiors, grouped_bar of labeled Q4 endpoints stands; #316 re-authored s06 right / s07 right / both s09 under-plot tables as independent navy-header `support_table` (same figures; interiors stay #301); #336 syncs those per-pane independent tables to the larger type (24px) without re-authoring; #317 s11 write-off panes pin fixed 0–5%; #320 s15/s17 rate/yield as `chart_grouped_annex` peers (no combo line); #321 re-authored s24 onto chart_grouped_annex (bars + share chips + two tables); #345 adds s24 share-chip stub `% of Total Network Volumes` + 20px centered type on bar centers (24px overflows leftover after D47 + annex); #322 s27 donut names outside + slice_id identity; #323/#342 s28 two-row category support boxes freeze/paint a 24px row gap, stub-safe wider boxes, and borderless stubs (not a navy IR table); #324 s28/s31 thin/zero stack labels uncollide in-column (never fit-drop non-zero); #343 s28/s31 inside-navy + segments stay below stack crown ($ totals only above); #335 re-authored s13 waterfall two-tone loans+receivables (Change to Q4'21 component-less; thin/$0.0 caps stay); #340 shrinks the pie/donut ring so #339 can pin s27 names+percents at 24px; #341 requires outside name/percent AABB to clear the painted disk; #344 caps generated small-percent domains at a 5-point floor (s29 2.4% on 0–5, occupancy ≥40%); #346 authors s18 independent FY'21 Revenue $42.4 support_table and s11 per-pane category 30+/GCP strips (NWO bars only; Q2'21 GCP (0.9)); next observation sim is `scripts/run_amex_simulation_q4_2021_v3_observe.sh` (`git reset --hard origin/main` then recapture; no re-author) on `gnhf/objective-given-the-d60385`; Type B remainder s35; do not stale-mark), verifier corrections (e.g. `baseline_v10_VERIFIER_CORRECTION_146.md`), normative shipped p0–p5/token specs, generated `renderer_v2_LAYOUTS.md`

- Repo-wide `rg` will not read `README.md` — per-file markers matter

## Work Guidance

- Prefer code + root/docs AGENTS over wiki plans when they disagree
- Do not implement from superseded specs

## Verification

- `python scripts/gen_layout_index.py --check` if touching the generated layouts index or its generator inputs

## Child DOX Index

- No child AGENTS.md.
