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
DIVIDER_TITLE_PX: Final = 56
DIVIDER_META_PX: Final = 22
LEGAL_TITLE_PX: Final = 28
LEGAL_BODY_PX: Final = 16
TAKEAWAY_LABEL_PX: Final = 14
DISCLOSURE_PX: Final = 14
SOURCE_FOOTER_PX: Final = 14

# Adaptive floors / ceilings (D12/D14/D51/D59/D171/D172/D225/D288).
SUBTITLE_FLOOR: Final = 22
SUBTITLE_CEIL: Final = 26
BODY_FLOOR: Final = 22
BODY_CEIL: Final = 28
TAKEAWAY_FLOOR: Final = 22
TAKEAWAY_CEIL: Final = 28
TABLE_FLOOR: Final = 20  # D44 ordinary data_table
TABLE_CEIL: Final = 24
TABLE_MAX_LABEL_LINES: Final = 2
# Must match publish CSS padding on table.data-table th/td (8px*2, 6px*2).
TABLE_CELL_PAD_X: Final = 16
TABLE_CELL_PAD_Y: Final = 12
TABLE_RULE_Y: Final = 1

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
DISCLOSURE_INDENT_EM: Final = 1.25
_METRIC_CHARS: Final = ''.join(chr(i) for i in range(32, 127))
_SOURCE_SANS_ADVANCES: Final = {
    400: dict(zip(_METRIC_CHARS, (0.2,0.289,0.426,0.497,0.497,0.824,0.609,0.249,0.303,0.303,0.418,0.497,0.249,0.311,0.249,0.35,0.497,0.497,0.497,0.497,0.497,0.497,0.497,0.497,0.497,0.497,0.249,0.249,0.497,0.497,0.497,0.425,0.847,0.543,0.588,0.571,0.615,0.527,0.494,0.617,0.652,0.263,0.479,0.579,0.486,0.727,0.647,0.664,0.566,0.664,0.569,0.534,0.536,0.645,0.515,0.786,0.513,0.476,0.539,0.303,0.35,0.303,0.497,0.5,0.542,0.504,0.553,0.456,0.555,0.496,0.292,0.504,0.544,0.246,0.247,0.495,0.255,0.829,0.547,0.542,0.555,0.555,0.347,0.419,0.338,0.544,0.467,0.719,0.446,0.467,0.425,0.303,0.241,0.303,0.497))),
    700: dict(zip(_METRIC_CHARS, (0.2,0.34,0.537,0.528,0.528,0.857,0.667,0.3,0.344,0.344,0.457,0.528,0.3,0.332,0.3,0.339,0.528,0.528,0.528,0.528,0.528,0.528,0.528,0.528,0.528,0.528,0.3,0.3,0.528,0.528,0.528,0.463,0.902,0.573,0.605,0.582,0.635,0.548,0.524,0.638,0.674,0.301,0.509,0.614,0.518,0.762,0.665,0.684,0.596,0.684,0.613,0.556,0.556,0.665,0.556,0.813,0.567,0.525,0.541,0.344,0.339,0.344,0.528,0.5,0.555,0.527,0.573,0.468,0.573,0.518,0.341,0.534,0.571,0.276,0.278,0.548,0.286,0.857,0.572,0.555,0.573,0.573,0.398,0.443,0.383,0.568,0.523,0.776,0.514,0.521,0.46,0.344,0.268,0.344,0.528))),
}


@dataclass
class SurfacePlan:
    """Frozen plan for one semantic surface (D312)."""

    surface_id: str
    role: str
    slide_number: int
    slide_index: int
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
    # Per-unit painted indents (disclosure summary/list vs paragraph).
    _unit_indent_ems: list[float] = field(default_factory=list)
    _default_size: Optional[int] = None
    _maximum_size: Optional[int] = None
    # data_table fit payload (formatted cells + labels); None for non-tables.
    _table_spec: Optional[dict[str, Any]] = None
    # Frozen paint input for data_table (public to painters; set at seal).
    table_paint: Optional[dict[str, Any]] = None

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

    sync_roles: dict[str, set[str]] = {}
    for sp in surfaces:
        if sp._sync_group and sp._fit_role and sp._explicit_size is None:
            sync_roles.setdefault(sp._sync_group, set()).add(sp._fit_role)
    invalid_sync = {group for group, roles in sync_roles.items() if len(roles) > 1}
    for sp in surfaces:
        if sp._explicit_size is not None or sp._sync_group not in invalid_sync:
            continue
        events.append(
            event(
                code="validation.conflict" if strict else "repair.sync_disabled",
                severity="error" if strict else "warning",
                phase="plan",
                role=sp.role,
                path=f"/slides/{sp.slide_index}/{sp.role}/typography/sync_group",
                action="reject" if strict else "disable_sync",
                result="failed" if strict else "independent",
                slide_number=sp.slide_number,
                layout_type=sp.layout_type,
                surface_id=sp.surface_id,
                expected="sync_group contains one typography role",
            )
        )
        if not strict:
            sp._sync_group = None

    # Phase 1 — independent measure at design stage.
    for sp in surfaces:
        if _uses_fallback_metrics(sp):
            events.append(
                event(
                    code="plan.conservative_metrics",
                    severity="warning",
                    phase="plan",
                    role=sp.role,
                    path=f"/slides/{sp.slide_index}/{sp.role}",
                    action="measure",
                    result="accepted",
                    slide_number=sp.slide_number,
                    layout_type=sp.layout_type,
                    surface_id=sp.surface_id,
                    expected="unsupported glyphs measured with conservative fallback advances",
                )
            )
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
                    path=f"/slides/{sp.slide_index}/{sp.role}",
                    action="measure",
                    result="accepted",
                    slide_number=sp.slide_number,
                    layout_type=sp.layout_type,
                    surface_id=sp.surface_id,
                    expected=f"{fit} grew to {size}px",
                    input_meta={"type": "int", "value": size},
                )
            )

    fit_errors = [e for e in events if e.code == "validation.fit"]
    overflow = [s for s in surfaces if s._overflow]
    if strict and (overflow or fit_errors or invalid_sync):
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
    for slide_index, slide in enumerate(deck.slides):
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
                    slide_index=slide_index,
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

        if lt == "section_divider":
            region += 1
            # Label + optional registry-order number come from D215 only (D269).
            sec = next(
                s for s in deck.sections if s.section_id == slide.payload.section_id
            )
            ord_n = next(
                i + 1
                for i, s in enumerate(deck.sections)
                if s.section_id == slide.payload.section_id
            )
            label = sec.label
            meta = f"Section {ord_n}"
            items: list[tuple[str, str]] = [(label, "title"), (meta, "meta")]
            out.append(
                SurfacePlan(
                    surface_id=f"slide-{sn}-divider",
                    role="section_divider",
                    slide_number=sn,
                    slide_index=slide_index,
                    layout_type=lt,
                    slot_order=0,
                    design_stage_region=region,
                    role_sizes={
                        "title": DIVIDER_TITLE_PX,
                        "meta": DIVIDER_META_PX,
                    },
                    _cover_items=items,
                    _text_items=[(t, rk == "title") for t, rk in items],
                    _box_w=CONTENT_W,
                    _box_h=DESIGN_STAGE_H - PAD_TOP - PAD_BOTTOM,
                    _fit_role=None,
                    _mode="fixed",
                    _margin_boxes=len(items),
                )
            )
            continue

        if lt == "legal_notice":
            region += 1
            p = slide.payload
            # Fixed legal typography (D182/D226/D271): part 1 title; later — continued.
            heading = p.title if p.part == 1 else "— continued"
            assert heading is not None
            legal_items: list[tuple[str, str]] = [(heading, "title")]
            for para in p.paragraphs:
                legal_items.append((para, "body"))
            if p.part > 1:
                legal_items.append((f"Part {p.part} of {p.total_parts}", "meta"))
            out.append(
                SurfacePlan(
                    surface_id=f"slide-{sn}-legal",
                    role="legal_notice",
                    slide_number=sn,
                    slide_index=slide_index,
                    layout_type=lt,
                    slot_order=0,
                    design_stage_region=region,
                    role_sizes={
                        "title": LEGAL_TITLE_PX,
                        "body": LEGAL_BODY_PX,
                        "meta": LEGAL_BODY_PX,
                    },
                    _cover_items=legal_items,
                    _text_items=[(t, rk == "title") for t, rk in legal_items],
                    _box_w=CONTENT_W,
                    _box_h=DESIGN_STAGE_H - PAD_TOP - PAD_BOTTOM,
                    _fit_role=None,
                    _mode="fixed",
                    _margin_boxes=len(legal_items),
                )
            )
            continue

        if lt not in ("narrative", "data_table"):
            continue

        # Slot order: title chrome (fixed), subtitle, body/table, takeaway.
        region += 1
        title_h = _required_height([(slide.title, True)], TITLE_PX, CONTENT_W, 1)
        used = title_h

        # Title is fixed chrome — recorded so painters share one plan.
        out.append(
            SurfacePlan(
                surface_id=f"slide-{sn}-title",
                role="title",
                slide_number=sn,
                slide_index=slide_index,
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
                slide_index=slide_index,
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
                slide_index=slide_index,
                layout_type=lt,
                slot_order=100,  # after body; set final after body slots
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
        body_slots = 0
        if lt == "narrative":
            blocks = list(slide.payload.blocks)
            body_slots = len(blocks)
            # One common body size across all blocks (D225/D270).
            body_typo = slide.payload.typography
            mode, sync, explicit = _typo_fields(body_typo, "body_font_size")
            for i, block in enumerate(blocks):
                items = _block_text_items(block)
                surface_id = f"slide-{sn}-block-{block.block_id}"
                if block.type == "paragraphs":
                    margin_boxes = max(1, len(block.paragraphs))
                else:
                    margin_boxes = 1
                out.append(
                    SurfacePlan(
                        surface_id=surface_id,
                        role="narrative_block",
                        slide_number=sn,
                        slide_index=slide_index,
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
        else:
            # data_table: one full-width table surface (D183/D257).
            body_slots = 1
            table = slide.payload.table
            table_typo = table.typography
            mode, sync, explicit = _typo_fields(table_typo, "table_font_size")
            table_spec = _build_table_spec(table, deck.number_formats)
            # All labels + values feed conservative-metrics + digest.
            text_items = [(t, False) for t in table_spec["all_texts"]]
            out.append(
                SurfacePlan(
                    surface_id=table.surface_id,
                    role="data_table",
                    slide_number=sn,
                    slide_index=slide_index,
                    layout_type=lt,
                    slot_order=10,
                    design_stage_region=region,
                    role_sizes={"table": TABLE_FLOOR},
                    _text_items=text_items,
                    _box_w=CONTENT_W,
                    _fit_role="table",
                    _typo=table_typo,
                    _mode=mode,
                    _sync_group=sync,
                    _explicit_size=explicit,
                    _margin_boxes=0,
                    _default_size=TABLE_FLOOR,
                    _maximum_size=TABLE_CEIL,
                    _table_spec=table_spec,
                )
            )
            adaptive_surfaces.append(out[-1])

        if takeaway_plan is not None:
            takeaway_plan.slot_order = 10 + body_slots
            adaptive_surfaces.append(takeaway_plan)
            out.append(takeaway_plan)

        next_slot = 11 + body_slots
        if slide.disclosure is not None:
            for section in slide.disclosure.sections:
                items = [(section.title, True)]
                items.extend((item.text, False) for item in section.items)
                # Summary + list items indented in paint; plain paragraphs full width.
                unit_indents = [DISCLOSURE_INDENT_EM]
                unit_indents.extend(
                    LIST_INDENT_EM if item.kind == "bullet" else 0.0
                    for item in section.items
                )
                bullet_groups = sum(
                    item.kind == "bullet"
                    and (i == 0 or section.items[i - 1].kind != "bullet")
                    for i, item in enumerate(section.items)
                )
                paragraph_boxes = sum(item.kind == "paragraph" for item in section.items)
                disclosure = SurfacePlan(
                    surface_id=f"slide-{sn}-disclosure-{section.surface_id}",
                    role="disclosure",
                    slide_number=sn,
                    slide_index=slide_index,
                    layout_type=lt,
                    slot_order=next_slot,
                    design_stage_region=region,
                    role_sizes={"body": DISCLOSURE_PX},
                    _text_items=[
                        item
                        for pair in zip(items, [("\n", False)] * len(items))
                        for item in pair
                    ][:-1],
                    _box_w=CONTENT_W,
                    _fit_role=None,
                    _mode="fixed",
                    _margin_boxes=paragraph_boxes + bullet_groups,
                    _indent_em=0,
                    _unit_indent_ems=unit_indents,
                )
                next_slot += 1
                adaptive_surfaces.append(disclosure)
                out.append(disclosure)

        if slide.source_footer is not None:
            source_text = "Sources: " + "; ".join(
                deck.evidence_registry[eid].source_name for eid in slide.source_footer
            )
            source = SurfacePlan(
                surface_id=f"slide-{sn}-source-footer",
                role="source_footer",
                slide_number=sn,
                slide_index=slide_index,
                layout_type=lt,
                slot_order=next_slot,
                design_stage_region=region,
                role_sizes={"body": SOURCE_FOOTER_PX},
                _text_items=[(source_text, False)],
                _box_w=CONTENT_W,
                _fit_role=None,
                _mode="fixed",
                _margin_boxes=1,
            )
            adaptive_surfaces.append(source)
            out.append(source)

        _allocate_geometry(adaptive_surfaces, body_h)

    # Stable plan order follows authored deck order (D312).
    out.sort(key=lambda s: (s.slide_index, s.slot_order, s.surface_id))
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
        if sp._table_spec is not None:
            ok, _, height = _table_fit_detail(sp._table_spec, size, sp._box_w, 10**9)
            return height if ok else 10**9
        return _required_height(
            sp._text_items, size, sp._box_w, sp._margin_boxes, sp._indent_em, sp._unit_indent_ems
        )

    baseline_sizes = [
        sp._explicit_size
        if sp._explicit_size is not None
        else sp._default_size or next(iter(sp.role_sizes.values()))
        for sp in surfaces
    ]
    floors = [need(sp, size) for sp, size in zip(surfaces, baseline_sizes)]
    remaining = max(0, available_h - sum(sp._chrome_h for sp in surfaces))
    allocations = [0] * len(surfaces)
    priority = sorted(
        range(len(surfaces)),
        key=lambda i: (
            surfaces[i].role not in {"takeaway", "disclosure", "source_footer"}
            and surfaces[i]._explicit_size is None
            and surfaces[i]._mode != "fixed",
            i,
        ),
    )
    for i in priority:
        allocations[i] = min(remaining, floors[i])
        remaining -= allocations[i]

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
            sp._text_items, px, sp._box_w, sp._box_h, margin_boxes=sp._margin_boxes, indent_em=sp._indent_em, unit_indent_ems=sp._unit_indent_ems
        ):
            sp._overflow = True
        return

    floor = sp.role_sizes[fit]
    ceil_map = {
        "subtitle": SUBTITLE_CEIL,
        "body": BODY_CEIL,
        "table": TABLE_CEIL,
    }
    ceil = ceil_map[fit]
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
                path=f"/slides/{sp.slide_index}/typography",
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

    def _fits(size: int) -> tuple[bool, bool]:
        if sp._table_spec is not None:
            ok, codes, _h = _table_fit_detail(
                sp._table_spec, size, sp._box_w, sp._box_h
            )
            return ok, "plan.text_wrapped" in codes
        return _text_fits_detail(
            sp._text_items,
            size,
            sp._box_w,
            sp._box_h,
            margin_boxes=sp._margin_boxes,
            indent_em=sp._indent_em,
            unit_indent_ems=sp._unit_indent_ems,
        )

    if sp._mode == "fixed":
        size = sp._explicit_size if sp._explicit_size is not None else floor
        sp.role_sizes[fit] = size
        ok, _ = _fits(size)
        if not ok:
            sp._overflow = True
            if sp._table_spec is not None:
                _apply_table_floor_adaptations(sp, size, events)
        elif sp._table_spec is not None:
            _record_table_adaptations(sp, size, events)
        return

    # Adaptive grow-only (D2): try ceiling down to floor; pick largest that fits.
    if sp._explicit_size is not None:
        # Pinned role — no growth (D218); still must fit.
        size = sp._explicit_size
        sp.role_sizes[fit] = size
        ok, _ = _fits(size)
        if not ok:
            # Spec: explicit that does not fit → normal strict/non-strict (D27).
            sp._overflow = True
            if sp._table_spec is not None:
                _apply_table_floor_adaptations(sp, size, events)
        elif sp._table_spec is not None:
            _record_table_adaptations(sp, size, events)
        return

    chosen = floor
    wrapped = False
    for size in range(ceil, floor - 1, -1):
        ok, did_wrap = _fits(size)
        if ok:
            chosen = size
            wrapped = did_wrap
            break
    else:
        # Floor does not fit.
        sp._overflow = True
        chosen = floor
        if sp._table_spec is not None:
            _apply_table_floor_adaptations(sp, chosen, events)

    sp.role_sizes[fit] = chosen
    if chosen > floor:
        sp.adaptation_codes.append("plan.typography_grown")
    if sp._table_spec is not None and not sp._overflow:
        _record_table_adaptations(sp, chosen, events)
    elif wrapped:
        sp.adaptation_codes.append("plan.text_wrapped")
        events.append(
            event(
                code="plan.text_wrapped",
                severity="info",
                phase="plan",
                role=sp.role,
                path=f"/slides/{sp.slide_index}/{sp.role}",
                action="measure",
                result="accepted",
                slide_number=sp.slide_number,
                layout_type=sp.layout_type,
                surface_id=sp.surface_id,
            )
        )


def _unit_indent(unit_index: int, indent_em: float, unit_indent_ems: list[float]) -> float:
    if unit_indent_ems and unit_index < len(unit_indent_ems):
        return unit_indent_ems[unit_index]
    return indent_em


def _text_fits(
    items: list[tuple[str, bool]],
    px: int,
    box_w: int,
    box_h: int,
    *,
    margin_boxes: int = 1,
    indent_em: float = 0,
    unit_indent_ems: list[float] | None = None,
) -> bool:
    ok, _ = _text_fits_detail(
        items,
        px,
        box_w,
        box_h,
        margin_boxes=margin_boxes,
        indent_em=indent_em,
        unit_indent_ems=unit_indent_ems,
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
    unit_indent_ems: list[float] | None = None,
) -> tuple[bool, bool]:
    """Return (fits, wrapped). Never truncates or drops text (D59)."""
    if box_w <= 0 or box_h <= 0:
        return False, False
    units = _split_units(items)
    indents = unit_indent_ems or []
    line_h = _line_box(px)
    total_lines = 0
    wrapped = False
    width_overflow = False
    for i, unit_items in enumerate(units):
        text_u = "".join(t for t, _ in unit_items)
        if not text_u:
            continue
        indent = _unit_indent(i, indent_em, indents)
        lines, wo = _wrap_lines(unit_items, px, box_w - math.ceil(px * indent))
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
    unit_indent_ems: list[float] | None = None,
) -> int:
    units = _split_units(items)
    indents = unit_indent_ems or []
    lines = sum(
        max(
            1,
            len(
                _wrap_lines(
                    unit,
                    px,
                    box_w - math.ceil(px * _unit_indent(i, indent_em, indents)),
                )[0]
            ),
        )
        for i, unit in enumerate(units)
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


def _wrap_tokens(text: str) -> list[tuple[int, str]]:
    """Break after whitespace and after - , ; : . when more content follows."""
    soft = frozenset("-,:;.")
    tokens: list[tuple[int, str]] = []
    i = 0
    n = len(text)
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break
        start = i
        while i < n and not text[i].isspace():
            i += 1
            if text[i - 1] in soft and i < n and not text[i].isspace():
                break
        end = i
        while end < n and text[end].isspace():
            end += 1
        tokens.append((start, text[start:end]))
        i = end
    return tokens


def _wrap_lines(
    items: list[tuple[str, bool]], px: int, box_w: int
) -> tuple[list[str], bool]:
    """Word-wrap at spaces/hyphens; never mid-word split or truncate (D24/D59).

    Returns (lines, width_overflow). Width overflow means an unbreakable token
    exceeds the box — still kept intact, never truncated.
    """
    text = "".join(t for t, _ in items)
    if not text:
        return [""], False
    advances: list[float] = []
    for run, strong in items:
        amap = _advance_map(strong)
        advances.extend(amap.get(char, 1.2) for char in run)

    def width(start: int, length: int) -> float:
        measured = sum(advances[start : start + length]) * px
        return max(measured * 1.05, measured + 2)

    tokens = _wrap_tokens(text)
    if not tokens:
        return [text], width(0, len(text)) > box_w
    lines: list[str] = []
    line_start = tokens[0][0]
    cur = ""
    width_overflow = False
    for start, tok in tokens:
        if width(start, len(tok.rstrip())) > box_w:
            width_overflow = True
        trial = cur + tok
        if cur and width(line_start, len(trial)) > box_w:
            lines.append(cur.rstrip())
            line_start = start
            cur = tok
        else:
            cur = trial
    if cur:
        lines.append(cur.rstrip())
    return (lines or [""]), width_overflow


# Extra glyphs used by table paint (em dash, en dash, ellipsis).
_EXTRA_ADVANCES: Final = {
    "—": 0.5,  # em dash (D103 missing)
    "–": 0.5,  # en dash (ranges)
    "…": 0.75,  # ellipsis (D25 labels)
}


_ADVANCE_MAPS: Final = {
    strong: {**_SOURCE_SANS_ADVANCES[700 if strong else 400], **_EXTRA_ADVANCES}
    for strong in (False, True)
}


def _advance_map(strong: bool) -> dict[str, float]:
    return _ADVANCE_MAPS[strong]


def _uses_fallback_metrics(sp: SurfacePlan) -> bool:
    for text, strong in sp._text_items:
        amap = _advance_map(strong)
        if any(char not in amap for char in text if char != "\n"):
            return True
    return False


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
            "table": TABLE_FLOOR,
        }[fit]
        # Start from min of independently chosen sizes, then try grow to max
        # of those if all fit — D3: largest that safely fits every member.
        independent = [m.role_sizes[fit] for m in members]
        target = min(independent)
        upper = max(independent)

        def _sync_member_fits(m: SurfacePlan, size: int) -> bool:
            if m._table_spec is not None:
                ok, _, _ = _table_fit_detail(m._table_spec, size, m._box_w, m._box_h)
                return ok
            return _text_fits(
                m._text_items,
                size,
                m._box_w,
                m._box_h,
                margin_boxes=m._margin_boxes,
                indent_em=m._indent_em,
                unit_indent_ems=m._unit_indent_ems,
            )

        for size in range(upper, role_floor - 1, -1):
            if all(_sync_member_fits(m, size) for m in members):
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
            # Table paint must match the frozen synchronized size (D69/D70).
            if m._table_spec is not None:
                ok, codes, _ = _table_fit_detail(
                    m._table_spec, target, m._box_w, m._box_h
                )
                if ok:
                    m._overflow = False
                    for code in codes:
                        if code not in m.adaptation_codes:
                            m.adaptation_codes.append(code)
                            events.append(
                                event(
                                    code=code,  # type: ignore[arg-type]
                                    severity="info",
                                    phase="plan",
                                    role=m.role,
                                    path=f"/slides/{m.slide_index}/{m.role}",
                                    action="measure",
                                    result="accepted",
                                    slide_number=m.slide_number,
                                    layout_type=m.layout_type,
                                    surface_id=m.surface_id,
                                )
                            )
                else:
                    m._overflow = True
                    _apply_table_floor_adaptations(m, target, events)
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
                        path=f"/slides/{m.slide_index}/{m.role}",
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
    # Freeze table paint payload so painters never reformat (D69/D70).
    if sp._table_spec is not None:
        sp.table_paint = dict(sp._table_spec)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _overflow_event(sp: SurfacePlan) -> DiagnosticEvent:
    return event(
        code="plan.unresolved_overflow",
        severity="error",
        phase="plan",
        role=sp.role,
        path=f"/slides/{sp.slide_index}/{sp.role}",
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


# ---------------------------------------------------------------------------
# data_table measure (D24/D25/D44/D104)
# ---------------------------------------------------------------------------


def _build_table_spec(table: Any, number_formats: Any) -> dict[str, Any]:
    """Pre-format every cell once; fitting never reformats values (D70)."""
    from .format import format_semantic_value

    columns = list(table.columns)
    rows = list(table.rows)
    col_ids = [c.column_id for c in columns]
    header_full = [table.stub_header.label] + [c.label for c in columns]
    header_short = [
        table.stub_header.short_label or table.stub_header.label
    ] + [c.short_label or c.label for c in columns]
    row_labels_full = [r.label for r in rows]
    row_labels_short = [r.short_label or r.label for r in rows]

    cells_vis: list[list[str]] = []
    cells_acc: list[list[str]] = []
    cells_role: list[list[str]] = []
    cells_align: list[list[str]] = []
    format_ids_used: list[str] = []
    for r in rows:
        vis_row: list[str] = []
        acc_row: list[str] = []
        role_row: list[str] = []
        align_row: list[str] = []
        for cid in col_ids:
            fv = format_semantic_value(r.cells[cid], number_formats)
            vis_row.append(fv.visible)
            acc_row.append(fv.accessible)
            role_row.append(fv.role)
            align_row.append(fv.align)
            fid = getattr(r.cells[cid], "format_id", None)
            if fid is not None and fid not in format_ids_used:
                format_ids_used.append(fid)
        cells_vis.append(vis_row)
        cells_acc.append(acc_row)
        cells_role.append(role_row)
        cells_align.append(align_row)

    groups = None
    if table.column_groups:
        groups = [
            {
                "group_id": g.group_id,
                "label": g.label,
                "short_label": g.short_label or g.label,
                "column_ids": list(g.column_ids),
                "colspan": len(g.column_ids),
            }
            for g in table.column_groups
        ]

    scale_labels: list[str] = []
    for fid in format_ids_used:
        disc = number_formats[fid].scale_label
        if disc and disc not in scale_labels:
            scale_labels.append(disc)

    all_texts = (
        header_full
        + header_short
        + row_labels_full
        + row_labels_short
        + [v for row in cells_vis for v in row]
        + [g["label"] for g in (groups or [])]
        + [g["short_label"] for g in (groups or [])]
        + scale_labels
    )
    # Column header alignment follows body column role (D104).
    col_aligns = [
        cells_align[0][c] if cells_align else "right" for c in range(len(col_ids))
    ]
    return {
        "col_ids": col_ids,
        "n_cols": len(col_ids),
        "n_rows": len(rows),
        "header_full": header_full,
        "header_short": header_short,
        "row_labels_full": row_labels_full,
        "row_labels_short": row_labels_short,
        "cells_vis": cells_vis,
        "cells_acc": cells_acc,
        "cells_role": cells_role,
        "cells_align": cells_align,
        "col_aligns": col_aligns,
        "groups": groups,
        "scale_labels": scale_labels,
        "all_texts": all_texts,
        # Filled by fitter for painter consumption (frozen paint input).
        "display_headers": list(header_full),
        "display_row_labels": list(row_labels_full),
        "display_groups": None,
        "col_widths": [],
        "ellipsized": False,
        "short_label_used": False,
    }


def _text_width(text: str, px: int, *, strong: bool = False) -> float:
    advances = _advance_map(strong)
    measured = sum(advances.get(ch, 1.2) for ch in text) * px
    return max(measured * 1.05, measured + 2)


def _wrap_label_lines(text: str, px: int, box_w: int, *, strong: bool = False) -> list[str]:
    lines, _wo = _wrap_lines([(text, strong)], px, box_w)
    return lines or [""]


def _ellipsis_to_width(text: str, px: int, box_w: int, *, strong: bool = False) -> str:
    """Ellipsize label only; values never call this (D25)."""
    if _text_width(text, px, strong=strong) <= box_w:
        return text
    ell = "\u2026"
    if _text_width(ell, px, strong=strong) > box_w:
        return ell
    lo, hi = 0, len(text)
    best = ell
    while lo <= hi:
        mid = (lo + hi) // 2
        cand = text[:mid].rstrip() + ell
        if _text_width(cand, px, strong=strong) <= box_w:
            best = cand
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def _table_fit_detail(
    spec: dict[str, Any],
    px: int,
    box_w: int,
    box_h: int,
    *,
    allow_short: bool = True,
    allow_ellipsis: bool = True,
) -> tuple[bool, list[str], int]:
    """Try to fit table at one common size. Mutates spec display fields on success path callers."""
    codes: list[str] = []
    n_cols = spec["n_cols"]
    n_value_cols = n_cols
    # Stub + value columns.
    total_cols = n_value_cols + 1

    headers = list(spec["header_full"])
    row_labels = list(spec["row_labels_full"])
    groups = spec["groups"]
    group_labels = None if groups is None else [g["label"] for g in groups]
    short_used = False
    ellipsized = False

    # Minimum widths from values (never wrap/ellipsize values — D25/D70).
    value_mins = [0.0] * n_value_cols
    for r in range(spec["n_rows"]):
        for c in range(n_value_cols):
            w = _text_width(spec["cells_vis"][r][c], px) + TABLE_CELL_PAD_X
            if w > value_mins[c]:
                value_mins[c] = w
    def try_widths(h_labels: list[str], r_labels: list[str], g_labels: list[str] | None):
        mins = [0.0] * total_cols
        # Recompute label-driven mins for current label set.
        tokens = _wrap_tokens(h_labels[0])
        mins[0] = max(
            (_text_width(tok.rstrip(), px, strong=True) for _, tok in tokens),
            default=_text_width(h_labels[0], px, strong=True),
        ) + TABLE_CELL_PAD_X
        for lab in r_labels:
            toks = _wrap_tokens(lab)
            tw = max(
                (_text_width(tok.rstrip(), px, strong=True) for _, tok in toks),
                default=_text_width(lab, px, strong=True),
            )
            mins[0] = max(mins[0], tw + TABLE_CELL_PAD_X)
        for c in range(n_value_cols):
            toks = _wrap_tokens(h_labels[c + 1])
            tw = max(
                (_text_width(tok.rstrip(), px, strong=True) for _, tok in toks),
                default=_text_width(h_labels[c + 1], px, strong=True),
            )
            mins[c + 1] = max(tw + TABLE_CELL_PAD_X, value_mins[c])
        # Group labels need span width.
        if g_labels is not None and groups is not None:
            # Map leaf index → width slot; groups only cover value cols possibly including gaps.
            leaf_to_slot = {cid: i + 1 for i, cid in enumerate(spec["col_ids"])}
            for g, glab in zip(groups, g_labels):
                slots = [leaf_to_slot[cid] for cid in g["column_ids"]]
                span_min = sum(mins[s] for s in slots)
                need = _text_width(glab, px, strong=True) + TABLE_CELL_PAD_X
                if need > span_min and slots:
                    # Grow last slot in span.
                    mins[slots[-1]] += need - span_min
        total = sum(mins)
        if total > box_w:
            return None
        # Ceil so value cells never lose the fractional px that round drops (D70).
        widths = [int(math.ceil(m)) for m in mins]
        if sum(widths) > box_w:
            # Float mins fit but integer floors do not — try label adaptations.
            return None
        # Give leftover to the stub column.
        if widths:
            widths[0] += box_w - sum(widths)
        return widths

    def ellipsize_labels(
        h_labels: list[str], r_labels: list[str], g_labels: list[str] | None, widths: list[int]
    ) -> tuple[list[str], list[str], list[str] | None, bool]:
        changed = False
        new_headers = []
        for c, h in enumerate(h_labels):
            cell_w = widths[c] - TABLE_CELL_PAD_X
            lines = _wrap_label_lines(h, px, max(1, cell_w), strong=True)
            if len(lines) > TABLE_MAX_LABEL_LINES or any(
                _text_width(ln, px, strong=True) > cell_w for ln in lines
            ):
                h2 = _ellipsis_to_width(h, px, max(1, cell_w), strong=True)
                if h2 != h:
                    changed = True
                new_headers.append(h2)
            else:
                new_headers.append(h)
        new_rows = []
        cell_w0 = widths[0] - TABLE_CELL_PAD_X
        for lab in r_labels:
            lines = _wrap_label_lines(lab, px, max(1, cell_w0), strong=True)
            if len(lines) > TABLE_MAX_LABEL_LINES or any(
                _text_width(ln, px, strong=True) > cell_w0 for ln in lines
            ):
                lab2 = _ellipsis_to_width(lab, px, max(1, cell_w0), strong=True)
                if lab2 != lab:
                    changed = True
                new_rows.append(lab2)
            else:
                new_rows.append(lab)
        new_g = g_labels
        if g_labels is not None and groups is not None:
            leaf_to_slot = {cid: i + 1 for i, cid in enumerate(spec["col_ids"])}
            new_g = []
            for g, glab in zip(groups, g_labels):
                slots = [leaf_to_slot[cid] for cid in g["column_ids"]]
                span_w = sum(widths[s] for s in slots) - TABLE_CELL_PAD_X
                g2 = _ellipsis_to_width(glab, px, max(1, span_w), strong=True)
                if g2 != glab:
                    changed = True
                new_g.append(g2)
        return new_headers, new_rows, new_g, changed

    def measure(
        h_labels: list[str], r_labels: list[str], g_labels: list[str] | None, widths: list[int]
    ) -> tuple[bool, list[str], int]:
        """Return (fits, adaptation_codes, height) for one label/width assignment."""
        local_codes: list[str] = []
        line_h = _line_box(px)
        geometry_ok = True
        header_lines = 0
        for c, h in enumerate(h_labels):
            cell_w = max(1, widths[c] - TABLE_CELL_PAD_X)
            lines = _wrap_label_lines(h, px, cell_w, strong=True)
            if len(lines) > TABLE_MAX_LABEL_LINES:
                geometry_ok = False
                lines = lines[:TABLE_MAX_LABEL_LINES] or [h]
            header_lines = max(header_lines, max(len(lines), 1))
            if len(lines) > 1 and "plan.text_wrapped" not in local_codes:
                local_codes.append("plan.text_wrapped")
        group_lines = 0
        if g_labels is not None and groups is not None:
            leaf_to_slot = {cid: i + 1 for i, cid in enumerate(spec["col_ids"])}
            for g, glab in zip(groups, g_labels):
                slots = [leaf_to_slot[cid] for cid in g["column_ids"]]
                span_w = max(1, sum(widths[s] for s in slots) - TABLE_CELL_PAD_X)
                lines = _wrap_label_lines(glab, px, span_w, strong=True)
                if len(lines) > TABLE_MAX_LABEL_LINES:
                    geometry_ok = False
                    lines = lines[:TABLE_MAX_LABEL_LINES] or [glab]
                group_lines = max(group_lines, max(len(lines), 1))
                if len(lines) > 1 and "plan.text_wrapped" not in local_codes:
                    local_codes.append("plan.text_wrapped")

        body_lines_total = 0
        for r, lab in enumerate(r_labels):
            cell_w = max(1, widths[0] - TABLE_CELL_PAD_X)
            lines = _wrap_label_lines(lab, px, cell_w, strong=True)
            if len(lines) > TABLE_MAX_LABEL_LINES:
                geometry_ok = False
                lines = lines[:TABLE_MAX_LABEL_LINES] or [lab]
            row_lines = max(len(lines), 1)
            body_lines_total += row_lines
            if len(lines) > 1 and "plan.text_wrapped" not in local_codes:
                local_codes.append("plan.text_wrapped")
            for c in range(n_value_cols):
                if _text_width(spec["cells_vis"][r][c], px) > widths[c + 1] - TABLE_CELL_PAD_X:
                    geometry_ok = False

        scale_h = 0
        if spec["scale_labels"]:
            # Scale disclosure paints at the resolved table size (D22/D44/D257).
            scale_h = _line_box(px) + BLOCK_MARGIN_Y

        n_header_rows = (1 if group_lines else 0) + 1
        height = (
            (group_lines + header_lines) * line_h
            + body_lines_total * line_h
            + (spec["n_rows"] + n_header_rows) * TABLE_CELL_PAD_Y
            + (spec["n_rows"] + n_header_rows) * TABLE_RULE_Y
            + scale_h
            + BLOCK_MARGIN_Y
        )
        fits = geometry_ok and height <= box_h and sum(widths) <= box_w
        return fits, local_codes, height

    def commit(
        h_labels: list[str],
        r_labels: list[str],
        g_labels: list[str] | None,
        widths: list[int],
        *,
        short: bool,
        ellipsis: bool,
        adapt_codes: list[str],
        height: int,
        fits: bool,
    ) -> tuple[bool, list[str], int]:
        spec["display_headers"] = h_labels
        spec["display_row_labels"] = r_labels
        spec["col_widths"] = widths
        spec["ellipsized"] = ellipsis
        spec["short_label_used"] = short
        if groups is not None and g_labels is not None:
            spec["display_groups"] = [
                {**g, "display_label": glab}
                for g, glab in zip(groups, g_labels)
            ]
        else:
            spec["display_groups"] = None
        return fits, adapt_codes, height

    best: tuple[list[str], list[str], list[str] | None, list[int], bool, bool, list[str], int] | None = None

    def consider(
        h_labels: list[str],
        r_labels: list[str],
        g_labels: list[str] | None,
        widths: list[int],
        *,
        short: bool,
        ellipsis: bool,
    ) -> bool:
        nonlocal best, codes
        fits_now, stage_codes, height = measure(h_labels, r_labels, g_labels, widths)
        adapt = list(stage_codes)
        if short and "plan.short_label_used" not in adapt:
            adapt.append("plan.short_label_used")
        if ellipsis and "plan.label_ellipsized" not in adapt:
            adapt.append("plan.label_ellipsized")
        best = (h_labels, r_labels, g_labels, widths, short, ellipsis, adapt, height)
        if fits_now:
            codes = adapt
            return True
        return False

    widths = try_widths(headers, row_labels, group_labels)
    if widths is not None and consider(
        headers, row_labels, group_labels, widths, short=False, ellipsis=False
    ):
        h, r, g, w, sh, el, ad, ht = best  # type: ignore[misc]
        return commit(h, r, g, w, short=sh, ellipsis=el, adapt_codes=ad, height=ht, fits=True)

    if allow_short:
        headers = list(spec["header_short"])
        row_labels = list(spec["row_labels_short"])
        group_labels = (
            None if groups is None else [g["short_label"] for g in groups]
        )
        widths = try_widths(headers, row_labels, group_labels)
        if widths is not None and consider(
            headers, row_labels, group_labels, widths, short=True, ellipsis=False
        ):
            h, r, g, w, sh, el, ad, ht = best  # type: ignore[misc]
            return commit(h, r, g, w, short=sh, ellipsis=el, adapt_codes=ad, height=ht, fits=True)

    if allow_ellipsis:
        headers = list(spec["header_short"])
        row_labels = list(spec["row_labels_short"])
        group_labels = (
            None if groups is None else [g["short_label"] for g in groups]
        )
        # Values keep ceil mins whenever they fit the box; leftover may be
        # only a few px on the stub (labels ellipsize). Equal-split only when
        # value ceils alone exceed box_w.
        value_ceils = [int(math.ceil(v)) for v in value_mins]
        value_total = sum(value_ceils)
        if value_total <= box_w:
            widths = [box_w - value_total] + value_ceils
        else:
            base = max(1, box_w // total_cols)
            widths = [base] * total_cols
            widths[0] += box_w - sum(widths)
        headers, row_labels, group_labels, ellipsized = ellipsize_labels(
            headers, row_labels, group_labels, widths
        )
        short_used = True
        if consider(
            headers,
            row_labels,
            group_labels,
            widths,
            short=True,
            ellipsis=ellipsized,
        ):
            h, r, g, w, sh, el, ad, ht = best  # type: ignore[misc]
            return commit(h, r, g, w, short=sh, ellipsis=el, adapt_codes=ad, height=ht, fits=True)

    if best is not None:
        h, r, g, w, sh, el, ad, ht = best
        codes = ad
        return commit(h, r, g, w, short=sh, ellipsis=el, adapt_codes=ad, height=ht, fits=False)

    return False, codes, 10**9


def _record_table_adaptations(
    sp: SurfacePlan, size: int, events: list[DiagnosticEvent]
) -> None:
    assert sp._table_spec is not None
    ok, codes, _h = _table_fit_detail(
        sp._table_spec, size, sp._box_w, sp._box_h
    )
    if not ok:
        return
    for code in codes:
        if code not in sp.adaptation_codes:
            sp.adaptation_codes.append(code)
        events.append(
            event(
                code=code,  # type: ignore[arg-type]
                severity="info",
                phase="plan",
                role=sp.role,
                path=f"/slides/{sp.slide_index}/{sp.role}",
                action="measure",
                result="accepted",
                slide_number=sp.slide_number,
                layout_type=sp.layout_type,
                surface_id=sp.surface_id,
            )
        )


def _apply_table_floor_adaptations(
    sp: SurfacePlan, size: int, events: list[DiagnosticEvent]
) -> None:
    """Non-strict path: still apply short/ellipsis at floor for complete paint (D25)."""
    assert sp._table_spec is not None
    # Commit best-effort display even when width/height overflow (fit returns False).
    _ok, codes, _h = _table_fit_detail(
        sp._table_spec, size, sp._box_w, 10**9, allow_short=True, allow_ellipsis=True
    )
    for code in codes:
        if code not in sp.adaptation_codes:
            sp.adaptation_codes.append(code)
        events.append(
            event(
                code=code,  # type: ignore[arg-type]
                severity="info",
                phase="plan",
                role=sp.role,
                path=f"/slides/{sp.slide_index}/{sp.role}",
                action="measure",
                result="accepted",
                slide_number=sp.slide_number,
                layout_type=sp.layout_type,
                surface_id=sp.surface_id,
            )
        )
