"""Generate the committed boardroom_amex CSS artifact from the theme manifest (D129)."""
from __future__ import annotations

from pathlib import Path

from .theme import THEME_ID, generate_theme_css

THEME_RELATIVE_PATH = Path(
    f"impact_slides/renderer_v3/theme/{THEME_ID}.tokens.css"
)


def theme_css() -> str:
    return generate_theme_css()


def theme_css_path(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else _default_repo_root()
    return root / THEME_RELATIVE_PATH


def write_theme(repo_root: Path | None = None) -> Path:
    path = theme_css_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(theme_css(), encoding="utf-8", newline="\n")
    return path


def check_theme(repo_root: Path | None = None) -> None:
    """Raise SystemExit if the committed CSS artifact drifts from the manifest."""
    path = theme_css_path(repo_root)
    expected = theme_css()
    if not path.is_file():
        raise SystemExit(f"missing theme CSS artifact: {path}")
    actual = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if actual != expected:
        raise SystemExit(
            f"theme CSS drift: {path} does not match theme manifest. "
            "Run: python -m impact_slides.renderer_v3.theme_export"
        )


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description=f"Generate or check {THEME_ID} theme CSS"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if committed theme CSS drifts from the manifest",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="repository root (defaults to auto-detect)",
    )
    args = parser.parse_args(argv)
    if args.check:
        check_theme(args.root)
        print("theme css ok")
        return 0
    path = write_theme(args.root)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
