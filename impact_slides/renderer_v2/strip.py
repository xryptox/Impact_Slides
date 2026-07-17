"""Text cleaning: E#### scrub, dek merge, quote body cleanup."""
from __future__ import annotations

import re
from typing import Any, Mapping

_EID_PARENS = re.compile(
    r"\s*\(\s*E\d{4}(?:\s*,\s*E\d{4})*\s*\)",
    re.IGNORECASE,
)
_EID_BARE = re.compile(r"\bE\d{4}\b", re.IGNORECASE)
_WS = re.compile(r"\s+")

_QUOTE_SPAN = re.compile(
    r"[\"\u201c](.+?)[\"\u201d]",
    re.DOTALL,
)
_SAID_TAIL = re.compile(
    r",?\s*said\s+[A-Z][a-zA-Z.\-']+(?:\s+[A-Z][a-zA-Z.\-']+)*.*$",
)
_SAID_NAME = re.compile(
    r"said\s+([A-Z][a-zA-Z.\-']+(?:\s+[A-Z][a-zA-Z.\-']+){0,3})"
    r"(?:\s*,\s*([^\"\u201d\n]{3,80}))?",
)


def esc(text: Any) -> str:
    if text is None:
        return ""
    s = str(text)
    return (
        s.replace("&", "&"+"amp;")
        .replace("<", "&"+"lt;")
        .replace(">", "&"+"gt;")
        .replace('"', "&"+"quot;")
    )


def strip_eids(text: Any) -> str:
    if text is None:
        return ""
    s = str(text)
    s = _EID_PARENS.sub("", s)
    s = _EID_BARE.sub("", s)
    return _WS.sub(" ", s).strip(" ,;|-")


def scrub_tree(obj: Any, *, _key: str | None = None) -> Any:
    """Recursively scrub E#### from face-facing strings.

    Preserves ids under evidence_* keys and pure E#### tokens so the
    manifest can still cite them (they never paint on face).
    """
    if isinstance(obj, str):
        if _key in ("id", "evidence_id", "evidence_ids", "source") or re.fullmatch(
            r"E\d{4}", obj, re.I
        ):
            return obj
        return strip_eids(obj)
    if isinstance(obj, list):
        return [scrub_tree(x, _key=_key) for x in obj]
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            # do not strip inside evidence_sources id fields
            if k in ("evidence_sources", "evidence_ids"):
                out[k] = scrub_tree(v, _key=k)
            else:
                out[k] = scrub_tree(v, _key=k if k in ("id", "evidence_id", "source") else _key)
        return out
    return obj


def near_dup(a: str, b: str) -> bool:
    aa, bb = a.strip().lower(), b.strip().lower()
    if not aa or not bb:
        return False
    if aa == bb:
        return True
    if aa in bb or bb in aa:
        return True
    return False


def chosen_dek(slide: Mapping[str, Any]) -> str:
    """One under-title line: prefer subtitle, drop headline near-dup / KPI noise."""
    content = slide.get("content") or {}
    sub = strip_eids(content.get("subtitle") or slide.get("subtitle") or "")
    head = strip_eids(content.get("headline") or "")
    if sub and head:
        if near_dup(sub, head):
            return sub if len(sub) >= len(head) else head
        # Prefer framing subtitle when head looks like a number dump
        if re.search(r"[$€£%]|\d{2,}", head) and not re.search(r"[$€£%]|\d{3,}", sub):
            return sub
        return sub
    return sub or head


def clean_quote_body(text: Any) -> str:
    """First spoken line only; strip trailing ', said Name, Role'."""
    raw = strip_eids(text)
    if not raw:
        return ""
    m = _QUOTE_SPAN.search(raw)
    body = m.group(1).strip() if m else raw.strip().strip("\"\u201c\u201d")
    body = _SAID_TAIL.sub("", body).strip(" ,")
    # Prefer first sentence if multiple
    if ". " in body and len(body) > 200:
        body = body.split(". ", 1)[0].strip() + "."
    return body


def parse_cite_from_quote(text: Any, attribution: Any = None) -> str:
    attr = strip_eids(attribution or "")
    if attr and not re.fullmatch(r"E\d{4}", attr, re.I) and len(attr) > 2:
        return attr.replace(" - ", " — ").replace(" – ", " — ")
    raw = str(text or "")
    m = _SAID_NAME.search(raw)
    if m:
        name = m.group(1).strip()
        role = (m.group(2) or "").strip(" .")
        return f"{name} — {role}" if role else name
    return ""


def banned_face_opener(text: str) -> bool:
    t = (text or "").lstrip()
    bans = (
        "This means",
        "The implication is",
        "That puts",
        "To put a fine point",
        "In other words",
        "This sets up",
        "Key takeaway",
        "Bottom line",
    )
    return any(t.startswith(b) for b in bans)
