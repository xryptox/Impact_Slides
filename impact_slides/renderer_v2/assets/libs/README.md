# Vendored third-party libraries (renderer_v2)

Minified/UMD, **version-pinned** third-party JS/CSS lives here so decks can be
generated fully self-contained (offline / corporate VPN safe).

Rules:

- **Pin versions** — record every file in `../THIRD_PARTY.md` (name, version,
  license, source URL, how obtained).
- **Never fetch at render time** — `render_deck` must not touch the network;
  these files are committed (or vendored by an explicit maintainer step).
- **Inline via `lib_inliner.py` only** — no ad-hoc CDN tags in layout code.
- Include upstream LICENSE text alongside vendored artifacts.

## Current pins

| File | Feature id | Notes |
|------|------------|--------|
| `chart.umd.min.js` | `charts` | Chart.js 4.4.8 UMD build (jsDelivr). Inlined only when `charts` is enabled. |

Mermaid / Alpine / Swiper / Lucide remain deferred (MVP1.1+).
