# SPEC: Renderer v2 — P1 Feature×Size Gating

**Status:** Engineering PRD — ready to ticket  
**Date:** 2026-07-19  
**Theme:** P1 (MVP1)  
**Scope lock:** `wiki/SCOPE_renderer_v2_mvp1.md`  
**Depends on:** P0 complete (`wiki/SPEC_renderer_v2_p0_self_contained.md`, issues #41–#45 closed)  
**Alignment:** D2 (soft size warn), D3 (JS feature-gated), missing-feature policy C (auto-enable + soft warn; fail closed only on unknown/unsupported constructs), D14  
**Success criteria:** SC-SIZE-1, SC-CLI-1 (feature subsetting), SC-IX-2 (static readable when JS libs off), SC-COMPAT-1  
**Confirmed seams (user lock):** primary = `render_deck` → HTML + `run_meta.json`; supporting = `build_head_assets(..., feature_ids=)`; thin pure = feature detection over normalized handoff. **Gate-only — no Chart.js (or other JS lib) pin in P1.**

---

## Problem Statement

After P0, every deck is offline-safe for Boardroom chrome and fonts — but the generator still has no product contract for *which optional capabilities* a deck needs. When Chart.js, Mermaid, Alpine, Swiper, or icon packs land, naively inlining all of them on every handoff will blow single-file HTML size, make corporate share/email painful, and hide whether a deck actually uses a capability.

Operators and agents also cannot see payload impact today: there is no size report, no soft warn, and no auto-enable path from handoff content. Reserved feature ids already exist on the inliner seam but are inert.

## Solution

Introduce a **feature detection + gating layer** on the existing self-contained foundation:

1. Inspect the normalized handoff and **auto-enable** known feature ids the content needs.
2. Pass those ids into the existing inliner so only enabled features contribute optional assets (none new in P1 beyond the gate machinery — reserved for P3/MVP1.1 payloads).
3. **Report** enabled features and approximate payload bytes on `run_meta.json` / `DECK_META`.
4. **Soft-warn** on stderr when payload exceeds a documented advisory threshold; never hard-fail on size in P1.
5. Fail closed only on **unknown** feature ids forced by the caller (not on “handoff might want charts later”).
6. Keep default generation compatible: handoffs that need no optional features behave as today (fonts + Boardroom CSS only).

No Chart.js (or other third-party JS) is vendored or inlined in this theme. P1 builds the gate, detection rules, size matrix, and reporting so P3 can drop Chart.js behind `charts` without another gating rewrite.

## User Stories

1. As a deck operator, I want optional libraries omitted from decks that do not need them, so that shared HTML stays as small as practical.
2. As a deck operator, I want features auto-enabled from the handoff, so that I do not hand-maintain a feature checklist per deck.
3. As a deck operator, I want a soft size warning when a deck grows large, so that I notice bloat before hard limits exist.
4. As a deck operator, I want size and feature metadata in `run_meta.json`, so that I can audit payloads in CI and support tickets.
5. As a deck operator, I want the same metadata in `DECK_META` inside the HTML, so that offline inspection of a shipped file still reveals what was enabled.
6. As a deck operator, I want CLI overrides to force or suppress features, so that I can reproduce edge cases and debug false auto-detects.
7. As a deck operator, I want unknown forced feature ids rejected clearly, so that typos do not silently no-op.
8. As a deck operator, I want reserved feature ids (`charts`, `mermaid`, `alpine`, `swiper`, `icons`) accepted by the gate even when their payload is not yet shipped, so that tooling can target the vocabulary early.
9. As a deck operator, I want enabling `charts` in P1 to change metadata without requiring Chart.js bytes, so that gate tests do not depend on P3 assets.
10. As a presentation author (Builder handoff producer), I want chart layouts to mark the `charts` feature without changing my handoff schema, so that existing chart slides keep working.
11. As a presentation author, I want non-chart handoffs to leave `charts` off by default, so that simple narrative decks stay lean.
12. As a presentation author, I want future Mermaid/Alpine/Swiper/icon needs expressed through the same feature vocabulary, so that I learn one model.
13. As a corporate recipient, I want decks that did not need optional JS to open without those scripts present, so that offline and locked-down browsers stay safe.
14. As a corporate recipient, I want static content still readable when optional features are off, so that progressive enhancement holds (SC-IX-2).
15. As a CI maintainer, I want fixture tests that assert “no charts feature ⇒ no charts asset id inlined,” so that regressions are caught automatically.
16. As a CI maintainer, I want a documented size matrix (baseline vs theoretical +feature rows), so that later pins have a place to record real KB.
17. As a CI maintainer, I want soft size warns to be detectable in stderr without failing the process exit code (unless unrelated strict validation fails), so that warn-only policy is enforceable.
18. As a renderer developer, I want one detection function over the normalized handoff, so that auto-enable logic is unit-testable without full paint.
19. As a renderer developer, I want `build_head_assets` to remain the only place optional third-party assets are chosen, so that SC-MOD-1 holds.
20. As a renderer developer, I want `render_deck` to orchestrate detect → inline → validate → report, so that callers need not wire the pipeline themselves.
21. As a renderer developer, I want feature detection to reuse `is_chart_layout` (and layout_type inspection), so that chart detection does not fork taxonomy.
22. As a renderer developer, I want MVP1.1 features (`mermaid`, `alpine`, …) to have explicit “not implemented payload” behavior, so that enabling them cannot pretend assets exist.
23. As a renderer developer, I want a single advisory byte threshold constant, so that soft-warn policy is not scattered magic numbers.
24. As a support engineer, I want `features_enabled` and `payload_bytes` (or equivalent) on every run, so that “why is this HTML huge?” is answerable from artifacts alone.
25. As a support engineer, I want delivery mode and features recorded together, so that CDN-dev vs self-contained diagnosis stays coherent.
26. As a product owner, I want hard size limits deferred until real bundles are measured, so that we do not invent fail thresholds from guesses (D2).
27. As a product owner, I want auto-enable as the default policy, so that missing-feature silent omission is minimized (policy C).
28. As a product owner, I want fail-closed behavior reserved for unknown/unsupported constructs, so that genuine mistakes stop the pipeline.
29. As an agent implementer, I want this PRD’s seams named and stable, so that `/implement` + `/tdd` can lock tests before code.
30. As an agent implementer, I want P1 explicitly out-of-scope for Chart.js vendoring, so that scope creep into P3 is rejected in review.
31. As a docs reader, I want README / operator notes to mention feature auto-enable and size warn, so that humans discover the contract.
32. As a dual-mode user, I want feature gating to apply in both self-contained and CDN modes, so that dev CDN runs still reflect which features are on.
33. As a dual-mode user, I want CDN mode to still record the same feature metadata shape, so that tools do not special-case mode for feature lists.
34. As a layout author, I want detection to consider freeform / nested visual types that are chart layouts, so that dual-chart and pack charts still auto-enable `charts`.
35. As a security reviewer, I want unknown feature ids never to trigger network fetches or eval, so that the gate cannot become an open loader.
36. As a release manager, I want THIRD_PARTY.md size-matrix cross-links updated when P1 lands, so that inventory and payload reporting stay aligned.
37. As a future P3 owner, I want enabling `charts` already to flow `feature_ids` into the inliner, so that adding a vendored Chart.js file is a payload plug-in, not a redesign.
38. As a future MVP1.1 owner, I want detection stubs or extension points for mermaid/alpine content markers documented, even if they always return off until those themes ship.
39. As a strict-mode user, I want size soft-warn not to equal validation failure, so that `--no-strict` is not required just to accept a large-but-valid deck.
40. As a golden-fixture maintainer, I want existing mini handoff tests to keep passing with `features_enabled` possibly empty or charts-on only when charts exist in the fixture, so that SC-COMPAT-1 holds.

## Implementation Decisions

1. **Primary public seam:** `render_deck` remains the acceptance surface. Observable outputs: `presentation.html`, `run_meta.json`, stderr warnings, exit semantics of CLI `main`.
2. **Supporting inliner seam:** extend existing `build_head_assets(mode, feature_ids=…)` so known feature ids influence the returned bundle metadata (`assets` list, `bytes_inlined`, and a features field). No second inliner API.
3. **Thin pure seam:** add a pure detection function over the normalized handoff (name left to implementer; concept: handoff → frozenset of known feature ids). Must be callable without writing files.
4. **Orchestration order inside `render_deck`:** normalize/validate handoff → detect features (union any CLI/API force list, minus suppress list) → `build_head_assets(delivery, feature_ids=…)` → render slides → wrap → validate HTML for delivery → write artifacts including feature/size report.
5. **Reserved feature vocabulary (normative ids):** `charts`, `mermaid`, `alpine`, `swiper`, `icons`. Same set as P0 `KNOWN_FEATURES`. Do not rename.
6. **P1 payload policy (gate-only):**  
   - No new vendored JS/CSS library files required.  
   - Enabling a feature **must** appear in `features_enabled` / bundle meta.  
   - Enabling a feature **must not** require network.  
   - Enabling a feature **may** add a stable asset id placeholder in `assets_inlined` only if it does not imply a remote URL and does not break SC-OFFLINE-2; prefer **metadata-only** enablement until P3/MVP1.1 supplies real bytes.  
   - `bytes_inlined` continues to reflect real inlined bytes (fonts today); optional features with zero payload do not inflate bytes.
7. **Detection rules (MVP1):**  
   - `charts` — on if any slide (including nested freeform/pack visual types where applicable) has a layout_type that `is_chart_layout` accepts, or an equivalent chart content marker already used by dispatch.  
   - `mermaid`, `alpine`, `swiper`, `icons` — off by default in P1; detection may exist as stubs returning empty until those themes define markers. Do not invent handoff schema fields solely for stubs.
8. **Caller overrides (API + CLI):**  
   - Force-enable list and force-disable list (disable wins on conflict for a given id, unless implementer documents the inverse — pick one and test it; recommendation: **suppress beats force beats detect**).  
   - CLI flags should be discoverable in `--help` and mutually coherent with delivery flags. Exact flag spelling is implementer choice but must be documented in README.
9. **Unknown ids:**  
   - Unknown ids in force lists → fail closed (ValueError / CLI nonzero), message names the id.  
   - This tightens P0’s “warn and ignore” only for **explicit caller force** paths; detection never emits unknown ids.  
   - Inliner may keep warn-on-unknown for defense in depth if called directly with garbage, but `render_deck` should not pass unknowns through.
10. **Size reporting:**  
    - Record at least: total output HTML byte size (UTF-8), `bytes_inlined` from the bundle, `features_enabled` sorted list, `delivery`.  
    - Soft-warn if HTML byte size ≥ advisory threshold. Initial threshold: **2_000_000 bytes (≈2 MiB)** unless measurement of current golden/mini decks justifies a different documented constant — constant must live in one module and appear in the size matrix doc section.  
    - Warn text must include actual size and threshold. Exit code unchanged by warn alone.
11. **Hard size fail:** out of P1 (D2).
12. **run_meta.json / DECK_META:** additive fields only; do not remove P0 `delivery` / `assets_inlined`.
13. **Validation:** keep P0 remote-fetch guard. Feature gating must not reintroduce CDN links in self-contained mode.
14. **Charts rendering path:** unchanged in P1 — existing SVG/`charts.py` output remains. Feature flag does not switch renderers yet (that is P3).
15. **Docs:** README Step 4 + package docstring mention auto-enable, overrides, soft size warn, and point at this spec. Update `assets/THIRD_PARTY.md` process note to reference the size matrix / P1 reporting.
16. **Size matrix (documentation artifact):** table in this spec’s Further Notes (and/or THIRD_PARTY) with rows: baseline self-contained mini deck; +fonts (already in baseline); +charts (P3 TBD); +mermaid (1.1 TBD); etc. P1 fills real numbers for baseline only; other rows marked TBD.
17. **No new always-on JS.** Token/CSS remains always on (D3); optional features are the only gates.
18. **Theme / Open Props:** out of P1 (owned by P2).
19. **Labels for tickets:** `ready-for-agent`, `renderer-v2`, and a `P1` label (create if missing), consistent with P0 filing.
20. **Ticket slicing suggestion (not mandatory):** (1) detect_features + unit tests; (2) plumb features through render_deck/run_meta/DECK_META + CLI overrides; (3) size report + soft-warn; (4) docs + size matrix baseline measurement.

## Testing Decisions

**What good tests look like**

- Assert **external behavior** at `render_deck` / CLI / pure detect boundaries: files written, JSON fields, stderr, presence/absence of remote URLs, feature lists.
- Do **not** assert private helper names, dict key order beyond documented canonicalization, or exact warn wording punctuation beyond stable substrings (size, threshold, feature id).
- Prefer one high seam (`render_deck`) for integration; use pure detect tests for combinatorial handoff shapes without full paint cost.

**Modules / behaviors under test**

- Feature detection over handoff shapes (chart layout on/off; freeform nested chart if supported; empty slides).
- `render_deck` default auto-enable for mini fixture with charts vs without.
- Force/suppress overrides and precedence.
- Unknown force id → failure.
- `run_meta.json` / `DECK_META` contain `features_enabled` and size fields.
- Soft-warn fires when threshold lowered via test seam (inject/monkeypatch threshold) or by constructing oversized HTML only if practical — prefer threshold injection over multi‑MB fixtures.
- Self-contained output still has zero remote fetch URLs (regression).
- Enabling reserved features without payloads does not add `https://` assets.
- CLI help/override smoke via `main([...])` like P0 self-contained tests.

**Prior art**

- `tests/test_renderer_v2_self_contained.py` — delivery, inliner, remote URL, run_meta/DECK_META patterns.
- `tests/test_renderer_v2_gates.py` / gridlines — mini handoff with chart layouts.
- `tests/test_renderer_v2_themes.py` — `render_deck` HTML inspection.

**Suggested home:** extend `tests/test_renderer_v2_self_contained.py` **or** add `tests/test_renderer_v2_features.py` if the file would become unwieldy; either is fine if package conventions stay consistent (module-level imports).

## Out of Scope

- Vendoring or inlining Chart.js, Mermaid, Alpine, Swiper, or Lucide (P3 / MVP1.1 / P6).
- Switching `charts.py` from SVG to Canvas/Chart.js (P3).
- Hard size failures or CI quotas beyond soft-warn.
- Open Props / semantic token ownership work (P2).
- Native disclosure patterns (P5).
- Productized composition recipes (P7 / MVP1.1).
- PDF/export seams (parallel track).
- Animation / motion packs (D15).
- New handoff schema versions solely for feature flags (detection must work on existing layout_type content).
- Downloading libraries at generate time.
- Replacing Boardroom / `gl-*`.
- Making CDN the production default.

## Further Notes

### Relationship to P0

P0 delivered `DeliveryMode`, `build_head_assets`, vendored fonts, remote URL validation, and metadata hooks. P1 **activates** the `feature_ids` parameter and reporting without expanding the offline font contract.

### Relationship to P3

P3 will vendor Chart.js (or chosen build), map `charts` feature → real bytes + init, and honor animation-off defaults. P1 must not pre-implement that payload.

### Size matrix (initial)

| Configuration | Approx HTML bytes | Notes |
|---------------|-------------------|--------|
| Baseline mini handoff, self-contained, no optional features | ~175 KB (suppress charts) | Fonts + Boardroom CSS + nav JS |
| Mini with chart layouts, `charts` enabled, P1 (no Chart.js pin) | **175008 bytes** (measured 2026-07-19) | Metadata-only enable; same payload as baseline until P3 |
| + Chart.js pin | TBD P3 | |
| + Mermaid allowlist | TBD MVP1.1 | |
| + Alpine | TBD MVP1.1 | |
| + Swiper | TBD later | |
| + icon pack expansion | TBD P6 | |

### Advisory threshold

Start at **2 MiB** soft-warn for full `presentation.html` size. Revisit after P3 pin measurements; do not promote to hard-fail in this theme.

### Acceptance checklist (engineering)

| ID | Criterion |
|----|-----------|
| P1-AC1 | Default `render_deck` auto-enables `charts` iff handoff needs chart layouts |
| P1-AC2 | `run_meta.json` and `DECK_META` include sorted `features_enabled` and a payload size field |
| P1-AC3 | Soft-warn on stderr when HTML size ≥ advisory threshold; exit code not failed by warn alone |
| P1-AC4 | Force/suppress overrides work with documented precedence |
| P1-AC5 | Unknown forced feature id fails closed |
| P1-AC6 | Self-contained output still passes remote-fetch validation |
| P1-AC7 | No Chart.js (or other new third-party JS) file required in repo for P1 green |
| P1-AC8 | Existing renderer_v2 suites remain green (SC-COMPAT-1) |
| P1-AC9 | Docs mention auto-enable, overrides, soft-warn |
| P1-AC10 | Size matrix baseline row filled with a measured number from the mini (or golden) fixture |

### Seams locked with user (2026-07-19)

1. Primary seam = `render_deck` + `run_meta` — **yes**  
2. Gate-only, **no** Chart.js pin — **yes**  
3. Supporting inliner + pure detect — as above  

*End of P1 spec.*
