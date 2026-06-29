# Step 4 — Python Builder / Validator Updated Plan

## Alignment Decisions

1. **HTML output format:** one standalone `presentation.html` with embedded assets.
2. **HTML richness:** HTML may be more animated/rich than PPTX.
3. **Inline editing:** skip for now.
4. **HTML to PDF:** optional export supported.
5. **Weak brand data:** use clean neutral fallback while incorporating maximum valid attributes from `brand_style_summary.json`.
6. **Internet access:** allowed for Google Fonts / Fontshare and other web fonts.

---

## Inputs

- `Final_Slide_Content.json` from Impact Slide Builder
- `brand_style_summary.json` from Step 1
- `asset_manifest.json` optional
- source image/assets folder optional

---

## Outputs

- `updated_presentation.pptx`
- `presentation.html` optional standalone HTML deck
- `presentation.pdf` optional PDF export from HTML
- `validation_report.md`
- `validation_report.json`
- `html_validation_report.md` optional

---

## Core Modules

### 1. JSON Validator

Validates:

- Required presentation and slide fields
- Slide count consistency
- Evidence references
- Bullet length
- Missing speaker notes
- Visual spec completeness
- Unsupported layout types

### 2. Brand Theme Resolver

Reads `brand_style_summary.json` and creates normalized theme tokens:

```json
{
  "colors": {},
  "fonts": {},
  "layout": {},
  "chart_style": {},
  "logo_rules": {},
  "fallbacks_used": []
}
```

Rules:

- Use valid extracted brand colors first.
- Use extracted fonts where practical.
- If brand data is weak, use clean neutral fallback.
- Preserve brand-derived attributes in both PPTX and HTML.
- Validate color contrast where possible.

### 3. PPTX Builder

Uses `python-pptx` to generate:

- Title slides
- Text + visual slides
- KPI slides
- Comparison slides
- Process/timeline slides
- Basic chart/table layouts where possible

PPTX should be clean, brand-aligned, and less animated than HTML.

### 4. HTML Deck Builder

Uses the `frontend-slides` architecture:

- Fixed 1920×1080 slide stage
- Stage scales uniformly to viewport
- No responsive content reflow
- `.active` / `.visible` slide switching
- Full `viewport-base.css` embedded
- Inline CSS and JS
- Keyboard, touch, and wheel navigation
- `prefers-reduced-motion` support
- No inline editing controls for now
- Standalone HTML with embedded image assets
- Internet web fonts allowed

HTML may include richer but tasteful animations:

- Staggered reveals
- Subtle chart/card entrance animations
- Background gradients/patterns
- Section transitions
- Reduced-motion fallback

### 5. HTML Asset Embedder

Embeds assets as base64 data URIs inside the HTML file.

Rules:

- Never overwrite original assets.
- Resize very large images before embedding if needed.
- Add useful alt text from slide JSON or asset metadata.
- Keep final HTML portable as a single file.

### 6. HTML Validator

Checks:

- Required `.deck-viewport`, `.deck-stage`, `.slide` structure
- 1920×1080 stage dimensions
- Slide count matches JSON
- CSS variables exist
- Brand tokens are used
- Images are embedded or resolvable
- Basic accessibility attributes
- No obvious text overflow markers

Optional visual validation with Playwright:

- Render screenshots at 1920×1080
- Check slides load without JS errors
- Export screenshots/PDF if requested

### 7. Optional HTML to PDF Export

Uses Playwright Chromium to render each slide and export a PDF.

Output:

- `presentation.pdf`

Notes:

- PDF is static; animations are not preserved.
- Uses final visual state of slides.

---

## Proposed CLI

```bash
python step4_builder_validator.py ^
  --input Final_Slide_Content.json ^
  --brand brand_style_summary.json ^
  --output output_folder ^
  --pptx ^
  --html
```

Optional:

```bash
--html-standalone
--export-html-pdf
--density speaker-led
--density reading-first
--open-html
--validate-visual
--assets asset_manifest.json
--asset-root path_to_assets
```

---

## Additional Packages

```bash
python -m pip install beautifulsoup4 playwright
python -m playwright install chromium
```

Core Step 4 packages:

```bash
python -m pip install python-pptx jinja2 pydantic jsonschema matplotlib plotly kaleido pillow webcolors wcag-contrast-ratio
```

---

## Implementation Priority

1. JSON validation and reporting
2. Brand theme resolver
3. Basic PPTX generation
4. Standalone HTML generation
5. HTML validation
6. Optional HTML-to-PDF export
7. Richer layout templates and animations
