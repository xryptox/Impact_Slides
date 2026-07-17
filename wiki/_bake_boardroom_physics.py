# -*- coding: utf-8 -*-
"""Bake full Boardroom component physics from live_copilot_sim into Renderer prompt."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
RENDERER = ROOT / "Impact Slide Renderer - Copilot and ChatGPT.md"

# Full replacement from "## Layout Renderers" through end of ### `other` (before Speaker Notes)
LAYOUTS = r'''## Layout Renderers (per `layout_type`)

Render exactly one body per slide based on `layout_type`. Fill the 1920×1080
canvas with **story + facts** using **Boardroom component physics** (this section),
not four obligatory chrome bands and not a lone SVG on a dead half-canvas.

### Packing + depth (Boardroom)

| Element | Source | When to paint on face |
|---|---|---|
| `<p class="subtitle dek">` | **one dek**: prefer `content.subtitle`, else `content.headline` | Non-empty; **never stack** both under title (see Dek merge) |
| `<p class="lead-band">` / context | `content.body_text` | When packing allows; on splits often **above** rails |
| `<div class="insight-strip so-what-callout">` | `content.so_what` | Under the hero; muted navy line — **omit** if only restates title/dek |
| **On-face `narrative-bridge` / story-bridge** | — | **Never.** Hide/remove. Integration belongs in **speaker notes only** |
| `<div class="source-strip">` | source_file **names only** | Optional on metric / true table / chart; never E#### |

### Packing defaults (if `packing_mode` missing)

| layout_type | default packing | Prefer |
|---|---|---|
| `title_or_opening` | `cover-led` | bi-band cover · title · dek · goal; **no** context/so_what |
| `metric_dashboard`, `data_table`, charts, heatmap | `stat-led` | numbers dominate; insight under grid/chart |
| `timeline`, `full_process_flow`, `roadmap` | `sequence-led` | steps/rail dominate |
| `quote_card` | `voice-led` | quotes dominate; multi drops face so_what |
| `split_text_visual`, `comparison_grid`, `icon_grid`, `other` | `argument-led` | dual-rail / cards + **one** insight |

**Density floor:** layout carrier + ≥2 non-redundant layers from `{dek, body_text, so_what}` (bridge does **not** count toward face density — it is notes-only). Prefer omit over filler.

**Hard-banned face openers:** `This means` · `The implication is` · `That puts` · `To put a fine point` · `In other words` · `This sets up` · `Key takeaway` · `Bottom line`.

### Dek merge (auto)

Under the title paint **exactly one** dek line via `chosen_dek()`:

1. Prefer `content.subtitle` when present.
2. Else `content.headline`.
3. If both present and near-duplicate (equal / substring), keep the longer or the subtitle.
4. If headline is mostly numeric inventory already on KPIs/title and subtitle is framing prose → keep **subtitle**.
5. **Never** render a second under-title line for the leftover headline — proof lives in KPIs / bullets / so_what / charts.

### Slide-1 hard title + renumber

Slide 1 is always `title_or_opening`. If Builder put a semantic layout on slide 1,
insert it as slide 2, renumber, carry `narrative_bridge` intent into **notes** for the
new next slide (not onto face rails).

### When Builder leaves depth empty

Prefer omit. Only synthesize if density floor would fail **and** you can add a new
mechanism (not a rewrap). Never invent on-face bridges. Never invent comparison
card bodies like “Keep this open through close.”

---

## Boardroom Component Physics (contracts)

Shared CSS classes must match Brand & Theme tokens. Content-height cards; pack-from-top;
`align-items: start` on short lists; no flex-grow on 2–3 item rails.

### 1. Split dual-rail + proof / fact (`split_text_visual`)

**Structure (never loner-icon half-canvas when proof data exists):**

```text
[ full-width lead-band from body_text (argument-led may promote so_what → lead when body empty) ]
[ gap ~40px ]
[ split-layout 1fr 1fr — twin soft panels, equal columns ]
   left:  navy-hat argument kicker + bullet-list (argument spine)
   right: navy-hat panel kicker + proof-list OR fact-grid (evidence facts)
```

**Left bullets** = argument spine. **Right points** = evidence facts (orthogonal).

**Right panel source order**
1. Matrix `steps_or_data` rows with ≥2 cells → **fact-panel** (2–4 tiles)
2. Else `content.supporting_points` strings (if Builder sent them)
3. Else string `steps_or_data` (dedupe vs left bullets)
4. Cap **2–4**; else large semantic icon-only fallback

**Fact tiles (Platform | Region etc.)**
- Prefer header row detection (`platform`, `region`, `metric`, `name`…).
- **Primary large value** = platform / entity name (Resy, Tock, TheFork, Combined).
  **Secondary label** = region (US, Europe…). Never hero two identical region codes.
- Header-aware `platform_first`; if missing, regionish set `{us,usa,uk,eu,europe,global,apac,latam,emea}` forces name-as-value.
- Fact-panel is `display:flex; flex-direction:column; padding:0` with **full-bleed** navy hat above the grid (never grid lands hat beside tiles). `border-radius:16px; overflow:hidden` on both rails so hats match.

**Hats (both rails)**
- Identical shape: min-height ~64px, pad `16px 22px`, font-size **26px**, weight 700, mixed-case (not tiny uppercase 13px bars).
- **Left hat (`argument` kicker)** content-derived — not the static phrase “The argument”:

| Signal in title/headline/section | Left hat |
|---|---|
| integrat / continuity | Why continuity |
| advisor / leadership / operator / ceo | Who to keep |
| risk | Open risks |
| analyst / street / research | What street says |
| venue / network / map / platform / scale | The map |
| dining / experience / growth / engagement | The case |
| deal / cash / $ | The deal |
| section How / Why / Now | How it works / Why it matters / What next |
| else | The case |

- **Right hat (`panel` kicker)** for argument-led only (omit on non-argument packs if empty of meaning):

| Signal | Right hat |
|---|---|
| integrat / continuity | What continuity buys |
| leadership / operator / advisor | Who stays |
| risk | What stays open |
| street / analyst | Street check |
| map / platform / venue / scale | How the maps join |
| dining / engagement / engine | Where dining fits |
| deal / cash | What the check buys |
| section How / Why / Now | How this lands / What makes the case / What to watch |
| else | In the evidence |

**Do not** insert artificial `(n−1)` spacers to force first proof to align with last left bullet — top-align both columns; kicker is a compact header tight above the proof list.

**Proof list:** icon-sm + line; body type **22px** matching left bullets.

```html
<div class="split-stack">
  <p class="lead-band"><!-- body_text or promoted so_what --></p>
  <div class="split-layout"><!-- 1fr 1fr -->
    <div class="text-column visual-panel proof-panel">
      <h3 class="panel-kicker"><!-- argument kicker --></h3>
      <ul class="bullet-list"><li>…</li></ul>
    </div>
    <aside class="visual-panel proof-panel"><!-- or fact-panel -->
      <h3 class="panel-kicker"><!-- panel kicker --></h3>
      <ul class="proof-list">…</ul><!-- or fact-grid -->
    </aside>
  </div>
</div>
```

```css
.layout-split .split-stack { display:flex; flex-direction:column; gap:40px; width:100%; }
.layout-split .split-layout { display:grid; grid-template-columns:1fr 1fr; gap:22px; align-items:start; }
.layout-split .visual-panel { background:var(--panel); border:1px solid var(--panel-border);
  border-radius:16px; overflow:hidden; display:flex; flex-direction:column; padding:0; }
.layout-split .panel-kicker { margin:0; background:var(--navy); color:#fff; font-size:26px;
  font-weight:700; letter-spacing:-0.01em; text-transform:none; min-height:64px;
  padding:16px 22px; display:flex; align-items:center; }
.layout-split .bullet-list, .layout-split .proof-list { list-style:none; margin:0;
  padding:6px 22px 16px; display:flex; flex-direction:column; gap:12px; }
.layout-split .bullet-list li, .layout-split .proof-list li {
  font-size:22px; line-height:1.35; color:var(--ink); display:flex; gap:10px; align-items:flex-start;
  flex:0 0 auto; }
.layout-split .fact-panel .fact-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px;
  padding:6px 22px 16px; }
.layout-split .fact-value { font-size:28px; font-weight:700; color:var(--navy); font-family:var(--font-num); }
.layout-split .fact-label { font-size:16px; color:var(--ink-muted); font-weight:600; }
```

---

### 2. Metric dashboard

- Carrier: `content.key_stats[{label,value,source}]` (render-critical), cap **6**.
- Grid matrix: n≤3 single row; **n==4 dense-2x2** (`cols=2`); n=5–6 three-col multi-row.
- Value `--fs-kpi` ~70 blue tabular; label ~24 / weight 700 (~0.34× value).
- Optional small icon on card; **strip E#### from source meta** if shown.
- `so_what` → **insight-strip under grid** (not footer auto-bottom, not duplicate ribbon).

---

### 3. Data table

| Condition | Render |
|---|---|
| ≤2 columns **and** 1–6 body rows | **Table-as-KPI** — same KPI grid language as metric (`layout-table-as-kpi`) |
| Else | True Boardroom table |

True table: navy-hat `th` (size ≥ body, ~20 vs ~18), **all cells center by default**,
**no vertical separators** between header cells, optional zebra, insight under frame.
Ledger frame for short 2-col when *not* KPI-mapped: constrained max-width, not full wash.

---

### 4. Timeline / roadmap / process

#### Date / year parse (`_split_step_copy`)
From each `steps_or_data` string extract kicker + title:

1. Leading date/year forms: `Mon DD, YYYY`, `YYYY`, `H1 2026`, `Q2 2026`, `By end 2026`, `End 2026` then `:`/dash + rest.
2. Simple `Label: rest` when label ≤48 chars.
3. Trailing `before end YYYY` / `end YYYY` → kicker `End YYYY`, title = leading phrase (`Close`).
4. Trailing bare year/month-year → kicker that year, title = prefix.
5. Else empty kicker, full string as title.

#### Vertical rail (timeline / roadmap **with 4 steps**)
- True vertical `process-flow--vertical` (not dense-2x2 fake grid).
- Step numbers: **navy** circle + white digits on soft navy rail.
- Year kickers: **signal blue**, ~32px, tabular, **text-transform: none** (readable dates).
- Step titles ~26px weight 700.
- Insight strip under the rail.

#### Horizontal process (`full_process_flow`, or non-timeline multi-step)
- Even gutters; step-text ~26–28px; large index badges.
- If **last** step matches closed-loop synthesis keys (`closed-loop`, `payments + loyalty`,
  `circuit complete`, `completes the`) → pull it into full-width **`process-outcome`** bar
  under a **3-card** platform row (keep Resy/Tock/TheFork-class cards on one baseline).
- Outcome: blue badge + kicker (e.g. Closed-loop) + navy synthesis text; so_what with ~36px margin above insight.

#### Timeline year enrichment (undated close-path steps)
When layout is timeline/roadmap and steps lack parseable years **and** title/purpose
clearly describes a path-to-close / regulatory/labor sequence:

- Prefer enriching from evidence seed dates when available.
- Else apply **content-shaped** ordered edition labels that fit the story (e.g. sequential
  H2 / End-year for a same-window close path) — still honest that years may be
  operational framing. Never invent years that contradict cited evidence.
- Re-run `_split_step_copy` after enrichment.

Builder should prefer dated `steps_or_data` (`H2 2026: Labor consultation`) so the
Renderer does not guess.

---

### 5. Comparison grid (risk / multi-card)

**Copy contract (never house-phrase bodies):**
1. Prefer `Head: body` inside each `steps_or_data` string.
2. Else title-only steps **paired** with `content.bullets[i]` as body.
3. Else bullets alone.
4. **Never invent** placeholder body esp. “Keep this open through close.”

**Card chrome:** solid navy ~1.5px border, radius ~14px, white body + full navy hat,
head ~26px, body ~22px, grid gap ~22px, min-height ~200, **pack-from-top** (no equal-height flex stretch of short copy).

---

### 6. Quote card

| n quotes in `steps_or_data` | Face |
|---|---|
| 0–1 | Large single pull-quote + optional full-width `quote-insight` under it |
| 2–3 | **Vertical stack** `quote-layout--stack` full width; **all** quotes visible; **drop face so_what / side kicker** (insight → notes) |

Rules:
- Quote body = **first spoken line only** (`clean_quote_body`): pull first `“…”`/`"…"` span; strip `, said Name, Role` from body (cite owns attribution).
- Cite format `Name — Role` via: (1) structured attribution if it is a name, (2) parse `said Name, Role` from datapath, (3) source filename stem, (4) generic role — **never invent a person not in evidence**. If attribution is only `E####`, parse name from quote text.
- Stack gap generous (`~56px` between cards). Cite ~20px.
- Never leave quote_card content only at slide 1 (displace rule).

---

### 7. Cover bi-band (`title_or_opening`)

Top ~62% navy, bottom ~38% signal blue. White display title left-aligned in the
navy field; meta/date on blue band. **No logos / seals / hero-orbs.** No on-face bridge.

---

### 8. Charts / icon_grid

Unchanged contracts under Chart layouts / icon_grid sections: navy/blue series,
one label per value, real icon tiles, never split fallback.

---

## Layout HTML templates

### `title_or_opening` (slide 1 / cover)
```html
<section class="slide title-slide active" data-slide-number="1">
  <div class="slide-number">01 / NN</div>
  <div class="slide-inner cover-inner">
    <div class="title-stack">
      <div class="kicker"><!-- audience or deck kicker — NOT Why/What/How/Now --></div>
      <h1><!-- title --></h1>
      <p class="headline"><!-- chosen_dek / goal line --></p>
      <div class="title-footer"><span class="cover-date"><!-- optional meta --></span></div>
    </div>
  </div>
  <!-- speaker-notes aside only — no face narrative-bridge -->
</section>
```

### `split_text_visual`
Use dual-rail structure from Component Physics §1. Single `subtitle.dek` in
header via dek merge. Insight only if non-empty and not consumed as lead-band.
No face narrative-bridge.

### `metric_dashboard`
```html
<header class="slide-header">
  <h2 class="slide-title"><!-- title --></h2>
  <p class="subtitle dek"><!-- chosen_dek --></p>
</header>
<div class="slide-main layout-metric">
  <div class="kpi-grid dense-2x2" style="--col-count:2"><!-- when n==4; else set cols --></div>
  <div class="insight-strip so-what-callout"><span><!-- so_what --></span></div>
</div>
```

### `data_table`
Apply table-as-KPI branch when short 2-col; else:
```html
<div class="table-frame …">
  <table class="data-table">
    <thead><tr><th>…</th></tr></thead>
    <tbody>…</tbody>
  </table>
</div>
<div class="insight-strip">…</div>
```
Drop any Source/E#### column. th/td default `text-align:center`; th no `border-right`.

### `full_process_flow` / `timeline` / `roadmap`
Vertical rail HTML when timeline/roadmap + 4 steps; else horizontal cards + optional
`process-outcome`. Each step:
```html
<article class="step-card step-card--vertical">
  <div class="step-number">01</div>
  <div class="step-body">
    <div class="step-kicker"><!-- year/date if parsed --></div>
    <div class="step-text"><!-- title --></div>
  </div>
</article>
```

### `comparison_grid`
```html
<div class="comparison-grid layout-comparison">
  <article class="comparison-card risk">
    <div class="card-head"><!-- head --></div>
    <div class="card-body"><p><!-- body or empty --></p></div>
  </article>
</div>
```

### `quote_card`
Single: `quote-layout--single` + optional `quote-insight`.  
Multi (2–3): `quote-layout--stack` only — no side panel, no face so_what.

'''

SPEAKER_NOTES = r'''## Speaker Notes Block (every slide, hidden — presenter-deliverable prose)

Inside every `<section class="slide">`, append a hidden
`<aside class="speaker-notes" data-slide-number="N">` containing
**spoken claim language** — sentences a presenter would actually say aloud.
This is **not** a structured reference block and **not** general facilitation.

### Hard bans (spoken + face-adjacent)

- No `E####`, source-file names, section labels (`Why`/`What`…), badges.
- No sticky readiness watermarks / score chants
  (`Figures are directional under readiness N`, “readiness is 23 of 100”).
- No stage directions: `Hold for…`, `Make the room feel…`, `Link X to Y`,
  `Setup beat`, `Pressure:`, `Leave them with…`.
- No fixed leave-slide cadence: **do not** end optional bridges with
  `When we leave this slide…` / `Up next…` / `This sets up…` as the stock form.
- No face `story-bridge` / `narrative-bridge` rails. If residual CSS exists, it must be
  `display:none`. Bridge **intent** from `content.narrative_bridge` is woven into
  prose as a natural thesis turn (“The cash ticket only holds if labor clocks…”) —
  claims only, no meta.

### Length + shape

- **~40–100 words**, typically **3–5 sentences** (cover may be 2–3).
- Prefer Builder `speaker_notes` when it is already clean claim prose; scrub
  labels and readiness, then then expand with slide substance.
- Layout-aware substance: metrics get 1–2 spoken numbers; process names the
  path; quotes name the speakers parsed from quote text; splits argue the spine
  then one proof fact.

### Candor quota

Only when *this* slide is risk / thin-data / OCR / synthesized and over-claim would
mislead. Cover may frame low readiness **once** without saying the number unless
asked. Not 15 identical disclaimers.

### Sources to draw from (synthesize, do not list fields)

`audience_takeaway`, `purpose`, `content.*`, cleaned `speaker_notes`,
`narrative_bridge` (as claim turn), optional next-slide title only if it becomes a
real spoken sentence (not “Next lays out X”).

```html
<aside class="speaker-notes" data-slide-number="N">
  <h2 class="visually-hidden">Slide N speaker notes</h2>
  <p><!-- spoken prose --></p>
</aside>
```

### `evidence_manifest.json` (emit alongside the HTML)

A flat, machine-checkable slide→evidence map (replaces on-slide IDs as the
verification mechanism). This is the **sole** machine-checkable slide→evidence
map; the speaker-notes aside contains no `E####` — it is presenter prose only.
Include `"style_preset": "BoardroomEarnings"`.
```jsonc
{
  "source_handoff": "builder_handoff.json",
  "style_preset": "BoardroomEarnings",
  "presentation_title": "",
  "total_slides": 14,
  "readiness_score": 23,
  "quality_flags": [],
  "slides": [
    {
      "slide_number": 1,
      "title": "",
      "section": "Why",
      "layout_type": "title_or_opening",
      "evidence_ids": ["E0135", "E0155", "E0136"],
      "synthesized": false,
      "confidence": "high"
    }
  ]
}
```

### `slide_notes.md` (emit alongside the HTML)

A plain-text rendering of every slide's notes block (same content as the
`<aside>`s — presenter-deliverable prose), one `## Slide N — Title` heading
then the prose paragraphs. This is the human-readable export of the notes pane
and the future input to a PPTX builder step.

'''


def mainly(t: str) -> str:
    # Replace Layout Renderers through ### other (exclusive of Speaker Notes)
    start = t.find("## Layout Renderers (per `layout_type`)")
    end = t.find("## Speaker Notes Block (every slide, hidden — presenter-deliverable prose)")
    if start < 0 or end < 0:
        raise SystemExit(f"layout/speaker anchors miss {start} {end}")

    # Keep chart layouts + icon_grid + other from original file (after quote_card through Speaker Notes)
    # We need charts/icon_grid to remain. Locate Chart layouts inside old block.
    old = t[start:end]
    c_start = old.find("### Chart layouts")
    if c_start < 0:
        raise SystemExit("chart layouts miss inside layouts block")
    # also keep ### `icon_grid` and ### `other` that follow Charts
    charts_and_after = old[c_start:]  # Chart layouts … icon_grid … other …
    # Drop any face narrative-bridge mentions watered inside charts section? leave
    # Strip trailing --- before speaker if any
    charts_and_after = charts_and_after.rstrip() + "\n\n"

    t = t[:start] + LAYOUTS + charts_and_after + t[end:]

    # Replace Speaker Notes section through Density Mode
    s0 = t.find("## Speaker Notes Block (every slide, hidden — presenter-deliverable prose)")
    s1 = t.find("## Density Mode")
    if s0 < 0 or s1 < 0:
        raise SystemExit("speaker/density miss")
    t = t[:s0] + SPEAKER_NOTES + "\n" + t[s1:]

    # Density mode note about bridges
    if "narrative-bridge is notes-only" not in t:
        old_d = (
            "**Dense ≠ four identical chrome bands.** Density means *relevant facts +\n"
            "story layers that add stakes or mechanism*, varied by `packing_mode`. Stacking\n"
            "the same subtitle / context / so-what / bridge skeleton on every slide is a\n"
            "delivery failure even when the canvas looks \"full.\"\n"
        )
        new_d = (
            "**Dense ≠ four identical chrome bands.** Density means *relevant facts +\n"
            "story layers that add stakes or mechanism*, varied by `packing_mode`. Stacking\n"
            "the same subtitle / context / so-what skeleton on every slide is a delivery\n"
            "failure even when the canvas looks \"full.\" **`narrative_bridge` is notes-only**\n"
            "under Boardroom — do not paint face story-bridge rails.\n"
        )
        if old_d in t:
            t = t.replace(old_d, new_d, 1)

    # QC rows
    for old, new, lab in [
        (
            "| **Bridges are turn-forces, not next-title breadcrumbs** | Pass / Risk |  |\n",
            "| **Bridges are notes-only turn-forces** (no face story-bridge; no When-we-leave cadence) | Pass / Risk |  |\n"
            "| **Split dual-rail + dynamic hats** when argument-led with proof data (not loner SVG) | Pass / Risk |  |\n"
            "| **Comparison pairing** (Head:body or step+bullet; no invented house body) | Pass / Risk |  |\n"
            "| **Multi-quote stack** keeps all 2–3 voices; single may use insight | Pass / Risk |  |\n"
            "| **Metric n==4 is dense-2x2**; short 2-col tables map to KPI | Pass / Risk |  |\n"
            "| **Timeline 4-step vertical rail** with year parse / navy pointers / blue kickers | Pass / Risk |  |\n"
            "| **Closed-loop last horizontal step → process-outcome bar** | Pass / Risk |  |\n",
            "qc",
        ),
    ]:
        if old not in t:
            raise SystemExit("MISS " + lab)
        t = t.replace(old, new, 1)

    # Guardrails add physics rules if missing
    block = (
        "- **Boardroom component physics are mandatory** for every layout named in\n"
        "  Layout Renderers — dual-rail splits, table-as-KPI, metric 2×2, vertical\n"
        "  timeline years, comparison pairing, multi-quote stack, closed-loop outcome\n"
        "  bars, spoken note bridges off-face. Do not regress to loner-icon splits,\n"
        "  generic 1×4 KPI strips, placeholder risk bodies, or face story-bridge rails.\n"
    )
    if "Boardroom component physics are mandatory" not in t:
        anchor = "- **Honor chart / `icon_grid` layouts.**"
        if anchor not in t:
            raise SystemExit("MISS honor chart")
        t = t.replace(anchor, block + anchor, 1)

    # shell: hide narrative bridges
    if "story-bridge { display: none" not in t:
        t = t.replace(
            "  .source-strip { position: absolute; left: 90px; bottom: 28px;\n"
            "                  font-family: var(--font-body); font-size: 14px;\n"
            "                  opacity: .45; letter-spacing: .02em; }\n",
            "  .source-strip { position: absolute; left: 90px; bottom: 28px;\n"
            "                  font-family: var(--font-body); font-size: 14px;\n"
            "                  opacity: .45; letter-spacing: .02em; }\n"
            "  /* Boardroom: bridges live in speaker notes only */\n"
            "  .narrative-bridge, .story-bridge { display: none !important; }\n",
            1,
        )

    # Soften brand shell so-what-callout to insight strip preference already global;
    # Update packing density line that still says bridge count
    t = t.replace(
        "Never\n"
        "    force all four of subtitle / context-band / so-what / bridge.",
        "Never\n"
        "    force all of subtitle / context-band / so-what / face bridge.",
        1,
    )

    return t


def main() -> None:
    t0 = RENDERER.read_text(encoding="utf-8")
    t1 = mainly(t0)
    RENDERER.write_text(t1, encoding="utf-8")
    print("bytes", len(t0), "->", len(t1))

    checks = {
        "dual-rail": "Split dual-rail + proof" in t1,
        "fact primary": "Primary large value" in t1,
        "table-as-kpi": "Table-as-KPI" in t1,
        "dense-2x2": "n==4 dense-2x2" in t1 or "n==4 dense-2x2" in t1,
        "year parse": "_split_step_copy" in t1,
        "vertical rail": "process-flow--vertical" in t1,
        "outcome": "process-outcome" in t1,
        "comparison pair": "Never invent" in t1 and "Keep this open through close" in t1,
        "quote stack": "quote-layout--stack" in t1,
        "bridge off face": "On-face `narrative-bridge` / story-bridge" in t1,
        "spoken ban leave": "When we leave this slide" in t1,
        "dek merge": "chosen_dek" in t1,
        "qc dual": "Split dual-rail + dynamic hats" in t1,
        "physics guard": "Boardroom component physics are mandatory" in t1,
        "css hide bridge": ".narrative-bridge, .story-bridge { display: none !important; }" in t1,
        "no old face bridge template on cover": t1.count('class="narrative-bridge"')
        == t1.count("display: none"),  # print soft
        "charts kept": "### Chart layouts" in t1,
        "icon grid kept": "### `icon_grid`" in t1 or "### `icon_grid`" in t1,
    }
    # dense check
    checks["dense"] = "dense-2x2" in t1
    for k, v in checks.items():
        print(("PASS" if v else "FAIL"), k)
    if not all(checks.values()):
        raise SystemExit("validation failed")
    # residual undesirable mode
    if "## Phase 0" in t1:
        raise SystemExit("phase0 returned")
    print("ALL_PASS")


if __name__ == "__main__":
    main()
