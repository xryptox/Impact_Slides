# Third-party assets vendored by renderer_v2

Inventory of external assets embedded into generated decks. Keep one row per
vendored artifact; update whenever a file under `assets/` changes.

| Asset | Version | License | Source | Obtained via | Notes |
|-------|---------|---------|--------|--------------|-------|
| Source Sans 3 (variable WOFF2, latin) | Google Fonts v19 (2026-07) | SIL OFL 1.1 (`fonts/SOURCE_SANS_3_LICENSE.txt`) | https://fonts.google.com/specimen/Source+Sans+3 · upstream: https://github.com/adobe-fonts/source-sans | Google Fonts css2 API, latin subset | `fonts/source-sans-3-latin.woff2` (28.7 KB); weights 400–700 |
| IBM Plex Sans (variable WOFF2, latin) | Google Fonts v23 (2026-07) | SIL OFL 1.1 (`fonts/IBM_PLEX_SANS_LICENSE.txt`) | https://fonts.google.com/specimen/IBM+Plex+Sans · upstream: https://github.com/IBM/plex | Google Fonts css2 API, latin subset | `fonts/ibm-plex-sans-latin.woff2` (45.7 KB); weights 400–700 |
| Chart.js UMD (min) | 4.4.8 | MIT (`libs/CHART_JS_LICENSE.md`) | https://www.chartjs.org/ · https://github.com/chartjs/Chart.js | jsDelivr `chart.js@4.4.8/dist/chart.umd.min.js` | `libs/chart.umd.min.js` (~202 KB); feature-gated `charts`; CDN URL matches min pin |

Process (per `wiki/SPEC_renderer_v2_p0_self_contained.md`):

1. Download from the official upstream release/CDN only.
2. Commit the upstream LICENSE beside the artifact.
3. Record version + source URL here.
4. Re-measure inlined byte size when bumping versions — use `run_meta.json`
   `html_bytes` / `bytes_inlined` and update the size matrix in
   `wiki/SPEC_renderer_v2_p1_feature_size_gating.md`.
