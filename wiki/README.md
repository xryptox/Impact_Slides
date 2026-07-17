# Wiki / archive

Historical prompts, plans, research, chat exports, and one-shot bake/gen scripts moved out of the repo root so the project surface stays code-first.

Prefer live code under `impact_slides/`, entry scripts at repo root, and `README.md` for current docs. Agent skill config: `AGENTS.md` + `docs/agents/`.

### Legacy preprocessor bodies

Full historical step1 implementations (v1–v3) live under `legacy/`. Root `step1_preprocessor*.py` for those versions are thin import shims so pytest keeps working. **Canonical pipeline entrypoint: `step1_preprocessor_v4.py` → `impact_slides/`.**
