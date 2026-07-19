# SPEC: Renderer v2 — P0 Self-Contained Foundation

**Status:** Engineering spec — ready to ticket; **not** implemented by this doc  
**Date:** 2026-03-26  
**Theme:** P0 (MVP1)  
**Scope lock:** `wiki/SCOPE_renderer_v2_mvp1.md`  
**Alignment:** D1 (self-contained default), D3 (tokens always on; JS later gated), D14 (spec → tickets → implement)  
**Success criteria:** SC-OFFLINE-1, SC-OFFLINE-2, SC-CLI-1, SC-MOD-1, SC-REG-1 (and P0 slice of SC-COMPAT-1)

---

## 0. Purpose

Make “self-contained HTML deck” a **real, tested product contract**, not a docstring claim.

Today the package already inlines Boardroom CSS and deck navigation JS, but **production output still depends on the network** (Google Fonts CDN). There is no dual-mode CLI, no centralized third-party asset pipeline, and no regression guard against remote URLs.

P0 fixes that foundation and leaves **seams** for P1+ (feature gates, Chart.js, etc.) without implementing those themes.

---

## 1. Current state (factual baseline)

| Area | Today | Gap vs P0 |
|------|--------|-----------|
| CSS | `shell.load_css()` concatenates `css/*.css` + `chart_css()` into a `<style>` block | Already local; must stay on the inliner path |
| Deck JS | Inline IIFE in `shell.wrap_deck` (`fitStage`, keys, notes) | Already local; optional to route via inliner for consistency |
| Fonts | `<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3...&family=IBM+Plex+Sans...">` in `shell.py` | **Breaks offline / VPN** — primary P0 defect |
| CLI | `--handoff`, `--out`, `--seed`, `--debug`, `--no-strict`, `--version` | No `--self-contained` / `--use-cdn` |
| `render_deck` | No delivery-mode parameter | Must accept mode and pass through to shell |
| Vendored libs | No `assets/libs/` | Need layout + pin metadata for fonts now; JS libs later |
| Inliner module | **Absent** | Add `lib_inliner.py` (or equivalent name) as single owner |
| Validation | `manifest.validate_html` checks Boardroom tokens / face EIDs / `fitStage` | No external-URL policy |
| Tests | Layout/theme/grid gates exist | No self-contained URL fixture tests |
| Entry points | `python -m impact_slides.renderer_v2`, `step4_renderer_v2.py` shim | Both must honor new flags via `cli.main` |

**Non-goals already true and must not regress:** Boardroom + `gl-*` shell; single-file `presentation.html` output model; existing validation rules unless extended additively.

---

## 2. Goals and non-goals

### 2.1 Goals

1. **Production default = self-contained** (D1): generated `presentation.html` does not *require* any network request to render Boardroom text/layout/chrome.  
2. **CDN mode = explicit dev escape hatch** only (`--use-cdn`).  
3. **Centralize** embedding of external/vendored assets (fonts now; future CSS/JS libs via same module).  
4. **Test** self-contained output for unexpected remote URL references.  
5. **Record** delivery mode in `run_meta.json` / `DECK_META` for supportability.  
6. Preserve **backward-compatible** default behavior for callers that don’t pass new flags: default becomes self-contained (stricter offline), which may change font loading vs today’s CDN — that is intentional.

### 2.2 Non-goals (out of P0)

| Out | Owner theme |
|-----|-------------|
| Feature flags / auto-enable / size warn matrix | **P1** |
| Open Props token merge | **P2** |
| Chart.js wiring + static fallback policy beyond keeping current SVG charts working | **P3** |
| Native disclosure patterns | **P5** |
| Mermaid, Alpine, Swiper, Lucide | MVP1.1+ |
| PDF ready-state hooks | P9 / parallel |
| Downloading libs from the internet **at generate time** in CI by default | Prefer **committed vendored** assets; optional maintainer script only |
| Changing chart rendering from current SVG pipeline | P3 |
| Animation work | D15 non-goal |

---

## 3. Delivery-mode contract

### 3.1 Modes

| Mode | CLI | Default? | Behavior |
|------|-----|----------|----------|
| **self-contained** | default; optional explicit `--self-contained` | **Yes** | No required remote CSS/JS/font URLs in output. Fonts via vendored `@font-face` and/or safe local/system stack documented below. Future libs inlined from `assets/libs/`. |
| **cdn** | `--use-cdn` | No | May emit documented CDN `<link>` / `<script src>` for **dev** (fonts today; later libs). Must never be implied by “ship” docs/examples. |

**Mutual exclusion:** If both flags are passed, **fail** with a clear CLI error (exit ≠ 0).

**API:**

```python
render_deck(
    handoff_path,
    out_dir,
    *,
    seed_path=None,
    debug=False,
    strict=True,
    theme=None,
    delivery: Literal["self-contained", "cdn"] = "self-contained",
)
```

Name `delivery` is normative in this spec; implementors may use `self_contained: bool` **only if** CLI and `run_meta` still expose the two-mode vocabulary above.

### 3.2 What “no required network” means

For **self-contained** mode, `presentation.html` must:

1. Render slide chrome, typography fallback, grid, and navigation with **network disabled**.  
2. Contain **no** of the following *network-fetching* constructs for **required** assets:
   - `<link rel="stylesheet" href="http(s)://...">`
   - `<script src="http(s)://...">`
   - CSS `@import url("http(s)://...")`
   - `@font-face` `url("http(s)://...")`  
3. **Allow** non-fetching URL-like strings that are not browser network loads:
   - SVG `xmlns="http://www.w3.org/2000/svg"` (and similar XML namespaces)
   - `xmlns:xlink` etc.  
4. **Allow** `data:` URLs for fonts/images inlined by the generator.  
5. **Disallow** protocol-relative URLs `//fonts.googleapis.com/...` as well.

**CDN mode** may include the current Google Fonts stylesheet link (and, later, pinned CDN URIs for libs). CDN mode still inlines first-party Boardroom CSS/JS as today unless a future spec says otherwise.

### 3.3 Font strategy (P0-critical)

Boardroom tokens reference **Source Sans 3** and **IBM Plex Sans** (`css/tokens.css`).

#### Normative self-contained approach (choose one primary; document in code)

**Preferred (A) — Vendored WOFF2 subset + `@font-face`**

1. Commit binary font files under:

   ```text
   impact_slides/renderer_v2/assets/fonts/
     SOURCE_SANS_3_LICENSE.txt
     IBM_PLEX_SANS_LICENSE.txt
     source-sans-3-latin-400.woff2
     source-sans-3-latin-600.woff2
     source-sans-3-latin-700.woff2
     ibm-plex-sans-latin-400.woff2
     ibm-plex-sans-latin-500.woff2
     ibm-plex-sans-latin-600.woff2
     ibm-plex-sans-latin-700.woff2
   ```

   Exact filenames may vary; **weights used by Boardroom CSS must be covered** (at least 400/600/700 for Source Sans 3; 400/500/600/700 for IBM Plex Sans if referenced). Latin subset is enough unless product later requires more.

2. Inliner emits a `<style>` (or fragment merged into main CSS) with `@font-face` rules using **`url(data:font/woff2;base64,...)`** *or* documents a companion-file mode (see §3.4). **Default product shape remains single `presentation.html`** → prefer **base64 data URLs** for fonts in self-contained mode.

3. Keep `tokens.css` family names unchanged so components don’t churn.

**Acceptable fallback (B) — System stack only (no webfont files)**

If vendoring WOFF2 is blocked (license packaging delay), self-contained mode may:

1. **Strip** the Google Fonts `<link>`.  
2. Adjust `--font-*` stacks to prioritize high-quality system fonts that preserve metrics reasonably, e.g. `"Source Sans 3", "Segoe UI", system-ui, sans-serif`, while still listing Boardroom names first for environments that have them installed.

**B is allowed only as a transitional implementation** if A cannot land in the same ticket set; the P0 epic is **not done** until either A ships **or** product explicitly accepts B as permanent (default expectation: **A**).

**CDN mode:** may keep today’s Google Fonts `<link>` (optionally version-pinned query). Must not be the production default.

### 3.4 Single-file vs sidecar assets

| Policy | P0 decision |
|--------|-------------|
| Default output | **Single** `presentation.html` (plus existing `slide_notes.md`, `evidence_manifest.json`, `run_meta.json`) |
| Sidecar `assets/` next to HTML | **Not required** in P0 |
| Inlined vendor JS/CSS (future) | Embed as raw text in `<script>` / `<style>` via inliner |
| Inlined fonts | `data:` URLs (preferred) |

If an implementation temporarily writes sidecars, that is a **spec deviation** needing scope amendment.

---

## 4. Module design

### 4.1 New: `impact_slides/renderer_v2/lib_inliner.py`

**Single owner** for third-party / vendored asset embedding (SC-MOD-1).

Suggested public surface (normative names can be bikesheded in review if equivalent):

```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

class DeliveryMode(str, Enum):
    SELF_CONTAINED = "self-contained"
    CDN = "cdn"

@dataclass(frozen=True)
class AssetRef:
    asset_id: str          # e.g. "font-source-sans-3-400", "css-open-props" (future)
    kind: str              # "font" | "css" | "js"
    path: Path | None      # vendored file path
    cdn_url: str | None    # only used in CDN mode
    license_path: Path | None = None

@dataclass(frozen=True)
class InlineBundle:
    head_html: str         # <style>/<link>/<script> fragments for <head> or end of body
    meta: dict             # ids included, mode, byte estimates

def iter_core_assets() -> list[AssetRef]:
    """Assets required for every deck (fonts; later always-on CSS libs)."""

def build_head_assets(
    mode: DeliveryMode,
    *,
    feature_ids: Iterable[str] = (),
) -> InlineBundle:
    """
    P0: feature_ids ignored or only validated empty/unknown.
    P1+: feature_ids selects optional JS/CSS to inline.
    """
```

**Responsibilities:**

| Must | Must not |
|------|----------|
| Resolve vendored paths relative to package | Scrape the live internet during normal `render_deck` |
| Emit self-contained or CDN tags per mode | Duplicate Google Fonts link logic in random layout files |
| Provide approximate byte size of inlined payload (for P1 warnings) | Implement Chart.js/Mermaid/Alpine |
| Fail clearly if required vendored file missing in self-contained mode | Silently fall back to CDN when self-contained was requested |

**Package layout:**

```text
impact_slides/renderer_v2/
  lib_inliner.py
  assets/
    fonts/           # P0
    libs/            # P1+ (may be empty dir + README in P0)
      README.md      # “pin versions here; do not fetch at runtime”
    THIRD_PARTY.md   # short inventory: name, version, license, source URL (start fonts)
  css/               # existing first-party
  shell.py
  cli.py
  ...
```

### 4.2 Change: `shell.py`

1. Remove hard-coded Google Fonts `<link>` from the always-on template path.  
2. Call `lib_inliner.build_head_assets(mode)` and inject `bundle.head_html` into the document head (before or after main Boardroom `<style>` — order must be documented: **font faces before components CSS**).  
3. `wrap_deck(..., delivery: DeliveryMode | str = "self-contained")`.  
4. Include in `DECK_META`:

   ```json
   "delivery": "self-contained" | "cdn",
   "assets_inlined": ["font-...", "..."]
   ```

5. First-party CSS (`load_css`) remains first-party; **do not** move Boardroom CSS into `assets/libs/`. Optional later: route through a thin helper for one injection site — not required if fonts/libs are the only inliner consumers.

### 4.3 Change: `cli.py` / `render_deck`

1. Add flags:

   | Flag | Effect |
   |------|--------|
   | `--self-contained` | Force `delivery=self-contained` (default already; useful for scripts/docs) |
   | `--use-cdn` | Force `delivery=cdn` |

2. Pass `delivery` into `wrap_deck`.  
3. Extend `run_meta.json`:

   ```json
   {
     "generator": "impact_slides.renderer_v2",
     "version": "...",
     "delivery": "self-contained",
     "assets_inlined": ["..."],
     "...": "existing fields unchanged"
   }
   ```

4. Keep `step4_renderer_v2.py` as thin shim — no duplicate argparse.

### 4.4 Change: `manifest.validate_html` (or dedicated validator)

Add **mode-aware** checks:

```text
validate_html(html, *, delivery: DeliveryMode = SELF_CONTAINED) -> list[str]
```

When `delivery == SELF_CONTAINED`:

- Error if any **network-fetching** remote reference matches the policy in §3.2 (implement via robust regex/parser; prefer a small dedicated function `remote_fetch_urls(html) -> list[str]` for testability).  
- Do **not** flag SVG/XML namespaces.  
- Do **not** flag `data:` URLs.

When `delivery == CDN`:

- Skip the “no remote URLs” hard fail (or only warn on *unknown* hosts — optional, not required in P0).  
- Still run existing Boardroom / face-EID / `fitStage` checks.

Wire `render_deck` so strict mode applies these errors like today.

### 4.5 Seams for P1 (implement stubs only if cheap)

P0 should not build full feature detection, but the inliner API should accept `feature_ids: Iterable[str] = ()` and:

- **P0 behavior:** ignore empty; if non-empty unknown ids → **warn** or **ignore** (pick **warn to stderr**, don’t fail — fail-closed feature policy is P1).  
- Document reserved ids: `charts`, `mermaid`, `alpine`, `swiper`, `icons` (no behavior yet).

Do **not** implement auto-enable from handoff in P0.

---

## 5. CLI UX and docs

### 5.1 Examples (normative for README / module doc)

```bash
# Production / corporate (default)
python -m impact_slides.renderer_v2 --handoff builder_handoff.json --out out_dir

# Explicit self-contained
python -m impact_slides.renderer_v2 --handoff builder_handoff.json --out out_dir --self-contained

# Dev-only CDN fonts (and later CDN libs)
python -m impact_slides.renderer_v2 --handoff builder_handoff.json --out out_dir --use-cdn
```

### 5.2 Help text requirements

- Describe default as self-contained / offline-safe.  
- Label `--use-cdn` as **development only; not for customer/VPN deliverables**.

### 5.3 Maintainer note

`assets/THIRD_PARTY.md` lists each vendored font (and later lib): package name, version, license, upstream URL, and how files were obtained. No need for a full SBOM tool in P0.

Optional maintainer script `scripts/vendor_renderer_fonts.py` (or under package) **may** exist to regenerate base64/font files; **render path must not call network**.

---

## 6. Acceptance criteria (P0 done)

| ID | Criterion | Verify how |
|----|-----------|------------|
| **P0-AC1** | Default CLI/`render_deck` uses self-contained delivery | Unit/CLI test |
| **P0-AC2** | Self-contained HTML has **zero** required remote fetch URLs per §3.2 | `remote_fetch_urls` test on fixture output |
| **P0-AC3** | Self-contained deck uses Boardroom font **families** without Google Fonts link | Assert no `fonts.googleapis.com`; assert `@font-face` and/or accepted system stack per chosen strategy A/B |
| **P0-AC4** | `--use-cdn` emits CDN font stylesheet (or documented CDN tags) and does not break render | CLI test on fixture |
| **P0-AC5** | Passing both `--self-contained` and `--use-cdn` errors | CLI test |
| **P0-AC6** | `run_meta.json` and `DECK_META` record `delivery` | Fixture assert |
| **P0-AC7** | Inliner is the only module that knows vendored font/lib paths for head assets | Code structure review + import direction (shell → inliner, not reverse) |
| **P0-AC8** | Existing handoff fixtures still render (`SC-COMPAT-1` smoke); strict validation still passes for known-good fixtures | Existing + new tests |
| **P0-AC9** | Missing vendored font file in self-contained mode → **clear fail** (not silent CDN) | Unit test with monkeypatched path / tmp assets |
| **P0-AC10** | `validate_html` fails self-contained output if a Google Fonts link is reintroduced | Unit test with poisoned HTML string |

**SC mapping:** AC2–AC3 → SC-OFFLINE-*; AC1/AC4/AC5 → SC-CLI-1; AC7 → SC-MOD-1; AC2/AC10 → SC-REG-1.

**Offline open check:** At least one automated test must generate HTML from a minimal handoff fixture and assert the remote-URL policy. A full “headless browser with network offline” check is **nice** but **not required** for P0 if static HTML policy tests are solid; MVP1 golden deck offline open remains a later MVP1 bar (P3/P5).

---

## 7. Test plan

### 7.1 New tests (suggested file)

`tests/test_renderer_v2_self_contained.py`

| Test | Intent |
|------|--------|
| `test_default_delivery_is_self_contained` | API/CLI default |
| `test_self_contained_html_has_no_remote_fetches` | Core offline contract |
| `test_self_contained_strips_google_fonts_link` | Specific regression for current bug |
| `test_cdn_mode_allows_google_fonts_link` | Dual mode |
| `test_cli_rejects_conflicting_flags` | UX |
| `test_run_meta_records_delivery` | Observability |
| `test_validate_html_flags_remote_stylesheet` | Guard |
| `test_remote_fetch_urls_ignores_svg_xmlns` | False-positive guard |
| `test_missing_font_asset_fails_self_contained` | Fail closed on assets (strategy A) |

### 7.2 Fixtures

- Reuse a minimal handoff under `tests/fixtures/renderer_v2/` (existing if suitable; else add `minimal_handoff.json` with 1–2 simple slides, no new chart lib requirements).  
- Do not require network in pytest.

### 7.3 Manual check (optional checklist for implementer)

1. Generate with default flags.  
2. Open `presentation.html` in browser with network disabled (DevTools offline).  
3. Confirm slides navigate and text is readable (fonts may be subset/system).  
4. Generate with `--use-cdn`; confirm fonts load when online.

---

## 8. Implementation slices (ticketizable)

These are **suggested tickets**, not filed issues. File only when asked (`gh`), after any review tweaks to this spec.

### Ticket P0.1 — Delivery mode plumbing

- Add `DeliveryMode` + `render_deck(..., delivery=...)`.  
- CLI `--self-contained` / `--use-cdn` + conflict error.  
- Thread through `wrap_deck`; record in `run_meta` + `DECK_META`.  
- Tests: default, conflict, meta.  
**Effort:** S  

### Ticket P0.2 — `lib_inliner` + package assets layout

- Create `lib_inliner.py`, `assets/fonts/`, `assets/libs/README.md`, `assets/THIRD_PARTY.md`.  
- Move font head-tag responsibility out of hard-coded `shell.py` string.  
- Tests: import/path resolution; shell calls inliner.  
**Effort:** S–M  

### Ticket P0.3 — Self-contained fonts (strategy A preferred)

- Vendor WOFF2 + licenses; emit `@font-face` data URLs in self-contained mode.  
- CDN mode keeps Google Fonts link via inliner.  
- Fail if files missing in self-contained.  
**Effort:** M (licensing + binary packaging)  

### Ticket P0.4 — Remote URL validation + regression tests

- `remote_fetch_urls()` + `validate_html(..., delivery=)`.  
- Full test module §7.1.  
- Ensure existing renderer tests still pass.  
**Effort:** S  

### Ticket P0.5 — Docs touch-up

- Module docstring / `step4_renderer_v2.py` usage lines / short note in relevant wiki or README pointing at default offline behavior and `--use-cdn` dev-only.  
**Effort:** S  

**Suggested merge order:** P0.1 → P0.2 → P0.3 → P0.4 → P0.5 (P0.4 can start in parallel with P0.3 against temporary “strip CDN link + system fonts” if A slips).

---

## 9. Risks and edge cases

| Risk | Mitigation |
|------|------------|
| Base64 fonts bloat HTML | Latin subsets only; measure in P1 size matrix; still smaller political cost than broken VPN decks |
| License packaging mistakes | Commit upstream LICENSE text beside binaries; THIRD_PARTY.md |
| False positives on `http://` in SVG/xmlns | Allowlist namespace patterns in `remote_fetch_urls` |
| False negatives via CSS tricks / JS dynamic inject | P0 covers static generator output only; no runtime CDN loaders in first-party JS |
| Callers depending on Google Fonts aesthetics online | Default self-contained may look slightly different until WOFF2 ships; CDN flag preserves old path |
| Windows path / package data missing in wheels | Use `importlib.resources` or `Path(__file__).parent` consistently; add test that assets resolve from installed layout |
| Double font definition if tokens and @font-face diverge | Inliner owns @font-face; tokens keep family names only |

---

## 10. Explicit “done / not done” boundaries

### P0 is done when

- All **P0-AC1–AC10** pass in CI.  
- Default generation path no longer emits `fonts.googleapis.com`.  
- Inliner module exists and owns head asset emission for fonts.  
- Docs state self-contained default + CDN dev-only.

### P0 is not done if

- Self-contained silently uses CDN when fonts missing.  
- Layout/recipe files grow their own `<script src="https://...">`.  
- Feature auto-enable / Chart.js / Open Props are required to merge P0 (those are later themes).

---

## 11. Dependencies / follow-on

| After P0 | Consumes |
|----------|----------|
| **P1** | `feature_ids` on inliner; size estimate API; auto-enable |
| **P2** | Still first-party CSS pipeline; may add always-on Open Props file via inliner or `css/` |
| **P3** | Optional `charts` asset id → Chart.js vendor file |
| MVP1 golden offline deck | Relies on P0 contract + P3/P5 content |

---

## 12. Open implementation choices (resolve in PR, not product realignment)

1. **Strategy A vs transitional B** for fonts (§3.3) — default expectation **A**.  
2. Exact WOFF2 subset source (Google fonts download, adobe-fonts/source-sans, IBM plex release zips) — must be legal redistributable files with licenses committed.  
3. Whether deck navigation `_JS` moves behind inliner (optional consistency) or stays private in `shell.py` (acceptable in P0).  
4. Regex vs HTML parser for `remote_fetch_urls` — either OK if tests lock behavior.

These do **not** reopen D1–D15.

---

## 13. Document control

| Field | Value |
|-------|--------|
| Parent scope | `wiki/SCOPE_renderer_v2_mvp1.md` |
| Next step | File tickets P0.1–P0.5 (when user asks) → implement |
| Implementation in this step | **None** |

*End of P0 engineering spec.*
