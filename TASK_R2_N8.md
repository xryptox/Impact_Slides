# Ticket bundle: R2 IR callout/board chrome + N8 CAGR dual-ended rule

You are working in an isolated git worktree on branch `feat/r2-n8-callout-recipe`,
branched from `origin/main` at `94d6f27`. Full suite baseline before you touch
anything: **1296 passed, 15 skipped**.

These two tickets are bundled because they share one mechanism: the callout
overlay family (`_build_callout_overlays` in `impact_slides/renderer_v2/charts.py`,
the `calloutGeometry` afterLayout plugin in `shell.py`, and the
`.chartjs-callout*` CSS block in `css/components.css`). Do not split them across
branches.

## Context you need first

Read `wiki/SPEC_renderer_v2_amex_fidelity_r5.md` and the R2/N8 rows of
`wiki/baseline_v8_GAP_ANALYSIS.md`.

Critical background: the *placement* half of R2 is already SOLVED and verified
to ±0.1px by ticket T1 (PR #115) plus T6/T7/T9 (PR #120). The overlay nodes are
positioned from live Chart.js `chartArea` pixel space by the `calloutGeometry`
plugin. **Do not re-derive or re-engineer that geometry.** What remains is purely
the *art recipe* — what the chrome looks like, not where it sits.

Also already closed, do NOT reopen:
- R2 elbow L-bracket arm down to the axis — accepted divergence, r5 spec L3.
- R3 Centurion seal — permanent wontfix, no third-party brand assets.

## Ground truth

The PDF is at `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf`.
Render pages with PyMuPDF at dpi 170. Deck slide index == fitz 0-based page index
for these: slide 05 -> page 5, slide 16 -> page 16.

Frozen v8 handoff for rendering: fetch it with

    git fetch origin gnhf/objective-produce-a-b7e827
    git show origin/gnhf/objective-produce-a-b7e827:simulation/amex_q1_2026/passes/pass_03/handoff.json > /tmp/v8h.json

## N8 — CAGR dual-ended rule (do this one FIRST; it is better specified)

Slide 16, `primary_visual.chart_config.callouts` declares:

    [{"type": "band", "from": 0, "to": 7, "text": "17% CAGR"}]

I measured the PDF recipe from page 16. It is:

- A **thin horizontal navy rule** spanning from the first bar's centre to the
  last bar's centre, sitting ABOVE the tallest bar, well clear of it.
- An **arrowhead at BOTH ends** (left-pointing at the start, right-pointing at
  the end) — a dual-ended measure line.
- A **blue rounded pill centred on the rule**, containing `17% / Year`, which
  interrupts/overlays the rule at its midpoint.
- A small **gray sub-caption `% CAGR` centred directly beneath the pill**.

Today `band` paints a translucent full-height span roughly 678x413 covering the
whole plot, which reads as a shaded region rather than a measure line. `band` and
`elbow_arrow` are both wrong for this; the elbow is a thick continuum capsule.

Your call on mechanism, but the two candidates are: extend `band` with a
declarative style variant, or add a new callout type (e.g. `measure_rule`) to
`_CALLOUT_TYPES`. Prefer whichever needs less new machinery. If you add a type,
it must fail closed on unknown/missing anchors exactly like the existing types,
and it must be positioned by the existing `calloutGeometry` plugin from
`chartArea` — not by hardcoded wrap percentages. That percentage-of-wrap mistake
is the single most repeated bug in this subsystem (T1, T6, T7, T9 all fixed
instances of it); do not add a fifth.

The handoff text is `17% CAGR` but the PDF shows `17% / Year` in the pill and
`% CAGR` as the sub-caption. Do NOT invent a text-splitting heuristic in the
renderer. Either drive it from declarative config the handoff can set, or render
the given text in the pill and leave the sub-caption to an optional key. Say
which you chose and why.

While you are on slide 16, two smaller observations I measured — fix them only
if they fall out cheaply and cleanly, otherwise report them and leave them:
- PDF bar value labels are **gray**, ours are navy.
- PDF shows `$2.0`, we render `$2` (trailing zero dropped by the `:g` rule in
  `_fmt_value_label`). Changing this affects the shared formatter that ticket
  T14 just unified and has a pinned test contract in
  `tests/test_bar_point_labels_t14.py` — do not break those tests. If a fix
  needs an opt-in config key, that is acceptable; a silent global change is not.

## R2 — IR callout/board chrome recipe

Slide 05 tile 0 (`grouped_bar_chart`, label "Spend Growth is Accelerating")
declares:

    callouts: [{"type":"elbow_arrow","from":0,"to":4,"value":11,"text":"+ ~6 percentage points"},
               {"type":"chevron","at":2,"text":"Refresh"}]

Slide 05 has been the worst-looking board for seven simulation rounds despite
three verified-correct geometry fixes. The residual, per v8, is chrome recipe:

1. **Elbow silhouette.** Ours is a thick full-span capsule spanning bar 0 to bar
   4. The PDF art is a shorter, thinner line-art elbow that leads into a pill
   rather than being one continuous thick capsule.
2. **IR board head chrome.** The PDF board is title-only. Ours paints a dual
   legend (both `side_legend` and the Chart.js legend) plus heavier title
   packing. NOTE: v7 proved `side_legend` is load-bearing here — stripping it
   grows the chart wrap from 709 to 853px and makes things worse. So this is a
   renderer-side chrome question, not a handoff strip.
3. **Chevron scale** relative to the PDF marker.

**Measure before you change anything.** Crop the PDF and our render side by
side, and write down actual pixel numbers for the elbow's stroke thickness,
length, pill size, and the chevron's dimensions, before touching CSS. If your
measurement shows my characterisation above is wrong, say so and stop — do not
implement against a description you have disproved. That has already happened
twice on this board (R4 was mis-scoped as a type-scale gap for two rounds; N5
was mis-scoped as typography).

R2 is subjective art, unlike N8. If after measuring you judge that part of it
cannot be closed without guessing, implement the parts you are confident in and
report the rest as accepted divergence with your reasoning. A smaller honest
diff beats a speculative restyle.

## Constraints

- **SC-COMPAT-1**: decks that do not opt into new behaviour must render
  byte-identically. Any new knob defaults to today's output. Prove this by
  serializing configs before and after for an unaffected chart and diffing.
- Positioning comes from Chart.js `chartArea` via the existing plugin. No new
  hardcoded percentage-of-wrap positions.
- Use Boardroom tokens, not hardcoded hex or px spacing. There are token audit
  tests (`test_components_css_no_hardcoded_border_radius`,
  `test_no_hardcoded_hex_outside_css_strings`, `test_no_literal_px_spacing_outside_tokens`)
  that WILL fail the build. Beware `--radius-round`: it is `50%`, not `999px`,
  so on a wide short box it paints an ellipse. That trap has now bitten three
  times. Use `--radius-md` (14px) for pills.
- Stay out of these files/areas — another worktree owns them: the `segmentNames`
  plugin in `shell.py`, `exterior_segment_names` / `segment_name_*` handling in
  `charts.py`, and stacked-bar packing.
- Separate commits per ticket (N8, then R2) on the one branch.

## Verification — this is where previous tickets failed

Run the **FULL** suite (`python -m pytest tests/ -q`), not a file-scoped subset.
A file-scoped run has twice let a token-audit failure land on main. Baseline is
1296 passed, 15 skipped.

Then verify **visually and numerically on the live deck**, because config-level
assertions are exactly what let PRs #97 and #104 pass while being visibly wrong:

1. Render the v8 handoff, drive to the slide by toggling the `.active` class on
   `section.slide` (`scrollIntoView` does NOT navigate).
2. Measure the new chrome's real bounding boxes against `chartArea` and the
   relevant `scales.x.getPixelForValue(...)` / bar centres. State
   measured-vs-expected pairs with a ±4px tolerance.
3. Take a screenshot and **crop and actually look at it**. Numbers within
   tolerance can still look wrong: a pill can be within 4px on all edges and
   still paint as an ellipse.

## When implementation is done: run the gate yourself

After your commits are in and the full suite is green, gate the branch:

    export PATH="$PATH:/c/Users/Ag1Le/AppData/Local/no-mistakes"
    no-mistakes axi run --intent "<your intent>"

Rules for the gate:
- `--intent` must state the user-facing goal plus the decisions and tradeoffs
  you made — not a restatement of the diff. Mention what you deliberately did
  NOT do and why.
- It blocks for several minutes. That is normal.
- If it reports a review finding, fix it on top of the branch as a new commit.
  Never reset, rebase, abort-and-restart, or replace the branch in a way that
  drops pipeline fix commits.
- If it parks at a step awaiting approval, or a finding needs a judgment call
  that is not obviously mine to make, STOP and report rather than guessing.
- Known infrastructure flake: if the run appears frozen at one step for tens of
  minutes, check `no-mistakes doctor` — the daemon can die and orphan the run,
  which shows misleadingly as `running`. Recovery is `no-mistakes daemon start`,
  then rerun. This is not your code failing.
- Do NOT merge. The user merges.

## Report back to me (the orchestrating agent)

When you are done, write a concise report covering:
1. What you measured, with numbers, before implementing — and whether it
   confirmed or contradicted the brief above.
2. What you changed, per ticket, and the mechanism you chose with the reasoning.
3. Anything you deliberately did NOT fix, and why.
4. Full suite result, and your live geometry measured-vs-expected pairs.
5. The gate outcome: run id, PR number, every finding it raised and how each was
   resolved.
6. Anything that surprised you or that you are unsure about. Flag uncertainty
   explicitly — I would much rather hear "I could not verify this" than a
   confident claim I later find is wrong.

Do not push to `main`, do not merge, do not touch the other worktree's files.
