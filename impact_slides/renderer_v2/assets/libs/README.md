# Vendored third-party libraries (renderer_v2)

Minified, **version-pinned** third-party JS/CSS lives here so decks can be
generated fully self-contained (offline / corporate VPN safe).

Rules:

- **Pin versions** — record every file in `../THIRD_PARTY.md` (name, version,
  license, source URL, how obtained).
- **Never fetch at render time** — `render_deck` must not touch the network;
  these files are committed (or vendored by an explicit maintainer step).
- **Inline via `lib_inliner.py` only** — no `<script src="https://...">` or
  ad-hoc CDN tags in layout/shell code.
- Include upstream LICENSE text alongside vendored artifacts.

Currently empty: Chart.js / Mermaid / Alpine / Swiper / Lucide land with P1+
feature work (see `wiki/SPEC_renderer_v2_p0_self_contained.md` and
`wiki/SCOPE_renderer_v2_mvp1.md`).
