"""Native-first progressive disclosure (P5).

Expands additive handoff declarations into Boardroom-styled HTML/CSS-only
patterns — no Alpine, no Swiper, no new JS library.

Spec: wiki/SPEC_renderer_v2_p5_native_disclosure.md

Handoff shapes (additive; any one may be used):

  slide["disclosure"] = {
    "pattern": "detail" | "accordion" | "tabs",
    "panels": [{"title": str, "body": str | list[str]}, ...],
    "default_index": int,   # optional; tabs default panel / details open hint
  }

  # or nested under content / visual_spec:
  content.disclosure / visual_spec.disclosure
"""
from __future__ import annotations

import uuid
from typing import Any, Mapping, Sequence

from .strip import esc

KNOWN_PATTERNS = frozenset({"detail", "accordion", "tabs"})


class DisclosureError(ValueError):
    """Unknown or invalid disclosure declaration."""


def _as_text(body: Any) -> str:
    if body is None:
        return ""
    if isinstance(body, str):
        return body
    if isinstance(body, Sequence) and not isinstance(body, (bytes, bytearray)):
        parts = [str(x).strip() for x in body if str(x).strip()]
        return "\n".join(parts)
    return str(body)


def _panels(raw: Mapping[str, Any]) -> list[tuple[str, str]]:
    panels = raw.get("panels") or raw.get("items") or []
    if not isinstance(panels, list):
        return []
    out: list[tuple[str, str]] = []
    for p in panels:
        if isinstance(p, str):
            out.append(("Details", p))
            continue
        if not isinstance(p, Mapping):
            continue
        title = str(p.get("title") or p.get("label") or p.get("summary") or "Details")
        body = _as_text(p.get("body") or p.get("content") or p.get("text") or "")
        out.append((title, body))
    return out


def extract_disclosure(slide: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return the disclosure declaration dict, or None if absent."""
    for bag in (
        slide.get("disclosure"),
        (slide.get("content") or {}).get("disclosure")
        if isinstance(slide.get("content"), Mapping)
        else None,
        (slide.get("visual_spec") or {}).get("disclosure")
        if isinstance(slide.get("visual_spec"), Mapping)
        else None,
    ):
        if isinstance(bag, Mapping) and bag:
            return dict(bag)
    return None


def build_disclosure_html(slide: Mapping[str, Any]) -> str:
    """Expand slide disclosure declaration to HTML, or '' if none.

    Raises DisclosureError on unknown pattern when disclosure is declared.
    """
    raw = extract_disclosure(slide)
    if raw is None:
        return ""

    pattern = str(raw.get("pattern") or raw.get("type") or "").lower().strip()
    if not pattern:
        raise DisclosureError("disclosure declaration missing pattern/type")
    if pattern not in KNOWN_PATTERNS:
        raise DisclosureError(
            f"unknown disclosure pattern {pattern!r} "
            f"(known: {', '.join(sorted(KNOWN_PATTERNS))})"
        )

    panels = _panels(raw)
    if not panels:
        # Allow title+body shorthand for detail
        title = str(raw.get("title") or raw.get("summary") or "Details")
        body = _as_text(raw.get("body") or raw.get("content") or "")
        if body:
            panels = [(title, body)]
    if not panels:
        return ""

    default_index = int(raw.get("default_index") or raw.get("defaultOpen") or 0)
    if default_index < 0:
        default_index = 0

    if pattern == "detail":
        return _render_detail(panels[0], open_first=(default_index == 0 and bool(raw.get("default_open", False))))
    if pattern == "accordion":
        return _render_accordion(panels, default_index=default_index if raw.get("default_open") else -1)
    return _render_tabs(panels, default_index=default_index)


def _body_html(text: str) -> str:
    parts = [p.strip() for p in text.split("\n") if p.strip()]
    if not parts:
        return ""
    if len(parts) == 1:
        return f"<p>{esc(parts[0])}</p>"
    lis = "".join(f"<li>{esc(p)}</li>" for p in parts)
    return f"<ul>{lis}</ul>"


def _render_detail(panel: tuple[str, str], *, open_first: bool) -> str:
    title, body = panel
    open_attr = " open" if open_first else ""
    return (
        f'<div class="gl-disclosure gl-disclosure-detail" data-disclosure="detail">'
        f"<details{open_attr}>"
        f"<summary>{esc(title)}</summary>"
        f'<div class="gl-disclosure-body">{_body_html(body)}</div>'
        f"</details></div>"
    )


def _render_accordion(panels: list[tuple[str, str]], *, default_index: int) -> str:
    parts = [
        '<div class="gl-disclosure gl-disclosure-accordion" data-disclosure="accordion">'
    ]
    for i, (title, body) in enumerate(panels):
        open_attr = " open" if i == default_index else ""
        parts.append(
            f"<details{open_attr}>"
            f"<summary>{esc(title)}</summary>"
            f'<div class="gl-disclosure-body">{_body_html(body)}</div>'
            f"</details>"
        )
    parts.append("</div>")
    return "".join(parts)


def _render_tabs(panels: list[tuple[str, str]], *, default_index: int) -> str:
    if default_index >= len(panels):
        default_index = 0
    # Radio-group CSS tabs — no JS. Unique name per instance (stable within doc).
    uid = uuid.uuid4().hex[:10]
    name = f"gl-tabs-{uid}"
    parts = [
        f'<div class="gl-disclosure gl-disclosure-tabs" data-disclosure="tabs" data-tabs-id="{uid}">'
    ]
    # radios first (CSS sibling selectors)
    for i, (title, _body) in enumerate(panels):
        checked = " checked" if i == default_index else ""
        parts.append(
            f'<input class="gl-tab-input" type="radio" name="{name}" '
            f'id="{name}-{i}"{checked}/>'
        )
    parts.append('<div class="gl-tab-list" role="tablist">')
    for i, (title, _body) in enumerate(panels):
        parts.append(
            f'<label class="gl-tab" role="tab" for="{name}-{i}">{esc(title)}</label>'
        )
    parts.append("</div>")
    parts.append('<div class="gl-tab-panels">')
    for i, (_title, body) in enumerate(panels):
        parts.append(
            f'<div class="gl-tab-panel" data-tab-index="{i}" role="tabpanel">'
            f"{_body_html(body)}</div>"
        )
    parts.append("</div></div>")
    return "".join(parts)


def inject_disclosure(
    html: str,
    slide: Mapping[str, Any],
    *,
    prebuilt: str | None = None,
) -> str:
    """Insert disclosure markup into a painted slide HTML fragment.

    Pass ``prebuilt`` when the block was already validated/built upstream
    so we don't double-render pure HTML.
    """
    block = prebuilt if prebuilt is not None else build_disclosure_html(slide)
    if not block:
        return html
    needle = '<div class="gl-footer">'
    if needle in html:
        return html.replace(needle, f"{block}{needle}", 1)
    # Cover / atypical shells: append before closing section
    close = "</section>"
    if close in html:
        return html.replace(close, f"{block}{close}", 1)
    return html + block
