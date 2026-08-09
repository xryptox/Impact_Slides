"""Schema-v1 typed deck model (D117–D224, D251, D268–D271 kernel subset).

This module is the single source of truth for the closed handoff contract.
JSON Schema is generated from these models (D121).
"""
from __future__ import annotations

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

KERNEL_LAYOUTS = frozenset({"opening_cover", "closing_cover", "narrative"})


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

    @field_validator("locator")
    @classmethod
    def _locator_is_json_object(cls, v: Any) -> Any:
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("locator must be a JSON object")
        return v


class UnitSpec(ClosedModel):
    text: NonEmptyStr
    position: Literal["prefix", "suffix"]
    spacing: Literal["none", "space"]
    accessible_name: NonEmptyStr


class NumberFormat(ClosedModel):
    unit: Optional[UnitSpec] = None
    value_decimals: int = Field(ge=0, le=4)
    tick_decimals: Optional[int] = Field(default=None, ge=0, le=4)
    negative_style: Literal["minus", "parentheses"]
    value_scale: float = Field(default=1.0, gt=0)
    scale_label: Optional[NonEmptyStr] = None

    @model_validator(mode="after")
    def _scale_label_rule(self) -> NumberFormat:
        if self.value_scale != 1 and not self.scale_label:
            raise ValueError("scale_label required when value_scale != 1")
        if self.value_scale == 1 and self.scale_label is not None:
            raise ValueError("scale_label forbidden when value_scale == 1")
        return self


class Typography(ClosedModel):
    mode: Literal["adaptive", "fixed"] = "adaptive"
    sync_group: Optional[SemanticId] = None
    body_font_size: Optional[int] = Field(default=None, ge=8, le=48)
    subtitle_font_size: Optional[int] = Field(default=None, ge=8, le=48)


class SubtitleContent(ClosedModel):
    subtitle: NonEmptyStr
    typography: Optional[Typography] = None


class Takeaway(ClosedModel):
    text: NonEmptyStr
    typography: Optional[Typography] = None


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
    section_id: SemanticId


# ---------------------------------------------------------------------------
# Slides
# ---------------------------------------------------------------------------


class _SlideBase(ClosedModel):
    slide_number: int = Field(gt=0)
    layout_type: LayoutTypeName
    payload: Any  # narrowed per subclass
    speaker_notes: Optional[NonEmptyStr] = None
    evidence_ids: Optional[list[SemanticId]] = Field(default=None, min_length=1)


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


class NarrativeSlide(_SlideBase):
    layout_type: Literal["narrative"] = "narrative"
    section_id: SemanticId
    title: NonEmptyStr
    payload: NarrativePayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(default=None, min_length=1, max_length=4)

    @model_validator(mode="after")
    def _footer_subset(self) -> NarrativeSlide:
        if self.source_footer is not None:
            if self.evidence_ids is None:
                raise ValueError("source_footer requires evidence_ids")
            if len(self.source_footer) != len(set(self.source_footer)):
                raise ValueError("source_footer must be duplicate-free")
            missing = [i for i in self.source_footer if i not in self.evidence_ids]
            if missing:
                raise ValueError("source_footer must be a subset of evidence_ids")
        if self.evidence_ids is not None and len(self.evidence_ids) != len(
            set(self.evidence_ids)
        ):
            raise ValueError("evidence_ids must be duplicate-free")
        return self


# Kernel validates the three compositions needed for the minimal deck.
# Other D210 layout_type values are recognized at the envelope and rejected
# with a clear "not yet implemented in kernel" structure error so the closed
# vocabulary stays honest without shipping 29 empty payload shells.
Slide = Annotated[
    Union[OpeningCoverSlide, ClosingCoverSlide, NarrativeSlide],
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

        # Slide numbers unique
        nums = [s.slide_number for s in self.slides]
        if len(nums) != len(set(nums)):
            raise ValueError("slide_number values must be deck-unique")

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

        # Section references + contiguity (D215)
        used_sections: list[str] = []
        for s in self.slides:
            sid = getattr(s, "section_id", None)
            if sid is None:
                continue
            if sid not in section_ids:
                raise ValueError(f"unknown section_id {sid!r}")
            if not used_sections or used_sections[-1] != sid:
                used_sections.append(sid)
        # Contiguous runs already enforced by append-on-change; check registry order
        # and that each registry entry is used.
        if section_ids:
            # Filter used to registry order presence
            if used_sections != [sid for sid in section_ids if sid in used_sections]:
                raise ValueError("section runs must follow registry order")
            unused = [sid for sid in section_ids if sid not in used_sections]
            if unused:
                raise ValueError(f"unused sections: {unused}")
        elif any(getattr(s, "section_id", None) for s in self.slides):
            raise ValueError("section_id present but sections registry is empty")

        # Evidence: every registry entry referenced; every slide ref resolves (D216/D217)
        referenced: set[str] = set()
        for s in self.slides:
            eids = getattr(s, "evidence_ids", None) or []
            for eid in eids:
                if eid not in self.evidence_registry:
                    raise ValueError(f"unresolved evidence id {eid!r}")
                referenced.add(eid)
        unused_ev = [k for k in self.evidence_registry if k not in referenced]
        if unused_ev:
            raise ValueError(f"unused evidence entries: {unused_ev}")

        return self
