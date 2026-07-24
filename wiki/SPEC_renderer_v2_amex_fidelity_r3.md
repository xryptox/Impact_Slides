# SPEC (stub): Amex Q1'26 IR fidelity — round 3 (v3 residual gaps)

**Status:** alignment record from the 2026-07-24 grill-with-docs session. Full acceptance criteria live in the child tickets; this stub records the locked decisions only.

**Evidence:** `simulation/amex_q1_2026/GAP_ANALYSIS.md` (v3 AFTER round-2 run; mean MAE 89.10–89.17% vs v2 final 89.25% — flat mean, structural wins; compare shots under `simulation/amex_q1_2026/passes/pass_0N/screenshots/compare_YY.png`).

**Predecessor:** epic #86 (round 2, closed). Round-2 results verified by v3: F3 signed stacks **resolved**, F6+ cover load path **resolved**; horizontal bar tiles, callout nodes, tall multi_panel slots, freestanding pill shells all exist but several are **weak / mis-wired**.

## Locked decisions (grilling Q1–Q8)

1. **Q1 — F10+ is a bug.** `y_axis_min`/`y_axis_max` on `horizontal_bar_chart` land under `scales.x.ticks` instead of scale-root `min`/`max`; Chart.js silently ignores them and the 90–100 anniversary window never paints. Valid handoff config mis-placed by the renderer = broken behavior on an existing surface. Wave 0.
2. **Q2 — full catalog.** All 9 v3 open items, bundling R1/R4/F12+ as one polish ticket, minus R3 (see Q6) → **8 children** under one round-3 epic.
3. **Q3 — one bug only.** F10+ carries the bug label; N1/N2/R2/F11+/N3/F4+/polish are enhancements (each behaves per its shipped ACs; the gaps are new capability or weak chrome).
4. **Q4 — two tracks.** Platinum chain: F10+ (W0) → R2 ‖ N2 (W1) → F11+ (W2). Free-floating (no edges, disjoint surfaces): N1, N3, F4+, polish. Frontier at filing = F10+ plus all four free-floaters.
5. **Q5 — done bar upgraded.** Contract tests **plus a fresh Playwright screenshot of the affected slide** posted as an image artifact on each issue (round 2 shipped structural probes only; that was called out in the round-2 review).
6. **Q6 — R3 dropped permanently.** No third-party trademarks or brand assets — recorded as a CONTEXT.md rule. The v3 sim handoffs (all three passes) were reverted to the v2 cover/trailing-divider output (slides 1 and 44; v2's invented generic star SVG is original artwork, not Amex IP). Cover placement-recipe work is out of this round.
7. **Q7 — N2 config surface.** `bar_labels_inside` upgrades to accept `"category"` (≡ current `true`, backward compatible) or `"series"` (paints series names — e.g. years — inside bars). No new key; old handoffs unchanged.
8. **Q8 — shared understanding confirmed.**

## Ticket map

| Ticket | Gap IDs | Label | Track / blocked by |
|--------|---------|-------|--------------------|
| T1 | **F10+** scale-root min/max on horizontal_bar | bug | W0 (Platinum chain) |
| T2 | **R2** IR callout chrome (pill band arrow + under-axis chevron geometry) | enhancement | W1 ← T1 |
| T3 | **N2** `bar_labels_inside: "series"` | enhancement | W1 ← T1 |
| T4 | **F11+** IR navy dual tall-card multi_panel skin | enhancement | W2 ← T3 |
| T5 | **N1** secondary_visual under non-line chart layouts | enhancement | free-floating |
| T6 | **N3** stacked category total tops / signed parentheses | enhancement | free-floating |
| T7 | **F4+** freestanding pill packing density | enhancement | free-floating |
| T8 | polish: **R1** stage chrome + **R4** hero scale + **F12+** annex headers | enhancement | free-floating |

All children: `fidelity`, `renderer-v2`, `ready-for-agent` labels. Chart.js remains the canonical painter; SVG fallback per prior rounds. Minimal `chart_config` extension: only `bar_labels_inside` upgrade (Q7); everything else is geometry/chrome on existing surfaces.

## Out of scope

- R3 / Centurion or any third-party trademark assets (permanent rule).
- Cover placement recipe (dropped with R3).
- MAE/SSIM gates in CI (white-biased metric; screenshots are human evidence).
- Animation, Alpine, Swiper, Mermaid (MVP1.1 queue, separate track).
