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

KERNEL_TABLE_LAYOUTS = frozenset(
    {
        "data_table",
        "annex_table",
        "grouped_annex_table",
        "period_comparison",
        "comparison_cards",
    }
)
KERNEL_LINEAR_LAYOUTS = frozenset(
    {
        "process_flow",
        "timeline",
        "layered_architecture",
        "data_pipeline",
    }
)
KERNEL_RELATIONSHIP_LAYOUTS = frozenset(
    {
        "decision_tree",
        "feedback_loop",
        "hierarchy",
        "stakeholder_map",
        "quadrant_matrix",
    }
)

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
CHART_PANE_TITLE_PX: Final = 40
CHART_PANE_SUBTITLE_PX: Final = 22
CHART_PANE_PAD_Y: Final = 20
CHART_PANE_GAP: Final = 4
CHART_VIEW_MIN_H: Final = 252
_AXIS_CHART_ROLES: Final = frozenset(
    {
        "line_chart",
        "grouped_bar_chart",
        "horizontal_bar_chart",
        "waterfall_chart",
    }
)

# Adaptive floors / ceilings (D12/D14/D51/D59/D171/D172/D225/D288).
SUBTITLE_FLOOR: Final = 22
SUBTITLE_CEIL: Final = 26
BODY_FLOOR: Final = 22
BODY_CEIL: Final = 28
TAKEAWAY_FLOOR: Final = 22
TAKEAWAY_CEIL: Final = 28
TABLE_FLOOR: Final = 20  # D44 ordinary data_table / period / cards
TABLE_CEIL: Final = 24
HEATMAP_TABLE_FLOOR: Final = 18  # D44/D60/D246 heatmap
HEATMAP_TABLE_CEIL: Final = 24
ANNEX_TABLE_FLOOR: Final = 12  # D44 annex + grouped annex
ANNEX_TABLE_CEIL: Final = 24
METRIC_STRIP_FLOOR: Final = 14  # D265 support labels
METRIC_STRIP_CEIL: Final = 24
METRIC_STRIP_VALUE_PX: Final = 28  # fixed KPI display (not 70px hero)
METRIC_STRIP_GAP: Final = 16
METRIC_STRIP_PAD_Y: Final = 16
METRIC_STRIP_PAD_X: Final = 16
GROUPED_ANNEX_GAP: Final = 24  # divider gutter between peers
GROUPED_ANNEX_HEADING_PX: Final = 18
COMPARISON_CARD_GAP: Final = 16
COMPARISON_CARD_PAD: Final = 16
COMPARISON_CARD_HEADING_FLOOR: Final = 22
COMPARISON_CARD_LABEL_FLOOR: Final = 14
COMPARISON_CARD_VALUE_FLOOR: Final = 22
# D60 fixed first-delivery type for geometry-specialized linear/grouping comps.
LINEAR_HEADING_PX: Final = 22
LINEAR_DETAIL_PX: Final = 16
LINEAR_META_PX: Final = 14  # step numbers / time labels
LINEAR_GAP: Final = 16
LINEAR_CARD_PAD: Final = 16
LINEAR_CARD_MARGIN: Final = 4
LINEAR_CONNECTOR_H: Final = 24
LINEAR_INNER_GAP: Final = 8
LINEAR_LAYER_GAP: Final = 20
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
COVER_GAP_Y: Final = 12  # --space-sm between flex items
COVER_TITLE_MARGIN_Y: Final = 20  # --space-md
COVER_BAND_H: Final = 8
COVER_BAND_MARGIN_Y: Final = 28  # --space-lg
DIVIDER_META_MARGIN_Y: Final = 12  # --space-sm
DIVIDER_RULE_H: Final = 4
DIVIDER_RULE_MARGIN_Y: Final = 20  # --space-md
LEGAL_HEADING_MARGIN_Y: Final = 20  # --space-md
LEGAL_PART_MARGIN_Y: Final = 20  # --space-md
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
    # Linear/grouping composition measure + paint payload (D272–D277).
    _linear_spec: Optional[dict[str, Any]] = None
    # CSS white-space:pre-wrap surfaces preserve authored hard line breaks.
    _preserve_newlines: bool = False
    # Frozen paint input for data_table (public to painters; set at seal).
    table_paint: Optional[dict[str, Any]] = None
    # Frozen axis-chart plan (public to Chart.js + SVG painters; set at seal).
    _chart_spec: Optional[dict[str, Any]] = None
    _chart_visual: Any = None
    _chart_formats: Any = None
    chart_paint: Optional[dict[str, Any]] = None

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
        if self.chart_paint is not None:
            row["chart_type"] = self.chart_paint.get("chart_type")
        return row


@dataclass
class DeckPlan:
    surfaces: list[SurfacePlan]
    events: list[DiagnosticEvent] = field(default_factory=list)

    def public_plans(self) -> list[dict[str, Any]]:
        return [s.to_public() for s in self.surfaces]

    def by_surface_id(self) -> dict[str, SurfacePlan]:
        return {s.surface_id: s for s in self.surfaces}


def plan_deck(
    deck: Deck,
    *,
    strict: bool = True,
    uncolored_heatmap_surfaces: frozenset[str] | None = None,
    relationship_defect_slides: frozenset[int] | None = None,
) -> DeckPlan:
    """Measure every kernel surface, synchronize, freeze whole-pixel sizes (D69)."""
    surfaces = _collect_surfaces(
        deck,
        uncolored_heatmap_surfaces=uncolored_heatmap_surfaces or frozenset(),
        relationship_defect_slides=relationship_defect_slides or frozenset(),
    )
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
        # Grouped annex: one peer overflow replaces the whole composition (D185).
        grouped_slides = {
            s.slide_number
            for s in overflow
            if s.role == "grouped_annex_table"
        }
        if grouped_slides:
            for s in surfaces:
                if (
                    s.slide_number in grouped_slides
                    and s.role == "grouped_annex_table"
                ):
                    s._overflow = True
                    _apply_composition_fallback(s)
            overflow = [s for s in surfaces if s._overflow]
        for s in overflow:
            events.append(_overflow_event(s))
            if s.fallback is None:
                s.fallback = "fallback_unresolved"
            # Composition-specific complete-data fallbacks already set above.
            _apply_composition_fallback(s)

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


def _collect_surfaces(
    deck: Deck,
    *,
    uncolored_heatmap_surfaces: frozenset[str] = frozenset(),
    relationship_defect_slides: frozenset[int] = frozenset(),
) -> list[SurfacePlan]:
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
                    _margin_boxes=0,
                    _chrome_h=(
                        COVER_BAND_H
                        + COVER_BAND_MARGIN_Y
                        + COVER_TITLE_MARGIN_Y
                        + COVER_GAP_Y * len(cover_items)
                    ),
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
                    _margin_boxes=0,
                    _chrome_h=(
                        DIVIDER_META_MARGIN_Y
                        + DIVIDER_RULE_H
                        + DIVIDER_RULE_MARGIN_Y
                    ),
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
                    _margin_boxes=len(p.paragraphs),
                    _chrome_h=(
                        LEGAL_HEADING_MARGIN_Y
                        + (LEGAL_PART_MARGIN_Y if p.part > 1 else 0)
                    ),
                    _preserve_newlines=True,
                )
            )
            continue

        if (
            lt not in ("narrative", "single_chart")
            and lt not in KERNEL_TABLE_LAYOUTS
            and lt not in KERNEL_LINEAR_LAYOUTS
            and lt not in KERNEL_RELATIONSHIP_LAYOUTS
        ):
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
        # Annex variants forbid takeaway at the model layer (D258/D259).
        takeaway_plan: SurfacePlan | None = None
        takeaway = getattr(slide, "takeaway", None)
        if takeaway is not None:
            typo = takeaway.typography
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
                _text_items=[(takeaway.text, False)],
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
        elif lt == "grouped_annex_table":
            body_slots, body_plans = _collect_grouped_annex_body(
                slide, deck, sn, slide_index, lt, region
            )
            for bp in body_plans:
                out.append(bp)
                adaptive_surfaces.append(bp)
        elif lt == "comparison_cards":
            body_slots, body_plans = _collect_comparison_cards_body(
                slide, deck, sn, slide_index, lt, region
            )
            for bp in body_plans:
                out.append(bp)
                adaptive_surfaces.append(bp)
        elif lt in KERNEL_LINEAR_LAYOUTS:
            body_slots, body_plans = _collect_linear_body(
                slide, sn, slide_index, lt, region
            )
            for bp in body_plans:
                out.append(bp)
                adaptive_surfaces.append(bp)
        elif lt in KERNEL_RELATIONSHIP_LAYOUTS:
            body_slots, body_plans = _collect_relationship_body(
                slide,
                sn,
                slide_index,
                lt,
                region,
                structural_defect=sn in relationship_defect_slides,
            )
            for bp in body_plans:
                out.append(bp)
                adaptive_surfaces.append(bp)
        elif lt == "single_chart":
            # single_chart axis charts + heatmap (D239/D240/D243/D245/D246/D302/D307/D308).
            from .charts import freeze_chart, freeze_heatmap
            from .models import HeatmapVisual

            body_slots = 1
            chart = slide.payload.primary_visual
            if isinstance(chart, HeatmapVisual):
                chart_spec = freeze_heatmap(
                    chart,
                    deck.number_formats,
                    box_w=CONTENT_W,
                    table_floor=HEATMAP_TABLE_FLOOR,
                    colored=chart.surface_id not in uncolored_heatmap_surfaces,
                )
                # Heatmap is a native table: fit through table fitter (18–24px).
                table_spec = _heatmap_table_spec(chart_spec)
                text_items = [(t, False) for t in chart_spec["all_texts"]]
                role_sizes = {"table": HEATMAP_TABLE_FLOOR}
                if chart.heading:
                    role_sizes["pane_title"] = 40
                    if chart.subtitle:
                        role_sizes["pane_subtitle"] = 22
                out.append(
                    SurfacePlan(
                        surface_id=chart.surface_id,
                        role="heatmap",
                        slide_number=sn,
                        slide_index=slide_index,
                        layout_type=lt,
                        slot_order=10,
                        design_stage_region=region,
                        role_sizes=role_sizes,
                        _text_items=text_items,
                        _box_w=CONTENT_W,
                        _fit_role="table",
                        _mode="adaptive",
                        _margin_boxes=0,
                        _default_size=HEATMAP_TABLE_FLOOR,
                        _maximum_size=HEATMAP_TABLE_CEIL,
                        _chrome_h=_heatmap_chrome_height(chart_spec),
                        _table_spec=table_spec,
                        _chart_spec=chart_spec,
                        _chart_visual=chart,
                        _chart_formats=deck.number_formats,
                    )
                )
            else:
                chart_spec = freeze_chart(
                    chart,
                    deck.number_formats,
                    box_w=CONTENT_W,
                )
                text_items = _chart_text_items(chart_spec)
                role_sizes = dict(chart_spec["role_sizes"])
                # Pane title band is fixed chrome when authored (D9/D42).
                if chart.heading:
                    role_sizes["pane_title"] = 40
                    if chart.subtitle:
                        role_sizes["pane_subtitle"] = 22
                chart_role = {
                    "line": "line_chart",
                    "grouped_bar": "grouped_bar_chart",
                    "horizontal_bar": "horizontal_bar_chart",
                    "waterfall": "waterfall_chart",
                }.get(chart.chart_type, f"{chart.chart_type}_chart")
                out.append(
                    SurfacePlan(
                        surface_id=chart.surface_id,
                        role=chart_role,
                        slide_number=sn,
                        slide_index=slide_index,
                        layout_type=lt,
                        slot_order=10,
                        design_stage_region=region,
                        role_sizes=role_sizes,
                        display_identity_strategy=chart_spec["identity_strategy"],
                        expected_placement_classes=sorted(
                            {
                                p["class"]
                                for p in chart_spec["placements"]
                                if p.get("class") and p["class"] != "suppressed"
                            }
                        ),
                        _text_items=text_items,
                        _box_w=CONTENT_W,
                        _box_h=math.ceil(chart_spec["geometry"]["view_h"]),
                        _fit_role=None,  # sizes frozen inside chart planner
                        _mode=(
                            chart.typography.mode
                            if chart.typography is not None
                            else "adaptive"
                        ),
                        _margin_boxes=0,
                        _chrome_h=_chart_chrome_height(chart_spec),
                        _chart_spec=chart_spec,
                        _chart_visual=chart,
                        _chart_formats=deck.number_formats,
                    )
                )
            adaptive_surfaces.append(out[-1])
        else:
            # data_table / annex_table / period_comparison table surface(s).
            body_slots, body_plans = _collect_single_table_body(
                slide, deck, sn, slide_index, lt, region
            )
            for bp in body_plans:
                out.append(bp)
                adaptive_surfaces.append(bp)

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

    chart_targets = {
        sp.surface_id: sp._box_h
        for sp in surfaces
        if sp._chart_spec is not None and sp.role in _AXIS_CHART_ROLES
    }

    def need(sp: SurfacePlan, size: int) -> int:
        if sp._chart_spec is not None and sp.role in _AXIS_CHART_ROLES:
            return CHART_VIEW_MIN_H
        if sp._linear_spec is not None:
            ok, height = _linear_fit_detail(sp)
            return height if ok else 10**9
        if _is_rectangular_table_spec(sp._table_spec):
            assert sp._table_spec is not None
            if sp.role == "comparison_cards":
                ok, _ = _comparison_cards_fit_detail(sp, size)
                roles = (sp._table_spec or {}).get("card_role_sizes") or {}
                card_h = int(roles.get("card_h") or size * 6)
                rows = 2 if sp._table_spec.get("peer_count") == 4 else 1
                h = rows * card_h + (rows - 1) * COMPARISON_CARD_GAP
                return h if ok else 10**9
            ok, _, height = _table_fit_detail(sp._table_spec, size, sp._box_w, 10**9)
            return height if ok else 10**9
        if sp._table_spec is not None and sp._table_spec.get("kind") == "metric_strip":
            # Estimate from label size + fixed value + optional detail.
            metrics = sp._table_spec["metrics"]
            value_px = sp.role_sizes.get("value", METRIC_STRIP_VALUE_PX)
            h = 0
            for m in metrics:
                lab = max(1, len(_wrap_label_lines(m["label"], size, sp._box_w)))
                det = (
                    len(_wrap_label_lines(m["detail"], size, sp._box_w))
                    if m.get("detail")
                    else 0
                )
                h = max(h, lab * _line_box(size) + _line_box(value_px) + det * _line_box(size))
            return h
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
        wanted = chart_targets.get(
            sp.surface_id,
            need(sp, sp._maximum_size or next(iter(sp.role_sizes.values()))),
        )
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
        if sp._chart_spec is not None and sp.role in _AXIS_CHART_ROLES:
            from .charts import freeze_chart

            sp._chart_spec = freeze_chart(
                sp._chart_visual,
                sp._chart_formats,
                box_w=sp._box_w,
                box_h=height + 40,
            )
            sp._text_items = _chart_text_items(sp._chart_spec)
            sp.role_sizes.update(sp._chart_spec["role_sizes"])
            sp.display_identity_strategy = sp._chart_spec["identity_strategy"]
            sp.expected_placement_classes = sorted(
                {
                    p["class"]
                    for p in sp._chart_spec["placements"]
                    if p.get("class") and p["class"] != "suppressed"
                }
            )


# ---------------------------------------------------------------------------
# Measure
# ---------------------------------------------------------------------------


def _measure_surface(sp: SurfacePlan, events: list[DiagnosticEvent]) -> None:
    fit = sp._fit_role
    if sp._chart_spec is not None and sp.role in _AXIS_CHART_ROLES:
        if math.ceil(sp._chart_spec["geometry"]["view_h"]) > sp._box_h:
            sp._overflow = True
        return
    if fit is None:
        # Fixed chrome — measure each cover role at its own frozen size (R178-005).
        if sp._cover_items:
            if not _cover_fits(sp):
                sp._overflow = True
            return
        if sp._linear_spec is not None:
            ok, _h = _linear_fit_detail(sp)
            if not ok:
                sp._overflow = True
                _apply_composition_fallback(sp)
            return
        px = next(iter(sp.role_sizes.values()))
        if not _text_fits(
            sp._text_items, px, sp._box_w, sp._box_h, margin_boxes=sp._margin_boxes, indent_em=sp._indent_em, unit_indent_ems=sp._unit_indent_ems
        ):
            sp._overflow = True
        return

    floor = sp._default_size if sp._default_size is not None else sp.role_sizes[fit]
    ceil_map = {
        "subtitle": SUBTITLE_CEIL,
        "body": BODY_CEIL,
        "table": TABLE_CEIL,
        "label": METRIC_STRIP_CEIL,
    }
    ceil = (
        sp._maximum_size
        if sp._maximum_size is not None
        else ceil_map.get(fit, BODY_CEIL)
    )
    if fit == "body" and sp.role == "takeaway":
        floor, ceil = TAKEAWAY_FLOOR, TAKEAWAY_CEIL
        sp.role_sizes[fit] = floor
    # Keep role_sizes[fit] at floor before grow so pins/overflow share one baseline.
    if fit in sp.role_sizes and sp.role != "takeaway":
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
        return _surface_fits_detail(sp, size)

    if sp._mode == "fixed":
        size = sp._explicit_size if sp._explicit_size is not None else floor
        sp.role_sizes[fit] = size
        ok, _ = _fits(size)
        if not ok:
            sp._overflow = True
            _apply_surface_floor_adaptations(sp, size, events)
        else:
            _record_surface_adaptations(sp, size, events)
        _finalize_composition_roles(sp, size)
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
            _apply_surface_floor_adaptations(sp, size, events)
        else:
            _record_surface_adaptations(sp, size, events)
        _finalize_composition_roles(sp, size)
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
        _apply_surface_floor_adaptations(sp, chosen, events)

    sp.role_sizes[fit] = chosen
    if chosen > floor:
        sp.adaptation_codes.append("plan.typography_grown")
    if not sp._overflow:
        _record_surface_adaptations(sp, chosen, events)
    elif wrapped and "plan.text_wrapped" not in sp.adaptation_codes:
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
    _finalize_composition_roles(sp, chosen)
    _apply_composition_fallback(sp)


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
    """Measure each fixed element and its renderer-owned chrome."""
    need_h = sp._chrome_h
    for text_c, role_key in sp._cover_items:
        px = sp.role_sizes[role_key]
        strong = role_key == "title"
        hard_lines = text_c.split("\n") if sp._preserve_newlines else [text_c]
        for hard_line in hard_lines:
            lines, wo = _wrap_lines([(hard_line, strong)], px, sp._box_w)
            if wo:
                return False
            need_h += max(1, len(lines)) * _line_box(px)
    return need_h + sp._margin_boxes * BLOCK_MARGIN_Y <= sp._box_h


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
        # Bound at the max member floor so no member freezes below its own
        # documented fit range (D44).
        member_floors = [
            m._default_size if m._default_size is not None else m.role_sizes[fit]
            for m in members
        ]
        role_floor = max(member_floors)
        # Start from min of independently chosen sizes, then try grow to max
        # of those if all fit — D3: largest that safely fits every member.
        independent = [m.role_sizes[fit] for m in members]
        target = max(min(independent), role_floor)
        upper = max(independent)

        def _sync_member_fits(m: SurfacePlan, size: int) -> bool:
            ok, _ = _surface_fits_detail(m, size)
            return ok

        for size in range(upper, role_floor - 1, -1):
            if all(_sync_member_fits(m, size) for m in members):
                target = size
                break
        changed = False
        for m, m_floor in zip(members, member_floors):
            if m.role_sizes[fit] != target:
                changed = True
            m.role_sizes[fit] = target
            # Drop grow code only when frozen size is the member's own floor.
            if target == m_floor:
                m.adaptation_codes = [
                    c for c in m.adaptation_codes if c != "plan.typography_grown"
                ]
            elif "plan.typography_grown" not in m.adaptation_codes and target > m_floor:
                m.adaptation_codes.append("plan.typography_grown")
            # Table paint must match the frozen synchronized size (D69/D70).
            if m._table_spec is not None:
                ok, codes_wrapped = _surface_fits_detail(m, target)
                if ok:
                    m._overflow = False
                    _record_surface_adaptations(m, target, events)
                    _finalize_composition_roles(m, target)
                else:
                    m._overflow = True
                    _apply_surface_floor_adaptations(m, target, events)
                    _apply_composition_fallback(m)
                _ = codes_wrapped
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
        frozen_table = dict(sp._table_spec)
        # Heatmap: merge fitted labels/widths into chart_paint (sole paint input).
        heat_src = frozen_table.pop("_heatmap_chart_spec", None)
        sp.table_paint = frozen_table
        if heat_src is not None and sp._chart_spec is not None:
            sp._chart_spec = dict(sp._chart_spec)
            sp._chart_spec["display_headers"] = list(
                frozen_table.get("display_headers") or heat_src["display_headers"]
            )
            sp._chart_spec["display_row_labels"] = list(
                frozen_table.get("display_row_labels") or heat_src["display_row_labels"]
            )
            sp._chart_spec["col_widths"] = list(
                frozen_table.get("col_widths") or []
            )
            sp._chart_spec["short_label_used"] = bool(
                frozen_table.get("short_label_used")
            )
            sp._chart_spec["ellipsized"] = bool(frozen_table.get("ellipsized"))
            sp._chart_spec["role_sizes"] = dict(sp.role_sizes)
            # Uncolored fallback when plan marked degraded (non-strict overflow).
            if sp.fallback == "uncolored_heatmap":
                sp._chart_spec["colored"] = False
                sp._chart_spec["scale"] = dict(sp._chart_spec.get("scale") or {})
                sp._chart_spec["scale"]["key_stops"] = []
                for row in sp._chart_spec["cells"]:
                    for cell in row:
                        cell["fill"] = None
                        cell["ink"] = None
    if sp._chart_spec is not None:
        sp.chart_paint = dict(sp._chart_spec)
        # Keep role_sizes aligned with sealed chart plan.
        for k, v in sp._chart_spec.get("role_sizes", {}).items():
            sp.role_sizes.setdefault(k, v)


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
# Composition body collectors (#180)
# ---------------------------------------------------------------------------


def _table_floor_ceil(lt: str) -> tuple[int, int]:
    if lt in ("annex_table", "grouped_annex_table"):
        return ANNEX_TABLE_FLOOR, ANNEX_TABLE_CEIL
    return TABLE_FLOOR, TABLE_CEIL


def _table_surface_plan(
    *,
    table: Any,
    deck: Deck,
    sn: int,
    slide_index: int,
    lt: str,
    region: int,
    slot_order: int,
    box_w: int,
    role: str,
    extra_spec: dict[str, Any] | None = None,
) -> SurfacePlan:
    floor, ceil = _table_floor_ceil(lt)
    table_typo = table.typography
    mode, sync, explicit = _typo_fields(table_typo, "table_font_size")
    table_spec = _build_table_spec(table, deck.number_formats)
    if extra_spec:
        table_spec.update(extra_spec)
    text_items = [(t, False) for t in table_spec["all_texts"]]
    return SurfacePlan(
        surface_id=table.surface_id,
        role=role,
        slide_number=sn,
        slide_index=slide_index,
        layout_type=lt,
        slot_order=slot_order,
        design_stage_region=region,
        role_sizes={"table": floor},
        _text_items=text_items,
        _box_w=box_w,
        _fit_role="table",
        _typo=table_typo,
        _mode=mode,
        _sync_group=sync,
        _explicit_size=explicit,
        _margin_boxes=0,
        _default_size=floor,
        _maximum_size=ceil,
        _table_spec=table_spec,
    )


def _collect_single_table_body(
    slide: Any,
    deck: Deck,
    sn: int,
    slide_index: int,
    lt: str,
    region: int,
) -> tuple[int, list[SurfacePlan]]:
    """data_table / annex_table / period_comparison body surfaces."""
    plans: list[SurfacePlan] = []
    table = slide.payload.table
    role = {
        "data_table": "data_table",
        "annex_table": "annex_table",
        "period_comparison": "period_comparison",
    }[lt]
    # Period comparison: reserve exterior metric strip above the table (D186).
    strip = getattr(slide.payload, "metric_strip", None)
    slot = 10
    if strip is not None:
        plans.append(
            _metric_strip_plan(
                strip,
                deck,
                sn=sn,
                slide_index=slide_index,
                lt=lt,
                region=region,
                slot_order=slot,
            )
        )
        slot += 1
    plans.append(
        _table_surface_plan(
            table=table,
            deck=deck,
            sn=sn,
            slide_index=slide_index,
            lt=lt,
            region=region,
            slot_order=slot,
            box_w=CONTENT_W,
            role=role,
            extra_spec={"variant": lt},
        )
    )
    return len(plans), plans


def _metric_strip_plan(
    strip: Any,
    deck: Deck,
    *,
    sn: int,
    slide_index: int,
    lt: str,
    region: int,
    slot_order: int,
) -> SurfacePlan:
    from .format import format_semantic_value

    typo = strip.typography
    mode, sync, explicit = _typo_fields(typo, "body_font_size")
    metrics = []
    texts: list[tuple[str, bool]] = []
    for m in strip.metrics:
        fv = format_semantic_value(m.value, deck.number_formats)
        metrics.append(
            {
                "metric_id": m.metric_id,
                "label": m.label,
                "detail": m.detail,
                "visible": fv.visible,
                "accessible": fv.accessible,
                "role": fv.role,
                "align": fv.align,
            }
        )
        texts.append((m.label, False))
        texts.append((fv.visible, True))
        if m.detail:
            texts.append((m.detail, False))
    n = max(1, len(metrics))
    cell_w = (CONTENT_W - METRIC_STRIP_GAP * (n - 1)) // n
    return SurfacePlan(
        surface_id=strip.surface_id,
        role="metric_strip",
        slide_number=sn,
        slide_index=slide_index,
        layout_type=lt,
        slot_order=slot_order,
        design_stage_region=region,
        role_sizes={
            "label": METRIC_STRIP_FLOOR,
            "value": METRIC_STRIP_VALUE_PX,
            "detail": METRIC_STRIP_FLOOR,
        },
        _text_items=texts,
        _box_w=cell_w - METRIC_STRIP_PAD_X,
        _fit_role="label",
        _typo=typo,
        _mode=mode,
        _sync_group=sync,
        _explicit_size=explicit,
        _margin_boxes=0,
        _chrome_h=METRIC_STRIP_PAD_Y + BLOCK_MARGIN_Y,
        _default_size=METRIC_STRIP_FLOOR,
        _maximum_size=METRIC_STRIP_CEIL,
        _table_spec={"kind": "metric_strip", "metrics": metrics, "n": n},
    )


def _collect_grouped_annex_body(
    slide: Any,
    deck: Deck,
    sn: int,
    slide_index: int,
    lt: str,
    region: int,
) -> tuple[int, list[SurfacePlan]]:
    peers = list(slide.payload.tables)
    n = len(peers)
    if n == 1:
        peer_w = CONTENT_W
    else:
        peer_w = (CONTENT_W - GROUPED_ANNEX_GAP) // 2
    # Shared sync so both peers freeze one common annex size (D185).
    plans: list[SurfacePlan] = []
    for i, peer in enumerate(peers):
        heading = peer.heading
        short = peer.short_heading or peer.heading
        # Prefer short heading only when full heading cannot fit (D259).
        full_h = _required_height([(heading, True)], GROUPED_ANNEX_HEADING_PX, peer_w, 1)
        short_h = _required_height([(short, True)], GROUPED_ANNEX_HEADING_PX, peer_w, 1)
        full_lines = _wrap_lines([(heading, True)], GROUPED_ANNEX_HEADING_PX, peer_w)[0]
        use_short = len(full_lines) > 2 and short != heading
        display_heading = short if use_short else heading
        heading_h = short_h if use_short else full_h
        sp = _table_surface_plan(
            table=peer.table,
            deck=deck,
            sn=sn,
            slide_index=slide_index,
            lt=lt,
            region=region,
            slot_order=10 + i,
            box_w=peer_w,
            role="grouped_annex_table",
            extra_spec={
                "variant": "grouped_annex_table",
                "peer_index": i,
                "peer_count": n,
                "heading_full": heading,
                "heading_short": short,
                "display_heading": display_heading,
                "heading_px": GROUPED_ANNEX_HEADING_PX,
            },
        )
        sp._chrome_h = heading_h + BLOCK_MARGIN_Y
        sp._text_items = [(heading, True), (short, True)] + sp._text_items
        # Equivalent annex peers share one common adaptive size (D185).
        if sp._mode == "adaptive" and sp._explicit_size is None:
            sp._sync_group = sp._sync_group or f"slide-{sn}-grouped-annex"
        plans.append(sp)
    return len(plans), plans


def _collect_comparison_cards_body(
    slide: Any,
    deck: Deck,
    sn: int,
    slide_index: int,
    lt: str,
    region: int,
) -> tuple[int, list[SurfacePlan]]:
    """One surface owns the peer table; paint derives card geometry (D187/D261)."""
    table = slide.payload.table
    n_peers = len(table.rows)
    cols = 2 if n_peers == 4 else n_peers
    card_w = (CONTENT_W - COMPARISON_CARD_GAP * (cols - 1)) // cols
    sp = _table_surface_plan(
        table=table,
        deck=deck,
        sn=sn,
        slide_index=slide_index,
        lt=lt,
        region=region,
        slot_order=10,
        box_w=card_w - 2 * COMPARISON_CARD_PAD,
        role="comparison_cards",
        extra_spec={
            "variant": "comparison_cards",
            "peer_count": n_peers,
            "grid_cols": cols,
            "card_w": card_w,
        },
    )
    # Multi-role fit: heading / label / value share grow decisions via table size
    # for the a11y table fallback path; card paint uses role_sizes below.
    sp.role_sizes = {
        "table": TABLE_FLOOR,  # fallback ordinary table size
        "heading": COMPARISON_CARD_HEADING_FLOOR,
        "label": COMPARISON_CARD_LABEL_FLOOR,
        "value": COMPARISON_CARD_VALUE_FLOOR,
    }
    sp._default_size = TABLE_FLOOR
    sp._maximum_size = TABLE_CEIL
    return 1, [sp]


def _collect_linear_body(
    slide: Any,
    sn: int,
    slide_index: int,
    lt: str,
    region: int,
) -> tuple[int, list[SurfacePlan]]:
    """One fixed-type surface for process/timeline/layers/pipeline (D272–D277)."""
    payload = slide.payload
    text_items: list[tuple[str, bool]] = []
    if lt == "process_flow":
        items = [
            {
                "id": s.step_id,
                "heading": s.heading,
                "detail": s.detail,
                "ordinal": i + 1,
            }
            for i, s in enumerate(payload.steps)
        ]
        for it in items:
            text_items.append((it["heading"], True))
            if it["detail"]:
                text_items.append((it["detail"], False))
        spec: dict[str, Any] = {
            "kind": "process_flow",
            "items": items,
            "orientation": "horizontal" if len(items) <= 4 else "vertical",
        }
        role = "process_flow"
        surface_id = f"slide-{sn}-process-flow"
    elif lt == "timeline":
        items = [
            {
                "id": m.milestone_id,
                "time_label": m.time_label,
                "heading": m.heading,
                "detail": m.detail,
            }
            for m in payload.milestones
        ]
        for it in items:
            text_items.append((it["time_label"], True))
            text_items.append((it["heading"], True))
            if it["detail"]:
                text_items.append((it["detail"], False))
        spec = {
            "kind": "timeline",
            "items": items,
            "orientation": "horizontal" if len(items) <= 4 else "vertical",
        }
        role = "timeline"
        surface_id = f"slide-{sn}-timeline"
    elif lt == "layered_architecture":
        layers = []
        for ly in payload.layers:
            comps = [
                {
                    "id": c.component_id,
                    "heading": c.heading,
                    "detail": c.detail,
                }
                for c in ly.components
            ]
            layers.append(
                {"id": ly.layer_id, "heading": ly.heading, "components": comps}
            )
            text_items.append((ly.heading, True))
            for c in comps:
                text_items.append((c["heading"], True))
                if c["detail"]:
                    text_items.append((c["detail"], False))
        spec = {"kind": "layered_architecture", "layers": layers}
        role = "layered_architecture"
        surface_id = f"slide-{sn}-layered-architecture"
    else:  # data_pipeline
        stages = []
        for st in payload.stages:
            comps = [
                {
                    "id": c.component_id,
                    "heading": c.heading,
                    "detail": c.detail,
                }
                for c in st.components
            ]
            stages.append(
                {
                    "id": st.stage_id,
                    "heading": st.heading,
                    "components": comps,
                    "transfer_label": st.transfer_label,
                }
            )
            text_items.append((st.heading, True))
            if st.transfer_label:
                text_items.append((st.transfer_label, False))
            for c in comps:
                text_items.append((c["heading"], True))
                if c["detail"]:
                    text_items.append((c["detail"], False))
        spec = {
            "kind": "data_pipeline",
            "stages": stages,
            "orientation": "horizontal" if len(stages) <= 4 else "vertical",
        }
        role = "data_pipeline"
        surface_id = f"slide-{sn}-data-pipeline"

    sp = SurfacePlan(
        surface_id=surface_id,
        role=role,
        slide_number=sn,
        slide_index=slide_index,
        layout_type=lt,
        slot_order=10,
        design_stage_region=region,
        role_sizes={
            "heading": LINEAR_HEADING_PX,
            "detail": LINEAR_DETAIL_PX,
            "meta": LINEAR_META_PX,
        },
        _text_items=text_items,
        _box_w=CONTENT_W,
        _fit_role=None,
        _mode="fixed",
        _margin_boxes=0,
        _default_size=LINEAR_HEADING_PX,
        _maximum_size=LINEAR_HEADING_PX,
        _linear_spec=spec,
    )
    return 1, [sp]


def _collect_relationship_body(
    slide: Any,
    sn: int,
    slide_index: int,
    lt: str,
    region: int,
    *,
    structural_defect: bool = False,
) -> tuple[int, list[SurfacePlan]]:
    """Fixed-type surface for decision/cycle/hierarchy/map/quadrant (D274–D280)."""
    payload = slide.payload
    text_items: list[tuple[str, bool]] = []
    if lt == "decision_tree":
        nodes = []
        for n in payload.nodes:
            branches = None
            if n.branches:
                branches = [
                    {"label": b.label, "target_id": b.target_id} for b in n.branches
                ]
            nodes.append(
                {
                    "id": n.node_id,
                    "kind": n.kind,
                    "heading": n.heading,
                    "detail": n.detail,
                    "branches": branches,
                }
            )
            text_items.append((n.heading, True))
            if n.detail:
                text_items.append((n.detail, False))
            if branches:
                for b in branches:
                    text_items.append((b["label"], False))
        spec: dict[str, Any] = {
            "kind": "decision_tree",
            "root_id": payload.root_id,
            "nodes": nodes,
            "structural_defect": structural_defect,
        }
        role = "decision_tree"
        surface_id = f"slide-{sn}-decision-tree"
    elif lt == "feedback_loop":
        items = []
        for it in payload.items:
            items.append(
                {
                    "id": it.item_id,
                    "heading": it.heading,
                    "detail": it.detail,
                    "effect": it.effect,
                    "relationship_label": it.relationship_label,
                }
            )
            text_items.append((it.heading, True))
            if it.detail:
                text_items.append((it.detail, False))
            if it.relationship_label:
                text_items.append((it.relationship_label, False))
        classification = payload.loop_classification
        if classification:
            text_items.append((classification, True))
        spec = {
            "kind": "feedback_loop",
            "loop_kind": payload.kind,
            "items": items,
            "classification": classification,
            "structural_defect": structural_defect,
        }
        role = "feedback_loop"
        surface_id = f"slide-{sn}-feedback-loop"
    elif lt == "hierarchy":
        nodes = []
        for n in payload.nodes:
            nodes.append(
                {
                    "id": n.node_id,
                    "heading": n.heading,
                    "detail": n.detail,
                    "children": list(n.children or []),
                }
            )
            text_items.append((n.heading, True))
            if n.detail:
                text_items.append((n.detail, False))
        text_items.append((payload.relationship, True))
        spec = {
            "kind": "hierarchy",
            "relationship": payload.relationship,
            "root_id": payload.root_id,
            "nodes": nodes,
            "structural_defect": structural_defect,
        }
        role = "hierarchy"
        surface_id = f"slide-{sn}-hierarchy"
    elif lt == "stakeholder_map":
        focal = {
            "id": payload.focal.entity_id,
            "heading": payload.focal.heading,
            "detail": payload.focal.detail,
        }
        text_items.append((focal["heading"], True))
        if focal["detail"]:
            text_items.append((focal["detail"], False))
        spokes = []
        for s in payload.stakeholders:
            spoke = {
                "id": s.entity_id,
                "heading": s.heading,
                "detail": s.detail,
                "relationship_label": s.relationship_label,
                "direction": s.direction,
            }
            spokes.append(spoke)
            text_items.append((spoke["heading"], True))
            text_items.append((spoke["relationship_label"], False))
            if spoke["detail"]:
                text_items.append((spoke["detail"], False))
        spec = {
            "kind": "stakeholder_map",
            "focal": focal,
            "stakeholders": spokes,
            "structural_defect": structural_defect,
        }
        role = "stakeholder_map"
        surface_id = f"slide-{sn}-stakeholder-map"
    else:  # quadrant_matrix
        x_axis = {
            "label": payload.x_axis.label,
            "low_label": payload.x_axis.low_label,
            "high_label": payload.x_axis.high_label,
        }
        y_axis = {
            "label": payload.y_axis.label,
            "low_label": payload.y_axis.low_label,
            "high_label": payload.y_axis.high_label,
        }
        for ax in (x_axis, y_axis):
            text_items.append((ax["label"], True))
            text_items.append((ax["low_label"], False))
            text_items.append((ax["high_label"], False))
        items = []
        for it in payload.items:
            items.append(
                {
                    "id": it.item_id,
                    "heading": it.heading,
                    "detail": it.detail,
                    "x_band": it.x_band,
                    "y_band": it.y_band,
                }
            )
            text_items.append((it.heading, True))
            if it.detail:
                text_items.append((it.detail, False))
        spec = {
            "kind": "quadrant_matrix",
            "x_axis": x_axis,
            "y_axis": y_axis,
            "items": items,
            "structural_defect": structural_defect,
        }
        role = "quadrant_matrix"
        surface_id = f"slide-{sn}-quadrant-matrix"

    sp = SurfacePlan(
        surface_id=surface_id,
        role=role,
        slide_number=sn,
        slide_index=slide_index,
        layout_type=lt,
        slot_order=10,
        design_stage_region=region,
        role_sizes={
            "heading": LINEAR_HEADING_PX,
            "detail": LINEAR_DETAIL_PX,
            "meta": LINEAR_META_PX,
        },
        _text_items=text_items,
        _box_w=CONTENT_W,
        _fit_role=None,
        _mode="fixed",
        _margin_boxes=0,
        _default_size=LINEAR_HEADING_PX,
        _maximum_size=LINEAR_HEADING_PX,
        _linear_spec=spec,
    )
    if structural_defect:
        # Force relationship-table paint path; never reconnect (D274/D278).
        sp.fallback = {
            "decision_tree": "accessible_relationship_table",
            "feedback_loop": "accessible_relationship_table",
            "hierarchy": "accessible_relationship_table",
            "stakeholder_map": "accessible_relationship_table",
            "quadrant_matrix": "accessible_four_group",
        }[role]
        spec["paint_as"] = "relationship_fallback"
    return 1, [sp]


# ---------------------------------------------------------------------------
# data_table measure (D24/D25/D44/D104)
# ---------------------------------------------------------------------------


def _chart_chrome_height(chart_spec: dict[str, Any]) -> int:
    height = BLOCK_MARGIN_Y
    if chart_spec.get("heading"):
        inner_w = CONTENT_W - 32
        height += CHART_PANE_PAD_Y + BLOCK_MARGIN_Y
        height += _required_height(
            [(chart_spec["heading"], True)], CHART_PANE_TITLE_PX, inner_w, 0
        )
        if chart_spec.get("subtitle"):
            height += CHART_PANE_GAP + _required_height(
                [(chart_spec["subtitle"], True)],
                CHART_PANE_SUBTITLE_PX,
                inner_w,
                0,
            )
    if chart_spec.get("identity_strategy") == "legend":
        px = chart_spec["role_sizes"]["legend"]
        rows = 1
        used = 0.0
        for series in chart_spec["series"]:
            width = _text_width(series["name"], px) + 52
            if used and used + width > CONTENT_W:
                rows += 1
                used = 0.0
            used += width
        height += rows * _line_box(px) + (rows - 1) * 16 + BLOCK_MARGIN_Y
    return height


def _heatmap_chrome_height(chart_spec: dict[str, Any]) -> int:
    """Pane title band only; scale key is part of the fitted table height."""
    height = BLOCK_MARGIN_Y
    if chart_spec.get("heading"):
        inner_w = CONTENT_W - 32
        height += CHART_PANE_PAD_Y + BLOCK_MARGIN_Y
        height += _required_height(
            [(chart_spec["heading"], True)], CHART_PANE_TITLE_PX, inner_w, 0
        )
        if chart_spec.get("subtitle"):
            height += CHART_PANE_GAP + _required_height(
                [(chart_spec["subtitle"], True)],
                CHART_PANE_SUBTITLE_PX,
                inner_w,
                0,
            )
    return height


def _heatmap_table_spec(chart_spec: dict[str, Any]) -> dict[str, Any]:
    """Adapt freeze_heatmap payload to the shared rectangular table fitter."""
    n_cols = chart_spec["n_cols"]
    n_rows = chart_spec["n_rows"]
    cells_vis = chart_spec["cells_vis"]
    cells_acc = chart_spec["cells_acc"]
    cells_role = [
        [("missing" if c["missing"] else "number") for c in row]
        for row in chart_spec["cells"]
    ]
    cells_align = [["right"] * n_cols for _ in range(n_rows)]
    # Scale key height: one line when colored stops exist.
    scale_labels: list[str] = []
    if chart_spec.get("colored") and (chart_spec.get("scale") or {}).get("key_stops"):
        scale_labels.append("heatmap-scale-key")
    return {
        "kind": "heatmap",
        "paint_as": "heatmap",
        "col_ids": list(chart_spec["col_ids"]),
        "n_cols": n_cols,
        "n_rows": n_rows,
        "header_full": list(chart_spec["header_full"]),
        "header_short": list(chart_spec["header_short"]),
        "row_labels_full": list(chart_spec["row_labels_full"]),
        "row_labels_short": list(chart_spec["row_labels_short"]),
        "cells_vis": cells_vis,
        "cells_acc": cells_acc,
        "cells_role": cells_role,
        "cells_align": cells_align,
        "col_aligns": ["right"] * n_cols,
        "groups": None,
        "scale_labels": scale_labels,
        "all_texts": list(chart_spec["all_texts"]),
        "display_headers": list(chart_spec["display_headers"]),
        "display_row_labels": list(chart_spec["display_row_labels"]),
        "display_groups": None,
        "col_widths": list(chart_spec.get("col_widths") or []),
        "ellipsized": False,
        "short_label_used": False,
        # Keep a back-pointer so seal can merge fitted labels into chart_paint.
        "_heatmap_chart_spec": chart_spec,
    }


def _chart_text_items(chart_spec: dict[str, Any]) -> list[tuple[str, bool]]:
    """Digest inputs for chart surfaces (labels + formatted values)."""
    items: list[tuple[str, bool]] = []
    if chart_spec.get("heading"):
        items.append((chart_spec["heading"], True))
    if chart_spec.get("subtitle"):
        items.append((chart_spec["subtitle"], False))
    for cat in chart_spec.get("categories") or []:
        items.append((cat["label"], False))
    for s in chart_spec.get("series") or []:
        items.append((s["name"], False))
    for p in chart_spec.get("points") or []:
        if p.get("visible"):
            items.append((p["visible"], False))
    return items


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


def _is_rectangular_table_spec(spec: dict[str, Any] | None) -> bool:
    return bool(spec) and spec.get("kind") != "metric_strip" and "col_ids" in (spec or {})


def _surface_fits_detail(sp: SurfacePlan, size: int) -> tuple[bool, bool]:
    """Return (fits, wrapped) for table / metric_strip / prose surfaces."""
    if sp._linear_spec is not None:
        ok, _h = _linear_fit_detail(sp)
        return ok, False
    spec = sp._table_spec
    if _is_rectangular_table_spec(spec):
        assert spec is not None
        if sp.role == "comparison_cards":
            return _comparison_cards_fit_detail(sp, size)
        ok, codes, _h = _table_fit_detail(spec, size, sp._box_w, sp._box_h)
        return ok, "plan.text_wrapped" in codes
    if spec is not None and spec.get("kind") == "metric_strip":
        return _metric_strip_fit_detail(sp, size)
    return _text_fits_detail(
        sp._text_items,
        size,
        sp._box_w,
        sp._box_h,
        margin_boxes=sp._margin_boxes,
        indent_em=sp._indent_em,
        unit_indent_ems=sp._unit_indent_ems,
    )


def _metric_strip_fit_detail(sp: SurfacePlan, size: int) -> tuple[bool, bool]:
    """Labels/details share adaptive size; values stay fixed KPI (D265)."""
    assert sp._table_spec is not None
    metrics = sp._table_spec["metrics"]
    cell_w = sp._box_w
    value_px = sp.role_sizes.get("value", METRIC_STRIP_VALUE_PX)
    wrapped = False
    # Two label lines + value + optional two detail lines + pads.
    total_h = METRIC_STRIP_PAD_Y
    for m in metrics:
        lab_lines = _wrap_label_lines(m["label"], size, cell_w)
        if len(lab_lines) > 2:
            return False, True
        if len(lab_lines) > 1:
            wrapped = True
        total_h = max(
            total_h,
            METRIC_STRIP_PAD_Y
            + len(lab_lines) * _line_box(size)
            + _line_box(value_px)
            + (
                len(_wrap_label_lines(m["detail"], size, cell_w)) * _line_box(size)
                if m.get("detail")
                else 0
            )
            + BLOCK_MARGIN_Y,
        )
        if m.get("detail"):
            d_lines = _wrap_label_lines(m["detail"], size, cell_w)
            if len(d_lines) > 2:
                return False, True
            if len(d_lines) > 1:
                wrapped = True
        if _text_width(m["visible"], value_px, strong=True) > cell_w:
            return False, wrapped
    fits = total_h <= sp._box_h + sp._chrome_h if sp._box_h else True
    # Height is allocated via chrome + fit box; when box_h still 0 pre-allocate, allow.
    if sp._box_h <= 0:
        fits = True
    else:
        # Recompute height into the text box only (chrome already reserved).
        text_h = total_h - METRIC_STRIP_PAD_Y - BLOCK_MARGIN_Y
        fits = text_h <= sp._box_h and not any(
            _text_width(m["visible"], value_px, strong=True) > cell_w for m in metrics
        )
    return fits, wrapped


def _linear_lines(
    text: str, px: int, inner_w: int, *, strong: bool = False, max_lines: int = 3
) -> tuple[list[str], bool]:
    """Wrap label; False when unbreakable overflow or too many lines for fixed chrome."""
    lines = _wrap_label_lines(text, px, inner_w, strong=strong)
    if not lines:
        return lines, True
    if any(_text_width(line, px, strong=strong) > inner_w for line in lines):
        return lines, False
    if len(lines) > max_lines:
        return lines, False
    return lines, True


def _linear_fit_detail(sp: SurfacePlan) -> tuple[bool, int]:
    """Fixed D60 geometry fit for linear + relationship compositions."""
    assert sp._linear_spec is not None
    spec = sp._linear_spec
    kind = spec["kind"]
    heading_px = sp.role_sizes.get("heading", LINEAR_HEADING_PX)
    detail_px = sp.role_sizes.get("detail", LINEAR_DETAIL_PX)
    meta_px = sp.role_sizes.get("meta", LINEAR_META_PX)
    box_w = sp._box_w
    box_h = sp._box_h if sp._box_h > 0 else 10**9
    ok = True

    if kind in KERNEL_RELATIONSHIP_LAYOUTS:
        return _relationship_fit_detail(sp)

    if kind in ("process_flow", "timeline"):
        items = spec["items"]
        n = len(items)
        orientation = spec.get("orientation", "horizontal")
        if orientation == "horizontal":
            col_w = max(
                40,
                (
                    box_w
                    - 2 * LINEAR_GAP * (n - 1)
                    - LINEAR_CONNECTOR_H * (n - 1)
                )
                // n,
            )
            heights = []
            for it in items:
                meta = (
                    str(it.get("ordinal", ""))
                    if kind == "process_flow"
                    else it.get("time_label")
                )
                inner_w = max(40, col_w - 2 * LINEAR_CARD_PAD)
                h = LINEAR_CARD_PAD
                if meta:
                    lines, fit = _linear_lines(
                        str(meta), meta_px, inner_w, strong=True, max_lines=2
                    )
                    ok = ok and fit
                    h += len(lines) * _line_box(meta_px)
                lines, fit = _linear_lines(
                    it["heading"], heading_px, inner_w, strong=True, max_lines=3
                )
                ok = ok and fit
                h += len(lines) * _line_box(heading_px)
                if it.get("detail"):
                    lines, fit = _linear_lines(
                        it["detail"], detail_px, inner_w, max_lines=4
                    )
                    ok = ok and fit
                    h += len(lines) * _line_box(detail_px)
                h += LINEAR_CARD_PAD + 2 * LINEAR_CARD_MARGIN
                heights.append(h)
            total = max(heights) + LINEAR_CONNECTOR_H + BLOCK_MARGIN_Y
        else:
            total = 0
            for it in items:
                meta = (
                    str(it.get("ordinal", ""))
                    if kind == "process_flow"
                    else it.get("time_label")
                )
                inner_w = max(40, box_w - 2 * LINEAR_CARD_PAD)
                h = LINEAR_CARD_PAD
                if meta:
                    lines, fit = _linear_lines(
                        str(meta), meta_px, inner_w, strong=True, max_lines=2
                    )
                    ok = ok and fit
                    h += len(lines) * _line_box(meta_px)
                lines, fit = _linear_lines(
                    it["heading"], heading_px, inner_w, strong=True, max_lines=3
                )
                ok = ok and fit
                h += len(lines) * _line_box(heading_px)
                if it.get("detail"):
                    lines, fit = _linear_lines(
                        it["detail"], detail_px, inner_w, max_lines=4
                    )
                    ok = ok and fit
                    h += len(lines) * _line_box(detail_px)
                h += (
                    LINEAR_CARD_PAD
                    + 2 * LINEAR_CARD_MARGIN
                    + LINEAR_CONNECTOR_H
                    + 2 * LINEAR_GAP
                )
                total += h
            total = total - LINEAR_CONNECTOR_H - 2 * LINEAR_GAP + BLOCK_MARGIN_Y
        if not ok:
            return False, 10**9
        return total <= box_h, total

    if kind == "layered_architecture":
        total = 0
        for layer in spec["layers"]:
            comps = layer["components"]
            n = max(1, len(comps))
            col_w = max(40, (box_w - LINEAR_GAP * (n - 1)) // n)
            lines, fit = _linear_lines(
                layer["heading"], heading_px, box_w, strong=True, max_lines=2
            )
            ok = ok and fit
            layer_h = len(lines) * _line_box(heading_px) + LINEAR_INNER_GAP
            comp_heights = []
            for c in comps:
                inner_w = max(40, col_w - 2 * LINEAR_CARD_PAD)
                ch = LINEAR_CARD_PAD
                lines, fit = _linear_lines(
                    c["heading"], heading_px, inner_w, strong=True, max_lines=3
                )
                ok = ok and fit
                ch += len(lines) * _line_box(heading_px) + LINEAR_CARD_MARGIN
                if c.get("detail"):
                    lines, fit = _linear_lines(
                        c["detail"], detail_px, inner_w, max_lines=4
                    )
                    ok = ok and fit
                    ch += len(lines) * _line_box(detail_px)
                ch += LINEAR_CARD_PAD
                comp_heights.append(ch)
            layer_h += max(comp_heights) if comp_heights else 0
            total += layer_h + LINEAR_LAYER_GAP
        total = total - LINEAR_LAYER_GAP + BLOCK_MARGIN_Y
        if not ok:
            return False, 10**9
        return total <= box_h, total

    # data_pipeline
    stages = spec["stages"]
    n = len(stages)
    orientation = spec.get("orientation", "horizontal")
    if orientation == "horizontal":
        col_w = max(
            40,
            (
                box_w
                - 2 * LINEAR_GAP * (n - 1)
                - LINEAR_CONNECTOR_H * (n - 1)
            )
            // n,
        )
        heights = []
        inner_w = max(40, col_w - 2 * LINEAR_CARD_PAD)
        for i, st in enumerate(stages):
            lines, fit = _linear_lines(
                st["heading"], heading_px, col_w, strong=True, max_lines=3
            )
            ok = ok and fit
            h = (
                len(lines) * _line_box(heading_px)
                + LINEAR_CARD_MARGIN
                + LINEAR_INNER_GAP
            )
            for c in st["components"]:
                lines, fit = _linear_lines(
                    c["heading"], detail_px, inner_w, strong=True, max_lines=3
                )
                ok = ok and fit
                h += (
                    2 * LINEAR_CARD_PAD
                    + LINEAR_CARD_MARGIN
                    + len(lines) * _line_box(detail_px)
                )
                if c.get("detail"):
                    lines, fit = _linear_lines(
                        c["detail"], detail_px, inner_w, max_lines=3
                    )
                    ok = ok and fit
                    h += len(lines) * _line_box(detail_px)
            h += LINEAR_INNER_GAP * max(0, len(st["components"]) - 1)
            if st.get("transfer_label"):
                nxt = stages[i + 1]["heading"] if i + 1 < n else ""
                lines, fit = _linear_lines(
                    f"{st['heading']} to {nxt}: {st['transfer_label']}",
                    meta_px,
                    col_w,
                    max_lines=2,
                )
                ok = ok and fit
                h += (
                    LINEAR_INNER_GAP
                    + LINEAR_CARD_MARGIN
                    + len(lines) * _line_box(meta_px)
                )
            heights.append(h)
        total = max(heights) + BLOCK_MARGIN_Y
    else:
        total = 0
        inner_w = max(40, box_w - 2 * LINEAR_CARD_PAD)
        for i, st in enumerate(stages):
            lines, fit = _linear_lines(
                st["heading"], heading_px, box_w, strong=True, max_lines=3
            )
            ok = ok and fit
            h = (
                len(lines) * _line_box(heading_px)
                + LINEAR_CARD_MARGIN
                + LINEAR_INNER_GAP
            )
            for c in st["components"]:
                lines, fit = _linear_lines(
                    c["heading"], detail_px, inner_w, strong=True, max_lines=3
                )
                ok = ok and fit
                h += (
                    2 * LINEAR_CARD_PAD
                    + LINEAR_CARD_MARGIN
                    + len(lines) * _line_box(detail_px)
                )
                if c.get("detail"):
                    lines, fit = _linear_lines(
                        c["detail"], detail_px, inner_w, max_lines=3
                    )
                    ok = ok and fit
                    h += len(lines) * _line_box(detail_px)
            h += LINEAR_INNER_GAP * max(0, len(st["components"]) - 1)
            if st.get("transfer_label"):
                nxt = stages[i + 1]["heading"] if i + 1 < n else ""
                lines, fit = _linear_lines(
                    f"{st['heading']} to {nxt}: {st['transfer_label']}",
                    meta_px,
                    box_w,
                    max_lines=2,
                )
                ok = ok and fit
                h += (
                    LINEAR_INNER_GAP
                    + LINEAR_CARD_MARGIN
                    + len(lines) * _line_box(meta_px)
                )
            h += LINEAR_CONNECTOR_H + 2 * LINEAR_GAP
            total += h
        total = total - LINEAR_CONNECTOR_H - 2 * LINEAR_GAP + BLOCK_MARGIN_Y
    if not ok:
        return False, 10**9
    return total <= box_h, total


def _relationship_fit_detail(sp: SurfacePlan) -> tuple[bool, int]:
    """Conservative fixed D60 height budget for relationship compositions."""
    assert sp._linear_spec is not None
    spec = sp._linear_spec
    kind = spec["kind"]
    heading_px = sp.role_sizes.get("heading", LINEAR_HEADING_PX)
    detail_px = sp.role_sizes.get("detail", LINEAR_DETAIL_PX)
    meta_px = sp.role_sizes.get("meta", LINEAR_META_PX)
    box_w = sp._box_w
    box_h = sp._box_h if sp._box_h > 0 else 10**9
    ok = True
    # Structural defects always take the accessible fallback path.
    if spec.get("structural_defect") or spec.get("paint_as") == "relationship_fallback":
        return True, min(box_h, 400)

    def card_h(heading: str, detail: str | None, *, meta: str | None = None) -> int:
        nonlocal ok
        inner = max(40, box_w // 3 - 2 * LINEAR_CARD_PAD)
        h = 2 * LINEAR_CARD_PAD
        if meta:
            lines, fit = _linear_lines(meta, meta_px, inner, strong=True, max_lines=2)
            ok = ok and fit
            h += len(lines) * _line_box(meta_px) + LINEAR_CARD_MARGIN
        lines, fit = _linear_lines(heading, heading_px, inner, strong=True, max_lines=3)
        ok = ok and fit
        h += len(lines) * _line_box(heading_px) + LINEAR_CARD_MARGIN
        if detail:
            lines, fit = _linear_lines(detail, detail_px, inner, max_lines=3)
            ok = ok and fit
            h += len(lines) * _line_box(detail_px)
        return h

    if kind == "decision_tree":
        nodes = spec["nodes"]
        # Depth-banded layout: up to 4 rows of cards.
        row_h = max(card_h(n["heading"], n.get("detail"), meta=n["kind"]) for n in nodes)
        # Estimate depth from node count (conservative 4 bands).
        bands = min(4, max(2, (len(nodes) + 2) // 3))
        total = bands * row_h + (bands - 1) * LINEAR_LAYER_GAP + BLOCK_MARGIN_Y
    elif kind == "feedback_loop":
        items = spec["items"]
        n = len(items)
        col_w = max(40, (box_w - LINEAR_GAP * n) // max(1, n))
        heights = []
        for it in items:
            meta = it.get("effect") or it.get("relationship_label")
            inner = max(40, col_w - 2 * LINEAR_CARD_PAD)
            h = 2 * LINEAR_CARD_PAD
            if meta:
                lines, fit = _linear_lines(str(meta), meta_px, inner, max_lines=2)
                ok = ok and fit
                h += len(lines) * _line_box(meta_px) + LINEAR_CARD_MARGIN
            lines, fit = _linear_lines(
                it["heading"], heading_px, inner, strong=True, max_lines=3
            )
            ok = ok and fit
            h += len(lines) * _line_box(heading_px)
            if it.get("detail"):
                lines, fit = _linear_lines(it["detail"], detail_px, inner, max_lines=3)
                ok = ok and fit
                h += len(lines) * _line_box(detail_px)
            heights.append(h)
        total = max(heights) + 2 * LINEAR_CONNECTOR_H + BLOCK_MARGIN_Y
        if spec.get("classification"):
            lines, fit = _linear_lines(
                str(spec["classification"]), meta_px, box_w, strong=True, max_lines=1
            )
            ok = ok and fit
            total += len(lines) * _line_box(meta_px) + LINEAR_GAP
    elif kind == "hierarchy":
        nodes = spec["nodes"]
        row_h = max(card_h(n["heading"], n.get("detail")) for n in nodes)
        bands = min(4, max(2, (len(nodes) + 1) // 2))
        total = (
            bands * row_h
            + (bands - 1) * LINEAR_LAYER_GAP
            + _line_box(meta_px)
            + BLOCK_MARGIN_Y
        )
        lines, fit = _linear_lines(
            str(spec["relationship"]), meta_px, box_w, strong=True, max_lines=1
        )
        ok = ok and fit
    elif kind == "stakeholder_map":
        focal = spec["focal"]
        spokes = spec["stakeholders"]
        hub = card_h(focal["heading"], focal.get("detail"), meta="focal")
        spoke_h = max(
            card_h(
                s["heading"],
                s.get("detail"),
                meta=f'{s["relationship_label"]} ({s["direction"]})',
            )
            for s in spokes
        )
        total = hub + spoke_h + 2 * LINEAR_LAYER_GAP + BLOCK_MARGIN_Y
    else:  # quadrant_matrix
        items = spec["items"]
        # 2x2 grid; within-quadrant stack preserves order.
        by_q: dict[tuple[str, str], list] = {
            ("low", "high"): [],
            ("high", "high"): [],
            ("low", "low"): [],
            ("high", "low"): [],
        }
        for it in items:
            by_q[(it["x_band"], it["y_band"])].append(it)
        cell_w = max(40, (box_w - LINEAR_GAP) // 2)
        inner = max(40, cell_w - 2 * LINEAR_CARD_PAD)

        def quad_h(group: list) -> int:
            nonlocal ok
            h = _line_box(meta_px) + LINEAR_INNER_GAP
            if not group:
                return h + LINEAR_CARD_PAD
            for it in group:
                ch = 2 * LINEAR_CARD_PAD
                lines, fit = _linear_lines(
                    it["heading"], heading_px, inner, strong=True, max_lines=3
                )
                ok = ok and fit
                ch += len(lines) * _line_box(heading_px)
                if it.get("detail"):
                    lines, fit = _linear_lines(
                        it["detail"], detail_px, inner, max_lines=2
                    )
                    ok = ok and fit
                    ch += len(lines) * _line_box(detail_px)
                h += ch + LINEAR_INNER_GAP
            return h

        top = max(quad_h(by_q[("low", "high")]), quad_h(by_q[("high", "high")]))
        bot = max(quad_h(by_q[("low", "low")]), quad_h(by_q[("high", "low")]))
        axis_h = 2 * _line_box(meta_px) + LINEAR_GAP
        total = top + bot + axis_h + LINEAR_GAP + BLOCK_MARGIN_Y

    if not ok:
        return False, 10**9
    return total <= box_h, total


def _comparison_cards_fit_detail(sp: SurfacePlan, size: int) -> tuple[bool, bool]:
    """Fit peer cards; size drives ordinary-table fallback floor simultaneously."""
    assert sp._table_spec is not None
    spec = sp._table_spec
    card_w = sp._box_w
    heading_px = max(COMPARISON_CARD_HEADING_FLOOR, min(size + 2, 28))
    label_px = max(COMPARISON_CARD_LABEL_FLOOR, min(size - 6, 20))
    value_px = max(COMPARISON_CARD_VALUE_FLOOR, min(size, 28))
    n_peers = spec["peer_count"]
    cols = spec["grid_cols"]
    rows_of_cards = 2 if n_peers == 4 else 1
    # Measure one card height from tallest peer.
    max_card_h = 0
    wrapped = False
    for r_i, row_lab in enumerate(spec["row_labels_full"]):
        h_lines = _wrap_label_lines(row_lab, heading_px, card_w, strong=True)
        if len(h_lines) > 2:
            return False, True
        if len(h_lines) > 1:
            wrapped = True
        h = len(h_lines) * _line_box(heading_px) + COMPARISON_CARD_PAD
        for c_i, col_lab in enumerate(spec["header_full"][1:]):
            l_lines = _wrap_label_lines(col_lab, label_px, card_w)
            if len(l_lines) > 2:
                return False, True
            if len(l_lines) > 1:
                wrapped = True
            val = spec["cells_vis"][r_i][c_i]
            if _text_width(val, value_px) > card_w:
                return False, wrapped
            h += len(l_lines) * _line_box(label_px) + _line_box(value_px) + 8
        max_card_h = max(max_card_h, h + COMPARISON_CARD_PAD)
    total_h = rows_of_cards * max_card_h + (rows_of_cards - 1) * COMPARISON_CARD_GAP
    fits = total_h <= sp._box_h if sp._box_h > 0 else True
    # Stash card role sizes for paint when this size wins.
    if fits or sp._box_h <= 0:
        spec["card_role_sizes"] = {
            "heading": heading_px,
            "label": label_px,
            "value": value_px,
            "card_h": max_card_h,
        }
    return fits, wrapped


def _finalize_composition_roles(sp: SurfacePlan, size: int) -> None:
    """Propagate frozen multi-role sizes after the primary fit key is chosen."""
    if sp.role == "metric_strip":
        sp.role_sizes["label"] = size
        sp.role_sizes["detail"] = size
        sp.role_sizes.setdefault("value", METRIC_STRIP_VALUE_PX)
    elif sp.role == "comparison_cards" and sp._table_spec:
        roles = sp._table_spec.get("card_role_sizes") or {}
        if roles:
            sp.role_sizes["heading"] = roles["heading"]
            sp.role_sizes["label"] = roles["label"]
            sp.role_sizes["value"] = roles["value"]
        sp.role_sizes["table"] = size


def _apply_composition_fallback(sp: SurfacePlan) -> None:
    """Non-strict composition fallbacks preserve complete data (D185/D186/D187/D272–D277)."""
    if not sp._overflow:
        return
    if sp.role == "comparison_cards":
        sp.fallback = "ordinary_data_table"
        if sp._table_spec is not None:
            sp._table_spec["paint_as"] = "data_table"
            # Re-fit as full-width ordinary table for complete accessible paint.
            sp._box_w = CONTENT_W
            floor = TABLE_FLOOR
            _table_fit_detail(sp._table_spec, floor, CONTENT_W, 10**9)
            sp.role_sizes["table"] = floor
    elif sp.role == "period_comparison":
        sp.fallback = "ordinary_data_table"
        if sp._table_spec is not None:
            sp._table_spec["paint_as"] = "data_table"
            sp._table_spec["variant"] = "data_table"
    elif sp.role == "grouped_annex_table":
        sp.fallback = "sequential_flat_tables"
        if sp._table_spec is not None:
            sp._table_spec["paint_as"] = "sequential_annex"
            sp._box_w = CONTENT_W
            floor = ANNEX_TABLE_FLOOR
            _table_fit_detail(sp._table_spec, floor, CONTENT_W, 10**9)
            sp.role_sizes["table"] = floor
    elif sp.role == "heatmap":
        # D246/D308: keep complete uncolored semantic table at 18px floor.
        sp.fallback = "uncolored_heatmap"
        if sp._table_spec is not None:
            sp._table_spec["paint_as"] = "heatmap"
            sp._box_w = CONTENT_W
            floor = HEATMAP_TABLE_FLOOR
            _table_fit_detail(sp._table_spec, floor, CONTENT_W, 10**9)
            sp.role_sizes["table"] = floor
    elif sp.role in KERNEL_LINEAR_LAYOUTS and sp._linear_spec is not None:
        # Accessible ordered/nested list; omit connectors/geometry (D272–D277).
        fallback_by_role = {
            "process_flow": "accessible_ordered_list",
            "timeline": "accessible_chronological_list",
            "layered_architecture": "accessible_nested_outline",
            "data_pipeline": "accessible_ordered_flow",
        }
        sp.fallback = fallback_by_role[sp.role]
        sp._linear_spec["paint_as"] = "fallback_list"
    elif sp.role in KERNEL_RELATIONSHIP_LAYOUTS and sp._linear_spec is not None:
        # Valid-but-unfittable trees/maps → outline/list; defects already set.
        if sp._linear_spec.get("structural_defect"):
            return
        fallback_by_role = {
            "decision_tree": "accessible_nested_outline",
            "feedback_loop": "accessible_ordered_relationship_list",
            "hierarchy": "accessible_nested_outline",
            "stakeholder_map": "accessible_relationship_list",
            "quadrant_matrix": "accessible_four_group",
        }
        sp.fallback = fallback_by_role[sp.role]
        sp._linear_spec["paint_as"] = "relationship_fallback"


def _record_surface_adaptations(
    sp: SurfacePlan, size: int, events: list[DiagnosticEvent]
) -> None:
    if _is_rectangular_table_spec(sp._table_spec) and sp.role != "comparison_cards":
        _record_table_adaptations(sp, size, events)
        return
    ok, wrapped = _surface_fits_detail(sp, size)
    if ok and wrapped and "plan.text_wrapped" not in sp.adaptation_codes:
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


def _apply_surface_floor_adaptations(
    sp: SurfacePlan, size: int, events: list[DiagnosticEvent]
) -> None:
    if _is_rectangular_table_spec(sp._table_spec) and sp.role != "comparison_cards":
        _apply_table_floor_adaptations(sp, size, events)
        return
    # Metric strip / cards: still freeze display payload at floor.
    _surface_fits_detail(sp, size)
    _finalize_composition_roles(sp, size)


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
