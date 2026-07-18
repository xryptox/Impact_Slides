"""Centralized inliner for vendored third-party assets (P0 foundation).

Single owner (SC-MOD-1) for how renderer_v2 embeds external CSS/JS/fonts into
generated decks. First-party Boardroom CSS lives in ``css/`` and stays separate.

Spec: wiki/SPEC_renderer_v2_p0_self_contained.md
"""
from __future__ import annotations

import base64
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable

_PKG_DIR = Path(__file__).resolve().parent
ASSETS_DIR = _PKG_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
LIBS_DIR = ASSETS_DIR / "libs"

GOOGLE_FONTS_CDN_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Source+Sans+3:wght@400;600;700"
    "&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap"
)

# Reserved feature ids for P1+ (no behavior in P0).
KNOWN_FEATURES = frozenset({"charts", "mermaid", "alpine", "swiper", "icons"})


class DeliveryMode(str, Enum):
    """How required third-party assets reach the generated deck."""

    SELF_CONTAINED = "self-contained"
    CDN = "cdn"


def coerce_delivery(value: "DeliveryMode | str | None") -> DeliveryMode:
    """Normalize a delivery value, rejecting anything unknown."""
    if value is None:
        return DeliveryMode.SELF_CONTAINED
    if isinstance(value, DeliveryMode):
        return value
    try:
        return DeliveryMode(str(value))
    except ValueError:
        raise ValueError(
            f"invalid delivery {value!r}: expected "
            f"'{DeliveryMode.SELF_CONTAINED.value}' or '{DeliveryMode.CDN.value}'"
        ) from None


@dataclass(frozen=True)
class AssetRef:
    """One third-party asset the deck may need."""

    asset_id: str          # e.g. "font-boardroom", "charts" (P3)
    kind: str              # "font" | "css" | "js"
    path: Path | None      # vendored file path (None until vendored)
    cdn_url: str | None    # used only in CDN mode
    license_path: Path | None = None


@dataclass(frozen=True)
class FontFace:
    """One vendored @font-face source."""

    family: str            # e.g. "Source Sans 3"
    weight: int            # e.g. 400
    style: str             # "normal" | "italic"
    filename: str          # file under assets/fonts/


# Vendored Boardroom faces (populated when WOFF2 files are committed — P0.3).
FONT_MANIFEST: tuple[FontFace, ...] = ()


@dataclass(frozen=True)
class InlineBundle:
    """Head fragments + metadata for one render."""

    head_html: str
    meta: dict = field(default_factory=dict)


def iter_core_assets() -> list[AssetRef]:
    """Assets required for every deck (fonts; always-on CSS libs later)."""
    return [
        AssetRef(
            asset_id="font-boardroom",
            kind="font",
            path=None,  # individual faces live in FONT_MANIFEST / assets/fonts/
            cdn_url=GOOGLE_FONTS_CDN_URL,
        ),
    ]


def _cdn_head(assets: Iterable[AssetRef]) -> str:
    tags = []
    for asset in assets:
        if not asset.cdn_url:
            continue
        if asset.kind in {"font", "css"}:
            tags.append(f'<link href="{asset.cdn_url}" rel="stylesheet">')
        elif asset.kind == "js":
            tags.append(f'<script src="{asset.cdn_url}"></script>')
    return "\n".join(tags)


def _font_face_css(face: FontFace, path: Path) -> tuple[str, int]:
    if not path.exists():
        raise FileNotFoundError(
            f"self-contained delivery requires vendored font {path.name} "
            f"({face.family} {face.weight}). Vendor fonts under "
            f"assets/fonts/ or use --use-cdn for development."
        )
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    css = (
        "@font-face {\n"
        f"  font-family: \"{face.family}\";\n"
        f"  font-style: {face.style};\n"
        f"  font-weight: {face.weight};\n"
        "  font-display: swap;\n"
        f"  src: url(data:font/woff2;base64,{b64}) format(\"woff2\");\n"
        "}"
    )
    return css, len(raw)


def _self_contained_head() -> tuple[str, int, list[str]]:
    faces: list[str] = []
    total = 0
    for face in FONT_MANIFEST:
        css, size = _font_face_css(face, FONTS_DIR / face.filename)
        faces.append(css)
        total += size
    if not faces:
        return "", 0, []
    head = "<style>\n" + "\n".join(faces) + "\n</style>"
    return head, total, ["font-boardroom"]


def build_head_assets(
    mode: DeliveryMode | str,
    *,
    feature_ids: Iterable[str] = (),
) -> InlineBundle:
    """Build <head> asset fragments for a delivery mode.

    P0: core assets only (fonts). ``feature_ids`` is the P1 seam: reserved ids
    (charts/mermaid/alpine/swiper/icons) are accepted but inert; anything else
    warns on stderr and is ignored.
    """
    mode = coerce_delivery(mode)
    unknown = [f for f in feature_ids if f not in KNOWN_FEATURES]
    for fid in unknown:
        print(f"[lib_inliner] unknown feature id ignored: {fid}", file=sys.stderr)

    if mode is DeliveryMode.CDN:
        head = _cdn_head(iter_core_assets())
        return InlineBundle(
            head_html=head,
            meta={"mode": mode.value, "assets": [], "bytes_inlined": 0},
        )

    head, total, inlined = _self_contained_head()
    return InlineBundle(
        head_html=head,
        meta={"mode": mode.value, "assets": inlined, "bytes_inlined": total},
    )
