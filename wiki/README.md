# Wiki / archive

Historical prompts, plans, research, chat exports, and one-shot bake/gen scripts moved out of the repo root so the project surface stays code-first.

Prefer live code under `impact_slides/`, entry scripts at repo root, and `README.md` for current docs. Agent skill config: `AGENTS.md` + `docs/agents/`.

### Legacy preprocessor bodies

Full historical step1 implementations (v1–v3) live under `legacy/`. Root `step1_preprocessor*.py` for those versions are thin import shims so pytest keeps working. **Canonical pipeline entrypoint: `step1_preprocessor_v4.py` → `impact_slides/`.**

### Stale-doc markers

Docs that describe deleted code, or that a later numbered doc supersedes, carry a
`> **Superseded - historical ...**` line directly under their H1. This exists because a
repo-wide `rg` does not read this file: without the marker, dead guidance comes back
formatted exactly like live guidance.

Deliberately **not** marked: `SPEC_renderer_v2_amex_fidelity_r6.md` (live draft,
pending human lock), `baseline_v8_GAP_ANALYSIS.md` (current baseline), the
`SPEC_renderer_v2_p0..p5` / `tokens_owner` specs (shipped but still normative), the
`Impact Slide *` GPT prompts (live Step 2/3 artifacts), and the generated
`renderer_v2_LAYOUTS.md`.
