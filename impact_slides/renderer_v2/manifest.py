"""evidence_manifest.json + slide_notes.md writers + run validation."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from .lib_inliner import DeliveryMode, coerce_delivery

_FACE_EID = re.compile(r"\bE\d{4}\b")

# Network-fetching URL constructs (SC-OFFLINE-2). Non-fetching URL-like strings
# such as SVG/XML namespaces and data: URLs must not match.
_REMOTE_FETCH_PATTERNS = (
    re.compile(r'<link\b[^>]*?\bhref\s*=\s*["\'](https?://[^"\']+|//[^"\']+)["\']', re.I),
    re.compile(r'<script\b[^>]*?\bsrc\s*=\s*["\'](https?://[^"\']+|//[^"\']+)["\']', re.I),
    # Media hosts that would fetch when painted (P0 review amendment).
    re.compile(
        r'<(?:img|iframe|video|audio|source|track|embed)\b[^>]*?\bsrc\s*=\s*["\']'
        r'(https?://[^"\']+|//[^"\']+)["\']',
        re.I,
    ),
    re.compile(
        r'<(?:img|source)\b[^>]*?\bsrcset\s*=\s*["\']([^"\']+)["\']',
        re.I,
    ),
    re.compile(r'@import\s+(?:url\(\s*)?["\']?(https?://[^\s"\')>]+|//[^\s"\')>]+)', re.I),
    re.compile(r'url\(\s*["\']?(https?://[^\s"\')]+|//[^\s"\')]+)\s*["\']?\)', re.I),
)
_SRCSET_REMOTE = re.compile(r'(https?://\S+|//\S+)')


def remote_fetch_urls(html: str) -> list[str]:
    """URLs the browser would fetch over the network to render this HTML.

    Covers link/script, media tags (img/iframe/video/audio/source/track/embed),
    srcset candidates, @import, and CSS url(). Ignores XML namespaces and
    ``data:`` URLs.
    """
    found: set[str] = set()
    for pattern in _REMOTE_FETCH_PATTERNS:
        for match in pattern.findall(html):
            # srcset yields the full attribute value — split candidates.
            if "," in match or " " in match:
                for cand in _SRCSET_REMOTE.findall(match):
                    found.add(cand.rstrip(","))
            else:
                found.add(match)
    return sorted(found)


def build_manifest(
    handoff: Mapping[str, Any],
    slides: Sequence[Mapping[str, Any]],
    *,
    source_name: str = "builder_handoff.json",
) -> dict[str, Any]:
    pres = handoff.get("presentation") or {}
    out_slides = []
    for s in slides:
        eids = []
        # evidence_sources may be list of ids or objects
        for item in s.get("evidence_sources") or []:
            if isinstance(item, str) and re.fullmatch(r"E\d{4}", item, re.I):
                eids.append(item.upper())
            elif isinstance(item, dict):
                eid = item.get("id") or item.get("evidence_id") or ""
                if re.fullmatch(r"E\d{4}", str(eid), re.I):
                    eids.append(str(eid).upper())
        out_slides.append(
            {
                "slide_number": s.get("slide_number"),
                "title": s.get("title") or "",
                "section": s.get("section") or "",
                "layout_type": s.get("layout_type") or "",
                "evidence_ids": eids,
                "synthesized": bool(s.get("synthesized", False)),
                "confidence": s.get("confidence") or "medium",
            }
        )
    return {
        "source_handoff": source_name,
        "style_preset": "BoardroomEarnings",
        "presentation_title": pres.get("title") or "",
        "total_slides": len(slides),
        "readiness_score": pres.get("readiness_score"),
        "quality_flags": pres.get("quality_flags") or [],
        "slides": out_slides,
    }


def write_slide_notes_md(
    path: Path,
    slides: Sequence[Mapping[str, Any]],
    notes_by_num: Mapping[int, str],
) -> None:
    lines: list[str] = ["# Slide Notes", ""]
    for s in slides:
        n = int(s.get("slide_number") or 0)
        title = s.get("title") or f"Slide {n}"
        lines.append(f"## Slide {n} — {title}")
        lines.append("")
        prose = (notes_by_num.get(n) or "").strip()
        lines.append(prose or "_(no notes)_")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def face_eid_violations(html: str) -> list[str]:
    """Find E#### outside speaker-notes asides and scripts."""
    # Drop asides
    cleaned = re.sub(
        r"<aside class=\"speaker-notes\"[\s\S]*?</aside>",
        "",
        html,
        flags=re.I,
    )
    cleaned = re.sub(r"<script[\s\S]*?</script>", "", cleaned, flags=re.I)
    cleaned = re.sub(r"<svg class=\"svg-sprite\"[\s\S]*?</svg>", "", cleaned, flags=re.I)
    return sorted(set(_FACE_EID.findall(cleaned)))


def validate_html(
    html: str,
    *,
    delivery: DeliveryMode | str = DeliveryMode.SELF_CONTAINED,
) -> list[str]:
    delivery = coerce_delivery(delivery)
    errs: list[str] = []
    html_l = html.lower()
    for token in ("#00175a", "#006fcf", "BoardroomEarnings", "gl-slide", "deck-stage"):
        if token.lower() not in html_l:
            if token == "BoardroomEarnings":
                errs.append("missing BoardroomEarnings preset marker")
            else:
                errs.append(f"missing required token/class: {token}")
    if face_eid_violations(html):
        errs.append(f"face E#### residual: {face_eid_violations(html)[:8]}")
    if 'class="narrative-bridge"' in html or 'class="story-bridge"' in html:
        # allowed only if also hidden; hard fail on emitting face rails
        if re.search(r'<div class="(?:narrative|story)-bridge"', html):
            errs.append("face narrative/story-bridge element present")
    if "fitStage" not in html:
        errs.append("missing fitStage JS")
    if delivery is DeliveryMode.SELF_CONTAINED:
        for url in remote_fetch_urls(html):
            errs.append(f"remote fetch in self-contained deck: {url}")
    return errs
