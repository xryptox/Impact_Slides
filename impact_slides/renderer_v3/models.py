"""Schema-v1 typed deck model (D117–D224, D251, D268–D280 kernel compositions).

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
        "annex_table",
        "grouped_annex_table",
        "period_comparison",
        "comparison_cards",
        "single_chart",
        "process_flow",
        "timeline",
        "layered_architecture",
        "data_pipeline",
        "decision_tree",
        "feedback_loop",
        "hierarchy",
        "stakeholder_map",
        "quadrant_matrix",
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

PERIOD_COMPARISON_COLUMN_IDS: tuple[str, str, str] = (
    "current_period",
    "comparison_period",
    "variance",
)

# Default non-color identity pairs for multi-series lines (D99/D302).
LINE_STYLE_PAIRS: tuple[tuple[str, str], ...] = (
    ("solid", "circle"),
    ("dashed", "square"),
    ("dotted", "triangle"),
    ("dash_dot", "diamond"),
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


class AnnexTablePayload(ClosedModel):
    """Dense full-width annex table (D184/D258)."""

    table: TableData


class GroupedAnnexPeer(ClosedModel):
    """One headed peer matrix inside grouped_annex_table (D185/D259)."""

    heading: NonEmptyStr
    short_heading: Optional[NonEmptyStr] = None
    table: TableData


class GroupedAnnexTablePayload(ClosedModel):
    """One or two ordered peer annex surfaces (D185/D259)."""

    tables: list[GroupedAnnexPeer] = Field(min_length=1, max_length=2)


class MetricItem(ClosedModel):
    """One directionless metric in a strip (D165/D265)."""

    metric_id: SemanticId
    label: NonEmptyStr
    value: SemanticValue
    detail: Optional[NonEmptyStr] = None


class MetricStrip(ClosedModel):
    """Compact exterior metric row (D165/D265); period_comparison caps at 3."""

    surface_id: SemanticId
    metrics: list[MetricItem] = Field(min_length=1, max_length=3)
    typography: Optional[Typography] = None

    @model_validator(mode="after")
    def _unique_metrics_and_typo(self) -> MetricStrip:
        ids = [m.metric_id for m in self.metrics]
        if len(ids) != len(set(ids)):
            raise ValueError("metric_id values must be unique within the strip")
        if self.typography is not None:
            t = self.typography
            if t.subtitle_font_size is not None or t.table_font_size is not None:
                raise ValueError(
                    "metric_strip typography allows only mode, sync_group, body_font_size"
                )
        return self


class PeriodComparisonPayload(ClosedModel):
    """Financial period comparison with fixed role columns (D186/D260)."""

    table: TableData
    metric_strip: Optional[MetricStrip] = None

    @model_validator(mode="after")
    def _fixed_roles(self) -> PeriodComparisonPayload:
        cols = [c.column_id for c in self.table.columns]
        expected = list(PERIOD_COMPARISON_COLUMN_IDS)
        if cols != expected:
            raise ValueError(
                "period_comparison columns must be exactly ordered "
                f"{expected}; got {cols}"
            )
        if not (1 <= len(self.table.rows) <= 8):
            raise ValueError("period_comparison requires 1–8 metric rows")
        if self.table.column_groups is not None:
            raise ValueError("period_comparison forbids column_groups (D256/D260)")
        if self.metric_strip is not None:
            if self.metric_strip.surface_id == self.table.surface_id:
                raise ValueError(
                    "metric_strip.surface_id must differ from table.surface_id"
                )
        return self


class ComparisonCardsPayload(ClosedModel):
    """Peer comparison cards derived from one rectangular table (D187/D261)."""

    table: TableData

    @model_validator(mode="after")
    def _peer_fact_bounds(self) -> ComparisonCardsPayload:
        n_rows = len(self.table.rows)
        n_cols = len(self.table.columns)
        if not (2 <= n_rows <= 4):
            raise ValueError("comparison_cards requires 2–4 peer rows")
        if not (2 <= n_cols <= 4):
            raise ValueError("comparison_cards requires 2–4 fact columns")
        if self.table.column_groups is not None:
            raise ValueError("comparison_cards forbids column_groups (D256/D261)")
        return self


# ---------------------------------------------------------------------------
# Linear + grouping semantic compositions (D192–D193/D196–D197/D272–D273/D276–D277)
# ---------------------------------------------------------------------------


class ProcessStep(ClosedModel):
    """One authored step in a linear process_flow (D192/D272)."""

    step_id: SemanticId
    heading: NonEmptyStr
    detail: Optional[NonEmptyStr] = None


class ProcessFlowPayload(ClosedModel):
    """2–6 author-ordered steps; connections are implicit sequence only."""

    steps: list[ProcessStep] = Field(min_length=2, max_length=6)

    @model_validator(mode="after")
    def _unique_step_ids(self) -> ProcessFlowPayload:
        ids = [s.step_id for s in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("step_id values must be unique within process_flow")
        return self


class TimelineMilestone(ClosedModel):
    """One authored milestone; time_label is display text, never parsed (D193/D273)."""

    milestone_id: SemanticId
    time_label: NonEmptyStr
    heading: NonEmptyStr
    detail: Optional[NonEmptyStr] = None


class TimelinePayload(ClosedModel):
    """2–8 author-ordered milestones; array order is chronology."""

    milestones: list[TimelineMilestone] = Field(min_length=2, max_length=8)

    @model_validator(mode="after")
    def _unique_milestone_ids(self) -> TimelinePayload:
        ids = [m.milestone_id for m in self.milestones]
        if len(ids) != len(set(ids)):
            raise ValueError("milestone_id values must be unique within timeline")
        return self


class ArchitectureComponent(ClosedModel):
    """One component inside a layered_architecture layer (D196/D276)."""

    component_id: SemanticId
    heading: NonEmptyStr
    detail: Optional[NonEmptyStr] = None


class ArchitectureLayer(ClosedModel):
    """One ordered layer; order is grouping/stack only, never dependency."""

    layer_id: SemanticId
    heading: NonEmptyStr
    components: list[ArchitectureComponent] = Field(min_length=1, max_length=4)


class LayeredArchitecturePayload(ClosedModel):
    """2–4 ordered layers; component IDs unique across the surface."""

    layers: list[ArchitectureLayer] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def _unique_ids(self) -> LayeredArchitecturePayload:
        layer_ids = [ly.layer_id for ly in self.layers]
        if len(layer_ids) != len(set(layer_ids)):
            raise ValueError("layer_id values must be unique within layered_architecture")
        comp_ids = [
            c.component_id for ly in self.layers for c in ly.components
        ]
        if len(comp_ids) != len(set(comp_ids)):
            raise ValueError(
                "component_id values must be unique across layered_architecture"
            )
        return self


class PipelineComponent(ClosedModel):
    """One component inside a data_pipeline stage (D197/D277)."""

    component_id: SemanticId
    heading: NonEmptyStr
    detail: Optional[NonEmptyStr] = None


class PipelineStage(ClosedModel):
    """One ordered stage; optional transfer_label describes the next-stage edge."""

    stage_id: SemanticId
    heading: NonEmptyStr
    components: list[PipelineComponent] = Field(min_length=1, max_length=3)
    transfer_label: Optional[NonEmptyStr] = None


class DataPipelinePayload(ClosedModel):
    """2–6 ordered stages; final stage forbids transfer_label."""

    stages: list[PipelineStage] = Field(min_length=2, max_length=6)

    @model_validator(mode="after")
    def _unique_ids_and_transfers(self) -> DataPipelinePayload:
        stage_ids = [st.stage_id for st in self.stages]
        if len(stage_ids) != len(set(stage_ids)):
            raise ValueError("stage_id values must be unique within data_pipeline")
        comp_ids = [
            c.component_id for st in self.stages for c in st.components
        ]
        if len(comp_ids) != len(set(comp_ids)):
            raise ValueError(
                "component_id values must be unique across data_pipeline"
            )
        last = self.stages[-1]
        if last.transfer_label is not None:
            raise ValueError(
                "transfer_label is invalid on the final data_pipeline stage"
            )
        return self


# ---------------------------------------------------------------------------
# Relationship + decision compositions (D194–D195/D198–D200/D274–D275/D278–D280)
# ---------------------------------------------------------------------------
# Local shape only here. Graph/assignment connectivity is analyzed in
# validate.analyze_relationship_structure so non-strict can preserve facts
# without reconnecting (D274/D278).


class DecisionBranch(ClosedModel):
    """One authored branch from a decision node (D194/D274)."""

    label: NonEmptyStr
    target_id: SemanticId


class DecisionTreeNode(ClosedModel):
    """Decision (2–3 branches) or outcome leaf (D194/D274)."""

    node_id: SemanticId
    kind: Literal["decision", "outcome"]
    heading: NonEmptyStr
    detail: Optional[NonEmptyStr] = None
    branches: Optional[list[DecisionBranch]] = Field(default=None, min_length=2, max_length=3)

    @model_validator(mode="after")
    def _kind_branches(self) -> DecisionTreeNode:
        if self.kind == "decision":
            if not self.branches:
                raise ValueError("decision nodes require 2–3 ordered branches")
            labels = [b.label.casefold().strip() for b in self.branches]
            if len(labels) != len(set(labels)):
                raise ValueError("branch labels must be normalized-unique on a decision")
        elif self.branches is not None:
            raise ValueError("outcome nodes must omit branches")
        return self


class DecisionTreePayload(ClosedModel):
    """3–15 nodes + authored root; tree invariants checked at validate (D194/D274)."""

    root_id: SemanticId
    nodes: list[DecisionTreeNode] = Field(min_length=3, max_length=15)

    @model_validator(mode="after")
    def _unique_ids(self) -> DecisionTreePayload:
        ids = [n.node_id for n in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("node_id values must be unique within decision_tree")
        return self


class FeedbackLoopItem(ClosedModel):
    """One cycle item; causal edges author next-edge polarity (D195/D275)."""

    item_id: SemanticId
    heading: NonEmptyStr
    detail: Optional[NonEmptyStr] = None
    effect: Optional[Literal["same_direction", "opposite_direction"]] = None
    relationship_label: Optional[NonEmptyStr] = None


class FeedbackLoopPayload(ClosedModel):
    """3–8 ordered items forming one implicit cycle (D195/D275)."""

    kind: Literal["procedural", "causal"]
    items: list[FeedbackLoopItem] = Field(min_length=3, max_length=8)

    @model_validator(mode="after")
    def _ids_and_kind_fields(self) -> FeedbackLoopPayload:
        ids = [it.item_id for it in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("item_id values must be unique within feedback_loop")
        if self.kind == "procedural":
            for it in self.items:
                if it.effect is not None or it.relationship_label is not None:
                    raise ValueError(
                        "procedural feedback_loop forbids effect and relationship_label"
                    )
        # Causal missing/malformed effects are structure defects (D275), not shape drops.
        return self

    @property
    def loop_classification(self) -> Optional[Literal["reinforcing", "balancing"]]:
        """Derive reinforcing/balancing only when every causal effect is authored."""
        if self.kind != "causal":
            return None
        effects = [it.effect for it in self.items]
        if any(e is None for e in effects):
            return None
        opposite = sum(1 for e in effects if e == "opposite_direction")
        return "balancing" if opposite % 2 == 1 else "reinforcing"


class HierarchyNode(ClosedModel):
    """One hierarchy node with ordered child IDs (D198/D278)."""

    node_id: SemanticId
    heading: NonEmptyStr
    detail: Optional[NonEmptyStr] = None
    children: Optional[list[SemanticId]] = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _unique_child_refs(self) -> HierarchyNode:
        if self.children is not None and len(self.children) != len(set(self.children)):
            raise ValueError("children must be duplicate-free on a hierarchy node")
        return self


class HierarchyPayload(ClosedModel):
    """3–20 nodes, one root, one uniform relation (D198/D278)."""

    relationship: Literal["reports_to", "part_of", "is_a"]
    root_id: SemanticId
    nodes: list[HierarchyNode] = Field(min_length=3, max_length=20)

    @model_validator(mode="after")
    def _unique_ids(self) -> HierarchyPayload:
        ids = [n.node_id for n in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("node_id values must be unique within hierarchy")
        return self


class StakeholderEntity(ClosedModel):
    """Focal entity fields shared shape (D199/D279)."""

    entity_id: SemanticId
    heading: NonEmptyStr
    detail: Optional[NonEmptyStr] = None


class StakeholderSpoke(ClosedModel):
    """One hub-spoke stakeholder with explicit direction (D199/D279)."""

    entity_id: SemanticId
    heading: NonEmptyStr
    relationship_label: NonEmptyStr
    direction: Literal["undirected", "to_focal", "from_focal", "bidirectional"]
    detail: Optional[NonEmptyStr] = None


class StakeholderMapPayload(ClosedModel):
    """One focal + 2–8 ordered stakeholders (D199/D279)."""

    focal: StakeholderEntity
    stakeholders: list[StakeholderSpoke] = Field(min_length=2, max_length=8)

    @model_validator(mode="after")
    def _unique_ids(self) -> StakeholderMapPayload:
        ids = [self.focal.entity_id] + [s.entity_id for s in self.stakeholders]
        if len(ids) != len(set(ids)):
            raise ValueError(
                "entity_id values must be unique across stakeholder_map"
            )
        return self


class QuadrantAxis(ClosedModel):
    """One binary axis with exact endpoint labels (D200/D280)."""

    label: NonEmptyStr
    low_label: NonEmptyStr
    high_label: NonEmptyStr

    @model_validator(mode="after")
    def _distinct_ends(self) -> QuadrantAxis:
        if self.low_label.casefold().strip() == self.high_label.casefold().strip():
            raise ValueError("axis low_label and high_label must be normalized-distinct")
        return self


class QuadrantItem(ClosedModel):
    """One item with explicit low/high band on both axes (D200/D280)."""

    item_id: SemanticId
    heading: NonEmptyStr
    x_band: Literal["low", "high"]
    y_band: Literal["low", "high"]
    detail: Optional[NonEmptyStr] = None


class QuadrantMatrixPayload(ClosedModel):
    """Two axes + 1–16 assigned items (D200/D280)."""

    x_axis: QuadrantAxis
    y_axis: QuadrantAxis
    items: list[QuadrantItem] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def _unique_ids(self) -> QuadrantMatrixPayload:
        ids = [it.item_id for it in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("item_id values must be unique within quadrant_matrix")
        return self


# ---------------------------------------------------------------------------

# Axis charts + heatmap + single_chart composition (D162/D163/D227–D240, D243, D245–D248, D290–D302, D307/D308)
# ---------------------------------------------------------------------------


class ChartTypography(ClosedModel):
    """Semantic chart typography roles (D294) — not prose Typography."""

    mode: Literal["adaptive", "fixed"] = "adaptive"
    sync_group: Optional[SemanticId] = None
    category_ticks: Optional[int] = Field(default=None, ge=14, le=24)
    value_ticks: Optional[int] = Field(default=None, ge=14, le=28)
    ordinary_values: Optional[int] = Field(default=None, ge=14, le=32)
    legend: Optional[int] = Field(default=None, ge=16, le=24)
    series_labels: Optional[int] = Field(default=None, ge=16, le=24)
    axis_titles: Optional[int] = Field(default=None, ge=13, le=24)
    context_labels: Optional[int] = Field(default=None, ge=16, le=24)
    annotations: Optional[int] = Field(default=None, ge=13, le=24)

    @model_validator(mode="after")
    def _adaptive_sync_only(self) -> ChartTypography:
        if self.sync_group is not None and self.mode != "adaptive":
            raise ValueError("sync_group requires adaptive typography")
        return self


class ChartDisplay(ClosedModel):
    """Sparse axis-chart display overrides (D231/D295)."""

    ordinary_values: Optional[Literal["show", "hide"]] = None
    series_identity: Optional[Literal["auto", "legend", "pane_title"]] = None

    @model_validator(mode="after")
    def _not_empty_noise(self) -> ChartDisplay:
        if (
            self.ordinary_values is None
            and self.series_identity is None
        ):
            raise ValueError("display must declare at least one override")
        return self


class ChartCategory(ClosedModel):
    category_id: SemanticId
    label: NonEmptyStr
    short_label: Optional[NonEmptyStr] = None


class ChartSeriesStyle(ClosedModel):
    """Complete line style + marker pair (D99/D133/D291)."""

    line_style: Literal["solid", "dashed", "dotted", "dash_dot"]
    marker: Literal["circle", "square", "triangle", "diamond"]


class ChartSeries(ClosedModel):
    series_id: SemanticId
    name: NonEmptyStr
    values: list[Optional[CanonicalDecimal]] = Field(min_length=1)
    color: Optional[NonEmptyStr] = None  # palette key (D130)
    style: Optional[ChartSeriesStyle] = None


class ChartData(ClosedModel):
    """Ordered category-and-series matrix (D228/D291).

    Family cardinality (line vs bar category/series floors) is enforced on the
    chart visual; this model owns rectangular identity only.
    """

    categories: list[ChartCategory] = Field(min_length=1, max_length=24)
    series: list[ChartSeries] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def _matrix_invariants(self) -> ChartData:
        cat_ids = [c.category_id for c in self.categories]
        if len(cat_ids) != len(set(cat_ids)):
            raise ValueError("category_id values must be unique within the chart")
        ser_ids = [s.series_id for s in self.series]
        if len(ser_ids) != len(set(ser_ids)):
            raise ValueError("series_id values must be unique within the chart")
        names_norm = [s.name.casefold().strip() for s in self.series]
        if len(names_norm) != len(set(names_norm)):
            raise ValueError("series names must be normalized-unique within the chart")
        n = len(self.categories)
        for s in self.series:
            if len(s.values) != n:
                raise ValueError(
                    f"series {s.series_id!r} must supply exactly one value per category"
                )
        return self


class CategoryGroup(ClosedModel):
    """Semantic category hierarchy only — never aggregates values (D155/D237)."""

    group_id: SemanticId
    label: NonEmptyStr
    category_ids: list[SemanticId] = Field(min_length=1)
    short_label: Optional[NonEmptyStr] = None


class BoxedLabelAuxiliary(ClosedModel):
    """Category-aligned boxed labels targeting one bar series (D146/D235)."""

    auxiliary_id: SemanticId
    role: Literal["boxed_label"] = "boxed_label"
    label: NonEmptyStr
    format_id: SemanticId
    target_series_id: SemanticId
    values: list[Optional[CanonicalDecimal]] = Field(min_length=1)


class CategoryAxis(ClosedModel):
    visible: bool
    title: Optional[NonEmptyStr] = None


class GeneratedDomain(ClosedModel):
    kind: Literal["generated"] = "generated"
    min: Optional[CanonicalDecimal] = None
    max: Optional[CanonicalDecimal] = None
    target_ticks: Optional[int] = Field(default=None, ge=2, le=8)


class FixedDomain(ClosedModel):
    kind: Literal["fixed"] = "fixed"
    min: CanonicalDecimal
    max: CanonicalDecimal
    ticks: list[CanonicalDecimal] = Field(min_length=2, max_length=8)

    @model_validator(mode="after")
    def _ticks_span(self) -> FixedDomain:
        lo = Decimal(self.min)
        hi = Decimal(self.max)
        if lo >= hi:
            raise ValueError("fixed domain requires min < max")
        vals = [Decimal(t) for t in self.ticks]
        if vals != sorted(vals) or len(vals) != len(set(vals)):
            raise ValueError("fixed ticks must be strictly increasing")
        if vals[0] != lo or vals[-1] != hi:
            raise ValueError("fixed ticks must span min and max endpoints")
        return self


ValueDomain = Annotated[
    Union[GeneratedDomain, FixedDomain],
    Field(discriminator="kind"),
]


class LeadingBreak(ClosedModel):
    to: CanonicalDecimal


class ValueAxis(ClosedModel):
    visible: bool
    format_id: SemanticId
    domain: ValueDomain
    title: Optional[NonEmptyStr] = None
    leading_break: Optional[LeadingBreak] = None

    @model_validator(mode="after")
    def _hidden_domain_rules(self) -> ValueAxis:
        if not self.visible:
            if self.domain.kind != "generated":
                raise ValueError("hidden value axis requires generated domain")
            if self.domain.target_ticks is not None:
                raise ValueError("hidden value axis forbids target_ticks")
            if self.leading_break is not None:
                raise ValueError("hidden value axis forbids leading_break")
        if self.leading_break is not None and self.domain.kind == "generated":
            if self.domain.min is None:
                raise ValueError("leading_break requires generated domain min")
            if Decimal(self.domain.min) >= Decimal(self.leading_break.to):
                raise ValueError("leading_break requires min < to")
        if self.leading_break is not None and self.domain.kind == "fixed":
            if not any(
                Decimal(t) == Decimal(self.leading_break.to)
                for t in self.domain.ticks
            ):
                raise ValueError(
                    "leading_break with a fixed domain requires a fixed tick"
                    " equal to leading_break.to (D157/D159)"
                )
        return self


class ValueAxes(ClosedModel):
    primary: ValueAxis

    @model_validator(mode="before")
    @classmethod
    def _no_secondary(cls, data: Any) -> Any:
        if isinstance(data, dict) and "secondary" in data:
            raise ValueError("secondary value axis is combo-only (D230)")
        return data


def _common_chart_heading_rules(chart: Any) -> None:
    if chart.subtitle is not None and chart.heading is None:
        raise ValueError("subtitle requires heading")
    identity = (
        chart.display.series_identity if chart.display is not None else None
    )
    if identity == "pane_title":
        if chart.heading is None:
            raise ValueError("series_identity pane_title requires heading")
        if len(chart.chart_data.series) != 1:
            raise ValueError(
                "series_identity pane_title requires exactly one series"
            )


def _domain_contains_finite(chart: Any) -> None:
    domain = chart.value_axes.primary.domain
    lo = Decimal(domain.min) if domain.min is not None else None
    hi = Decimal(domain.max) if domain.max is not None else None
    for s in chart.chart_data.series:
        for v in s.values:
            if v is None:
                continue
            dv = Decimal(v)
            if (lo is not None and dv < lo) or (hi is not None and dv > hi):
                raise ValueError(
                    "authored domain bounds must contain every finite value"
                )


def _validate_category_groups(chart: Any) -> None:
    groups = getattr(chart, "category_groups", None)
    if not groups:
        return
    cat_ids = [c.category_id for c in chart.chart_data.categories]
    cat_pos = {cid: i for i, cid in enumerate(cat_ids)}
    seen_gids: set[str] = set()
    occupied: dict[str, str] = {}
    ordered_first: list[int] = []
    for g in groups:
        if g.group_id in seen_gids:
            raise ValueError("category group_id values must be unique")
        seen_gids.add(g.group_id)
        if len(g.category_ids) != len(set(g.category_ids)):
            raise ValueError(
                f"category group {g.group_id!r} has duplicate category_ids"
            )
        positions: list[int] = []
        for cid in g.category_ids:
            if cid not in cat_pos:
                raise ValueError(
                    f"category group {g.group_id!r} references unknown "
                    f"category_id {cid!r}"
                )
            if cid in occupied:
                raise ValueError(
                    f"category_id {cid!r} belongs to multiple groups"
                )
            occupied[cid] = g.group_id
            positions.append(cat_pos[cid])
        # Contiguous and chart-order (D237).
        if positions != sorted(positions):
            raise ValueError(
                f"category group {g.group_id!r} category_ids must follow chart order"
            )
        if positions[-1] - positions[0] + 1 != len(positions):
            raise ValueError(
                f"category group {g.group_id!r} category_ids must be contiguous"
            )
        ordered_first.append(positions[0])
    if ordered_first != sorted(ordered_first):
        raise ValueError("category_groups must follow first-category order")


def _validate_boxed_labels(chart: Any) -> None:
    aux = getattr(chart, "auxiliary_series", None) or []
    boxed = [a for a in aux if a.role == "boxed_label"]
    if len(boxed) > 1:
        raise ValueError("at most one boxed_label auxiliary_series entry (D235)")
    if not boxed:
        return
    b = boxed[0]
    n = len(chart.chart_data.categories)
    if len(b.values) != n:
        raise ValueError(
            "boxed_label values must supply exactly one entry per category"
        )
    ser_ids = {s.series_id for s in chart.chart_data.series}
    if b.target_series_id not in ser_ids:
        raise ValueError(
            f"boxed_label target_series_id {b.target_series_id!r} is not a chart series"
        )


def _finite_values(chart: Any) -> list[Decimal]:
    out: list[Decimal] = []
    for s in chart.chart_data.series:
        for v in s.values:
            if v is not None:
                out.append(Decimal(v))
    return out


def _leading_break_rules(
    chart: Any, *, allow: bool, positive_only: bool = False
) -> None:
    br = chart.value_axes.primary.leading_break
    if br is None:
        return
    if not allow:
        raise ValueError(
            f"{chart.chart_type} forbids leading_break (D157/D240)"
        )
    target = Decimal(br.to)
    finite = _finite_values(chart)
    if not finite:
        raise ValueError("leading_break requires at least one finite value")
    if any(v <= target for v in finite):
        # D157/D243: every finite value lies beyond the break target.
        raise ValueError("leading_break.to must be below every finite value")
    if positive_only and any(v <= 0 for v in finite):
        raise ValueError(
            "leading_break requires every finite value on the positive side (D243)"
        )


def _bar_domain_includes_zero(chart: Any) -> None:
    """Without a leading break, bar domains must include semantic zero (D240/D243)."""
    if chart.value_axes.primary.leading_break is not None:
        return
    domain = chart.value_axes.primary.domain
    if domain.kind == "fixed":
        lo, hi = Decimal(domain.min), Decimal(domain.max)
        if lo > 0 or hi < 0:
            raise ValueError("bar fixed domain must include zero")
        return
    # generated: authored bounds alone must not exclude zero when both set
    lo = Decimal(domain.min) if domain.min is not None else None
    hi = Decimal(domain.max) if domain.max is not None else None
    if lo is not None and hi is not None and (lo > 0 or hi < 0):
        raise ValueError("bar generated domain bounds must include zero")


class LineChartVisual(ClosedModel):
    """Flat line-chart visual envelope (D227/D239/D290/D302)."""

    type: Literal["chart"] = "chart"
    surface_id: SemanticId
    chart_type: Literal["line"] = "line"
    heading: Optional[NonEmptyStr] = None
    subtitle: Optional[NonEmptyStr] = None
    chart_data: ChartData
    category_axis: CategoryAxis
    value_axes: ValueAxes
    display: Optional[ChartDisplay] = None
    typography: Optional[ChartTypography] = None

    @model_validator(mode="after")
    def _line_invariants(self) -> LineChartVisual:
        if len(self.chart_data.categories) < 2:
            raise ValueError("line charts require at least two categories")
        for s in self.chart_data.series:
            finite = sum(1 for v in s.values if v is not None)
            if finite < 2:
                raise ValueError(
                    f"series {s.series_id!r} requires at least two finite values"
                )
        _common_chart_heading_rules(self)
        _leading_break_rules(self, allow=True)
        _domain_contains_finite(self)
        return self


class GeneratedHeatmapScale(ClosedModel):
    """Scale derived from all finite heatmap cells (D163/D246/D308)."""

    mode: Literal["generated"] = "generated"


class FixedHeatmapScale(ClosedModel):
    """Authored finite min < max containing every finite cell (D163/D246)."""

    mode: Literal["fixed"] = "fixed"
    min: CanonicalDecimal
    max: CanonicalDecimal

    @model_validator(mode="after")
    def _ordered_bounds(self) -> FixedHeatmapScale:
        if Decimal(self.min) >= Decimal(self.max):
            raise ValueError("fixed heatmap scale requires min < max")
        return self


HeatmapScale = Annotated[
    Union[GeneratedHeatmapScale, FixedHeatmapScale],
    Field(discriminator="mode"),
]


class HeatmapVisual(ClosedModel):
    """Native semantic heatmap: one D255 table + one color scale (D163/D246/D308)."""

    type: Literal["chart"] = "chart"
    surface_id: SemanticId
    chart_type: Literal["heatmap"] = "heatmap"
    heading: Optional[NonEmptyStr] = None
    subtitle: Optional[NonEmptyStr] = None
    table_data: TableData
    scale: HeatmapScale

    @model_validator(mode="before")
    @classmethod
    def _forbid_axis_chart_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        forbidden = (
            "chart_data",
            "category_axis",
            "value_axes",
            "display",
            "typography",
            "context_labels",
            "annotations",
            "measurements",
            "category_groups",
            "auxiliary_series",
            "coverage",
        )
        for key in forbidden:
            if key in data:
                raise ValueError(f"heatmap forbids field {key!r}")
        return data

    @model_validator(mode="after")
    def _heatmap_invariants(self) -> HeatmapVisual:
        if self.subtitle is not None and self.heading is None:
            raise ValueError("subtitle requires heading")
        table = self.table_data
        n_cols = len(table.columns)
        n_rows = len(table.rows)
        if not (1 <= n_cols <= 12):
            raise ValueError("heatmap requires 1–12 value columns")
        if not (1 <= n_rows <= 12):
            raise ValueError("heatmap requires 1–12 rows")
        if table.column_groups is not None:
            raise ValueError("heatmap forbids column_groups")
        if table.typography is not None:
            raise ValueError("heatmap forbids table typography overrides")
        format_ids: set[str] = set()
        finite: list[Decimal] = []
        for row in table.rows:
            for cell in row.cells.values():
                kind = getattr(cell, "type", None)
                if kind == "missing":
                    continue
                if kind != "number":
                    raise ValueError(
                        "heatmap cells must be number or missing only"
                    )
                format_ids.add(cell.format_id)
                finite.append(Decimal(cell.value))
        if not finite:
            raise ValueError("heatmap requires at least one finite value")
        if len(format_ids) != 1:
            raise ValueError(
                "heatmap numbers must share exactly one format_id"
            )
        if self.scale.mode == "fixed":
            lo = Decimal(self.scale.min)
            hi = Decimal(self.scale.max)
            for v in finite:
                if v < lo or v > hi:
                    raise ValueError(
                        "fixed heatmap scale must contain every finite value"
                    )
        return self

    @property
    def shared_format_id(self) -> str:
        for row in self.table_data.rows:
            for cell in row.cells.values():
                fid = getattr(cell, "format_id", None)
                if fid is not None:
                    return fid
        raise RuntimeError("heatmap has no numeric format_id")


class GroupedBarChartVisual(ClosedModel):
    """Vertical zero-baseline grouped bars (D240)."""

    type: Literal["chart"] = "chart"
    surface_id: SemanticId
    chart_type: Literal["grouped_bar"] = "grouped_bar"
    heading: Optional[NonEmptyStr] = None
    subtitle: Optional[NonEmptyStr] = None
    chart_data: ChartData
    category_axis: CategoryAxis
    value_axes: ValueAxes
    display: Optional[ChartDisplay] = None
    typography: Optional[ChartTypography] = None
    category_groups: Optional[list[CategoryGroup]] = Field(
        default=None, min_length=1, max_length=6
    )
    auxiliary_series: Optional[list[BoxedLabelAuxiliary]] = Field(
        default=None, min_length=1
    )

    @model_validator(mode="after")
    def _grouped_invariants(self) -> GroupedBarChartVisual:
        n_cat = len(self.chart_data.categories)
        n_ser = len(self.chart_data.series)
        if not (1 <= n_cat <= 12):
            raise ValueError("grouped_bar requires 1–12 categories")
        if not (1 <= n_ser <= 4):
            raise ValueError("grouped_bar requires 1–4 series")
        for s in self.chart_data.series:
            if s.style is not None:
                raise ValueError("grouped_bar forbids line series style")
            if not any(v is not None for v in s.values):
                raise ValueError(
                    f"series {s.series_id!r} requires at least one finite value"
                )
        _common_chart_heading_rules(self)
        _leading_break_rules(self, allow=False)
        _bar_domain_includes_zero(self)
        _domain_contains_finite(self)
        _validate_category_groups(self)
        _validate_boxed_labels(self)
        return self


class HorizontalBarChartVisual(ClosedModel):
    """Horizontal grouped bars with optional leading break (D243)."""

    type: Literal["chart"] = "chart"
    surface_id: SemanticId
    chart_type: Literal["horizontal_bar"] = "horizontal_bar"
    heading: Optional[NonEmptyStr] = None
    subtitle: Optional[NonEmptyStr] = None
    chart_data: ChartData
    category_axis: CategoryAxis
    value_axes: ValueAxes
    display: Optional[ChartDisplay] = None
    typography: Optional[ChartTypography] = None
    category_groups: Optional[list[CategoryGroup]] = Field(
        default=None, min_length=1, max_length=6
    )
    auxiliary_series: Optional[list[BoxedLabelAuxiliary]] = Field(
        default=None, min_length=1
    )

    @model_validator(mode="after")
    def _hbar_invariants(self) -> HorizontalBarChartVisual:
        n_cat = len(self.chart_data.categories)
        n_ser = len(self.chart_data.series)
        if not (1 <= n_cat <= 12):
            raise ValueError("horizontal_bar requires 1–12 categories")
        if not (1 <= n_ser <= 4):
            raise ValueError("horizontal_bar requires 1–4 series")
        for s in self.chart_data.series:
            if s.style is not None:
                raise ValueError("horizontal_bar forbids line series style")
            if not any(v is not None for v in s.values):
                raise ValueError(
                    f"series {s.series_id!r} requires at least one finite value"
                )
        _common_chart_heading_rules(self)
        _leading_break_rules(self, allow=True, positive_only=True)
        _bar_domain_includes_zero(self)
        _domain_contains_finite(self)
        _validate_category_groups(self)
        _validate_boxed_labels(self)
        return self


class WaterfallStep(ClosedModel):
    """One authored waterfall step (D162/D245/D307)."""

    category_id: SemanticId
    label: NonEmptyStr
    role: Literal["change", "total", "computed_total"]
    value: Optional[CanonicalDecimal] = None
    short_label: Optional[NonEmptyStr] = None

    @model_validator(mode="after")
    def _role_value(self) -> WaterfallStep:
        if self.role == "computed_total":
            if self.value is not None:
                raise ValueError(
                    "computed_total forbids authored value (D245/D307)"
                )
        elif self.value is None:
            raise ValueError(
                f"{self.role} requires a canonical decimal value (D245/D307)"
            )
        return self


class WaterfallData(ClosedModel):
    """Ordered waterfall steps — not D228 series (D245/D307)."""

    steps: list[WaterfallStep] = Field(min_length=2, max_length=12)

    @model_validator(mode="after")
    def _sequence(self) -> WaterfallData:
        ids = [s.category_id for s in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("waterfall category_id values must be unique")
        if self.steps[0].role != "total":
            raise ValueError("first waterfall step must be total (D245/D307)")
        if self.steps[-1].role not in ("total", "computed_total"):
            raise ValueError(
                "last waterfall step must be total or computed_total (D245/D307)"
            )
        return self


class WaterfallChartVisual(ClosedModel):
    """Explicit arithmetic waterfall (D162/D245/D248/D307)."""

    type: Literal["chart"] = "chart"
    surface_id: SemanticId
    chart_type: Literal["waterfall"] = "waterfall"
    heading: Optional[NonEmptyStr] = None
    subtitle: Optional[NonEmptyStr] = None
    waterfall_data: WaterfallData
    category_axis: CategoryAxis
    value_axes: ValueAxes
    typography: Optional[ChartTypography] = None

    @model_validator(mode="before")
    @classmethod
    def _forbid_bar_only_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        forbidden = (
            "chart_data",
            "display",
            "category_groups",
            "auxiliary_series",
        )
        hit = [k for k in forbidden if k in data]
        if hit:
            raise ValueError(
                f"waterfall forbids {', '.join(hit)} (D245/D307)"
            )
        return data

    @model_validator(mode="after")
    def _waterfall_invariants(self) -> WaterfallChartVisual:
        if self.subtitle is not None and self.heading is None:
            raise ValueError("subtitle requires heading")
        if self.value_axes.primary.leading_break is not None:
            raise ValueError("waterfall forbids leading_break (D245/D307)")
        # Domain must include zero and every authored total/change level.
        levels = _waterfall_levels(self)
        domain = self.value_axes.primary.domain
        lo = Decimal(domain.min) if domain.min is not None else None
        hi = Decimal(domain.max) if domain.max is not None else None
        if domain.kind == "fixed":
            lo, hi = Decimal(domain.min), Decimal(domain.max)
            if lo > 0 or hi < 0:
                raise ValueError("waterfall fixed domain must include zero")
        elif lo is not None and hi is not None and (lo > 0 or hi < 0):
            raise ValueError(
                "waterfall generated domain bounds must include zero"
            )
        for lv in levels:
            if (lo is not None and lv < lo) or (hi is not None and lv > hi):
                raise ValueError(
                    "authored domain bounds must contain every waterfall level"
                )
        return self


def _waterfall_levels(chart: "WaterfallChartVisual") -> list[Decimal]:
    """Running levels + zero for domain containment (placement arithmetic only)."""
    level = Decimal(0)
    out: list[Decimal] = [Decimal(0)]
    for step in chart.waterfall_data.steps:
        if step.role == "total":
            level = Decimal(step.value)  # type: ignore[arg-type]
            out.append(level)
        elif step.role == "change":
            level = level + Decimal(step.value)  # type: ignore[arg-type]
            out.append(level)
        else:
            out.append(level)
    return out


ChartVisual = Annotated[
    Union[
        LineChartVisual,
        GroupedBarChartVisual,
        HorizontalBarChartVisual,
        WaterfallChartVisual,
        HeatmapVisual,
    ],
    Field(discriminator="chart_type"),
]


class SingleChartPayload(ClosedModel):
    """single_chart composition: one axis-chart or heatmap primary, no support yet (D140)."""

    primary_visual: ChartVisual

    @model_validator(mode="before")
    @classmethod
    def _forbid_support(cls, data: Any) -> Any:
        if isinstance(data, dict) and "support_visual" in data:
            raise ValueError(
                "support_visual is not implemented on single_chart"
            )
        return data


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

    @field_validator("evidence_ids")
    @classmethod
    def _evidence_ids_duplicate_free(
        cls, v: Optional[list[str]]
    ) -> Optional[list[str]]:
        if v is not None and len(v) != len(set(v)):
            raise ValueError("evidence_ids must be duplicate-free")
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


class AnnexTableSlide(_SlideBase):
    """Dense annex: one table + disclosure notes; no takeaway (D184/D258)."""

    layout_type: Literal["annex_table"] = "annex_table"
    section_id: SemanticId
    title: NonEmptyStr
    payload: AnnexTablePayload
    content: Optional[SubtitleContent] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="before")
    @classmethod
    def _forbid_takeaway(cls, data: Any) -> Any:
        if isinstance(data, dict) and "takeaway" in data:
            raise ValueError("annex_table forbids takeaway (D258)")
        return data

    @model_validator(mode="after")
    def _footer_subset(self) -> AnnexTableSlide:
        return _ordinary_footer_subset(self)


class GroupedAnnexTableSlide(_SlideBase):
    """1–2 peer annex matrices; no takeaway (D185/D259)."""

    layout_type: Literal["grouped_annex_table"] = "grouped_annex_table"
    section_id: SemanticId
    title: NonEmptyStr
    payload: GroupedAnnexTablePayload
    content: Optional[SubtitleContent] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="before")
    @classmethod
    def _forbid_takeaway(cls, data: Any) -> Any:
        if isinstance(data, dict) and "takeaway" in data:
            raise ValueError("grouped_annex_table forbids takeaway (D259)")
        return data

    @model_validator(mode="after")
    def _footer_subset(self) -> GroupedAnnexTableSlide:
        return _ordinary_footer_subset(self)


class PeriodComparisonSlide(_SlideBase):
    """Period roles + optional exterior metric strip (D186/D260)."""

    layout_type: Literal["period_comparison"] = "period_comparison"
    section_id: SemanticId
    title: NonEmptyStr
    payload: PeriodComparisonPayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def _footer_subset(self) -> PeriodComparisonSlide:
        return _ordinary_footer_subset(self)


class ComparisonCardsSlide(_SlideBase):
    """Peer cards from one rectangular fact table (D187/D208/D261)."""

    layout_type: Literal["comparison_cards"] = "comparison_cards"
    section_id: SemanticId
    title: NonEmptyStr
    payload: ComparisonCardsPayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def _footer_subset(self) -> ComparisonCardsSlide:
        return _ordinary_footer_subset(self)


class ProcessFlowSlide(_SlideBase):
    """Linear procedural sequence (D192/D272)."""

    layout_type: Literal["process_flow"] = "process_flow"
    section_id: SemanticId
    title: NonEmptyStr
    payload: ProcessFlowPayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def _footer_subset(self) -> ProcessFlowSlide:
        return _ordinary_footer_subset(self)


class TimelineSlide(_SlideBase):
    """Authored chronology without date parsing (D193/D273)."""

    layout_type: Literal["timeline"] = "timeline"
    section_id: SemanticId
    title: NonEmptyStr
    payload: TimelinePayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def _footer_subset(self) -> TimelineSlide:
        return _ordinary_footer_subset(self)


class LayeredArchitectureSlide(_SlideBase):
    """Non-graph layered grouping (D196/D276)."""

    layout_type: Literal["layered_architecture"] = "layered_architecture"
    section_id: SemanticId
    title: NonEmptyStr
    payload: LayeredArchitecturePayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def _footer_subset(self) -> LayeredArchitectureSlide:
        return _ordinary_footer_subset(self)


class DataPipelineSlide(_SlideBase):
    """Directed stage flow with optional transfer labels (D197/D277)."""

    layout_type: Literal["data_pipeline"] = "data_pipeline"
    section_id: SemanticId
    title: NonEmptyStr
    payload: DataPipelinePayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def _footer_subset(self) -> DataPipelineSlide:
        return _ordinary_footer_subset(self)


class DecisionTreeSlide(_SlideBase):
    """Branching decision/outcome tree (D194/D274)."""

    layout_type: Literal["decision_tree"] = "decision_tree"
    section_id: SemanticId
    title: NonEmptyStr
    payload: DecisionTreePayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def _footer_subset(self) -> DecisionTreeSlide:
        return _ordinary_footer_subset(self)


class FeedbackLoopSlide(_SlideBase):
    """One ordered procedural or causal cycle (D195/D275)."""

    layout_type: Literal["feedback_loop"] = "feedback_loop"
    section_id: SemanticId
    title: NonEmptyStr
    payload: FeedbackLoopPayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def _footer_subset(self) -> FeedbackLoopSlide:
        return _ordinary_footer_subset(self)


class HierarchySlide(_SlideBase):
    """Uniform parent-child hierarchy (D198/D278)."""

    layout_type: Literal["hierarchy"] = "hierarchy"
    section_id: SemanticId
    title: NonEmptyStr
    payload: HierarchyPayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def _footer_subset(self) -> HierarchySlide:
        return _ordinary_footer_subset(self)


class StakeholderMapSlide(_SlideBase):
    """Hub-and-spoke stakeholder map (D199/D279)."""

    layout_type: Literal["stakeholder_map"] = "stakeholder_map"
    section_id: SemanticId
    title: NonEmptyStr
    payload: StakeholderMapPayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def _footer_subset(self) -> StakeholderMapSlide:
        return _ordinary_footer_subset(self)


class QuadrantMatrixSlide(_SlideBase):
    """Two-axis semantic quadrant matrix (D200/D280)."""

    layout_type: Literal["quadrant_matrix"] = "quadrant_matrix"
    section_id: SemanticId
    title: NonEmptyStr
    payload: QuadrantMatrixPayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def _footer_subset(self) -> QuadrantMatrixSlide:
        return _ordinary_footer_subset(self)


class SingleChartSlide(_SlideBase):
    layout_type: Literal["single_chart"] = "single_chart"
    section_id: SemanticId
    title: NonEmptyStr
    payload: SingleChartPayload
    content: Optional[SubtitleContent] = None
    takeaway: Optional[Takeaway] = None
    disclosure: Optional[Disclosure] = None
    source_footer: Optional[list[SemanticId]] = Field(
        default=None, min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def _footer_subset(self) -> SingleChartSlide:
        return _ordinary_footer_subset(self)


# Kernel compositions: covers + divider + narrative + legal + data_table (#191)
# plus annex/comparison tables (#180), single_chart axis charts
# (line #182; grouped/horizontal bars #183; waterfall #186; heatmap #187),
# linear/grouping compositions (#192), and relationship/decision compositions (#193).
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
        AnnexTableSlide,
        GroupedAnnexTableSlide,
        PeriodComparisonSlide,
        ComparisonCardsSlide,
        ProcessFlowSlide,
        TimelineSlide,
        LayeredArchitectureSlide,
        DataPipelineSlide,
        DecisionTreeSlide,
        FeedbackLoopSlide,
        HierarchySlide,
        StakeholderMapSlide,
        QuadrantMatrixSlide,
        SingleChartSlide,
    ],
    Field(discriminator="layout_type"),
]


def _slide_table_surface_ids(slide: Any) -> list[str]:
    """Authored table/metric surface IDs owned by one slide."""
    lt = getattr(slide, "layout_type", None)
    payload = getattr(slide, "payload", None)
    if lt in (
        "data_table",
        "annex_table",
        "period_comparison",
        "comparison_cards",
    ):
        ids = [payload.table.surface_id]
        strip = getattr(payload, "metric_strip", None)
        if strip is not None:
            ids.append(strip.surface_id)
        return ids
    if lt == "grouped_annex_table":
        return [peer.table.surface_id for peer in payload.tables]
    if lt == "single_chart":
        chart = payload.primary_visual
        # Heatmap owns a nested D255 table with its own deck-unique surface (D308).
        table = getattr(chart, "table_data", None)
        if table is not None:
            return [table.surface_id]
    return []


def _slide_semantic_values(slide: Any) -> list[Any]:
    """Every D213 value that may carry a format_id on one slide."""
    values: list[Any] = []
    for table in _slide_tables(slide):
        for row in table.rows:
            values.extend(row.cells.values())
    payload = getattr(slide, "payload", None)
    strip = getattr(payload, "metric_strip", None) if payload is not None else None
    if strip is not None:
        values.extend(m.value for m in strip.metrics)
    return values


def _slide_tables(slide: Any) -> list[TableData]:
    lt = getattr(slide, "layout_type", None)
    payload = getattr(slide, "payload", None)
    if lt in (
        "data_table",
        "annex_table",
        "period_comparison",
        "comparison_cards",
    ):
        return [payload.table]
    if lt == "grouped_annex_table":
        return [peer.table for peer in payload.tables]
    if lt == "single_chart":
        table = getattr(payload.primary_visual, "table_data", None)
        if table is not None:
            return [table]
    return []


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
            surface_ids.extend(_slide_table_surface_ids(slide))
            if isinstance(slide, SingleChartSlide):
                surface_ids.append(slide.payload.primary_visual.surface_id)
            disclosure = getattr(slide, "disclosure", None)
            if disclosure is not None:
                surface_ids.extend(section.surface_id for section in disclosure.sections)
        if len(surface_ids) != len(set(surface_ids)):
            raise ValueError("surface_id values must be deck-unique")

        # Format references must resolve; unused formats are invalid (D144/D216 style).
        referenced_formats: set[str] = set()
        for slide in self.slides:
            for value in _slide_semantic_values(slide):
                fid = getattr(value, "format_id", None)
                if fid is None:
                    continue
                if fid not in self.number_formats:
                    raise ValueError(f"unresolved format_id {fid!r}")
                referenced_formats.add(fid)
            if isinstance(slide, SingleChartSlide):
                chart = slide.payload.primary_visual
                if isinstance(
                    chart,
                    (
                        LineChartVisual,
                        GroupedBarChartVisual,
                        HorizontalBarChartVisual,
                        WaterfallChartVisual,
                    ),
                ):
                    fid = chart.value_axes.primary.format_id
                    if fid not in self.number_formats:
                        raise ValueError(f"unresolved format_id {fid!r}")
                    referenced_formats.add(fid)
                    for aux in getattr(chart, "auxiliary_series", None) or []:
                        afid = aux.format_id
                        if afid not in self.number_formats:
                            raise ValueError(f"unresolved format_id {afid!r}")
                        referenced_formats.add(afid)
                    # Author series colors must be known palette keys (D16/D98/D130).
                    if not isinstance(chart, WaterfallChartVisual):
                        from .theme import palette_keys  # local; avoid import cycle

                        keys = set(palette_keys())
                        for s in chart.chart_data.series:
                            if s.color is not None and s.color not in keys:
                                raise ValueError(
                                    f"unknown series color key {s.color!r}"
                                )
                elif isinstance(chart, HeatmapVisual):
                    fid = chart.shared_format_id
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
            if seen_parts != list(range(1, total + 1)):
                raise ValueError(
                    f"legal_notice {nid!r} parts must be exactly 1..{total} in order"
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
