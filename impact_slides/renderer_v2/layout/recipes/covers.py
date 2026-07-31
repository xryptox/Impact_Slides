"""Title, brand cover, section divider, quote recipes."""
from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from ...slide_view import content as _sv_content
from ...slide_view import steps as _sv_steps
from ...strip import (
    banned_face_opener,
    chosen_dek,
    clean_quote_body,
    esc,
    parse_cite_from_quote,
    strip_eids,
)
from ..regions import gl_card, insight_strip, notes_aside, slide_shell, source_strip

from .shared import _content, _so_what, _source_names, _vs_steps



# ================== RECIPES ==================

def render_title(slide, total, notes, active=False):
    pres_goal = strip_eids(_content(slide).get("headline") or "")
    dek = chosen_dek(slide) or pres_goal
    title = strip_eids(slide.get("title") or "Presentation")
    kicker = strip_eids(slide.get("section") or "")
    kicker_html = ""
    if kicker and kicker.lower() not in ("why", "what", "how", "now"):
        kicker_html = f'<div class="kicker">{esc(kicker)}</div>'
    dek_html = f'<p class="headline">{esc(dek)}</p>' if dek else ""
    main = (
        '<div class="gl-areas-cover cover-inner">'
        '<div class="gl-band-navy">'
        '<div class="title-stack">'
        f"{kicker_html}"
        f"<h1>{esc(title)}</h1>"
        f"{dek_html}"
        "</div></div>"
        '<div class="gl-band-blue"><div class="title-footer">'
        '<span class="cover-date">Boardroom Earnings</span></div></div>'
        "</div>"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=title,
        dek="",
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        layout_class="title_or_opening",
        active=active,
        cover=True,
    )



def render_brand_cover(slide, total, notes, active=False, *, divider: bool = False):
    """Full-bleed two-tone brand cover / divider with an inlined brand-mark
    lockup (#76/F6). Brand-parameterizable via content.brand_mark_svg (an
    inline SVG string, data-URL'd so self-contained decks need no fetch) and
    content.brand_tone. Generic — not Amex-hardcoded.
    """
    import base64

    from ...brand import load_brand_mark

    c = slide.get("content") or {}
    mark_name = strip_eids(c.get("brand_mark") or "")
    mark_svg = c.get("brand_mark_svg")
    subtitle = strip_eids(c.get("subtitle") or "")
    tone = strip_eids(c.get("brand_tone") or "two-tone")
    mark_html = ""
    if mark_name:
        # Named vendored seal/lockup (#93/R3): inline SVG, currentColor-toned.
        # Unknown names fail closed inside load_brand_mark.
        named = load_brand_mark(mark_name)
        mark_html = (
            f'<span class="gl-brand-mark gl-brand-mark-named" '
            f'data-mark="{esc(mark_name)}">{named}</span>'
        )
    elif isinstance(mark_svg, str) and mark_svg.strip().startswith("<svg"):
        # Inline as a data URL so the deck stays self-contained (no remote fetch).
        b64 = base64.b64encode(mark_svg.encode("utf-8")).decode("ascii")
        mark_html = (
            f'<img class="gl-brand-mark" alt="brand mark" '
            f'src="data:image/svg+xml;base64,{b64}"/>'
        )
    role = "divider" if divider else "cover"
    layout = "brand_divider" if divider else "brand_cover"
    title = strip_eids(slide.get("title") or "")
    sub_html = f'<div class="gl-brand-sub">{esc(subtitle)}</div>' if subtitle else ""
    main = (
        f'<div class="gl-brand gl-brand-{role} gl-brand-two-tone" data-tone="{esc(tone)}">'
        f"{mark_html}"
        f'<div class="gl-brand-title">{esc(title)}</div>'
        f"{sub_html}"
        f"</div>"
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=title,
        dek="",
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html="",
        layout_class=layout,
        active=active,
        item_count=1,
    )



def render_section_divider(slide, total, notes, active=False):
    """Low-density section break with message and accent line."""
    c = _content(slide)
    message = strip_eids(c.get("headline") or c.get("body_text") or slide.get("title") or "")
    subtitle = strip_eids(c.get("subtitle") or "")
    sub_html = f'<p class="section-subtitle">{esc(subtitle)}</p>' if subtitle else ""
    main = (
        f'<div class="layout-section-divider">'
        f'<div class="accent-line"></div>'
        f'<h2 class="section-message">{esc(message)}</h2>'
        f'{sub_html}'
        f'</div>'
    )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek="",  # subtitle already rendered in the centered divider body
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        footer_html=source_strip(_source_names(slide)),
        layout_class="section_divider",
        active=active,
        item_count=1,
    )



def render_quote(slide, total, notes, active=False):
    steps = _vs_steps(slide)
    quotes = []
    for st in steps:
        if isinstance(st, dict):
            text = st.get("text") or st.get("quote") or st.get("body") or ""
            attr = st.get("attribution") or st.get("cite") or ""
            body = clean_quote_body(text)
            cite = parse_cite_from_quote(text, attr)
            if body:
                quotes.append((body, cite))
        elif isinstance(st, str):
            body = clean_quote_body(st)
            cite = parse_cite_from_quote(st)
            if body:
                quotes.append((body, cite))
    if not quotes:
        body = clean_quote_body(_content(slide).get("body_text") or _content(slide).get("headline") or "")
        if body:
            quotes.append((body, ""))

    sow = _so_what(slide)
    n = len(quotes)
    if n >= 2:
        cards = []
        for body, cite in quotes[:3]:
            cite_html = f"<cite>{esc(cite)}</cite>" if cite else ""
            cards.append(
                f'<article class="quote-card card">'
                f"<blockquote>{esc(body)}</blockquote>{cite_html}</article>"
            )
        main = f'<div class="gl-areas-quote-stack quote-layout--stack">{"".join(cards)}</div>'
    else:
        body, cite = quotes[0] if quotes else ("", "")
        cite_html = f"<cite>{esc(cite)}</cite>" if cite else ""
        insight = f'<div class="quote-insight">{esc(sow)}</div>' if sow else ""
        main = (
            f'<div class="quote-layout--single">'
            f'<article class="quote-card card"><blockquote>{esc(body)}</blockquote>{cite_html}</article>'
            f"{insight}"
            f"</div>"
        )
    return slide_shell(
        number=int(slide["slide_number"]),
        total=total,
        title=strip_eids(slide.get("title") or ""),
        dek=chosen_dek(slide),
        main_html=main,
        notes_html=notes_aside(int(slide["slide_number"]), notes),
        layout_class="quote_card",
        active=active,
        item_count=n,
    )
