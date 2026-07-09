"""YAML config support (v3 #21): layered config resolution + validation.

Extracted from the monolith. CONFIG_DEFAULTS is the single source of truth —
argparse defaults and YAML defaults stay in sync because both derive from this
dict. CONFIG_CHOICES mirrors the `choices=[...]` on argparse flags so YAML
values are validated the same way CLI values are.

Precedence: CLI flag (explicit) > YAML value > argparse default.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
    _HAS_YAML = True
except ImportError:  # pragma: no cover - graceful degradation
    yaml = None
    _HAS_YAML = False


from .schemas import MAX_TEXT_LENGTH as _SCHEMA_MAX_TEXT_LENGTH

CONFIG_DEFAULTS = {
    "input": None,
    "output": None,
    "filter_level": "conservative",
    "boost_keywords": [],
    "verbose": False,
    "export_md": False,
    "export_csv": False,
    "enable_ocr": False,
    "tesseract_cmd": None,
    "pdf_table_engine": "auto",
    "dedup_engine": "auto",
    "inspect": False,
    "inspect_top": 15,
    "emit_schema": False,
    "stage_rules": None,    # v3 #24: optional Why/What/How/Now mapping overrides
    "focus_areas": 5,       # v4 #26: number of focus areas in the briefing
    "briefing": None,       # v4 #26: optional briefing config (weights, business_keywords)
    "max_text_length": _SCHEMA_MAX_TEXT_LENGTH,  # uniform evidence `text` cap
    "semantic_type_keywords": [],  # v4: extra Risk keywords (plain substrings)
}

CONFIG_CHOICES = {
    "filter_level": ("conservative", "moderate", "permissive"),
    "pdf_table_engine": ("auto", "pdfplumber", "pymupdf"),
    "dedup_engine": ("auto", "embeddings", "tfidf", "fuzzy"),
}


def load_config(path: Optional[str]) -> Dict[str, Any]:
    """Load a YAML config file into a dict.

    - path is None -> returns {} (no config; CLI-only mode).
    - path given but missing -> raises FileNotFoundError (a typo'd --config
      must never silently fall back to defaults and run against the wrong
      input folder).
    - PyYAML not installed -> raises RuntimeError with a clear pip hint.
    - Top level must be a YAML mapping.
    """
    if not path:
        return {}
    if not _HAS_YAML:
        raise RuntimeError(
            "--config requires PyYAML which is not installed. "
            "Install it with: pip install pyyaml"
        )
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)  # safe_load, never load() — config files are shared
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(
            f"Config file {path} must contain a YAML mapping at the top level, "
            f"got {type(data).__name__}"
        )
    return data


def _cli_was_set(parser, args, key: str) -> bool:
    """True iff the user explicitly passed --key on the command line (vs
    relying on the argparse default). Determined by comparing the parsed value
    against the parser's registered default, so YAML can override any flag the
    user did not type."""
    return getattr(args, key, None) != parser.get_default(key)


def merge_config(parser, args) -> Dict[str, Any]:
    """Resolve the layered config: CLI (explicit) > YAML > defaults.

    Returns a plain dict keyed by CONFIG_DEFAULTS keys (snake_case)."""
    result = dict(CONFIG_DEFAULTS)
    yaml_cfg = getattr(args, "config_data", {}) or {}
    result.update(yaml_cfg)  # YAML overrides defaults
    for key in CONFIG_DEFAULTS:
        if _cli_was_set(parser, args, key):
            result[key] = getattr(args, key)  # explicit CLI wins
    return result


def validate_config(cfg: Dict[str, Any]) -> None:
    """Validate config values against CONFIG_CHOICES (mirrors argparse
    `choices=[...]`). Raises ValueError on a bad value so a YAML typo fails
    fast with a clear message instead of silently misbehaving."""
    for key, allowed in CONFIG_CHOICES.items():
        v = cfg.get(key)
        if v is not None and v not in allowed:
            raise ValueError(
                f"config '{key}'={v!r} is invalid; must be one of {list(allowed)}"
            )
    if not isinstance(cfg.get("inspect_top", 15), int):
        raise ValueError(
            f"config 'inspect_top' must be an integer, got {cfg.get('inspect_top')!r}"
        )
    # v4 #26: focus_areas must be a positive integer.
    fa = cfg.get("focus_areas", 5)
    if not isinstance(fa, int) or fa < 1:
        raise ValueError(
            f"config 'focus_areas' must be a positive integer, got {fa!r}"
        )
    # max_text_length must be a positive integer and cannot exceed the schema
    # ceiling (the Pydantic field's max_length is the hard contract — a user
    # value above it would pass the preprocessor's truncation but then fail
    # schema validation, so clamp here with a clear error).
    mtl = cfg.get("max_text_length", _SCHEMA_MAX_TEXT_LENGTH)
    if not isinstance(mtl, int) or mtl < 1:
        raise ValueError(
            f"config 'max_text_length' must be a positive integer, got {mtl!r}"
        )
    if mtl > _SCHEMA_MAX_TEXT_LENGTH:
        raise ValueError(
            f"config 'max_text_length'={mtl} exceeds the schema ceiling "
            f"({_SCHEMA_MAX_TEXT_LENGTH}); use a value <= {_SCHEMA_MAX_TEXT_LENGTH}"
        )
    # v4 #26: validate optional briefing weights/business_keywords shape.
    br = cfg.get("briefing")
    if br is not None:
        if not isinstance(br, dict):
            raise ValueError("config 'briefing' must be a mapping")
        for wkey in ("readiness_weights", "focus_weights"):
            w = br.get(wkey)
            if w is None:
                continue
            if not isinstance(w, dict):
                raise ValueError(f"config 'briefing.{wkey}' must be a mapping")
            from .analyst_briefing import READINESS_WEIGHTS as _RW, FOCUS_WEIGHTS as _FW
            ref = _RW if wkey == "readiness_weights" else _FW
            if set(w.keys()) != set(ref.keys()):
                raise ValueError(
                    f"config 'briefing.{wkey}' keys must be {sorted(ref.keys())}; "
                    f"got {sorted(w.keys())}"
                )
            tot = sum(w.values())
            if not (0.999 <= tot <= 1.001):
                raise ValueError(
                    f"config 'briefing.{wkey}' weights must sum to 1.0; got {tot}"
                )
        bk = br.get("business_keywords")
        if bk is not None and not isinstance(bk, list):
            raise ValueError("config 'briefing.business_keywords' must be a list")
    # v4: semantic_type_keywords — extra plain substrings that reclassify
    # matching evidence to "Risk" (extends the built-in risk-language set).
    stk = cfg.get("semantic_type_keywords", [])
    if stk is None:
        stk = []
        cfg["semantic_type_keywords"] = stk
    if not isinstance(stk, list):
        raise ValueError(
            f"config 'semantic_type_keywords' must be a list, got {type(stk).__name__}"
        )
    for kw in stk:
        if not isinstance(kw, str):
            raise ValueError(
                f"config 'semantic_type_keywords' entries must be strings, got {kw!r}"
            )
