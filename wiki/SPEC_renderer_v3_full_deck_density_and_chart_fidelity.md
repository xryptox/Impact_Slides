# Renderer v3 — full-deck density and chart-fidelity specification

Status: **FINAL — user-approved in full; implementation tickets may now be prepared.**

Inventory (no requirement change): renderer-owned DP-7 geometry overrides live in `SPEC_renderer_v3_pdf_design_parity.md` (#246 stub-slack cap + sparse bar occupancy).

Evidence baseline: user-reviewed v11 44-slide PDF↔HTML comparisons from
`origin/gnhf/objective-produce-th-5765a4` at `42f620c`.

## Approval record

- The user approved the complete specification after one-decision-at-a-time review.
- Approval explicitly authorizes slide 21's new neutral `Capital Summary` heading, retains slide 6's authored approximate six-percentage-point claim, adopts the source-precedence and tracked-release-PDF contracts, and makes D316's canonical precedence binding.
- Dependency-ordered implementation tickets may now be prepared from this final specification.

## Accepted decisions

### D1 — Adaptive typography is the renderer default

Density-aware sizing is the global renderer default for supported chart axes,
trend/value labels, support tables, annex tables, and main slide subtitles. It
is no longer limited to handoffs that opt into `typography.mode="auto"`.

- Sparse content scales up within role-specific readability caps instead of
  leaving important content unnecessarily small.
- Dense content fits safely using the renderer's deterministic adaptations.
- Explicit valid handoff sizes remain per-channel overrides.
- Sizing remains deterministic and shared by Chart.js and SVG paths.

### D2 — Automatic sizing is grow-only from current defaults

Adaptive sizing must never make renderer-selected typography smaller than each
surface's current default. Sparse and low-density content may grow; dense
content stays at its current default and resolves pressure through geometry,
wrapping, rotation, tick reduction, abbreviation/ellipsis where permitted, and
selective lower-priority label suppression. Explicit valid handoff sizes remain
intentional author overrides.

### D3 — Synchronize comparable panes and authored sequences

Sibling chart panes and clearly related authored slide sequences share the
largest typography size that safely fits every member. Independent per-chart
sizing remains the fallback for unrelated slides; no deck-wide smallest-common
size may let a dense annex constrain sparse charts.

### D4 — Cross-slide synchronization uses explicit groups

Same-slide comparable sibling panes synchronize automatically. Cross-slide
sequence membership requires an explicit shared author key such as
`chart_config.typography.sync_group`; section and title similarity are
insufficient. Charts without a shared key size independently.

### D5 — Chart plot and body surfaces are transparent

All chart plot/body surfaces are transparent across chart recipes; gray,
gradient, and white chart-body fills are removed. Semantic chrome remains:
blue title bands, axes, zero lines, support-table fills and borders, label
boxes, callouts, and other meaning-bearing marks are not treated as chart
backgrounds.

### D6 — Chart containers are flat and borderless by default

Chart containers lose decorative rounded borders and shadows as well as body
fills. Borders remain only where they define a meaningful pane or grouped
composition; title-band boundaries and other semantic structure remain.

### D7 — Deterministic trend-label collision placement

Line-chart value labels resolve collisions in this order: above, below,
left/right offset, then a leader-line placement; suppression is the last resort.
Labels clear their own marker by at least the marker radius plus 4px and must
also avoid other labels, legends, and callouts. A leader line is required when
displacement makes ownership ambiguous. Chart.js and SVG follow the same
priority and emit equivalent diagnostics.

### D8 — Annex headers use one complete blue band

Every annex-table `<thead>` cell uses the same blue background and white text,
including the top-left stub, period, metric, grouped, and multi-row cells.
Visible separators preserve column/group boundaries. Row-label cells in
`<tbody>` remain white so the data hierarchy stays clear.

### D9 — Explicit chart-pane titles use one blue title band

Every explicitly titled chart pane—single, dual, hero, or multi-panel—uses one
full-width blue band with a large white title at the existing 40px/700 pane-title
scale, wrapping to at most two lines. The overall slide title remains unchanged.
The renderer removes duplicate chart-internal title treatments and never
synthesizes a pane band merely by copying the slide title.

### D10 — Chart/table space is allocated by typography need

Single-chart compositions replace fixed chart/table proportions with a
typography-driven allocator. It first reserves enough space for both surfaces
at current default sizes, then grows the smaller table/support typography by
reclaiming surplus chart area, then grows chart typography, and leaves
whitespace only after neither surface can usefully grow. Semantic plot geometry
is preserved and neither surface's automatic type may fall below its current
default.

### D11 — Automatic growth has role-specific ceilings

Automatic type growth stops at role-specific maxima even when unused space
remains; it does not expand until the surface is visually full. Chart ceilings
reuse the existing contract: 24px x-axis ticks, 28px y-axis ticks, and 32px
ordinary value labels. Table and main-subtitle ceilings are locked below; any additional role needs
its own explicit ceiling rather than inheriting one accidentally.

### D12 — Content-aware table and subtitle growth applies globally

Content-aware growth is a renderer-wide capability wherever the eligible role
appears, not an annex-only recipe. Every semantic table surface—including
ordinary data tables, chart support tables, annex and grouped-annex tables, and
matrix/inset table variants—may grow headers, stubs, row labels, and body values
from its current default up to 24px as geometry permits. This is a fitted
maximum, not a blanket 24px declaration. Main slide subtitles/deks may grow from
the current 22px default up to 26px. The grow-only, deterministic, synchronized,
and explicit-override rules from D1–D4 apply throughout.

### D13 — Eligible explanatory roles grow; display and metadata roles stay fixed

Content-aware growth also applies globally to chart legends, axis titles,
callout/annotation text, support labels, and ordinary card/body text. Slide and
cover titles, 40px chart-pane title bands, KPI/display numbers, footnotes,
sources, disclosures, slide numbers, and brand/legal typography remain fixed.
Each eligible role requires a named current-default floor and role-specific
ceiling; no generic scale factor may silently change unrelated hierarchy.

### D14 — Explanatory-role growth ceilings

Automatic growth caps chart legends and direct series labels at 24px, axis
titles at 24px, callouts/annotations at 24px, support labels at 24px, and
ordinary card/body text at 28px. These are fitted maxima rather than blanket
sizes; each role grows only when its own measured geometry permits it.

### D15 — Every chart series has one visible identity owner

Each declared line-series identity appears exactly once: as a direct endpoint
label when it fits, otherwise in a legend, but never in both. Semantically
distinct annotations remain independent. A single-series label is not omitted
merely because only one series exists; it may be suppressed only when the
author explicitly declares that the pane title owns the same identity. Missing
series identities must be supplied by the handoff; the renderer does not infer
them from nearby tables, prose, or slide titles. Contextual values that are not
plotted series are a separate semantic role and must not be disguised as legend
entries.

### D16 — Theme and authoring own series colors

A valid explicit author color wins. Otherwise, a single or primary trend series
uses dark theme navy and additional simultaneous series use the approved theme
palette for distinction. Markers, direct labels, and legend swatches inherit
the exact resolved series color so every identity treatment remains consistent.

### D17 — Context labels are distinct from plotted-series legends

The handoff may provide structured contextual labels such as
`{label: "G&S", value: "3% YoY"}` for facts adjacent to, but not represented by,
a plotted series. The renderer places these in a reserved exterior chart lane.
Legends remain exclusive to plotted series, so contextual values cannot imply a
false line or bar identity. Context-label typography follows D13–D14 and its
reserved lane participates in fit and collision calculations.

### D18 — Duplicate identity chrome is suppressed semantically

When normalized annotation or context-label text duplicates a plotted-series
identity, the renderer suppresses the duplicate and records a diagnostic.
Coordinate placement alone does not make repeated identity text distinct. An
author may retain genuinely different meaning only by assigning an explicit
semantic role such as `event` or `explanation`; those roles still participate
in collision handling.

### D19 — Identity completeness overrides legend suppression

`show_legend: false` means prefer direct endpoint labels; it does not authorize
removing series identity. If direct labels do not fit, the renderer restores the
legend. Only an explicit single-series declaration such as
`series_identity_owner: "pane_title"` may suppress both direct and legend
identity treatments.

### D20 — Fixed sizing is an explicit escape hatch

Adaptive grow-only sizing is the default when typography mode is omitted, and
legacy `mode: "auto"` remains adaptive. `typography.mode: "fixed"` retains each
current renderer default plus valid explicit author sizes without automatic
growth. Recipes may not disable growth implicitly; intentional fixed sizing
must be present in the handoff.

### D21 — Adaptive behavior is auditable without noisy success warnings

Every adaptive surface records a compact audit entry with slide/layout and
surface role, available geometry, default/selected/maximum sizes, explicit
override or fixed mode, synchronization group, geometry reallocations and fit
adaptations, and any suppressed, deduplicated, or fallback content.
`run_meta.json` always carries these entries and the rendered surface carries
compact `data-*` diagnostics. Stderr warns only for information loss, invalid
configuration, fallback geometry/font metrics, or unresolved overflow—not for
successful growth.

### D22 — One deterministic renderer-side fit engine owns sizing

Every eligible role uses one shared renderer-side fit engine to choose the
largest whole-pixel size between its current default and ceiling from known
content, pane geometry, reservations, and calibrated IBM Plex Sans/Source Sans
3 metrics. HTML, Chart.js, and SVG consume the same resolved plan. Chromium and
runtime JavaScript may paint or position content but may not independently
choose typography. Unreliable dimensions use documented conservative geometry
and emit a diagnostic.

### D23 — Fitted text metrics have a measured accuracy bound

Across every eligible role, estimated bounds must conservatively contain the
rendered bounds with error no greater than 5% or 2px, whichever is larger.
Acceptance measures both vendored fonts across supported sizes and weights at
1920×1080. Unknown fonts use conservative fallback metrics and emit a
diagnostic.

### D24 — Each table uses one common fitted size

A semantic table chooses one common fitted font size for headers, stubs, row
labels, and values rather than maximizing cells independently. Before growth
stops, the fitter may reallocate width from short numeric columns to text-heavy
columns, wrap eligible text at word or punctuation boundaries to at most two
lines, and increase row height within the available table region. It never
splits words, shrinks below current defaults, or introduces mixed per-cell sizes
merely to fill space.

### D25 — Dense tables fail soft without deleting data

If a table still cannot fit at its current default after region reclamation,
column redistribution, and two-line wrapping, it uses an author-provided
`short_label`, then ellipsizes labels only while preserving full accessibility
text. Values are never altered and rows or columns are never dropped. Remaining
overflow fails strict rendering; non-strict rendering paints at the current
default and records unresolved overflow rather than silently deleting data.

### D26 — Synchronization compares equivalent roles only

Table text synchronizes with comparable table text, x ticks with x ticks,
legends with legends, body text with body text, and so on. Adjacent chart and
table roles may resolve to different sizes. A `sync_group` may coordinate
multiple surfaces, but each role computes its own largest common fitting size;
one dense role cannot flatten unrelated hierarchy.

### D27 — Explicit sizes override only their authored member and role

A valid explicit size applies only to that surface and role; it does not force
the same value onto synchronized automatic siblings. Automatic members still
share their largest common safe size. Authors wanting one exact size everywhere
must set it everywhere. An explicit size that does not fit follows normal
strict/non-strict validation, and synchronization never silently reduces it.

### D28 — Malformed adaptive configuration is all-or-nothing

Strict rendering rejects malformed typography configuration before painting the
affected surface. Non-strict rendering discards the entire malformed typography
group, uses default adaptive behavior, and records run-meta plus stderr
diagnostics. Invalid `sync_group` membership makes that surface size
independently. No partially valid fields from a malformed group survive.

### D29 — Context labels use a minimal semantic handoff contract

`chart_config.context_labels` accepts one to four author-ordered objects with
required non-empty `label` and `value` and an optional `short_label`. The
renderer owns placement and styling; the handoff supplies neither inferred
values nor arbitrary pixel coordinates. Malformed entries fail strict
rendering, or are individually dropped with diagnostics in non-strict mode.

### D30 — Series and context labels share one fail-safe exterior lane

Direct series identities and `context_labels` share a renderer-owned right-side
lane. Direct identities remain nearest their endpoints; context labels follow
in author order without overlap. The allocator may reclaim surplus plot width
down to the chart's semantic minimum. If the lane still cannot fit, direct
identities fall back to a legend and context labels wrap to two lines or use
`short_label`. Remaining overflow fails strict rendering; non-strict rendering
moves the complete context block below the plot with a diagnostic and never
drops individual facts.

### D31 — Pane-title bands require explicit title authoring

The blue pane-title band appears only when the handoff supplies an explicit pane
`heading` or `chart_config.title`. Legacy `label` remains available as a
semantic series or tile label but no longer promotes into title chrome, and a
lone `series_names` entry no longer synthesizes a pane title. Existing handoffs
that require the band must migrate to `heading`; untitled charts remain flat and
transparent.

### D32 — Decorative chart-surface controls are retired compatibly

`chart_config.surface` can no longer add white, gray, or gradient plot/body
fills, and legacy settings cannot restore decorative chart-frame backgrounds,
shadows, or rounded borders. `stage: "flat"` remains accepted as a compatibility
no-op. Meaningful grouped-pane containers and blue title bands remain
renderer-owned semantic chrome. Deprecated nontransparent values emit
diagnostics and render transparently rather than failing strict mode.

### D33 — Pane separation is minimal and renderer-owned

Single-chart and chart-plus-support-table compositions have no outer border.
Dual and multi-pane compositions may use only a 1px straight divider or outline
where needed to distinguish independently titled panes. No chart pane uses a
shadow, rounded decorative frame, or body fill. Support-table borders and blue
title-band boundaries remain semantic structure. This policy adds no handoff
styling flag.

### D34 — Line-point values are visible by default

Finite point values on line and combo-line series render by default;
`show_point_labels: false` is the explicit opt-out. Labels use the deterministic
collision placement and adaptive sizing contracts above, with first and last
values receiving highest retention priority and diagnosed suppression only as a
last resort. Point-value labels remain semantically distinct from endpoint
series-identity labels.

### D35 — Label chrome follows semantic role

Point values and endpoint series identities use unboxed text in the resolved
series color. Context labels use unboxed exterior text with each label and value
visually paired. Legends use a series line or swatch plus identity text. Event
or explanation annotations may use bordered callout boxes. A generic annotation
box never substitutes for a legend or series identity.

### D36 — Point-label suppression preserves trend meaning

If every line-point value cannot fit after all placement options, the renderer
retains each series' first and last finite point, then local minima and maxima,
then remaining points selected for even chronological coverage. Ties resolve by
author series order and then category order. First and last finite values are
never suppressed, and every other suppression is reported.

### D37 — Each chart uses one complete identity-placement strategy

A multi-series chart uses endpoint identities only when every series endpoint
label fits. Otherwise it uses one complete legend containing every series and
suppresses all endpoint identity labels. Series identity is never split between
a partial legend and partial endpoint treatment. Context labels remain separate
under D17.

### D38 — Every plotted trend series requires an authored identity

Every line or combo-line series requires a non-empty authored name. Strict
rendering fails before painting an unnamed series. Non-strict rendering paints
the data with a neutral visible fallback such as `Unnamed series 1` and records
a diagnostic. The renderer never invents a business identity from slide titles,
tables, or neighboring prose. A pane-title identity owner still retains the
underlying series name in accessibility metadata.

### D39 — Identity completeness applies across chart families

The authored-identity rule applies to every multi-series chart. Line and
combo-line charts use all endpoint identities when they fit, otherwise one
complete legend. Grouped, stacked, and horizontal bars use a complete legend
unless every series is already identified by non-duplicative in-chart or
exterior labels. Waterfalls remain category-driven unless they genuinely
contain multiple series. Unnamed-series handling follows D38.

### D40 — Pane subtitles live inside the title band

An explicitly titled chart pane renders its subtitle inside the same full-width
blue band directly below the title. Subtitle text is white and semibold and may
grow from 22px to 26px when measured geometry permits, wraps to at most two
lines, and reserves title-band space before chart fitting. A pane subtitle
requires an explicit title: an orphan subtitle fails strict rendering, while
non-strict rendering paints it as ordinary diagnosed support text outside the
band.

### D41 — Adaptive controls live on the nearest semantic surface

Renderer-wide typography authoring uses one consistent `typography` object at
the nearest semantic owner: charts retain `chart_config.typography`, table and
card visuals use their own `typography`, and the main slide subtitle or dek uses
`content.typography`. A typography object may declare `mode`, `sync_group`, and
only the named role-specific size overrides applicable to that surface. There
is no deck-wide override object, arbitrary CSS, or generic scale factor.
Unsupported role fields make the entire group malformed under D28.

### D42 — Structural bands use dark navy; chart color defaults stay role-aware

Chart-pane title/subtitle bands and every annex-table header band use dark theme
navy (`#00175A` in the Amex theme) with white text, not primary blue. Valid
explicit author series colors still take precedence under D16. Without an
author color, a single trend line uses dark navy; bar charts may use primary
blue (`#006FCF` in the Amex theme), and a two-color bar chart uses primary blue
plus dark navy.

### D43 — Default series palette order follows chart family

When valid author colors are absent, a single trend line uses dark navy;
multiple trend lines use dark navy, primary blue, then accessible theme
accents. A single bar series uses primary blue; multiple bar series use primary
blue, dark navy, then accessible theme accents. Markers, direct labels, and
legend swatches inherit the resolved series color. Semantic increase/decrease,
warning, and total colors remain explicit exceptions.

### D44 — Each table's common floor preserves its largest current default

A table surface's common adaptive font-size floor is the largest current default
used by any of its ordinary cells, so unifying table typography never shrinks
existing text. Standard data tables therefore start at 20px, annex and grouped
annex tables at 12px, chart support tables at 14px, and outlined support boxes
at 22px. Each may grow to the 24px D12 ceiling. If the common floor cannot fit,
D25 adaptations and strict/non-strict handling apply; automatic font shrinking
is forbidden.

### D45 — Typography overrides use a closed role-specific vocabulary

Chart typography accepts the existing `x_tick_font_size`,
`y_tick_font_size`, and `datalabel_font_size` fields plus
`legend_font_size`, `axis_title_font_size`, `series_label_font_size`,
`context_label_font_size`, `annotation_font_size`, and
`support_label_font_size`. Table surfaces accept only `table_font_size`, cards
accept only `body_font_size`, and main slide subtitles/deks accept only
`subtitle_font_size`. Pane titles, KPI numbers, metadata, and other fixed roles
remain non-overridable. Unknown or surface-inapplicable fields invalidate the
whole typography group under D28.

### D46 — Pane-title bands are aligned structural headers

A chart-pane title band spans the pane's full usable width and sits flush above
the plot rather than floating as a label or chip. It uses square edges, no
shadow or rounded card treatment, and consistent token-derived internal
padding. Comparable sibling panes align their plot tops by reserving the height
of the tallest sibling title/subtitle band, subject to the two-line limits.

### D47 — Chart/table allocation uses a solved chart floor

The allocator computes the smallest chart region that still paints all marks,
axes, identities, annotations, and current-default typography using permitted
non-lossy adaptations, with an absolute 320×240px plot floor. Only space above
that solved minimum may be reclaimed for an adjacent table or support surface.
Tick rotation or reduction and wrapping may establish the floor, but identity
or value-label suppression may not be used merely to enlarge the table. If the
table still cannot fit or grow, chart shrinking stops and D25 table adaptations
apply.

### D48 — Chart-only compositions do not shrink to manufacture whitespace

A chart-only composition keeps its existing usable chart region, grows eligible
chart typography up to the role ceilings, and uses surplus space for clearer
mark spacing and collision resolution. Any space left after those gains remains
intentional whitespace. The renderer never shrinks a plot merely to imitate a
smaller reference chart when no adjacent semantic surface can use the reclaimed
space.

### D49 — Explicit sizes must remain within each role's adaptive range

Explicit author sizes use the same role-specific floor and ceiling bounds as
automatic sizing; they do not bypass readability ceilings. A value below its
role floor or above its ceiling makes the typography group malformed. Strict
mode rejects the affected surface before painting. Non-strict mode discards the
entire group and applies diagnosed default adaptive behavior under D28.

### D50 — Named display callouts are fixed semantic chrome

Approved named display-callout recipes, such as the FDIC side callout with its
26px/24px lines, retain their fixed typography and are excluded from D14's
ordinary-callout adaptive range. Ordinary annotations, context labels, and
explanatory callouts remain adaptive within their named role ranges. A future
callout may bypass those ranges only through a dedicated semantic contract, not
arbitrary font-size fields, and diagnostics identify the fixed display-callout
role.

### D51 — Shared role floors preserve the largest current painter default

The shared adaptive floors are 14px for x-axis ticks, 14px for y-axis ticks,
14px for ordinary value labels, 16px for legends and direct series identities,
13px for axis titles, 16px for context labels, 13px for ordinary
annotations/callouts, 14px for support labels, 22px for ordinary card/body
text, and 22px for main subtitles/deks. Tables use the D44 surface-specific
floors. Where current Chart.js, SVG, or HTML painters differ, the largest
equivalent current default becomes the shared floor, so adopting one resolved
plan may immediately grow a smaller treatment but never shrink a larger one.
D11–D14 ceilings still apply.

### D52 — Structural numeric labels use automatic-only fitted roles

Semantic chart values that are not ordinary datalabels participate in grow-only
fitting as separate roles: boxed labels fit from 12px to 24px, explicit or
computed stack totals from 14px to 24px, and waterfall bridge/total values from
18px to 24px. They are not controlled by `datalabel_font_size`, and D45 gains
no additional author overrides. These labels are never collision-suppressed,
truncated, or dropped merely to fit; the renderer reserves space, moves boxed
labels outside with connectors, or adjusts structural placement. Remaining
overflow strict-fails, while non-strict paints at the role floor with a
diagnostic. This supersedes waterfall's fixed-18px treatment while preserving
that ordinary `datalabel_font_size` is inapplicable to waterfall values.

### D53 — Point-label placement uses rendered geometry under one policy

Python resolves point-label typography, retention priorities, candidate order,
and fallback rules. SVG applies those candidates from its known coordinates.
Chart.js uses a deterministic post-layout plugin to test the same candidates
against actual marker, label, legend, callout, and chart-area bounds. Runtime
code may choose only among the predeclared candidates; it may not choose font
size, invent text, reorder priorities, or use nondeterministic search.
Equivalent inputs choose the same placement class where geometry permits;
browser acceptance allows ±2px positional tolerance and requires identical
suppression and leader-line decisions. Compact diagnostics record the chosen
candidate for every point label.

### D54 — Delivery includes canonical Amex handoff migration

Implementation includes migrating the canonical 44-slide Amex handoff wherever
this specification requires semantics the renderer may not infer. The migration
adds explicit pane headings/subtitles, complete series identities and identity
ownership, structured `context_labels` such as G&S/T&E values, deliberate
`sync_group` keys for related slides, and valid fixed modes or explicit sizes
only where intentional. It removes obsolete duplicate annotations and
decorative surface settings. The renderer must not recover these meanings from
PDF text, slide titles, or neighboring tables. Acceptance re-renders and
compares all 44 migrated slides.

### D55 — The PDF is a semantic and design reference, not a pixel target

Acceptance requires reference fidelity for content, semantic roles, hierarchy,
series identity, structural chrome, and relative composition. Adaptive
typography and renderer-owned geometry may differ where the locked fitting
rules require it, but every deliberate visual divergence is listed and
justified. Verification uses contract assertions, geometry probes, and
1920×1080 side-by-side human review rather than whole-slide MAE, SSIM, or other
similarity scoring. Visual resemblance cannot excuse incorrect semantics,
accessibility, diagnostics, or Chart.js/SVG parity.

### D56 — Contracts apply across valid handoffs in the sole current theme

Fit, collision, transparency, title-band, table-header, identity, and diagnostic
behavior applies to every valid handoff under the sole current Boardroom/Amex
theme. The canonical Amex deck is the primary acceptance corpus, supplemented
by targeted same-theme fixtures for sparse and dense extremes, long labels,
mixed-sign data, and malformed input. No alternate-theme or custom-font
acceptance path is required.

### D57 — JavaScript-disabled SVG is a first-class acceptance path

Every affected chart contract must pass in both settled Chart.js and
JavaScript-disabled SVG output with the same authored content, identity
strategy, resolved typography plan, adaptations, and information-retention
outcome. Geometry may differ only within explicit tested tolerances; markup need
not match. If SVG cannot represent a capability, strict rendering fails and
non-strict rendering uses a diagnosed semantic fallback rather than a blank or
silently reduced chart. The 44-slide acceptance audit captures both modes at
1920×1080.

### D58 — Visual adaptations preserve accessible meaning

SVG and Chart.js expose equivalent chart title, subtitle, series identities,
context labels, annotations, categories, and values. `short_label`, ellipsis,
visual suppression, and deduplication affect presentation only; full authored
text and underlying data remain accessible. Each semantic fact is announced
once rather than duplicated across title, endpoint-label, and legend
alternatives. Tables retain native header associations, including grouped and
multi-row annex headers. Strict mode rejects inaccessible output; non-strict
mode uses a diagnosed accessible fallback instead of omitting meaning.

### D59 — Prose fitting never deletes or abbreviates authored meaning

Main subtitles/deks and ordinary card/body text grow from their role floor to
the largest fitting whole-pixel size, using natural wrapping and available
region reclamation before growth stops. Prose fitting never invents
abbreviations, uses `short_label`, ellipsizes prose, suppresses sentences, or
drops cards. If complete text cannot fit at the current-default floor, strict
mode fails the affected surface. Non-strict mode paints the complete text at
the floor and records unresolved overflow, preserving all authored and
accessible content.

### D60 — The first adaptive scope excludes geometry-specialized visuals

Heatmaps participate as semantic tables with one common 18–24px fitted size.
Matrix and inset tables use their applicable D44 table floor through 24px.
Icon-grid and ordinary tile/card bodies use the 22–28px card/body role. Diagram
nodes/connectors, timelines, process flows, quote typography, disclosure
controls, and other geometry-specialized visuals retain current typography and
require separate measured contracts before becoming adaptive; they may not opt
into this fitter accidentally.

### D61 — Complete legends occupy a reserved strip

A chart legend occupies a dedicated full-width strip below the pane-title band,
or at the pane top when untitled, and above the plot. It never overlays marks,
annotations, or title chrome; preserves author series order; and uses the
resolved series line or swatch colors. Legend text fits from 16px to 24px,
preferring one row and allowing at most two. The strip may reclaim plot space
only down to D47's semantic floor. If the complete legend still cannot fit,
strict mode fails. Non-strict mode paints the complete legend at 16px in an
expanded strip and diagnoses composition overflow, never truncating, dropping,
or splitting identities. Context labels remain separate under D17 and D30.

### D62 — Adaptive typography does not scale line or marker geometry

Line stroke widths, dash patterns, and point-marker radii retain their current
theme or painter values while labels grow and move around the fixed marks under
D7 and D53. Collision clearance uses the actual rendered marker radius plus
4px. Valid explicit series colors and line styles remain author-controlled, but
no typography mode scales marks. Any future adaptive mark scaling requires a
separate measured contract.

### D63 — Ordinary plot gridlines are prohibited

Horizontal and vertical plot gridlines never render in Chart.js or SVG. Legacy
`show_gridlines: true` and `gridlines: true` settings are deprecated, diagnosed
no-ops. Axes, ticks, semantic zero lines, measure rules, connectors,
support-table borders, heatmap cells, and structural dividers remain. No theme
or recipe may silently restore ordinary plot gridlines.

### D64 — Delivery is one renderer-v3 behavior change

These contracts define the new `impact_slides.renderer_v3` package and schema-v1
handoffs; they do not alter `impact_slides.renderer_v2` handoff behavior in place.
Omitted typography becomes adaptive under D20; chart surfaces become transparent
and borderless; point labels follow D34; explicit pane headings use the new navy
bands; gridline requests become D63-diagnosed no-ops; and series-identity and
accessibility validation becomes mandatory. `typography.mode: "fixed"` remains
the only narrow compatibility control and affects typography only. Canonical v3
fixtures, snapshots, and the Amex handoff migrate together. Renderer v3 contains
no embedded renderer-v2 compatibility path; the separate v2 package remains the
frozen legacy implementation during migration and after v3 release.

### D65 — Transparency preserves semantic data and separation fills

Plot, chart-body, tile, and decorative frame fills are transparent by default.
Data-encoding fills remain for bars, waterfall totals, confidence or range
bands, heatmap cells, boxed labels, semantic highlight regions, and authored
area-series fills. A fill may remain only when it encodes a named data series,
state, threshold, semantic region, or necessary component separation rather
than decoration; it inherits the resolved series or semantic color and remains
represented in legend and accessibility metadata where applicable. Ambiguous
legacy fills are diagnosed and removed rather than guessed. KPI cards and
similar non-chart semantic components may retain a background when needed to
separate the component from the deck canvas; the exact separation rule is
locked separately.

### D66 — Component backgrounds are role-based rather than guessed

Named bounded content components such as KPI, driver, evidence, comparison,
and risk/opportunity cards may use a renderer-owned background when the
boundary communicates grouping or separates the unit from the deck canvas.
The treatment is a solid theme panel token plus a visible 1px theme border;
decorative gradients and shadows are retired. It applies consistently by
component role rather than runtime contrast heuristics or author-supplied CSS.
Chart plots and chart-body containers stay transparent even inside a card, and
all background/text combinations meet accessibility contrast requirements.
Unbounded body content and ordinary chart tiles do not gain a background merely
to fill whitespace.

### D67 — Named cards consistently receive separation chrome

KPI and metric cards, driver cards, evidence and source cards, comparison and
before/after cards, risk/opportunity cards, and recommendation/rationale cards
consistently receive D66's solid panel background and 1px border. Ordinary
chart panes, chart tiles, support tables, and unbounded prose remain
transparent. Nested compositions render only the innermost meaningful card
boundary rather than stacking card-within-card fills. Themes provide accessible
panel, border, and text tokens, and authors cannot toggle this chrome per card.

### D68 — Adaptive plans target the fixed 1920×1080 design stage

Typography and layout resolve only against the renderer's canonical 1920×1080
slide geometry. Browser viewport changes uniformly scale the completed stage;
they do not recalculate font sizes, wrapping, allocations, label placement, or
synchronization. Screenshot and export evidence is captured at 1920×1080.
Chart.js may use settled rendered coordinates under D53, but resizing must
reproduce the same placement class and semantic outcome. Responsive or
alternate-aspect slide reflow is out of scope and requires a separate contract.

### D69 — Synchronization uses a deck-wide two-phase plan

Rendering first measures every valid adaptive surface at canonical geometry,
collects each role's largest safe size, and resolves same-slide sibling groups
and authored `sync_group` members. It then paints Chart.js, SVG, HTML, and
diagnostics from those frozen plans. Slide order cannot affect results, and a
member constrains only equivalent roles it actually contains. Invalid group
membership falls back to independent sizing under D28. Runtime JavaScript may
not revise synchronized font sizes. Strict failures occur before any deck files
are emitted; non-strict rendering records affected-member diagnostics and
continues from frozen fallback plans.

### D70 — Fitting never changes numeric meaning or precision

Adaptive typography may move, wrap, rotate, skip eligible axis ticks, or
suppress lower-priority point labels under the locked rules. It may not change
units, scale, signs, decimal precision, percentages, currency, totals, or
period labels merely to fit. Compact forms such as `$1.2B` may appear only when
produced by the existing semantic formatter or explicitly authored formatting,
never invented by the fitter. Accessibility retains the complete formatted
value. Required structural values that cannot fit at their role floor follow
D25 or D52 rather than being shortened.

### D71 — Ordinary bar values sit beyond the bar end with complete units

Every finite ordinary bar value renders by default. Positive vertical-bar
labels sit above the bar end, negative vertical-bar labels below it, and
horizontal-bar labels beyond the terminal edge in the value direction. Labels
use the complete semantic formatter and preserve percent, currency, sign,
precision, and unit position under D70. The renderer reserves clearance and
repositions labels rather than moving them inside merely because space is
tight. Ordinary labels use unboxed text, with equivalent Chart.js and SVG
outcomes. Stacked-segment labels, stack totals, and `boxed_labels` retain their
separate D52 contracts and are not reclassified.

### D72 — Bar-label collisions use space before suppression

Outside bar-label collisions resolve deterministically by first reserving
headroom through display-domain extension without changing authored values or
tick meaning; then applying small outward and lateral offsets within the
category slot; then staggering neighboring labels with a thin leader line when
ownership becomes ambiguous; then reducing eligible axis-tick density or
reclaiming nonsemantic whitespace. Only after those steps may later ordinary
labels be suppressed in dataset/series then category order, with first and last
categories and local extrema retained first. Suppressed labels remain in
accessible chart data and diagnostics. D52 structural labels are never
suppressed. Chart.js and SVG share priorities and placement classes.

### D73 — Ordinary bar values have one explicit visibility control

Omitted `show_point_labels` shows every finite ordinary bar value by default;
`show_point_labels: false` explicitly hides them. Legacy `point_labels` remains
a compatibility alias, with `show_point_labels` taking precedence when both
are present. The control affects only ordinary values and cannot hide stack
totals, boxed labels, waterfall values, or other D52 structural labels. Units
come only from authored semantic formatting such as `y_axis_unit` and
`y_axis_unit_position`; the renderer never infers percent from magnitude or
slide prose. The canonical Amex handoff explicitly authors `%` for slides
13–14 and every analogous chart.

### D74 — Axis and value units have one semantic source

`y_axis_unit` and `y_axis_unit_position` format y-scaled values and ordinary
vertical-bar, line-point, combo-line, and waterfall values. Horizontal charts
use the same value-axis contract despite x orientation. Per-series units are
allowed only through an explicit `series_units` list aligned with
`series_names`; units are never inferred from titles, subtitles, legends,
magnitudes, or neighboring tables. A missing unit produces a unitless value
without warning. A conflicting or misaligned `series_units` declaration
strict-fails; non-strict discards the complete declaration, uses the chart-level
unit, and diagnoses the fallback. Axis ticks, visible values, accessibility
text, Chart.js, and SVG share one formatter.

### D75 — Every quantitative axis has exactly one unit contract

All datasets sharing one quantitative axis use the same unit and unit position.
`series_units` may repeat that shared unit for validation and formatting, but
conflicting units on one axis are invalid. A dual-axis combo may author a
separate `line_overlay.y_axis_unit` and `y_axis_unit_position` for its right
axis. If `line_overlay.dual_axis: false`, the overlay unit must match the
primary axis. Conflicts strict-fail; non-strict discards the conflicting
declaration, uses the axis-level unit, and diagnoses the fallback. Legends and
series identities never substitute for axis-unit authoring.

### D76 — Decimal precision is explicit rather than reconstructed

`chart_config.value_decimals` from 0 through 4 controls ordinary value labels
and computed totals on the primary axis. `axis_tick_decimals` from 0 through 4
controls tick labels; when omitted, the renderer chooses the minimum precision
needed to distinguish the authored or generated tick step. A dual-axis overlay
may define its own `value_decimals` and `axis_tick_decimals`. Explicit textual
labels such as `stack_total_labels` remain byte-for-byte authored. The renderer
never infers intended trailing zeros from magnitude, prose, or JSON lexical
form. Malformed precision configuration strict-fails; non-strict discards it
and diagnoses the deterministic fallback. The Amex migration uses
`value_decimals: 0` for slide 13 and `value_decimals: 1` for slide 14, preserving
`7%`, `1.3%`, and `2.0%` as shown in the PDF.

### D77 — Numeric display rounding is renderer-owned and decimal-safe

Declared precision converts each finite value through its canonical decimal
string rather than binary-float formatting, then rounds presentation values
half away from zero. Required trailing zeros remain, with locale-invariant `,`
thousands separators and `.` decimals. Chart.js receives the same preformatted
strings used by SVG; browser plugins never round independently. Axis domains,
stacking, totals, and collision geometry continue using full numeric values,
with rounding limited to displayed and accessible text. Explicit textual labels
remain untouched.

### D78 — Zero, missing, and invalid values are distinct

A finite zero is real data and renders its ordinary value label by default. A
vertical zero label sits just above the zero baseline; a horizontal zero label
sits just beyond it in the positive direction. `null` or an explicitly missing
value creates a gap with no mark or value label while remaining represented as
missing in accessible data. `NaN`, infinity, booleans, and malformed numeric
strings are invalid: strict mode rejects the affected chart; non-strict mode
omits only the invalid point, diagnoses it, and preserves the remaining series.
Collision and suppression rules apply to zero labels like other ordinary
labels.

### D79 — Stacked-chart labels remain separate from ordinary bar labels

D73's default-visible ordinary values apply only to non-stacked bars.
`show_segment_labels: true` explicitly shows every finite stacked-segment value
and defaults to false. `show_stack_totals: true` shows one total per stack;
existing `stack_totals` remains a compatibility alias. Explicit
`stack_total_labels` implies visible totals and remains authoritative over
computed totals. Segment values use their series unit and precision; totals use
the shared stack-axis unit and precision unless explicitly authored. Segment
labels remain inside when readable and otherwise move outside with a connector;
they are never silently dropped. Segment and total controls are independent and
may render together.

### D80 — Ordinary bar-value labels use high-contrast semantic text

Non-stacked bar-value labels use dark navy independently of bar fill, the
adaptive ordinary-value size from 14px through 32px at weight 700, and unboxed
text. They retain at least 4px clearance from the bar end before collision
offsets. When displacement makes ownership ambiguous, only the leader line uses
the resolved series color. Stacked labels retain their separate inside/outside
color rules.

### D81 — Explicit axis bounds remain authoritative

Explicit `y_axis_min`, `y_axis_max`, and authored tick lists remain unchanged.
The renderer first reserves an exterior top, bottom, or right value-label gutter
outside the plot. D72's display-domain extension may add unlabeled visual
headroom only for automatically generated domains and never rewrites explicit
bounds or ticks. Labels outside an explicit domain remain visible in the
reserved gutter rather than being clipped. Plot fitting accounts for that
gutter before choosing typography or suppressing labels.

### D82 — Exterior value-label gutters are measured and pane-aligned

D81's gutter is measured from the tallest or widest fitted value label plus its
required clearance and leader-line allowance rather than a fixed pixel guess,
and reserves only the edges used by that chart. D22 and D47 include it in
available-plot calculations before font selection. Comparable sibling panes
use the largest required gutter so plot baselines and tops align. Unrelated
charts remain independent, and cross-slide groups share the gutter only when
the authored group synchronizes the applicable value-label role. Diagnostics
record every resolved exterior gutter.

### D83 — Explicit axis bounds may not hide plotted data

Every finite plotted value, stacked extent, computed total that influences the
domain, and semantic zero when required must fall within authored axis bounds.
D81–D82 exterior gutters provide text space only and do not legitimize clipping
bars, lines, markers, or totals. Excluding, reversed, non-finite, or
tick-inconsistent axis declarations are malformed. Strict mode rejects the
affected chart before painting. Non-strict mode discards the complete authored
bounds and ticks group, computes a safe domain from full data, preserves units
and precision, and diagnoses the fallback. Dual-axis combo charts validate each
axis independently.

### D84 — Semantic zero lines appear only when analytically meaningful

One emphasized zero line renders when the resolved quantitative domain spans
negative and positive values, or when an explicit semantic contract such as
waterfall bridging requires zero. For an all-positive domain beginning at zero,
the ordinary axis baseline owns zero and no duplicate interior line appears.
For an all-negative domain ending at zero, the top axis boundary owns zero.
The line is theme-token-derived, 1px, exposed as structural context, equivalent
in Chart.js and SVG, and independent of D63's prohibited plot gridlines.

### D85 — Whole-axis visibility remains explicitly authored

Ordinary value labels do not automatically remove an axis. `show_x_axis: false`
and `show_y_axis: false` are the only controls that hide the corresponding
visual axis and ticks. Adaptive fitting may reduce or skip eligible ticks under
the locked rules but may not silently remove the complete axis. Hidden axes
remain represented in accessible chart data and diagnostics. Semantic zero
lines and required category labels remain independently governed. The Amex
migration sets `show_y_axis: false` on slides 13–14 to match the PDF while their
complete percentage value labels carry the quantitative reading.

### D86 — Category identities cannot disappear as a fitting shortcut

Every authored category remains visibly identified by default. Adaptive fitting
may wrap, rotate, use an authored `short_label`, or evenly skip intermediate
axis ticks while retaining first and last ticks. When ticks are skipped, every
category must remain identifiable through its visible value label, support
table, or another explicit in-chart treatment. If no alternate visible owner
exists, category ticks may not be skipped and unresolved fit follows the
strict/non-strict overflow contract. `show_x_axis: false` may hide category
ticks only when another explicit visible owner identifies every category.
Accessibility retains every full category label exactly once.

### D87 — Each quantitative axis owns one negative-number style

`chart_config.negative_style` accepts `"minus"` or `"parentheses"` and defaults
to `"minus"`. The selected style applies consistently to generated ticks,
ordinary values, segment labels, computed totals, and waterfall values on that
axis. A dual-axis overlay may declare its own style. Values rounding to zero
render as unsigned zero, never `-0` or `(0)`. Explicit textual labels remain
untouched, while accessibility always announces a negative value as negative.
Invalid declarations strict-fail; non-strict discards the declaration, uses
`"minus"`, and diagnoses the fallback.

### D88 — Unit formatting never rescales numeric data implicitly

`y_axis_unit`, `series_units`, and related unit fields add presentation
formatting but never multiply, divide, or reinterpret values. A value of `1.3`
with unit `%` renders as `1.3%`; authors provide `0.013` only when the plotted
scale genuinely uses fractional units. Magnitude suffixes such as `$B` and `$M`
do not rescale values. When display scaling is required, the handoff explicitly
declares a finite nonzero `value_scale`; the renderer applies it consistently
to displayed ticks and labels while plotting and computing totals from source
values. Axis titles and accessibility disclose the scaling. Conflicting or
malformed scaling strict-fails; non-strict discards scaling, uses source values,
and diagnoses it.

### D89 — `value_scale` is an axis-scoped multiplicative display transform

`value_scale` defaults to 1 and computes `display_value = source_value ×
value_scale` with decimal-safe arithmetic before D77 rounding. Authored data,
axis bounds, and explicit ticks remain in source-value space; generated ticks
come from the source domain and are scaled only for display. Totals are computed
from full source values and scaled once rather than summing rounded labels. Every
series sharing an axis uses the same scale, while a genuine dual axis may define
its own. Per-series scaling on one shared axis is invalid.

### D90 — Display scaling is disclosed once without duplicating units

A `value_scale` other than 1 requires a non-empty explicit `scale_label`, such
as `$ in billions` or `in millions`. The label renders once per axis, preferring
the pane subtitle when it already contains the exact normalized disclosure and
otherwise using a dedicated adaptive axis-scale caption. Ticks and values retain
useful currency or percent signs, while a redundant magnitude suffix is omitted
only when the scale caption already declares the same magnitude. Accessibility
associates the scale label with every value on that axis. Missing or
contradictory disclosure strict-fails; non-strict ignores `value_scale`, uses
source values, and diagnoses the fallback.

### D91 — Plotted values use undecorated numeric input

Quantitative chart data accepts finite JSON numbers or canonical
locale-invariant decimal strings such as `"1.3"`, `"-73"`, or `"1.2e6"`.
Booleans and decorated plotted values such as `"7%"`, `"$1,223"`, and
`"1,000"` are invalid; units and scaling belong in explicit axis or series
contracts. The renderer preserves a normalized decimal representation for
formatting, totals, and D77 rounding and converts separately for plotting
geometry. Strict mode rejects the affected chart; non-strict handles the value
under D78. Formatted strings remain valid in tables, cards, callouts, and
explicit textual labels. The canonical Amex migration converts decorated
plotted values to undecorated data plus explicit units and precision.

### D92 — Missing chart values preserve structure and never become zero

For line and combo-line charts, `null` breaks the path and is never implicitly
interpolated. Grouped and horizontal bars preserve the category slot but paint
no bar or value label. Stacked bars preserve the series/category position and
do not treat a missing segment as zero. A computed stack total is withheld when
any contributing segment is missing, although an explicit authored
`stack_total_labels` entry may render as an independently supplied fact. Missing
values never shift later categories or series into another position, and
accessibility identifies the corresponding value as missing. Future
interpolation requires a separate explicit semantic contract.

### D93 — Chart matrices are rectangular and positionally exact

Each series supplies exactly one position for every authored category, with
`null` as the only valid missing placeholder. Ragged rows, surplus values,
missing trailing positions, and duplicate category identities are malformed.
`series_names`, `series_units`, and other per-series arrays must match the
plotted-series count exactly. Strict mode rejects the chart before painting.
Non-strict mode preserves positions by padding missing entries with `null`,
ignores surplus positions, assigns neutral unique labels to duplicate
categories, and diagnoses every repair. It never shifts values, infers a
category, or truncates every series to the shortest row.

### D94 — Duplicate display labels require stable authored category identities

Visible category labels may repeat when semantically valid, such as `Q1` across
different years. Repeated labels require a parallel unique `category_ids` array
matching category count exactly. IDs are non-empty deck-local strings used only
for structural association, diagnostics, accessibility, and deterministic label
placement; they are not rendered. Without `category_ids`, normalized visible
labels must be unique. `short_label` changes presentation only and never
identity. Malformed or duplicate IDs strict-fail; non-strict generates neutral
positional IDs, preserves every visible label and value position, and diagnoses
the repair.

### D95 — Cross-chart series continuity uses stable authored identities

Visible `series_names` are non-empty and normalized-unique within each chart.
Optional `series_ids` provide stable non-rendered identities and match the
series count exactly. They are required when display names repeat or the same
semantic series must retain color across panes or slides. Within one deck, one
`series_id` resolves to one theme-palette color unless one consistent explicit
author color overrides it; conflicting explicit colors are malformed. The
renderer never infers continuity from similar names, positions, or neighboring
prose. Invalid declarations strict-fail; non-strict generates positional IDs,
sizes and colors the chart independently, and diagnoses the repair.

### D96 — Semantic duplicate detection uses conservative normalization

Duplicate identities use Unicode NFKC normalization, trimmed and collapsed
whitespace, case folding, equivalent typographic and ASCII quotes/dashes, and
removal only of non-semantic surrounding punctuation such as a trailing colon.
Numbers, units, signs, percentages, and semantic words remain significant. The
renderer never stems words, expands abbreviations, or uses fuzzy matching.
Normalization affects comparison only; rendered and accessible authored text
remains unchanged. Suppression diagnostics identify both retained and
suppressed authored strings.

### D97 — Duplicate semantic chrome has a deterministic owner

When D96 finds equivalent visible text, retention priority is: an explicit
`series_identity_owner: "pane_title"`; the complete endpoint-label or legend
strategy selected by D15/D37; a structured context label carrying an
independent value; an explicit event or explanation annotation; then generic or
legacy labels. Within one role, the first author-ordered occurrence wins.
Suppression removes only duplicate chrome, never plotted values, categories,
units, or accessibility facts. A context label with the same label but a
distinct authored value is not a duplicate. Diagnostics record both roles and
both authored strings.

### D98 — Author colors must satisfy semantic contrast

A valid explicit author color meets WCAG contrast against its resolved
background: 4.5:1 for ordinary text, 3:1 for large text, and at least 3:1 for
meaningful graphics including lines, markers, bars, leader lines, and borders.
Series remain distinguishable through identities, dash or marker treatment, or
another non-color cue rather than hue alone. Checks occur after theme and
transparency resolution. Strict mode rejects a failing explicit color;
non-strict replaces it with the nearest role-appropriate accessible theme color
and diagnoses both colors. Decorative marks carrying no meaning are exempt.

### D99 — Multi-series trends use deterministic non-color identities

A single or primary trend uses a solid line with the current circular marker.
Additional simultaneous series receive renderer-owned accessible line and marker
pairs in this order: dashed/square, dotted/triangle, then dash-dot/diamond. The
same `series_id` retains its resolved line and marker style across the deck just
as it retains color under D95. Valid explicit author styles take precedence,
but all series must remain distinguishable; partial or conflicting declarations
are malformed. Legends show the actual line/marker pair and direct labels remain
associated with it. Styling never invents meanings such as forecast or reported;
those require authored identities.

### D100 — One trend pane supports at most four simultaneous series

A line or combo-line pane supports one through four simultaneous trend series.
More than four is malformed and style pairs never repeat within one pane.
Authors split denser comparisons across panes or use a semantic table. Strict
mode rejects the affected chart before painting. Non-strict replaces it with a
complete semantic table preserving title, subtitle, categories, series, values,
units, and accessibility and records a diagnostic. It never paints only the
first four or hides excess series.

### D101 — Bar series use structure before decorative patterns

Grouped bars use stable author series order and a complete ordered legend as
their non-color identity, preserving the same left-to-right order in every
category. Stacked bars use stable bottom-to-top order plus a complete ordered
legend. If stack order changes by category, or a segment cannot be traced
through that order, every segment requires a visible direct identity or the
chart is malformed. Hatch patterns are not added by default because they reduce
presentation-scale legibility. A chart that remains ambiguous strict-fails;
non-strict uses D100's complete semantic-table fallback. Accessibility exposes
series identity on every bar or segment.

### D102 — Complete semantic-table fallback has a deterministic location

A D100/D101 non-strict fallback replaces only the malformed chart pane and
occupies that pane's allocated region beneath its existing title/subtitle band.
It uses D24–D25 adaptive table fitting and the D8/D42 navy header contract,
preserves author category and series order with categories as rows and series
as columns, and retains complete units, precision, missing-value state, scale
disclosure, and accessibility. Neighboring panes, cards, support tables, and
slide chrome remain unchanged. Output carries
`data-chart-fallback="semantic-table"` plus run-meta and stderr diagnostics.
Strict mode still emits no deck files under D69.

### D103 — Missing values have one visible table representation

Every semantic table and chart-to-table fallback renders `null` as an em dash
(`—`), never blank, zero, `N/A`, or an empty cell. Accessibility announces
`Missing`, not `dash`, while a true zero retains its formatted numeric value.
Authors cannot use arbitrary missing-value tokens inside quantitative data.
Explicit textual tables may still contain authored `N/A` when it is actual
source content rather than a numeric placeholder. Chart.js and SVG accessible
data, support and annex tables, and semantic fallbacks preserve the same
distinction.

### D104 — Semantic tables align cells by data role

Stub, row-label, and prose columns align left; quantitative values align right.
Values with one declared precision align on the decimal separator, while
whole-number columns align on their final digit. Column headers follow their
body column's alignment and grouped headers remain centered across their span.
Missing-value em dashes occupy the same aligned value position. Currency
symbols, signs, parentheses, and magnitude suffixes remain part of the aligned
formatted value. Authors cannot override alignment cell by cell; semantic
column role owns it.

### D105 — Quantitative text uses tabular lining numerals

Generated quantitative text uses tabular lining figures in table values, chart
ticks, point and bar labels, totals, callouts, and legends containing generated
values. Prose, categories, titles, and authored textual labels retain normal
proportional figures. D104 decimal alignment uses the formatted separator rather
than inserted spaces. Both vendored fonts expose equivalent tabular-numeral
faces for HTML, SVG, and Chart.js. A font without calibrated tabular figures
strict-fails; non-strict uses the diagnosed conservative fallback font. D23
metric calibration includes tabular digits, signs, separators, parentheses,
and unit suffixes.

### D106 — Each chart pane emits one shared accessible data table

Every chart pane emits one renderer-owned semantic data table containing its
title, subtitle, scale disclosure, categories, series identities, formatted
values, units, missing states, context labels, and annotations. Chart.js canvas
and SVG marks reference that same representation and do not announce duplicate
facts independently. Visual shortening, suppression, fallback legends, and
collision placement never change its complete content. It is visually hidden
for ordinary charts and becomes the visible pane replacement for D100–D102
semantic-table fallback. JavaScript-disabled output exposes the same table
without duplicating SVG announcements. Missing or inconsistent structure
strict-fails; non-strict uses the visible semantic-table fallback.

### D107 — Charts never depend on interaction for meaning

Every identity, value, unit, annotation, and context fact is available through
visible output or D106's semantic table without hover, focus, or pointer input.
Chart.js tooltips may repeat facts for convenience but never contain exclusive
information. Individual marks do not enter the tab order; the chart pane and
semantic table provide the accessible reading structure. Decorative hover
animation cannot move labels, change placement classes, or alter the frozen
plan. Print, screenshot, SVG, and JavaScript-disabled output retain the complete
semantic result. Future genuinely interactive charts require a separate
keyboard and state contract.

### D108 — Production charts are motionless and capture-stable

All Chart.js entrance, resize, hover, and data-transition animations are
disabled, and the frozen D69 plan paints immediately. SVG and HTML chart chrome
remain motionless, so reduced-motion preference is inherently honored. Legacy
animation settings are diagnosed no-ops. Screenshot readiness requires nonzero
settled geometry and completed label plugins rather than elapsed animation time.

### D109 — Paint readiness includes every fidelity-critical stage

A slide becomes capture-ready only after vendored fonts load, its frozen plan is
attached, every visible Chart.js chart has nonzero chart-area and dataset
geometry, collision/leader-line/alignment/accessibility plugins complete, and
SVG/HTML adaptive layout is present. One subsequent animation frame must confirm
unchanged geometry. One deterministic slide-level state exposes readiness.
Timeout or plugin failure strict-fails capture; non-strict capture records a
diagnostic and visibly marks the affected pane unresolved rather than silently
capturing partial output.

### D110 — Diagnostics use stable machine-readable events

Every adaptation, fallback, suppression, repair, and unresolved condition emits
a structured event with stable `code` and `severity`, slide number, layout,
semantic surface ID and role, relevant authored input, renderer action and
resulting state, and affected category or series IDs where applicable.
`run_meta.json` stores complete events; compact DOM `data-*` attributes store
codes/counts and resolved-plan summaries rather than duplicate payloads.
Identical events deduplicate per surface, stderr follows D21's warning policy,
and event codes are tested compatibility contracts.

### D111 — Diagnostic severities have fixed operational meaning

Severity is limited to `info`, `warning`, and `error`. `info` covers successful
adaptive growth, synchronization, or non-lossy repositioning, keeps the run
clean, and stays off stderr. `warning` covers diagnosed fallback, author
correction, visible suppression retained accessibly, fallback metrics/geometry,
or non-strict repair; rendering completes but `ok` becomes false. `error`
covers a violation preventing faithful painting: strict mode emits no deck,
while non-strict requires an explicit safe fallback and remains `ok: false`.
No ad hoc severity names are permitted. Run metadata records counts and sets
`ok: true` only when no warnings or errors exist.

### D112 — Clean, degraded, and failed runs are operationally distinct

A `clean` run has only info events, reports `ok: true`, emits the deck, and the
CLI exits 0. A `degraded` non-strict run used a warning/error fallback, reports
`ok: false`, emits the diagnosed deck, and exits 2. A `failed` strict or
non-strict run reports `ok: false` in its typed exception payload, emits no deck
files, raises the applicable typed renderer error through the API, and exits 1
through the CLI. Non-strict is recovery policy, not a guarantee of publication;
exit 2 is reserved for a successfully published degraded deck. Output replacement
is transactional, so any failed run leaves existing files untouched. Automation
inspects status rather than treating HTML existence as success.

### D113 — Equivalent inputs produce byte-reproducible deck output

Random canvas, disclosure-tab, and related DOM IDs are replaced with deck-local
IDs derived from stable slide and semantic-surface identities. Equivalent
handoff, theme, renderer version, and options produce byte-identical HTML, CSS,
JavaScript payloads, and `run_meta.json`; structured diagnostics and plan entries
use stable ordering. IDs remain unique when visible titles repeat. Timestamps,
absolute machine paths, and random values stay out of emitted artifacts. A
meaningful input change may alter affected IDs, but unrelated surfaces retain
theirs.

### D114 — Stable artifact IDs use semantic surface identities

`slide_number` is unique within the deck. Fixed recipe slots derive stable IDs
from slide number plus a canonical role such as `primary`, `secondary`, or
`support`. Repeatable or reorderable panes, tiles, tables, and cards require a
unique authored `surface_id`. Cross-slide `sync_group`, diagnostics,
accessibility references, DOM IDs, and frozen plans use these identities rather
than titles, array positions, or randomness. Reordering or inserting one
surface leaves unrelated IDs unchanged. Missing or duplicate required IDs
strict-fail; non-strict generates deterministic positional IDs, diagnoses their
instability, and disables cross-slide synchronization for those surfaces.

### D115 — Authored semantic IDs use a closed stable format

`surface_id`, `series_id`, `category_id`, and `sync_group` values are lowercase
ASCII slugs matching `[a-z][a-z0-9_-]{0,63}`. They are opaque, never render as
user-facing text, remain stable across wording/order/style changes, and are not
derived from mutable prose. Surface IDs are deck-unique; series and category IDs
are unique within their semantic collection; sync-group names are deck-unique
keys. Malformed IDs strict-fail, while non-strict uses the already defined
deterministic positional fallback and diagnostics. The Amex migration assigns
deliberate semantic slugs rather than hashes.

### D116 — Strict rendering remains the default

`render_deck(..., strict=True)` remains the API default, and the CLI renders
strictly unless the author explicitly selects non-strict mode. Strict validation
and deck-wide planning finish before output replacement begins. A strict
violation never silently retries non-strict. Non-strict rendering is an explicit
recovery choice and reports `degraded` under D112 whenever it repairs or falls
back. Tests and simulations state which mode they exercised.

### D117 — The handoff contract has an explicit schema version

This delivery establishes `meta.handoff_schema_version: 1`. Strict rendering
requires exactly version 1. The version validates data shape and does not select
a legacy renderer or alternate visual behavior. Missing version in non-strict
mode is diagnosed as unversioned legacy input and follows normal safe-fallback
rules without invented business semantics. Malformed or unsupported versions
fail in both modes because their meaning is unknown. Emitted metadata records
the accepted version. Canonical fixtures and the 44-slide Amex handoff migrate
to version 1 in this delivery.

### D118 — Schema v1 uses closed renderer-owned objects

Every renderer-owned object—slide, content, visual, pane/tile, `chart_config`,
typography, series/category metadata, and table/card contracts—accepts only
documented fields. Unknown fields strict-fail with their full path and nearest
valid names. Non-strict drops only the unknown field, preserves valid siblings,
emits a warning, and becomes degraded. Existing legitimate fields are formally
represented during migration rather than retained through `extra="allow"`.
Version 1 has no generic extension bag or `x-*` escape hatch. Explicitly opaque
source/evidence payloads remain exempt and are preserved unchanged.

### D119 — Legacy handoffs migrate offline rather than during rendering

Delivery includes one deterministic migration tool that reads an unversioned
handoff and writes a separate schema-v1 candidate. It converts only mechanically
provable structures, decorated chart numbers, aliases, and documented legacy
fields; it never invents headings, IDs, units, series identities, ownership, or
missing business facts. It emits machine-readable unresolved decisions with
exact paths and refuses to mark output as version 1 until all required decisions
are resolved. `--check` writes nothing and source files are never modified. The
production renderer gains no hidden legacy path beyond D117's explicit
non-strict handling.

### D120 — Validation reports all detectable authoring errors in one pass

Schema-v1 validation collects every independently detectable structural and
semantic error before returning. Each finding has a stable code, exact JSON
path, rejected value or type, and expected contract; nearest valid field names
appear only for an unambiguous match. Findings order deterministically by slide,
surface, path, then code, and root errors do not generate cascading duplicates.
Strict mode fails once with the complete report before planning or writing.
Non-strict applies only defined safe repairs and revalidates the repaired model
before planning.

### D121 — Schema v1 is published as a machine-readable contract

Delivery includes one generated JSON Schema artifact derived from the same typed
models used by renderer validation. It describes closed objects, required
fields, enums, numeric bounds, ID formats, conditional chart-family rules,
field descriptions, and minimal valid examples. The offline migrator consumes
it and handoff-authoring agents may inspect it. CI checks the committed artifact
for model drift; no second manually maintained schema exists.

### D122 — Painting consumes only the validated canonical model

Validation produces one canonical typed deck model. Strict painting consumes
that model only and never the original raw handoff dictionaries. Non-strict
safe repairs produce and revalidate a canonical model before painting. Unknown,
malformed, or rejected fields cannot leak into recipes through raw access;
D118's explicitly opaque source/evidence payloads remain available unchanged.
The frozen plan, accessible tables, diagnostics, Chart.js, and SVG all derive
from this same model. No recipe independently reinterprets or repairs raw input.

### D123 — Non-strict repairs are explicitly allowlisted and non-semantic

Non-strict rendering applies only repairs individually authorized by this
specification, including unknown-field removal, deterministic fallback IDs,
positional `null` padding, invalid-point omission, safe-domain replacement,
accessible theme-color replacement, and named semantic fallbacks. A closed
repair registry maps each stable diagnostic code to one deterministic
canonical-model transformation. Repairs never infer or fabricate business text,
units, precision, scale, identity, ownership, category meaning, totals, or
missing values. Violations without an authorized repair fail rather than invite
a guess. Events record pre-repair input and canonical result, and every repair
has mutation plus strict/non-strict parity tests.

### D124 — Published handoff schema versions are immutable

After schema v1 ships, its fields, meanings, requiredness, bounds, and repair
semantics are frozen. A handoff-contract change creates the next integer schema
version; documentation-only clarification does not. Renderers explicitly
declare supported versions and never reinterpret an old version with newer
semantics. Cross-version conversion remains an offline deterministic migration,
never an implicit render step. Visual changes that do not alter handoff meaning
advance the renderer version instead. Emitted metadata records both versions.

### D125 — The breaking renderer contract ships as `renderer_v3` version 3.0.0

This contract is implemented in the new `impact_slides.renderer_v3` package with
public interfaces `from impact_slides.renderer_v3 import render_deck` and
`python -m impact_slides.renderer_v3`. The current
`impact_slides.renderer_v2` package remains the frozen legacy renderer and is not
renamed, wrapped around v3, or copied wholesale into v3. Shared immutable assets
may be factored into a neutral package only when both versions genuinely consume
them; v3 otherwise owns its canonical model, planner, diagnostics, painters,
shell, and artifacts. One v3 version source feeds `__version__`, run metadata,
diagnostics, and generated artifacts. Patch releases fix defects without changing
contracts, minor releases add backward-compatible capability, and major releases
may change defaults, visual contracts, or supported handoff schemas. Handoff
schema versions remain independently governed by D117/D124.

### D126 — The migrated 44-slide deck is a release-blocking corpus

Renderer 3.0.0 ships only when the canonical Amex deck validates and renders in
strict mode with `clean` status across all 44 slides in settled Chart.js and
JavaScript-disabled SVG modes. Every slide reaches D109 readiness with no
clipped, overlapping, missing, duplicated, or inaccessible semantic content.
Both modes preserve identical facts, units, precision, identities, adaptations,
and diagnostics. Contract and geometry probes plus complete 1920×1080
side-by-side human PDF review pass, every deliberate D55 divergence is recorded,
and reproducible evidence identifies the exact handoff, renderer, and schema
versions.

### D127 — Renderer 3.0.0 retains only the current theme

Renderer 3.0.0 supports only the existing Boardroom/Amex theme. It does not add
a `slate` theme, alternate named themes, custom fonts, duplicate recipes, or a
cross-theme release corpus. D56's acceptance scope is correspondingly limited
to valid handoffs under this sole current theme.

### D128 — Schema v1 removes theme customization

Schema v1 removes arbitrary `presentation.theme` token dictionaries and needs no
theme selector while only one theme exists. Emitted metadata records
`theme_id: "boardroom_amex"`. Existing `render_deck(theme=...)` calls accept
only `None`; a supplied override raises a typed configuration error. The offline
migrator removes a theme dictionary only after confirming that it equals the
approved current-theme tokens; differing overrides become unresolved author
decisions. Theme colors and fonts have one vendored source of truth.

### D129 — The sole theme uses one canonical token namespace

Semantic `--color-*`, `--font-*`, spacing, border, and typography tokens become
the sole public token layer. Production CSS drops duplicate legacy aliases such
as `--navy`, `--blue`, and `--panel` after consumers migrate. One canonical
Python theme manifest supplies generated CSS declarations and resolved Chart.js
and SVG colors; CI checks generated artifacts for drift. Production painters
contain no raw theme hex literals except explicitly documented semantic
exceptions.

### D130 — Author colors reference the approved palette rather than raw CSS

Schema-v1 chart color authoring uses approved semantic palette keys such as
`navy`, `primary_blue`, `sky_blue`, `success`, `neutral`, and `warning` from the
sole theme manifest rather than raw hex, RGB/HSL, CSS variables, gradients, or
other CSS values. Equivalent `*_color_key` fields govern overlays and other
authored semantic marks. Valid author choices retain D16 precedence and D98
contrast validation. The migrator converts exact approved color matches to keys
and flags all others for human resolution. Diagnostics record both the semantic
key and resolved canonical color.

### D131 — Palette keys are role-qualified for contrast

Series-identity keys are `navy`, `primary_blue`, `success`, `neutral`, and
`warning`; each passes 4.5:1 on the transparent white chart body because direct
labels inherit series color. `neutral` resolves to the existing accessible
muted ink `#63666A`. Light colors such as `sky_blue` are restricted to
non-text semantic fills on approved dark or sufficiently outlined surfaces and
cannot identify a series. White is restricted to text or marks on approved dark
surfaces. The Amex migration replaces legacy `#8A93A6` series uses with
`neutral`. Every key declares allowed roles/backgrounds; other use is malformed
under D98, and default series cycles use only identity-safe keys.

### D132 — Bar fills and identities share one resolved series key

Every bar series resolves one identity-safe palette key. Bars, legend swatches,
connectors, and direct identity treatments derive from that same key. Ordinary
numeric bar-value text remains dark navy under D80 rather than inheriting the
fill. A stacked label inside a segment uses white only when contrast passes;
otherwise it moves outside and uses dark navy with a series-colored connector.
No separate author fields split fill from identity color. Semantic increase,
decrease, warning, or total roles override a series key only where those roles
carry actual chart-family meaning, such as waterfall.

### D133 — Authored line styles use closed semantic keys

Schema v1 line authoring uses `line_style_key` (`solid`, `dashed`, `dotted`, or
`dash_dot`) together with `marker_key` (`circle`, `square`, `triangle`, or
`diamond`). Raw dash arrays, callbacks, SVG paths, CSS, and arbitrary marker
geometry are invalid. Overriding D99 requires a complete pair; one `series_id`
uses the same explicit pair everywhere under D95, and simultaneous series must
remain distinguishable under D98. Malformed or conflicting styles strict-fail;
non-strict discards the complete pair and applies D99's deterministic assignment
with diagnostics.

### D134 — Every chart category and series has a stable authored ID

Schema v1 requires one `category_id` for every chart category and one
`series_id` for every series, including unique categories and single-series
charts. IDs remain stable across wording, formatting, color, and order changes.
Strict mode rejects missing, malformed, duplicate, or count-mismatched IDs.
Non-strict may generate diagnosed positional IDs but disables cross-pane or
cross-slide synchronization and continuity for them. The canonical Amex
migration uses reviewed semantic IDs rather than generated positional IDs.

### D135 — Schema v1 uses one canonical chart-data structure

Axis-based charts use a required ordered `chart_data` object containing typed
`categories` and `series`. Every category owns `category_id`, `label`, and an
optional `short_label`; every series owns `series_id`, `name`, exact
position-aligned `values`, and optional `color_key`, `line_style_key`, and
`marker_key`. Style and identity no longer live in parallel `series_names`,
`series_colors`, or `series_styles` arrays. `chart_config` controls behavior and
geometry only, not data or identity. Renderer 3.0.0 performs no header-row or
list-of-lists inference. Semantic tables keep their separate model. The offline
migrator converts only unambiguous legacy forms and flags the rest.

### D136 — Combo charts use typed series on one shared category model

A `combo_chart` uses D135's `chart_data.categories` and `chart_data.series`.
Each series declares `mark_type` as `bar` or `line` and may declare `axis_key`
as `primary` or `secondary`, defaulting to primary; secondary requires a
separately valid secondary axis. The chart requires at least one bar and one
line series, and one chart-level setting controls bar grouping versus stacking.
Legacy `line_overlay`, nested overlay data, and label-based category matching
are removed. Every series supplies one exact positional value or `null` per
shared category, while author order is preserved independently within bar and
line layers.

### D137 — Axes use semantic typed objects

Schema v1 axis-based charts require a `category_axis` object and a
`value_axes.primary` object. `value_axes.secondary` exists only when a valid
combo series references it. Category-axis fields own visible category chrome;
each value-axis object owns visibility, title, one D145 `format_id`, bounds, and
ticks. Horizontal charts map these semantic roles to physical y/x axes without
a different handoff shape. D74–D90 validation applies through the referenced
format and the axis domain. Legacy orientation-specific unit/domain fields and
duplicate aliases are removed. Hidden chrome still preserves D86 ownership and
D106 accessibility.

### D138 — Composition and chart family are separate concepts

Schema v1 `layout_type` describes composition: `single_chart`, `dual_chart`,
or `chart_hero_dual`; generic `multi_panel` is removed under D154. A chart
visual uses `type: "chart"`, owns a `surface_id`, and selects `chart_type` from
`line`, `grouped_bar`, `stacked_bar`,
`horizontal_bar`, `combo`, `waterfall`, or `heatmap`. Root chart-family layouts
and nested `_chart` spellings disappear; full-slide charts migrate to
`single_chart`. Strict rendering never infers composition from visual type.
Icon grids, semantic tables, cards, and diagrams remain distinct non-chart
visuals. The offline migrator converts unambiguous legacy spelling and placement
mechanically.

### D139 — Chart pane chrome has one explicit owner

Every schema-v1 chart visual owns an explicit `heading` and optional `subtitle`;
`heading` is the sole source of D9/D40 pane-title chrome, and a subtitle requires
a heading. `visual.label`, `chart_config.title`, lone series names, and slide
titles never synthesize pane chrome. `series_identity_owner: "pane_title"` is
valid only for a single-series chart with an explicit heading and is an author
assertion rather than a prose-match inference. The full series name remains in
D106's semantic table and accessibility metadata. The migrator maps only one
unambiguous legacy title source; conflicts require human resolution.

### D140 — Single-chart support is one explicit typed slot

A `single_chart` has exactly one chart and at most one typed support
surface (`support_table`, `outlined_support`, or `metric_strip`).
Payload slot names are owned by D252 (`chart`, `support`).
Legacy keys `primary_visual`, `support_visual`, and `secondary_visual` are invalid.
This composition no longer paints `secondary_visual` or
`content.key_stats` implicitly. Each support visual owns a `surface_id`, typed
content, typography plan, diagnostics, and accessibility structure. Table and
outlined support align to chart categories through `category_id`, never label
matching. D10/D47 plan chart and support together. Unsupported or multiple
support visuals strict-fail; non-strict uses only a named complete-surface
fallback and never truncates extras. Migration converts only unambiguous legacy
secondary tables or metric strips.

### D141 — Table-backed visuals share one canonical semantic model

Schema v1 uses a typed `table_data` object for every table-backed visual. It
contains a typed stub header, ordered columns with stable `column_id`, and
ordered rows with stable `row_id`, labels, and exactly one cell keyed by
`column_id` for every declared column. Missing, duplicate, or surplus cells are
invalid. Labels may own `short_label`; IDs never derive from labels. Data,
annex, grouped-annex, support, pill, heatmap, and matrix/inset tables reuse this
model while retaining distinct visual recipes. D106 generated chart tables use
the same internal model. Legacy list-of-lists and inferred header rows disappear;
the migrator converts only rectangular unambiguous input.

### D142 — Grouped headers reference exact ordered column spans

Grouped and multi-row table headers use ordered `column_groups` with stable
`group_id`, label, and contiguous `column_ids` that reference existing columns.
Within each level, spans do not overlap; every column belongs to exactly one
group or is explicitly ungrouped with its own rowspan. Grouping is limited to
two levels. Renderer-derived colspan, rowspan, `scope`, and `headers` replace
authored numeric spans or HTML semantics. Side-by-side grouped-annex blocks are
separate table surfaces, not another header level. Invalid references, overlap,
gaps, noncontiguity, or excess depth strict-fail; non-strict may use a diagnosed
complete flat header only when every leaf column remains unambiguous.

### D143 — Table cells use an explicit semantic value union

Every `table_data` cell is exactly one of `number`, `text`, or `missing`.
Numeric cells hold a canonical undecorated decimal plus a required `format_id`
for formatted facts; decorated numeric strings are invalid. Text cells preserve
authored text byte-for-byte and are never parsed numerically. Missing cells are
D103's canonical null state, visibly render an em dash, and are announced as
“Missing”; empty strings cannot represent missing data. Real zero remains a
normal numeric value. Cell type drives D104 alignment and D105 numeral handling.
The migrator converts only unambiguous decorated values and flags mixed text.

### D144 — Numeric formats use one deck-level declarative registry

Schema v1 defines a deck-level `number_formats` registry with stable
`format_id`. Numeric table cells and quantitative chart axes reference a format.
Each definition uses only validated unit, unit position, precision, negative
style, optional decimal-safe value scale, and the required scale disclosure.
No printf pattern, locale string, callback, or formatting code is accepted.
Format IDs follow D115 and are unique deck-wide; identical semantics reuse one
format and conflicting definitions are invalid. One formatter serves Chart.js,
SVG, HTML/semantic tables, and accessibility. Scale disclosure renders once per
owning axis or table surface; explicit textual cells remain outside the system.

### D145 — Format references replace inline numeric formatting

Every quantitative value axis and numeric table cell requires one `format_id`;
unit, position, scale, negative style, and precision cannot be restated inline.
A format definition contains `unit`, `unit_position`, `value_decimals` from
0–4, optional `tick_decimals` from 0–4 for generated ticks, `negative_style`,
`value_scale`, and the required `scale_label` when scaled. Omitted tick precision
uses D76's deterministic rule. Value precision governs point/bar labels, totals,
waterfalls, and table values; tick precision governs axis ticks only. Reuse
means identical visible and accessible formatting everywhere. Conflicting
legacy inline fields are migration errors, not precedence cases.

### D146 — Quantitative chart labels derive from typed numeric sources

Ordinary point, bar, segment, waterfall, and computed-total labels derive from
canonical series numbers plus their value-axis `format_id`; duplicate authored
formatted strings are invalid. Non-plotted category-aligned quantitative facts
use typed `auxiliary_series` with stable `auxiliary_id`, role, label,
`format_id`, and exact category-aligned decimal-or-`null` values. Initial roles
are closed to `boxed_label` and `authored_stack_total`. Auxiliary IDs follow
D115, are chart-unique, and their facts appear in D106's semantic table and
accessibility output. Legacy formatted `boxed_labels.values` and
`stack_total_labels` arrays disappear. Context labels and prose annotations
remain separate semantic text under D29/D97.

### D147 — Chart annotations use semantic anchors, never coordinates

Every annotation has stable `annotation_id`, role `event` or `explanation`,
non-empty text, and one typed anchor: whole `chart`, one `category`, one
`data_point`, or an inclusive `category_range`. References use authored IDs;
`x`, `y`, offsets, percentages, CSS, and renderer coordinates are invalid. The
renderer owns placement, collisions, leader lines, and fallback. ID ranges
replace numeric-index measure rules and group brackets. Context labels, series
identities, boxed labels, stack totals, and the FDIC display callout remain
separate roles. Invalid references strict-fail; non-strict retains the fact in
D106's semantic table and omits only visual annotation chrome with diagnostics.
Pixel-positioned legacy annotations require human anchor selection in migration.

### D148 — Range measurements are typed facts, not drawing instructions

Schema v1 replaces `elbow_arrow`, `band`, and `measure_rule` with typed
`measurements`. Each has stable `measurement_id`, role `change` or `cagr`, a
`series_id`, inclusive `from_category_id` and `to_category_id`, explicit
canonical decimal `value`, `format_id`, and `approximate`. The renderer never
recomputes the value from rounded endpoints; sign supplies change direction and
approximation is visible and accessible. The renderer owns rule/elbow chrome,
placement, collisions, and leaders. Event markers use D147 annotations.
Indexes, visual style names, coordinates, and duplicate display strings are
invalid. Measurements appear in D106's semantic table. Legacy callouts migrate
only when role, series, range, value, and format are unambiguous.

### D149 — `dual_chart` is an exact two-chart composition

Schema v1 `dual_chart` contains exactly two ordered chart visuals in `charts`
(payload slot name owned by D253), left-to-right and in accessibility order. Both receive equal usable width at
the fixed stage with only D33's renderer-owned divider. Equivalent typography,
title-band height, plot tops, and exterior gutters synchronize under D3, D46,
and D82; data, axes, identities, annotations, and D106 semantic tables remain
pane-local. Cards, support tables, and metric surfaces are invalid. Authored
widths, ratios, coordinates, and pane CSS are invalid. Strict mode rejects a
malformed pane; non-strict replaces only that pane with D102's semantic-table
fallback. Legacy primary/secondary visuals migrate only when both are
unambiguously charts.

### D150 — `chart_hero_dual` is one chart plus one explicit hero surface

Schema v1 `chart_hero_dual` contains exactly one left `chart`
and one right `hero` (payload slot names owned by D254), in the same
accessibility order. The renderer owns
the fixed 2:1 stage ratio; widths, coordinates, CSS, and responsive authoring
are invalid. `hero.hero_type` is initially closed to `metric_stack` for 1–3
prominent metrics and `driver_card` for D151's structured explanatory rows.
Both surfaces own stable `surface_id`, validation, diagnostics, typography
plans, and accessibility. The chart follows D139 chrome and remains transparent
and borderless; hero surfaces use D66–D67 semantic card chrome. `content.key_stats`,
`secondary_visual`, and implicit metric substitution no longer feed the hero
pane. Invalid hero content strict-fails; non-strict uses only a defined
information-preserving type fallback. Legacy content migrates only when chart
and hero facts map unambiguously.

### D151 — `driver_card` uses ordered typed fact rows

A driver card has required heading, optional subtitle, and 1–6 author-ordered
rows. Each row has stable unique `row_id`, required label and D143 semantic
value, plus optional detail, direction (`up`, `down`, `flat`), and tone
(`positive`, `negative`, `neutral`, `accent`). Numeric values require a D144
format. Direction and tone are independent authored facts, never inferred; the
renderer conveys them with separate theme-owned shape and color plus accessible
wording. Arbitrary icons/colors, sorting, and embedded arrows are invalid.
Label/detail may wrap to two lines; irreducible overflow strict-fails, while
non-strict visually ellipsizes only those fields, retains full accessible text,
and diagnoses this bounded-card exception to D59. Values remain complete.
Malformed rows strict-fail or are individually dropped non-strict; no remaining
rows produce an explicit unresolved hero surface, never substituted metrics.

### D152 — `metric_stack` is an ordered set of prominent facts

A metric stack contains 1–3 author-ordered metrics. Heading and subtitle are
optional, but subtitle requires heading. Each metric has stable unique
`metric_id`, one D143 semantic value, non-empty label, and optional supporting
detail; numeric values use D144 formats and are never parsed from labels.
Display-number typography remains renderer-owned and fixed under D13, while
label/detail prose follows D59 without truncation or suppression. The stack is
one bounded D66–D67 card, not nested cards. Arbitrary color, icon, direction,
tone, size, and per-metric layout controls are invalid; directional facts use
`driver_card`. Explicit missing values remain visible and accessible. Malformed
metrics strict-fail or are individually dropped non-strict; no remaining
metrics produce an explicit unresolved hero surface without `content.key_stats`.

### D153 — `chart_hero_dual` may include one chart-aligned support surface

`chart_hero_dual` may include one optional `support` beneath its left
chart (payload slot name owned by D254); it is not a third pane. The closed types are D140's `support_table`,
`outlined_support`, and `metric_strip`. Table/outlined support aligns through
`category_id`. Chart and support share the left two-thirds region under D10/D47
while preserving the 320x240px chart floor and the composition's fixed 2:1
ratio. Support owns unique `surface_id`, typography plan, diagnostics, and
accessibility; the right hero cannot contain support. Implicit secondary
visuals, `content.key_stats`, and raw-table inference remain invalid. Invalid
support strict-fails or uses D140's complete-surface non-strict fallback without
dropping its facts or replacing chart/hero. Legacy slide 21's ROE row migrates
here.

### D154 — Schema v1 removes generic `multi_panel`

Schema v1 removes `multi_panel` from D138's composition enum and prohibits
arbitrary chart/metric tile mixtures, implicit columns, and tile-specific
chrome. An exact two-chart legacy panel migrates to D149 `dual_chart`; the
recognized chart/support/metric-stack form migrates to D150/D153
`chart_hero_dual`. Every other legacy multi-panel shape remains an explicit
human migration decision rather than being guessed. A genuinely new
composition requires a named semantic contract in a future schema version.

### D155 — Category groups are semantic hierarchy, not bracket instructions

Schema v1 replaces legacy `bar_groups` with `category_groups`. Each group has
stable `group_id`, non-empty label, optional `short_label`, and one or more
contiguous `category_id` references. Single-category groups are valid; categories
may remain deliberately ungrouped. First delivery permits one non-overlapping,
non-nested level. Groups express hierarchy only and never create aggregate bars,
values, series, or subtotals. The renderer owns bracket/header chrome and
includes hierarchy in D106 accessibility and semantic tables. Indexes,
coordinates, and bracket-style controls are invalid. Invalid references,
overlap, or noncontiguity strict-fail; non-strict preserves chart data, omits
only malformed group chrome, and records unresolved hierarchy visibly in the
semantic table plus diagnostics. Legacy groups migrate only when associations
are unambiguous.

### D156 — The FDIC treatment becomes a typed `coverage_callout`

Schema v1 replaces generic `side_callout` with at most one
`coverage_callout`, valid only on a stacked-bar chart. It has stable chart-unique
`callout_id`, one D143/D144 numeric value, required label, and optional period
label. It is one chart-level coverage fact, not a category, series, legend,
annotation, or generic callout. The renderer owns D50's fixed prominent chrome,
wrapping, and shared exterior lane with segment identities; placement, skin,
coordinates, colors, sizes, and authored line breaks are invalid. The complete
fact appears in D106 accessibility and semantic tables. Planning may reclaim
width only to D47's floor. Remaining overflow strict-fails; non-strict moves the
whole callout below the plot with diagnostics rather than omitting it. Legacy
side callouts migrate only when value, label, and period separate unambiguously.

### D157 — Axis breaks are explicit leading-domain omissions

Schema v1 value axes may declare one `leading_break.to` only for line and
horizontal-bar charts. It omits the interval from declared domain minimum
through `to`; interior, trailing, and multiple breaks are invalid. `to` must be
below every finite plotted value and equal the first visible tick. Values remain
true source numbers; only axis space is omitted. The renderer owns the break
glyph and discloses the omitted interval in D106 accessibility/semantic tables;
Chart.js and SVG use equivalent domains/chrome. No semantic zero line appears
when zero is omitted. Vertical/stacked bars, combos, waterfalls, and heatmaps
cannot truncate their baseline. Invalid breaks strict-fail; non-strict discards
the break, computes a safe continuous domain, and diagnoses it. Legacy breaks
migrate only when they match this leading form.

### D158 — Axis visibility is semantic and never changed automatically

`category_axis.visible` and each `value_axes.*.visible` default true. Adaptive
planning may wrap, rotate, or reduce ticks but never hides a whole axis. A
hidden category axis is valid only when every category has another visible
owner; a hidden value axis is an explicit author choice whose complete meaning
remains in D106. Hidden chrome includes axis line, ticks, labels, and visual
title, while title remains accessible. D84-required zero lines remain.
Authored bounds may still control geometry/comparability, but ticks are invalid
on a hidden value axis. Physical `show_x_axis`/`show_y_axis` aliases disappear;
semantic roles map by orientation. Non-strict drops contradictory hidden-axis
ticks with diagnostics. Amex slides 13–14 migrate to hidden primary value axes
with complete outside percentage labels.

### D159 — Value-axis domains distinguish fixed from generated ticks

Each value-axis domain is `generated` or `fixed`. Generated domains permit
optional valid bounds and `target_tick_count` 2–8; the renderer chooses ticks
deterministically and may reduce density while preserving endpoints and required
zero. Fixed domains require at least two finite strictly increasing ticks whose
first/last equal min/max; those ticks are authoritative and cannot be skipped,
changed, or supplemented. Both obey D83 containment. Hidden value axes cannot
be fixed. `force_ticks` disappears: a tick list means fixed. Bare legacy bounds
migrate to generated and valid explicit lists to fixed. Invalid fixed domains
strict-fail; non-strict discards the whole declaration and computes a diagnosed
safe generated domain. Sibling typography/gutters may synchronize, authored
domains do not.

### D160 — Bar spacing is renderer-owned and geometry-driven

Schema v1 removes `bar_percentage`, `category_percentage`, and `fill_tile`.
Authors supply data, grouping/stacking, identities, and composition rather than
width ratios or fill behavior. The frozen D69 plan chooses bar thickness and
category occupancy from plot geometry, category/series counts, grouping,
outside-label bounds, legends, category groups, support alignment, and exterior
lanes, using theme-owned thickness bounds. Sibling panes coordinate category
pitch only when category IDs/order match exactly. Chart.js and SVG share planned
plot rectangles, centers, and thickness within 2px at 1920x1080. Authors cannot
force fill; D47/D48 govern allocation. Legacy ratios are migration review hints
then removed. Slide 28's approved density is pinned by geometry assertions, not
handoff percentages.

### D161 — Bar arrangement is intrinsic to the chart family

`grouped_bar` means vertical side-by-side bars and permits one series;
`stacked_bar` means vertical stacks; `horizontal_bar` means horizontal grouped
bars only in schema v1. `combo` requires one chart-level `bar_mode` of `grouped`
or `stacked` for all bar series. Legacy `stacked`, arbitrary stack IDs, and
per-series overrides disappear. A stack uses one value axis/format; conflicting
units, scales, or axes are invalid. Positive and negative segments accumulate
independently from zero. D101 order, D92 missing segments, and D79/D146 labels
and totals apply. Malformed arrangements strict-fail or replace only the pane
with D102's non-strict semantic-table fallback. Horizontal stacking requires a
future measured schema contract. Migration converts only unambiguous legacy
arrangements.

### D162 — Waterfalls use explicit typed step roles

A waterfall has exactly one series/value axis and ordered categories typed as
`change`, `total`, or `computed_total`. Change requires a signed canonical
decimal and moves the running level. Total requires an absolute decimal, paints
from zero, and resets the level. Computed total has no authored value and paints
the exact known accumulated level without changing it. Zero remains zero and
never implies computation; roles are never inferred from sign, label, position,
or value. Theme-owned increase/decrease/total colors and the axis format apply;
D52/D146 labels cannot be suppressed. A missing change makes later computed
totals unknown until an explicit total restores level. Multiple series,
secondary axes, stacking, and arbitrary step colors are invalid. Malformed
waterfalls strict-fail or use D102's non-strict semantic-table pane fallback.

### D163 — Heatmaps are typed semantic tables with one color scale

Heatmaps use D141 `table_data`, not axis-series data. Body cells are only D143
numeric or missing values and share one heatmap `format_id`; prose and per-cell
formats are invalid. Scale mode is `generated` from all finite cells or `fixed`
with authored finite min < max; out-of-range fixed-scale values are invalid.
First delivery uses one renderer-owned sequential light-to-primary-blue scale,
with no diverging palette, arbitrary colors, thresholds, or cell styling. Every
finite cell visibly prints its formatted value. Missing cells show an em dash,
announce “Missing,” and remain neutrally unfilled. A visible compact scale key
and D106 representation are required when finite values exist. D141–D145 and
D103–D105 govern headers/type/associations; cell boundaries remain semantic.
Malformed/empty scales strict-fail or use D102's non-strict visible table
fallback without color encoding.

### D164 — Chart display policies replace overlapping visibility booleans

Schema v1 chart visuals use one closed `display` object. `ordinary_values` is
`show` or `hide`, defaults to show for line/combo-line and non-stacked bars, and
is invalid where ordinary labels do not apply. `stack_segments` and
`stack_totals` are independent `show`/`hide` policies, default hide, and apply
only to stacked-bar layers; a D146 authored stack total implies totals shown.
`series_identity` is `auto`, `legend`, or `pane_title`: auto follows D15/D37,
legend always renders one complete legend, and pane-title is valid only for
D139's explicitly titled single-series case. These policies cannot hide
categories, context facts, measurements, annotations, structural waterfall
values, or D106 semantic tables. Legacy visibility booleans and aliases migrate
only when unambiguous, then disappear. Inapplicable or conflicting fields
strict-fail; non-strict discards the whole malformed display object and applies
diagnosed defaults.

### D165 — `metric_strip` is a compact typed support surface

A metric strip contains 1–6 author-ordered metrics, each with unique `metric_id`,
non-empty label, D143 semantic value, and optional detail. Numeric values require
a D144 format; missing stays visible and accessible. It has no independent
heading/subtitle and renders as one renderer-owned horizontal row of equal-width
cells supporting its chart. Values retain fixed KPI/display typography; labels
and details use adaptive support typography and may wrap to two lines without
abbreviation, reordering, or dropping. Icons, colors, trends, directions,
per-cell layout, and arbitrary styling are invalid and belong to metric-stack or
driver-card semantics. D47 allocates height while preserving the chart floor.
Malformed entries strict-fail; non-strict drops invalid entries with diagnostics
and omits an empty resulting strip as unresolved. Legacy `content.key_stats`
migrates only when it is an explicit chart metric row and is never painted
implicitly.

### D166 — `outlined_support` is one category-aligned measure row

Outlined support is a constrained D141 table with exactly one row whose column
IDs/order exactly match the owning chart categories. The chart visually owns
category labels, so the row omits a duplicate visual header while retaining
complete semantic-table associations. Its label occupies a dedicated exterior
lane and may wrap to two lines; each value uses one square-edged outlined box
centered on the frozen chart-category center. Label/value boxes share D44's
22–24px fitted size. The label lane cannot overlap the first box, and Chart.js,
SVG, and boxes align within 2px at 1920x1080. Missing values retain em-dash
slots. Skins, widths, gutters, offsets, cell styles, and authored/runtime
geometry are invalid. If D47-safe alignment cannot fit, strict fails; non-strict
renders the complete row as ordinary support-table content with diagnostics.
Legacy `data_table` plus `skin: outlined_boxes` migrates only for one
unambiguously category-aligned row.

### D167 — `support_table` has explicit alignment semantics

A support table declares `alignment: category` or `independent`. Category
alignment requires table columns to match every owning-chart category ID and
order exactly, uses the frozen category centers in Chart.js/SVG, and omits a
repeated visual header when the chart already visibly owns those categories
while preserving semantic associations. Independent tables use ordinary D141
layout and may have unrelated columns. Support tables contain 1–4 rows, use one
D44 14–24px fitted size, and cannot own heading/subtitle chrome. D10/D47 govern
allocation. Alignment is never inferred from labels, counts, or position.
Invalid category alignment strict-fails; non-strict preserves the complete table
as diagnosed independent alignment. Migration chooses category only for
unambiguous ID mappings and otherwise emits independent.

### D168 — Context labels are typed chart facts with stable IDs

Schema-v1 `context_labels` lives directly on the chart visual and contains 1–4
author-ordered facts. Each requires a unique D115 `context_id`, non-empty label,
and D143 semantic value; `short_label` is optional. Numeric values require a
D144 format, text remains exact, and missing remains visible/accessibly missing.
Values, icons, tones, colors, coordinates, and styling are never inferred.
D30 owns placement and retention; D18/D97 suppress only duplicate chrome. D106
contains each complete fact exactly once even when a short visual label is used.
Malformed entries strict-fail; non-strict drops only malformed entries with
diagnostics and never recasts them as annotations or identities. Legacy
label/value pairs migrate only when value semantics are unambiguous; decorated
numeric strings requiring interpretation remain migration decisions.

### D169 — `chart_config` contains only display-planning policy

Schema-v1 `chart_config` is optional and contains only `typography` and
`display`; omission means adaptive typography plus D164 defaults. Data/identity
stay in `chart_data`; semantic axes are direct chart fields; context labels,
annotations, measurements, auxiliary series, category groups, and coverage
callouts are direct semantic fields; family-specific semantics remain in their
typed structures. Legacy title, surface/stage, gridline, series-array, plot,
gutter, offset, density, wrapping, callback, and style payloads disappear.
Typography and display validate independently under D28/D164, so one malformed
subgroup does not discard the other. Unknown fields follow D118. Generic
`extra`, `options`, `plugins`, and renderer escape hatches are forbidden.

### D170 — Pane headings are composition-dependent

A `single_chart` heading is optional; when absent, the slide title is the sole
visible heading and no pane band is synthesized. Both `dual_chart` charts and
the left chart/right hero in `chart_hero_dual` require non-empty headings,
including metric-stack when used as that hero. A subtitle always requires its
own surface heading. Missing headings are never inferred from slide title,
series name, legacy label, or neighboring prose. Strict rejects a missing
required heading. Non-strict preserves the surface with diagnosed neutral
structural wording such as “Untitled chart 1” or “Untitled summary,” without
inventing business meaning. D31/D139 title-band and accessibility rules apply.

### D171 — The main slide subtitle has one explicit owner

Every ordinary content slide requires a non-empty root `title` and may contain
one non-empty `content.subtitle`, rendered exactly once beneath the slide title
with D12/D41/D59 adaptive 22–26px typography. `content.typography` controls only
that subtitle through `subtitle_font_size`, `mode`, and `sync_group`. Generic
`content.headline`, `chosen_dek`, duplicate comparison, numeric heuristics, and
headline/subtitle fallback disappear. Body headings belong to typed visuals or
cards; covers/dividers use their own composition fields. Empty strings are
invalid rather than omission. Subtitle overflow reclaims geometry and wraps but
never abbreviates, ellipsizes, or loses text; strict fails if it cannot fit,
while non-strict paints complete floor-size text with diagnostics. Migration
maps a lone subtitle directly and a lone headline only when its recipe
unambiguously used it as this line; conflicts require human resolution.

### D172 — `so_what` becomes one explicit slide takeaway

An ordinary content slide may contain at most one `takeaway` with non-empty
text and optional card typography. It is a slide-level conclusion distinct from
subtitle, chart annotation, context fact, source, and notes, rendered exactly
once after the main composition as a bounded D66–D67 recommendation/rationale
component and never inside a chart plot. The renderer supplies accessible “Key
takeaway” wording. Typography follows D41/D59 at 22–28px with complete wrapping
and no abbreviation, ellipsis, or suppression. Its height is reserved before
the frozen plan; overlap is forbidden. Heading, icon, tone, arbitrary color,
coordinates, and layout controls are invalid. Legacy non-empty
`content.so_what` migrates directly; heuristic promotion from headline/body/
bullets does not. Unfittable complete text strict-fails or uses D59's diagnosed
non-strict floor-size overflow behavior.

### D173 — Speaker notes are authored prose, never renderer-generated

Optional root `speaker_notes` is non-empty authored plain text. The renderer
preserves wording and paragraph breaks exactly except safe HTML escaping and
never synthesizes from titles, bullets, takeaways, metrics, charts, purpose, or
neighboring slides. It does not remove stage directions, rewrite bridges, strip
IDs, join claims, or truncate. Missing notes emit no notes content. Notes remain
outside the visible slide and match exactly between HTML notes view and the
notes artifact. HTML, Markdown directives, evidence commands, and executable
content remain literal. Empty strings are invalid. Migration copies genuine
presentation notes unchanged, while operational comments such as pass names,
renderer instructions, or fidelity grades require human resolution. Any
cross-artifact mismatch fails acceptance.

### D174 — Supplementary disclosure uses one native pattern

Optional disclosure is supplemental only; interpretation-critical facts cannot
be hidden there. It contains 1–4 ordered sections with stable disclosure/section
IDs, non-empty titles, and 1–6 authored plain-text paragraphs or list items.
The renderer uses one `<details>` block for one section and a native details
accordion for several. Author-selected patterns, tabs, default-open state,
styling, HTML, and interaction controls disappear. Print/static output expands
all sections; no-JS remains complete. IDs derive from semantic identities, never
UUIDs. Accessibility includes complete disclosure once without duplicating
visible facts. Malformed disclosure strict-fails; non-strict drops malformed
sections with diagnostics and omits an empty unresolved block. Legacy detail and
accordion migrate mechanically; tabs require human confirmation because they may
represent alternate primary views.

### D175 — Evidence uses one deck registry plus slide references

Schema v1 has one authoritative deck-level `evidence_registry`; slides carry an
ordered duplicate-free `evidence_ids` list referencing it. Registry IDs use
D115 slugs and are deck-unique; each entry requires `source_name` and may retain
an opaque `locator`. The renderer validates references but never opens sources,
resolves URLs, or validates business truth. IDs/locators never appear visibly or
in notes; optional source footers use deduplicated source names only. The
evidence manifest deterministically preserves full registry metadata and
slide links. Missing, duplicate, or malformed references strict-fail;
non-strict drops only unresolved references with diagnostics and degrades the
deck. Legacy EIDs migrate through an explicit ID map and may remain opaque
provenance aliases, not exceptions to D115. Per-slide evidence objects and mixed
string/object forms disappear.

### D176 — Visible source footers are explicit, never inferred

Optional `source_footer` contains an ordered duplicate-free list of 1–4
evidence IDs that must be a subset of the slide's `evidence_ids`; omission means
no visible footer. It renders each referenced registry `source_name` exactly once
in authored order and never exposes IDs, locators, paths, or inferred filenames.
Evidence alone never creates a footer. Fixed footer typography is outside
adaptive growth, and its space is reserved before planning so it cannot overlap
content, disclosure, or slide numbering. Covers and dividers cannot carry one.
Overflow strict-fails; non-strict omits the complete footer with diagnostics
while retaining manifest links. Legacy source strips migrate only when every
displayed name maps unambiguously to registered evidence.

### D177 — Typed composition replaces `packing_mode`

Schema v1 removes root `packing_mode`; typed compositions and semantic surfaces
determine layout. D69's frozen planner derives density and allocation from
validated content, geometry, typography, and composition contracts. Legacy
`chart-led`, `stat-led`, `argument-led`, `metric-led`, and `cover-led` cannot
influence notes, kickers, title chrome, fallbacks, or CSS. Internal planning
strategies may appear in diagnostics but are not author controls. Migration
removes the hint only when typed composition fully represents its intent and
flags ambiguous conflicts for human resolution. In schema v1 the field is an
unknown-field error under D118.

### D178 — Deck sections use stable registry identities

Schema v1 defines an ordered deck-level `sections` registry with D115
`section_id` and non-empty authored `label`; every ordinary content slide
references exactly one section. Opening/closing brand slides may omit it, while
a section divider references the section it introduces. Registry order defines
navigation, and each section's slides form one contiguous run in that order.
Identity feeds navigation, accessibility, diagnostics, and manifests, but its
label never automatically becomes a content-slide kicker, pane heading, or
footer; only the typed divider paints automatic section chrome. Missing or
duplicate references, ordering conflicts, and discontiguous runs strict-fail.
Non-strict preserves slide order, uses diagnosed positional identities as
needed, and marks navigation degraded rather than moving slides. Migration
coalesces exact repeated legacy section strings; inconsistent spellings or
ambiguous boundaries require human resolution.

### D179 — Covers and dividers use semantic renderer-owned compositions

Schema v1 has explicit `opening_cover`, `section_divider`, and `closing_cover`
compositions. At most one opening cover is first and at most one optional closing
cover is last. A divider immediately precedes the first ordinary slide in its
referenced section and gets its title only from the section registry. Cover
titles are required; optional subtitle, period, and date remain separate fields.
The renderer owns the Boardroom/Amex seal, lockup, bands, spacing, and all brand
chrome. Brand marks/SVG, tone, arbitrary colors, and layout controls disappear.
Covers/dividers cannot contain ordinary surfaces, takeaways, disclosures, or
source footers; notes and non-visible evidence references remain allowed.
Position, multiplicity, missing-title, or misplaced-divider violations
strict-fail. Non-strict preserves order and emits a diagnosed title-only brand
plate without inventing text. Migration removes exact current-theme controls,
splits only unambiguous period/date text, and flags custom marks or conflicting
or concatenated titles for human resolution.

### D180 — Every slide uses a closed semantic composition

Schema-v1 `layout_type` is a closed discriminated union of named semantic
compositions. Each owns exact allowed surfaces, cardinality, reading order,
accessibility, and planning rules. Shared slide fields are limited to title,
subtitle, takeaway, notes, evidence, source footer, disclosure, and section
identity. Generic `primary_visual`, `secondary_visual`, grids, CSS, coordinates,
and implicit surface inference disappear; D69 owns geometry. Unknown
compositions or invalid surface combinations strict-fail before painting.
Non-strict never guesses or paints raw dictionaries; it emits a typed diagnosed
unresolved slide containing only validated common prose and accessibility
content. Migration maps only semantically unambiguous legacy layouts, while
split/freeform slides require human composition selection.

### D181 — Text-only content uses one typed `narrative` composition

`narrative` has one full-width body with 1–4 ordered blocks. Initial block types
are paragraph and bullet list; repeatable blocks own D115-style `block_id`.
Lists contain 1–8 items and paragraph blocks 1–6 non-empty paragraphs. Charts,
tables, cards, arbitrary grids, columns, and coordinates are invalid. D69 owns
geometry and D59's adaptive 22–28px prose rules apply. Author order and wording
are preserved without rewriting, summarizing, combining, dropping, or automatic
slide splitting. Floor-level overflow strict-fails; non-strict retains complete
text with an unresolved-overflow diagnostic. Legal notices use a separate
fixed-typography composition. Migration maps `ir_bullet_sheet` and text-only
`split_text_visual` only when no visual intent exists; mixed/freeform slides
require human selection.

### D182 — Legal prose uses a dedicated `legal_notice` composition

`legal_notice` contains 1–6 authored non-empty plain-text paragraphs. A
multi-slide notice shares one stable `notice_id`; adjacent slides use contiguous
`part` values from 1 through `total_parts`. Part 1 requires the full title and
later parts expose a renderer-owned accessible continuation state rather than
authored `(cont.)` titles. Typography is fixed outside adaptive growth. The
renderer preserves every character and paragraph boundary except safe HTML
escaping and never summarizes, rewrites, moves text between slides, or generates
legal language. Floor-level overflow strict-fails; non-strict emits all text in
a visibly diagnosed overflow-safe legal pane without clipping or loss. Charts,
tables, cards, takeaways, disclosures, and source footers are invalid; notes and
non-visible evidence links remain allowed. Print, screenshot, HTML,
accessibility, and extracted text preserve identical wording and part order.
Migration requires exact extraction plus human-confirmed part boundaries.

### D183 — Ordinary tables use one `data_table` composition

`data_table` contains exactly one full-width D141 table surface. The slide root
owns its required title and optional subtitle; table chrome cannot duplicate
them. D8 supplies uniform navy headers, D24–D25 fitting, and D44 one common
adaptive 20–24px size. D144–D145 scale disclosure renders once per table. Body
cells remain transparent; outer card fill, shadow, rounded frames, skins,
per-cell styling, merged body cells, authored widths, and CSS are invalid. One
D172 takeaway may follow and participates in the frozen plan. Capacity is
validated from complete 1920x1080 fit rather than fixed row/column counts, and
no declared row or column may disappear. Unfittable content strict-fails;
non-strict uses D25 floor-size diagnosed behavior without truncation. Migration
requires unambiguous D141–D145 headers, rows, cells, formats, and missing states.

### D184 — Dense annexes use one dedicated `annex_table` composition

`annex_table` contains exactly one full-width D141 table and supports D142
grouped/multi-row headers through two levels. Every header uses D8/D42 navy,
white text, and visible separators. The slide root exclusively owns title and
optional subtitle. One common D44 adaptive 12–24px size plus D24–D25 fitting
applies to the complete table. All rows, columns, associations, units, formats,
missing states, and footnote references remain. Body cells are transparent with
semantic separators; cards, shadows, rounded frames, skins, authored widths, and
per-cell styling are invalid. Annex slides cannot contain takeaways, cards,
charts, or sibling tables; supplemental prose uses D174 disclosure. Capacity
comes from complete 1920x1080 fit. Unfittable content strict-fails; non-strict
paints the complete 12px-floor table with unresolved-overflow diagnostics and
never truncates, splits, or moves rows. Migration requires unambiguous headers,
groups, rows, values, formats, missing states, and associations.

### D185 — Peer annex matrices use `grouped_annex_table`

`grouped_annex_table` contains exactly 1–2 ordered peer annex surfaces, each
with unique stable `surface_id`, non-empty heading, and complete D141 table. Two
surfaces render side by side at equal usable width with one renderer-owned
straight divider; they never flatten or stack vertically. D142 headers and D184
annex styling apply, and equivalent roles share the largest common safe 12–24px
size. Group headings are semantic table headings, not pane bands or duplicate
slide titles. Charts, takeaways, cards, and additional tables are invalid;
D174 disclosure remains allowed. If either peer cannot fit, strict fails;
non-strict replaces the complete composition with a sequential accessible
flat-table fallback preserving both headings and all rows, never only one peer.
Migration requires 1–2 complete unambiguous groups and identities.

### D186 — Financial period comparisons use `period_comparison`

`period_comparison` contains one D141 table with a stub and exactly three ordered
value-column roles: current period, comparison period, and variance, with 1–8
complete metric rows. D143/D144 govern values and formats. The renderer owns
three separated square-edged bounded columns with navy header caps, solid panel
tokens, and 1px borders; gradients, shadows, rounded pills, skins, and authored
styling are invalid. One common adaptive 20–24px size applies. One optional D165
metric strip with 1–3 related metrics may occupy a planned exterior lane without
overlap or readability loss. D172 takeaway and D174 disclosure remain allowed
and planned. Missing roles or unfittable content strict-fail; non-strict
preserves all data in a diagnosed ordinary data-table fallback and retains the
metric strip separately. Migration requires unambiguous roles, formats, rows,
and optional metrics.

### D187 — Structured peer comparisons use `comparison_cards`

`comparison_cards` uses one D141 table as its semantic source: 2–4 rows become
peer cards and 2–4 columns define the same ordered fact roles across every card.
Each row label is the card heading; cells retain D143 number/text/missing
semantics. Cards have equal rank, width, fact order, and fitted typography.
D66–D67 supplies solid panel tokens, 1px borders, square edges, and no gradients
or shadows. Heading, label, and value roles adapt independently while preserving
hierarchy. Authored positions, widths, colors, icons, circles, ratios, HTML, and
CSS are invalid. D172 takeaway and D174 disclosure remain allowed; unrelated
key stats or duplicate bullet prose are invalid. Unfittable complete content
strict-fails; non-strict renders the same D141 data as a complete accessible
table. Migration requires unambiguous peer headings/fact roles and one selected
canonical source when legacy bullets/key stats duplicate data.

### D188 — Quantitative ranges are typed semantic values

D143 adds a closed quantitative range with finite canonical-decimal `lower` and
`upper`, `lower < upper`, and one shared D144 `format_id`. D77 formatting,
rounding, trailing zeros, scaling, unit, and negative style apply to both
endpoints; visible output preserves both complete values and accessibility
announces the full interval. Ranges may appear in tables, metrics, driver cards,
context facts, and other non-plotted semantic values, while plotted series,
domains, stacks, totals, and coordinates remain scalar-only. Equal endpoints use
one ordinary number; open-ended ranges require a future contract. Malformed
ranges strict-fail. Non-strict collapses only an equal range to its scalar and
otherwise emits diagnosed missing rather than swapping or guessing bounds.
Legacy range strings migrate only when both endpoints and their shared format
are unambiguous.

### D189 — Metric-led slides use `metric_overview`

`metric_overview` contains one required metric surface with 2–6 ordered
D152-style metrics and at most one detail surface beneath it. The metric surface
has stable ID, required heading, equal-rank bounded D66–D67 chrome, and metrics
with stable IDs, D143/D188 values, labels, and optional detail. Display numbers
stay fixed; labels/details adapt at 22–28px and wrap to two lines without loss.
The optional detail has its own heading and 1–4 D181 paragraph/bullet blocks.
Generic supporting points, colon parsing, synthesized “Breakdown,” source strings
inside cards, and duplicate key-stat/bullet sources disappear. Charts are
invalid; chart-plus-metric cases use D140/D150 support contracts. D172 takeaway
and D174 disclosure remain allowed. Unfittable content strict-fails; non-strict
preserves every metric and detail block in a sequential accessible fallback.
Migration requires one canonical metric source and explicit classification of
legacy bullets as detail.

### D190 — Guidance reuses `metric_overview`

Schema v1 removes `guidance_statement_card`. Guidance uses D189 metrics with
D188 ranges/shared formats and exact authored qualification prose in the
optional detail surface. The renderer never infers midpoints, period comparison,
raised/lowered/reaffirmed status, or positive/negative tone. Guidance-specific
colors, icons, arrows, badges, and hard-coded chrome do not exist; planning,
accessibility, diagnostics, and fallback match every metric overview. Migration
requires unambiguous metrics and qualification prose or human resolution.

### D191 — Specialized visual families survive only as closed contracts

Renderer 3.0 retains useful non-Amex quote, process, relationship-diagram,
decision-matrix, and icon-card families only as named semantic compositions with
closed typed models. Generic grids, arbitrary nodes, renderer coordinates, raw
SVG/CSS, and catch-all configuration remain forbidden. D60 keeps their first-
delivery typography fixed; D5–D6 applies to plot-like regions and D66–D67 to
real semantic cards. Each retained family requires deterministic HTML/SVG,
accessibility, strict validation, a safe non-strict fallback, and schema-v1
migration coverage. Direction/style-only variants consolidate into semantic
fields. Layouts without a defensible semantic model are removed for human
migration rather than receiving compatibility recipes, and no family exists
merely to preserve a legacy layout string.

### D192 — Procedural sequences use one `process_flow` composition

`process_flow` contains 2–6 author-ordered steps, each with a stable `step_id`,
non-empty heading, and optional detail. Connections are implicitly sequential;
authors cannot specify arrows, coordinates, direction, numbering, colors, icons,
or CSS. The frozen planner chooses horizontal or vertical placement without
changing semantic order, and renderer-generated step numbers are display chrome.
Terminal outcomes are ordinary final steps rather than inferred closed loops.
Branches/decisions, chronology, and feedback cycles belong to separate semantic
contracts. D60 keeps first-delivery typography fixed. Unfittable content strict-
fails; non-strict preserves every step in a diagnosed accessible ordered list.
Migration accepts only genuinely linear legacy sequences; inferred outcomes,
decision diamonds, dates, and cycles require semantic migration.

### D193 — Chronology uses one `timeline` composition

`timeline` contains 2–8 author-ordered milestones, each with a stable
`milestone_id`, exact non-empty `time_label`, non-empty heading, and optional
detail. Time labels remain authored text so fiscal periods and qualitative terms
survive without date parsing. Author order is authoritative; the renderer never
sorts, normalizes, calculates durations, invents periods, or rewrites years from
titles. The frozen planner chooses horizontal or vertical geometry without
changing chronology. Status, progress, dependencies, phase bands, icons, colors,
coordinates, and arbitrary connectors are excluded pending separate measured
contracts. Undated procedures use D192 and branching plans use the decision
contract. D60 keeps first-delivery typography fixed. Unfittable content strict-
fails; non-strict preserves every milestone in a diagnosed accessible
chronological list. Migration requires unambiguous periods and wording.

### D194 — Branching logic uses a constrained `decision_tree`

`decision_tree` contains 3–15 stable-ID nodes, one authored root, and maximum
depth four. Decision nodes require a non-empty prompt and exactly 2–3 ordered
branches, each with an authored non-empty label and valid target; outcome leaves
require a heading and optional detail. The structure is one rooted, connected,
acyclic tree: every non-root node has one parent, every node is reachable, and
shared targets, loops, and cross-links are invalid. Authors cannot specify
shapes, coordinates, routes, colors, icons, or CSS; visual geometry may vary but
node/branch order remains authored. D60 keeps typography fixed. Valid but
unfittable trees strict-fail or become a complete diagnosed nested outline non-
strict. Structurally invalid trees strict-fail or become an accessible
relationship table preserving every authored node/relation and visibly marking
unresolved targets without guessing. Migration requires explicit prompts,
branch labels, targets, and outcomes.

### D195 — Cycles use a closed `feedback_loop` union

`feedback_loop` contains 3–8 author-ordered stable-ID items with headings and
optional details, connected as exactly one cycle in authored order including the
closing edge. `kind` is `procedural`, whose edges mean next, or `causal`, whose
items additionally author the next-edge effect as `same_direction` or
`opposite_direction` plus optional relationship label. The renderer derives the
complete causal loop's reinforcing/balancing classification from those authored
polarities but never infers individual relationships. Branches, chords, shared
targets, disconnected items, arbitrary links, coordinates/routes, colors,
icons, and CSS are invalid. Geometry may rotate/reposition without changing
order. D60 keeps typography fixed. Valid but unfittable loops strict-fail or
become a complete accessible ordered relationship list non-strict. Invalid
causal data strict-fails or becomes a diagnosed relationship table preserving
all authored items and valid relationships without invented links/polarities.
Migration requires one clear cycle and unambiguous procedural-versus-causal
meaning; decorative circles require human resolution.

### D196 — Architecture uses non-graph `layered_architecture`

`layered_architecture` contains 2–4 ordered layers, each with stable ID, heading,
and 1–4 stable-ID components with headings and optional detail. Layer order
expresses grouping and visual stacking only, never dependency, causality, or
flow; the renderer invents no arrows from position/order. Components use D66–
D67 bounded chrome while layers use structural grouping without decorative
fills or shadows. Links, ports, protocols, status, icons, arbitrary roles,
coordinates, colors, and CSS are invalid; directed movement belongs to the
pipeline contract. D60 keeps typography fixed. Unfittable content strict-fails
or becomes a complete diagnosed nested outline non-strict. Migration requires
unambiguous layer/component/detail fields; meaningful legacy arrows or inferred
dependencies require human resolution.

### D197 — Directed system flow uses `data_pipeline`

`data_pipeline` contains 2–6 ordered stages. Each has a stable ID, heading, and
1–3 stable-ID components with headings and optional details. Stage order defines
one linear directed flow; optional `transfer_label` gives the exact transfer to
the next stage and is invalid on the final stage. The renderer owns arrows and
routes and infers no protocols, dependencies, transformations, roles, or labels.
Branches, merges, loops, cross-links, ports, coordinates, icons, colors, and CSS
are invalid. Components use D66–D67 bounded chrome; stage boundaries are
structural and undecorated. Procedures use D192 and static grouping D196. D60
keeps typography fixed. Unfittable content strict-fails or becomes a complete
diagnosed accessible ordered flow non-strict. Migration requires unambiguous
stages, components, and adjacent transfers; graph-like flows require human
resolution.

### D198 — Parent-child structures use constrained `hierarchy`

`hierarchy` contains 3–20 stable-ID nodes, one root, and maximum depth four.
Each node has a heading, optional detail, and ordered child IDs.
The whole tree declares one child-to-parent relationship: `reports_to`,
`part_of`, or `is_a`; mixed relationships require a future contract. It is one
rooted, connected, acyclic tree: root has no parent, every other node exactly
one, all nodes are reachable, and shared children, loops, and cross-links are
invalid. Child-ID order controls sibling order. Authors cannot specify geometry,
routes, status, icons, colors, shapes, or CSS. D60 keeps typography fixed. Valid
but unfittable trees strict-fail or become a diagnosed nested outline non-strict.
Invalid trees strict-fail or become a complete relationship table preserving
nodes/declared relations and marking unresolved targets without reconnection.
Migration requires explicit parent-child semantics and never infers hierarchy
from adjacent legacy groups.

### D199 — Ecosystems use hub-and-spoke `stakeholder_map`

`stakeholder_map` contains exactly one stable-ID focal entity and 2–8 ordered
stable-ID stakeholders, all with headings and optional detail. Each stakeholder
requires an exact relationship label and direction relative to the focal entity:
`undirected`, `to_focal`, `from_focal`, or `bidirectional`. Only focal-to-
stakeholder relationships exist; stakeholder links, multiple hubs, chains,
branches, and unlabeled relationships are invalid. Author order controls
deterministic placement; geometry may rotate but never reorder. Authors cannot
specify coordinates, routes, line styles, colors, icons, shapes, or CSS. D60
keeps typography fixed. Valid but unfittable maps strict-fail or become complete
diagnosed relationship lists non-strict. Invalid maps strict-fail or become
relationship tables preserving valid authored entities/relations and visibly
marking unresolved references. Migration requires one clear focal entity and
only focal links; arbitrary webs require human resolution.

### D200 — Two-axis prioritization uses `quadrant_matrix`

`quadrant_matrix` has exactly two authored binary axes defining four quadrants;
each axis has a label and exact low/high endpoint labels. It contains 1–16
ordered stable-ID items with heading, optional detail, and explicit `low`/`high`
band assignment on both axes. Bands are semantic, never numeric coordinates or
inferred scores. The renderer owns within-quadrant placement while preserving
order, and empty quadrants remain labelled. Scores, coordinates, sizes, colors,
icons, quadrant styling, and CSS are invalid. D60 keeps typography fixed. Valid
but unfittable matrices strict-fail or become a diagnosed accessible four-group
fallback preserving axes, quadrants, and items. Invalid assignments strict-fail
or enter a visibly unresolved group non-strict rather than being guessed.
Migration requires explicit or mechanically unambiguous axes and assignments.

### D201 — Icon collections become `feature_cards`

`feature_cards` contains 2–6 ordered equal-rank cards with stable `card_id`,
non-empty heading, optional detail, and optional `icon_key` from a closed theme-
owned registry. Raw SVG, paths, URLs, emoji, arbitrary icon names, colors, and
CSS are invalid. Icons are decorative/accessibility-hidden, so all meaning stays
in text. Cards use D66–D67 square-edged panel chrome with consistent role fit.
This preserves D60's icon-card exception: text adapts within 22–28px while icon
size/geometry stay fixed, narrowing D191's broad fixed-typography wording.
Metrics, evidence, process steps, comparisons, and quantitative values use their
dedicated contracts. Unfittable content strict-fails or becomes a complete
diagnosed heading/detail list non-strict. Migration requires recognized icons
and clear heading/detail cards; unknown or potentially semantic icons require
human resolution rather than substitution.

### D202 — Quotations use provenance-aware `quotation`

`quotation` contains 1–3 ordered quotations. Each has a stable `quote_id`, 1–3
non-empty plain-text paragraphs, and attribution with required name plus optional
role and organization. Optional `evidence_id` must resolve through D175 and be
among the slide's evidence references; provenance IDs/locators never paint.
Wording, punctuation, paragraph boundaries, names, roles, and organizations stay
exact. The renderer never parses attribution from punctuation and never invents
“Anonymous”; unattributed prose uses D181. Decorative quote marks stay out of
accessible text while native blockquote/cite semantics announce each fact once.
Quotation is a D67 bounded card with square solid panel/border chrome and no
gradient/shadow. D60 keeps typography fixed. D172/D174/D176 remain allowed but
cannot duplicate quotation/attribution text. Unfittable content strict-fails or
becomes complete sequential blockquotes non-strict. Migration requires body and
attribution to be separable without heuristic guessing.

### D203 — Evidence-led slides use `evidence_review`

`evidence_review` contains 1–6 ordered findings, each with stable `finding_id`,
exact non-empty statement, and 1–4 ordered duplicate-free `evidence_ids`. Every
reference resolves through D175 and belongs to the slide's evidence references.
Each D67 bounded card paints the finding once and resolved source names in order;
IDs, locators, paths, and filenames never paint. The renderer does not extract,
judge, summarize, parse colon bullets, or treat filenames as labels.
`source_footer` is invalid because cards own visible sources; a slide conclusion
uses D172. D59 adaptive 22–28px prose applies. Unfittable content strict-fails or
becomes a complete diagnosed sequential evidence list non-strict. Unresolved
references strict-fail; non-strict drops bad references and, when none remain,
preserves the statement in a visibly diagnosed “Source unavailable” item rather
than presenting unsupported evidence. Migration requires explicit registry
mapping and exact finding text; filenames/EIDs/inferred summaries/ambiguous
bullets require human resolution.

### D204 — Risks and opportunities use `risk_opportunity_review`

`risk_opportunity_review` requires 1–6 risks and 1–6 opportunities. Every item
has a collection-unique stable ID, exact non-empty statement, and optional
detail. Groups retain independent author order; the renderer never pairs, ranks,
scores, or balances by index. Renderer-owned headings identify both roles, so
meaning never depends on color. Items use D66–D67 bounded chrome; any theme
accent retains a non-color role label. Likelihood, impact, priority, mitigation,
upside, and sentiment are never inferred. Charts, arbitrary icons/colors,
coordinates, and CSS are invalid. D59 adaptive 22–28px prose applies; D172 and
D174 remain allowed. Unfittable content strict-fails or becomes two complete
diagnosed accessible sections non-strict. Missing groups/malformed items strict-
fail; non-strict drops bad items individually and visibly marks an empty
unresolved group without invention. Migration requires explicit role
classification, never position or tone inference.

### D205 — Recommendations use `recommendation_case`

`recommendation_case` requires one exact non-empty recommendation and 1–6
ordered rationales, each with stable `rationale_id`, exact statement, and
optional detail. Recommendation and rationales use distinct D66–D67 bounded
chrome with renderer-owned role labels. The renderer never rewrites, synthesizes
“because,” ranks rationales, or infers priority, owner, timing, status,
confidence, or sentiment. Evidence remains slide-level under D175; no per-
rationale relationship is inferred. Charts, arbitrary icons/colors, scores,
coordinates, and CSS are invalid. D59 adaptive 22–28px prose applies. D172 is
invalid because the recommendation already owns the concluding action; D174 and
D176 remain allowed. Unfittable content strict-fails or becomes a complete
diagnosed sequential fallback. Malformed rationales strict-fail; non-strict
drops them individually but preserves a recommendation with no valid rationale
as visibly unresolved rather than inventing support. Migration requires one
clear recommendation and explicit rationale boundaries.

### D206 — Transformations use `state_transition`

`state_transition` requires ordered `before` and `after` state surfaces, each
with a non-empty heading and 1–4 D181 paragraph/bullet blocks. Renderer-owned
accessible role labels distinguish the states; authored headings describe them.
Blocks are not paired by position; row-wise facts use D187 or D183. Optional
`transition_steps` contains 1–4 compact D192-style authored steps and is never
derived from state differences. The renderer calculates no deltas, improvement,
sentiment, or assumption that after is better; arrows are structural chrome
only. States use D66–D67 bounded chrome and D60 fixed first-delivery typography.
D172/D174 remain allowed. Unfittable content strict-fails or becomes a complete
diagnosed sequential fallback preserving both states and all steps non-strict.
Migration requires explicit state/step boundaries; bullet-halving or sentiment
classification requires human resolution.

### D207 — Directional KPIs are explicit `metric_overview` change semantics

D189 metric items may carry optional `change` with authored `direction` (`up`,
`down`, `flat`), exact non-empty comparison `basis`, optional D143/D188 change
value, and optional authored tone (`positive`, `negative`, `neutral`). Direction
and tone are independent and never inferred from signs, labels, values, or
business meaning. Renderer-owned shape plus accessible wording conveys
direction; color may reinforce tone but never carry it alone. Base and change
values use independent declared formats. Sparklines, inferred trends, arbitrary
arrows/icons/colors, and CSS are invalid. D152 metric stacks and D165 strips
remain directionless. Malformed change strict-fails; non-strict diagnoses and
drops only the change while preserving the base metric. Legacy KPI trend cards
migrate only with explicit direction and comparison basis; isolated arrows or
`trend` values require human resolution.

### D208 — `comparison_cards` is the sole peer-comparison composition

Schema v1 removes `comparison_grid`, `comparison_with_metrics`, and
`three_column_comparison` as separate layouts. D187 `comparison_cards` owns every
peer fact—including metrics—through shared D141 fact columns; D172 may summarize
the comparison. Detached metric strips, authored circle/ratio graphics, duplicate bullets,
and secondary fact sources are invalid. A renderer-owned circular dual-metric
visual may be derived from two numeric facts plus one `Nx` multiplier (D261). Metrics that cannot map consistently to
every peer use D189 when primary or another semantic composition/slide when
independent. The renderer never aligns orphan facts by position, label
similarity, or count. Migration requires one canonical complete peer-row/shared-
role source; ambiguous detached metrics require human resolution. D187's
complete accessible table is the non-strict fallback and never drops unmatched
facts.

### D209 — Prose emphasis uses typed inline runs, never Markdown

Only prose contracts that explicitly opt in may use ordered inline runs,
initially D181 narrative paragraphs/bullets, D189 detail blocks, D193 milestone
details, D202 quotation paragraphs, and D206 state blocks. Each run has non-
empty text and optional `emphasis: strong`; empty or adjacent same-state runs are
invalid rather than silently merged. Concatenated text is authoritative wording
and accessibility text. Emphasis changes weight only and cannot encode semantic
status, links, units, evidence, or hidden meaning. Headings, labels, values,
notes, disclosures, legal text, sources, and chart/table text remain plain unless
a later contract opts in. Markdown, HTML, links, underline, italics, colors,
font sizes, line breaks, and arbitrary spans are invalid. Strict rejects
malformed runs; non-strict concatenates valid text as diagnosed plain text
without dropping wording. Migration converts only balanced unambiguous existing
`**strong**`; all other markup requires human resolution.

### D210 — Schema v1 closes the composition vocabulary

Authored `layout_type` permits exactly 29 compositions: `opening_cover`,
`section_divider`, `closing_cover`, `single_chart`, `dual_chart`,
`chart_hero_dual`, `data_table`, `annex_table`, `grouped_annex_table`,
`period_comparison`, `comparison_cards`, `metric_overview`, `narrative`,
`legal_notice`, `process_flow`, `timeline`, `decision_tree`, `feedback_loop`,
`layered_architecture`, `data_pipeline`, `hierarchy`, `stakeholder_map`,
`quadrant_matrix`, `feature_cards`, `quotation`, `evidence_review`,
`risk_opportunity_review`, `recommendation_case`, and `state_transition`. Chart
families are nested typed chart visuals; hero/support types are nested surfaces.
Legacy aliases, chart-named roots, generic split/freeform/multi-panel/comparison,
and catch-all layouts disappear. D180's unresolved slide is internal non-strict
output only. Unknown compositions strict-fail or become that typed unresolved
slide non-strict without guessing. The typed discriminated union alone generates
D121's JSON Schema and layout catalog. Migration records one disposition for
every recognized legacy layout: deterministic target, human decision, or
removed. Adding a composition after schema-v1 publication requires schema v2.

### D211 — Schema v1 has one minimal top-level deck envelope

The canonical handoff has exactly `meta`, `sections`, `number_formats`,
`evidence_registry`, and `slides`. `meta` contains only
`handoff_schema_version`; renderer version, timestamps, paths, authoring-tool
state, and arbitrary metadata are not handoff content. The two registries and
sections array follow D144, D175, and D178, and `slides` is a non-empty authored-
order array of D210's discriminated union. Every collection is present even when
empty. There are no deck-wide defaults, inheritance, `presentation`, `theme`,
`config`, `assets`, or extension dictionaries; D128's fixed theme remains
renderer configuration, and the opening cover—not metadata—owns any visible
deck title. D121's generated schema derives the complete closed envelope.
Migration removes only mechanically recognized legacy presentation/theme data;
unknown or potentially meaningful top-level data requires human resolution.

### D212 — Slides use one closed common envelope plus one typed payload

Every slide requires a positive deck-unique integer `slide_number`, one D210
`layout_type`, and exactly one layout-specific typed payload; number is stable
authored identity while array order is presentation order. Ordinary slides also
require D178 `section_id` and D171 `title`. Optional common `content` contains
only subtitle and its D41 typography. Other common optionals are D172 takeaway,
D174 disclosure, D173 notes, D175 evidence IDs, and D176 source footer, subject
to each composition's applicability rules. Absent data is omitted; null, empty
strings/arrays/objects are invalid placeholders. Semantic payload names replace
generic visual specs, primary/secondary visuals, grids, and catch-all content.
Packing/source/purpose/renderer hints, coordinates, and arbitrary metadata are
removed. Forbidden fields are errors, never ignored. Strict reports all unknown
or inapplicable fields; non-strict applies only D123 repairs then revalidates.
D121 expresses discriminator-specific applicability.

### D213 — Non-plotted semantic values use one tagged union

All D143 values use exactly four tagged forms: `number` with canonical-decimal
`value` and required `format_id`; D188 `range` with canonical `lower`/`upper` and
required shared format; exact non-empty plain `text`; or fieldless `missing`.
The union is shared across tables, metrics, driver/context/comparison facts, KPI
changes, and all other non-plotted values. Primitive strings/numbers, null,
booleans, and shape inference are invalid. Text is never parsed/formatted as a
number, and formats are forbidden on text/missing. Missing stays visibly and
accessibly distinct from zero, empty text, and N/A. D135 chart geometry retains
its separate positional numeric model, excluding ranges/text. Strict rejects
malformed values; non-strict substitutes diagnosed `missing` in place so the
containing surface and neighboring content retain position. D121 defines this
union once; compositions cannot add private variants.

### D214 — Number formats are closed declarative registry entries

Each D144 registry key is its deck-unique D115 `format_id`; entries contain
optional typed `unit`, required `value_decimals` 0–4, optional `tick_decimals`
0–4, required `negative_style` (`minus`/`parentheses`), optional positive
canonical-decimal `value_scale` defaulting to 1, and `scale_label` required
exactly when scale differs from 1. Unit requires short plain text,
`prefix`/`suffix`, `none`/`space`, and accessible name; it never rescales.
Grouping, decimal point, rounding, trailing zeros, negative zero, locale, and
scientific notation remain renderer-owned. One format has one meaning globally;
formatter templates/callbacks/locales/HTML/CSS are invalid. Invalid entries
strict-fail before planning; non-strict drops the complete entry and converts
references to diagnosed D213 missing rather than guessing. Scale disclosure
paints/associates once per owning axis or table/metric surface under D90/D145.

### D215 — Sections are an ordered, fully used registry

Each D178 section has exactly one D115 `section_id` and exact non-empty plain
label; IDs and normalized labels are deck-unique and registry order is
authoritative. Every ordinary slide references one registered section, each
section's slides form one contiguous run, and every registry entry owns at least
one ordinary slide. An optional `section_divider` references the section it
introduces, appears immediately before its first ordinary slide, and occurs at
most once per section. Covers omit section identity and no label paints outside
an explicit divider. Strict rejects missing/duplicate/unused/unknown/out-of-
order relationships. Non-strict preserves slide order and uses D178's diagnosed
positional identities without merging, reordering, or inventing meaning. An
empty registry is valid only when no slide requires a section.

### D216 — Evidence registry stores minimal deck provenance

Each D175 registry key is the D115 evidence ID; entries contain exactly required
non-empty plain `source_name` and optional opaque JSON-object `locator`.
Source name is human-readable citation text, not a path or inferred filename;
multiple entries may share it. Locator is deterministically preserved in
`evidence_manifest.json` but never interpreted, painted, fetched, executed, or
rewritten. It must be bounded finite JSON; HTML, callbacks, binary, and non-JSON
values are invalid. Full upstream Evidence Entry claims, scoring, confidence,
narrative, and extraction metadata stay outside the renderer handoff. Every
entry must be slide-referenced. Strict rejects malformed/unused entries;
non-strict drops unused entries and malformed locators while retaining entries
with valid names. Legacy EIDs require explicit D115 mapping and only clear
source/locator meanings migrate. D113 serialization sorts locator object keys
without changing arrays or scalar values.

### D217 — Evidence links and source footers use bare ID arrays

Slide `evidence_ids` and `source_footer` are ordered duplicate-free arrays of
D216 registry IDs with no wrappers or inline names. Either is omitted when
unused; null and empty arrays are invalid. Evidence IDs contain every slide link
and persist in `evidence_manifest.json`. Source footer contains 1–4 IDs, all
present in the same slide's evidence IDs, resolving to normalized-unique source
names painted once in authored order; IDs and locators never paint. Strict
rejects unresolved/duplicate/non-subset references and duplicate visible names.
Non-strict drops invalid references and later duplicate footer names with
diagnostics, omitting an empty repaired footer. Footers are never inferred from
evidence links. This supersedes D212's illustrative source-footer wrapper.

### D218 — Typography uses one closed surface-local control object

Every typography-capable surface may carry one closed `typography` object;
omission means adaptive mode. Mode is `adaptive` or `fixed`, and legacy `auto`
disappears during migration. Applicable whole-pixel overrides use only D45's
role vocabulary. In adaptive mode, authored sizes pin only their roles while
omitted roles grow; in fixed mode, omitted roles retain renderer defaults
without growth. D49/D51 bounds apply. `sync_group` is adaptive-only and
synchronizes equivalent automatically sized roles; pinned roles neither
constrain nor inherit. Unknown/inapplicable fields invalidate the whole object
under D28. Invalid cross-role membership strict-fails or is removed with a
non-strict diagnostic so the surface sizes independently. Canonical authoring
omits empty/default-only objects. Inheritance, deck defaults, scale factors,
responsive units, CSS, and breakpoint values are forbidden. The frozen plan
records resolved sizes and runtime JavaScript cannot revise them.

### D219 — Root `content` is only the under-title subtitle surface

Ordinary-slide `content` is optional and valid only where the composition
permits a root subtitle. When present it requires exactly one non-empty plain
`subtitle`; optional D218 typography is restricted to mode, sync group, and
subtitle size and cannot exist without subtitle. Root title remains required
and has no authored typography. Headline/dek/body/bullets/key stats/so-what/
narrative bridges and arbitrary prose belong in typed payloads or D172, never
content. A normalized subtitle duplicate of title strict-fails or is omitted
with a D97 non-strict diagnostic. Empty/whitespace, arrays, rich runs, Markdown,
and HTML are invalid. Cover-specific or subtitle-prohibiting compositions reject
content. Omit content entirely when no subtitle exists.

### D220 — Slide takeaway is one typed bounded prose surface

Optional D172 `takeaway` is allowed only by explicit compositions and requires
one non-empty plain `text`. Optional D218 typography permits only mode, sync
group, and body size. The renderer supplies accessible “Key takeaway”; authors
cannot add heading, tone, icon, color, evidence links, layout hints,
coordinates, rich text, Markdown, or HTML. Text is exact and paints once after
the main composition; it may wrap/grow but never abbreviates, ellipsizes,
splits, suppresses, or moves slides. Evidence remains slide-level. D97 handles
normalized duplicate prose: strict rejects, non-strict preserves the higher-
priority owner and diagnoses omission. Floor overflow strict-fails before output
or non-strict paints complete floor-sized text with D59 diagnosis. Omit when
absent; strings, null, and empty objects are not shorthand.

### D221 — Speaker notes remain one exact root plain-text string

Optional root `speaker_notes` is one non-whitespace plain string, never an
object, paragraph array, or rich-text model. Wording, Unicode, whitespace, and
paragraph breaks are preserved exactly; the renderer never trims, cleans,
joins, truncates, summarizes, synthesizes, or moves notes. Markup, IDs, stage
directions, and executable-looking text remain literal and are safely escaped
in HTML. Notes do not affect visible planning, diagnostics, evidence, or capture
readiness. HTML notes and the notes artifact derive from the same canonical
string. All slide classes may carry notes. Empty/non-string notes fail in both
strict and non-strict modes rather than being deleted or stringified. Migration
copies genuine presenter notes exactly; operational comments, renderer
instructions, fidelity grades, and pass names require human resolution.

### D222 — Disclosure uses ordered native-detail sections

D174 `disclosure.sections` contains 1–4 ordered sections, each with deck-unique
D115 `surface_id`, normalized-unique non-empty plain title, and 1–6 ordered
items. An item is exactly a non-empty plain `paragraph` or `bullet`; consecutive
bullets form one native list without changing order. One section renders one
native details block; multiple sections render an ordered details accordion
without single-open enforcement. Screen state starts closed with no author
control; print/static expands all, and no-JS remains complete and operable. DOM
IDs derive from slide number plus surface ID, never UUIDs. Text paints and is
announced once. Markup/rich runs/nesting/links/style/icons/interaction settings
are invalid. Critical facts remain authoring-review responsibility and cannot be
hidden here. A malformed item invalidates its section: strict rejects the
complete disclosure; non-strict drops that section diagnostically and omits an
empty repaired disclosure. Empty/null and legacy pattern/open controls fail.

### D223 — Brand slides use closed renderer-owned payloads

`opening_cover` and `closing_cover` each require `cover` with exact non-empty
plain title plus optional separate subtitle, period label, and date label; the
renderer never parses, combines, reformats, or infers them. Cover title owns the
accessible deck/closing title with no duplicate root/metadata title. At most one
opening cover is first and one closing cover is last. `section_divider` requires
only `divider.section_id`; visible wording comes exactly from D215 and cannot be
overridden. Dividers remain optional under D215 placement. The renderer owns all
Amex marks/colors/bands/lockups; authored marks, SVG, tone, style, and assets are
invalid. Root content, takeaway, disclosure, and source footer are forbidden;
D217 evidence links and D221 notes remain allowed. Missing optionals are omitted.
Malformed payloads strict-fail or use D180's unresolved non-strict fallback
without invented title, brand wording, or section meaning.

### D224 — Rich-capable prose uses one canonical run-list shape

Every D209-capable prose value is an object with non-empty ordered `runs`; each
run has required non-empty text and optional `emphasis: strong`, with omission
meaning ordinary text. This applies only to explicitly opted-in narrative/list,
metric-detail, timeline-detail, quotation, and state prose. Authors own spaces
and punctuation at boundaries; exact concatenation is authoritative wording and
accessibility text. Empty runs, adjacent equal-emphasis runs, and string
shorthand are invalid; ordinary prose uses one ordinary run. Non-opted fields
remain plain strings. Runs forbid line controls, markup, links, colors, sizes,
and semantic status. Rendering escapes each run and announces concatenated text
once. Strict rejects malformed runs. Non-strict may flatten complete valid
wording to diagnosed plain text only when emphasis structure alone is malformed;
missing/invalid wording triggers the containing composition fallback. Separate
size limits never rewrite authored text.

### D225 — `narrative` uses typed paragraph and bullet-list blocks

`narrative.blocks` contains 1–4 ordered blocks with slide-unique D115 block IDs.
A block is exactly `paragraphs` with 1–6 D224 prose values or `bullet_list` with
1–8 D224 values and carries only its type-specific field. Root title and D219
subtitle own headings; blocks cannot add them. Optional payload D218 typography
permits mode, sync group, and body size, with one resolved 22–28px size across
all blocks. Blocks paint vertically at full usable width in authored order;
columns, grids, sidebars, cards, icons, numbering, nesting, and alignment flags
are invalid. The renderer never merges/splits/reorders/rewrites content. Fit
failure strict-fails before emission; non-strict preserves every block at the
22px floor in a diagnosed sequential overflow fallback without dropping or
moving text. Applicable D212 common fields remain. Migration requires
mechanically unambiguous paragraph/list boundaries.

### D226 — `legal_notice` owns one immutable contiguous notice sequence

`legal_notice` requires D115 `notice_id`, positive `part` and `total_parts`, and
1–6 exact non-empty plain paragraphs. One notice's adjacent slides share total
and cover exactly 1..total with no gaps/duplicates. Part 1 alone requires exact
plain title; later parts forbid authored titles and receive renderer-derived
accessible continuation wording. Legal prose forbids D224, bullets, markup,
automatic splitting, rewriting, normalization, and truncation. Section ID is
required; root title/content/takeaway/disclosure/source footer are forbidden,
while evidence links and notes remain allowed. Typography is fixed and has no
author object. Authors own paragraph pagination. Strict rejects broken sequence,
misplaced title, or fit failure. Non-strict preserves authored order and every
valid paragraph in a visibly diagnosed legal fallback without inventing parts
or reconnections. Migration requires exact boundaries/order; ambiguous
continuations require human resolution.

### D227 — Charts use one common envelope plus one family payload

Every chart requires deck-unique D115 `surface_id`, one D138 `chart_type`, and
exactly one family payload; a redundant `type: chart` is omitted in typed chart
slots. Common optionals are composition-governed heading/subtitle, chart data,
semantic axes, display, typography, context labels, annotations, measurements,
category groups, auxiliary series, and coverage callout. Family applicability
is strict: axis charts require data/axes, heatmaps use D163 table/scale,
waterfall roles and combo bar mode stay family-local, and coverage applies only
to stacked bars. Absent fields are omitted; null/empty placeholders fail.
`chart_config` disappears: display and typography live directly on chart while
other behavior uses explicit semantic fields. No common data/fact/policy may be
duplicated in family payloads. Each chart emits D106 and one frozen surface-ID
plan. Unknown/inapplicable fields strict-fail; non-strict uses only D123 repairs
then canonical paint or complete pane-local semantic-table fallback. D121 uses
closed chart-type discriminator branches.

### D228 — `chart_data` uses exact positional arrays and decimals

D135 chart data requires ordered non-empty categories and series. Categories
have collection-unique D115 ID, exact non-empty label, and optional authored
short label. Series have collection-unique D115 ID, normalized-unique name, and
one position-aligned canonical-decimal string or null per category. JSON
numbers/booleans/decorated strings/coercion are invalid in v1; D91 JSON-number
acceptance is narrowed to unambiguous offline migration. Null retains position.
Optional color uses D130–D132. Line styles require a complete D133 style/marker
pair and are invalid for bars. Combo adds mark type and optional primary-default
axis key. Units/precision/scaling/negative style remain axis-format owned.
Parallel arrays, primitive categories, headers, transposition/list inference,
per-point colors/formats are invalid. Strict rejects malformed/ragged data;
non-strict applies only D93/D123 positional padding, surplus omission, and
diagnosed positional IDs without shifting values or inventing labels. Family
count/arrangement rules remain separate.

### D229 — Category axes expose only visibility and optional title

Every line/bar/combo/waterfall axis chart requires `category_axis` with explicit
boolean `visible`; migration writes true when legacy input omits it. Optional
title is exact non-empty plain text. Visible paints line/ticks/labels/title;
hidden removes visual chrome while D106/accessibility retain all categories.
Hidden is valid only when another visible chart or category-aligned support owns
every category under D86. Otherwise strict rejects or non-strict restores the
axis visibly with diagnosis. Category identity/order/text comes only from D228.
Rotation, wrapping, skipping, ellipsis, and placement are renderer-owned frozen
adaptations. Reversal, sorting, scale type, tick lists, captions, formatting,
offsets, and styling are invalid. Horizontal charts map the same semantic axis
to physical vertical; heatmaps use D163 and reject this object.

### D230 — Value axes use explicit format, visibility, and domain policy

Every axis chart requires primary value axis; secondary is combo-only and must
be series-referenced. Each requires explicit visibility, valid D214 format ID,
and `generated` or `fixed` domain, with optional exact plain title. Generated
allows optional canonical min/max and target ticks 2–8. Fixed requires min/max
and 2–8 strictly increasing canonical ticks normally spanning both endpoints.
D157 leading break is the explicit exception: min < break target, first visible
tick equals target, and last equals max. All declarations remain source-space;
display scale is format-owned. D83 contains values/stacks/totals/required zero.
Hidden axes retain semantics/format but permit only generated domain without
tick target. Generated may add label headroom; fixed remains authoritative.
Breaks are line/horizontal-bar only. Format solely owns units/precision/sign/
scale. Reversal/log/callback/grid/style/orientation aliases are invalid. Invalid
domain/break strict-fails or non-strict becomes diagnosed safe generated domain.
Missing/invalid format strict-fails or uses D102 pane fallback with exact source
decimals and unresolved-format diagnosis, never guessed formatting.

### D231 — Chart display policy uses one sparse enum object

Optional `display` is sparse deliberate overrides; omission applies family
rules: ordinary line/combo-line/non-stacked bar values show, stack segments and
totals hide, and series identity is auto. Empty/default-equal entries are
invalid canonical noise. Policies use enums, never booleans. Ordinary values
show/hide line points and non-stacked/grouped bars. Stack segment/total fields
are show/hide only for stacked bars or stacked combo; authored stack totals
imply visibility and contradict hide. Display cannot hide waterfall structural
labels, boxed/context/measurement/annotation/coverage facts, categories, or
semantic tables. Series identity is auto, complete legend, or D139-valid headed
single-series pane title. Inapplicable/incomplete/multi-series pane-title policy
strict-fails; non-strict discards the whole malformed object for diagnosed
family defaults under D28. Legacy booleans migrate only unambiguously. Runtime
cannot revise the frozen policy.

### D232 — Context labels are chart-local typed facts

Optional `context_labels` contains 1–4 authored-order entries with chart-unique
D115 context ID, exact non-empty label, D213 value, and optional exact short
label. Stable identity is surface/context; context IDs need not be independently
deck-unique. Formats govern numeric/range values, text remains exact, and
missing remains visibly/accessibly missing. Short labels substitute only visible
labels under D30 pressure and never identity/accessibility/value. Facts are
unplotted, domain-neutral, and cannot act as series/legends/annotations/
measurements/subtitles. They paint in D30's shared lane and appear exactly once
in D106. D97 suppresses only duplicate chrome with both owners diagnosed.
Styling/position/alignment/icons/colors/priority/sorting/metadata are invalid.
Omit when unused. Strict rejects malformed entries; non-strict drops them
individually and omits an empty repaired field. Fit moves the complete surviving
block below the plot rather than dropping facts.

### D233 — Annotations use four closed semantic anchor types

Optional `annotations` contains 1–8 authored-order entries with chart-unique
D115 ID, role event/explanation, exact non-empty plain text, and one anchor;
stable identity is surface/annotation. Anchors are `chart` with no extras,
`category` by category ID, finite `data_point` by series/category IDs, or an
inclusive authored-order `category_range` of at least two categories. Events
cannot be chart-wide; explanations may. Singletons use category. Quantitative
change/CAGR uses D148 and label/value facts use D232, without role duplication.
Text is plain/complete with no rich/short form. Order only breaks placement ties.
Renderer owns placement/collisions/leaders/accessibility wording. Coordinates,
offsets, sides, style, icons, HTML/CSS/metadata are invalid. Every fact appears
once in D106; D97 may suppress chrome only. Strict rejects malformed/unresolved
or required-unplaceable chrome. Non-strict preserves the fact in D106, omits
only failed chrome, and diagnoses. Omit when unused; empty arrays fail.

### D234 — Measurements carry one exact typed quantitative fact

Optional `measurements` contains 1–4 authored-order entries with chart-unique
D115 ID, role change/CAGR, valid series ID, inclusive authored-order category
range spanning at least two finite endpoints, canonical-decimal value, valid
D214 format, and explicit approximate boolean. Stable identity is
surface/measurement. Renderer never recomputes/verifies authored values because
period/adjustment methodology may be external. Change derives only sign-based
direction, never sentiment; CAGR owns annualized meaning without a duplicate
flag. Approximation wording is renderer-owned rather than embedded in value.
Format owns unit/precision/scale/sign. Measurements are unplotted/domain-neutral;
renderer chooses rule/bracket/elbow chrome by family/geometry. Each appears once
in D106 with role/endpoints/approximation/value. Duplicate semantic role-series-
range measurements are invalid. Strict rejects malformed/duplicate/unplaceable
required chrome. Non-strict keeps the complete D106 fact, omits failed chrome
with diagnosis, and never recalculates/drops it. Omit unused; empty arrays fail.

### D235 — Auxiliary series are role-specific category-aligned facts

Optional `auxiliary_series` has at most one boxed-label and one authored-total
entry. Each has chart-unique D115 ID, exact label, valid D214 format, and one
canonical decimal/null per D228 category; stable identity is surface/auxiliary.
Boxed label requires target bar-series ID and applies only to non-stacked grouped,
horizontal, or grouped-combo bars with D52 placement. Authored total forbids
target, applies only to stacked bars/combos, implies visible totals, and is
segment-visibility independent. Neither changes bar geometry; boxed labels are
domain-neutral, while totals participate in D83/D82 containment/gutters.
Null keeps its slot, paints no label, and is Missing in D106. Totals are
authoritative and are not rejected for differing from component sums. D106 owns
each fact once. Short/text/per-category formats/style/color/coordinates/
visibility are invalid. Strict rejects family/role/target/format/count errors.
Non-strict permits only D93 pad/surplus repair; otherwise uses complete pane
semantic fallback rather than dropping facts. Omit unused; empty arrays fail.

### D236 — Stacked-bar coverage uses one numeric semantic callout

At most one `coverage_callout` is valid, only on stacked bar (not combo). It
requires chart-unique D115 ID, exact non-empty label, D213 number value, and
optional exact period; stable identity is surface/callout. Range/text/missing
are invalid. Label/period stay separate, with no authored line breaks or unit in
the numeric value. D214 formats value and D50 owns fixed chrome. The fact is not
category/series/annotation/legend/subtitle/context and changes neither stack
geometry nor domain. It shares D30's exterior lane: direct segment identities
stay nearest stacks and width reclaims only to D47's floor. Side-lane failure
strict-rejects or non-strict moves the complete callout below the plot with
diagnosis. D106 contains it once. Style/placement/skin/color/font/wrap/
coordinates/icons/label-line arrays are invalid. Legacy conflated objects
migrate only when value, label, unit, and period separate mechanically;
otherwise human resolution is required.

### D237 — Category groups reference contiguous category IDs

Optional `category_groups` contains authored groups with chart-unique D115 ID,
exact label, ordered non-empty D228 category IDs, and optional exact short label;
stable identity is surface/group. References must exist, be contiguous, and
follow chart order; groups themselves follow first-category order, cannot
overlap/nest, may leave categories ungrouped, and may contain one category.
First delivery permits groups only on bar-bearing grouped/stacked/horizontal/
combo charts. Groups express hierarchy only and never aggregate/reorder/change
domains or replace category labels. Renderer owns bracket/header chrome and
accessibility; short text is visual-only under fit and D106 retains full group
membership. Style/coordinates/index spans/depth/aggregates/children are invalid.
Strict rejects reference/order/overlap/nesting/family errors. Non-strict keeps
chart data, removes each malformed group and all groups participating in a
conflict (no first-wins), and preserves unresolved hierarchy in D106 with
diagnostics. Omit unused; empty arrays fail.

### D238 — `chart_type` is the sole chart-family discriminator

`chart_type` alone selects one closed D121 branch; there is no nested family,
line/bar/waterfall/heatmap wrapper. Line and bar families directly use D228–D230;
combo additionally owns bar arrangement; waterfall directly owns typed steps;
heatmap directly owns D163 table/scale instead of axis-chart fields. D227 common
fields remain direct. Families without extra controls gain no empty marker
object. Cross-family fields are applicability errors. Internal model reuse is
allowed but the public generated schema is the closed discriminated union. This
clarifies D227's “family payload” as a family schema branch, not a nested field.
Legacy nesting/config flattens only when unambiguous.

### D239 — Line charts are straight marker-based single-axis trends

Line requires at least two categories and 1–4 series, each with at least two
finite values. All share primary value axis/format; dual/mixed charts use combo.
Finite adjacent points connect by straight segments; null breaks paths without
interpolation. Every finite point gets D62 fixed renderer-owned marker geometry.
D231 ordinary values show by default and D34–D36/D53 govern placement and
suppression. D37 chooses all endpoint identities or one complete legend, with
headed single-series pane-title option. Complete valid D133 styles/colors win;
otherwise D43/D99 assigns deterministic identities. D157 primary leading break
and common contexts/annotations/measurements remain valid. Groups, auxiliaries,
coverage, stacks, secondary axes, smoothing/splines/steps/interpolation, area or
confidence fills, calculated trends, and per-point style are invalid; area/band
semantics require a future measured contract. Chart.js/SVG preserve points,
gaps, identities, values, placement classes, and D106. Invalid cardinality/
family fields strict-fail or use complete D102 fallback without deleting series,
joining gaps, or painting one-point pseudo-trends.

### D240 — `grouped_bar` uses vertical zero-baseline bars

Grouped bar has 1–12 categories and 1–4 series; one series is valid. Bars are
vertical side-by-side in authored series order. Every finite value paints from
semantic zero: positive up, negative down, zero as real zero-height mark with
label, null as empty positional slot. Primary domain must include zero; D160 owns
width/spacing/pitch/sibling geometry. D71–D73/D231 show ordinary labels beyond
ends by default. Multi-series always uses one complete authored-order legend.
Single-series may use valid pane-title ownership; otherwise one-item legend.
D237 groups and targeted D235 boxed labels are valid. Stack totals, coverage,
segment labels, stacking, secondary axes, breaks, per-bar colors, variable/
floating/range bars, and horizontal orientation are invalid. Valid annotations/
measurements remain. Chart.js/SVG meet D160 2px geometry and match placement,
identity, missing slots, and D106. Invalid counts/domain/family fields strict-
fail or use D102 complete fallback without dropping/stacking/altering domains.

### D241 — Authored stack totals are label facts, not axis coordinates

D235 authored stack totals may use a format different from the plotted axis,
including dollar totals on percentage stacks. They are category-aligned semantic
labels: never domain inputs, never required to equal segment sums, and never
positioned through the value scale. Renderer anchors each at the completed
stack's outer edge and reserves D82 clearance. For mixed-sign stacks, positive
or zero totals sit above positive extent and negative totals below negative
extent, with a leader when ownership is ambiguous. Null keeps a Missing D106
slot and paints no label. D83 applies to plotted values and stack extents, not
authored totals; this supersedes D235's containment sentence, while D82 planning
still applies. Computed totals remain separately derived from plotted source
values. Chart.js/SVG share anchor class and formatted text.

### D242 — `stacked_bar` uses vertical signed stacks with independent labels

Stacked bar has 1–12 categories and 2–6 series. Vertical positive and negative
segments accumulate separately from zero; author series order is bottom-to-top
within each sign. Null preserves its segment slot and invalidates the computed
total for that sign/category. Primary shared-format domain includes zero and
both extents. One complete authored-order legend is mandatory; exterior direct
segment names are not separately authored. D231 independently defaults segment
and total labels hidden. Visible segments derive axis formatting, remain inside
only when contrast/fit works, otherwise move outside with series connector/navy
text, and are not dropped merely for size. Computed totals sum source values by
sign, yielding separate positive/negative totals and withholding a side with a
missing contributor. D235/D241 authored totals imply totals, replace computed
labels for their category, and remain one authored fact. D236 coverage and D237
groups are valid. Boxed/ordinary labels, secondary axes, breaks, arbitrary stack
IDs/style/placement, horizontal orientation, and variable widths are invalid.
D160/Chart.js/SVG preserve geometry within 2px, order, signed stacking, label
classes, totals, missing state, and D106. Invalid counts/format/axis/family
strict-fail or use complete D102 fallback without dropping/grouping/invention.

### D243 — `horizontal_bar` is grouped-only with an optional leading break

Horizontal bar has 1–12 categories and 1–4 series and never stacks. Categories
run top-to-bottom; series within each category follow authored top-to-bottom
order. Without D157 leading break, finite bars start at semantic zero, positive
right/negative left, and domain includes zero. With a break, every finite value
lies beyond its target on the same positive side; mixed-sign/negative-only data
are invalid, visible bars start at the disclosed boundary while labels/D106 keep
full values, Chart.js/SVG show equivalent break chrome, and omitted zero has no
zero line. Null preserves a slot; zero is real data without a break. D160 owns
thickness/gaps/pitch/synchronization. D71–D73/D231 show values beyond ends.
Multi-series requires one complete authored-order legend; single-series may use
valid pane-title ownership or a one-item legend. D235 boxed labels, D237 groups,
and common contexts/annotations/measurements are valid. Stacks/totals/coverage,
secondary axes, floating/range/variable bars, vertical orientation, arbitrary
positioning, and per-bar style are invalid. Chart.js/SVG meet D160's 2px bound
and preserve order, break disclosure, labels, missing slots, identity, and D106.
Invalid counts/break/domain/family strict-fail or use D102 complete fallback
without silently removing the break, changing values, stacking, or dropping.

### D244 — `combo` shares one category model across bar and line layers

Combo has 2–12 categories, 1–4 bar series with at least one finite value each,
and 1–4 line series with at least two. All use the exact D228 category sequence.
Required `bar_mode` grouped/stacked applies to every bar series; bars paint behind
lines and author order remains stable within each layer. Bars always use primary.
Lines all use primary when axis key is omitted or all use secondary; mixed line-
axis ownership is invalid. Secondary axis is required exactly for secondary
lines. Primary includes zero; secondary need not. D240/D242/D239 govern layer
semantics. Auto identity uses all fitting line endpoint identities plus a bar
legend, otherwise one complete all-series legend; forced legend is complete and
pane-title ownership is invalid. D231 governs grouped/line ordinary values and
stacked controls. Boxed labels apply only to grouped bars; authored totals only
to stacked bars. D237 groups and common contexts/annotations/measurements remain.
Coverage, breaks, horizontal/floating/range bars, per-series bar modes, arbitrary
stack IDs, and more than two axes are invalid. Chart.js/SVG preserve categories,
layers, axes, identity, labels, missing state, and D106. Invalid counts/axes/
family fields strict-fail or use D102 complete fallback without deleting layers,
changing axis ownership, or converting bar mode.

### D245 — Waterfall steps use a dedicated typed sequence

Waterfall uses `waterfall_data.steps`, not D228 series, with 2–12 authored-order
steps. Each has chart-unique D115 category ID, exact label, role change/total/
computed-total, and optional exact short label. Change requires signed canonical
decimal and advances the running level; total requires an absolute-level decimal
and resets it; computed total forbids value and paints the known running level.
First step is total and last is total/computed-total. Zero is real and never
means computation. Null is forbidden, superseding D162's missing-change branch;
unresolved movement uses semantic fallback or migration resolution. One primary
D214-formatted axis contains zero, all resets, and every intermediate level.
Theme owns increase/decrease/total colors, bridges, and semantic zero line.
Structural labels cannot hide/suppress/abbreviate. No legend; categories and
roles own identity. Common contexts/annotations/measurements remain, with the
reserved implicit series ID `waterfall` for point/measurement references.
Auxiliaries, coverage, groups, breaks, secondary axes, stacking, ordinary
display fields, arbitrary series/style are invalid. D106 records each role,
authored/computed value and running level. Chart.js/SVG match levels, resets,
bridges, labels, and D106. Malformed/unresolved arithmetic strict-fails or uses
complete D102 fallback without guessing, skipping, or partial painting.

### D246 — Heatmaps are visible semantic tables, not canvas charts

Heatmap uses D141 `table_data`, not chart data/axes, with 1–12 rows and 1–12
value columns fitting completely. Cells are only D213 number or missing; all
numbers share one D214 format, while text/range/mixed/empty are invalid. Scale is
generated or fixed canonical min<max containing every finite cell. Generated
all-equal maps all finite cells to palette midpoint and shows one exact-value
key. Renderer owns a monotonic light-to-primary-blue scale and contrast-safe
navy/white text. Missing is neutral em dash/“Missing”; every finite formatted
value is visible. D141–D143 own headers; authored colors/thresholds/bins/
gradients/cell style/icons/custom legends are invalid. One common adaptive
18–24px size applies without loss, and a scale key is mandatory when finite data
exists. The visible native HTML table is D106—no hidden duplicate, canvas, or
SVG painter—and is identical in settled/no-JS delivery. Context facts and chart-
wide explanation annotations are valid; point/range annotations, measurements,
auxiliaries, groups, coverage, axes, display, and series are invalid. No finite
cells or scale/format/count/fit errors strict-fail or paint the complete non-
colored diagnosed semantic table non-strict, never dropping/inventing cells.

### D247 — Every chart owns one reusable semantic-table DOM node

Each chart owns exactly one deterministic surface-derived table ID. The same
node is visually hidden/accessibility-visible normally and made visible in place
for D102; no second fallback table is generated. Visible headings/subtitles own
document structure and table references them instead of repeating text. Canvas,
SVG marks, visual legends/labels/annotations represented by the table are aria-
hidden to prevent duplicate announcements. Axis tables use authored category
rows and plotted-series then auxiliary columns with complete D214 text and em-
dash/“Missing” nulls; stacked tables add existing positive/negative computed-
total columns. Waterfall columns cover step, role, authored/computed value, and
running level. Heatmap reuses D246's visible table. A deterministic final chart-
facts section records axes/units/scales/breaks, groups, contexts, annotations,
measurements, then coverage using human wording without IDs. Visual adaptation
never changes table content. Tables are not focusable; marks stay out of tab
order and tooltips add no exclusive facts. Print/no-JS retains the same
accessible table with frozen visuals. Construction failure strict-emits nothing
or non-strict shows a diagnosed unresolved semantic table. IDs/order/wording are
D113 byte-stable.

### D248 — One chart artifact contains Chart.js and its no-JS SVG counterpart

One deck emits settled Chart.js plus a noscript SVG for each ordinary axis or
waterfall chart; heatmaps remain native HTML only. Both consume the same
canonical chart, D69 frozen plan, formatter, identity strategy, and D247 table.
Python fixes allocation, domains/ticks, text, identities/legend, collision
candidates/priorities, expected placement classes, typography, and diagnostics
before emission. Chart.js may use actual geometry only for D53 bounded candidate
selection/final pixels and cannot revise semantics, text, font, priority,
visibility, or synchronization; SVG applies the frozen decisions directly.
Existing family geometry/label tolerances apply. Both visuals are aria-hidden;
shared title/legend/context/support/table chrome stays outside noscript and is
not duplicated. Print shows Chart.js when settled or SVG without JavaScript,
never both. `suppress_features=["charts"]` remains development/test-only direct
SVG selection without changing validation/planning/semantics/diagnostics;
handoffs cannot choose a painter. Required-painter failure strict-emits nothing
or non-strict shows the D247 pane fallback. Acceptance compares both paths from
one render invocation, not separate handoffs or planning passes.

### D249 — Renderer 3.0 exposes one narrow deterministic public API

The new `impact_slides.renderer_v3` package exposes
`render_deck(handoff_path, out_dir, *, seed_path=None, debug=False, strict=True,
theme=None, chrome_level=None, delivery=SELF_CONTAINED, force_features=None,
suppress_features=None)` so intentional caller migration is an import-path change
rather than an interface redesign.
Strict is boolean/default true; debug adds deterministic inspection chrome only.
Accepted legacy-shaped values are seed/theme/chrome None, self-contained
delivery, no forced features, and suppression absent/empty or exactly charts for
D248 test/development SVG selection. Any other caller configuration raises typed
`RendererConfigurationError` in either mode; non-strict repairs handoffs, not
callers. CDN, seed evidence, token/theme overrides, minimal chrome, arbitrary
features and handoff painter choice are removed paths. Return retains applicable
operational keys and adds clean/degraded status, renderer/schema versions, and
deterministic severity counts; `errors` contains stable error diagnostic codes,
not free-form validator strings. Any failed strict or non-strict call raises the
applicable typed renderer error and returns nothing; `RendererValidationError`
covers unrecoverable handoff or planning failure while configuration/publication
use their D312 types. Runtime paths may reflect caller paths while artifacts obey
D113. CLI mirrors strict default, explicit non-strict, debug, and documented
`--svg-only`, with no CDN/theme/chrome/seed/arbitrary feature switches.
Deprecated kwargs remain only for clear typed rejection, not compatibility.

### D250 — Successful renders publish exactly five canonical artifacts

Output contains only `presentation.html`, `slide_notes.md`,
`evidence_manifest.json`, `run_meta.json`, and byte-copied
`handoff_schema_v1.json`. Presentation is LF UTF-8 self-contained with vendored
assets, D248 paths, deterministic IDs, no remote/environment/random data. Notes
follow authored slide order/headings and preserve exact D221 text, using
`_(no notes)_` only when omitted, without synthesis/reflow/evidence IDs. Evidence
manifest records versions/theme, ordered registry and slide number/layout/
section/evidence links plus canonical opaque locators; it excludes confidence,
synthesis/readiness/quality/source paths/inference. Run metadata records status,
versions/theme, count/layout order, byte counts, severity counts, full D110
events, frozen-plan summaries, static payload readiness and planned painter
semantic digests using stable IDs, without paths/times/host/user/process/
durations/random/cache data. D312/D315 own runtime browser readiness and measured
painter parity outside renderer output. Schema is the
checked-in D121 artifact byte-for-byte. No extra debug/seed/cache/CDN/temp/
screenshot/source-copy files; debug changes only HTML chrome and metadata. JSON
is LF UTF-8, two-space, one trailing newline, sorted where order is nonsemantic,
with authored arrays preserved. Publishing stages all five in a sibling temp,
closes/syncs, atomically replaces where possible or uses rollback-safe Windows
replacement, and cleans temps. Any failed strict or non-strict render leaves
prior output byte-identical; degraded non-strict rendering publishes all five
with diagnostics. Runtime results point only to
published artifacts.

### D251 — Every slide uses one uniformly named typed `payload`

Every slide has exactly one required `payload`; `layout_type` selects its closed
schema. No root layout-named properties (`single_chart`, `narrative`,
`legal_notice`, `cover`, `divider`) exist. Payload is not an extension bag:
D118 applies and D121 discriminates by layout type. Common slide fields remain
outside: number/type, applicable section/title, content, takeaway, disclosure,
notes, evidence IDs, and source footer. Composition-owned charts/support,
tables/cards, brand wording, narrative blocks, legal sequencing, processes/
timelines/diagrams and specialized data remain inside. D223 cover/divider, D225
narrative, and similar terms name payload schemas rather than keys; this
supersedes those key shapes. Non-strict unresolved slides retain a typed payload
containing only validated common prose and diagnostics, never rejected raw data.
Migration always emits payload and never legacy visual/content wrappers.

### D252 — `single_chart` has one chart and one optional typed support

Payload requires one complete D227 `chart` and permits one `support` discriminated
only by `support_type`: `support_table`, `outlined_support`, or `metric_strip`.
Legacy type/skin/layout wrappers are invalid. Both surfaces have distinct
D115 deck-unique IDs. Semantic order is chart heading/subtitle, chart plus its
D247 table, then support; support paints below the transparent borderless chart
without an outer frame or heading chrome. D10/D47 jointly preserve the 320x240
plot floor and all chart semantics, grow support typography before surplus chart
type, never suppress chart content to enlarge support, and leave whitespace only
when neither can usefully grow. Category-aligned supports match exact D228 IDs
and order; independent tables may differ; metric strips are never aligned.
Chart heading remains optional. Common slide fields stay outside payload.
Additional charts/supports, heroes/cards, implicit key stats, legacy visuals,
authored regions/ratios/coordinates/CSS are invalid. Strict rejects malformed or
unfit plans. Non-strict uses only D123 repairs, D166/D167 support fallbacks and
D102 chart fallback; if valid support facts cannot remain canonical, the whole
composition becomes D180 unresolved rather than chart-only. Migration requires
one unambiguous chart and at most one unambiguous support.

### D253 — `dual_chart` contains exactly two ordered charts

Payload `charts` is an exact two-item array of complete D227 chart surfaces;
order is left/right, reading/accessibility order, and positional fallback order.
Each requires distinct deck-unique surface ID and non-empty heading; subtitle
requires that heading. Panes are equal-width with no authored ratio/side/
responsive geometry/CSS. Renderer supplies only one straight divider,
synchronized title-band height, plot tops, equivalent-role fitting and largest
exterior gutters; category pitch synchronizes only for exact matching D228 IDs
and order. Synchronization never changes data, domains/ticks, formatting,
identity, annotations, measurements, or context. Each chart owns one D247 table
and independent diagnostics; failure cannot mutate its peer. Non-strict replaces
only a failed chart beneath retained title chrome where possible. If equal-width
floors cannot fit, strict fails and non-strict renders both complete surfaces
sequentially with diagnostics, never dropping or undersizing one. Supports,
metrics/heroes, pane takeaways, nested/additional charts/chrome are invalid.
Common root fields follow D212/D251. Legacy dual/hero/multi-panel migrates only
for exactly two unambiguous charts in preserved order.

### D254 — `chart_hero_dual` has explicit chart, hero, and support slots

Payload requires one complete D227 `chart`, one `hero` discriminated by
`hero_type` (`metric_stack` or `driver_card`), and optional D252 `support`.
All have distinct deck-unique surface IDs. Chart and hero require headings;
subtitles require their owner. Metric hero has 1–3 D152 metrics; driver hero has
1–6 D151 rows. Renderer owns fixed 2:1 chart/hero ratio. Support paints beneath
the chart inside the left two-thirds, never hero. Planning preserves the 320x240
plot floor, complete hero/support at role floors, and comparable title-band
height; support readability receives surplus before chart type without reducing
hero below floor. Chart is transparent/borderless, hero uses D66–D67 card
chrome, support only its semantic chrome. Reading order is chart, support, hero.
Malformed chart uses D102; malformed hero strict-fails or non-strict preserves
valid facts in an unresolved sequential card/list without inference; malformed
support follows D252. If fixed-ratio floors cannot fit, strict fails and
non-strict sequentially preserves chart/support/hero with diagnostics. Authored
geometry/style/responsiveness and legacy primary/secondary/key-stat inference are
invalid. Migration requires one unambiguous chart, recognized hero, and at most
one support. This supersedes D150's primary_visual/hero_visual key names.

### D255 — All table-backed surfaces share one exact `table` object

The common table object is reused by data/annex/grouped-annex tables,
period-comparison, comparison-cards, support/outlined support, heatmaps, visible
chart fallbacks, and D247 semantic tables. It requires deck-unique `surface_id`,
`stub_header`, and non-empty ordered `columns`/`rows`. Stub has exact label and
optional short label. Columns have collection-unique D115 `column_id`, label,
and optional short label; rows likewise use `row_id`, label/short label, and
`cells`. Cells is keyed by declared column ID and contains exactly one D213 value
per column with no extras; arrays define order and serialized cell keys sort.
Short labels are fitting-only while accessibility retains full labels; IDs never
derive from prose. Optional D218 typography is limited to mode, sync group, and
table font size. Allowed column groups remain a sibling of leaf columns under a
separate contract. Alignment, scale, role interpretation, ownership and fallback
diagnostics stay composition-specific outside the table. Authored geometry,
alignment/spans/style/CSS/HTML/metadata, primitive/positional cells, inferred
headers and merged body cells are invalid. Strict rejects mismatch. Non-strict
may only use D123 fallback IDs/unknown removal, convert malformed or missing
cells to diagnosed missing, and discard extra cell keys without reordering. If
rectangular identity-safe repair fails, the owning complete fallback applies;
rows/columns are never truncated.

### D256 — Grouped headers use explicit contiguous leaf-column spans

Optional `column_groups` is allowed only by supporting compositions. Each group
has collection-unique D115 `group_id`, exact label, optional short label, and
1–12 ordered existing leaf `column_ids` forming one contiguous range. Groups
cannot overlap/repeat/reorder columns, nest, or create more than two visible
header levels. Ungrouped columns remain explicit leaf headers with derived
rowspan; group order must match first-leaf order. Renderer derives colspan,
rowspan, scope, deterministic header IDs, and cell header associations. Authored
spans/parents/depth/header rows/HTML IDs/scope/alignment/style/CSS are invalid.
Short labels are fitting-only; accessibility retains full labels. Empty groups
are invalid. Strict reports all independent reference/overlap/contiguity/order/
identity errors. Non-strict removes malformed groups and uses a diagnosed flat
header whenever surviving grouping is incomplete or conflicting, while retaining
all leaf columns/cells in order. HTML, print/no-JS, accessibility and visible
fallbacks share the associations. Migration requires explicit unambiguous legacy
spans, never proximity or repeated wording. This narrows D142 to one non-nested
group level over leaves while permitting two rendered header rows.

### D257 — `data_table` payload contains exactly one ordinary table

Payload contains only one D255 table; explicit D256 groups are allowed. Root
title is its only visible heading and root content subtitle its only subtitle;
table caption/title-band labels are invalid. D220 takeaway, D222 disclosure,
evidence/source footer and notes remain allowed and planned. Table is full-width.
Headers use square navy/white semantic separators; transparent body cells use
semantic separators without stripes/colors/cards/per-cell styling. One common
20–24px adaptive D44 size covers every header, label, value and scale disclosure.
D24–D25 fitting redistributes renderer-owned widths, wraps labels to two lines,
grows rows, uses authored short labels, then ellipsizes labels accessibly; values
are never abbreviated/ellipsized/reformatted outside D214/dropped. Counts are fit-derived,
not schema-capped. Strict fails if complete content cannot fit at 20px after all
reserved chrome/common surfaces. Non-strict paints complete 20px content with
stable unresolved-overflow diagnosis, no pagination/clipping-by-design/loss/card
conversion/shrinking; any physical overflow is visibly marked, degraded, and not
paint-ready. Authored geometry/alignment/sorting/pagination/sticky/merged-body/
skin/style/HTML/CSS/interaction are invalid. Migration requires one complete,
unambiguous ordinary rectangular table including groups and semantics.

### D258 — `annex_table` is one dense table with disclosure-only notes

Payload contains exactly one D255 table and may use D256 groups. Root title and
optional subtitle are its only heading/dek. Supplemental annex notes use D222
disclosure only; table-local footnotes/footer strings and marker/source/cell
inference are invalid, while literal markers create no automatic relationship.
Interpretation-critical units, periods, qualifications and labels live directly
in D214 formats, headers, row labels and exact cells; disclosure cannot repair
incomplete semantics. Takeaway is forbidden; evidence/source footer/disclosure/
notes remain allowed. Every stub/leaf/grouped/ungrouped header uses the same
square navy/white separated chrome; body is transparent with semantic
separators. One common adaptive 12–24px size covers the entire table under
D24–D25. Complete fit reserves title/subtitle, source footer, disclosure control
and deck chrome. Strict rejects failure at 12px. Non-strict paints all content at
12px, diagnoses and visibly marks unresolved physical overflow, is degraded and
not paint-ready, and never truncates/paginates/splits/moves/drops structure.
Charts/cards/sibling tables/metric strips/takeaways, authored geometry/skins/
decorative or per-cell style/arbitrary notes are invalid. Migration requires one
complete dense matrix with unambiguous groups, cells, formats, missing states,
units/qualifications and disclosure boundaries.

### D259 — `grouped_annex_table` has one or two headed table peers

Payload `tables` contains exactly 1–2 ordered peers, each with exact heading,
optional short heading, and one complete D255 table; the table surface ID
identifies the peer, with no wrapper ID. D256 groups are peer-local. Root title/
subtitle remain slide-level. Peer headings use annex heading chrome, not chart
bands, and appear once visually/accessibly. Two peers are ordered left/right,
equal-width, divider-separated, and share one safe 12–24px equivalent-role size;
valid header rows align only where structures permit, without invented groups.
One peer is full-width with no phantom region. Peer-local subtitles/takeaways/
disclosures/source footers/cards/charts/nesting are invalid. One slide disclosure
is allowed after the composition; takeaway forbidden; evidence/source/notes stay
slide-level. Authored columns/ratios/stacking/placement/style/responsiveness are
invalid. Strict rejects invalid count/malformed tables/failure at shared 12px or
inability to preserve equal-width completeness. Non-strict replaces the whole
composition with sequential heading+complete-table peers at 12px, preserving all
semantics and diagnosing/visibly marking unresolved overflow; physical overflow
is degraded/not-ready and one peer is never dropped alone. Migration requires
one or two complete explicitly separated annex matrices with unambiguous heading
and order.

### D260 — `period_comparison` uses three fixed semantic column IDs

Payload table is D255 with exactly ordered IDs `current_period`,
`comparison_period`, `variance`; these IDs are the roles with no mapping object,
while labels/short labels author actual period wording. Stub names metrics and
there are 1–8 ordered rows. D213 values permit formatted number/range, exact text
such as NM, or missing. D256 groups are invalid. Optional `metric_strip` is one
D165 1–3-metric surface with a distinct deck-unique ID. Root title/subtitle own
slide chrome. Renderer supplies square bounded columns, navy caps, panel tokens
and 1px borders without gradients/shadows/rounding/skins. One common adaptive
20–24px table size applies; metric display values stay fixed and support labels
fit normally. Strip occupies a planned exterior lane and cannot push table below
20px. Takeaway/disclosure/evidence/source/notes remain allowed slide-level.
Strict rejects role-column mismatch/order/count, row count, malformed values or
fit failure. Non-strict preserves the full table as ordinary data-table fallback,
retains a valid strip, diagnoses lost comparison chrome, and never guesses roles.
Aliases/inference/computed variances/sorting/geometry/style/icons/arrows/pills/
duplicate metrics are invalid. Migration requires explicit unambiguous roles,
never merely three adjacent columns.

### D261 — `comparison_cards` derives fixed card geometry from one peer table

Payload is one D255 table with 2–4 peer rows and 2–4 shared fact columns. Table
ID owns the composition, row IDs own cards, row labels are headings, column
labels are shared fact labels, and D213 cells supply values. Every peer has every
fact; explicit missing is valid, absent cells/schema variation invalid. D256
groups are invalid. Geometry is fixed: two/three peers in one row; four in 2x2;
authored order is row-major. Cards are equal-width/equal-rank and equal-height
within rendered rows, growing to the tallest without reordering peers/facts.
D66–D67 gives innermost square panel/1px-border chrome without gradient/shadow.
Heading/fact-label/value/text roles fit independently but consistently across
cards; optional D218 body size pins only ordinary textual cells, while headings,
labels and display values remain renderer-owned. Numeric cells use D214; prose
stays complete. Root title/subtitle and slide-level takeaway/disclosure/evidence/
source/notes apply. The complete D255 table is the accessibility source and
print/no-JS preserve all facts without duplicate announcements. Strict rejects
counts, incomplete schemas, malformed values or role-floor fit failure.
Non-strict renders the full ordinary accessible table, never dropping cards or
facts. Authored grid/geometry/icons/style/ranking/sorting/badges/HTML/CSS or
detached metrics are invalid. The renderer may derive a circular dual-metric
visual (two circles, connector arrow, category captions) when every peer is
exactly two numeric facts plus one `Nx` multiplier text; other boards stay
text facts. The D255 table remains the accessibility/print source. Migration
requires one canonical complete peer-by-fact source; duplicate sources require
human selection.

### D262 — `metric_overview` has one metric group and optional narrative detail

Required payload `metrics` has deck-unique surface ID, exact heading, 2–6 ordered
items, and optional D218 mode/sync/body size. Items require unique metric ID,
plain label, D213 value, optional plain detail and optional change. Change requires
direction up/down/flat and exact comparison basis, with optional numeric/range
D213 value and positive/negative/neutral tone. Direction and tone are independent
and both accessibly expressed; renderer never derives direction, tone, midpoint,
amount, basis or guidance status. Values keep fixed display type; labels/details/
basis and detail prose adapt 22–28px without loss. Metrics are one equal-rank
D66–D67 square panel group with 1px borders and no decorative/guidance chrome.
Optional `detail` has distinct deck-unique ID, exact heading, 1–4 D225 blocks and
optional mode/sync/body typography, paints below in authored order, and cannot
duplicate metric facts. Root/common slide fields apply. Strict rejects counts,
IDs, values/changes or role-floor fit failure. Non-strict removes only malformed
change chrome while retaining/diagnosing its metric; malformed metrics follow
D123 and visibly mark unresolved, and fewer than two valid metrics produce a
sequential accessible unresolved composition preserving surviving facts/detail,
never invented meaning. Generic key stats/parsed bullets/metric strips/charts/
inferred headings/duplicate sources/authored geometry/style/HTML/CSS are invalid.
Migration requires one canonical source, classified prose, and explicit legacy
change semantics.

### D263 — `metric_stack` hero has one closed prominent-metric shape

Required hero fields are deck-unique surface ID, literal metric_stack type,
exact heading, and 1–3 ordered metrics; optional subtitle and D218 mode/sync/body
size apply. Metrics require unique ID, plain label, D213 value and optional plain
detail. Number/range uses D214; missing remains visible. Order is immutable.
Heading/subtitle share D40/D46 navy band; beneath it one vertical equal-rank
D66–D67 bounded square panel uses solid token/1px border without nested borders.
Display values keep fixed prominent type; labels/details adapt 22–28px under one
role plan, and body override pins only those roles. Text/ranges remain complete.
Direction/tone/trends/deltas/basis/icons/gauges/badges/colors/sparklines/per-item
style are invalid and directional metrics belong to D262. No inference from
chart/key stats/prose/peers. Strict rejects malformed or unfit metrics.
Non-strict drops malformed items diagnostically in order; zero survivors produce
a visibly unresolved retained hero beneath its heading, never invented/removed.
Accessibility, print and no-JS expose the stack once and completely. Migration
requires an explicit unambiguous 1–3 prominent-metric source.

### D264 — `driver_card` hero is one ordered fact-row list

Required hero fields are deck-unique ID, literal driver_card type, exact heading,
and 1–6 ordered rows; optional subtitle and D218 mode/sync/body size apply. Rows
require unique ID, plain label and D213 value, with optional plain detail,
up/down/flat direction and positive/negative/neutral/accent tone. Direction and
tone are independent and never inferred from sign/wording/color/each other.
Number/range uses D214; missing is visible/accessibly missing; order is immutable.
Heading/subtitle use the shared navy band. Rows form one vertical D66–D67 square
bounded panel with 1px outer border and semantic separators, not nested cards.
Renderer shape/wording conveys direction and semantic color plus wording conveys
tone, never color alone. Values keep fixed type; labels/details adapt 22–28px,
body override pins only those, and may wrap two lines. Residual text overflow
strict-fails or non-strict ellipsizes only its label/detail while retaining full
accessible text and row/field diagnosis. Values are never shortened/suppressed/
reformatted outside D214. Malformed rows strict-fail or drop individually
non-strict; zero survivors retain heading over visibly unresolved hero without
invention/substitution. Icons/arbitrary arrows/colors/sorting/ranking/grouping/
row geometry/HTML/CSS/inferred sentiment are invalid. Accessibility, print,
settled/no-JS preserve each surviving fact once. Migration requires explicit,
unambiguous row semantics.

### D265 — `metric_strip` is one compact directionless metric row

Required support fields are deck-unique ID, literal metric_strip type, and 1–6
ordered metrics; optional D218 mode/sync/support-label size applies. Metrics
require unique ID, plain label and D213 value with optional plain detail.
Number/range uses D214; missing remains visible/accessibly missing. Metrics paint
as one equal-width authored-order horizontal row. Values keep fixed KPI type;
labels/details share adaptive 14–24px, wrap at most two lines, and are never
abbreviated/ellipsized/suppressed; override pins only these roles. Strip has no
heading/subtitle/title band/card fill/gradient/shadow/nested cards, only necessary
semantic cell separators. Beneath owning charts it participates in D10/D47 but
is never category-aligned and does not affect centers/domain/gutters/identity.
Direction/tone/deltas/basis/arrows/icons/sparklines/colors/ranking/sorting/cell
style/geometry are invalid; use D262 or D264. Strict rejects malformed metrics or
failure at 14px while preserving chart floor. Non-strict drops malformed items
diagnostically in order and omits/degrades only an empty surviving strip, never
inventing or reading key stats. Accessibility, print and settled/no-JS expose
each survivor once. Migration requires 1–6 explicit directionless support facts.

### D266 — `support_table` wraps one table with explicit alignment

Required wrapper fields are literal support_table type, category/independent
alignment, and one complete D255 table whose surface ID identifies the support;
no wrapper ID. Optional D218 mode/sync/table size applies. Tables contain 1–4
rows; D256 groups are independent-only. Category alignment requires exact owning
D228 IDs/order/count and visible ownership by axis or explicit surface. Frozen
Chart.js/SVG centers align within 2px; duplicate visual headers omit only when the
chart owns all categories while accessibility associations remain, and hidden
axis makes support headers visible category owners. Independent alignment permits
unrelated IDs/groups and never center-aligns. No label/count/proximity inference.
One common transparent-body 14–24px table size and semantic separators apply,
without heading/band/card/shadow/rounding. D10/D47 preserve chart 320x240 floor,
complete 14px support and all chart semantics/gutters. Strict rejects malformed,
identity/order/ownership/alignment or fit failures. Non-strict converts invalid
category alignment to diagnosed independent while preserving table; residual fit
failure uses D252 complete sequential fallback without loss. Authored geometry/
hidden-header/tolerance/skin/style/merged cells/HTML/CSS are invalid. Migration
uses category only for exact identity, otherwise independent. Table-backed
support identity is table.surface_id; only non-table support carries ID directly.

### D267 — `outlined_support` is one category-aligned single-row table

Wrapper requires literal outlined_support and one D255 table whose ID owns the
surface. Table has exactly one row and exact owning-chart D228 category IDs/order
with complete cells; alignment is implicit category and D256 groups invalid.
Stub label is the visible exterior label. Required row label remains semantic but
is not separately painted; normalized duplication appears once visually. Chart
must visibly own categories and hidden category axis makes this surface invalid.
A dedicated at-most-two-line label lane cannot overlap square outlined boxes;
boxes include missing em dashes and centers match frozen Chart.js/SVG within 2px.
One common adaptive 22–24px table size covers label and boxes. Values cannot be
shortened/suppressed/moved/reformatted outside D214. Renderer owns lane/box/gap/
border/center geometry; author skin/geometry/style/visibility/HTML/CSS is invalid.
D10/D47 preserve chart 320x240 and complete support at 22px. Strict rejects row/
category/ownership/overlap/alignment/fit failures. Non-strict converts the whole
surface to D266 support_table, category-aligned where exact ownership survives or
independent otherwise, preserving all semantics; it never partially aligns or
drops/shortens boxes/label. Migration requires an explicit unambiguous one-row
category-aligned matrix.

### D268 — Opening and closing covers share one exact payload schema

Both cover layouts require exact plain `title` and optionally separate exact
`subtitle`, `period_label`, and `date_label`; renderer never parses/combines/
normalizes/reformats/infers them and date-like text remains display text. Covers
omit root section/title/content/takeaway/disclosure/source footer, while evidence
and notes remain allowed. At most one opening first and closing last. Opening
title owns accessible deck title; closing title owns only its slide. Fields paint
at most once and omissions create no placeholders. Renderer-owned boardroom_amex
chrome controls all marks/bands/colors/spacing/alignment/type/arrangement; cover
type is fixed. Authored theme/assets/geometry/style/background/arbitrary metadata
are invalid. Text wraps only at renderer word boundaries with no loss/shrink;
strict fails if unfit. Non-strict preserves title/subtitle/period/date order in a
visibly diagnosed plain-cover fallback without invention/drop; physical overflow
is degraded/not-ready. Misplaced/duplicate covers strict-fail or non-strict stay
in order as D180 unresolved, never moved/deleted. Migration requires each visible
string to have one unambiguous role; combined or operational text needs humans.

### D269 — `section_divider` payload contains only `section_id`

Payload contains only one required registered D215 section ID. Divider omits root
section/title and derives exact visible/accessibility wording from the registry,
without override/abbreviation/style/translation/supplement. A section has at most
one divider, immediately before its first ordinary slide after prior sections and
in registry order; divider itself is not an ordinary section slide. Evidence and
notes remain allowed; content/takeaway/disclosure/source footer and payload prose/
period/date/kicker/number/summary are forbidden. Renderer-owned boardroom_amex
chrome and optional registry-order-derived numbering are fixed outside D218.
Strict rejects unknown/duplicate/misplaced/out-of-order/extra content. Non-strict
preserves position as D180 unresolved, diagnoses the relation, and never guesses,
moves, merges or deletes. Unfit valid labels strict-fail or non-strict paint a
complete diagnosed plain divider without shortening; overflow is degraded/not-
ready. Migration requires explicit unambiguous section relationship/label, never
visual proximity. This supersedes D223's divider wrapper under D251.

### D270 — `narrative` uses an ordered discriminated block list

Payload has 1–4 authored-order blocks, each with slide-unique D115 block ID,
paragraphs/bullet_list discriminator, and exactly matching content. Paragraphs
hold 1–6 D224 prose objects; bullets hold 1–8 D224 items. Empty/cross/additional
fields are invalid. Optional D218 mode/sync/body size resolves one common
22–28px size. Root title/subtitle are sole headings; blocks cannot own heading/
caption/callout/card/column/sidebar/icon/number/nesting/layout. Wording, runs,
emphasis, boundaries and order are immutable. Renderer may wrap, redistribute
vertical spacing and grow whole pixels, but never merge/split/rewrite/summarize/
shorten/suppress/move or continue onto another slide. Strong is weight only.
Composition is one full-width transparent prose region without decorative/card/
authored-column chrome. Takeaway/disclosure/evidence/source/notes remain allowed
slide-level and planned. Strict fails if complete content cannot fit at 22px.
Non-strict paints every block sequentially at 22px, preserving boundaries and
visibly diagnosing unresolved overflow as degraded/not-ready without designed
clipping/loss. Invalid blocks drop only under D123 when remaining meaning stays
complete, otherwise D180 unresolved applies. Migration requires mechanically
unambiguous paragraph/list/emphasis boundaries; inferred structure needs humans.

### D271 — `legal_notice` is an explicit contiguous multipart sequence

Payload requires D115 notice ID, positive part/total with part<=total, and 1–6
exact non-empty plain paragraphs. Part 1 requires exact title; later parts forbid
it. A sequence shares ID/total/section, is adjacent and exactly covers 1..total
without recurrence, gaps or duplicates; every part has one registered root
section. Root title/content omit. Part-1 title is sole authored heading; later
parts receive deterministic visible `— continued` and accessible part-of-total
wording without duplicating authored content. Paragraph wording/Unicode/internal
whitespace/boundaries/order are exact with safe escaping only; no D224, emphasis,
markup/links/bullets/style. Typography is fixed, with no D218, adaptation or
automatic pagination/redistribution. Takeaway/disclosure/source footer and other
surfaces are forbidden; evidence/notes remain allowed. Deck-wide strict rejects
sequence/title/section/fit defects. Non-strict never renumbers/reorders/merges/
splits/moves/invents; each affected slide stays in order as visibly diagnosed
legal fallback preserving valid title/paragraphs, marking unresolved relations,
and reporting physical overflow degraded/not-ready. Migration requires explicit
unambiguous title, boundaries, order and continuation relationships.

### D272 — `process_flow` is one implicit linear sequence

Payload contains 2–6 ordered steps with unique D115 step ID, exact heading and
optional exact detail. Order owns process/reading order and implicit next-step
connections; first/last have no special role and outcomes are ordinary authored
final steps. Renderer owns orientation/reflow/numbering/connectors/routing/spacing
and equal-rank D66–D67 square panels; reflow cannot alter order/edges and
connectors add no unannounced meaning. Typography is fixed under D60 with no
D218/authored sizes and complete fit. Root/common takeaway/disclosure/evidence/
source/notes remain allowed. Explicit edges/branches/merges/loops/decisions/
time/status/owner/icon/style/progress or authored geometry/SVG/HTML/CSS are
invalid; specialized compositions own those semantics. Strict rejects counts,
IDs/text or fit failure. Non-strict paints every valid step as a visibly
diagnosed accessible ordered list preserving detail/order/adjacency and omits
misleading connectors; D123 may drop malformed steps, but fewer than two invokes
D180 unresolved. Migration requires one explicit unambiguous linear sequence;
inferred outcome/branch/date/cycle/decision meaning needs humans.

### D273 — `timeline` preserves authored chronology without parsing

Payload has 2–8 authored-order milestones with unique D115 milestone ID, exact
time label and heading, plus optional exact detail. Array order is authoritative
chronology/accessibility. Time labels are display text: renderer never parses,
sorts, normalizes, expands, or derives duration/spacing. Renderer owns orientation,
spacing, line/connectors, marker and row wrapping; visual distance has no duration
meaning and connectors mean only sequence. Typography/marks are fixed under
D60/D62 with complete fit and no D218/scaling. Root/common takeaway/disclosure/
evidence/source/notes remain allowed. Parsed dates/ranges/durations/progress/
phase/status/owner/dependency/branches/cycles/tracks/bands/icons/style/geometry/
SVG/HTML/CSS are invalid; ranged/parallel schedules need a future composition.
Strict rejects counts/IDs/text/fit. Non-strict preserves every valid milestone in
a visibly diagnosed accessible chronological list and omits misleading timeline
geometry; D123 may drop malformed milestones, but fewer than two invokes D180
unresolved. Migration requires explicit unambiguous order/time/heading/detail;
date extraction or inferred ordering needs humans.

### D274 — `decision_tree` uses explicit decision and outcome nodes

Payload requires root node ID and 3–15 authored nodes. Nodes have unique D115 ID,
decision/outcome type, exact heading and optional detail. Decisions require 2–3
ordered branches with normalized-unique exact labels and existing target IDs;
outcomes are branchless leaves. Root references a decision. Relationships form
one reachable rooted tree: one parent per non-root, no cycles/self/shared targets/
cross-links, maximum root-to-leaf depth four nodes. Node array gives stable
serialization/fallback order; branch order owns sibling/reading order. Renderer
owns orientation, dimensions, routing, labels, spacing and alignment; connectors
mean only authored branches and roles are not color-only. Nodes use fixed D60
D66–D67 square chrome. Authored geometry/style/icons/status/probability/score/
recommendation/default/executable logic/formulas/code/HTML/SVG/CSS are invalid.
Renderer never evaluates/chooses/infers/merges/reorders/parses logic. Root/common
slide fields apply. Strict rejects structure or complete-fit failure. Non-strict
preserves all nodes/branch labels/targets in a visibly diagnosed relationship
table marking invalid relations without reconnect/delete/guess; a valid but
unlayoutable tree may use nested accessible outline. Physical fallback overflow
is degraded/not-ready. Migration requires explicit unambiguous roles, labels,
targets, root and complete tree.

### D275 — `feedback_loop` is one ordered implicit cycle

Payload requires procedural/causal loop type and 3–8 authored-order items with
unique D115 ID, exact heading and optional detail. Order connects each item to the
next and last to first and owns reading order. Procedural forbids edge effect/
label and means recurrence only. Causal requires every item's next-edge effect
same_direction/opposite_direction and permits exact relationship label, including
last-to-first. Even opposite edges derive reinforcing, odd derive balancing, with
accessible classification and every effect; renderer never infers effects and
labels cannot contradict them. Renderer owns clockwise geometry, nodes/routes/
arrows/edge labels/indicator; D60/D62 fixed type/marks and D66–D67 square nodes
apply. Explicit targets/branches/chords/multiple cycles/start-end/geometry/style/
icons/scores/time/formulas/code/HTML/SVG/CSS are invalid. Root/common slide fields
apply. Strict rejects counts/IDs/applicability/contradiction/fit. Non-strict never
drops cycle items/edges; it preserves all content as visibly diagnosed ordered
relationship table with next items and causal effects/labels, marking missing or
malformed effects unresolved without inference; physical overflow is degraded/
not-ready. Migration requires one explicit closed cycle, order, kind and every
required causal effect.

### D276 — `layered_architecture` expresses grouping only

Payload has 2–4 authored-order layers with unique D115 layer ID, exact heading,
and 1–4 ordered components. Component IDs are unique across the surface; each has
exact heading and optional detail. Layer order means grouping/visual stack only;
component order means within-layer order only, never dependency/flow/causality/
time/priority or more than explicit membership. Renderer draws no arrows and owns
vertical stack, component distribution, equal-rank sizing, spacing/separators.
Layers are transparent unframed groups; components use innermost D66–D67 square
panel/1px-border chrome. Typography is fixed D60 with complete fit/no D218.
Root/common slide fields apply. Links/ports/protocols/APIs/transfers/arrows/
dependencies/targets/status/owner/role/logos/icons/style/badges or authored
geometry/HTML/CSS/SVG are invalid; specialized compositions own relationships.
Strict rejects counts/IDs/text/fit. Non-strict preserves all valid layers,
membership/order/details in a visibly diagnosed nested accessible outline and
omits misleading geometry; D123 may drop malformed components, empty layers stay
visibly unresolved, and fewer than two valid layers invokes D180. Migration
requires explicit layers/membership without directional or hierarchy semantics.

### D277 — `data_pipeline` is an ordered sequence of structured stages

Payload has 2–6 authored-order stages with unique D115 stage ID, exact heading,
and 1–3 ordered components. Component IDs are surface-unique with exact heading
and optional detail. Every nonfinal stage may have exact transfer label; final
forbids it. Order owns one directed next-stage connection and reading order;
transfer label describes only that edge and is never interpreted as protocol/
transform/SLA/condition/code. Components mean stage membership only with no
component links. Renderer owns orientation/wrapping, dimensions, distribution,
arrows and labels while preserving order. Stages are transparent structural
groups with only needed semantic boundary; components use D66–D67 square cards;
arrows mean stage transfer only. D60/D62 fixed type/marks apply. Root/common slide
fields apply. Explicit edges/targets/branches/merges/loops/cross-links/component
transfers/protocol/API/ports/schema/status/owner/time/throughput/transformation/
style or authored geometry/HTML/SVG/CSS are invalid. Strict rejects counts/IDs/
misplaced label/text/fit. Non-strict preserves every stage/component/transfer in
a visibly diagnosed accessible ordered flow, states `A to B: label`, omits
misleading arrows, and never infers relations; D123 may drop malformed components,
empty stages stay unresolved, and fewer than two valid stages invokes D180.
Migration requires explicit linear stages, membership and transfer ownership.

### D278 — `hierarchy` uses one uniform child-to-parent relationship

Payload requires reports_to/part_of/is_a relationship, root ID and 3–20 nodes.
Nodes have unique D115 ID, exact heading, optional exact detail and ordered child
IDs; empty child lists omit. A child reports to/is part of/is a kind of its
current parent according to one deck-surface-wide relationship. Root is sole
parentless node. Relations form one reachable rooted tree: one parent per
non-root, no cycles/self/shared/duplicate children/cross-links, max depth four.
Node array owns stable fallback order; child order owns sibling/accessibility
order. Renderer owns orientation, levels, dimensions, routing and wrapping;
connectors express only the relationship. D66–D67 square nodes and fixed D60 type
apply, with accessible relationship wording. Duplicate parent representation,
arbitrary/mixed edges, dotted/matrix/shared/alias/multi-root structures, ranks/
geometry/style/images/HTML/SVG/CSS are invalid; specialized compositions own
other relations. Strict rejects structure/identity/reference/depth/fit.
Non-strict preserves all valid nodes/references in a visibly diagnosed relation
table marking dangling/duplicate/cyclic/shared/unreachable/mixed defects without
reconnect/root choice/edge deletion/invention; valid-but-unlayoutable trees may
use nested outline, and fallback overflow is degraded/not-ready. Migration
requires explicit unambiguous root, uniform relation, links and sibling order.

### D279 — `stakeholder_map` is one focal entity with explicit spokes

Payload requires one focal entity and 2–8 ordered stakeholders. Focal has
surface-unique D115 entity ID, exact heading and optional detail. Stakeholders
have surface-unique ID, exact heading, exact relationship label,
undirected/to_focal/from_focal/bidirectional direction and optional detail. Every
edge is stakeholder-focal only; renderer never infers wording/direction. Array
order owns serialization/reading/clockwise order. Renderer owns hub/spoke
geometry, dimensions, routes, arrows and label placement; distance carries no
strength/priority meaning. D66–D67 square nodes and fixed D60 type apply, with
accessible wording/direction never arrows alone. Spoke-spoke edges/multiple hubs/
hierarchy/groups/layers/chains/cycles/weights/status/owner/frequency or authored
geometry/style/logos/images/HTML/SVG/CSS are invalid; specialized compositions
own other relations. Root/common slide fields apply. Strict rejects count/IDs/
relationships/links/fit. Non-strict preserves focal and all valid stakeholders in
a visibly diagnosed relationship table with details/labels/direction, marks
unresolved relations, never invents/drops/links, and fewer than two stakeholders
invokes D180; fallback overflow is degraded/not-ready. Migration requires one
explicit hub and exclusively explicit hub-spoke relationships.

### D280 — `quadrant_matrix` uses semantic low/high assignments

Payload requires x/y axes and 1–16 authored-order items. Each axis has exact
label and normalized-distinct exact low/high labels. Items have unique D115 ID,
exact heading, low/high x and y assignments and optional exact detail. Assignments
select one quadrant. Renderer owns dimensions, axis direction/placement, item
placement/collisions and preserves authored within-quadrant order; empty
quadrants stay labeled and distance conveys no ranking/magnitude. No inference
from numbers/wording/order/business context. Items use D66–D67 square cards with
fixed D60 type; axis/quadrant boundaries are semantic structures exempt from D63
and assignments are accessible without color/position alone. Scores/coordinates/
percentages/midpoints/size/rank/confidence/weight/arbitrary quadrant names/style/
icons/shapes/arrows/regions/thresholds/HTML/SVG/CSS are invalid; richer axes need
a future composition. Root/common slide fields apply. Strict rejects axis/ID/
assignment/fit defects. Non-strict preserves axes and every valid item in a
visibly diagnosed four-group accessible fallback, marks unresolved assignments
without guessing and never drops for fit; overflow is degraded/not-ready.
Migration requires explicit binary axes/endpoints and every item assignment.

### D281 — `feature_cards` uses a closed semantic icon registry

Payload has 2–6 authored-order equal-rank cards with unique D115 ID, exact
heading, optional exact detail and optional icon key. Closed schema keys are:
`growth`, `decline`, `globe`, `users`, `currency`, `percent`, `warning`, `check`,
`flow`, `calendar`, `scale`, `building`, `restaurant`, `travel`, `target`,
`energy`, `shield`, `chart`, `layers`, `clock`, `link`, `credit_card`, `wallet`,
`institution`, `receipt`, `document`, `partnership`, `security`, `briefcase`,
`coins`; internal `ic-*` names are not public. Theme sprite icons are decorative,
aria-hidden and cannot carry/infer meaning. Geometry is 2/3 one row, 4 as 2x2,
5/6 balanced two rows in row-major authored order. D66–D67 square panel/border
chrome applies without gradient/shadow; icons remain fixed. Equivalent heading/
detail roles adapt 22–28px without loss. Optional D218 mode/sync/body size pins
one common text size only. Root/common slide fields apply. Values/metrics/tone/
ranking/evidence-per-card/relationships/process semantics or authored grid/style/
icon geometry/assets/HTML/CSS are invalid. Strict rejects count/IDs/icon/fit.
Non-strict drops only unknown decorative icons diagnostically, preserves all text,
and uses complete sequential cards/list when grid fails, never dropping cards.
Migration maps exact known decorative icons only; semantic/unknown icons need
human resolution.

### D282 — `quotation` preserves exact prose and explicit attribution

Payload has 1–3 authored-order quotes with unique D115 quote ID, 1–3 exact plain
paragraphs and attribution requiring exact name plus optional exact role/
organization. Optional evidence ID resolves through D216 and slide D217 links for
provenance only and never paints. Attribution remains separate and is never
parsed/invented. Quote wording/Unicode/internal whitespace/boundaries/order are
exact with safe escaping only; no D224/markup/links or authored quote control.
Renderer supplies visual quote chrome but preserves literal authored quotation
marks. Each quote is one blockquote with associated cite and attribution once.
One quote is full-width; 2–3 are equal-rank authored-order D67 square cards with
panel/1px border and no gradient/shadow. D60 typography is fixed without D218 or
shortening/paraphrase/shrink. Root/common takeaway/disclosure/source/notes apply;
duplicate visible sources follow D97. Photos/logos/icons/style/ratings/sentiment/
URLs/locator/source filenames or authored geometry/HTML/SVG/CSS are invalid.
Strict rejects counts/evidence/attribution/fit. Non-strict preserves all valid
quotes/attributions sequentially, retains unresolved-provenance quotes marked
unavailable/degraded, never drops text or invents attribution, and physical
overflow is not-ready. Migration requires explicit separable body, paragraphs,
attribution and evidence.

### D283 — `evidence_review` is exact findings linked to registered evidence

Payload has 1–6 authored-order findings with unique D115 ID, exact D224 statement
and 1–4 ordered duplicate-free D216 evidence IDs also present in slide links.
Renderer never extracts/verifies/rewrites/ranks or infers support. Findings are
equal-rank D66–D67 square panel/1px-border cards without gradient/shadow, showing
complete statement and ordered resolved source names only—never IDs/locators/
paths/files/inferred URLs/scores. Strong emphasis is visual only and source names
are noninteractive provenance labels. 1–3 findings use one row when fit; 4–6 a
balanced two-row row-major arrangement. D60 type is fixed, no D218 or shortening/
loss/shrink. Root title/subtitle, takeaway conclusion, disclosure and notes apply;
source footer is forbidden. Finding heading/score/rank/tone/icon/style/quote/
generated summary/conclusion or copied evidence metadata/assets/geometry/HTML/
SVG/CSS are invalid. Strict rejects counts/IDs/statements/references/fit.
Non-strict preserves valid statements, drops bad references individually with
diagnostics, paints `Source unavailable` if none survive, retains unsupported
finding, and uses sequential accessible list when cards fail; physical overflow
is degraded/not-ready. Each statement/source set is announced once. Migration
requires exact finding boundaries and explicit registry links; inferred links
need humans.

### D284 — `risk_opportunity_review` uses two authored groups

Payload requires risks and opportunities, each 1–6 authored-order items. Items
have ID unique across payload, exact D224 statement and optional exact D224
detail. Membership owns role; renderer never infers sentiment, pairs/balances,
ranks/scores/reorders or invents likelihood/impact/urgency/mitigation/upside/
owner/status. Groups are equal-rank peers with renderer-owned visible/accessibility
headings `Risks` and `Opportunities`, not author-overridable. Items use D66–D67
square panel/1px-border chrome without gradient/shadow; headings/structure and
optional accessible accent convey role, never color alone. Two equal-width
columns use top-to-bottom authored order when fit. D60 type is fixed without D218
or text loss/shrink. Root/common slide fields apply. Per-item role/tone/style/
icon/score/rank/priority/analysis/owner/status/evidence/pairing/geometry/arrows/
HTML/SVG/CSS are invalid; structured prioritization needs a future composition.
Strict rejects groups/counts/IDs/prose/fit. Non-strict D123-drops malformed items,
keeps survivors in role/order, visibly marks an emptied group unresolved, and
uses sequential Risks then Opportunities when columns fail, never moving or
layout-dropping items; overflow is degraded/not-ready. Migration requires
explicit group boundaries/statements; sentiment classification needs humans.

### D285 — `recommendation_case` separates recommendation from rationale

Payload requires one exact D224 recommendation and 1–6 authored-order rationales
with unique D115 ID, exact D224 statement and optional detail. Recommendation is
sole recommendation; rationales are reasons, not steps/ranks/evidence/metrics/
risks/actions. Renderer never rewrites/ranks/infers/verifies/generates/promotes.
Roles use distinct renderer-owned D66–D67 square bounded recommendation panel and
smaller ordered rationale cards with solid tokens/1px borders/no gradient/shadow.
Accessibility names Recommendation and numbered Rationales; role is not size/
color alone and strong emphasis is visual only. D60 type is fixed without D218 or
text loss/shrink. Root title/subtitle, disclosure, slide evidence/source/notes
apply; takeaway and per-rationale evidence are forbidden. Authored heading/tone/
icon/priority/status/owner/date/score/confidence/approval/plan or rationale rank/
weight/style/layout/arrows/HTML/SVG/CSS are invalid; specialized compositions own
action/evidence. Strict rejects prose/counts/IDs/fit. Non-strict preserves the
recommendation, D123-drops malformed rationales, visibly marks missing support if
none survive, and uses sequential accessible recommendation then rationales when
cards fail, never inventing/promoting disclosure; overflow is degraded/not-ready.
Migration requires one exact recommendation and explicit rationale boundaries.

### D286 — `state_transition` has exact states and optional steps

Payload requires before/after states, each with deck-unique D115 surface ID,
exact heading and 1–4 D270 blocks; block IDs are unique across payload. Headings
need not say Before/After but roles are fixed. Optional 1–4 D272-style transition
steps have unique IDs, exact headings and optional details in ordered movement
from complete before toward complete after. States are never positionally paired;
renderer computes/infers no delta/improvement/sentiment/causality/success.
Renderer owns equal-rank D66–D67 square state panels, structural indicator and
step lane while reading before, steps, after; arrows add only sequence meaning.
D60 typography is fixed for states/steps with no D218. Root/common slide fields
apply. Pairing/computed facts/metrics/status/score/tone/success/owner/time/
dependency or authored arrows/geometry/style/icons/HTML/SVG/CSS are invalid;
specialized compositions own those facts. Strict rejects states/blocks/steps/
IDs/fit. Non-strict preserves complete before, every valid optional step and
complete after sequentially; D123 may drop malformed optional steps but never
state prose when meaning changes, in which case D180 unresolved applies; no
pairing/delta/transition inference and overflow is degraded/not-ready. Migration
requires explicit before/after and optional step boundaries.

### D287 — Common slide fields use one applicability matrix

Opening/closing covers and section dividers forbid root section/title/content/
takeaway/disclosure/source footer but allow evidence/notes. Legal notice requires
section and forbids title/content/takeaway/disclosure/source footer while allowing
evidence/notes. Annex/grouped annex require section/title, allow content,
disclosure/source/evidence/notes and forbid takeaway. Evidence review requires
section/title, allows content/takeaway/disclosure/evidence/notes and forbids source
footer. Recommendation case requires section/title, allows content/disclosure/
source/evidence/notes and forbids takeaway. Every other D210 composition requires
section/title and allows all six optional common fields. Allowed means optional
and omitted when absent; null/empty placeholders are invalid and required text is
non-empty plain. Content exists only with subtitle and optional D218 mode/sync/
subtitle size. All heading owners remain distinct and duplicates follow D97.
Payload cannot smuggle forbidden common fields. Strict reports path-specific
inapplicability; non-strict D123-drops only when meaning remains complete,
otherwise D180 unresolved, and any drop degrades. D121 encodes this per branch.
Migrator moves only mechanically clear ownership and flags unique forbidden prose,
never deleting it. This matrix supersedes ambiguous scattered applicability.

### D288 — `takeaway` is one fixed-slot plain-text object

Takeaway requires one exact non-empty plain `text` and optionally D218 mode/sync/
body size. It is a fixed slot with no authored surface ID; identity derives from
slide number plus takeaway, at most once. Renderer supplies non-overridable
visible/accessibility `Key takeaway`. Safe escaping is the only transformation;
no D224/markup/links/bullets/emphasis or rewriting/shortening/loss. Text adapts
22–28px; override pins text only while role-label type stays fixed. It paints once
after main composition and before disclosure/source, using D66–D67 square
recommendation panel/1px border without gradient/shadow, with planned nonoverlap.
It remains distinct from subtitle/recommendation/chart facts/evidence/source/
notes; D97 removes only duplicate chrome, never unique wording. Strict fails if
complete text cannot fit at 22px. Non-strict paints complete 22px text, visibly
diagnoses physical overflow and is degraded/not-ready, never moving content.
Primitive shorthand/empty/heading/tone/icon/style/evidence/layout/HTML/CSS are
invalid. Migration maps legacy so_what only when one unambiguous slide-level
takeaway; competing/duplicated prose needs humans.

### D289 — `disclosure` uses typed items in native detail sections

Disclosure has 1–4 authored-order sections with deck-unique D115 surface ID,
normalized-unique exact title and 1–6 ordered items. Items are paragraph/bullet
with exact plain text; consecutive bullets form one native list and type changes
boundaries without reorder. Safe escaping only; literal markers remain and no
markup/link/footnote/evidence/list parsing occurs. One section uses native details;
multiple use an accessible details accordion, all initially closed with exact
summary titles. Tabs/pattern/open/exclusivity/animation/icon/style/interaction
controls are invalid. Print/static/no-JS exposes everything without interaction.
Deterministic IDs derive from surface IDs, never UUID/position. Disclosure is
supplemental and cannot solely own critical facts; such hiding is validation
failure. Type/chrome are fixed D60, square as needed, no D218/gradient/shadow.
It paints after composition/takeaway before source; collapsed and expanded forms
participate in planning. Strict rejects counts/IDs/titles/text/static fit.
Non-strict drops malformed sections whole, preserves valid order, omits empty
result, diagnoses/degrades, and never promotes text. Empty/D224/markup/links/
nesting/item headings/evidence/attributes/CSS are invalid. Migration converts
unambiguous detail/accordion only; tabs and ambiguous boundaries need humans and
markup-looking text is never auto-structured.

### D290 — Every chart uses one flat common envelope

Every chart requires deck-unique D115 surface ID and D238 chart type. Optional
common direct fields are exact heading, heading-dependent subtitle, D218
typography, D231 display, D232 context labels, D233 annotations and D234
measurements. Axis families directly add chart_data/category_axis/value_axes;
family branches directly permit only applicable bar mode/groups/auxiliaries/
coverage, waterfall data, or heatmap table/scale. No chart_config/options/config/
family/data/visual/nested family payload exists. Optional collections/objects
omit rather than empty. Heading alone owns pane title with no synthesis and D170
requiredness. Chart owns one frozen plan, D247 table, diagnostic identity, and
both D248 representations. All facts are painter-neutral and both painters use
one canonical data/format/identity/type/annotation/diagnostic plan. Branches are
closed; unknown/inapplicable/cross-family fields error, never silently ignored.
Strict rejects before planning. Non-strict uses only D123 and subgroup-specific
repairs, otherwise complete D102 pane fallback, never raw rejected config. D121
generates one flat discriminated chart union. Migration flattens only mechanically
unambiguous legacy config; conflicts need humans. This supersedes D169 chart_config.

### D291 — Axis-chart data is one ordered category-and-series model

Line/grouped/stacked/horizontal/combo require chart_data; waterfall/heatmap forbid
it. Non-empty categories have unique D115 ID, exact label and optional short
label; equal visible labels remain distinct and never merge. Non-empty series
have unique D115 ID, normalized-unique exact name and exactly one canonical
undecorated decimal string or null per category. Numbers/booleans/decorated/
empty/nonfinite/text are invalid. Decimals drive source geometry and axis D214
formats display; null preserves position/missing with no zero/interpolation.
Series may use color key. Line marks alone may author complete style+marker pair.
Combo requires mark_type bar/line and optional primary/secondary axis; those are
invalid elsewhere and bars cannot use line style. Array order owns categories,
series, grouped/stacked order, line identity and semantic-table order. Renderer
never sorts/aggregates/deduplicates/pivots/transposes/interpolates/infers headers.
Continuity/colors/styles use series ID; supports/siblings align category ID.
Strict rejects IDs/names/ragged/values/applicability/family counts. Non-strict may
only generate diagnosed IDs, trailing-null-pad, discard surplus trailing values,
and turn malformed points to null; never shifts/invents labels/names/reorders/
guesses marks/axes/colors/identity. If no family-compliant complete identity
survives, D102 fallback applies. Migration converts legacy matrices only when all
category/series/position/mark/axis meaning is mechanically clear.

### D292 — Axes use semantic roles with generated or fixed domains

Every axis chart requires category_axis visible bool plus optional exact title,
and value_axes.primary visible bool, D214 format, domain and optional exact title.
Secondary is combo-only, required exactly when referenced, same shape and never
unused. Roles are semantic across orientation; no physical x/y aliases. Hidden
titles remain accessible but unpainted and are never synthesized. Generated
domain permits canonical min/max, target ticks 2–8 and family-valid leading break;
ticks are deterministic, preserve bounds/endpoints/required zero, add headroom
only without blocking bound and may reduce density. Fixed requires canonical
min/max and 2–8 increasing ticks spanning endpoints absent a break; ticks are
authoritative/unskippable and satisfy containment. Break has only canonical `to`,
line/horizontal only, requires min<to below every finite value, preserves values
and discloses omitted range; fixed first visible tick equals to. It is invalid for
vertical bars/combo/waterfall/heatmap/mixed signs. Hidden category needs another
visible owner. Hidden value still needs format but generated-only with no target/
break. Visibility never adapts. Family domains enforce zero and waterfall levels.
Physical aliases/inline formatting/tick strings/callbacks/scales/log/reverse/
grid/style/painter options are invalid. Strict rejects axis/format/visibility/
domain/ownership/break defects. Non-strict visibly restores unowned categories,
uses diagnosed safe generated domains, removes unsupported breaks/hidden tick
controls, but never guesses format; invalid formatting/axis ownership uses D102.
Chart.js/SVG/D247/accessibility/diagnostics share one frozen axis plan.

### D293 — Number formats use a small closed unit vocabulary

Registry keys are D115 format IDs; entries require value decimals 0–4 and
minus/parentheses negative style, and optionally unit, tick decimals 0–4,
positive canonical value_scale and exact scale_label. Units are only usd,
percent, percentage_points, basis_points; omission is unitless. Renderer forms
are `$` prefix and `%`, ` pp`, ` bps` suffixes with expanded accessible wording;
placement is intrinsic and legacy unit-position disappears. Units never rescale.
Scale defaults 1 by omission, affects display only after source geometry/totals/
domain, must be omitted at 1, and requires scale_label exactly when present,
rendered once per axis/table. No scaling inference. Value decimals govern all
ordinary formatted facts/accessibility; tick decimals govern ticks, otherwise
minimum 0–4 distinguishing precision. Formatting preserves source decimal,
scales display, rounds half-away-zero, emits trailing zeros/comma separators,
applies negative style to the whole unit-plus-magnitude quantity: minus precedes
a prefix unit (`-$...`, never `$-...`) and parentheses wrap the whole quantity;
rounded zero is unsigned. Explicit text bypasses formatting. All painters,
tables, accessibility and diagnostics use one preformatted string. Arbitrary
units/templates/locales/symbol/sign/accounting/callback/HTML/CSS are invalid.
Strict rejects entries/references.
Non-strict drops invalid entry, makes dependent non-plotted values diagnosed
missing and charts D102 fallback, never guessing. Migration converts exact known
unit/precision/scale only; ambiguous magnitude prose needs humans.

### D294 — Chart typography uses semantic, not physical, role names

Typography omits to adaptive; mode is adaptive/fixed and adaptive-only sync group
uses D115. Closed integer overrides are category ticks 14–24, value ticks 14–28,
ordinary values 14–32, legend 16–24, series labels 16–24, axis titles 13–24,
context labels 16–24, and annotations/measurements 13–24. This replaces x/y tick
and generic datalabel names and remains semantic under horizontal orientation.
Overrides pin only their role. Adaptive grows omitted roles to deterministic fit;
fixed leaves omitted roles at floors; both retain non-lossy geometry/collisions
and fixed is not legacy behavior. Comparable siblings and valid sync groups share
automatically sized equivalent roles independently; pins neither force nor reduce
peers but must fit. Invalid membership sizes independently non-strict. Hidden/
absent/inapplicable roles cannot be authored. Segment/total/boxed/waterfall/
coverage/title/subtitle roles remain renderer-owned; title fixed 40px and subtitle
auto 22–26px. Unknown/inapplicable/noninteger/bool/out-of-range invalidates the
whole object: strict rejects, non-strict discards for diagnosed adaptive defaults.
Empty or adaptive-only object omits. D69 freezes sizes/synchronization/adaptations
with D110/DOM diagnostics and runtime JS cannot revise them.

### D295 — Chart display policy is sparse and semantic

Optional sparse display fields are ordinary_values, stack_segments, stack_totals
(show/hide) and series_identity (auto/legend/pane_title). Line/grouped/horizontal
allow ordinary+identity; stacked allows segment/total and auto/legend; combo
allows ordinary, stacked-only segment/total and auto/legend; waterfall/heatmap
forbid all. Defaults: ordinary values show for line/grouped/horizontal/combo;
stacked labels hide; stacked identity legend; others identity auto. Combo ordinary
controls line and grouped bars, but line only when stacked. It cannot hide
structural/auxiliary/context/annotation/measurement/coverage/semantic facts.
Segment and total controls are independent; authored totals imply/show totals and
conflict with hide. Auto uses all-endpoint-labels-or-complete-legend line policy,
complete bar legends except valid single headed pane-title ownership, stacked
legend, and combo line endpoints plus bar legend or one complete legend. Legend
always means complete ordered strip. Pane-title requires one headed series and
retains full accessible name; invalid for stacked/combo. Identity never vanishes
for fit: strict fails, non-strict expands diagnosed complete floor fallback.
Default-valued fields, empty object, unknown/inapplicable/contradictory fields are
invalid noise; strict rejects and non-strict discards whole object for diagnosed
defaults. Legacy visibility aliases are migrator-only. D69 freezes policy with
D110 diagnostics and runtime JS cannot alter it.

### D296 — `context_labels` are unanchored typed chart facts

Context labels are 1–4 authored-order facts with chart-local unique D115 context
ID, exact label, D213 value and optional exact short label affecting label only.
All D213 value types apply and numeric/range values require D214 formats. Facts
are unplotted/unanchored: they create no mark/series/category/axis/total/domain and
anchored/plotted facts belong elsewhere. Renderer never infers them. They paint
exactly once as one ordered block in the shared exterior lane after direct series
identities; strict fails if it cannot fit above D47 floor, while non-strict moves
the complete block below plot and never layout-drops a fact. Labels may wrap two
lines or use authored short label only after full-label failure, never to gain
size; values cannot shorten and facts cannot reorder/merge/summarize/suppress.
One common D294 context size adapts 16–24px. Facts avoid identity/legend/annotation/
measurement/coverage collisions. D97 suppresses only duplicate chrome; distinct
values survive and all facts remain in D247. Every family may use them; heatmaps
place them by/below native table without duplicate chart/table. Accessibility
exposes full label/value once. Anchors/references/style/semantics/links/evidence/
placement/geometry/type/HTML/SVG/CSS/callbacks are invalid. Strict rejects IDs/
labels/values/formats/count/fit. Non-strict drops malformed entries individually,
preserves survivors/missing/order, relocates whole block, omits none-surviving
field and diagnoses all adaptations/deduplication. Migration converts only clear
explicit unplotted label/value facts; ambiguous KPI/annotation/legend/series
meaning needs humans.

### D297 — Annotations use one typed semantic anchor

Annotations are 1–8 authored-order facts with chart-local unique D115 ID,
event/explanation role, exact text and one chart/category/data_point/category_range
anchor. References use D291 IDs; ranges are inclusive forward authored order and
point anchors require an existing finite plotted value, never null. Chart anchors
mean whole-chart explanation, not unresolved fallback. Renderer infers no timing/
causality/trend/severity/ownership/role/retargeting and owns placement/chrome/
leaders/range bands/collisions/offsets. Coordinates/offsets/style/icon/severity/
priority/score/type outside D294/HTML/SVG/CSS/callbacks/painter options are invalid.
One common annotation size adapts 13–24px. Deterministic frozen candidates prefer
nearest clear placement, then leaders/exterior/below-plot while retaining text;
annotations never convert to another semantic role. D97 removes only duplicate
chrome while D247 retains every fact. They collide with all chart chrome/facts.
Chart.js/SVG share frozen order/candidates/outcome; runtime chooses candidates
only, never text/role/anchor/size/suppression/interactivity. Heatmaps allow chart/
category/range column anchors, not data points, without obscuring values/key.
Strict rejects IDs/roles/text/anchors/references/ranges/retention. Non-strict keeps
valid semantic facts in D247, omits only failed visual chrome with exact diagnosis,
never retargets, and omits field only if none survive. Migration needs unambiguous
role/text/semantic anchor; pixels or indexes need humans.

### D298 — Measurements are authored finite-endpoint facts

Measurements are 1–4 authored-order facts with chart-local unique D115 ID,
change/CAGR role, valid series, inclusive forward range of at least two category
IDs with finite endpoints, canonical authored value, D214 format and explicit
approximate bool. Intermediate nulls stay missing. Renderer never recomputes or
verifies value; it may differ from derived results. Role owns chrome/wording,
direction derives only from formatted authored sign and is not sentiment, and
approximate adds visible/accessibility wording. Duplicate text/direction/tone/
formula/period/date/inline format/arrows/geometry/style are invalid. Allowed on
axis/waterfall families, not heatmap; waterfall uses reserved `waterfall` series
and step IDs, stacked targets one authored segment, never inferred total. Facts
never alter data/domain/totals/other roles. Renderer owns bracket/leader, complete
formatted value/role/range and deterministic placement at D294 annotation size
13–24px, clearing all chrome and moving complete facts exterior/below when needed.
D97 only deduplicates chrome; D247 retains facts and accessibility announces role,
series, endpoint labels, value and approximation. Both painters share frozen
semantics/type/candidates/outcome. Strict rejects malformed IDs/role/value/format/
bool/references/range/endpoints/family/retention. Non-strict retains valid facts in
D247, omits impossible chrome, drops malformed facts individually with diagnosis,
and never computes/retargets/reverses/substitutes. Migration of rules/CAGR/bands/
elbows requires mechanically clear role/series/range/value/format/approximation.

### D299 — Auxiliary series are aligned non-plotted numeric facts

Auxiliary series contains 1–2 authored-order, at most one per role, with unique
D115 auxiliary ID, boxed_label/authored_stack_total role, exact label, D214 format
and one canonical decimal/null per category. They create no plotted geometry,
axes/domains/legend/identity/stacking and remain in D247. Boxed labels are grouped
bar, horizontal bar, or grouped-combo only, require an existing bar target, paint consistently in
bar or outside with series connector, use one auto 12–24px size and are independent
of ordinary values. Authored totals are stacked bar/combo only, forbid target,
anchor at signed completed stack edge under D241, may differ from sum/axis format,
do not affect domain, use auto 14–24px, imply totals show and conflict with hide.
Finite authored values visually override computed category total; null remains
missing but does not suppress valid computation. Computed sign-side totals with
missing contributors withhold and use axis format. Complete D293 text never
shortens. Collisions may reserve/move/stagger/connect/reclaim; D52 forbids fit
suppression. Strict fails unresolved fit; non-strict paints floors then D102 if
overlap remains. Accessibility includes label/category/value/missing and boxed
target. Separate categories/preformatted strings/geometry/style/icons/font/CSS/
HTML/callbacks/painter options are invalid. Strict rejects structure/format/
array/role/family/target/display/fit. Non-strict only trailing-null-pads, ignores
surplus trailing entries, nulls malformed values or drops wholly unusable series,
with diagnosis and no shifting/inference. Migration requires clear role/label/
target/format/alignment.

### D300 — `category_groups` add one hierarchy level only

Category groups are 1–6 authored-order groups with chart-local unique D115 ID,
exact label, optional short label and 1–12 ordered duplicate-free D291 category
IDs. Membership is at most one group; ungrouped categories remain valid. Members
must exist, follow chart order and form one contiguous nonoverlapping span; group
order follows first member and meaningful singleton groups are allowed. Empty/
nested/overlap/repeat/noncontiguous groups are invalid. Allowed on grouped/
stacked/horizontal/combo only; combo applies across shared axis. Groups never
aggregate/subtotal/create series/axes/legends/facts, reorder/filter, or alter
pitch/values/domains/formats. Renderer owns vertical bracket/header or horizontal
equivalent while preserving individual category ownership; no authored visual
controls. Labels share category tick plan, may wrap two lines or use short label
only after full fails, with gutter/whitespace adjustment, never invented/
ellipsized/partially suppressed or shortened for larger type. D69 plans groups
before geometry. Identical sibling IDs+memberships synchronize centers/spans/type;
otherwise no label reconciliation. D247 owns group/member relationships once and
visual chrome is aria-hidden; support aligns individual IDs. Aggregates/values/
formats/series/parents/nesting/sort/visibility/style/type/geometry/HTML/SVG/CSS/
callbacks are invalid. Strict rejects structure/references/family/identity fit.
Non-strict omits malformed visual groups independently while chart facts remain,
records recoverable unresolved hierarchy in D247/diagnostics, never changes
membership/order/labels, and omits field if none remain. Migration requires clear
legacy label/short label/membership/order/contiguity.

### D301 — `coverage_callout` is one stacked-bar percentage fact

Optional singular stacked-bar-only coverage callout requires chart-local unique
D115 ID, D213 number using D293 percent format resolving to 0–100 after display
scale, exact label and optional exact period. It is authored, never derived, and
does not affect data/stacks/totals/domains/axes/identity/other facts. Renderer
presents formatted percentage, label, period in order using D50 fixed chrome:
26px/700 value, 24px/700 text, theme accessible color, about 29px line height,
without D218 or box/fill/icon/badge/decorative chrome. It occupies top shared
exterior lane before segment identities/context, reserved before D69. Plot may
shrink only to D47 floor. If unfit, strict fails and non-strict moves complete
callout below; no line loss. Label/period may naturally wrap two lines, never
abbreviate/ellipsize/rewrite/infer. It allocates/collides with all exterior facts
and labels. D247 owns complete fact once and visual is aria-hidden; both painters
share frozen lane/wording/format/type/relocation. Authored placement/line breaks/
geometry/type/style/icon/semantics/evidence/HTML/SVG/CSS/callbacks are invalid.
All other families including stacked combo forbid it. Strict rejects ID/value/
format/range/text/family/fit. Non-strict drops malformed callout whole without
data repair, relocates valid lane-unfit callout and leaves chart unchanged, with
diagnostics. Migration requires independently clear value/percent format/label/
period from the measured legacy side callout.

### D302 — `line` is a straight marker-based complete trend

Line requires 2–24 ordered categories and 1–4 primary-axis series, each with at
least two finite values. Secondary/combo fields invalid. Null preserves position,
breaks path, paints no marker/value and remains missing in D247. Lines are straight,
unfilled, marker-based and motionless; smoothing/steps/areas/interpolation/
forecasting/bands/regression/per-point style are invalid. Valid leading break and
common context/annotation/measurement are allowed; groups/auxiliary/coverage/
stacking/bar mode are not. Finite values show by default; hide removes only visual
labels. Labels use axis format, D294 ordinary 14–32px, unboxed series color, and
D53 above/below/side/leader candidates clearing marker+4px. Priority is first/last,
extrema, even coverage, then author order; first/last never suppress, others only
last-resort diagnosed with painter parity. Auto identity is all endpoint labels or
one complete legend; no partial identity. Valid one-series headed pane-title and
complete legend apply. Default palette/style/markers are D43/D99 stable by series
ID; authored style+marker pair is all-or-nothing and identity visuals stay
consistent. Marks do not scale with type. Category ownership, headroom/gutters and
D247 completeness follow shared contracts. Both painters share data/plan/identity/
type/candidates/outcome. Authored geometry/per-point/painter/interaction settings
are invalid. Strict rejects counts/finite trend/identity/data/applicability/
ownership/retention/fit. Non-strict only positional repair and accessible identity
substitution; otherwise D102 complete fallback, never interpolation/truncation or
partial trend. Migration requires unambiguous categories/series/values/format/
axes/identity.

### D303 — `grouped_bar` is vertical side-by-side comparison

Grouped bar renders 1–12 categories and 1–4 primary-axis bar series vertically
side by side, one series allowed, authored left-to-right. Positive/negative extend
from semantic zero and domain contains zero. Null preserves empty slot/missing;
finite zero paints zero anchor and visible ordinary label. Stacking/floating/
range/horizontal/per-bar color/secondary/break are invalid. Category groups,
boxed labels and common facts are allowed; totals/coverage are not. Ordinary
values default show outside bar ends, unboxed navy 700, axis-formatted at D294
14–32px with complete semantics. Collision order is generated head/footroom,
edge gutter, within-slot offset, stagger, series leader, then diagnosed suppression;
first/last categories and extrema prioritize and structural boxed labels never
suppress. Authored bounds do not expand. D160 owns thickness/occupancy and painter
rect/center/thickness parity within 2px. One headed single series may pane-title;
otherwise auto/legend is complete authored-order legend, never endpoint labels.
Palette is one primary blue then navy/accents, valid author keys win, all identity
treatments share series color while numeric labels stay navy. Groups do not
aggregate and boxes target bars independently of ordinary values. D247 is complete
and both painters share domain/zero/pitch/geometry/labels/legend/aux plan. Authored
stack/geometry/style/position/painter/interaction controls are invalid. Strict
rejects counts/domain/data/identity/applicability/geometry/retention. Non-strict
only positional/palette repair then D102 fallback; never stacks/drops/moves data.
Migration requires clear vertical nonstacked orientation/data/format/identity.

### D304 — `stacked_bar` uses sign-separated vertical stacks

Stacked bar has 1–12 categories and 2–6 primary series. Author order owns positive
bottom-up, negative top-down from zero, legend/table order. Domain contains zero
and signed extents. Null preserves missing slot; zero is data without area.
Computed totals separately sum source positive/negative sides in axis format and
withhold a side if any contributor there is missing. Segment/total labels default
hide independently. Shown nonzero segments use complete format at auto 14–24px,
prefer inside, but insufficient space/contrast moves navy text outside with series
connector; never fit-drop. Shown zero labels anchor zero distinctly. Computed
signed totals use auto 14–24px beyond stack edge and never fit-suppress. D299
authored totals may per-category visually override without geometry/domain change,
may differ format and use signed edge. Complete author-order legend is mandatory;
pane-title/endpoints invalid. Groups, coverage and common facts allowed; boxed
labels, secondary/break/stack IDs/assignments/horizontal/floating invalid. D160
owns occupancy/segments/edges/gutters with painter centers/rects/edges/anchors
within 2px. Label lanes may reserve head/foot/side/category/callout space; bounds
stay fixed. Unfit required labels strict-fail or non-strict D102 fallback, never
overlap/drop. Palette author order uses primary/navy/accents; fill/swatch/connector
match, white inside only with contrast else navy outside. D247 includes all data,
missing, complete computed sign totals, authored totals/groups/coverage/facts.
Authored stack/formula/position/style/label/geometry/painter controls invalid.
Strict rejects counts/domain/data/identity/display/facts/family/fit. Non-strict
positional repairs, withholds incomplete computed sides, drops malformed optional
facts whole, else D102; never flattens/reorders/omits series. Migration requires
clear orientation/order/data/format/display/totals/coverage.

### D305 — `horizontal_bar` is grouped-only with optional break

Horizontal bar has 1–12 top-to-bottom categories and 1–4 author-order grouped
series, one allowed, never stacking. Without break, domain contains zero and bars
extend by sign. D292 break is allowed only same-positive-side with min<to below
all finite values and no zero/crossing; bars visually start at disclosed break,
retain source values/format and represent only post-break interval without implying
zero. Negative/mixed/zero cases forbid break. Null preserves slot/missing; zero is
valid only continuous. Groups, boxed labels and common facts allowed; totals/
coverage invalid. Ordinary values default show complete beyond signed/post-break
ends, unboxed navy 700, axis formatted at D294 14–32px, never break deltas.
Collision order is side gutter, within-slot vertical offset, stagger, series leader,
then diagnosed suppression; first/last/extrema prioritize. Category labels adapt
14–24px, wrap or use short only after failure, with complete ownership. D160 owns
pitch/thickness/spacing/break/gutters; painter rect/center/thickness/break/anchors
within 2px. One headed single series may pane-title; otherwise complete ordered
legend, no endpoint identities. Grouped palette applies; identity connectors share
series color and numeric text remains navy. D247 includes data/missing/break/groups/
boxes/facts. Stacking/baseline/ranges/orientation/physical axes/break style/bar
geometry/per-bar style/label/painter controls invalid. Strict rejects counts/data/
fields/break/ownership/identity/geometry/retention. Non-strict positional repair,
removes invalid break for diagnosed safe zero domain, palette repair, else D102;
never vertical/stacked/delta conversion. Migration requires clear orientation/
grouping/data/format/identity/break semantics.

### D306 — `combo` is one bar mode plus one line layer

Combo requires grouped/stacked bar_mode, 2–12 categories, 1–4 bars and 1–4 lines.
Marks are explicit. Bars use primary; all lines share primary or all secondary,
with secondary present exactly when used; mixed ownership invalid. Paint bars,
lines, markers, then labels/chrome, preserving independent authored bar/line order.
Grouped bars follow D303, stacked D304, lines D302; null stays positional/missing
and breaks lines. No leading breaks. Groups apply shared axis. Grouped permits
boxed bar auxiliary, stacked authored totals, never opposite or coverage. Common
facts allowed; measurement uses target axis. Ordinary display controls grouped
bar+line or stacked line only, with stack labels independent. Joint collision plan
covers every mark/chrome/fact. Auto identity uses all line endpoints only if all
fit plus complete bar legend; otherwise one complete all-series legend. Legend
mode is complete authored order; pane-title invalid; swatches preserve mark/style.
Palette resolves across chart with valid authored identities and stable series IDs.
Axes validate format/domain/visibility/disclosure independently and remain clearly
associated without color alone. D160 owns shared centers/bar geometry/line points/
gutters/layers with painter geometry/anchors within 2px. D247 includes complete
data/identity/axes/totals/aux/common facts. Per-series stacks/overlay/mixed axes/
line smoothing/fill/per-point style/bar geometry/layer/axis/painter controls are
invalid. Strict rejects counts/layers/mode/axes/domain/data/identity/aux/display/
geometry/collision/retention. Non-strict positional/accessible identity repair
only, never guesses mark/mode/axis; otherwise D102 complete fallback, never paints
one layer alone. Migration requires clear categories/layers/mode/axes/format/data/
identity/auxiliary semantics.

### D307 — `waterfall` uses an explicit ordered step model

Waterfall has 2–12 authored-order unique D115 steps with exact label and change/
total/computed_total type. Change/total require canonical decimal; computed total
forbids value; null/numbers/bools/decorated/nonfinite invalid. First is total and
last total/computed. Total paints from zero and resets authored level; change
bridges current level by signed value; computed paints current level from zero
without reset. Intermediate resets/reports allowed. Renderer performs placement
arithmetic only, never infers type, treats zero specially, recomputes/reconciles/
balances/sorts/groups. Author totals remain authoritative without mismatch error.
Step IDs own categories and reserved series ID is `waterfall`. chart_data,
secondary/break/mode/groups/aux/coverage/display are invalid; common facts allowed
using reserved identity. Domain contains zero, all totals and running levels.
Renderer semantic increase/decrease/total colors are fixed. Every step has
mandatory complete axis-formatted structural 18–24px label; no display hiding.
Connectors show continuity only and semantic zero line remains, no plot grids.
Collision may reserve/offset/stagger/lead/reclaim but cannot suppress labels or
connectors; fixed bounds stay. Unfit strict-fails or non-strict D102 complete
fallback, never loss. D160 owns pitch/rects/levels/connectors/zero/anchors with
painter parity within 2px. D247 includes ordered type/authored/computed/reset facts
and accessibility distinguishes change direction/authored/computed totals.
Custom series/colors/connectors/step labels/geometry/style/formula/painter controls
invalid. Strict rejects sequence/IDs/text/type/value/rules/axis/format/fields/fit.
Non-strict never guesses or deletes/reconnects, uses complete fallback and reports
exact defect. Migration requires clear sequence/identity/type/value/format/reset.

### D308 — `heatmap` is one native semantic table

Heatmap renders one native visible D247 table, no canvas/SVG/duplicate table. Its
D255 table has a distinct deck-unique surface ID, exact stub, 1–12 value columns,
1–12 rows, no groups/type override. Cells are D213 number or missing only; every
number shares one valid D293 format. Missing is neutral em dash/accessibly Missing
and excluded from scale; at least one finite value required. Required scale is
generated from finite source values (equal values use deterministic centered
encoding) or fixed canonical min<max containing all values; bounds precede display
scaling. Renderer owns one light-to-primary-blue sequential encoding, with no
author stops/thresholds/divergence/log/reversal. Every complete formatted value
is visible with contrast-safe navy/white and cannot hide/shorten/suppress. Mandatory
scale key shows min/mid/max/shared format/missing meaning. One common 18–24px size
covers headers/labels/cells/key; no chart/table typography overrides. Navy/white
headers retain separators; data fills are semantic. Heading chrome is normal.
Context facts allowed; annotations only chart/column/column-range anchors. Point
anchors, measurements, groups, auxiliaries, coverage, axes, chart_data and display
are invalid. D69 freezes geometry/type/fills/key/fact lanes. Width redistribution,
two-line labels, row growth and authored short labels after failure are allowed;
never below 18px or alter/drop data/key. Native headers/caption/scale provide full
screen/print/capture/no-JS accessibility. Authored cell style/threshold/tooltip/
geometry/merge/group/HTML/SVG/CSS/painter controls invalid. Strict rejects shape/
IDs/cells/mixed formats/no data/scale/range/fit. Non-strict may turn malformed
cells missing; invalid/no scale paints complete diagnosed uncolored semantic table,
keeps all rows/columns at 18px, and unresolved overflow is degraded/not-ready.
Migration requires clear rectangular identities/numbers/shared format/scale.

### D309 — Diagnostics use one canonical event structure

Every diagnostic event is a closed object with required `code`, `severity`,
`phase`, semantic `role`, RFC 6901 `path`, `action`, `result`, and positive
`occurrences`. Phase is `validation`, `repair`, `plan`, `paint`, `readiness`, or
`publication`. Applicable identity fields—`slide_number`, `layout_type`, and
`surface_id`—are required when the event belongs to that scope and otherwise
omitted, never null. Optional `subjects` contains only sorted duplicate-free
arrays of modeled IDs: category, series, row, column, evidence, annotation,
measurement, context, group, or item IDs. Validation events additionally include
`expected.contract`, a short stable contract description.

Optional `input` is bounded to JSON type, exact non-prose scalar or semantic ID,
field name, string/collection length, and lowercase SHA-256 when correlation is
needed. Events never copy slide prose, notes, evidence locators, arbitrary source
objects, absolute paths, HTML, large collections, or sensitive authored strings.
`action.name` is a D311 repair/fallback action or `accept`, `reject`, `measure`,
`select_candidate`, `reserve`, `reallocate`, `deduplicate`, `suppress`, `paint`,
`check_readiness`, `publish`, or `rollback`. `result.name` is `accepted`, `failed`,
`canonicalized`, `dropped`, `missing`, `generated`, `defaulted`, `substituted`,
`flattened`, `independent`, `relocated`, `suppressed`, `deduplicated`,
`fallback_semantic_table`, `fallback_sequential`, `fallback_complete_surface`,
`fallback_unresolved`, `ready`, `published`, or `rolled_back`.

Events have no ID. Their identity is phase, slide/layout/surface, role, path, code,
canonical subjects, action name, and result name. Identical events per semantic
surface deduplicate by incrementing `occurrences`; distinct IDs may coalesce into
subjects only when action and result remain identical. Ordering is phase order,
deck before slides, slide number, surface ID, role, path, code, subjects, action,
then result. Stderr emits no info events and one deterministic line per warning or
error using only these fields; free-form diagnostic prose is not an interface.

### D310 — Diagnostic codes are a closed compatibility catalog

Renderer 3.0.0/schema v1 uses exactly these stable codes and severities:

| Family | Codes and fixed severity |
|---|---|
| Validation (`error`) | `validation.schema_version`, `validation.configuration`, `validation.required`, `validation.unknown_field`, `validation.inapplicable_field`, `validation.type`, `validation.value`, `validation.cardinality`, `validation.identity`, `validation.reference`, `validation.structure`, `validation.conflict`, `validation.fit`, `validation.accessibility` |
| Repair (`warning`) | `repair.schema_version_assumed`, `repair.field_dropped`, `repair.item_dropped`, `repair.reference_dropped`, `repair.id_generated`, `repair.position_repaired`, `repair.value_to_missing`, `repair.value_canonicalized`, `repair.prose_flattened`, `repair.format_dropped`, `repair.domain_replaced`, `repair.axis_restored`, `repair.policy_defaulted`, `repair.color_substituted`, `repair.sync_disabled`, `repair.structure_flattened`, `repair.chrome_omitted`, `repair.locator_dropped` |
| Plan (`info`) | `plan.typography_grown`, `plan.synchronized`, `plan.geometry_reallocated`, `plan.gutter_reserved`, `plan.text_wrapped`, `plan.text_rotated`, `plan.label_repositioned`, `plan.chrome_deduplicated`, `plan.identity_selected` |
| Plan (`warning`) | `plan.short_label_used`, `plan.ticks_skipped`, `plan.label_ellipsized`, `plan.label_suppressed`, `plan.surface_relocated`, `plan.conservative_metrics` |
| Plan (`error`) | `plan.unresolved_overflow` |
| Paint/readiness/publication | `paint.semantic_fallback` (`warning`), `paint.unresolved_fallback` (`error`), `paint.painter_failed` (`error`), `readiness.fonts_failed` (`error`), `readiness.geometry_failed` (`error`), `readiness.layout_failed` (`error`), `publication.transaction_failed` (`error`), `publication.rollback_failed` (`error`) |

Paths, roles, expected contracts, subjects, actions, and results identify the
specific rule; field-specific public codes are not added. A successfully repaired
non-strict defect emits its repair warning instead of also retaining the original
validation error. Codes are immutable within renderer major version 3; additions
are backward-compatible minor changes, while removal or meaning/severity changes
require renderer 4. Validation failures returned without publication retain these
same codes in the typed failure report.

### D311 — Non-strict repair and fallback actions are closed

The repair registry maps each action to exact permitted inputs and result. An
action is invalid anywhere not expressly listed here or in a composition contract.

| Action | Code/result | Permitted use |
|---|---|---|
| `assume_schema_v1` | `repair.schema_version_assumed` / canonicalized | Only when `meta` exists without `handoff_schema_version` and the complete input otherwise validates exactly as schema v1 with no legacy wrapper, alias, unknown field, or other migration. Insert version 1, diagnose, and revalidate; every genuinely legacy shape still requires D119. |
| `drop_field` | `repair.field_dropped` / dropped | Unknown field; forbidden optional common field; default-valued serialization noise; one contradictory hidden-axis control. Never remove required or composition-critical meaning. |
| `drop_item` | `repair.item_dropped` / dropped | Only where the detailed composition contract explicitly permits individual removal and minimum cardinality plus semantic completeness still hold. Permitted examples include optional context/annotation/measurement facts, risk/opportunity items, metric changes, decorative icons, and malformed process/milestone/layer/pipeline components under D272–D277. Never chart series/categories, table rows/columns, legal prose, recommendation/state content, or relationship items whose removal would reconnect or alter a decision tree, feedback loop, hierarchy, or stakeholder relation; otherwise use the complete named fallback or D180 unresolved slide. |
| `drop_reference` | `repair.reference_dropped` / dropped | Invalid optional evidence/footer/provenance reference or optional visual fact reference where the owning authored fact remains complete. |
| `drop_optional_fact` | `repair.item_dropped` / dropped | Complete optional callout, auxiliary series, decorative icon, unused evidence entry, or other standalone fact only where its detailed contract explicitly authorizes whole-fact removal; required facts and minimum cardinality remain. |
| `generate_positional_id` | `repair.id_generated` / generated | Missing/malformed/duplicate D115 identity only where its detailed contract permits; generated ID disables cross-slide synchronization/continuity. |
| `pad_trailing_null` / `drop_surplus_tail` | `repair.position_repaired` / canonicalized | D228 chart/auxiliary positional arrays only; never shift or insert within the sequence. |
| `replace_with_missing` | `repair.value_to_missing` / missing | Invalid D213 value or individual chart point where positional missing is explicitly allowed. |
| `collapse_equal_range` | `repair.value_canonicalized` / canonicalized | D188 range whose finite endpoints are exactly equal becomes the equivalent scalar number with the same format; no other range repair is allowed. |
| `flatten_prose_runs` | `repair.prose_flattened` / flattened | D224 prose whose complete authoritative concatenated wording is valid but emphasis structure alone is malformed becomes one plain run; text/order cannot change. |
| `drop_format` | `repair.format_dropped` / dropped | Invalid D293 registry entry; all non-plotted dependents become missing and dependent charts use the complete semantic fallback. |
| `replace_domain` | `repair.domain_replaced` / defaulted | Invalid generated/fixed domain or unsupported break becomes one deterministic safe generated continuous domain when a valid format and data remain. |
| `restore_category_axis` | `repair.axis_restored` / defaulted | Hidden category axis lacks another complete visible owner. |
| `default_typography` / `default_display` | `repair.policy_defaulted` / defaulted | Discard the malformed subgroup whole and apply its canonical defaults; never retain valid-looking fields from it. |
| `substitute_theme_color` | `repair.color_substituted` / substituted | Replace only an invalid/inaccessible authored semantic palette key with nearest role-valid accessible theme key. |
| `disable_sync` | `repair.sync_disabled` / independent | Invalid `sync_group` syntax, membership, or role comparability; surface then sizes independently. |
| `flatten_structure` | `repair.structure_flattened` / flattened | Drop malformed optional grouped headers/category hierarchy while preserving all leaves, or turn invalid aligned support into a complete independent support table. |
| `convert_outlined_support` | `repair.structure_flattened` / flattened | Convert the complete unfit/invalid outlined support to D266 support table without losing any row, column, value, or identity. |
| `omit_visual_chrome` | `repair.chrome_omitted` / dropped | Preserve a valid annotation/measurement/group relationship in D247 while omitting only invalid or impossible visual chrome. |
| `drop_locator` | `repair.locator_dropped` / dropped | Remove malformed opaque evidence locator while retaining valid source name. |
| `relocate_complete_block` | `plan.surface_relocated` / relocated | Move a complete context or coverage block to its specified below-plot fallback; never split or drop facts. |
| `use_semantic_table` | `paint.semantic_fallback` / fallback_semantic_table | Replace one malformed chart pane with its complete D247 table beneath retained title chrome. |
| `use_sequential_fallback` | `paint.semantic_fallback` / fallback_sequential | Use only the complete sequential fallback explicitly owned by that composition. |
| `use_complete_surface_fallback` | `paint.semantic_fallback` / fallback_complete_surface | Use a composition-owned complete `ordinary_table`, `relationship_table`, `nested_outline`, `ordered_list`, `grouped_sections`, `plain_cover`, `plain_divider`, `legal_pane`, or `retained_hero` fallback. `fallback_kind` is required, and each kind is legal only where the detailed composition contract expressly owns it. |
| `use_unresolved_slide` | `paint.unresolved_fallback` / fallback_unresolved | D180 slide fallback retaining only validated common content when no semantic composition can survive. |

Every action records bounded before/after state, code, path, semantic identity, and
result. Repairs run on the typed repair candidate, then the complete canonical
model is revalidated before planning. No recursive best-effort retry exists.
Non-strict mode may still fail with no publication when neither this registry nor
a named complete fallback applies.

### D312 — Run metadata, plan summaries, failures, and publication are exact

`run_meta.json` is a closed deterministic object with:

```json
{
  "renderer_version": "3.0.0",
  "handoff_schema_version": 1,
  "theme_id": "boardroom_amex",
  "status": "clean",
  "ok": true,
  "options": {"strict": true, "debug": false, "svg_only": false},
  "slide_count": 44,
  "slides": [],
  "severity_counts": {"info": 0, "warning": 0, "error": 0},
  "events": [],
  "plans": [],
  "static_readiness": [],
  "artifacts": []
}
```

`status` is clean or degraded; failed calls publish no metadata. Slides contain
number, layout, applicable section, and ordered surface IDs. Each plan contains
surface ID, semantic role, stable semantic digest, integer design-stage region,
resolved role sizes, display/identity strategy where applicable, ordered
adaptation codes, reservations, fallback, expected placement classes, and
painter-plan digest. Static readiness records only facts available before
publication: frozen plan attached, required HTML/SVG/canvas/plugin payload present,
semantic table present, stable IDs resolved, and readiness-contract version.
Actual browser facts—vendored fonts loaded, nonzero Chart.js chart area/dataset
geometry, plugin completion, stable subsequent animation frame, clipping/overlap,
and measured Chart.js/SVG geometry parity—exist only in D315 external release
evidence. `render_deck` never launches Chromium. This narrows D250's illustrative
readiness/parity metadata wording. `artifacts` records name, bytes, and SHA-256 for
the other four D250 artifacts; `run_meta.json` does not self-hash or self-count.
External D315 evidence hashes all five.

Plans exist for every planned surface even when no adaptation event occurs.
Events are only D309 changes/failures and use D309 order. Plans follow slide order,
fixed composition-slot order, authored repeatable-surface order, then surface ID.
JSON uses schema-defined key order, authored array order, two-space indentation,
UTF-8/LF, and one trailing newline.

Rendered surfaces expose only compact, deterministic attributes:
`data-surface-id`, `data-plan-sizes` as sorted `role:px` pairs,
`data-plan-adaptations` as ordered codes, `data-diagnostic-codes` as sorted unique
codes, `data-diagnostic-count`, and applicable `data-chart-fallback`. They never
embed full events, authored prose, raw plans, or environment data.

Typed renderer failures contain status failed, renderer/schema versions when
known, deterministic severity counts, and the complete ordered D309 event array.
They publish no artifacts. Configuration failures use `RendererConfigurationError`;
handoff/schema/planning failures use `RendererValidationError`; publication or
rollback failure uses `RendererPublicationError`.

Publication validates/repairs/revalidates, freezes the complete deck plan, stages
all five D250 files in a sibling directory, verifies names/encoding/schema copy/
readiness, finalizes metadata, syncs closed files, then atomically replaces the
output or performs rollback-safe Windows replacement. Strict failure or an
unrepairable non-strict failure preserves prior output byte-for-byte. Degraded
non-strict output publishes all five together. No timestamps, absolute paths,
UUIDs, random IDs, environment values, or partial files enter the destination.

### D313 — Every legacy layout input has one migration disposition

The inventory is the union of the current dispatch registry, schema map, aliases,
and unspecified sentinels: 57 distinct inputs, classified exactly once as 37
conditionally deterministic, 17 human decisions, and 3 removed sentinels.
“Deterministic” requires the stated semantic proof; failed proof emits an
unresolved migration decision and never falls through to a guessed target.

#### Deterministic dispositions

| Legacy input | Schema-v1 target | Required proof |
|---|---|---|
| `annex_table` | `annex_table` | One complete dense typed matrix and disclosure boundaries. |
| `before_after`, `before_after_detailed` | `state_transition` | Explicit before/after boundaries; detailed form may add explicit steps. |
| `chart_hero_dual` | `chart_hero_dual` | Exactly one chart, recognized hero, and at most one typed support. |
| `circular_process` | `feedback_loop` | One explicit ordered cycle; causal kind only with explicit edge effects. |
| `combo_chart` | `single_chart`/`combo` | Explicit marks, bar mode, axes, categories, values, formats, identities. |
| `comparison_grid`, `three_column_comparison` | `comparison_cards` | One complete 2–4 peer by 2–4 shared-fact table. |
| `data_table`, `table` | `data_table` | One complete typed ordinary table. |
| `data_table_with_insight` | `data_table` plus optional takeaway | Complete table and one unambiguous slide-level insight. |
| `decision_tree` | `decision_tree` | Explicit root, decisions, labeled branches, targets, and outcomes. |
| `dual_chart` | `dual_chart` | Exactly two ordered charts with no hero/support semantics. |
| `ecosystem_map` | `stakeholder_map` | One focal entity and only explicitly labeled/directed focal spokes. |
| `evidence_cards` | `evidence_review` | Exact findings and explicit evidence mappings. |
| `full_process_flow`, `horizontal_process` | `process_flow` | Genuinely linear ordered steps; orientation carries no semantics. |
| `grouped_annex_table` | `grouped_annex_table` | One or two explicitly headed complete annex matrices. |
| `grouped_bar_chart` | `single_chart`/`grouped_bar` | Explicit vertical non-stacked data, format, and identity. |
| `heatmap` | `single_chart`/`heatmap` | Rectangular identities, numeric/missing cells, one format, explicit scale. |
| `hierarchy_tree` | `hierarchy` | Explicit root, uniform relation, links, and sibling order. |
| `horizontal_bar_chart` | `single_chart`/`horizontal_bar` | Explicit grouped horizontal semantics and valid optional break. |
| `icon_grid` | `feature_cards` | Equal-rank cards and decorative icons from the closed registry. |
| `ir_bullet_sheet` | `narrative` | Text-only with explicit paragraph/list boundaries. |
| `line_chart` | `single_chart`/`line` | Explicit categories, series, values, axes, formats, and identities. |
| `metric`, `metric_dashboard` | `metric_overview` | One canonical 2–6 metric source without unresolved duplicates. |
| `metric_row_with_breakdown` | `metric_overview` | Explicit metric and narrative-detail boundaries. |
| `pill_comparison` | `period_comparison` | Explicit current/comparison/variance roles. |
| `priority_matrix` | `quadrant_matrix` | Explicit binary axes/endpoints and item assignments. |
| `quote_card` | `quotation` | Explicit quote paragraphs and attribution fields. |
| `recommendation_with_rationale` | `recommendation_case` | One exact recommendation and explicit rationales. |
| `risk_opportunity` | `risk_opportunity_review` | Explicit risk/opportunity membership. |
| `section_divider` | `section_divider` | Registered section and correct immediate placement. |
| `stacked_bar_chart` | `single_chart`/`stacked_bar` | Explicit stack order/data/format/display and optional totals/coverage. |
| `timeline` | `timeline` | Explicit milestones/time labels in authored order. |
| `waterfall_chart` | `single_chart`/`waterfall` | Explicit ordered step roles, values, format, and resets. |

#### Human dispositions

| Legacy input | Candidate target(s) | Why no automatic choice exists |
|---|---|---|
| `brand_cover` | opening/closing cover | One recipe served both deck boundaries and mixed brand fields. |
| `brand_divider` | section divider/closing cover | Current Amex uses both meanings. |
| `causal_loop` | feedback loop | Legacy arrows do not prove causal edge polarity. |
| `comparison_with_metrics` | comparison cards/metric overview/separate slides | Detached metric ownership is ambiguous. |
| `cover` | opening/closing/other | Alias of ambiguous `title_or_opening`. |
| `data_flow_diagram` | data pipeline/process flow/layered architecture/future | Generic graph does not prove relationship semantics. |
| `freeform_grid` | any applicable D210 composition | Coordinates are presentation, not semantics. |
| `guidance_statement_card` | metric overview | Ranges, periods, status, and qualification ownership need confirmation. |
| `insight_with_evidence` | evidence review/recommendation/narrative/other | “Insight” and evidence ownership are ambiguous. |
| `kpi_trend_cards` | metric overview/comparison/chart | Cards may encode metrics, peers, trends, or duplicates. |
| `multi_panel` | dual chart/chart hero/named composition/future | Only exact recognized semantic shapes can convert. |
| `process_with_decisions` | decision tree/process flow/future | Branch targets and node roles are not explicit. |
| `roadmap` | timeline/process flow/future | Chronology versus procedure/phases is ambiguous. |
| `source_deep_dive` | evidence review/quotation/narrative/other | Finding, quotation, and provenance ownership are unclear. |
| `split_text_visual` | narrative/state transition/comparison/other | Split geometry does not identify semantic roles. |
| `system_architecture` | layered architecture/hierarchy/data pipeline/stakeholder/future | Nodes and links do not prove grouping, parentage, flow, or spokes. |
| `title_or_opening` | opening/closing/divider/ordinary | Legacy name conflates title and deck role. |

The empty string, `default`, and `other` are removed sentinels with no target.
Removing a sentinel never removes its slide; the migrator proves a D210
composition or records it unresolved. The migration report lists all 57 inputs,
classification, proof result, target or candidates, source paths, and decision
status. `--check` succeeds only when every source slide has a resolved target and
no schema-v1 marker is written while any human decision remains.

### D314 — The canonical 44-slide Amex migration is explicit

The release input uses schema v1 with sections `earnings` (slides 2–22), `appendix`
(slides 24–37), and `legal` (slides 38–43). Slide 23 introduces `appendix`; covers
omit section. Evidence registry contains `amex-q1-2026-p01` through `p44`, each
named `American Express Q1 2026 Earnings Presentation` with opaque PDF hash,
physical page, and zero-based index locator; each slide links its page entry and
no source footer is inferred. Synthetic simulation evidence and all operational
`pass_*`, issue, renderer, or fidelity speaker notes are omitted. Number formats
are the minimal required combinations of D293 unitless, USD, percent, percentage
points, 0–2 decimals, and minus/parentheses styles. IDs are reviewed semantic
slugs and repeated series/categories reuse IDs only where continuity is intended.
The source PDF, merged corrected fixtures/tests, and bounded mutation contracts
outrank the archived v10 handoff.

| Slide | Composition | Canonical semantic migration |
|---:|---|---|
| 1 | `opening_cover` | Exact title `American Express Earnings Conference Call`; separate period `Q1'26` and date `April 23, 2026`. |
| 2 | `narrative` | Seven Business Highlights in exact order with valid D224 emphasis; Statistical Tables reference in disclosure. |
| 3 | `period_comparison` | Five metric rows; Q1'26/Q1'25/YoY roles; typed financial/EPS/share values; FX/non-GAAP notes in disclosure. |
| 4 | `single_chart` | Reported/FX-adjusted line over Q1'25–Q1'26, percent axis, category-aligned G&S/T&E support, leap-year explanation annotation. |
| 5 | `single_chart` | One UCS billed-business line plus independent generation support table; D302 collision contract applies. |
| 6 | `dual_chart` | Spend Growth grouped bars and Retention horizontal bars with valid 90% leading break; left-chart `+ ~6 percentage points` explanation annotation (category_range q1-25–q1-26); disclosure retains the 6pp source claim and is not recomputed from displayed endpoints. |
| 7 | `comparison_cards` | Lodging/Restaurants/Airlines peers with shared premium/member-growth, UCS benchmark, and multiplier facts; benefit detail in disclosure. |
| 8 | `single_chart` | FHR+THC/UCS Lodging line, four-item lodging `metric_strip` (3,400+ / 300+ / $600 / $550), `10x` / partner-funded detail in disclosure; duplicate 50%/5% metrics removed as chrome. |
| 9 | `single_chart` | Commercial FX-adjusted line plus independent U.S. SME/Large & Global/Total support table. |
| 10 | `single_chart` | ICS Reported/FX-adjusted line plus independent segment support; duplicate `Reported` annotation removed. |
| 11 | `single_chart` | Transaction Growth line with leap-year chart explanation. |
| 12 | `chart_hero_dual` | Stacked chart heading `Proprietary New Cards Acquired`, subtitle `in millions`; metric-stack heading `Proprietary New Accounts Acquired`, subtitle `Q1'2026`, with 66% and 73%; definitions in disclosure. |
| 13 | `single_chart` | Two-series grouped bars for Total Balances/Billed Business, outside percent-0 values, Q1'25–Q1'26. |
| 14 | `dual_chart` | Grouped-bar panes `30+ Days Past Due` and `Net Write-Off Rates`; percent-1 preserves 1.3% and 2.0%; correct pane ownership. |
| 15 | `single_chart` | Signed stacked Total Provision with usd_0 authored stack totals and category-aligned outlined Reserve Rate support (`stub_header` = row label); no duplicate key-stat total. |
| 16 | `data_table` | Five revenue rows with Q1'26/Q1'25/reported YoY/FX-adjusted YoY and typed USD/percent cells. |
| 17 | `dual_chart` | Net Card Fees grouped bars Q1'19–Q1'26 usd_1 (`$0.9…$2.8`) with authored 17% CAGR measurement; FX-adjusted YoY line Q1'24–Q1'26; qualification disclosure. |
| 18 | `chart_hero_dual` | NII grouped bars usd_1 (`$4.2…`) with YoY boxed labels; `NII: Volume & Margin Drivers` driver card with all four source rows and CAGR subtitle. |
| 19 | `single_chart` | Reported/FX-adjusted revenue line, category-aligned USD support row, leap-year explanation, no duplicate identity chrome. |
| 20 | `period_comparison` | Seven expense rows Q1'26/Q1'25/variance plus 44.7% VCE metric strip; exact commentary reference in disclosure. |
| 21 | `chart_hero_dual` | Left stacked-bar/secondary-line combo `Capital Return & Common Shares Outstanding`, authored stack totals, ROE outlined support; right driver card heading `Capital Summary` with 58%, 74%, 10.5%, and 10–11% facts; regulatory notes in disclosure. `Capital Summary` is new neutral structural wording required by D170—not source-derived—and becomes explicitly authored only through final approval of this candidate. |
| 22 | `metric_overview` | `Full-Year 2026 Guidance`: revenue-growth 9–10% and EPS $17.30–$17.90 ranges plus exact qualification detail; no inferred midpoint/status/tone. |
| 23 | `section_divider` | Payload only references `appendix`; visible wording derives from registry. |
| 24 | `single_chart` | Six customer-type growth bars, three explicit category groups, boxed-label `% of Total Network Volumes` series (not `outlined_support`; long stub overflows the role floor), and `$486B Total Network Volumes` annotation. |
| 25 | `data_table` | Currency exposure table with share and signed YoY currency change; unavailable value is missing; both FX notes disclosed. |
| 26 | `data_table` | Correct source orientation: columns Restaurants/Lodging/Airlines/Other/Total T&E; rows YoY Growth and % of Total Billed Business. |
| 27 | `dual_chart` | Unemployment and GDP line panes, three stable scenario identities each, Q1'25–Q1'28, percent-1 including negatives, exact scenario/SAAR disclosure. |
| 28 | `dual_chart` | Stacked panes `Funding Mix` and `Deposit Programs`, each subtitle `$ in billions`; authored usd_0 stack totals, on-stack percent segments, and one approved 92% FDIC annotation; no pseudo-title totals. |
| 29 | `narrative` | Variance-analysis introduction and first six exact ordered items; no freeform geometry. |
| 30 | `narrative` | Remaining six exact ordered variance items; no synthetic `(cont.)` title. |
| 31 | `annex_table` | Flat Q1'25–Q1'26 table with no column groups; Reported/FX-adjusted Billed Business, G&S, T&E, Processed Volumes and CAGR rows; sparse Processed/CAGR values sit under Q1'26 and preceding cells are missing. |
| 32 | `grouped_annex_table` | Two peers, `Commercial Services` and `International Card Services`, each complete Reported/FX-adjusted segment table. |
| 33 | `annex_table` | Complete Total Balances GAAP/FX/YoY/CAGR matrix, `$ in billions`, explicit missing. |
| 34 | `annex_table` | Complete Revenue reported/FX matrix, `$ in millions`, Q1'26/Q1'25/YoY. |
| 35 | `annex_table` | Complete Net Card Fees GAAP/FX/YoY/CAGR matrix, `$ in billions`, explicit missing. |
| 36 | `annex_table` | Complete Net Interest Income GAAP/FX/YoY/CAGR matrix, `$ in billions`, explicit missing. |
| 37 | `annex_table` | Complete Revenues Net of Interest Expense GAAP/FX/YoY matrix, `$ in billions`; no invented CAGR. |
| 38–43 | `legal_notice` | One contiguous `forward-looking-statements` six-part notice; exact source paragraphs/page boundaries, title only on part 1, renderer-owned continuation wording. |
| 44 | `closing_cover` | Exact title `American Express`; no synthetic subtitle/period/date or authored brand controls. |

The migration candidate must match this worksheet, preserve every source fact and
qualification, contain no unresolved decisions, validate strict-clean, and pin
source-page identity. Full numeric matrices remain sourced from the PDF and
corrected tracked fixtures rather than being duplicated into prose. Any mismatch
between those authoritative sources is a migration failure requiring explicit
human resolution, not renderer inference.

### D315 — Release evidence is one immutable versioned manifest

Renderer 3.0.0 evidence lives under `artifacts/renderer_3_release/3.0.0/` with
`acceptance_manifest.json`, README, checksums, and these directories:

```text
inputs/      canonical_amex_handoff_v1.json, handoff_schema_v1.json,
             migration_report.json, source_manifest.json,
             Q1-2026-Earnings-Presentation.pdf
contracts/   validation.json, diagnostics.json, determinism.json,
             accessibility.json, typography_calibration.json,
             targeted_fixtures.json
chartjs/     render/ (exactly the five D250 outputs), readiness.json,
             geometry.json, slides/01–44
svg/         render/ (exactly the five D250 outputs), readiness.json,
             geometry.json, slides/01–44
comparison/  slide_map.json, semantic_parity.json, geometry_parity.json,
             accessibility_parity.json, pdf_review.md
```

`chartjs/render/` and `svg/render/` are the renderer output roots and each contains
exactly D250’s five files; readiness, geometry, screenshots, and reports are
external sibling evidence. The exact public source PDF is committed once under
`inputs/` so release evidence never depends on a Downloads path or moving URL;
`source_manifest.json` records its SHA-256 and source-page identity. The manifest
records manifest/renderer/schema versions, `boardroom_amex`, 1920×1080 stage,
repository and exact 40-hex commit, handoff/schema/reference-PDF SHA-256 values,
both render modes, required gates, deliberate divergences, and every evidence
artifact except `acceptance_manifest.json`, `README.md`, and `checksums.sha256`,
using repository-relative POSIX path/SHA-256/bytes/media type/purpose. It contains no timestamps, absolute paths,
machines, users, or random IDs. `checksums.sha256` hashes the manifest and every
manifest-listed artifact, but never itself. Exactly `acceptance_manifest.json`,
`README.md`, and `checksums.sha256` are unlisted; the verifier rejects every other
missing or unlisted path.

Required gates are schema drift, zero-unresolved migration, strict-clean Chart.js,
strict-clean SVG-only, 44/44 paint readiness in both, semantic parity, contracted
geometry parity, accessibility, two-render byte determinism for all five outputs
in each mode, font calibration, sparse/dense/long-label/mixed-sign/malformed
fixtures, and complete identity-safe qualitative human PDF review. Required gates
must be `passed`; skipped, missing, warning, unreviewed, or not-applicable does not
pass. Both run metadata files report renderer 3.0.0, schema 1, clean/ok, 44 slides,
and zero warnings/errors. The copied schema is byte-identical in inputs and both
renders.

Semantic parity compares identities, order, formatted values/missing, units,
precision/scales, contexts, annotations, measurements, auxiliaries, groups,
coverage, semantic-table associations, disclosure, evidence, notes, and source
ownership. Geometry parity checks only contracted 1920×1080 behavior: D47 floors,
2px chart geometry/alignment tolerances, label placement classes/clearance,
title-band alignment, no overlap/clipping/gridlines, transparent chart bodies,
and complete legend/context/callout lanes. It never uses MAE, SSIM, or whole-slide
similarity. Each deliberate PDF divergence has stable ID, slide, contract refs,
exact reason, and explicit human approval. Evidence directories are immutable;
correction requires a new renderer-version directory.

### D316 — Canonical precedence and final confirmation

Accepted decision history remains as rationale, but implementation reads the
later canonical contracts. Explicit precedence is:

- D127–D131 supersede broader cross-theme/raw-color language in D16/D56/D98/D128.
- D218/D294 replace legacy `auto`, x/y tick, and generic datalabel controls in
  D4/D20/D41/D45; canonical mode is adaptive and axis roles are semantic.
- D293 supersedes arbitrary unit/position wording in D74–D90/D144–D145/D214.
- D287–D290 supersede illustrative common-field, takeaway, disclosure, and
  `chart_config` shapes in D169/D212/D219–D227.
- D228/D291 require canonical decimal strings for plotted data, narrowing D91.
- D256 supersedes nested/two-level group interpretations in D142.
- D154/D210 remove generic multi-panel and catch-all composition targets.
- D245/D307 forbid missing waterfall steps, superseding D162’s earlier branch.
- D295 supersedes D164’s illustrative display wording.
- D283–D286 supersede earlier incomplete D203–D206 payload details.
- D290–D301 are the canonical common chart envelope and chart-fact contracts.
- D302–D308 are the canonical seven chart-family contracts, superseding
  intermediate D239–D246 details where wording differs.
- D64/D125/D249 establish `impact_slides.renderer_v3` as the new package and
  retain `impact_slides.renderer_v2` as the separate frozen legacy renderer,
  superseding earlier in-place replacement assumptions.
- D309–D315 close diagnostics, repair, migration, canonical-corpus, and release
  evidence contracts. D311's closed actions and explicitly composition-owned
  fallback kinds supersede earlier illustrative non-strict transformations; an
  earlier clause without a D311 action or named complete fallback fails rather
  than creating another repair.

The old standing directions are fully resolved by D5–D15, D24–D25, D31–D53,
D63, D69–D109, and D294–D308. No composition or chart family remains undefined.
Finalization is complete: D1–D316 are present exactly once; 29 compositions and
seven chart families are defined; 57 migration inputs are classified; all 44 Amex
slides are mapped; no product choice remains pending; and the user explicitly
approved this specification, including the five caveats recorded above.
Dependency-ordered implementation tickets may be created from this final contract.
