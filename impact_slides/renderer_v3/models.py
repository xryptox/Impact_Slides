"""Schema-v1 typed deck model (D117–D224, D251, D268–D271 kernel subset).

This module is the single source of truth for the closed handoff contract.
JSON Schema is generated from these models (D121).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any, Literal, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from .ids import is_semantic_id

# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------

SemanticId = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9_-]{0,63}$"),
]
NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=False)]

# Canonical undecorated decimal: optional leading minus, digits, optional fraction.
_CANONICAL_DECIMAL = r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$"
CanonicalDecimal = Annotated[str, StringConstraints(pattern=_CANONICAL_DECIMAL)]

UnitKind = Literal["usd", "percent", "percentage_points", "basis_points"]

LAYOUT_TYPES = (
    "opening_cover",
    "section_divider",
    "closing_cover",
    "single_chart",
    "dual_chart",
    "chart_hero_dual",
    "data_table",
    "annex_table",
    "grouped_annex_table",
    "period_comparison",
    "comparison_cards",
    "metric_overview",
    "narrative",
    "legal_notice",
    "process_flow",
    "timeline",
    "decision_tree",
    "feedback_loop",
    "layered_architecture",
    "data_pipeline",
    "hierarchy",
    "stakeholder_map",
    "quadrant_matrix",
    "feature_cards",
    "quotation",
    "evidence_review",
    "risk_opportunity_review",
    "recommendation_case",
    "state_transition",
)
LayoutTypeName = Literal[
    "opening_cover",
    "section_divider",
    "closing_cover",
    "single_chart",
    "dual_chart",
    "chart_hero_dual",
    "data_table",
    "annex_table",
    "grouped_annex_table",
    "period_comparison",
    "comparison_cards",
    "metric_overview",
    "narrative",
    "legal_notice",
    "process_flow",
    "timeline",
    "decision_tree",
    "feedback_loop",
    "layered_architecture",
    "data_pipeline",
    "hierarchy",
    "stakeholder_map",
    "quadrant_matrix",
    "feature_cards",
    "quotation",
    "evidence_review",
    "risk_opportunity_review",
    "recommendation_case",
    "state_transition",
]

KERNEL_LAYOUTS = frozenset(
    {
        "opening_cover",
        "section_divider",
        "closing_cover",
        "narrative",
        "legal_notice",
        "data_table",
    }
)


class ClosedModel(BaseModel):
    """Renderer-owned object: unknown fields are forbidden (D118)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False, strict=True)

    @model_validator(mode="before")
    @classmethod
    def _reject_null_placeholders(cls, data: Any) -> Any:
        # D212: absent data is omitted; null is an invalid placeholder.
        if isinstance(data, dict):
            for key, value in data.items():
                if value is None:
                    raise ValueError(f"{key!r} must be omitted, not null")
        return data


class DeckMeta(ClosedModel):
    handoff_schema_version: Literal[1]


class SectionEntry(ClosedModel):
    section_id: SemanticId
    label: NonEmptyStr


class EvidenceEntry(ClosedModel):
    source_name: NonEmptyStr
    locator: Optional[dict[str, Any]] = None

    @field_validator("source_name")
    @classmethod
    def _source_name_non_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_name must be non-whitespace")
        return v

    @field_validator("locator")
    @classmethod
    def _locator_is_json_object(cls, v: Any) -> Any:
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("locator must be a JSON object")
        return v


class NumberFormat(ClosedModel):
    """Closed deck-level format registry entry (D144/D214/D293)."""

    unit: Optional[UnitKind] = None
    value_decimals: int = Field(ge=0, le=4)
    tick_decimals: Optional[int] = Field(default=None, ge=0, le=4)
    negative_style: Literal["minus", "parentheses"]
    # Omitted means 1; present only when display scale differs from source (D293).
    value_scale: Optional[CanonicalDecimal] = None
    scale_label: Optional[NonEmptyStr] = None

    @model_validator(mode="after")
    def _scale_label_rule(self) -> NumberFormat:
        if self.value_scale is not None:
            scale = Decimal(self.value_scale)
            if scale <= 0:
                raise ValueError("value_scale must be positive")
            if scale == 1:
                raise ValueError("value_scale must be omitted when scale is 1")
            if not self.scale_label:
                raise ValueError("scale_label required when value_scale is set")
        elif self.scale_label is not None:
            raise ValueError("scale_label forbidden when value_scale is omitted")
        return self


class Typography(ClosedModel):
    mode: Literal["adaptive", "fixed"] = "adaptive"
    sync_group: Optional[SemanticId] = None
    body_font_size: Optional[int] = Field(default=None, ge=8, le=48)
    subtitle_font_size: Optional[int] = Field(default=None, ge=8, le=48)
    table_font_size: Optional[int] = Field(default=None, ge=12, le=24)

    @model_validator(mode="after")
    def _adaptive_sync_only(self) -> Typography:
        if self.sync_group is not None and self.mode != "adaptive":
            raise ValueError("sync_group requires adaptive typography")
        return self


class SubtitleContent(ClosedModel):
    subtitle: NonEmptyStr
    typography: Optional[Typography] = None

    @model_validator(mode="after")
    def _subtitle_typography_only(self) -> SubtitleContent:
        if self.typography and (
            self.typography.body_font_size is not None
            or self.typography.table_font_size is not None
        ):
            raise ValueError(
                "body_font_size/table_font_size inapplicable to subtitle typography"
            )
        return self


class Takeaway(ClosedModel):
    text: NonEmptyStr
    typography: Optional[Typography] = None

    @model_validator(mode="after")
    def _body_typography_only(self) -> Takeaway:
        if self.typography and (
            self.typography.subtitle_font_size is not None
            or self.typography.table_font_size is not None
        ):
            raise ValueError(
                "subtitle_font_size/table_font_size inapplicable to takeaway typography"
            )
        return self


class DisclosureItem(ClosedModel):
    kind: Literal["paragraph", "bullet"]
    text: NonEmptyStr


class DisclosureSection(ClosedModel):
    surface_id: SemanticId
    title: NonEmptyStr
    items: list[DisclosureItem] = Field(min_length=1, max_length=6)


class Disclosure(ClosedModel):
    sections: list[DisclosureSection] = Field(min_length=1, max_length=4)


class ProseRun(ClosedModel):
    text: NonEmptyStr
    emphasis: Optional[Literal["strong"]] = None


class Prose(ClosedModel):
    runs: list[ProseRun] = Field(min_length=1)

    @model_validator(mode="after")
    def _no_adjacent_equal_emphasis(self) -> Prose:
        prev_emph: object = object()
        for run in self.runs:
            emph = run.emphasis or None
            if emph == prev_emph and emph is not None:
                # adjacent equal-emphasis runs invalid; ordinary-to-ordinary OK? D224:
                # "adjacent equal-emphasis runs" — treat both strong-strong and
                # ordinary-ordinary as invalid to force one ordinary run.
                raise ValueError("adjacent equal-emphasis runs are invalid")
            if emph is None and prev_emph is None:
                raise ValueError("adjacent ordinary runs are invalid; use one run")
            prev_emph = emph
        return self


class NarrativeParagraphsBlock(ClosedModel):
    block_id: SemanticId
    type: Literal["paragraphs"]
    paragraphs: list[Prose] = Field(min_length=1, max_length=6)


class NarrativeBulletListBlock(ClosedModel):
    block_id: SemanticId
    type: Literal["bullet_list"]
    items: list[Prose] = Field(min_length=1, max_length=8)


NarrativeBlock = Annotated[
    Union[NarrativeParagraphsBlock, NarrativeBulletListBlock],
    Field(discriminator="type"),
]


class NarrativePayload(ClosedModel):
    blocks: list[NarrativeBlock] = Field(min_length=1, max_length=4)
    typography: Optional[Typography] = None

    @model_validator(mode="after")
    def _body_typography_only(self) -> NarrativePayload:
        if self.typography and (
            self.typography.subtitle_font_size is not None
            or self.typography.table_font_size is not None
        ):
            raise ValueError(
                "subtitle_font_size/table_font_size inapplicable to narrative typography"
            )
        return self

    @model_validator(mode="after")
    def _unique_block_ids(self) -> NarrativePayload:
        ids = [b.block_id for b in self.blocks]
        if len(ids) != len(set(ids)):
            raise ValueError("block_id values must be unique within the slide")
        return self


class CoverPayload(ClosedModel):
    """Shared opening/closing cover payload (D268)."""

    title: NonEmptyStr
    subtitle: Optional[NonEmptyStr] = None
    period_label: Optional[NonEmptyStr] = None
    date_label: Optional[NonEmptyStr] = None


class SectionDividerPayload(ClosedModel):
    """Divider payload is only the registry section_id (D269)."""

    section_id: SemanticId


class LegalNoticePayload(ClosedModel):
    """Multipart legal notice sequence payload (D226/D271)."""

    notice_id: SemanticId
    part: int = Field(gt=0)
    total_parts: int = Field(gt=0)
    paragraphs: list[NonEmptyStr] = Field(min_length=1, max_length=6)
    title: Optional[NonEmptyStr] = None

    @model_validator(mode="after")
    def _part_bounds_and_title(self) -> LegalNoticePayload:
        if self.part > self.total_parts:
            raise ValueError("part must be <= total_parts")
        if self.part == 1:
            if self.title is None:
                raise ValueError("legal_notice part 1 requires title")
        elif self.title is not None:
            raise ValueError("legal_notice continuation parts forbid authored title")
        return self


# ---------------------------------------------------------------------------
# Semantic values + table model (D141–D145, D213, D255–D257)
# ---------------------------------------------------------------------------


class NumberValue(ClosedModel):
    type: Literal["number"] = "number"
    value: CanonicalDecimal
    format_id: SemanticId


class RangeValue(ClosedModel):
    type: Literal["range"] = "range"
    lower: CanonicalDecimal
    upper: CanonicalDecimal
    format_id: SemanticId

    @model_validator(mode="after")
    def _ordered_bounds(self) -> RangeValue:
        if Decimal(self.lower) >= Decimal(self.upper):
            raise ValueError("range requires lower < upper")
        return self


class TextValue(ClosedModel):
    type: Literal["text"] = "text"
    text: NonEmptyStr


class MissingValue(ClosedModel):
    type: Literal["missing"] = "missing"


SemanticValue = Annotated[
    Union[NumberValue, RangeValue, TextValue, MissingValue],
    Field(discriminator="type"),
]


class TableLabel(ClosedModel):
    label: NonEmptyStr
    short_label: Optional[NonEmptyStr] = None


class TableColumn(ClosedModel):
    column_id: SemanticId
    label: NonEmptyStr
    short_label: Optional[NonEmptyStr] = None


class TableRow(ClosedModel):
    row_id: SemanticId
    label: NonEmptyStr
    short_label: Optional[NonEmptyStr] = None
    cells: dict[str, SemanticValue]


class ColumnGroup(ClosedModel):
    group_id: SemanticId
    label: NonEmptyStr
    short_label: Optional[NonEmptyStr] = None
    column_ids: list[SemanticId] = Field(min_length=1, max_length=12)


class TableData(ClosedModel):
    """Canonical rectangular table (D141/D255)."""

    surface_id: SemanticId
    stub_header: TableLabel
    columns: list[TableColumn] = Field(min_length=1)
    rows: list[TableRow] = Field(min_length=1)
    column_groups: Optional[list[ColumnGroup]] = None
    typography: Optional[Typography] = None

    @model_validator(mode="after")
    def _rectangular_identity(self) -> TableData:
        col_ids = [c.column_id for c in self.columns]
        if len(col_ids) != len(set(col_ids)):
            raise ValueError("column_id values must be unique within the table")
        row_ids = [r.row_id for r in self.rows]
        if len(row_ids) != len(set(row_ids)):
            raise ValueError("row_id values must be unique within the table")
        col_set = set(col_ids)
        for row in self.rows:
            keys = set(row.cells)
            missing = col_set - keys
            extra = keys - col_set
            if missing or extra:
                raise ValueError(
                    f"row {row.row_id!r} cells must match columns exactly; "
                    f"missing={sorted(missing)} extra={sorted(extra)}"
                )
            for key in row.cells:
                if not is_semantic_id(key):
                    raise ValueError(f"invalid cell key {key!r}")
        if self.typography is not None:
            t = self.typography
            if t.body_font_size is not None or t.subtitle_font_size is not None:
                raise ValueError(
                    "table typography allows only mode, sync_group, table_font_size"
                )
        if self.column_groups is not None:
            self._validate_groups(col_ids)
        return self

    def _validate_groups(self, col_ids: list[str]) -> None:
        groups = self.column_groups or []
        if not groups:
            raise ValueError("column_groups must be non-empty when present")
        gids = [g.group_id for g in groups]
        if len(gids) != len(set(gids)):
            raise ValueError("group_id values must be unique within the table")
        seen: set[str] = set()
        index = {cid: i for i, cid in enumerate(col_ids)}
        first_leaf_order: list[int] = []
        for g in groups:
            idxs = []
            for cid in g.column_ids:
                if cid not in index:
                    raise ValueError(
                        f"column_groups reference unknown column_id {cid!r}"
                    )
                if cid in seen:
                    raise ValueError(f"column_id {cid!r} appears in multiple groups")
                seen.add(cid)
                idxs.append(index[cid])
            lo, hi = min(idxs), max(idxs)
            if hi - lo + 1 != len(idxs) or sorted(idxs) != list(range(lo, hi + 1)):
                raise ValueError(
                    f"group {g.group_id!r} column_ids must be a contiguous leaf span"
                )
            if [col_ids[i] for i in range(lo, hi + 1)] != list(g.column_ids):
                raise ValueError(
                    f"group {g.group_id!r} column_ids must follow leaf column order"
                )
            first_leaf_order.append(lo)
        if first_leaf_order != sorted(first_leaf_order):
            raise ValueError("column_groups must be ordered by first leaf column")


class DataTablePayload(ClosedModel):
    """Ordinary full-width table composition payload (D183/D257)."""

    table: TableData


# ---------------------------------------------------------------------------
# Slides
# ---------------------------------------------------------------------------


class _SlideBase(ClosedModel):
    slide_number: int = Field(gt=0)
    layout_type: LayoutTypeName
    payload: Any  # narrowed per subclass
    speaker_notes: Optional[NonEmptyStr] = None
    evidence_ids: Optional[list[SemanticId]] = Field(default=None, min_length=1)

    @field_validator("speaker_notes")
    @classmethod
    def _notes_non_whitespace(cls, v: Optional[str]) -> Optional[str]:
        # D221: empty/whitespace-only notes fail; never strip or invent content.
        if v is not None and not v.strip():
            raise ValueError("speaker_notes must be non-whitespace plain text")
        return v


class OpeningCoverSlide(_SlideBase):
    layout_type: Literal["opening_cover"] = "opening_cover"
    payload: CoverPayload

    # Covers forbid root title/section/content/takeaway/disclosure/source_footer
    @model_validator(mode="before")
    @classmethod
    def _forbid_ordinary_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in (
                "title",
                "section_id",
                "content",
                "takeaway",
                "disclosure",
                "source_footer",
            ):
                if key in data:
                    raise ValueError(f"opening_cover forbids root field {key!r}")
        return data


class ClosingCoverSlide(_SlideBase):
    layout_type: Literal["closing_cover"] = "closing_cover"
    payload: CoverPayload

    @model_validator(mode="before")
    @classmethod
    def _forbid_ordinary_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in (
                "title",
                "section_id",
                "content",
                "takeaway",
                "disclosure",
                "source_footer",
            ):
                if key in data:
                    raise ValueError(f"closing_cover forbids root field {key!r}")
        return data


class SectionDividerSlide(_SlideBase):
    layout_type: Literal["section_divider"] = "section_divider"
    payload: SectionDividerPayload

    @model_validator(mode="before")
    @classmethod
    def _forbid_ordinary_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in (
                "title",
                "section_id",
                "content",
                "takeaway",
                "disclosure",
                "source_footer",
            ):
                if key in data:
                    raise ValueError(f"section_divider forbids root field {key!r}")
        return data


class LegalNoticeSlide(_SlideBase):
    layout_type: Literal["legal_notice"] = "legal_notice"
    section_id: SemanticId
    payload: LegalNoticePayload

    @model_validator(mode="before")
    @classmethod
    def _forbid_ordinary_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in (
                "title",
                "content",
                "takeaway",
                "disclosure",
                "source_footer",
            ):
                if key in data:
                    raise ValueError(f"legal_notice forbids root field {key!r}")
        return data

    @model_validator(mode="after")
    def _evidence_dupes(self) -> LegalNoticeSlide:
        if self.evidence_ids is not None and len(self.evidence_ids) != len(
            set(self.evidence_ids)
        ):
            raise ValueError("evidence_ids must be duplicate-free")
        return self


def _ordinary_footer_subset(slide: Any) -> Any:
    """Shared evidence/source_footer checks for ordinary (non-cover) slides."""
    if slide.source_footer is not None:
        if slide.evidence_ids is None:
            raise ValueError("source_footer requires evidence_ids")
        if len(slide.source_footer) != len(set(slide.source_footer)):
            raise ValueError("source_footer must be duplicate-free")
        missing = [i for i in slide.source_footer if i not in slide.evidence_ids]
        if missing:
            raise ValueError("source_footer must be a subset of evidence_ids")
    if slide.evidence_ids is not None and len(slide.evidence_ids) != len(
        set(slide.evidence_ids)
    ):
        raise ValueError("evidence_ids must be duplicate-free")
    return slide


class NarrativeSlide(_SlideBase):
    layout_type: Literal["narrative"] = "narrative"
    section_id: SemanticId
    title: NonEmptyStr
    payload: NarrativePayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def _footer_subset(self) -> NarrativeSlide:
        return _ordinary_footer_subset(self)


class DataTableSlide(_SlideBase):
    layout_type: Literal["data_table"] = "data_table"
    section_id: SemanticId
    title: NonEmptyStr
    payload: DataTablePayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def _footer_subset(self) -> DataTableSlide:
        return _ordinary_footer_subset(self)


# Kernel compositions: covers + divider + narrative + legal + data_table (#191).
# Other D210 layout_type values are recognized at the envelope and rejected
# with a clear "not yet implemented in kernel" structure error so the closed
# vocabulary stays honest without shipping empty payload shells.
Slide = Annotated[
    Union[
        OpeningCoverSlide,
        SectionDividerSlide,
        ClosingCoverSlide,
        NarrativeSlide,
        LegalNoticeSlide,
        DataTableSlide,
    ],
    Field(discriminator="layout_type"),
]


class Deck(ClosedModel):
    """Minimal top-level deck envelope (D211)."""

    meta: DeckMeta
    sections: list[SectionEntry]
    number_formats: dict[str, NumberFormat]
    evidence_registry: dict[str, EvidenceEntry]
    slides: list[Slide] = Field(min_length=1)

    @field_validator("number_formats")
    @classmethod
    def _format_ids(cls, v: dict[str, NumberFormat]) -> dict[str, NumberFormat]:
        for key in v:
            if not is_semantic_id(key):
                raise ValueError(f"invalid format_id {key!r}")
        return v

    @field_validator("evidence_registry")
    @classmethod
    def _evidence_ids(cls, v: dict[str, EvidenceEntry]) -> dict[str, EvidenceEntry]:
        for key in v:
            if not is_semantic_id(key):
                raise ValueError(f"invalid evidence id {key!r}")
        return v

    @model_validator(mode="after")
    def _deck_invariants(self) -> Deck:
        # Section registry uniqueness
        section_ids = [s.section_id for s in self.sections]
        if len(section_ids) != len(set(section_ids)):
            raise ValueError("section_id values must be deck-unique")
        labels_norm = [s.label.casefold() for s in self.sections]
        if len(labels_norm) != len(set(labels_norm)):
            raise ValueError("section labels must be unique after normalization")

        # Slide numbers and authored surface identities are deck-unique.
        nums = [s.slide_number for s in self.slides]
        if len(nums) != len(set(nums)):
            raise ValueError("slide_number values must be deck-unique")

        surface_ids: list[str] = []
        for slide in self.slides:
            if isinstance(slide, DataTableSlide):
                surface_ids.append(slide.payload.table.surface_id)
            disclosure = getattr(slide, "disclosure", None)
            if disclosure is not None:
                surface_ids.extend(section.surface_id for section in disclosure.sections)
        if len(surface_ids) != len(set(surface_ids)):
            raise ValueError("surface_id values must be deck-unique")

        # Format references must resolve; unused formats are invalid (D144/D216 style).
        referenced_formats: set[str] = set()
        for slide in self.slides:
            if not isinstance(slide, DataTableSlide):
                continue
            table = slide.payload.table
            for row in table.rows:
                for cell in row.cells.values():
                    fid = getattr(cell, "format_id", None)
                    if fid is None:
                        continue
                    if fid not in self.number_formats:
                        raise ValueError(f"unresolved format_id {fid!r}")
                    referenced_formats.add(fid)
        unused_fmt = [k for k in self.number_formats if k not in referenced_formats]
        if unused_fmt:
            raise ValueError(f"unused number_formats: {unused_fmt}")

        # Cover placement (D223/D268)
        openings = [
            i for i, s in enumerate(self.slides) if s.layout_type == "opening_cover"
        ]
        closings = [
            i for i, s in enumerate(self.slides) if s.layout_type == "closing_cover"
        ]
        if len(openings) > 1:
            raise ValueError("at most one opening_cover")
        if len(closings) > 1:
            raise ValueError("at most one closing_cover")
        if openings and openings[0] != 0:
            raise ValueError("opening_cover must be first")
        if closings and closings[0] != len(self.slides) - 1:
            raise ValueError("closing_cover must be last")

        # Section references + contiguity + dividers (D215/D269)
        section_index = {sid: i for i, sid in enumerate(section_ids)}
        used_sections: list[str] = []
        divider_for: dict[str, int] = {}
        for i, s in enumerate(self.slides):
            if s.layout_type == "section_divider":
                dsid = s.payload.section_id
                if dsid not in section_index:
                    raise ValueError(f"unknown section_id {dsid!r}")
                if dsid in divider_for:
                    raise ValueError(f"duplicate section_divider for {dsid!r}")
                divider_for[dsid] = i
                continue
            sid = getattr(s, "section_id", None)
            if sid is None:
                continue
            if sid not in section_ids:
                raise ValueError(f"unknown section_id {sid!r}")
            if not used_sections or used_sections[-1] != sid:
                used_sections.append(sid)
        # Contiguous runs already enforced by append-on-change; check registry order
        # and that each registry entry is used by ordinary/legal slides.
        if section_ids:
            if used_sections != [sid for sid in section_ids if sid in used_sections]:
                raise ValueError("section runs must follow registry order")
            unused = [sid for sid in section_ids if sid not in used_sections]
            if unused:
                raise ValueError(f"unused sections: {unused}")
        elif any(
            getattr(s, "section_id", None) or s.layout_type == "section_divider"
            for s in self.slides
        ):
            raise ValueError("section_id present but sections registry is empty")

        # Divider must sit immediately before the first ordinary slide of its section.
        first_ordinary: dict[str, int] = {}
        for i, s in enumerate(self.slides):
            sid = getattr(s, "section_id", None)
            if sid is None or s.layout_type == "section_divider":
                continue
            first_ordinary.setdefault(sid, i)
        for dsid, di in divider_for.items():
            fo = first_ordinary.get(dsid)
            if fo is None:
                raise ValueError(f"section_divider {dsid!r} has no ordinary slide")
            if di != fo - 1:
                raise ValueError(
                    f"section_divider for {dsid!r} must immediately precede "
                    "its first ordinary slide"
                )

        # Legal notice multipart sequences (D226/D271)
        notice_runs: dict[str, list[tuple[int, Any]]] = {}
        for i, s in enumerate(self.slides):
            if s.layout_type != "legal_notice":
                continue
            notice_runs.setdefault(s.payload.notice_id, []).append((i, s))
        for nid, parts in notice_runs.items():
            total = parts[0][1].payload.total_parts
            section = parts[0][1].section_id
            if len(parts) != total:
                raise ValueError(
                    f"legal_notice {nid!r} must cover exactly 1..{total} parts"
                )
            indices = [i for i, _ in parts]
            if indices != list(range(indices[0], indices[0] + total)):
                raise ValueError(f"legal_notice {nid!r} parts must be adjacent")
            seen_parts: list[int] = []
            for _, slide in parts:
                if slide.payload.total_parts != total:
                    raise ValueError(
                        f"legal_notice {nid!r} total_parts must match across parts"
                    )
                if slide.section_id != section:
                    raise ValueError(
                        f"legal_notice {nid!r} section_id must match across parts"
                    )
                seen_parts.append(slide.payload.part)
            if sorted(seen_parts) != list(range(1, total + 1)):
                raise ValueError(
                    f"legal_notice {nid!r} parts must be exactly 1..{total}"
                )
            if [p for p in seen_parts] != list(range(1, total + 1)):
                raise ValueError(
                    f"legal_notice {nid!r} parts must appear in ascending order"
                )

        # Evidence: every registry entry referenced; every slide ref resolves (D216/D217)
        referenced: set[str] = set()
        for s in self.slides:
            eids = getattr(s, "evidence_ids", None) or []
            for eid in eids:
                if eid not in self.evidence_registry:
                    raise ValueError(f"unresolved evidence id {eid!r}")
                referenced.add(eid)
            footer = getattr(s, "source_footer", None)
            if footer:
                names = [
                    self.evidence_registry[eid].source_name.casefold()
                    for eid in footer
                    if eid in self.evidence_registry
                ]
                if len(names) != len(set(names)):
                    raise ValueError(
                        "source_footer visible source_name values must be "
                        "normalized-unique"
                    )
        unused_ev = [k for k in self.evidence_registry if k not in referenced]
        if unused_ev:
            raise ValueError(f"unused evidence entries: {unused_ev}")

        return self
