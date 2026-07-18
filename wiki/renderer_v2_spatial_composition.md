# Renderer v2 — Spatial Composition Contracts

**Status:** design guidance (born from Fidelity T8 / issue #36, 2026-07-18)
**Audience:** anyone adding a layout that composes multiple visual elements on one slide

---

## The lesson

A multi-element slide (chart + support table, chart + metric strip, dual charts,
diagram + callouts) is **one composed figure, not a stack of independent
elements**. The PDF this renderer models always treats them as one figure: the
support table's quarter columns are centered exactly under the chart's category
positions and the table is bounded to the plot width.

Our renderer originally stacked elements vertically — chart SVG on top, HTML
table below at 100% card width — with no shared geometry. The defect survived
**three rounds** of fidelity review because every review asked *"is the data
right? is the element present?"* and never asked *"do the spatial relationships
hold?"*

> **Whenever two elements on a slide refer to the same data axis, coordinate
> system, or visual row/column, their spatial relationship must be designed,
> contracted, and tested — or it will silently drift.**

## The pattern: geometry contracts

1. **Single source of truth for geometry.** The element that owns a coordinate
   system (e.g. a chart builder) must *export* its geometry, never let
   consumers guess or duplicate constants. In `charts.py`:
   `_CHART_GEOMETRY` / `chart_geometry(layout_type)` is the contract for plot
   insets; all internal builders read from it, and `chart_column_interval()`
   derives the SVG x-interval that N equal columns must span to center under
   the chart's categories.

2. **Consumers derive, never hardcode.** The support table computes its
   colgroup percentages from `chart_column_interval()` output. If a builder's
   padding ever changes, the table follows automatically. Mirrored constants
   across files are how alignment rots.

3. **Shared width context.** Percentage-based alignment only works if both
   elements live in the same width container. The aligned table is nested in
   `.chart-col` inside the SVG's width-constrained wrap — not appended to the
   full-width card. (This was the actual root cause of the p4 misalignment:
   the SVG was 55% wide, the table 100%.)

4. **Semantics differ per element — model them.** Line charts place points at
   plot *edges* (`pad_l + i·plot_w/(n-1)`), so edge table columns need a
   half-slot overhang beyond the plot; bar charts place categories at slot
   *centers*, so columns span the plot exactly. `chart_column_interval()`
   hides this difference. Don't assume one alignment formula fits all
   compositions.

5. **Layer the relationships: some are unconditional, some conditional.**
   WIDTH sharing is unconditional — every support table renders inside the
   chart's width context, even a segment-breakdown table with no column
   relationship to the x-axis (a full-card-width table under a 55%-wide chart
   reads as disconnected, defect #40). COLUMN alignment is conditional — it
   applies only when the recipe detects the table's header row matches the
   chart's category labels 1:1. Ask "which relationships ALWAYS hold in this
   composition?" separately from "which hold only for specific data shapes?"
   — and test both paths.

6. **Test geometry, not presence.** `assert "chart-support-table" in html`
   cannot catch misalignment. The core test
   (`test_table_columns_center_on_chart_categories`) parses real SVG point
   coordinates and colgroup widths, maps them into a common space, and asserts
   numeric agreement within tolerance. The builders also emit
   `data-align-left/right/width` attributes to make this auditable.

## Checklist for future multi-element layouts

When a recipe composes ≥2 visual elements, ask:

- [ ] Do the elements share a data axis, coordinate system, grid, or visual
      row/column? If yes, a spatial relationship exists and must be contracted.
- [ ] Which element owns the geometry? Does it export that geometry from a
      single source (helper/constants), or is the consumer about to hardcode
      mirrored numbers?
- [ ] Are both elements in the same width/height context (same container, or
      percentages valid against the same base)?
- [ ] Does the alignment apply conditionally when the relationship is detected,
      with a sane fallback when it isn't?
- [ ] Is there at least one **geometric** test (parsed coordinates compared
      numerically), not just presence/class assertions?
- [ ] If the spatial arrangement is a deliberate design decision, is it
      recorded (spec Implementation Decisions / this wiki) so "decision" is
      distinguishable from "never considered"?

## Why presence-based review missed this for 3 rounds

The fidelity rubric checked: correct chart type, correct data, label
collisions, unit formatting, legend placement. All passed while the table
floated unaligned. The rubric now has a **cross-element alignment** section
(see `pdf_fidelity_test_results.md` Round 4 checklist): column alignment, edge
alignment, relative sizing, label proximity. Run it on every composed slide.

## Addendum: a geometric test is only as good as its invariant (T11 / #39)

The Round-4 alignment shipped with a real geometric test — and the columns
were STILL visibly offset by half a slot. The test mapped SVG point positions
and colgroup centers through the same assumed interval and asserted the two
were consistent with each other. Both were computed from the same wrong
assumption, so the test verified *internal consistency*, not the *visual
relationship*.

The correct invariant anchors to something independent of the implementation:
the table and the SVG share a width container, therefore
**absolute column center (% of shared width) must equal cx / svg_width** —
a fact about the rendered output, not about either side's math.

Follow-on lessons:

- Geometric tests must relate two quantities through an invariant that does
  not depend on the code path being tested (ideally: pixel/percentage
  positions in the shared coordinate space).
- When alignment is geometrically impossible with current constants (equal
  columns centered on edge-placed points needed a negative label column),
  fix the CONSTANTS (n-dependent insets), don't approximate the layout.
- Edge-placed points need edge-aware label anchoring: the first data label
  straddles the y-axis if centered on its point.
