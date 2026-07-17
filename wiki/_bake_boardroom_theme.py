# -*- coding: utf-8 -*-
"""Bake Boardroom Earnings as sole deck theme; remove Phase 0 / font presets."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
RENDERER = ROOT / "Impact Slide Renderer - Copilot and ChatGPT.md"

BOARDROOM_SECTION = r'''## Brand & Theme — Boardroom Earnings (sole deck theme)

**Boardroom Earnings is the only visual system for every deck this prompt
produces.** There is no font-preset picker, no Phase 0 style discovery, and no
Corporate / Editorial / Modern fallback. Do not invent alternate palettes,
dark keynote skins, forest/cream/orange themes, or AI soft-tile blue cards.

**IP boundary.** This is a **generic boardroom finance theme**. Do **not** use
American Express logos, Centurion art, trademarked product marks as chrome,
proprietary BentonSans files, or photographic brand assets. Type faces below are
IP-safe web substitutes.

### Fixed type stack (always)

```html
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
```

| Role | Face | Weight |
|---|---|---|
| Display / titles | **Source Sans 3** | 700 |
| Body / bullets | **Source Sans 3** | 400 / 600 |
| Tabular figures / KPI values | **IBM Plex Sans** (`font-variant-numeric: tabular-nums`) | 600–700 |

**Banned forever as primary fonts:** Inter, Roboto, Arial, `system-ui`, Times,
Sora, DM Sans, Fraunces, Hanken Grotesk, Space Grotesk, Bricolage (Mat residuals).

### Fixed `:root` tokens (inline in every deck)

```css
:root {
  /* Type */
  --font-display: "Source Sans 3", sans-serif;
  --font-body: "Source Sans 3", sans-serif;
  --font-num: "IBM Plex Sans", "Source Sans 3", sans-serif;

  /* Surfaces */
  --stage-bg: #0b0f1a;
  --slide-bg: #ffffff;
  --bg-soft: #f8f8f8;
  --panel: #eff0f0;
  --panel-border: #d8dce3;

  /* Structure + signal (one accent blue only) */
  --navy: #00175a;
  --navy-deep: #001058;
  --blue: #006fcf;
  --blue-sky: #80c9ff;
  --ink: #53565a;
  --ink-muted: #63666a;
  --ink-faint: #929292;
  --ink-on-navy: #ffffff;
  --grid: #e0e4ea;
  --rule: #00175a;
  --negative: #53565a; /* parentheses / navy-ink; no red required */

  /* Aliases used by density / legacy selectors */
  --accent: var(--blue);
  --accent-2: var(--navy);
  --accent-warn: var(--navy);
  --callout-bg: rgba(0, 23, 90, 0.05);
  --ink-soft: var(--ink-muted);

  /* Type scale @ 1920×1080 */
  --fs-display: 72px;
  --fs-title: 56px;
  --fs-insight: 26px;
  --fs-sub: 22px;
  --fs-lead: 22px;
  --fs-body: 22px;
  --fs-kpi: 70px;
  --fs-kpi-label: 24px;
  --fs-meta: 14px;
  --fs-foot: 14px;

  /* Spacing (pack-from-top; denser than generous IR pads) */
  --pad-x: 96px;
  --pad-top: 56px;
  --pad-bottom: 48px;
  --gap-lg: 32px;
  --gap-md: 18px;
  --gap-sm: 12px;
  --gap-section: 32px;
  --gap-content: 24px;
  --gap-row: 16px;
  --gap-tight: 8px;
  --card-radius: 16px;
  --header-radius: 14px 14px 0 0;
}
```

### Non-negotiable design rules

1. **One signal color (blue `#006FCF`).** Navy `#00175A` is structure (titles,
   hats, rails, borders). Gray is context — never a second decorative accent
   (no orange, forest green, cream cards, multi-hue bento).
2. **Light paper content slides** (`#FFFFFF` / soft `#F8F8F8`). Dark stage only
   frames the viewport — not each content slide.
3. **Pack content from the top.** Do not flex-stretch short bullet/proof lists
   or 2–3 cards to fill vertical space for its own sake. Leave free band
   below the content block. Stretch only multi-item grids when the layout
   needs it (e.g. n==4 KPI dense-2x2).
4. **Titles left-aligned** on content slides (not auto-centered stacks). Cover
  bi-band is its own stack (see Title layout).
5. **So-what is a muted navy insight line / strip** under the hero — not a
   cream/orange accent card, not a bookmark warehouse of four chrome bands.
6. **KPI numbers prefer signal blue large tabular type**; labels navy weight 700
   at ~0.34× the value size.
7. **Navy-hat tables and risk cards** (white body, navy head bar). Soft gray
   panels for comparison tiles where cards are needed.
8. **Zero on-slide `E####`, zero readiness score watermarks**, zero AmEx marks.
9. **`pptx_profile.json` is optional and may only tint accents ≤±8% saturation
   toward family navy/blue** — it may **never** replace this theme, swap fonts,
   or introduce a second festival palette. If absent, render pure Boardroom.
10. Charts/icon_grid always use the Boardroom chart paint rules elsewhere in
    this prompt (series navy/blue, inline SVG/CSS, one label per value).

### Boardroom shell CSS (append after `:root` + viewport-base)

Inline at least these families so every deck shares the same chrome (layout
renderers add component templates below):

```css
body { font-family: var(--font-body); color: var(--ink); }
.slide {
  background: var(--slide-bg);
  color: var(--ink);
  font-family: var(--font-body);
  padding: var(--pad-top) var(--pad-x) var(--pad-bottom);
  box-sizing: border-box;
}
.slide-title, h1, h2 {
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--navy);
  letter-spacing: -0.02em;
  margin: 0;
  text-align: left;
}
.slide-title { font-size: var(--fs-title); line-height: 1.12; }
.subtitle, .dek {
  font-size: var(--fs-sub);
  color: var(--ink-muted);
  margin: 8px 0 0;
  text-align: left;
  max-width: 1500px;
}
.insight-strip, .so-what-callout {
  margin-top: var(--gap-content);
  padding: 0;
  border: 0;
  background: transparent;
  border-left: 0;
  color: var(--navy);
  font-size: var(--fs-insight);
  font-weight: 600;
  line-height: 1.35;
  max-width: 1500px;
}
.kpi-value {
  font-family: var(--font-num);
  font-size: var(--fs-kpi);
  font-weight: 700;
  color: var(--blue);
  font-variant-numeric: tabular-nums;
  line-height: 1.0;
}
.kpi-label {
  font-size: var(--fs-kpi-label);
  font-weight: 700;
  color: var(--navy);
  line-height: 1.25;
  max-width: 22ch;
}
.layout-metric.dense-2x2 .kpi-grid,
.kpi-grid.dense-2x2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--gap-md);
  align-content: start;
}
.card-head, .panel-kicker, thead th, .table-hat {
  background: var(--navy);
  color: var(--ink-on-navy);
  font-weight: 700;
}
.title-slide, .cover-inner {
  /* bi-band cover: top navy ~62%, bottom signal blue ~38% */
  background: linear-gradient(
    to bottom,
    var(--navy) 0%, var(--navy) 62%,
    var(--blue) 62%, var(--blue) 100%
  );
  color: var(--ink-on-navy);
  padding: 0;
}
.title-slide .slide-title,
.title-slide h1 { color: #fff; font-size: var(--fs-display); text-align: left; }
.slide-number {
  position: absolute; right: var(--pad-x); bottom: 28px;
  font-size: var(--fs-foot); color: var(--ink-faint);
  font-variant-numeric: tabular-nums;
}
```

Prefer layout-specific HTML/CSS from "Layout Renderers" (including chart pack)
for the rest. When density fields conflict with Boardroom chrome, **Boardroom
wins**: muted insight line > decorative callout card; pack-top > flex-stretch.

'''


def must_replace(hay: str, old: str, new: str, label: str) -> str:
    if old not in hay:
        raise SystemExit(f"MISS {label}: {old[:110]!r}")
    return hay.replace(old, new, 1)


def main() -> None:
    t = RENDERER.read_text(encoding="utf-8")

    # --- Performance rule 4 ---
    t = must_replace(
        t,
        "4. **Distinctive typography.** Never use Inter, Roboto, Arial, or `system-ui`\n"
        "   as the primary font. Pick from the curated font-pair presets. CSS variables\n"
        "   `--font-display` and `--font-body` drive every text element.\n",
        "4. **Boardroom typography only.** Always **Source Sans 3** + **IBM Plex Sans**\n"
        "   (tabular). Never Inter, Roboto, Arial, `system-ui`, Sora, Space Grotesk,\n"
        "   Fraunces, or any second preset. CSS variables `--font-display`,\n"
        "   `--font-body`, `--font-num` from Brand & Theme drive every text element.\n",
        "perf4",
    )

    # --- Source priority item 5 ---
    t = must_replace(
        t,
        "5. **`pptx_profile.json`** — brand cues, **read-only**. v4 may not produce it\n"
        "   (no `.pptx` among Step 1 inputs). If absent, use a neutral theme from the\n"
        "   font-pair presets. Brand colors/fonts may inform the accent palette but are\n"
        "   never required.\n",
        "5. **`pptx_profile.json`** — brand cues, **read-only** and **optional**. v4 may\n"
        "   not produce it. The deck skin is always **Boardroom Earnings**. Profile may\n"
        "   only gently tint navy/blue accents — never replace fonts, invert to dark\n"
        "   keynote, or introduce a second accent festival.\n",
        "src5",
    )

    # --- Shell: font link + root comment ---
    t = must_replace(
        t,
        "<!-- font-pair preset <link> goes here -->\n"
        "<style>\n"
        "  :root { /* font + color tokens (see Font-Pair Presets) */ }\n"
        "  /* viewport-base.css (above) */\n",
        "<!-- Boardroom fonts (Source Sans 3 + IBM Plex Sans) — sole theme -->\n"
        '<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">\n'
        "<style>\n"
        "  :root { /* Boardroom Earnings tokens — see Brand & Theme */ }\n"
        "  /* viewport-base.css (above) */\n"
        "  /* Boardroom shell CSS from Brand & Theme */\n",
        "shell",
    )

    # --- Replace entire Font-Pair Presets section ---
    start = t.find("## Font-Pair Presets (pick one; never generic fonts)")
    end = t.find("## Icon Library (inline SVG sprite")
    if start < 0 or end < 0:
        raise SystemExit("MISS font-presets / icon-library anchors")
    t = t[:start] + BOARDROOM_SECTION + "\n" + t[end:]

    # --- Mode A flow ---
    t = must_replace(
        t,
        "Do, in order, stopping after the user picks a style preview:\n"
        "1. **Phase 1 — Handoff Verification** (confirm the build plan is present + approved)\n"
        "2. **Phase 0 — Style Discovery** (generate 3 distinct single-slide HTML previews)\n"
        "3. **Stop.** Wait for the user to pick a preview (or name a preset).\n"
        "\n"
        "Then, after the pick:\n"
        "4. **Phase 2 — Full Deck Generation** (emit the complete `presentation.html` + `slide_notes.md` + `evidence_manifest.json`)\n"
        "5. **Phase 3 — Quality Checklist** (grounding, notes, no-on-slide-IDs, readiness carried)\n"
        "6. **Stop.** Wait for revisions.\n",
        "Do, in order (no style picker — Boardroom is mandatory):\n"
        "1. **Phase 1 — Handoff Verification** (confirm the build plan is present + approved)\n"
        "2. **Phase 2 — Full Deck Generation** (emit complete Boardroom `presentation.html` + `slide_notes.md` + `evidence_manifest.json`)\n"
        "3. **Phase 3 — Quality Checklist** (grounding, notes, Boardroom theme, no-on-slide-IDs, readiness carried)\n"
        "4. **Stop.** Wait for revisions.\n",
        "modeA",
    )

    t = must_replace(
        t,
        'slide 3", "switch slide 6 to a bar chart", "change the font preset").\n',
        'slide 3", "switch slide 6 to a bar chart", "tighten the insight line").\n',
        "modeB",
    )

    t = must_replace(
        t,
        "- If complete, continue to Phase 0.\n"
        "\n"
        "> The absence of `pptx_profile.json` is **not** an error — it means no `.pptx`\n"
        "> was among Step 1 inputs. Use a neutral font-pair preset theme.\n",
        "- If complete, continue immediately to **Phase 2** (Boardroom full deck).\n"
        "\n"
        "> The absence of `pptx_profile.json` is **not** an error — it means no `.pptx`\n"
        "> was among Step 1 inputs. Render pure **Boardroom Earnings** either way.\n",
        "phase1end",
    )

    # --- Delete Phase 0 section entirely ---
    p0 = t.find("## Phase 0 — Style Discovery (3 previews)")
    p2 = t.find("## Phase 2 — Full Deck Generation")
    if p0 < 0 or p2 < 0:
        raise SystemExit("MISS phase0/phase2")
    t = t[:p0] + t[p2:]

    # --- Phase 2 full deck requirements ---
    t = must_replace(
        t,
        "- `viewport-base.css` inlined verbatim.\n"
        "- The chosen font-pair preset `<link>` + `:root` tokens inlined.\n",
        "- `viewport-base.css` inlined verbatim.\n"
        "- **Boardroom Earnings only:** Source Sans 3 + IBM Plex Sans `<link>`,\n"
        "  `:root` tokens, and Boardroom shell CSS from Brand & Theme — never a\n"
        "  second preset, never a Phase-0 skin pick.\n"
        "- `DECK_META.style_preset = \"BoardroomEarnings\"` (string literal).\n",
        "phase2a",
    )

    t = must_replace(
        t,
        "> Deck rendered. The HTML is the visual source of truth; `slide_notes.md` and\n"
        "> `evidence_manifest.json` are the grounding/notes sidecars. Ask me to revise\n"
        "> any slide, switch the font preset, or adjust density.\n",
        "> Deck rendered in **Boardroom Earnings**. The HTML is the visual source of\n"
        "> truth; `slide_notes.md` and `evidence_manifest.json` are the grounding/notes\n"
        "> sidecars. Ask me to revise any slide, switch a layout, or adjust density —\n"
        "> not the theme (Boardroom is fixed).\n",
        "qc_end",
    )

    t = must_replace(
        t,
        "| Distinctive fonts (no Inter/Roboto/Arial/system) | Pass / Risk |  |\n",
        "| **Boardroom theme only** (Source Sans 3 + IBM Plex; navy `#00175A` + blue `#006FCF`; no second preset / Phase 0 artifacts) | Pass / Risk | Hard-fail if Corporate/Editorial/Modern or other skins |\n"
        "| Pack-from-top (no flex-stretch short lists for whitespace) | Pass / Risk |  |\n",
        "qc_boardroom",
    )

    t = must_replace(
        t,
        "- **Do not use generic fonts** (Inter, Roboto, Arial, `system-ui`) as primary.\n",
        "- **Do not use generic or second-theme fonts** (Inter, Roboto, Arial,\n"
        "  `system-ui`, Sora, Space Grotesk, Fraunces, DM Sans, Bricolage) as primary.\n"
        "  Boardroom is Source Sans 3 + IBM Plex Sans only.\n"
        "- **Do not reintroduce Phase 0 / 3-preview / font-preset choice.** There is\n"
        "  no style discovery step. Never emit Corporate / Editorial / Modern shells.\n"
        "- **Do not replace Boardroom** with Mat dark forest, long-table terracotta,\n"
        "  soft AI bento tiles, multi-accent rainbows, or dark-keynote default text\n"
        "  slides. Cover bi-band is the only staged dark+blue field.\n",
        "guard_fonts",
    )

    t = must_replace(
        t,
        "- **Do not embed brand colors/fonts as a hard requirement** — v4 produces no\n"
        "  `brand_style_summary.json`. Use the font-pair preset theme; if\n"
        "  `pptx_profile.json` is present you may inform the accent palette from it, but\n"
        "  never block the render on brand.\n",
        "- **Boardroom is the embed requirement; corporate brand files are not.** v4\n"
        "  produces no `brand_style_summary.json`. Always emit Boardroom tokens. If\n"
        "  `pptx_profile.json` is present you may gently tint navy/blue only — never\n"
        "  block the render, never swap the theme, never invent a second accent.\n",
        "guard_brand",
    )

    # track DECK_META style_preset in shell JS comment if present
    if 'style_preset: "BoardroomEarnings"' not in t:
        t = must_replace(
            t,
            "      var DECK_META = {\n"
            "        readiness_score: 0,              // presentation.readiness_score\n"
            "        readiness_components: {},         // presentation.readiness_components\n"
            "        quality_flags: []                 // presentation.quality_flags\n"
            "      };\n",
            "      var DECK_META = {\n"
            '        style_preset: "BoardroomEarnings",\n'
            "        readiness_score: 0,              // presentation.readiness_score\n"
            "        readiness_components: {},         // presentation.readiness_components\n"
            "        quality_flags: []                 // presentation.quality_flags\n"
            "      };\n",
            "deck_meta",
        )

    # residual ban lists
    residual_fail = []
    for needle in (
        "## Font-Pair Presets",
        "## Phase 0 — Style Discovery",
        "Preset 1 — Corporate",
        "Preset 2 — Editorial",
        "Preset 3 — Modern",
        "pick a style preview",
        "font-pair presets",
        "Which direction feels right",
    ):
        if needle in t:
            residual_fail.append(needle)

    must_have = [
        "## Brand & Theme — Boardroom Earnings",
        "Boardroom Earnings is the only visual system",
        'style_preset: "BoardroomEarnings"',
        "Source Sans 3",
        "IBM Plex Sans",
        "#00175a",
        "#006fcf",
        "continue immediately to **Phase 2**",
        "Do not reintroduce Phase 0",
        "Boardroom theme only",
    ]
    for m in must_have:
        if m not in t:
            residual_fail.append("MISSING:" + m)

    RENDERER.write_text(t, encoding="utf-8")
    print("wrote", RENDERER, "bytes", len(t.encode("utf-8")))
    if residual_fail:
        raise SystemExit("residual: " + repr(residual_fail))
    print("PASS")


if __name__ == "__main__":
    main()
