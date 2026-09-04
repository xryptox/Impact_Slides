"""Allowlisted non-strict repairs (D123 / D311 kernel subset)."""
from __future__ import annotations

import re
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from typing import Any, Callable  # Callable used by typography surface resolvers

from .diagnostics import DiagnosticEvent, event

RepairFn = Callable[[Any, list[DiagnosticEvent]], Any]

_SEMANTIC_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_CANONICAL_DECIMAL_RE = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$")


def _slide_number(slide: dict[str, Any]) -> int | None:
    v = slide.get("slide_number")
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def assume_schema_v1(raw: Any, events: list[DiagnosticEvent]) -> Any:
    """Insert handoff_schema_version:1 only when input is otherwise exact v1 (D311)."""
    if not isinstance(raw, dict):
        return raw
    meta = raw.get("meta")
    if not isinstance(meta, dict):
        return raw
    if "handoff_schema_version" in meta:
        return raw
    # Only empty meta + closed envelope; any unknown/legacy field blocks assume.
    legacy_markers = {
        "presentation",
        "theme",
        "config",
        "assets",
        "layout",
        "visual_spec",
    }
    if legacy_markers.intersection(raw):
        return raw
    if meta:
        return raw
    allowed_top = {"meta", "sections", "number_formats", "evidence_registry", "slides"}
    if set(raw) - allowed_top:
        return raw
    if _envelope_has_unknown_fields(raw):
        return raw
    out = deepcopy(raw)
    out["meta"] = {"handoff_schema_version": 1}
    # Prove the repaired input is exact schema v1 before keeping the assume.
    from .models import Deck

    try:
        Deck.model_validate(out)
    except Exception:
        return raw
    events.append(
        event(
            code="repair.schema_version_assumed",
            severity="warning",
            phase="repair",
            role="deck_meta",
            path="/meta/handoff_schema_version",
            action="assume_schema_v1",
            result="canonicalized",
            expected="meta.handoff_schema_version == 1",
        )
    )
    return out


def _envelope_has_unknown_fields(raw: dict[str, Any]) -> bool:
    """True if any closed object carries a field outside the kernel allowlist."""
    slides = raw.get("slides")
    if not isinstance(slides, list):
        return False
    for slide in slides:
        if not isinstance(slide, dict):
            continue
        layout = slide.get("layout_type")
        common = {
            "slide_number",
            "layout_type",
            "payload",
            "speaker_notes",
            "evidence_ids",
        }
        if layout in ("opening_cover", "closing_cover"):
            allowed = common
            payload_allowed = {"title", "subtitle", "period_label", "date_label"}
        elif layout == "section_divider":
            allowed = common
            payload_allowed = {"section_id"}
        elif layout == "legal_notice":
            allowed = common | {"section_id"}
            payload_allowed = {
                "notice_id",
                "part",
                "total_parts",
                "paragraphs",
                "title",
            }
        elif layout == "narrative":
            allowed = common | {
                "section_id",
                "title",
                "content",
                "takeaway",
                "disclosure",
                "source_footer",
            }
            payload_allowed = {"blocks", "typography"}
        elif layout in {
            "data_table",
            "annex_table",
            "grouped_annex_table",
            "period_comparison",
            "comparison_cards",
        }:
            allowed = common | {
                "section_id",
                "title",
                "content",
                "disclosure",
                "source_footer",
            }
            if layout not in {"annex_table", "grouped_annex_table"}:
                allowed.add("takeaway")
            payload_allowed = {
                "grouped_annex_table": {"tables"},
                "period_comparison": {"table", "metric_strip"},
            }.get(layout, {"table"})
        elif layout == "chart_grouped_annex":
            allowed = common | {
                "section_id",
                "title",
                "content",
                "disclosure",
                "source_footer",
            }
            payload_allowed = {"chart", "tables"}
        elif layout == "single_chart":
            allowed = common | {
                "section_id",
                "title",
                "content",
                "takeaway",
                "disclosure",
                "source_footer",
            }
            payload_allowed = {"chart", "support"}
        elif layout in {"dual_chart", "chart_hero_dual", "metric_overview"}:
            allowed = common | {
                "section_id",
                "title",
                "content",
                "takeaway",
                "disclosure",
                "source_footer",
            }
            payload_allowed = {
                "dual_chart": {"charts", "support"},
                "chart_hero_dual": {"chart", "hero", "support"},
                "metric_overview": {"surface_id", "heading", "metrics", "detail"},
            }[layout]
        elif layout in {
            "process_flow",
            "timeline",
            "layered_architecture",
            "data_pipeline",
            "feature_cards",
            "quotation",
            "evidence_review",
            "risk_opportunity_review",
            "recommendation_case",
            "state_transition",
            "decision_tree",
            "feedback_loop",
            "hierarchy",
            "stakeholder_map",
            "quadrant_matrix",
        }:
            allowed = common | {
                "section_id",
                "title",
                "content",
                "takeaway",
                "disclosure",
                "source_footer",
            }
            payload_allowed = {
                "process_flow": {"steps"},
                "timeline": {"milestones"},
                "layered_architecture": {"layers"},
                "data_pipeline": {"stages"},
                    "feature_cards": {"cards", "typography"},
                    "quotation": {"quotes"},
                    "evidence_review": {"findings"},
                    "risk_opportunity_review": {"risks", "opportunities", "groups_repaired"},
                    "recommendation_case": {"recommendation", "rationales", "support_repaired"},
                    "state_transition": {"before", "after", "transition_steps"},
                "decision_tree": {"root_id", "nodes"},
                "feedback_loop": {"kind", "items"},
                "hierarchy": {"relationship", "root_id", "nodes"},
                "stakeholder_map": {"focal", "stakeholders"},
                "quadrant_matrix": {"x_axis", "y_axis", "items"},
            }[layout]
        else:
            return True
        if set(slide) - allowed:
            return True
        payload = slide.get("payload")
        if isinstance(payload, dict) and set(payload) - payload_allowed:
            return True
    sections = raw.get("sections")
    if isinstance(sections, list):
        for sec in sections:
            if isinstance(sec, dict) and set(sec) - {"section_id", "label"}:
                return True
    return False


def _chart_support_allowed(support: dict[str, Any]) -> set[str]:
    st = support.get("support_type")
    if st == "metric_strip":
        return {"support_type", "surface_id", "metrics", "typography"}
    if st == "support_table":
        return {"support_type", "alignment", "table"}
    if st == "outlined_support":
        return {"support_type", "table"}
    return set(support.keys())


def drop_unknown_fields(raw: Any, events: list[DiagnosticEvent]) -> Any:
    """Drop unknown fields on closed deck envelope and known slide shapes.

    Kernel allowlist only — never invents business content (D123).
    """
    if not isinstance(raw, dict):
        return raw
    out = deepcopy(raw)
    _drop_unknown_object(
        out,
        allowed={"meta", "sections", "number_formats", "evidence_registry", "slides"},
        path="",
        events=events,
        role="deck",
    )
    meta = out.get("meta")
    if isinstance(meta, dict):
        _drop_unknown_object(
            meta,
            allowed={"handoff_schema_version"},
            path="/meta",
            events=events,
            role="deck_meta",
        )
    sections = out.get("sections")
    if isinstance(sections, list):
        for i, sec in enumerate(sections):
            if isinstance(sec, dict):
                _drop_unknown_object(
                    sec,
                    allowed={"section_id", "label"},
                    path=f"/sections/{i}",
                    events=events,
                    role="section",
                )
    slides = out.get("slides")
    if isinstance(slides, list):
        for i, slide in enumerate(slides):
            if not isinstance(slide, dict):
                continue
            layout = slide.get("layout_type")
            common = {
                "slide_number",
                "layout_type",
                "payload",
                "speaker_notes",
                "evidence_ids",
            }
            if layout in ("opening_cover", "closing_cover", "section_divider"):
                allowed = common
                # Brand chrome forbids ordinary semantic roots — never strip them.
                protected = _SEMANTIC_COMMON_FIELDS
            elif layout == "legal_notice":
                allowed = common | {"section_id"}
                # Legal requires section_id; other ordinary semantic roots stay.
                protected = _SEMANTIC_COMMON_FIELDS - {"section_id"}
            elif layout in {
                "narrative",
                "data_table",
                "annex_table",
                "grouped_annex_table",
                "chart_grouped_annex",
                "period_comparison",
                "comparison_cards",
                "single_chart",
                "dual_chart",
                "chart_hero_dual",
                "metric_overview",
                "process_flow",
                "timeline",
                "layered_architecture",
                "data_pipeline",
                "feature_cards",
                "quotation",
                "evidence_review",
                "risk_opportunity_review",
                "recommendation_case",
                "state_transition",
                "decision_tree",
                "feedback_loop",
                "hierarchy",
                "stakeholder_map",
                "quadrant_matrix",
            }:
                allowed = common | {
                    "section_id",
                    "title",
                    "content",
                    "disclosure",
                    "source_footer",
                }
                if layout not in {
                    "annex_table",
                    "grouped_annex_table",
                    "chart_grouped_annex",
                }:
                    allowed.add("takeaway")
                protected = frozenset()
            else:
                allowed = common | {
                    "section_id",
                    "title",
                    "content",
                    "takeaway",
                    "disclosure",
                    "source_footer",
                }
                protected = frozenset()
            _drop_unknown_object(
                slide,
                allowed=allowed,
                path=f"/slides/{i}",
                events=events,
                role="slide",
                slide_number=_slide_number(slide),
                layout_type=layout if isinstance(layout, str) else None,
                protected=protected,
            )
            payload = slide.get("payload")
            if isinstance(payload, dict) and layout in (
                "opening_cover",
                "closing_cover",
            ):
                _drop_unknown_object(
                    payload,
                    allowed={"title", "subtitle", "period_label", "date_label"},
                    path=f"/slides/{i}/payload",
                    events=events,
                    role="cover_payload",
                    slide_number=_slide_number(slide),
                    layout_type=layout,
                )
            if isinstance(payload, dict) and layout == "section_divider":
                _drop_unknown_object(
                    payload,
                    allowed={"section_id"},
                    path=f"/slides/{i}/payload",
                    events=events,
                    role="divider_payload",
                    slide_number=_slide_number(slide),
                    layout_type=layout,
                )
            if isinstance(payload, dict) and layout == "legal_notice":
                _drop_unknown_object(
                    payload,
                    allowed={
                        "notice_id",
                        "part",
                        "total_parts",
                        "paragraphs",
                        "title",
                    },
                    path=f"/slides/{i}/payload",
                    events=events,
                    role="legal_notice_payload",
                    slide_number=_slide_number(slide),
                    layout_type=layout,
                )
            if isinstance(payload, dict) and layout == "narrative":
                _drop_unknown_object(
                    payload,
                    allowed={"blocks", "typography"},
                    path=f"/slides/{i}/payload",
                    events=events,
                    role="narrative_payload",
                    slide_number=_slide_number(slide),
                    layout_type=layout,
                )
            payload_fields = {
                "data_table": {"table"},
                "annex_table": {"table"},
                "grouped_annex_table": {"tables"},
                "chart_grouped_annex": {"chart", "tables"},
                "period_comparison": {"table", "metric_strip"},
                "comparison_cards": {"table"},
                "process_flow": {"steps"},
                "timeline": {"milestones"},
                "layered_architecture": {"layers"},
                "data_pipeline": {"stages"},
                    "feature_cards": {"cards", "typography"},
                    "quotation": {"quotes"},
                    "evidence_review": {"findings"},
                    "risk_opportunity_review": {"risks", "opportunities", "groups_repaired"},
                    "recommendation_case": {"recommendation", "rationales", "support_repaired"},
                    "state_transition": {"before", "after", "transition_steps"},
                    "decision_tree": {"root_id", "nodes"},
                    "feedback_loop": {"kind", "items"},
                    "hierarchy": {"relationship", "root_id", "nodes"},
                    "stakeholder_map": {"focal", "stakeholders"},
                    "quadrant_matrix": {"x_axis", "y_axis", "items"},
                    "single_chart": {"chart", "support"},
                    "dual_chart": {"charts", "support"},
                    "chart_hero_dual": {"chart", "hero", "support"},
                    "metric_overview": {"surface_id", "heading", "metrics", "detail"},
            }
            if isinstance(payload, dict) and layout in payload_fields:
                _drop_unknown_object(
                    payload,
                    allowed=payload_fields[layout],
                    path=f"/slides/{i}/payload",
                    events=events,
                    role=f"{layout}_payload",
                    slide_number=_slide_number(slide),
                    layout_type=layout,
                )
                if layout in {"single_chart", "dual_chart", "chart_hero_dual"}:
                    support = payload.get("support")
                    if isinstance(support, dict):
                        _drop_unknown_object(
                            support,
                            allowed=_chart_support_allowed(support),
                            path=f"/slides/{i}/payload/support",
                            events=events,
                            role="chart_support",
                            slide_number=_slide_number(slide),
                            layout_type=layout,
                        )
                if layout == "dual_chart":
                    charts = payload.get("charts")
                    if isinstance(charts, list):
                        for j, item in enumerate(charts):
                            if not isinstance(item, dict) or "chart" not in item:
                                continue
                            _drop_unknown_object(
                                item,
                                allowed={"chart", "support"},
                                path=f"/slides/{i}/payload/charts/{j}",
                                events=events,
                                role="dual_chart_pane",
                                slide_number=_slide_number(slide),
                                layout_type=layout,
                            )
                            pane_support = item.get("support")
                            if isinstance(pane_support, dict):
                                _drop_unknown_object(
                                    pane_support,
                                    allowed=_chart_support_allowed(pane_support),
                                    path=f"/slides/{i}/payload/charts/{j}/support",
                                    events=events,
                                    role="chart_support",
                                    slide_number=_slide_number(slide),
                                    layout_type=layout,
                                )
    return out


# Authored ordinary semantic fields (D287). Non-strict must not silently drop
# these on brand/legal layouts — leave them so validation fails until a typed
# unresolved-slide fallback exists (D180/D268/D271).
_SEMANTIC_COMMON_FIELDS = frozenset(
    {
        "section_id",
        "title",
        "content",
        "takeaway",
        "disclosure",
        "source_footer",
    }
)


def _drop_unknown_object(
    obj: dict[str, Any],
    *,
    allowed: set[str],
    path: str,
    events: list[DiagnosticEvent],
    role: str,
    slide_number: int | None = None,
    layout_type: str | None = None,
    protected: frozenset[str] = frozenset(),
) -> None:
    unknown = [k for k in list(obj.keys()) if k not in allowed]
    for key in unknown:
        if key in protected:
            # Keep forbidden semantic content in place for validation failure.
            continue
        del obj[key]
        events.append(
            event(
                code="repair.field_dropped",
                severity="warning",
                phase="repair",
                role=role,
                path=f"{path}/{key}" if path else f"/{key}",
                action="drop_field",
                result="dropped",
                slide_number=slide_number,
                layout_type=layout_type,
                expected=f"closed object fields: {sorted(allowed)}",
                input_meta={"field": key},
            )
        )


def _is_semantic_id_str(value: Any) -> bool:
    return isinstance(value, str) and _SEMANTIC_ID_RE.fullmatch(value) is not None


def _is_canonical_decimal(value: Any) -> bool:
    return isinstance(value, str) and _CANONICAL_DECIMAL_RE.fullmatch(value) is not None


def _well_formed_cell(cell: Any) -> bool:
    if not isinstance(cell, dict):
        return False
    kind = cell.get("type")
    if kind == "missing":
        return set(cell) == {"type"}
    if kind == "number":
        return (
            set(cell) == {"type", "value", "format_id"}
            and _is_canonical_decimal(cell.get("value"))
            and _is_semantic_id_str(cell.get("format_id"))
        )
    if kind == "range":
        if not (
            set(cell) == {"type", "lower", "upper", "format_id"}
            and _is_canonical_decimal(cell.get("lower"))
            and _is_canonical_decimal(cell.get("upper"))
            and _is_semantic_id_str(cell.get("format_id"))
        ):
            return False
        try:
            return Decimal(cell["lower"]) < Decimal(cell["upper"])
        except InvalidOperation:
            return False
    if kind == "text":
        return (
            set(cell) == {"type", "text"}
            and isinstance(cell.get("text"), str)
            and len(cell["text"]) >= 1
        )
    return False


def _table_column_ids(table: dict[str, Any]) -> list[str] | None:
    cols = table.get("columns")
    if not isinstance(cols, list) or not cols:
        return None
    ids: list[str] = []
    for col in cols:
        if not isinstance(col, dict):
            return None
        cid = col.get("column_id")
        if not isinstance(cid, str):
            return None
        ids.append(cid)
    return ids


def _well_formed_groups(groups: Any, col_ids: list[str]) -> bool:
    if not isinstance(groups, list) or not groups:
        return False
    index = {cid: i for i, cid in enumerate(col_ids)}
    seen_group_ids: set[str] = set()
    seen_columns: set[str] = set()
    first_leaf_order: list[int] = []
    for group in groups:
        if not isinstance(group, dict):
            return False
        if set(group) - {"group_id", "label", "short_label", "column_ids"}:
            return False
        gid = group.get("group_id")
        label = group.get("label")
        short_label = group.get("short_label")
        members = group.get("column_ids")
        if not _is_semantic_id_str(gid) or gid in seen_group_ids:
            return False
        if not isinstance(label, str) or not label:
            return False
        if short_label is not None and (not isinstance(short_label, str) or not short_label):
            return False
        if not isinstance(members, list) or not 1 <= len(members) <= 12:
            return False
        seen_group_ids.add(gid)
        positions: list[int] = []
        for cid in members:
            if not isinstance(cid, str) or cid not in index or cid in seen_columns:
                return False
            seen_columns.add(cid)
            positions.append(index[cid])
        lo, hi = min(positions), max(positions)
        if sorted(positions) != list(range(lo, hi + 1)):
            return False
        if [col_ids[i] for i in range(lo, hi + 1)] != list(members):
            return False
        first_leaf_order.append(lo)
    return first_leaf_order == sorted(first_leaf_order)


def repair_table_data(raw: Any, events: list[DiagnosticEvent]) -> Any:
    """D255 non-strict table repair before TableData validation.

    Missing/malformed cells become diagnosed missing, keys outside the table
    columns are dropped, and malformed column_groups flatten away while the
    leaf columns and cell data survive.
    """
    if not isinstance(raw, dict) or not isinstance(raw.get("slides"), list):
        return raw
    out = deepcopy(raw)
    for i, slide in enumerate(out["slides"]):
        if not isinstance(slide, dict):
            continue
        layout = slide.get("layout_type")
        payload = slide.get("payload")
        if not isinstance(payload, dict):
            continue
        located: list[tuple[str, dict[str, Any]]] = []
        if layout in {"data_table", "annex_table", "period_comparison", "comparison_cards"}:
            table = payload.get("table")
            if isinstance(table, dict):
                located.append((f"/slides/{i}/payload/table", table))
        elif layout == "single_chart":
            visual = payload.get("chart")
            if (
                isinstance(visual, dict)
                and visual.get("chart_type") == "heatmap"
                and isinstance(visual.get("table_data"), dict)
            ):
                located.append(
                    (
                        f"/slides/{i}/payload/chart/table_data",
                        visual["table_data"],
                    )
                )
            support = payload.get("support")
            if isinstance(support, dict) and isinstance(support.get("table"), dict):
                located.append(
                    (f"/slides/{i}/payload/support/table", support["table"])
                )
        elif layout in {"dual_chart", "chart_hero_dual"}:
            support = payload.get("support")
            if isinstance(support, dict) and isinstance(support.get("table"), dict):
                located.append(
                    (f"/slides/{i}/payload/support/table", support["table"])
                )
            if layout == "dual_chart":
                charts = payload.get("charts")
                if isinstance(charts, list):
                    for j, item in enumerate(charts):
                        if not isinstance(item, dict):
                            continue
                        pane_support = item.get("support") if "chart" in item else None
                        if isinstance(pane_support, dict) and isinstance(
                            pane_support.get("table"), dict
                        ):
                            located.append(
                                (
                                    f"/slides/{i}/payload/charts/{j}/support/table",
                                    pane_support["table"],
                                )
                            )
        elif layout in {"grouped_annex_table", "chart_grouped_annex"}:
            peers = payload.get("tables")
            if isinstance(peers, list):
                for j, peer in enumerate(peers):
                    if isinstance(peer, dict) and isinstance(peer.get("table"), dict):
                        located.append(
                            (f"/slides/{i}/payload/tables/{j}/table", peer["table"])
                        )
        for path_base, table in located:
            _repair_one_table(
                table,
                path_base=path_base,
                events=events,
                slide_number=_slide_number(slide),
                layout_type=layout if isinstance(layout, str) else None,
            )
    return out


def _repair_one_table(
    table: dict[str, Any],
    *,
    path_base: str,
    events: list[DiagnosticEvent],
    slide_number: int | None,
    layout_type: str | None,
) -> None:
    col_ids = _table_column_ids(table)
    if col_ids is None:
        return
    surface_id = table.get("surface_id")
    surface_id = surface_id if isinstance(surface_id, str) else None
    col_set = set(col_ids)
    rows = table.get("rows")
    if isinstance(rows, list):
        for j, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            cells = row.get("cells")
            if not isinstance(cells, dict):
                cells = {}
                row["cells"] = cells
            extra_keys = [k for k in list(cells) if not isinstance(k, str) or k not in col_set]
            for key in extra_keys:
                del cells[key]
                events.append(
                    event(
                        code="repair.field_dropped",
                        severity="warning",
                        phase="repair",
                        role="table",
                        path=f"{path_base}/rows/{j}/cells/{key}",
                        action="drop_field",
                        result="dropped",
                        slide_number=slide_number,
                        layout_type=layout_type,
                        surface_id=surface_id,
                        expected="cell keys limited to the table columns",
                        input_meta={"field": key if isinstance(key, str) else type(key).__name__},
                    )
                )
            for cid in col_ids:
                present = cid in cells
                cell = cells.get(cid)
                if present and _well_formed_cell(cell):
                    continue
                cells[cid] = {"type": "missing"}
                if not present:
                    observed = {"type": "absent"}
                elif isinstance(cell, dict) and isinstance(cell.get("type"), str):
                    observed = {"type": cell["type"]}
                else:
                    observed = {"type": type(cell).__name__}
                events.append(
                    event(
                        code="repair.value_to_missing",
                        severity="warning",
                        phase="repair",
                        role="table",
                        path=f"{path_base}/rows/{j}/cells/{cid}",
                        action="replace_with_missing",
                        result="missing",
                        slide_number=slide_number,
                        layout_type=layout_type,
                        surface_id=surface_id,
                        expected="well-formed semantic value cell",
                        input_meta=observed,
                    )
                )
    groups = table.get("column_groups")
    if groups is not None and not _well_formed_groups(groups, col_ids):
        del table["column_groups"]
        events.append(
            event(
                code="repair.structure_flattened",
                severity="warning",
                phase="repair",
                role="table",
                path=f"{path_base}/column_groups",
                action="drop_field",
                result="flattened",
                slide_number=slide_number,
                layout_type=layout_type,
                surface_id=surface_id,
                expected="ordered contiguous column_groups over known columns",
            )
        )


def discard_inapplicable_typography(raw: Any, events: list[DiagnosticEvent]) -> Any:
    if not isinstance(raw, dict) or not isinstance(raw.get("slides"), list):
        return raw
    out = deepcopy(raw)
    for i, slide in enumerate(out["slides"]):
        if not isinstance(slide, dict):
            continue
        layout = slide.get("layout_type")
        if layout not in {
            "narrative",
            "data_table",
            "annex_table",
            "grouped_annex_table",
            "chart_grouped_annex",
            "period_comparison",
            "comparison_cards",
            "single_chart",
            "dual_chart",
            "chart_hero_dual",
            "metric_overview",
            "process_flow",
            "timeline",
            "layered_architecture",
            "data_pipeline",
            "feature_cards",
            "quotation",
            "evidence_review",
            "risk_opportunity_review",
            "recommendation_case",
            "state_transition",
            "decision_tree",
            "feedback_loop",
            "hierarchy",
            "stakeholder_map",
            "quadrant_matrix",
        }:
            continue

        surfaces_spec: list[
            tuple[str, str, str, int, int, dict[str, Any]]
        ] = []
        content = slide.get("content")
        if isinstance(content, dict):
            surfaces_spec.append(
                (
                    "content",
                    "subtitle_font_size",
                    "body_font_size|table_font_size",
                    22,
                    26,
                    content,
                )
            )
        takeaway = slide.get("takeaway")
        if isinstance(takeaway, dict):
            surfaces_spec.append(
                (
                    "takeaway",
                    "body_font_size",
                    "subtitle_font_size|table_font_size",
                    22,
                    28,
                    takeaway,
                )
            )
        payload = slide.get("payload")
        if isinstance(payload, dict):
            if layout == "narrative":
                surfaces_spec.append(
                    (
                        "payload",
                        "body_font_size",
                        "subtitle_font_size|table_font_size",
                        22,
                        28,
                        payload,
                    )
                )
            elif layout in {
                "process_flow",
                "timeline",
                "layered_architecture",
                "data_pipeline",
                "feature_cards",
                "quotation",
                "evidence_review",
                "risk_opportunity_review",
                "recommendation_case",
                "state_transition",
                "decision_tree",
                "feedback_loop",
                "hierarchy",
                "stakeholder_map",
                "quadrant_matrix",
            }:
                # D60 fixed type — no authored typography on these payloads.
                pass
            elif layout in {"single_chart", "dual_chart"}:
                supports: list[tuple[str, dict[str, Any]]] = []
                shared = payload.get("support")
                if isinstance(shared, dict):
                    supports.append(("support", shared))
                if layout == "dual_chart":
                    charts = payload.get("charts")
                    if isinstance(charts, list):
                        for j, item in enumerate(charts):
                            if isinstance(item, dict) and "chart" in item:
                                pane_support = item.get("support")
                                if isinstance(pane_support, dict):
                                    supports.append(
                                        (f"charts/{j}/support", pane_support)
                                    )
                for owner, support in supports:
                    st = support.get("support_type")
                    if st == "metric_strip":
                        surfaces_spec.append(
                            (
                                owner,
                                "body_font_size",
                                "subtitle_font_size|table_font_size",
                                14,
                                24,
                                support,
                            )
                        )
                    elif st in {"support_table", "outlined_support"}:
                        table = support.get("table")
                        if isinstance(table, dict):
                            floor = 22 if st == "outlined_support" else 14
                            surfaces_spec.append(
                                (
                                    f"{owner}/table",
                                    "table_font_size",
                                    "body_font_size|subtitle_font_size",
                                    floor,
                                    24,
                                    table,
                                )
                            )
            else:
                tables = [payload.get("table")]
                if layout in {"grouped_annex_table", "chart_grouped_annex"} and isinstance(
                    payload.get("tables"), list
                ):
                    tables = [
                        peer.get("table")
                        for peer in payload["tables"]
                        if isinstance(peer, dict)
                    ]
                for j, table in enumerate(tables):
                    if isinstance(table, dict):
                        owner = (
                            "table"
                            if layout not in {
                                "grouped_annex_table",
                                "chart_grouped_annex",
                            }
                            else f"tables/{j}/table"
                        )
                        floor = (
                            12
                            if layout
                            in {
                                "annex_table",
                                "grouped_annex_table",
                                "chart_grouped_annex",
                            }
                            else 20
                        )
                        surfaces_spec.append(
                            (
                                owner,
                                "table_font_size",
                                "body_font_size|subtitle_font_size",
                                floor,
                                24,
                                table,
                            )
                        )
                strip = payload.get("metric_strip")
                if isinstance(strip, dict):
                    surfaces_spec.append(
                        (
                            "metric_strip",
                            "body_font_size",
                            "subtitle_font_size|table_font_size",
                            14,
                            24,
                            strip,
                        )
                    )
        for owner, size_field, forbidden_csv, floor, ceiling, surface in surfaces_spec:
            has_typography = "typography" in surface
            typo = surface.get("typography")
            forbidden = set(forbidden_csv.split("|"))
            allowed = {"mode", "sync_group", size_field}
            malformed = has_typography and (
                not isinstance(typo, dict)
                or set(typo) - allowed
                or bool(forbidden.intersection(typo))
                or typo.get("mode", "adaptive") not in {"adaptive", "fixed"}
                or (
                    "sync_group" in typo
                    and (
                        typo.get("mode", "adaptive") != "adaptive"
                        or not isinstance(typo["sync_group"], str)
                        or not typo["sync_group"].strip()
                    )
                )
                or (
                    size_field in typo
                    and (
                        not isinstance(typo[size_field], int)
                        or isinstance(typo[size_field], bool)
                        or not floor <= typo[size_field] <= ceiling
                    )
                )
            )
            if malformed:
                del surface["typography"]
                path = (
                    f"/slides/{i}/payload/{owner}/typography"
                    if owner in {"table", "metric_strip", "support", "support/table"}
                    or owner.startswith(("tables/", "charts/"))
                    else f"/slides/{i}/{owner}/typography"
                )
                events.append(
                    event(
                        code="repair.policy_defaulted",
                        severity="warning",
                        phase="repair",
                        role=owner,
                        path=path,
                        action="default_typography",
                        result="defaulted",
                        slide_number=_slide_number(slide),
                        layout_type=layout if isinstance(layout, str) else None,
                        expected="surface-applicable typography fields",
                    )
                )
    return out


def repair_disclosure_sections(raw: Any, events: list[DiagnosticEvent]) -> Any:
    """D222 non-strict: drop malformed/duplicate disclosure sections; keep first.

    Deck-unique surface_id is enforced by preserving the first valid section and
    dropping later collisions diagnostically. Empty repaired disclosure is omitted.
    """
    if not isinstance(raw, dict) or not isinstance(raw.get("slides"), list):
        return raw
    out = deepcopy(raw)
    seen_ids: set[str] = set()
    for i, slide in enumerate(out["slides"]):
        if not isinstance(slide, dict) or slide.get("layout_type") not in {
            "narrative",
            "data_table",
            "annex_table",
            "grouped_annex_table",
            "chart_grouped_annex",
            "period_comparison",
            "comparison_cards",
            "single_chart",
            "dual_chart",
            "chart_hero_dual",
            "metric_overview",
            "process_flow",
            "timeline",
            "layered_architecture",
            "data_pipeline",
            "feature_cards",
            "quotation",
            "evidence_review",
            "risk_opportunity_review",
            "recommendation_case",
            "state_transition",
            "decision_tree",
            "feedback_loop",
            "hierarchy",
            "stakeholder_map",
            "quadrant_matrix",
        }:
            continue
        if "disclosure" not in slide:
            continue
        disc = slide.get("disclosure")
        path_base = f"/slides/{i}/disclosure"
        sn = _slide_number(slide)
        layout = slide.get("layout_type") if isinstance(slide.get("layout_type"), str) else None
        if disc is None or not isinstance(disc, dict) or not isinstance(disc.get("sections"), list):
            del slide["disclosure"]
            events.append(
                event(
                    code="repair.item_dropped",
                    severity="warning",
                    phase="repair",
                    role="disclosure",
                    path=path_base,
                    action="drop_field",
                    result="dropped",
                    slide_number=sn,
                    layout_type=layout,
                    expected="disclosure object with 1-4 valid sections",
                )
            )
            continue
        kept: list[dict[str, Any]] = []
        seen_titles: set[str] = set()
        for j, section in enumerate(disc["sections"]):
            if len(kept) >= 4:
                events.append(
                    event(
                        code="repair.item_dropped",
                        severity="warning",
                        phase="repair",
                        role="disclosure",
                        path=f"{path_base}/sections/{j}",
                        action="drop_item",
                        result="dropped",
                        slide_number=sn,
                        layout_type=layout,
                        expected="at most 4 disclosure sections",
                    )
                )
                continue
            spath = f"{path_base}/sections/{j}"
            if not isinstance(section, dict):
                events.append(
                    event(
                        code="repair.item_dropped",
                        severity="warning",
                        phase="repair",
                        role="disclosure",
                        path=spath,
                        action="drop_item",
                        result="dropped",
                        slide_number=sn,
                        layout_type=layout,
                        expected="disclosure section object",
                    )
                )
                continue
            sid = section.get("surface_id")
            title = section.get("title")
            items = section.get("items")
            valid_shape = (
                isinstance(sid, str)
                and bool(sid.strip())
                and isinstance(title, str)
                and bool(title.strip())
                and isinstance(items, list)
                and 1 <= len(items) <= 6
                and all(
                    isinstance(it, dict)
                    and it.get("kind") in {"paragraph", "bullet"}
                    and isinstance(it.get("text"), str)
                    and bool(it["text"].strip())
                    for it in items
                )
            )
            if not valid_shape:
                events.append(
                    event(
                        code="repair.item_dropped",
                        severity="warning",
                        phase="repair",
                        role="disclosure",
                        path=spath,
                        action="drop_item",
                        result="dropped",
                        slide_number=sn,
                        layout_type=layout,
                        expected="deck-unique surface_id, title, 1-6 plain items",
                    )
                )
                continue
            title_key = title.casefold()
            if sid in seen_ids:
                events.append(
                    event(
                        code="repair.item_dropped",
                        severity="warning",
                        phase="repair",
                        role="disclosure",
                        path=spath,
                        action="drop_item",
                        result="dropped",
                        slide_number=sn,
                        layout_type=layout,
                        expected="deck-unique disclosure surface_id",
                        input_meta={"surface_id": sid},
                    )
                )
                continue
            if title_key in seen_titles:
                events.append(
                    event(
                        code="repair.item_dropped",
                        severity="warning",
                        phase="repair",
                        role="disclosure",
                        path=spath,
                        action="drop_item",
                        result="dropped",
                        slide_number=sn,
                        layout_type=layout,
                        expected="normalized-unique disclosure title",
                        input_meta={"title": title},
                    )
                )
                continue
            seen_ids.add(sid)
            seen_titles.add(title_key)
            kept.append(section)
        if not kept:
            del slide["disclosure"]
            events.append(
                event(
                    code="repair.item_dropped",
                    severity="warning",
                    phase="repair",
                    role="disclosure",
                    path=path_base,
                    action="drop_field",
                    result="dropped",
                    slide_number=sn,
                    layout_type=layout,
                    expected="at least one valid disclosure section",
                )
            )
        else:
            slide["disclosure"] = {"sections": kept}
    return out


def repair_source_footer_names(raw: Any, events: list[DiagnosticEvent]) -> Any:
    """D217 non-strict: drop later footer IDs whose visible source_name collides."""
    if not isinstance(raw, dict) or not isinstance(raw.get("slides"), list):
        return raw
    registry = raw.get("evidence_registry")
    if not isinstance(registry, dict):
        return raw
    out = deepcopy(raw)
    reg = out.get("evidence_registry") or {}
    for i, slide in enumerate(out["slides"]):
        if not isinstance(slide, dict):
            continue
        footer = slide.get("source_footer")
        if not isinstance(footer, list):
            continue
        kept: list[Any] = []
        seen_names: set[str] = set()
        changed = False
        for j, eid in enumerate(footer):
            entry = reg.get(eid) if isinstance(eid, str) else None
            name = None
            if isinstance(entry, dict) and isinstance(entry.get("source_name"), str):
                name = entry["source_name"].casefold()
            if name is not None and name in seen_names:
                changed = True
                events.append(
                    event(
                        code="repair.item_dropped",
                        severity="warning",
                        phase="repair",
                        role="source_footer",
                        path=f"/slides/{i}/source_footer/{j}",
                        action="drop_item",
                        result="dropped",
                        slide_number=_slide_number(slide),
                        layout_type=slide.get("layout_type")
                        if isinstance(slide.get("layout_type"), str)
                        else None,
                        expected="normalized-unique source_footer source_name",
                        input_meta={"evidence_id": eid, "source_name": entry.get("source_name")}
                        if isinstance(entry, dict)
                        else {"evidence_id": eid},
                    )
                )
                continue
            if name is not None:
                seen_names.add(name)
            kept.append(eid)
        if not changed:
            continue
        if not kept:
            del slide["source_footer"]
        else:
            slide["source_footer"] = kept
    return out


def repair_uncontained_fixed_domains(raw: Any, events: list[DiagnosticEvent]) -> Any:
    """D230 non-strict: authored domain bounds that fail to contain every finite
    chart value are fixed before revalidation (strict rejects). Stacked bars also
    require zero + signed stack extents (D83/D242). A fixed domain is replaced by
    a diagnosed safe generated domain; offending authored generated min/max keys
    are dropped so the domain regenerates from the data."""
    if not isinstance(raw, dict) or not isinstance(raw.get("slides"), list):
        return raw
    out = deepcopy(raw)
    for i, slide in enumerate(out["slides"]):
        if not isinstance(slide, dict) or slide.get("layout_type") != "single_chart":
            continue
        payload = slide.get("payload")
        visual = payload.get("chart") if isinstance(payload, dict) else None
        if not isinstance(visual, dict) or visual.get("chart_type") not in (
            "line",
            "grouped_bar",
            "horizontal_bar",
            "stacked_bar",
            "combo",
            "waterfall",
        ):
            continue
        axes = visual.get("value_axes")
        primary = axes.get("primary") if isinstance(axes, dict) else None
        domain = primary.get("domain") if isinstance(primary, dict) else None
        if not isinstance(domain, dict) or domain.get("kind") not in (
            "fixed",
            "generated",
        ):
            continue
        finite: list[Decimal] = []
        if visual.get("chart_type") == "waterfall":
            # Domain containment uses authored totals/changes + running levels.
            wdata = visual.get("waterfall_data")
            steps = wdata.get("steps") if isinstance(wdata, dict) else None
            if not isinstance(steps, list):
                continue
            level = Decimal(0)
            finite.append(level)
            for step in steps:
                if not isinstance(step, dict):
                    continue
                role = step.get("role")
                raw_v = step.get("value")
                try:
                    if role == "total" and raw_v is not None:
                        level = Decimal(str(raw_v))
                        finite.append(level)
                    elif role == "change" and raw_v is not None:
                        level = level + Decimal(str(raw_v))
                        finite.append(level)
                    elif role == "computed_total":
                        finite.append(level)
                except (InvalidOperation, TypeError, ValueError):
                    continue
        else:
            data = visual.get("chart_data")
            series = data.get("series") if isinstance(data, dict) else None
            if not isinstance(series, list):
                continue
            for s in series:
                values = s.get("values") if isinstance(s, dict) else None
                if not isinstance(values, list):
                    continue
                for v in values:
                    if v is None:
                        continue
                    try:
                        finite.append(Decimal(str(v)))
                    except (InvalidOperation, TypeError, ValueError):
                        continue
            stacked_combo = (
                visual.get("chart_type") == "combo"
                and visual.get("bar_mode") == "stacked"
            )
            if visual.get("chart_type") == "stacked_bar" or stacked_combo:
                cats = data.get("categories") if isinstance(data, dict) else None
                n = len(cats) if isinstance(cats, list) else 0
                if n == 0 and series:
                    vals0 = (
                        series[0].get("values")
                        if isinstance(series[0], dict)
                        else None
                    )
                    n = len(vals0) if isinstance(vals0, list) else 0
                for c_i in range(n):
                    pos = Decimal(0)
                    neg = Decimal(0)
                    for s in series:
                        if stacked_combo and isinstance(s, dict) and s.get("mark_type") == "line":
                            continue
                        values = s.get("values") if isinstance(s, dict) else None
                        if not isinstance(values, list) or c_i >= len(values):
                            continue
                        v = values[c_i]
                        if v is None:
                            continue
                        try:
                            dv = Decimal(str(v))
                        except (InvalidOperation, TypeError, ValueError):
                            continue
                        if dv > 0:
                            pos += dv
                        elif dv < 0:
                            neg += dv
                    finite.extend((pos, neg, Decimal(0)))
        if not finite:
            continue
        domain_path = (
            f"/slides/{i}/payload/chart/value_axes/primary/domain"
        )
        if domain.get("kind") == "fixed":
            try:
                lo = Decimal(str(domain.get("min")))
                hi = Decimal(str(domain.get("max")))
            except (InvalidOperation, TypeError, ValueError):
                continue
            if all(lo <= dv <= hi for dv in finite):
                continue
            primary["domain"] = {"kind": "generated"}
            events.append(
                event(
                    code="repair.domain_replaced",
                    severity="warning",
                    phase="repair",
                    role="value_axis",
                    path=domain_path,
                    action="replace_domain",
                    result="generated",
                    slide_number=_slide_number(slide),
                    layout_type="single_chart",
                    expected="fixed domain containing every finite value",
                )
            )
            continue
        for key in ("min", "max"):
            raw_bound = domain.get(key)
            if raw_bound is None:
                continue
            try:
                bound = Decimal(str(raw_bound))
            except (InvalidOperation, TypeError, ValueError):
                continue
            if key == "min":
                uncontained = any(dv < bound for dv in finite)
            else:
                uncontained = any(dv > bound for dv in finite)
            if not uncontained:
                continue
            del domain[key]
            events.append(
                event(
                    code="repair.domain_replaced",
                    severity="warning",
                    phase="repair",
                    role="value_axis",
                    path=f"{domain_path}/{key}",
                    action="drop_field",
                    result="dropped",
                    slide_number=_slide_number(slide),
                    layout_type="single_chart",
                    expected=f"generated domain {key} containing every finite value",
                )
            )
    return out


def repair_invalid_heatmap_scales(raw: Any, events: list[DiagnosticEvent]) -> Any:
    """D163/D308 non-strict: missing/malformed/out-of-range heatmap scales become
    generated so validation can proceed; freeze paints uncolored when the repair
    marks the visual (scale replaced → no trusted encoding)."""
    if not isinstance(raw, dict) or not isinstance(raw.get("slides"), list):
        return raw
    out = deepcopy(raw)
    for i, slide in enumerate(out["slides"]):
        if not isinstance(slide, dict) or slide.get("layout_type") != "single_chart":
            continue
        payload = slide.get("payload")
        visual = payload.get("chart") if isinstance(payload, dict) else None
        if not isinstance(visual, dict) or visual.get("chart_type") != "heatmap":
            continue
        scale = visual.get("scale")
        table = visual.get("table_data")
        finite: list[Decimal] = []
        if isinstance(table, dict) and isinstance(table.get("rows"), list):
            for row in table["rows"]:
                cells = row.get("cells") if isinstance(row, dict) else None
                if not isinstance(cells, dict):
                    continue
                for cell in cells.values():
                    if not isinstance(cell, dict) or cell.get("type") != "number":
                        continue
                    try:
                        finite.append(Decimal(str(cell.get("value"))))
                    except (InvalidOperation, TypeError, ValueError):
                        continue
        path = f"/slides/{i}/payload/chart/scale"
        bad = False
        if not isinstance(scale, dict) or scale.get("mode") not in ("generated", "fixed"):
            bad = True
        elif scale.get("mode") == "fixed":
            try:
                lo = Decimal(str(scale.get("min")))
                hi = Decimal(str(scale.get("max")))
            except (InvalidOperation, TypeError, ValueError):
                bad = True
            else:
                if lo >= hi or (finite and any(v < lo or v > hi for v in finite)):
                    bad = True
        if not bad:
            continue
        visual["scale"] = {"mode": "generated"}
        events.append(
            event(
                code="repair.domain_replaced",
                severity="warning",
                phase="repair",
                role="heatmap",
                path=path,
                action="replace_domain",
                result="fallback_semantic_table",
                slide_number=_slide_number(slide),
                layout_type="single_chart",
                surface_id=(
                    visual.get("surface_id")
                    if isinstance(visual.get("surface_id"), str)
                    else None
                ),
                expected="generated or fixed min<max scale containing every finite value",
            )
        )
    return out


# Closed registry: name → transform (D123).
def repair_card_compositions(raw: Any, events: list[DiagnosticEvent]) -> Any:
    """Non-strict repairs for cards/reviews (D281–D286): icons, refs, items."""
    if not isinstance(raw, dict) or not isinstance(raw.get("slides"), list):
        return raw
    from .models import FEATURE_ICON_KEYS

    out = deepcopy(raw)
    icon_set = set(FEATURE_ICON_KEYS)
    for i, slide in enumerate(out["slides"]):
        if not isinstance(slide, dict):
            continue
        layout = slide.get("layout_type")
        sn = _slide_number(slide)
        payload = slide.get("payload")
        if not isinstance(payload, dict):
            continue

        # D287: drop forbidden common fields when meaning remains complete.
        if layout == "evidence_review" and "source_footer" in slide:
            del slide["source_footer"]
            events.append(
                event(
                    code="repair.field_dropped",
                    severity="warning",
                    phase="repair",
                    role="source_footer",
                    path=f"/slides/{i}/source_footer",
                    action="drop_field",
                    result="dropped",
                    slide_number=sn,
                    layout_type=layout,
                    expected="evidence_review forbids source_footer",
                )
            )
        if layout == "recommendation_case" and "takeaway" in slide:
            del slide["takeaway"]
            events.append(
                event(
                    code="repair.field_dropped",
                    severity="warning",
                    phase="repair",
                    role="takeaway",
                    path=f"/slides/{i}/takeaway",
                    action="drop_field",
                    result="dropped",
                    slide_number=sn,
                    layout_type=layout,
                    expected="recommendation_case forbids takeaway",
                )
            )

        if layout == "feature_cards":
            cards = payload.get("cards")
            if not isinstance(cards, list):
                continue
            for j, card in enumerate(cards):
                if not isinstance(card, dict):
                    continue
                key = card.get("icon_key")
                if key is None:
                    continue
                if not isinstance(key, str) or key not in icon_set:
                    del card["icon_key"]
                    events.append(
                        event(
                            code="repair.field_dropped",
                            severity="warning",
                            phase="repair",
                            role="icon_key",
                            path=f"/slides/{i}/payload/cards/{j}/icon_key",
                            action="drop_field",
                            result="dropped",
                            slide_number=sn,
                            layout_type=layout,
                            expected="closed feature_cards icon registry",
                        )
                    )

        if layout == "evidence_review":
            findings = payload.get("findings")
            if not isinstance(findings, list):
                continue
            slide_eids = set(slide.get("evidence_ids") or [])
            cleaned: list[Any] = []
            for j, finding in enumerate(findings):
                if not isinstance(finding, dict):
                    events.append(
                        event(
                            code="repair.item_dropped",
                            severity="warning",
                            phase="repair",
                            role="finding",
                            path=f"/slides/{i}/payload/findings/{j}",
                            action="drop_item",
                            result="dropped",
                            slide_number=sn,
                            layout_type=layout,
                            expected="finding with statement + evidence_ids",
                        )
                    )
                    continue
                stmt = finding.get("statement")
                if not isinstance(stmt, dict) or not stmt.get("runs"):
                    events.append(
                        event(
                            code="repair.item_dropped",
                            severity="warning",
                            phase="repair",
                            role="finding",
                            path=f"/slides/{i}/payload/findings/{j}",
                            action="drop_item",
                            result="dropped",
                            slide_number=sn,
                            layout_type=layout,
                            expected="finding with statement + evidence_ids",
                        )
                    )
                    continue
                refs = finding.get("evidence_ids")
                kept: list[Any] = []
                if isinstance(refs, list):
                    for k, eid in enumerate(refs):
                        if isinstance(eid, str) and eid in slide_eids and eid not in kept:
                            kept.append(eid)
                        else:
                            events.append(
                                event(
                                    code="repair.reference_dropped",
                                    severity="warning",
                                    phase="repair",
                                    role="evidence_ids",
                                    path=(
                                        f"/slides/{i}/payload/findings/{j}/"
                                        f"evidence_ids/{k}"
                                    ),
                                    action="drop_reference",
                                    result="dropped",
                                    slide_number=sn,
                                    layout_type=layout,
                                    expected=(
                                        "finding evidence_ids ⊆ slide evidence_ids"
                                    ),
                                )
                            )
                finding["evidence_ids"] = kept
                if not kept:
                    finding["refs_repaired"] = True
                cleaned.append(finding)
            payload["findings"] = cleaned

        if layout == "risk_opportunity_review":
            for group_key in ("risks", "opportunities"):
                items = payload.get(group_key)
                if not isinstance(items, list):
                    continue
                kept_items = []
                for j, it in enumerate(items):
                    if (
                        isinstance(it, dict)
                        and isinstance(it.get("item_id"), str)
                        and isinstance(it.get("statement"), dict)
                        and it["statement"].get("runs")
                    ):
                        kept_items.append(it)
                    else:
                        events.append(
                            event(
                                code="repair.item_dropped",
                                severity="warning",
                                phase="repair",
                                role=group_key,
                                path=f"/slides/{i}/payload/{group_key}/{j}",
                                action="drop_item",
                                result="dropped",
                                slide_number=sn,
                                layout_type=layout,
                                expected=f"valid {group_key} item",
                            )
                        )
                payload[group_key] = kept_items
            if not payload.get("risks") or not payload.get("opportunities"):
                payload["groups_repaired"] = True

        if layout == "recommendation_case":
            rats = payload.get("rationales")
            if isinstance(rats, list):
                kept_r = []
                for j, r in enumerate(rats):
                    if (
                        isinstance(r, dict)
                        and isinstance(r.get("rationale_id"), str)
                        and isinstance(r.get("statement"), dict)
                        and r["statement"].get("runs")
                    ):
                        kept_r.append(r)
                    else:
                        events.append(
                            event(
                                code="repair.item_dropped",
                                severity="warning",
                                phase="repair",
                                role="rationale",
                                path=f"/slides/{i}/payload/rationales/{j}",
                                action="drop_item",
                                result="dropped",
                                slide_number=sn,
                                layout_type=layout,
                                expected="valid rationale",
                            )
                        )
                payload["rationales"] = kept_r
                if not kept_r:
                    payload["support_repaired"] = True

        if layout == "quotation":
            quotes = payload.get("quotes")
            if not isinstance(quotes, list):
                continue
            slide_eids = set(slide.get("evidence_ids") or [])
            for j, q in enumerate(quotes):
                if not isinstance(q, dict):
                    continue
                eid = q.get("evidence_id")
                if eid is None:
                    continue
                if not isinstance(eid, str) or eid not in slide_eids:
                    del q["evidence_id"]
                    q["provenance_unavailable"] = True
                    events.append(
                        event(
                            code="repair.reference_dropped",
                            severity="warning",
                            phase="repair",
                            role="evidence_id",
                            path=f"/slides/{i}/payload/quotes/{j}/evidence_id",
                            action="drop_reference",
                            result="dropped",
                            slide_number=sn,
                            layout_type=layout,
                            expected="quote evidence_id among slide evidence_ids",
                        )
                    )

        if layout == "state_transition":
            steps = payload.get("transition_steps")
            if isinstance(steps, list):
                kept_s = []
                for j, s in enumerate(steps):
                    if (
                        isinstance(s, dict)
                        and isinstance(s.get("step_id"), str)
                        and isinstance(s.get("heading"), str)
                        and s.get("heading")
                    ):
                        kept_s.append(s)
                    else:
                        events.append(
                            event(
                                code="repair.item_dropped",
                                severity="warning",
                                phase="repair",
                                role="transition_step",
                                path=f"/slides/{i}/payload/transition_steps/{j}",
                                action="drop_item",
                                result="dropped",
                                slide_number=sn,
                                layout_type=layout,
                                expected="valid transition step",
                            )
                        )
                if kept_s:
                    payload["transition_steps"] = kept_s
                else:
                    payload.pop("transition_steps", None)
    return out


def repair_required_composition_headings(
    raw: Any, events: list[DiagnosticEvent]
) -> Any:
    """D170 non-strict: fill missing dual/hero headings with neutral wording."""
    if not isinstance(raw, dict) or not isinstance(raw.get("slides"), list):
        return raw
    out = deepcopy(raw)
    for i, slide in enumerate(out["slides"]):
        if not isinstance(slide, dict):
            continue
        layout = slide.get("layout_type")
        payload = slide.get("payload")
        if not isinstance(payload, dict):
            continue
        sn = _slide_number(slide)
        if layout == "dual_chart":
            charts = payload.get("charts")
            if not isinstance(charts, list):
                continue
            for j, item in enumerate(charts):
                if not isinstance(item, dict):
                    continue
                if "chart" in item and isinstance(item.get("chart"), dict):
                    chart = item["chart"]
                    path = f"/slides/{i}/payload/charts/{j}/chart/heading"
                else:
                    chart = item
                    path = f"/slides/{i}/payload/charts/{j}/heading"
                if not chart.get("heading"):
                    chart["heading"] = f"Untitled chart {j + 1}"
                    events.append(
                        event(
                            code="repair.policy_defaulted",
                            severity="warning",
                            phase="repair",
                            role="heading",
                            path=path,
                            action="default_display",
                            result="canonicalized",
                            slide_number=sn,
                            layout_type=layout,
                            expected="non-empty dual_chart heading",
                        )
                    )
        elif layout in {"chart_hero_dual", "chart_grouped_annex"}:
            chart = payload.get("chart")
            if isinstance(chart, dict) and not chart.get("heading"):
                chart["heading"] = "Untitled chart 1"
                events.append(
                    event(
                        code="repair.policy_defaulted",
                        severity="warning",
                        phase="repair",
                        role="heading",
                        path=f"/slides/{i}/payload/chart/heading",
                        action="default_display",
                        result="canonicalized",
                        slide_number=sn,
                        layout_type=layout,
                        expected=f"non-empty {layout} chart heading",
                    )
                )
            if layout != "chart_hero_dual":
                continue
            hero = payload.get("hero")
            if isinstance(hero, dict) and not hero.get("heading"):
                hero["heading"] = "Untitled summary"
                events.append(
                    event(
                        code="repair.policy_defaulted",
                        severity="warning",
                        phase="repair",
                        role="heading",
                        path=f"/slides/{i}/payload/hero/heading",
                        action="default_display",
                        result="canonicalized",
                        slide_number=sn,
                        layout_type=layout,
                        expected="non-empty chart_hero_dual hero heading",
                    )
                )
    return out


REPAIR_REGISTRY: dict[str, RepairFn] = {
    "assume_schema_v1": assume_schema_v1,
    "drop_unknown_fields": drop_unknown_fields,
    "repair_table_data": repair_table_data,
    "discard_inapplicable_typography": discard_inapplicable_typography,
    "repair_disclosure_sections": repair_disclosure_sections,
    "repair_source_footer_names": repair_source_footer_names,
    "repair_uncontained_fixed_domains": repair_uncontained_fixed_domains,
    "repair_invalid_heatmap_scales": repair_invalid_heatmap_scales,
    "repair_card_compositions": repair_card_compositions,
    "repair_required_composition_headings": repair_required_composition_headings,
}

def apply_allowlisted_repairs(raw: Any) -> tuple[Any, list[DiagnosticEvent]]:
    """Apply every kernel allowlisted repair in stable order; collect events.

    ``assume_schema_v1`` runs first and only keeps the edit when the rest of the
    input is already exact v1 (D311). Unknown-field drops never unlock assume.
    """
    events: list[DiagnosticEvent] = []
    current = raw
    for name in REPAIR_REGISTRY:
        current = REPAIR_REGISTRY[name](current, events)
    return current, events
