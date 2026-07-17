"""Named-area slot helpers built from gl-* primitives."""
from __future__ import annotations

from ..strip import esc


def gl_card(hat: str, body_html: str, extra_class: str = "") -> str:
    cls = "gl-card card" + (f" {extra_class}" if extra_class else "")
    hat_html = f'<h3 class="gl-card-hat">{esc(hat)}</h3>' if hat else ""
    return f'<div class="{cls}">{hat_html}<div class="gl-card-body">{body_html}</div></div>'


def slide_shell(
    *,
    number: int,
    total: int,
    title: str,
    dek: str,
    main_html: str,
    notes_html: str,
    footer_html: str = "",
    layout_class: str = "",
    active: bool = False,
    cover: bool = False,
    item_count: int | None = None,
) -> str:
    """Common content-slide chrome.

    item_count: multi-item carrier size (quotes, KPI cards, process steps,
    comparison cards, proof lines). When >= 3 the section receives
    ``data-items`` + class ``gl-density-hero`` so CSS can claim mid-canvas
    min-height without flex-stretching 1–2 item sparse lists.
    """
    act = " active" if active else ""
    if cover:
        return (
            f'<section class="slide title-slide{act}" data-slide-number="{number}" '
            f'data-layout="title_or_opening">'
            f'<div class="slide-number">{number:02d} / {total:02d}</div>'
            f"{main_html}"
            f"{notes_html}"
            f"</section>"
        )
    dek_html = f'<p class="subtitle dek gl-dek">{esc(dek)}</p>' if dek else ""
    footer = f'<div class="gl-footer">{footer_html}</div>' if footer_html else '<div class="gl-footer"></div>'
    n_items = int(item_count) if item_count is not None else 0
    items_attr = f' data-items="{n_items}"' if item_count is not None else ""
    hero = " gl-density-hero" if n_items >= 3 else ""
    dens = f" gl-items-{min(n_items, 6)}" if n_items else ""
    return (
        f'<section class="slide{act}{hero}{dens}" data-slide-number="{number}" '
        f'data-layout="{esc(layout_class)}"{items_attr}>'
        f'<div class="slide-number">{number:02d} / {total:02d}</div>'
        f'<div class="gl-slide layout-{esc(layout_class)}">'
        f'<header class="gl-header slide-header">'
        f'<h2 class="slide-title">{esc(title)}</h2>'
        f"{dek_html}"
        f"</header>"
        f'<div class="gl-main">{main_html}</div>'
        f"{footer}"
        f"</div>"
        f"{notes_html}"
        f"</section>"
    )


def notes_aside(number: int, prose: str) -> str:
    return (
        f'<aside class="speaker-notes" data-slide-number="{number}">'
        f'<h2 class="visually-hidden">Slide {number} speaker notes</h2>'
        f"<p>{esc(prose)}</p>"
        f"</aside>"
    )


def insight_strip(text: str) -> str:
    if not text:
        return ""
    return f'<div class="insight-strip so-what-callout"><span>{esc(text)}</span></div>'


def source_strip(names: list[str]) -> str:
    clean = [n for n in names if n]
    if not clean:
        return ""
    return f'<div class="source-strip">{esc(" · ".join(clean[:4]))}</div>'
