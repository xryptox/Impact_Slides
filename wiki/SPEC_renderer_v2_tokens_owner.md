# SPEC: Renderer v2 — Design Token Owner (normative)

**Status:** Normative owner doc (D4/D5)  
**Date:** 2026-07-19  
**Engineering PRD:** `wiki/SPEC_renderer_v2_p2_open_props_tokens.md`  
**Scope:** `wiki/SCOPE_renderer_v2_mvp1.md`

This document is the **single implementation authority** for renderer_v2 design
tokens. Historical research (`wiki/RESEARCH_renderer_v2_*.md` and any dual-track
open-props notes) is **non-normative** relative to this file.

---

## 1. Layer model

```
@font-face (P0 inliner — vendored Boardroom fonts)
→ primitives + Boardroom brand     (css/tokens.css)
→ semantic map                     (css/semantic-tokens.css)
→ viewport / gridlines / components / chart_css
→ optional theme override          (render_deck theme= → :root block)
```

| Layer | Owner file | Purpose |
|-------|------------|---------|
| **Primitives** | `tokens.css` (Open Props–*inspired* scales) | `--size-*`, `--radius-*`, `--shadow-*` scales |
| **Brand / Boardroom** | `tokens.css` | Navy/blue/ink, fonts, pads, type sizes, stage |
| **Semantic** | `semantic-tokens.css` | Themeable aliases (`--color-*`, `--space-*`, …) |
| **Components** | `components.css`, `gridlines.css`, chart CSS | Consume **semantic first**, primitives second |

Tokens are **always on** (D3). They are **not** a P1 feature id.

---

## 2. Curation rules (D5)

1. **No full upstream Open Props bundle** — scales are Boardroom-owned, OP-inspired.
2. **No utility-class framework** and no second grid system (Boardroom + `gl-*` wins).
3. **No animation/easing packs** beyond calm UI needs (D15).
4. New primitives require a one-line rationale here when added.
5. Prefer existing tokens over new hard-coded px/hex in components when values match.

---

## 3. Primitive scales (curated)

| Family | Names | Notes |
|--------|-------|-------|
| Size | `--size-1` … `--size-15` | 4px rhythm (4 → 96) |
| Radius | `--radius-1` … `--radius-6`, `--radius-round` | |
| Shadow | `--shadow-1` … `--shadow-6` + `--shadow-color` / `--shadow-strength` | Boardroom-tinted |

Brand tokens (non-exhaustive): `--navy`, `--blue`, `--ink*`, `--font-*`, `--fs-*`,
`--pad-*`, `--gap-*`, `--card-radius`, gradients.

---

## 4. Semantic surface (public theme keys)

Preferred keys for `render_deck(..., theme={...})` and brand injection:

**Color:** `--color-primary`, `--color-primary-deep`, `--color-primary-mid`,
`--color-accent`, `--color-accent-light`, `--color-accent-2`, `--color-warn`,
`--color-ink`, `--color-ink-muted`, `--color-ink-faint`, `--color-ink-on-primary`,
`--color-surface`, `--color-surface-soft`, `--color-panel`, `--color-panel-border`,
`--color-border`, `--color-grid`, `--color-rule`, `--color-negative`

**Space:** `--space-xs`, `--space-sm`, `--space-md`, `--space-lg`, `--space-xl`,
`--space-2xl`, `--space-3xl`

**Radius:** `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-card`

**Shadow:** `--shadow-sm`, `--shadow-md`, `--shadow-lg`

**Type:** `--text-xs` … `--text-display`, `--text-title`; `--font-display`,
`--font-body`, `--font-num`

**Theme API behavior:** unknown custom-property keys **pass through** into the
override `:root` block (permissive); only the keys above are **supported**.

---

## 5. How to add a token

1. Decide layer: primitive scale vs brand vs semantic alias.
2. Add to the correct CSS file with a fallback where semantic maps to brand.
3. Prefer the new name in components only when replacing an equal value.
4. Note non-obvious additions in this doc.
5. Extend token contract tests if the name is part of the public surface.

---

## 6. Non-goals

- Vendoring npm `open-props` (would need a new decision + THIRD_PARTY row).
- Feature-gating token CSS.
- Tailwind / utility classes.
- Dark-mode productization in this owner doc.

*End of token owner doc.*
