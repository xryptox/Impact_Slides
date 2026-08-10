"""Deck-wide measure/plan phase for kernel compositions (D1–D4, D22, D59, D68–D70).

Freezes whole-pixel role sizes against the fixed 1920×1080 design stage before
paint. Runtime may only consume these plans — never replan.
"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Any, Final, Optional

from .diagnostics import DiagnosticEvent, RendererValidationError, event, sort_events
from .models import Deck, Typography

from ._version import __version__ as RENDERER_VERSION

DESIGN_STAGE_W: Final = 1920
DESIGN_STAGE_H: Final = 1080
PAD_X: Final = 96
PAD_TOP: Final = 56
PAD_BOTTOM: Final = 48
CONTENT_W: Final = DESIGN_STAGE_W - 2 * PAD_X  # 1728

# Fixed chrome (D13) — never grow.
TITLE_PX: Final = 56
COVER_TITLE_PX: Final = 72
COVER_META_PX: Final = 22
TAKEAWAY_LABEL_PX: Final = 14

# Adaptive floors / ceilings (D12/D14/D51/D59/D171/D172/D225/D288).
SUBTITLE_FLOOR: Final = 22
SUBTITLE_CEIL: Final = 26
BODY_FLOOR: Final = 22
BODY_CEIL: Final = 28
TAKEAWAY_FLOOR: Final = 22
TAKEAWAY_CEIL: Final = 28

LINE_HEIGHT: Final = 1.4
# Must match publish.py / boardroom_amex theme box model.
BLOCK_MARGIN_Y: Final = 12  # p/ul margin-bottom (== --space-sm)
TITLE_MARGIN_Y: Final = 12  # h1 margin-bottom (== --space-sm)
# Takeaway chrome outside the text-fit box (label + pad + border + outer margin).
TAKEAWAY_PAD_Y: Final = 24  # --space-sm top+bottom
TAKEAWAY_BORDER_Y: Final = 2  # hairline top+bottom
TAKEAWAY_OUTER_MT: Final = 20  # --space-md
TAKEAWAY_LABEL_MB: Final = 8  # --space-xs under label
TAKEAWAY_PAD_X: Final = 40  # --space-md left+right
TAKEAWAY_BORDER_X: Final = 2  # hairline left+right
LIST_INDENT_EM: Final = 1.25
GLYPH_ADVANCE: Final = {
    "narrow": 0.35,
    "normal": 0.58,
    "wide": 0.90,
    "space": 0.28,
}
STRONG_MULTIPLIER: Final = 1.04


@dataclass
class SurfacePlan:
    """Frozen plan for one semantic surface (D312)."""

    surface_id: str
    role: str
    slide_number: int
    layout_type: str
    slot_order: int
    design_stage_region: int
    role_sizes: dict[str, int]
    adaptation_codes: list[str] = field(default_factory=list)
    reservations: list[dict[str, Any]] = field(default_factory=list)
    fallback: Optional[str] = None
    expected_placement_classes: list[str] = field(default_factory=list)
    display_identity_strategy: Optional[str] = None
    semantic_digest: str = ""
    painter_plan_digest: str = ""
    # Internal measure fields (not published).
    _text_items: list[tuple[str, bool]] = field(default_factory=list)  # (text, strong)
    _box_w: int = CONTENT_W
    _box_h: int = 0
    _fit_role: Optional[str] = None  # which role_sizes key is adaptive text
    _typo: Optional[Typography] = None
    _mode: str = "adaptive"
    _sync_group: Optional[str] = None
    _explicit_size: Optional[int] = None
    _overflow: bool = False
    _malformed_explicit: bool = False
    # Cover multi-role items: (text, role_key) measured at role_sizes[role_key].
    _cover_items: list[tuple[str, str]] = field(default_factory=list)
    # CSS block boxes that each contribute trailing margin (p/ul/h1).
    _margin_boxes: int = 1
    # Extra chrome height outside the text-fit box (takeaway panel).
    _chrome_h: int = 0
    _indent_em: float = 0
    _default_size: Optional[int] = None
    _maximum_size: Optional[int] = None

    def to_public(self) -> dict[str, Any]:
        sizes = {k: self.role_sizes[k] for k in sorted(self.role_sizes)}
        row: dict[str, Any] = {
            "surface_id": self.surface_id,
            "role": self.role,
            "slide_number": self.slide_number,
            "layout_type": self.layout_type,
            "semantic_digest": self.semantic_digest,
            "design_stage_region": self.design_stage_region,
            "available_geometry": {"width": self._box_w, "height": self._box_h},
            "role_sizes": sizes,
            "default_size": self._default_size,
            "selected_size": sizes.get(self._fit_role) if self._fit_role else None,
            "maximum_size": self._maximum_size,
            "mode": self._mode,
            "explicit_override": self._explicit_size,
            "synchronization_group": self._sync_group,
            "adaptation_codes": list(self.adaptation_codes),
            "reservations": list(self.reservations),
            "fallback": self.fallback,
            "expected_placement_classes": list(self.expected_placement_classes),
            "painter_plan_digest": self.painter_plan_digest,
        }
        if self.display_identity_strategy is not None:
            row["display_identity_strategy"] = self.display_identity_strategy
        return row


@dataclass
class DeckPlan:
    surfaces: list[SurfacePlan]
    events: list[DiagnosticEvent] = field(default_factory=list)

    def public_plans(self) -> list[dict[str, Any]]:
        return [s.to_public() for s in self.surfaces]

    def by_surface_id(self) -> dict[str, SurfacePlan]:
        return {s.surface_id: s for s in self.surfaces}


def plan_deck(deck: Deck, *, strict: bool = True) -> DeckPlan:
    """Measure every kernel surface, synchronize, freeze whole-pixel sizes (D69)."""
    surfaces = _collect_surfaces(deck)
    events: list[DiagnosticEvent] = []

    # Phase 1 — independent measure at design stage.
    for sp in surfaces:
        _measure_surface(sp, events)

    # Phase 2 — synchronize equivalent roles (D3/D4/D26/D69).
    _synchronize(surfaces, events)

    # Size-dependent events must describe the synchronized frozen sizes.
    events = [e for e in events if e.code != "plan.typography_grown"]
    for sp in surfaces:
        if "plan.typography_grown" in sp.adaptation_codes:
            fit = sp._fit_role
            assert fit is not None
            size = sp.role_sizes[fit]
            events.append(
                event(
                    code="plan.typography_grown",
                    severity="info",
                    phase="plan",
                    role=sp.role,
                    path=f"/slides/{sp.slide_number}/{sp.role}",
                    action="measure",
                    result="accepted",
                    slide_number=sp.slide_number,
                    layout_type=sp.layout_type,
                    surface_id=sp.surface_id,
                    expected=f"{fit} grew to {size}px",
                    input_meta={"type": "int", "value": size},
                )
            )

    # ponytail: synthetic AVG_ADVANCE is the interim engine (not unknown-font
    # fallback); emit plan.conservative_metrics only when a dual measured path
    # falls back (D23).

    fit_errors = [e for e in events if e.code == "validation.fit"]
    overflow = [s for s in surfaces if s._overflow]
    if strict and (overflow or fit_errors):
        raise RendererValidationError(
            sort_events(list(events) + [_overflow_event(s) for s in overflow]),
            handoff_schema_version=deck.meta.handoff_schema_version,
            renderer_version=RENDERER_VERSION,
        )
    if not strict and overflow:
        for s in overflow:
            events.append(_overflow_event(s))
            s.fallback = "fallback_unresolved"

    # Non-strict D28/D49: convert fit errors to policy-default warnings.
    if not strict and fit_errors:
        rewritten: list[DiagnosticEvent] = []
        for e in events:
            if e.code == "validation.fit":
                rewritten.append(
                    event(
                        code="repair.policy_defaulted",
                        severity="warning",
                        phase="plan",
                        role=e.role,
                        path=e.path,
                        action="default_typography",
                        result="defaulted",
                        slide_number=e.slide_number,
                        layout_type=e.layout_type,
                        surface_id=e.surface_id,
                        expected="role size within floor..ceiling",
                    )
                )
            else:
                rewritten.append(e)
        events = rewritten

    for sp in surfaces:
        _seal_digests(sp)

    return DeckPlan(surfaces=surfaces, events=sort_events(events))


# ---------------------------------------------------------------------------
# Surface collection (composition slot order)
# ---------------------------------------------------------------------------


def _collect_surfaces(deck: Deck) -> list[SurfacePlan]:
    out: list[SurfacePlan] = []
    region = 0
    for slide in deck.slides:
        lt = slide.layout_type
        sn = slide.slide_number
        if lt in ("opening_cover", "closing_cover"):
            region += 1
            p = slide.payload
            cover_items: list[tuple[str, str]] = [(p.title, "title")]
            if p.subtitle:
                cover_items.append((p.subtitle, "subtitle"))
            if p.period_label:
                cover_items.append((p.period_label, "meta"))
            if p.date_label:
                cover_items.append((p.date_label, "meta"))
            # Covers: fixed display chrome (D13/D223) — no adaptive growth.
            out.append(
                SurfacePlan(
                    surface_id=f"slide-{sn}-cover",
                    role="cover",
                    slide_number=sn,
                    layout_type=lt,
                    slot_order=0,
                    design_stage_region=region,
                    role_sizes={
                        "title": COVER_TITLE_PX,
                        "subtitle": COVER_META_PX,
                        "meta": COVER_META_PX,
                    },
                    _cover_items=cover_items,
                    _text_items=[(t, rk == "title") for t, rk in cover_items],
                    _box_w=CONTENT_W,
                    _box_h=DESIGN_STAGE_H - PAD_TOP - PAD_BOTTOM,
                    _fit_role=None,
                    _mode="fixed",
                    _margin_boxes=len(cover_items),
                )
            )
            continue

        if lt != "narrative":
            continue

        # Slot order: title chrome (fixed), subtitle, body blocks, takeaway.
        region += 1
        title_h = _required_height([(slide.title, True)], TITLE_PX, CONTENT_W, 1)
        used = title_h

        # Title is fixed chrome — recorded so painters share one plan.
        out.append(
            SurfacePlan(
                surface_id=f"slide-{sn}-title",
                role="title",
                slide_number=sn,
                layout_type=lt,
                slot_order=0,
                design_stage_region=region,
                role_sizes={"title": TITLE_PX},
                _text_items=[(slide.title, True)],
                _box_w=CONTENT_W,
                _box_h=title_h,
                _fit_role=None,
                _mode="fixed",
                _margin_boxes=1,
            )
        )

        adaptive_surfaces: list[SurfacePlan] = []
        if slide.content is not None:
            typo = slide.content.typography
            mode, sync, explicit = _typo_fields(typo, "subtitle_font_size")
            subtitle_plan = SurfacePlan(
                surface_id=f"slide-{sn}-subtitle",
                role="subtitle",
                slide_number=sn,
                layout_type=lt,
                slot_order=1,
                design_stage_region=region,
                role_sizes={"subtitle": SUBTITLE_FLOOR},
                _text_items=[(slide.content.subtitle, False)],
                _box_w=CONTENT_W,
                _fit_role="subtitle",
                _typo=typo,
                _mode=mode,
                _sync_group=sync,
                _explicit_size=explicit,
                _margin_boxes=1,
                _default_size=SUBTITLE_FLOOR,
                _maximum_size=SUBTITLE_CEIL,
            )
            adaptive_surfaces.append(subtitle_plan)
            out.append(subtitle_plan)

        # Takeaway reserved before body so body cannot steal its slot (D172/D288).
        takeaway_plan: SurfacePlan | None = None
        if slide.takeaway is not None:
            typo = slide.takeaway.typography
            mode, sync, explicit = _typo_fields(typo, "body_font_size")
            # Outer reservation includes chrome; fitter sees only text box (D172).
            chrome = (
                _line_box(TAKEAWAY_LABEL_PX)
                + TAKEAWAY_LABEL_MB
                + TAKEAWAY_PAD_Y
                + TAKEAWAY_BORDER_Y
                + TAKEAWAY_OUTER_MT
                + BLOCK_MARGIN_Y  # takeaway-text <p> trailing margin
            )
            takeaway_plan = SurfacePlan(
                surface_id=f"slide-{sn}-takeaway",
                role="takeaway",
                slide_number=sn,
                layout_type=lt,
                slot_order=100,  # after blocks; set final after block count
                design_stage_region=region,
                role_sizes={
                    "body": TAKEAWAY_FLOOR,
                    "label": TAKEAWAY_LABEL_PX,
                },
                _text_items=[(slide.takeaway.text, False)],
                _box_w=CONTENT_W - TAKEAWAY_PAD_X - TAKEAWAY_BORDER_X,
                _fit_role="body",
                _typo=typo,
                _mode=mode,
                _sync_group=sync,
                _explicit_size=explicit,
                _margin_boxes=0,  # text p margin already in chrome
                _chrome_h=chrome,
                _default_size=TAKEAWAY_FLOOR,
                _maximum_size=TAKEAWAY_CEIL,
            )

        body_h = DESIGN_STAGE_H - PAD_TOP - PAD_BOTTOM - used
        blocks = list(slide.payload.blocks)
        # One common body size across all blocks (D225/D270) — shared measure group.
        body_typo = slide.payload.typography
        mode, sync, explicit = _typo_fields(body_typo, "body_font_size")
        for i, block in enumerate(blocks):
            items = _block_text_items(block)
            # Deck-unique surface id: block_id is only slide-local (D115/D225).
            surface_id = f"slide-{sn}-block-{block.block_id}"
            # paragraphs: margin after every <p>; bullet_list: margin after the <ul>.
            if block.type == "paragraphs":
                margin_boxes = max(1, len(block.paragraphs))
            else:
                margin_boxes = 1
            out.append(
                SurfacePlan(
                    surface_id=surface_id,
                    role="narrative_block",
                    slide_number=sn,
                    layout_type=lt,
                    slot_order=10 + i,
                    design_stage_region=region,
                    role_sizes={"body": BODY_FLOOR},
                    _text_items=items,
                    _box_w=CONTENT_W,
                    _fit_role="body",
                    _typo=body_typo,
                    _mode=mode,
                    _sync_group=sync,
                    _explicit_size=explicit,
                    _margin_boxes=margin_boxes,
                    _indent_em=LIST_INDENT_EM if block.type == "bullet_list" else 0,
                    _default_size=BODY_FLOOR,
                    _maximum_size=BODY_CEIL,
                )
            )
            adaptive_surfaces.append(out[-1])

        if takeaway_plan is not None:
            takeaway_plan.slot_order = 10 + len(blocks)
            adaptive_surfaces.append(takeaway_plan)
            out.append(takeaway_plan)

        _allocate_geometry(adaptive_surfaces, body_h)

    # Stable plan order: slide, slot, surface_id (D312).
    out.sort(key=lambda s: (s.slide_number, s.slot_order, s.surface_id))
    return out


def _prose_items(prose: Any) -> list[tuple[str, bool]]:
    return [(run.text, run.emphasis == "strong") for run in prose.runs]


def _typo_fields(
    typo: Optional[Typography], size_field: str
) -> tuple[str, Optional[str], Optional[int]]:
    if typo is None:
        return "adaptive", None, None
    mode = typo.mode
    sync = typo.sync_group if mode == "adaptive" else None
    explicit = getattr(typo, size_field, None)
    return mode, sync, explicit


def _allocate_geometry(surfaces: list[SurfacePlan], available_h: int) -> None:
    """Reserve measured needs jointly so sparse siblings yield unused geometry."""
    if not surfaces:
        return

    def need(sp: SurfacePlan, size: int) -> int:
        return _required_height(
            sp._text_items, size, sp._box_w, sp._margin_boxes, sp._indent_em
        )

    floors = [need(sp, sp._default_size or next(iter(sp.role_sizes.values()))) for sp in surfaces]
    remaining = max(0, available_h - sum(sp._chrome_h for sp in surfaces))
    allocations = []
    for height in floors:
        allocations.append(min(remaining, height))
        remaining -= allocations[-1]

    groups: dict[tuple[str, str], list[int]] = {}
    for i, sp in enumerate(surfaces):
        if sp._mode != "adaptive" or sp._explicit_size is not None or not sp._fit_role:
            continue
        key = sp._sync_group or (
            f"slide:{sp.slide_number}:body" if sp.role == "narrative_block" else sp.surface_id
        )
        groups.setdefault((sp._fit_role, key), []).append(i)

    for indexes in groups.values():
        members = [surfaces[i] for i in indexes]
        floor = max(sp._default_size or 0 for sp in members)
        ceiling = min(sp._maximum_size or floor for sp in members)
        for size in range(ceiling, floor - 1, -1):
            wanted = [need(sp, size) for sp in members]
            extra = sum(max(0, height - allocations[i]) for i, height in zip(indexes, wanted))
            if extra <= remaining:
                for i, height in zip(indexes, wanted):
                    remaining -= max(0, height - allocations[i])
                    allocations[i] = max(allocations[i], height)
                break

    for i, sp in enumerate(surfaces):
        wanted = need(sp, sp._maximum_size or next(iter(sp.role_sizes.values())))
        extra = min(remaining, max(0, wanted - allocations[i]))
        allocations[i] += extra
        remaining -= extra

    for sp, height, floor_h in zip(surfaces, allocations, floors):
        sp._box_h = height
        sp.reservations = [
            {"kind": "text", "height": height},
            {"kind": "chrome", "height": sp._chrome_h},
        ]
        if height > floor_h:
            sp.adaptation_codes.append("plan.geometry_reallocated")


# ---------------------------------------------------------------------------
# Measure
# ---------------------------------------------------------------------------


def _measure_surface(sp: SurfacePlan, events: list[DiagnosticEvent]) -> None:
    fit = sp._fit_role
    if fit is None:
        # Fixed chrome — measure each cover role at its own frozen size (R178-005).
        if sp._cover_items:
            if not _cover_fits(sp):
                sp._overflow = True
            return
        px = next(iter(sp.role_sizes.values()))
        if not _text_fits(
            sp._text_items, px, sp._box_w, sp._box_h, margin_boxes=sp._margin_boxes, indent_em=sp._indent_em
        ):
            sp._overflow = True
        return

    floor = sp.role_sizes[fit]
    ceil = {"subtitle": SUBTITLE_CEIL, "body": BODY_CEIL}[fit]
    if fit == "body" and sp.role == "takeaway":
        floor, ceil = TAKEAWAY_FLOOR, TAKEAWAY_CEIL
        sp.role_sizes[fit] = floor

    # Explicit size validation (D49): out of role range is malformed.
    if sp._explicit_size is not None and not (floor <= sp._explicit_size <= ceil):
        events.append(
            event(
                code="validation.fit",
                severity="error",
                phase="plan",
                role=sp.role,
                path=f"/slides/{sp.slide_number}/typography",
                action="reject",
                result="failed",
                slide_number=sp.slide_number,
                layout_type=sp.layout_type,
                surface_id=sp.surface_id,
                expected=f"{fit} size within {floor}..{ceil}",
                input_meta={"type": "int", "value": sp._explicit_size},
            )
        )
        # Discard pin now so measure continues with defaults; strict raises later.
        sp._explicit_size = None
        sp._mode = "adaptive"
        sp._sync_group = None
        sp._malformed_explicit = True

    if sp._mode == "fixed":
        size = sp._explicit_size if sp._explicit_size is not None else floor
        sp.role_sizes[fit] = size
        if not _text_fits(
            sp._text_items, size, sp._box_w, sp._box_h, margin_boxes=sp._margin_boxes, indent_em=sp._indent_em
        ):
            sp._overflow = True
        return

    # Adaptive grow-only (D2): try ceiling down to floor; pick largest that fits.
    if sp._explicit_size is not None:
        # Pinned role — no growth (D218); still must fit.
        size = sp._explicit_size
        sp.role_sizes[fit] = size
        if not _text_fits(
            sp._text_items, size, sp._box_w, sp._box_h, margin_boxes=sp._margin_boxes, indent_em=sp._indent_em
        ):
            # Spec: explicit that does not fit → normal strict/non-strict (D27).
            sp._overflow = True
        return

    chosen = floor
    wrapped = False
    for size in range(ceil, floor - 1, -1):
        ok, did_wrap = _text_fits_detail(
            sp._text_items,
            size,
            sp._box_w,
            sp._box_h,
            margin_boxes=sp._margin_boxes,
            indent_em=sp._indent_em,
        )
        if ok:
            chosen = size
            wrapped = did_wrap
            break
    else:
        # Floor does not fit.
        sp._overflow = True
        chosen = floor

    sp.role_sizes[fit] = chosen
    if chosen > floor:
        sp.adaptation_codes.append("plan.typography_grown")
    if wrapped:
        sp.adaptation_codes.append("plan.text_wrapped")
        events.append(
            event(
                code="plan.text_wrapped",
                severity="info",
                phase="plan",
                role=sp.role,
                path=f"/slides/{sp.slide_number}/{sp.role}",
                action="measure",
                result="accepted",
                slide_number=sp.slide_number,
                layout_type=sp.layout_type,
                surface_id=sp.surface_id,
            )
        )


def _text_fits(
    items: list[tuple[str, bool]],
    px: int,
    box_w: int,
    box_h: int,
    *,
    margin_boxes: int = 1,
    indent_em: float = 0,
) -> bool:
    ok, _ = _text_fits_detail(
        items, px, box_w, box_h, margin_boxes=margin_boxes, indent_em=indent_em
    )
    return ok


def _text_fits_detail(
    items: list[tuple[str, bool]],
    px: int,
    box_w: int,
    box_h: int,
    *,
    margin_boxes: int = 1,
    indent_em: float = 0,
) -> tuple[bool, bool]:
    """Return (fits, wrapped). Never truncates or drops text (D59)."""
    if box_w <= 0 or box_h <= 0:
        return False, False
    units = _split_units(items)
    line_h = _line_box(px)
    total_lines = 0
    wrapped = False
    width_overflow = False
    for unit_items in units:
        text_u = "".join(t for t, _ in unit_items)
        if not text_u:
            continue
        lines, wo = _wrap_lines(unit_items, px, box_w - math.ceil(px * indent_em))
        width_overflow = width_overflow or wo
        total_lines += max(1, len(lines))
        if len(lines) > 1:
            wrapped = True
    # Paint applies margin-bottom after every CSS block box (p or ul).
    # margin_boxes is the count of those boxes for this surface (R178-002).
    boxes = max(0, margin_boxes)
    need_h = total_lines * line_h + boxes * BLOCK_MARGIN_Y
    fits = (need_h <= box_h) and not width_overflow
    return fits, wrapped


def _required_height(
    items: list[tuple[str, bool]],
    px: int,
    box_w: int,
    margin_boxes: int,
    indent_em: float = 0,
) -> int:
    units = _split_units(items)
    lines = sum(
        max(1, len(_wrap_lines(unit, px, box_w - math.ceil(px * indent_em))[0]))
        for unit in units
    )
    return lines * _line_box(px) + max(0, margin_boxes) * BLOCK_MARGIN_Y


def _cover_fits(sp: SurfacePlan) -> bool:
    """Measure each cover element at its own frozen role size (R178-005)."""
    box_w = sp._box_w
    box_h = sp._box_h
    need_h = 0
    for text_c, role_key in sp._cover_items:
        px = sp.role_sizes[role_key]
        strong = role_key == "title"
        lines, wo = _wrap_lines([(text_c, strong)], px, box_w)
        if wo:
            return False
        need_h += max(1, len(lines)) * _line_box(px) + BLOCK_MARGIN_Y
    return need_h <= box_h


def _split_units(
    items: list[tuple[str, bool]],
) -> list[list[tuple[str, bool]]]:
    """Split on explicit newline markers; otherwise one unit (single prose).

    Block collectors insert a ('\\n', False) sentinel between paragraphs/items.
    """
    units: list[list[tuple[str, bool]]] = [[]]
    for text, strong in items:
        if text == "\n" and not strong:
            if units[-1]:
                units.append([])
            continue
        units[-1].append((text, strong))
    return [u for u in units if u]


def _wrap_lines(
    items: list[tuple[str, bool]], px: int, box_w: int
) -> tuple[list[str], bool]:
    """Word-wrap at spaces/punctuation; never split words (D24/D59).

    Returns (lines, width_overflow). Width overflow means an unbreakable token
    exceeds the box — still kept intact, never truncated.
    """
    text = "".join(t for t, _ in items)
    if not text:
        return [""], False
    strong_chars = sum(len(run) for run, strong in items if strong)
    weight = 1 + (STRONG_MULTIPLIER - 1) * strong_chars / max(1, len(text))

    def width(value: str) -> float:
        measured = 0.0
        for char in value:
            if char.isspace():
                advance = GLYPH_ADVANCE["space"]
            elif char in "ilIjtfr.,:;!'|":
                advance = GLYPH_ADVANCE["narrow"]
            elif char in "MW@%&QGmwm":
                advance = GLYPH_ADVANCE["wide"]
            else:
                advance = GLYPH_ADVANCE["normal"]
            measured += px * advance * weight
        return max(measured * 1.05, measured + 2)

    tokens = re.findall(r"\S+\s*", text)
    if not tokens:
        return [text], width(text) > box_w
    lines: list[str] = []
    cur = ""
    width_overflow = False
    for tok in tokens:
        tok_w = width(tok.rstrip())
        if tok_w > box_w:
            width_overflow = True
        trial = cur + tok
        if cur and width(trial) > box_w:
            lines.append(cur.rstrip())
            cur = tok
        else:
            cur = trial
    if cur:
        lines.append(cur.rstrip())
    return (lines or [""]), width_overflow


def _line_box(px: int) -> int:
    return int(math.ceil(px * LINE_HEIGHT))


# ---------------------------------------------------------------------------
# Synchronize
# ---------------------------------------------------------------------------


def _synchronize(surfaces: list[SurfacePlan], events: list[DiagnosticEvent]) -> None:
    """Equivalent roles share the largest common safe size (D3/D26/D69)."""
    # Group by (fit_role_name, sync_key). Same-slide narrative body blocks share
    # an implicit group so D225 one-size-across-blocks holds even without key.
    groups: dict[tuple[str, str], list[SurfacePlan]] = {}
    for sp in surfaces:
        fit = sp._fit_role
        if fit is None or sp._mode != "adaptive" or sp._explicit_size is not None:
            continue
        if sp._sync_group:
            key = (fit, f"g:{sp._sync_group}")
        elif sp.role == "narrative_block":
            key = (fit, f"slide:{sp.slide_number}:body")
        else:
            continue  # independent
        groups.setdefault(key, []).append(sp)

    for (_fit, _key), members in sorted(groups.items(), key=lambda kv: kv[0]):
        if len(members) < 2:
            continue
        # Largest common size that every member can fit.
        fit = members[0]._fit_role
        if fit is None:
            continue
        # Role floor (not the already-chosen size) — preserve typography_grown.
        role_floor = {
            "subtitle": SUBTITLE_FLOOR,
            "body": TAKEAWAY_FLOOR if members[0].role == "takeaway" else BODY_FLOOR,
        }[fit]
        # Start from min of independently chosen sizes, then try grow to max
        # of those if all fit — D3: largest that safely fits every member.
        independent = [m.role_sizes[fit] for m in members]
        target = min(independent)
        upper = max(independent)
        for size in range(upper, role_floor - 1, -1):
            if all(
                _text_fits(
                    m._text_items,
                    size,
                    m._box_w,
                    m._box_h,
                    margin_boxes=m._margin_boxes,
                    indent_em=m._indent_em,
                )
                for m in members
            ):
                target = size
                break
        changed = False
        for m in members:
            if m.role_sizes[fit] != target:
                changed = True
            m.role_sizes[fit] = target
            # Drop grow code only when frozen size is the role floor.
            if target == role_floor:
                m.adaptation_codes = [
                    c for c in m.adaptation_codes if c != "plan.typography_grown"
                ]
            elif "plan.typography_grown" not in m.adaptation_codes and target > role_floor:
                m.adaptation_codes.append("plan.typography_grown")
        if changed or len(members) > 1:
            for m in members:
                if "plan.synchronized" not in m.adaptation_codes:
                    m.adaptation_codes.append("plan.synchronized")
                events.append(
                    event(
                        code="plan.synchronized",
                        severity="info",
                        phase="plan",
                        role=m.role,
                        path=f"/slides/{m.slide_number}/{m.role}",
                        action="measure",
                        result="accepted",
                        slide_number=m.slide_number,
                        layout_type=m.layout_type,
                        surface_id=m.surface_id,
                        expected=f"{fit} synchronized to {target}px",
                        input_meta={"type": "int", "value": target},
                    )
                )


# ---------------------------------------------------------------------------
# Digests / events
# ---------------------------------------------------------------------------


def _seal_digests(sp: SurfacePlan) -> None:
    sizes = ",".join(f"{k}:{sp.role_sizes[k]}" for k in sorted(sp.role_sizes))
    adap = ",".join(sp.adaptation_codes)
    base = (
        f"{sp.slide_number}|{sp.layout_type}|{sp.role}|{sp.surface_id}|"
        f"{sp.design_stage_region}|{sizes}|{adap}|{sp.fallback or ''}"
    )
    # Semantic digest: identity + content fingerprint (not sizes).
    content = "|".join(t for t, _ in sp._text_items)
    sem_src = f"{sp.slide_number}|{sp.role}|{sp.surface_id}|{content}"
    sp.semantic_digest = _sha(sem_src)
    sp.painter_plan_digest = _sha(base)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _overflow_event(sp: SurfacePlan) -> DiagnosticEvent:
    return event(
        code="plan.unresolved_overflow",
        severity="error",
        phase="plan",
        role=sp.role,
        path=f"/slides/{sp.slide_number}/{sp.role}",
        action="measure",
        result="failed",
        slide_number=sp.slide_number,
        layout_type=sp.layout_type,
        surface_id=sp.surface_id,
        expected="complete text fits at role floor without truncation",
    )


def _block_text_items(block: Any) -> list[tuple[str, bool]]:
    """Flatten block prose with unit separators for multi-unit height."""
    items: list[tuple[str, bool]] = []
    if block.type == "paragraphs":
        for i, prose in enumerate(block.paragraphs):
            if i:
                items.append(("\n", False))
            items.extend(_prose_items(prose))
    else:
        for i, prose in enumerate(block.items):
            if i:
                items.append(("\n", False))
            items.extend(_prose_items(prose))
    return items
