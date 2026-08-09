"""Generate the published JSON Schema artifact from typed models (D121)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Deck

SCHEMA_RELATIVE_PATH = Path("impact_slides/renderer_v3/schema/handoff_schema_v1.json")


def generate_schema() -> dict[str, Any]:
    """Return the JSON Schema object derived from the Deck model."""
    schema = Deck.model_json_schema(mode="validation")
    # Stable top-level metadata for consumers / migrator.
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://xryptox.github.io/Impact_Slides/renderer_v3/handoff_schema_v1.json",
        "title": "Impact Slides renderer v3 handoff schema v1",
        "description": (
            "Generated from impact_slides.renderer_v3.models.Deck. "
            "Do not edit by hand; regenerate via "
            "`python -m impact_slides.renderer_v3.schema_export`."
        ),
        **schema,
    }
    return schema


def schema_json(*, indent: int = 2) -> str:
    return json.dumps(generate_schema(), indent=indent, ensure_ascii=False) + "\n"


def schema_path(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else _default_repo_root()
    return root / SCHEMA_RELATIVE_PATH


def write_schema(repo_root: Path | None = None) -> Path:
    path = schema_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(schema_json(), encoding="utf-8", newline="\n")
    return path


def check_schema(repo_root: Path | None = None) -> None:
    """Raise SystemExit if the committed artifact drifts from the models."""
    path = schema_path(repo_root)
    expected = schema_json()
    if not path.is_file():
        raise SystemExit(f"missing schema artifact: {path}")
    # Compare LF form so Windows CRLF checkouts still match the D121 blob.
    actual = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if actual != expected:
        raise SystemExit(
            f"schema drift: {path} does not match models. "
            "Run: python -m impact_slides.renderer_v3.schema_export"
        )


def _default_repo_root() -> Path:
    # impact_slides/renderer_v3/schema_export.py → repo root is parents[2]
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate or check handoff schema v1")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if committed schema drifts from models",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="repository root (defaults to auto-detect)",
    )
    args = parser.parse_args(argv)
    if args.check:
        check_schema(args.root)
        print("schema ok")
        return 0
    path = write_schema(args.root)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
