"""Minimal inline rich-text spans for handoff bullet/copy text (#77/F7).

Semi-trusted handoff: the renderer escapes everything by default (see
strip.esc). This module adds a *selective* bold span via markdown-style
``**bold**`` — the only inline construct honored in MVP. Unsafe markup is
always escaped (fail closed); no arbitrary HTML passes through.
"""
from __future__ import annotations

import re
from typing import Any

from .strip import esc, strip_eids

_BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)


def rich_text(text: Any) -> str:
    """Escape text, then restore ``**bold**`` spans as ``<strong>``.

    Everything else (tags, scripts) stays escaped. ``**`` markers are
    consumed; unbalanced markers are left as escaped literal text.
    """
    if text is None:
        return ""
    s = strip_eids(text)
    # Split on **bold** so we escape plain and bold segments separately,
    # never allowing a tag to survive inside the bold content either.
    parts: list[str] = []
    pos = 0
    for m in _BOLD.finditer(s):
        parts.append(esc(s[pos : m.start()]))
        parts.append(f"<strong>{esc(m.group(1))}</strong>")
        pos = m.end()
    parts.append(esc(s[pos:]))
    return "".join(parts)


def rich_bullets(bullets: Any, cap: int = 8) -> list[str]:
    """Normalize a bullet list to rich-text HTML strings (capped)."""
    out: list[str] = []
    for b in bullets or []:
        if not isinstance(b, str):
            b = str(b)
        if not b.strip():
            continue
        out.append(rich_text(b))
        if len(out) >= cap:
            break
    return out
