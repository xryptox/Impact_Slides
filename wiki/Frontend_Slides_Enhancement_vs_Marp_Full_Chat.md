# Enhancing frontend-slides for Consistency (vs Marp)

**Conversation Export**  
**Starting Point:** "can we enhance the frontend slides skills to give consistent output and strong theme adherence like marp"  
**Date:** July 2026

---

## Overview

The user wanted to improve the `frontend-slides` skill (used in Impact Slides Step 4) to achieve better **layout consistency**, **theme adherence**, and **determinism** — similar to what Marp/Marpit provides through its declarative CSS theme system.

### Key Trade-off Identified

| Aspect                        | Marp/Marpit                  | frontend-slides (Original)      | Enhanced frontend-slides (Proposed) |
|-------------------------------|------------------------------|----------------------------------|-------------------------------------|
| Consistency                   | Very High                    | Medium                           | High                                |
| Theme Adherence               | Excellent                    | Good                             | Very Good                           |
| Rich Animations & Polish      | Weak                         | Excellent                        | Excellent                           |
| Determinism                   | Very High                    | Medium                           | High                                |
| Evidence Traceability         | Medium                       | Weak                             | Strong                              |
| Implementation Effort         | Already done                 | Already done                     | Medium-High                         |

**Recommendation:** Enhance `frontend-slides` using a **hybrid approach** (structured Python mapping + component library + validation) rather than fully switching to Marp.

---

## Proposed Enhancement Strategy

We designed a multi-phase improvement plan:

### Implementation Roadmap

| Phase | Task | Status |
|-------|------|--------|
| 1     | Create folder structure + `tokens.css` | Done |
| 2     | Build core component library | Done |
| 3     | Add strict component rules to SKILL.md | Recommended |
| 4     | Build Python mapping layer | Done |
| 5     | Add automated validation | Done (simplified) |
| 6     | Create full slide templates | Optional |

---

## Phase 2: Core Component Library

We implemented 7 high-priority reusable components using the design tokens system.

### Components Created:

1. `kpi-card.html`
2. `metrics-grid.html`
3. `bar-chart-horizontal.html`
4. `process-flow.html`
5. `evidence-box.html`
6. `data-table.html`
7. `two-column.html`

All components follow this structure:
- Use CSS custom properties from `tokens.css`
- Support `data-evidence-id`
- Designed for 1920×1080 fixed stage
- Animation-friendly

---

## Design Tokens (`tokens.css`)

### Extended Version (Recommended)

```css
:root {
  /* Brand Colors */
  --brand-primary: #1a365d;
  --brand-secondary: #2c5282;
  --brand-accent: #3182ce;
  --brand-highlight: #ed8936;

  /* Semantic Colors */
  --color-success: #38a169;
  --color-error: #e53e3e;

  /* Surfaces & Text */
  --color-bg: #ffffff;
  --color-surface: #f7fafc;
  --color-text: #1a202c;

  /* Typography */
  --font-heading: 'Inter', system-ui, sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;

  /* Spacing */
  --space-xs: 8px;
  --space-sm: 16px;
  --space-md: 24px;
  --space-lg: 32px;
  --space-xl: 48px;

  /* Component-specific tokens */
  --kpi-value-font-size: var(--font-size-5xl);
  --kpi-border-radius: var(--radius-xl);
  --chart-bar-height: 32px;
  --flow-step-number-size: 96px;
  --table-row-height: 64px;
  /* ... many more component tokens */
}
```

Tokens can be dynamically generated from `brand_style_summary.json`.

---

## Phase 4: Python Mapping Layer

This layer connects `Final_Slide_Content.json` → HTML Components.

### Key Files

- `mapping/component_map.py` — Defines allowed `visual_type` values and template mapping
- `mapping/renderer.py` — Uses Jinja2 to render components

**Core Logic:**

```python
COMPONENT_MAP = {
    "metrics_grid": "layouts/metrics-grid.html",
    "kpi_single": "cards/kpi-card.html",
    "horizontal_bar_chart": "charts/bar-chart-horizontal.html",
    "process_flow": "flows/process-flow.html",
    "evidence_callout": "feedback/evidence-box.html",
    # ...
}

def render_component(visual_type, data, evidence_id=""):
    # Renders the correct component template with data
```

---

## Phase 5: Automated Validation (Simplified)

Because of server constraints (no root, no Docker), we used **pure Python validation** only.

### Validators Implemented:

1. **Structural Validator** — Checks for component usage and overflow risks
2. **Evidence Validator** — Ensures all `evidence_ids` appear in rendered HTML
3. **Token Validator** — Verifies key design tokens are used

These require only `beautifulsoup4`.

---

## Final Cleaned-up Code

### `step4_builder_validator.py` (Production Version)

```python
# step4_builder_validator.py
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader

from mapping import render_component
from validation.structural_validator import validate_structural
from validation.evidence_validator import validate_evidence
from validation.token_validator import validate_design_tokens

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "mapping" / "templates"

def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def generate_dynamic_tokens(brand_data):
    return f"""
:root {{
  --brand-primary: {brand_data.get('primary_color', '#1a365d')};
  --brand-accent: {brand_data.get('accent_color', '#3182ce')};
}}
"""

def process_final_content(final_content_path, brand_summary_path, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    final_content = load_json(final_content_path)
    brand_data = load_json(brand_summary_path)

    all_issues = []
    rendered_slides = []

    for slide in final_content.get("slides", []):
        slide_id = slide.get("slide_id", "unknown")
        visual_type = slide.get("visual_type", "content")
        data = slide.get("data", {})
        evidence_ids = slide.get("evidence_ids", [])
        evidence_id = evidence_ids[0] if evidence_ids else ""

        # Phase 4: Render
        rendered_html, render_issues = render_component(visual_type, data, evidence_id)
        all_issues.extend([f"[{slide_id}] {i}" for i in render_issues])

        # Phase 5: Validate
        all_issues.extend(validate_structural(rendered_html, slide_id))
        all_issues.extend(validate_evidence(rendered_html, evidence_ids, slide_id))
        all_issues.extend(validate_design_tokens(rendered_html, slide_id))

        rendered_slides.append({
            "slide_id": slide_id,
            "visual_type": visual_type,
            "html": rendered_html
        })

    tokens_css = generate_dynamic_tokens(brand_data)
    final_html = build_final_html(rendered_slides, tokens_css)

    html_path = output_dir / "presentation.html"
    html_path.write_text(final_html, encoding="utf-8")

    if all_issues:
        (output_dir / "validation_report.md").write_text("\n".join(all_issues))

    return {"html_path": str(html_path), "issues": len(all_issues)}

if __name__ == "__main__":
    result = process_final_content(
        Path("Final_Slide_Content.json"),
        Path("brand_style_summary.json"),
        Path("output")
    )
    print(result)
```

---

## Server Constraints & Final Recommendations

**Constraints faced:**
- No root/sudo access on remote Linux server
- No Docker available
- Cannot easily install Playwright

**Final Practical Recommendation:**

- Use **pure Python validation** (BeautifulSoup-based)
- Skip Playwright visual checks on the server
- Run the full pipeline with **Phase 4 + Simplified Phase 5**
- Optionally run Playwright validation locally during development

This approach still delivers **significantly higher consistency** than the original `frontend-slides` skill while remaining deployable in the current environment.

---

## Conclusion

By combining:
- A strong **component library**
- **Design tokens**
- **Python mapping layer**
- **Automated validation**

We can bring `frontend-slides` much closer to Marp’s consistency level while retaining its advantages in animations and visual quality.

**Best Path Forward:** Implement Phases 1–5 as outlined above, then gradually add Phase 3 (strict rules in SKILL.md) and Phase 6 (full slide templates).

---

**End of Conversation Export**  
*Generated on 2026-07-07*