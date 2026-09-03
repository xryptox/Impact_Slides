"""Offline legacy handoff → schema-v1 candidate migrator (D119/D313/D316).

Never mutates sources. Converts only mechanically proven structures. Human and
failed-proof cases become unresolved decisions. The v1 marker is withheld until
every slide resolves and the candidate validates.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from .diagnostics import RendererValidationError
from .ids import is_semantic_id
from .validate import validate_handoff

INVENTORY_SIZE = 57

# ---------------------------------------------------------------------------
# D313 inventory — exactly 57 inputs, each classified once
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class InventoryEntry:
    legacy_input: str
    classification: str  # deterministic | human | removed_sentinel
    target: Optional[str] = None
    candidates: tuple[str, ...] = ()
    proof: str = ""
    reason: str = ""
    chart_family: Optional[str] = None  # D313 single_chart/<family> branch


def _det(
    name: str,
    target: str,
    proof: str,
    *,
    chart_family: Optional[str] = None,
) -> InventoryEntry:
    return InventoryEntry(
        name, "deterministic", target=target, proof=proof, chart_family=chart_family
    )


def _human(name: str, candidates: tuple[str, ...], reason: str) -> InventoryEntry:
    return InventoryEntry(name, "human", candidates=candidates, reason=reason)


def _sent(name: str) -> InventoryEntry:
    return InventoryEntry(
        name,
        "removed_sentinel",
        reason="No target; prove a D210 composition or leave unresolved.",
    )


_LEGACY_ENTRIES: tuple[InventoryEntry, ...] = (
    # Deterministic (37) — D313 table, aliases counted separately where listed
    _det("annex_table", "annex_table", "One complete dense typed matrix and disclosure boundaries."),
    _det("before_after", "state_transition", "Explicit before/after boundaries."),
    _det("before_after_detailed", "state_transition", "Explicit before/after boundaries; optional steps."),
    _det("chart_hero_dual", "chart_hero_dual", "Exactly one chart, recognized hero, at most one typed support."),
    _det("circular_process", "feedback_loop", "One explicit ordered cycle."),
    _det("combo_chart", "single_chart", "Explicit combo marks/axes/categories/values/formats/identities.", chart_family="combo"),
    _det("comparison_grid", "comparison_cards", "One complete 2–4 peer by 2–4 shared-fact table."),
    _det("three_column_comparison", "comparison_cards", "One complete 2–4 peer by 2–4 shared-fact table."),
    _det("data_table", "data_table", "One complete typed ordinary table."),
    _det("table", "data_table", "One complete typed ordinary table."),
    _det("data_table_with_insight", "data_table", "Complete table and one unambiguous slide-level insight."),
    _det("decision_tree", "decision_tree", "Explicit root, decisions, labeled branches, targets, outcomes."),
    _det("dual_chart", "dual_chart", "Exactly two ordered charts; optional shared independent support_table or metric_strip under both panes."),
    _det("ecosystem_map", "stakeholder_map", "One focal entity and only explicitly labeled/directed focal spokes."),
    _det("evidence_cards", "evidence_review", "Exact findings and explicit evidence mappings."),
    _det("full_process_flow", "process_flow", "Genuinely linear ordered steps."),
    _det("horizontal_process", "process_flow", "Genuinely linear ordered steps."),
    _det("grouped_annex_table", "grouped_annex_table", "One or two explicitly headed complete annex matrices."),
    _det("grouped_bar_chart", "single_chart", "Explicit vertical non-stacked data, format, and identity.", chart_family="grouped_bar"),
    _det("heatmap", "single_chart", "Rectangular identities, numeric/missing cells, one format, explicit scale.", chart_family="heatmap"),
    _det("hierarchy_tree", "hierarchy", "Explicit root, uniform relation, links, and sibling order."),
    _det("horizontal_bar_chart", "single_chart", "Explicit grouped horizontal semantics.", chart_family="horizontal_bar"),
    _det("icon_grid", "feature_cards", "Equal-rank cards and decorative icons from the closed registry."),
    _det("ir_bullet_sheet", "narrative", "Text-only with explicit paragraph/list boundaries."),
    _det("line_chart", "single_chart", "Explicit categories, series, values, axes, formats, and identities.", chart_family="line"),
    _det("metric", "metric_overview", "One canonical 2–6 metric source without unresolved duplicates."),
    _det("metric_dashboard", "metric_overview", "One canonical 2–6 metric source without unresolved duplicates."),
    _det("metric_row_with_breakdown", "metric_overview", "Explicit metric and narrative-detail boundaries."),
    _det("pill_comparison", "period_comparison", "Explicit current/comparison/variance roles."),
    _det("priority_matrix", "quadrant_matrix", "Explicit binary axes/endpoints and item assignments."),
    _det("quote_card", "quotation", "Explicit quote paragraphs and attribution fields."),
    _det("recommendation_with_rationale", "recommendation_case", "One exact recommendation and explicit rationales."),
    _det("risk_opportunity", "risk_opportunity_review", "Explicit risk/opportunity membership."),
    _det("section_divider", "section_divider", "Registered section and correct immediate placement."),
    _det("stacked_bar_chart", "single_chart", "Explicit stack order/data/format/display.", chart_family="stacked_bar"),
    _det("timeline", "timeline", "Explicit milestones/time labels in authored order."),
    _det("waterfall_chart", "single_chart", "Explicit ordered step roles, values, format, and resets.", chart_family="waterfall"),
    # Human (17)
    _human("brand_cover", ("opening_cover", "closing_cover"), "One recipe served both deck boundaries."),
    _human("brand_divider", ("section_divider", "closing_cover"), "Current Amex uses both meanings."),
    _human("causal_loop", ("feedback_loop",), "Legacy arrows do not prove causal edge polarity."),
    # D313 prose also names "separate slides"; omitted deliberately — not a single
    # composition target, so it is not a candidate token in this inventory.
    _human(
        "comparison_with_metrics",
        ("comparison_cards", "metric_overview"),
        "Detached metric ownership is ambiguous.",
    ),
    _human(
        "cover",
        ("opening_cover", "closing_cover", "other"),
        "Alias of ambiguous title_or_opening.",
    ),
    _human(
        "data_flow_diagram",
        ("data_pipeline", "process_flow", "layered_architecture", "future"),
        "Generic graph does not prove relationship semantics.",
    ),
    _human(
        "freeform_grid",
        ("any_d210_composition",),
        "Coordinates are presentation, not semantics.",
    ),
    _human(
        "guidance_statement_card",
        ("metric_overview",),
        "Ranges, periods, status, and qualification ownership need confirmation.",
    ),
    _human(
        "insight_with_evidence",
        ("evidence_review", "recommendation_case", "narrative", "other"),
        "Insight and evidence ownership are ambiguous.",
    ),
    _human(
        "kpi_trend_cards",
        ("metric_overview", "comparison_cards", "single_chart"),
        "Cards may encode metrics, peers, trends, or duplicates.",
    ),
    _human(
        "multi_panel",
        ("dual_chart", "chart_hero_dual", "named_composition", "future"),
        "Only exact recognized semantic shapes can convert.",
    ),
    _human(
        "process_with_decisions",
        ("decision_tree", "process_flow", "future"),
        "Branch targets and node roles are not explicit.",
    ),
    _human(
        "roadmap",
        ("timeline", "process_flow", "future"),
        "Chronology versus procedure/phases is ambiguous.",
    ),
    _human(
        "source_deep_dive",
        ("evidence_review", "quotation", "narrative", "other"),
        "Finding, quotation, and provenance ownership are unclear.",
    ),
    _human(
        "split_text_visual",
        ("narrative", "state_transition", "comparison_cards", "other"),
        "Split geometry does not identify semantic roles.",
    ),
    _human(
        "system_architecture",
        ("layered_architecture", "hierarchy", "data_pipeline", "stakeholder_map", "future"),
        "Nodes and links do not prove grouping, parentage, flow, or spokes.",
    ),
    _human(
        "title_or_opening",
        ("opening_cover", "closing_cover", "section_divider", "ordinary"),
        "Legacy name conflates title and deck role.",
    ),
    # Removed sentinels (3)
    _sent(""),
    _sent("default"),
    _sent("other"),
)

LEGACY_INVENTORY: dict[str, InventoryEntry] = {e.legacy_input: e for e in _LEGACY_ENTRIES}
assert len(LEGACY_INVENTORY) == INVENTORY_SIZE

_SLUG_RE = re.compile(r"[^a-z0-9]+")

_PERIOD_ROLE_ALIASES: dict[str, str] = {
    "current_period": "current_period",
    "current": "current_period",
    "curr": "current_period",
    "comparison_period": "comparison_period",
    "comparison": "comparison_period",
    "prior": "comparison_period",
    "previous": "comparison_period",
    "variance": "variance",
    "var": "variance",
    "yoy": "variance",
    "delta": "variance",
}


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class UnresolvedDecision:
    slide_number: Optional[int]
    path: str
    legacy_input: str
    reason: str
    candidates: tuple[str, ...] = ()
    target: Optional[str] = None


@dataclass(slots=True)
class SlideDisposition:
    slide_number: int
    legacy_input: str
    classification: str
    status: str  # resolved | unresolved
    target: Optional[str] = None
    candidates: tuple[str, ...] = ()
    proof_result: str = ""
    source_path: str = ""


@dataclass(slots=True)
class MigrationResult:
    ok: bool
    exit_code: int
    wrote: bool
    version_marked: bool
    candidate: Optional[dict[str, Any]]
    unresolved: list[UnresolvedDecision]
    slide_dispositions: list[SlideDisposition]
    inventory_report: list[dict[str, Any]]
    validation_errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slug(text: str, *, fallback: str) -> str:
    s = _SLUG_RE.sub("-", (text or "").strip().lower()).strip("-")
    if not s:
        s = fallback
    if s[0].isdigit():
        s = f"n-{s}"
    s = s[:64]
    if not is_semantic_id(s):
        s = fallback
    return s


def _unique_slug(base: str, used: set[str], fallback: str) -> str:
    s = _slug(base, fallback=fallback)
    if s not in used:
        used.add(s)
        return s
    n = 2
    while True:
        suffix = f"-{n}"
        cand = (s[: 64 - len(suffix)] + suffix) if len(s) + len(suffix) > 64 else s + suffix
        if cand[0].isdigit():
            cand = f"n-{cand}"
        if is_semantic_id(cand) and cand not in used:
            used.add(cand)
            return cand
        n += 1


def _register_surface_ids(node: Any, used: set[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "surface_id" and isinstance(value, str):
                node[key] = _unique_slug(value, used, fallback=value)
            else:
                _register_surface_ids(value, used)
    elif isinstance(node, list):
        for item in node:
            _register_surface_ids(item, used)


def _referenced_format_ids(node: Any) -> set[str]:
    ids: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "format_id" and isinstance(value, str):
                ids.add(value)
            else:
                ids |= _referenced_format_ids(value)
    elif isinstance(node, list):
        for item in node:
            ids |= _referenced_format_ids(item)
    return ids


def _raw_layout(slide: Mapping[str, Any]) -> str:
    """Return the inventory key for a slide without collapsing aliases."""
    if _has_freeform(slide):
        return "freeform_grid"
    raw = slide.get("layout_type")
    if raw is None:
        return ""
    if not isinstance(raw, str):
        return "other"
    lt = raw.strip().lower()
    if lt in ("", "default", "other"):
        return lt
    return lt


def _has_freeform(slide: Mapping[str, Any]) -> bool:
    vs = slide.get("visual_spec")
    if not isinstance(vs, dict):
        return False
    grid = vs.get("grid")
    if not isinstance(grid, dict):
        return False
    areas = grid.get("template_areas")
    slots = grid.get("slots")
    return isinstance(areas, list) and len(areas) >= 1 and isinstance(slots, dict) and bool(slots)


def _content(slide: Mapping[str, Any]) -> dict[str, Any]:
    c = slide.get("content")
    return c if isinstance(c, dict) else {}


def _primary_steps(slide: Mapping[str, Any]) -> Any:
    vs = slide.get("visual_spec")
    if not isinstance(vs, dict):
        return None
    pv = vs.get("primary_visual")
    if not isinstance(pv, dict):
        return None
    return pv.get("steps_or_data")


def _text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value if value.strip() else None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return None


def _matrix_from_steps(steps: Any) -> Optional[tuple[list[str], list[list[Optional[str]]]]]:
    """Header row + body rows of equal width; strings only (no invention)."""
    if not isinstance(steps, list) or len(steps) < 2:
        return None
    rows: list[list[Any]] = []
    for row in steps:
        if not isinstance(row, (list, tuple)) or not row:
            return None
        rows.append(list(row))
    width = len(rows[0])
    if width < 2:
        return None
    if any(len(r) != width for r in rows):
        return None
    header = [_text(c) for c in rows[0]]
    if any(h is None for h in header):
        return None
    body: list[list[Optional[str]]] = []
    for r in rows[1:]:
        cells: list[Optional[str]] = []
        for c in r:
            if c is None:
                cells.append(None)
            elif isinstance(c, str) and not c.strip():
                cells.append(None)
            else:
                t = _text(c)
                if t is None:
                    return None
                cells.append(t)
        # first cell is stub label — required non-empty
        if cells[0] is None:
            return None
        body.append(cells)
    if not body:
        return None
    return [h for h in header if h is not None], body  # type: ignore[return-value]


def _table_payload_from_matrix(
    matrix: tuple[list[str], list[list[Optional[str]]]],
    *,
    surface_fallback: str,
) -> dict[str, Any]:
    header, body = matrix
    used_cols: set[str] = set()
    used_rows: set[str] = set()
    stub = header[0]
    columns = []
    for i, label in enumerate(header[1:]):
        cid = _unique_slug(label, used_cols, fallback=f"col-{i+1}")
        columns.append({"column_id": cid, "label": label})
    rows = []
    for i, brow in enumerate(body):
        rid = _unique_slug(brow[0] or f"row-{i+1}", used_rows, fallback=f"row-{i+1}")
        cells: dict[str, Any] = {}
        for col, raw in zip(columns, brow[1:]):
            if raw is None:
                cells[col["column_id"]] = {"type": "missing"}
            else:
                cells[col["column_id"]] = {"type": "text", "text": raw}
        rows.append({"row_id": rid, "label": brow[0], "cells": cells})
    return {
        "table": {
            "surface_id": _slug(surface_fallback, fallback="table-1"),
            "stub_header": {"label": stub},
            "columns": columns,
            "rows": rows,
        }
    }


def _section_id_for(
    slide: Mapping[str, Any], used: set[str], sections: dict[str, str], *, register: bool = True
) -> str:
    label = _text(slide.get("section")) or _text(_content(slide).get("section")) or "section"
    # Prefer existing label match
    for sid, lab in sections.items():
        if lab.casefold() == label.casefold():
            return sid
    if not register:
        return ""
    sid = _unique_slug(label, used, fallback=f"section-{len(used)+1}")
    sections[sid] = label
    used.add(sid)
    return sid


def _evidence_from_slide(
    slide: Mapping[str, Any], registry: dict[str, dict[str, Any]]
) -> Optional[list[str]]:
    sources = slide.get("evidence_sources")
    if not isinstance(sources, list) or not sources:
        return None
    ids: list[str] = []
    for i, src in enumerate(sources):
        if not isinstance(src, dict):
            continue
        raw_id = src.get("id") or src.get("evidence_id")
        name = (
            _text(src.get("source_name"))
            or _text(src.get("source_file"))
            or _text(src.get("name"))
            or f"Source {i+1}"
        )
        if isinstance(raw_id, str) and is_semantic_id(raw_id.strip().lower()):
            eid = raw_id.strip().lower()
        else:
            eid = _slug(str(raw_id or name), fallback=f"src-{i+1}")
        if eid not in registry:
            entry: dict[str, Any] = {"source_name": name}
            locator: dict[str, Any] = {}
            for k in ("page", "sheet", "url", "path"):
                if k in src and src[k] is not None:
                    locator[k] = src[k]
            if locator:
                entry["locator"] = locator
            registry[eid] = entry
        if eid not in ids:
            ids.append(eid)
    return ids or None


# Layouts that forbid root disclosure on schema-v1 slides.
_NO_DISCLOSURE_LAYOUTS = frozenset(
    {"opening_cover", "closing_cover", "section_divider", "legal_notice"}
)


def _disclosure_locations(
    slide: Mapping[str, Any],
) -> list[tuple[str, Any]]:
    """Return (json-path, value) for every authored disclosure bag."""
    locs: list[tuple[str, Any]] = []
    if "disclosure" in slide and slide.get("disclosure") is not None:
        locs.append(("/disclosure", slide["disclosure"]))
    content = slide.get("content")
    if isinstance(content, dict) and content.get("disclosure") is not None:
        locs.append(("/content/disclosure", content["disclosure"]))
    vs = slide.get("visual_spec")
    if isinstance(vs, dict) and vs.get("disclosure") is not None:
        locs.append(("/visual_spec/disclosure", vs["disclosure"]))
    return locs


def _map_disclosure(
    slide: Mapping[str, Any],
    *,
    slide_number: int,
    path: str,
    legacy_input: str,
    target: Optional[str],
) -> tuple[Optional[dict[str, Any]], Optional[UnresolvedDecision]]:
    """Canonical-only disclosure map (Q3B/Q4A).

    Maps only top-level ``disclosure.panels[{title, body:str}]`` within schema
    caps. Recognized-but-unmapped shapes and cap overflow become unresolved
    decisions — never silent drops. Absent/empty disclosure → (None, None).
    Deck-unique surface_ids are finalized later by ``_register_surface_ids``.
    """
    locs = _disclosure_locations(slide)
    if not locs:
        return None, None

    def _unres(suffix: str, msg: str) -> UnresolvedDecision:
        return UnresolvedDecision(
            slide_number,
            f"{path}{suffix}",
            legacy_input,
            msg,
            target=target,
        )

    nested = [(p, v) for p, v in locs if p != "/disclosure"]
    if nested:
        where = nested[0][0]
        return None, _unres(
            where,
            "Proof failed: authored disclosure is nested under "
            f"{where}; only top-level disclosure.panels maps mechanically.",
        )

    raw = locs[0][1]
    if not isinstance(raw, dict):
        return None, _unres(
            "/disclosure",
            "Proof failed: disclosure must be an object with panels.",
        )
    if not raw:
        return None, None

    has_panels = isinstance(raw.get("panels"), list)
    has_items = "items" in raw and raw.get("items") is not None
    shorthand_keys = ("body", "content", "text", "title", "summary", "label")
    has_shorthand = any(k in raw for k in shorthand_keys) and not has_panels

    if has_items and not has_panels:
        return None, _unres(
            "/disclosure/items",
            "Proof failed: disclosure uses items container; only panels maps.",
        )
    if has_shorthand:
        return None, _unres(
            "/disclosure",
            "Proof failed: disclosure title+body shorthand is not canonical; "
            "only disclosure.panels maps.",
        )
    if not has_panels:
        # Pattern-only / empty declaration — nothing authored to preserve.
        return None, None

    panels = raw["panels"]
    assert isinstance(panels, list)
    if not panels:
        return None, None
    if len(panels) > 4:
        return None, _unres(
            "/disclosure/panels",
            f"Proof failed: disclosure has {len(panels)} panels; "
            "schema-v1 allows at most 4 (never truncate).",
        )

    sections: list[dict[str, Any]] = []
    local_ids: set[str] = set()
    for i, panel in enumerate(panels):
        pp = f"/disclosure/panels/{i}"
        if isinstance(panel, str):
            return None, _unres(
                pp,
                "Proof failed: bare-string disclosure panel is not canonical.",
            )
        if not isinstance(panel, dict):
            return None, _unres(
                pp,
                "Proof failed: disclosure panel must be an object.",
            )

        title = _text(panel.get("title"))
        if not title and (panel.get("label") is not None or panel.get("summary") is not None):
            return None, _unres(
                pp,
                "Proof failed: disclosure panel uses label/summary title alias; "
                "only title maps.",
            )

        body_raw = panel.get("body")
        if isinstance(body_raw, list):
            return None, _unres(
                f"{pp}/body",
                "Proof failed: disclosure panel body is a list; only string body maps.",
            )
        if body_raw is not None and not isinstance(body_raw, str):
            return None, _unres(
                f"{pp}/body",
                "Proof failed: disclosure panel body must be a string.",
            )
        body = _text(body_raw)
        if not body and (
            panel.get("content") is not None or panel.get("text") is not None
        ):
            return None, _unres(
                pp,
                "Proof failed: disclosure panel uses content/text body alias; "
                "only body maps.",
            )

        if not title or not body:
            return None, _unres(
                pp,
                "Proof failed: canonical disclosure panel needs non-empty title and body.",
            )

        parts = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
        if not parts:
            parts = [body]
        if len(parts) > 6:
            return None, _unres(
                f"{pp}/body",
                f"Proof failed: disclosure body splits into {len(parts)} paragraphs; "
                "schema-v1 allows at most 6 items per section (never truncate).",
            )

        sid = _unique_slug(
            title, local_ids, fallback=f"disc-{slide_number}-{i + 1}"
        )
        sections.append(
            {
                "surface_id": sid,
                "title": title,
                "items": [{"kind": "paragraph", "text": p} for p in parts],
            }
        )

    return {"sections": sections}, None


def _attach_disclosure(
    slide: Mapping[str, Any],
    converted: dict[str, Any],
    *,
    slide_number: int,
    path: str,
    legacy_input: str,
) -> Optional[UnresolvedDecision]:
    """Attach mapped disclosure or return unresolved; mutates converted on success."""
    layout = converted.get("layout_type")
    target = layout if isinstance(layout, str) else None
    locs = _disclosure_locations(slide)
    if not locs:
        return None
    if target in _NO_DISCLOSURE_LAYOUTS:
        return UnresolvedDecision(
            slide_number,
            f"{path}/disclosure",
            legacy_input,
            f"Proof failed: layout {target!r} forbids disclosure but authored "
            "disclosure is present (never drop).",
            target=target,
        )
    disc, err = _map_disclosure(
        slide,
        slide_number=slide_number,
        path=path,
        legacy_input=legacy_input,
        target=target,
    )
    if err is not None:
        return err
    if disc is not None:
        converted["disclosure"] = disc
    return None


def _common_fields(
    slide: Mapping[str, Any],
    *,
    section_id: Optional[str],
    title: Optional[str],
    include_takeaway: bool,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if section_id is not None:
        out["section_id"] = section_id
    if title is not None:
        out["title"] = title
    c = _content(slide)
    subtitle = _text(c.get("subtitle"))
    if subtitle:
        out["content"] = {"subtitle": subtitle}
    if include_takeaway:
        so = _text(c.get("so_what")) or _text(c.get("takeaway"))
        if so:
            out["takeaway"] = {"text": so}
    notes = _text(slide.get("speaker_notes"))
    if notes:
        out["speaker_notes"] = notes
    return out


# ---------------------------------------------------------------------------
# Converters — return (slide_dict | None, unresolved | None)
# ---------------------------------------------------------------------------


def _require_title(
    slide: Mapping[str, Any],
    *,
    slide_number: int,
    path: str,
    legacy_input: str,
    target: str,
) -> tuple[Optional[str], Optional[UnresolvedDecision]]:
    title = _text(slide.get("title"))
    if not title:
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/title",
            legacy_input,
            "Proof failed: authored title required (migrator never invents headings).",
            target=target,
        )
    return title, None


def _convert_narrative(
    slide: Mapping[str, Any],
    *,
    slide_number: int,
    section_id: str,
    path: str,
) -> tuple[Optional[dict[str, Any]], Optional[UnresolvedDecision]]:
    c = _content(slide)
    blocks: list[dict[str, Any]] = []
    body = _text(c.get("body_text")) or _text(c.get("headline"))
    if body:
        blocks.append(
            {
                "block_id": "lead",
                "type": "paragraphs",
                "paragraphs": [{"runs": [{"text": body}]}],
            }
        )
    bullets_raw = c.get("bullets") or c.get("supporting_points") or []
    items: list[dict[str, Any]] = []
    if isinstance(bullets_raw, list):
        for b in bullets_raw:
            t = _text(b) if not isinstance(b, dict) else _text(b.get("text") or b.get("label"))
            if t:
                items.append({"runs": [{"text": t}]})
    if items:
        blocks.append({"block_id": "bullets", "type": "bullet_list", "items": items})
    if not blocks:
        return None, UnresolvedDecision(
            slide_number,
            path,
            "ir_bullet_sheet",
            "Proof failed: text-only narrative needs paragraph or list boundaries.",
            target="narrative",
        )
    title, err = _require_title(
        slide,
        slide_number=slide_number,
        path=path,
        legacy_input="ir_bullet_sheet",
        target="narrative",
    )
    if err:
        return None, err
    out = {
        "slide_number": slide_number,
        "layout_type": "narrative",
        "payload": {"blocks": blocks},
        **_common_fields(
            slide,
            section_id=section_id,
            title=title,
            include_takeaway=True,
        ),
    }
    return out, None


def _convert_table_family(
    slide: Mapping[str, Any],
    *,
    slide_number: int,
    section_id: str,
    path: str,
    legacy_input: str,
    target: str,
    require_insight: bool = False,
) -> tuple[Optional[dict[str, Any]], Optional[UnresolvedDecision]]:
    matrix = _matrix_from_steps(_primary_steps(slide))
    if matrix is None:
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/visual_spec/primary_visual/steps_or_data",
            legacy_input,
            "Proof failed: need one complete dense rectangular matrix (header + body).",
            target=target,
        )
    c = _content(slide)
    insight = _text(c.get("so_what")) or _text(c.get("insight")) or _text(c.get("takeaway"))
    if require_insight and not insight:
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/content",
            legacy_input,
            "Proof failed: data_table_with_insight needs one unambiguous slide-level insight.",
            target=target,
        )
    title, err = _require_title(
        slide,
        slide_number=slide_number,
        path=path,
        legacy_input=legacy_input,
        target=target,
    )
    if err:
        return None, err
    payload = _table_payload_from_matrix(matrix, surface_fallback=f"slide-{slide_number}-table")
    out = {
        "slide_number": slide_number,
        "layout_type": target,
        "payload": payload,
        **_common_fields(
            slide,
            section_id=section_id,
            title=title,
            include_takeaway=target == "data_table",
        ),
    }
    if require_insight and insight and "takeaway" not in out:
        out["takeaway"] = {"text": insight}
    if target == "annex_table" and "takeaway" in out:
        del out["takeaway"]
    return out, None


def _convert_grouped_annex(
    slide: Mapping[str, Any],
    *,
    slide_number: int,
    section_id: str,
    path: str,
    legacy_input: str,
) -> tuple[Optional[dict[str, Any]], Optional[UnresolvedDecision]]:
    vs = slide.get("visual_spec")
    peers_raw: list[Any] = []
    if isinstance(vs, dict):
        if isinstance(vs.get("tables"), list):
            peers_raw = vs["tables"]
        elif isinstance(vs.get("primary_visual"), dict):
            sod = vs["primary_visual"].get("steps_or_data")
            if isinstance(sod, list) and sod and isinstance(sod[0], dict):
                peers_raw = sod
    if len(peers_raw) > 2:
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/visual_spec",
            legacy_input,
            "Proof failed: need one or two explicitly headed complete annex matrices.",
            target="grouped_annex_table",
        )
    peers_out: list[dict[str, Any]] = []
    if peers_raw:
        for i, peer in enumerate(peers_raw):
            if not isinstance(peer, dict):
                peers_out = []
                break
            heading = _text(peer.get("heading") or peer.get("title") or peer.get("label"))
            steps = peer.get("steps_or_data") or peer.get("rows") or peer.get("matrix")
            matrix = _matrix_from_steps(steps)
            if not heading or matrix is None:
                peers_out = []
                break
            payload = _table_payload_from_matrix(
                matrix, surface_fallback=f"slide-{slide_number}-peer-{i+1}"
            )
            entry = {"heading": heading, "table": payload["table"]}
            sh = _text(peer.get("short_heading"))
            if sh:
                entry["short_heading"] = sh
            peers_out.append(entry)
    if not peers_out:
        # Single matrix fallback is not enough — need explicit headed peers.
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/visual_spec",
            legacy_input,
            "Proof failed: need one or two explicitly headed complete annex matrices.",
            target="grouped_annex_table",
        )
    title, err = _require_title(
        slide,
        slide_number=slide_number,
        path=path,
        legacy_input=legacy_input,
        target="grouped_annex_table",
    )
    if err:
        return None, err
    out = {
        "slide_number": slide_number,
        "layout_type": "grouped_annex_table",
        "payload": {"tables": peers_out},
        **_common_fields(
            slide,
            section_id=section_id,
            title=title,
            include_takeaway=False,
        ),
    }
    out.pop("takeaway", None)
    return out, None


def _map_period_roles(
    header: list[str],
) -> Optional[list[tuple[str, str]]]:
    """Map header labels to the three D186 roles; None if any role is ambiguous."""
    roles: dict[str, str] = {}
    for label in header[1:]:
        key = _SLUG_RE.sub("_", label.strip().lower()).strip("_")
        # try full key then tokens
        role = _PERIOD_ROLE_ALIASES.get(key)
        if role is None:
            tokens = [t for t in key.replace("-", "_").split("_") if t]
            hits = {_PERIOD_ROLE_ALIASES[t] for t in tokens if t in _PERIOD_ROLE_ALIASES}
            if len(hits) == 1:
                role = next(iter(hits))
        if role is None or role in roles:
            return None
        roles[role] = label
    needed = ("current_period", "comparison_period", "variance")
    if set(roles) != set(needed):
        return None
    return [(rid, roles[rid]) for rid in needed]


def _convert_period_comparison(
    slide: Mapping[str, Any],
    *,
    slide_number: int,
    section_id: str,
    path: str,
    legacy_input: str,
) -> tuple[Optional[dict[str, Any]], Optional[UnresolvedDecision]]:
    matrix = _matrix_from_steps(_primary_steps(slide))
    if matrix is None:
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/visual_spec/primary_visual/steps_or_data",
            legacy_input,
            "Proof failed: period_comparison needs explicit current/comparison/variance roles.",
            target="period_comparison",
        )
    header, body = matrix
    if len(header) != 4:
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/visual_spec/primary_visual/steps_or_data",
            legacy_input,
            "Proof failed: period_comparison needs stub + current/comparison/variance columns.",
            target="period_comparison",
        )
    mapped = _map_period_roles(header)
    if mapped is None:
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/visual_spec/primary_visual/steps_or_data",
            legacy_input,
            "Proof failed: column labels must explicitly identify current/comparison/variance roles.",
            target="period_comparison",
        )
    label_to_idx = {lab: i for i, lab in enumerate(header)}
    columns = [{"column_id": rid, "label": lab} for rid, lab in mapped]
    used_rows: set[str] = set()
    rows = []
    for i, brow in enumerate(body):
        rid = _unique_slug(brow[0] or f"row-{i+1}", used_rows, fallback=f"row-{i+1}")
        cells = {}
        for role_id, lab in mapped:
            raw = brow[label_to_idx[lab]]
            cells[role_id] = (
                {"type": "missing"} if raw is None else {"type": "text", "text": raw}
            )
        rows.append({"row_id": rid, "label": brow[0], "cells": cells})
    title, err = _require_title(
        slide,
        slide_number=slide_number,
        path=path,
        legacy_input=legacy_input,
        target="period_comparison",
    )
    if err:
        return None, err
    out = {
        "slide_number": slide_number,
        "layout_type": "period_comparison",
        "payload": {
            "table": {
                "surface_id": _slug(f"slide-{slide_number}-period", fallback="period-1"),
                "stub_header": {"label": header[0]},
                "columns": columns,
                "rows": rows,
            }
        },
        **_common_fields(
            slide,
            section_id=section_id,
            title=title,
            include_takeaway=True,
        ),
    }
    return out, None


def _convert_comparison_cards(
    slide: Mapping[str, Any],
    *,
    slide_number: int,
    section_id: str,
    path: str,
    legacy_input: str,
) -> tuple[Optional[dict[str, Any]], Optional[UnresolvedDecision]]:
    matrix = _matrix_from_steps(_primary_steps(slide))
    if matrix is None:
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/visual_spec/primary_visual/steps_or_data",
            legacy_input,
            "Proof failed: comparison_cards needs one complete 2–4 peer by 2–4 shared-fact table.",
            target="comparison_cards",
        )
    header, body = matrix
    n_facts = len(header) - 1
    n_peers = len(body)
    if not (2 <= n_peers <= 4 and 2 <= n_facts <= 4):
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/visual_spec/primary_visual/steps_or_data",
            legacy_input,
            f"Proof failed: need 2–4 peers and 2–4 facts; got {n_peers}×{n_facts}.",
            target="comparison_cards",
        )
    payload = _table_payload_from_matrix(matrix, surface_fallback=f"slide-{slide_number}-cards")
    title, err = _require_title(
        slide,
        slide_number=slide_number,
        path=path,
        legacy_input=legacy_input,
        target="comparison_cards",
    )
    if err:
        return None, err
    out = {
        "slide_number": slide_number,
        "layout_type": "comparison_cards",
        "payload": payload,
        **_common_fields(
            slide,
            section_id=section_id,
            title=title,
            include_takeaway=True,
        ),
    }
    return out, None


def _convert_section_divider(
    slide: Mapping[str, Any],
    *,
    slide_number: int,
    section_id: str,
    path: str,
    legacy_input: str,
    sections: dict[str, str],
) -> tuple[Optional[dict[str, Any]], Optional[UnresolvedDecision]]:
    if section_id not in sections:
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/section",
            legacy_input,
            "Proof failed: section_divider needs a registered section.",
            target="section_divider",
        )
    out: dict[str, Any] = {
        "slide_number": slide_number,
        "layout_type": "section_divider",
        "payload": {"section_id": section_id},
    }
    notes = _text(slide.get("speaker_notes"))
    if notes:
        out["speaker_notes"] = notes
    return out, None


def _convert_line_chart(
    slide: Mapping[str, Any],
    *,
    slide_number: int,
    section_id: str,
    path: str,
    legacy_input: str,
) -> tuple[Optional[dict[str, Any]], Optional[UnresolvedDecision]]:
    """Only line_chart with explicit categories/series structure converts."""
    vs = slide.get("visual_spec")
    pv = vs.get("primary_visual") if isinstance(vs, dict) else None
    if not isinstance(pv, dict):
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/visual_spec/primary_visual",
            legacy_input,
            "Proof failed: line chart needs explicit primary_visual.",
            target="single_chart",
        )
    # Prefer structured chart_data if already present (rare in legacy).
    chart_data = pv.get("chart_data") if isinstance(pv.get("chart_data"), dict) else None
    if chart_data is None:
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/visual_spec/primary_visual/chart_data",
            legacy_input,
            "Proof failed: line chart needs explicit categories, series, values, axes, formats, identities.",
            target="single_chart",
        )
    # Pass through only if it already looks schema-shaped — no invention.
    required = ("categories", "series")
    if any(k not in chart_data for k in required):
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/visual_spec/primary_visual/chart_data",
            legacy_input,
            "Proof failed: chart_data missing categories/series.",
            target="single_chart",
        )
    title, err = _require_title(
        slide,
        slide_number=slide_number,
        path=path,
        legacy_input=legacy_input,
        target="single_chart",
    )
    if err:
        return None, err
    fmt = pv.get("value_axes") or {}
    # Require format_id on primary axis — no default invention.
    primary_axis = fmt.get("primary") if isinstance(fmt, dict) else None
    if not isinstance(primary_axis, dict) or not primary_axis.get("format_id"):
        return None, UnresolvedDecision(
            slide_number,
            f"{path}/visual_spec/primary_visual/value_axes",
            legacy_input,
            "Proof failed: explicit value axis format_id required.",
            target="single_chart",
        )
    surface = _text(pv.get("surface_id")) or f"slide-{slide_number}-line"
    visual = {
        "type": "chart",
        "surface_id": _slug(surface, fallback=f"chart-{slide_number}"),
        "chart_type": "line",
        "chart_data": chart_data,
        "value_axes": {"primary": primary_axis},
    }
    for opt in ("heading", "subtitle", "category_axis", "display", "typography"):
        if opt in pv:
            visual[opt] = pv[opt]
    out = {
        "slide_number": slide_number,
        "layout_type": "single_chart",
        "payload": {"chart": visual},
        **_common_fields(
            slide,
            section_id=section_id,
            title=title,
            include_takeaway=True,
        ),
    }
    return out, None


def _try_convert(
    slide: Mapping[str, Any],
    *,
    slide_number: int,
    legacy_input: str,
    entry: InventoryEntry,
    section_id: str,
    path: str,
    sections: dict[str, str],
) -> tuple[Optional[dict[str, Any]], Optional[UnresolvedDecision]]:
    if entry.classification == "human":
        return None, UnresolvedDecision(
            slide_number,
            path,
            legacy_input,
            entry.reason or "Human migration decision required.",
            candidates=entry.candidates,
        )
    if entry.classification == "removed_sentinel":
        return None, UnresolvedDecision(
            slide_number,
            path,
            legacy_input,
            entry.reason,
        )
    target = entry.target
    assert target is not None

    # Kernel-only mechanical converters. Other deterministic targets stay
    # unresolved until their compositions ship (failed proof / not yet convertible).
    if target == "narrative" and legacy_input == "ir_bullet_sheet":
        return _convert_narrative(
            slide, slide_number=slide_number, section_id=section_id, path=path
        )
    if target == "data_table":
        return _convert_table_family(
            slide,
            slide_number=slide_number,
            section_id=section_id,
            path=path,
            legacy_input=legacy_input,
            target="data_table",
            require_insight=legacy_input == "data_table_with_insight",
        )
    if target == "annex_table":
        return _convert_table_family(
            slide,
            slide_number=slide_number,
            section_id=section_id,
            path=path,
            legacy_input=legacy_input,
            target="annex_table",
        )
    if target == "grouped_annex_table":
        return _convert_grouped_annex(
            slide,
            slide_number=slide_number,
            section_id=section_id,
            path=path,
            legacy_input=legacy_input,
        )
    if target == "period_comparison":
        return _convert_period_comparison(
            slide,
            slide_number=slide_number,
            section_id=section_id,
            path=path,
            legacy_input=legacy_input,
        )
    if target == "comparison_cards":
        return _convert_comparison_cards(
            slide,
            slide_number=slide_number,
            section_id=section_id,
            path=path,
            legacy_input=legacy_input,
        )
    if target == "section_divider":
        return _convert_section_divider(
            slide,
            slide_number=slide_number,
            section_id=section_id,
            path=path,
            legacy_input=legacy_input,
            sections=sections,
        )
    if target == "single_chart" and legacy_input == "line_chart":
        return _convert_line_chart(
            slide,
            slide_number=slide_number,
            section_id=section_id,
            path=path,
            legacy_input=legacy_input,
        )

    family = f"/{entry.chart_family}" if entry.chart_family else ""
    return None, UnresolvedDecision(
        slide_number,
        path,
        legacy_input,
        f"Proof failed: required semantic proof for target {target}{family!s} "
        f"not satisfied by legacy payload ({entry.proof})",
        target=target,
        candidates=(f"{target}{family}" if family else target,),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def migrate_handoff(
    handoff_path: str | Path,
    *,
    out_dir: str | Path | None = None,
    check: bool = False,
) -> MigrationResult:
    """Migrate one unversioned legacy handoff into a separate schema-v1 candidate.

    Parameters
    ----------
    handoff_path:
        Source JSON path. Never modified.
    out_dir:
        Directory for candidate + report when not ``check``. Required to write.
    check:
        When True, write nothing; exit/ok reflect full resolution + validation.
    """
    src = Path(handoff_path)
    raw_text = src.read_text(encoding="utf-8")
    raw = json.loads(raw_text)
    if not isinstance(raw, dict):
        raise ValueError("handoff root must be an object")

    slides_in = raw.get("slides")
    if not isinstance(slides_in, list) or not slides_in:
        raise ValueError("handoff must contain a non-empty slides array")

    section_ids_used: set[str] = set()
    surface_ids_used: set[str] = set()
    sections: dict[str, str] = {}
    evidence_registry: dict[str, dict[str, Any]] = {}
    number_formats: dict[str, Any] = {}

    for pre_slide in slides_in:
        if not isinstance(pre_slide, dict):
            continue
        pre_entry = LEGACY_INVENTORY.get(_raw_layout(pre_slide))
        if pre_entry is not None and pre_entry.target != "section_divider":
            if _text(pre_slide.get("section")):
                _section_id_for(pre_slide, section_ids_used, sections)

    unresolved: list[UnresolvedDecision] = []
    dispositions: list[SlideDisposition] = []
    out_slides: list[dict[str, Any]] = []
    seen_inputs: set[str] = set()

    for i, slide in enumerate(slides_in):
        if not isinstance(slide, dict):
            unresolved.append(
                UnresolvedDecision(None, f"/slides/{i}", "other", "Slide entry is not an object.")
            )
            dispositions.append(
                SlideDisposition(
                    slide_number=i + 1,
                    legacy_input="other",
                    classification="removed_sentinel",
                    status="unresolved",
                    source_path=f"/slides/{i}",
                    proof_result="invalid",
                )
            )
            continue

        slide_number = slide.get("slide_number")
        if not isinstance(slide_number, int) or slide_number < 1:
            slide_number = i + 1
        path = f"/slides/{i}"
        legacy_input = _raw_layout(slide)
        seen_inputs.add(legacy_input)
        entry = LEGACY_INVENTORY.get(legacy_input)
        if entry is None:
            # Outside the 57 — still one disposition, never a guessed target.
            unresolved.append(
                UnresolvedDecision(
                    slide_number,
                    path,
                    legacy_input,
                    "Unknown legacy layout_type; not in the D313 57-input inventory.",
                )
            )
            dispositions.append(
                SlideDisposition(
                    slide_number=slide_number,
                    legacy_input=legacy_input,
                    classification="human",
                    status="unresolved",
                    proof_result="n/a",
                    source_path=path,
                )
            )
            continue

        section_id = (
            _section_id_for(
                slide,
                section_ids_used,
                sections,
                register=entry.target != "section_divider",
            )
            if entry.classification == "deterministic"
            else ""
        )

        converted, unres = _try_convert(
            slide,
            slide_number=slide_number,
            legacy_input=legacy_input,
            entry=entry,
            section_id=section_id,
            path=path,
            sections=sections,
        )

        if converted is not None and unres is None:
            disc_err = _attach_disclosure(
                slide,
                converted,
                slide_number=slide_number,
                path=path,
                legacy_input=legacy_input,
            )
            if disc_err is not None:
                unres = disc_err
                converted = None

        eids = _evidence_from_slide(slide, evidence_registry)
        if converted is not None and eids:
            converted["evidence_ids"] = eids
            # Never invent source_footer ownership (D119); only keep an authored list.
            authored_footer = slide.get("source_footer")
            if (
                isinstance(authored_footer, list)
                and authored_footer
                and converted.get("layout_type")
                not in _NO_DISCLOSURE_LAYOUTS
            ):
                kept = [x for x in authored_footer if isinstance(x, str) and x in eids]
                # de-dupe preserve order
                seen_f: list[str] = []
                for x in kept:
                    if x not in seen_f:
                        seen_f.append(x)
                if seen_f:
                    converted["source_footer"] = seen_f[:4]

        if unres is not None:
            unresolved.append(unres)
            dispositions.append(
                SlideDisposition(
                    slide_number=slide_number,
                    legacy_input=legacy_input,
                    classification=entry.classification,
                    status="unresolved",
                    target=entry.target or unres.target,
                    candidates=entry.candidates or unres.candidates,
                    proof_result="failed" if entry.classification == "deterministic" else "human",
                    source_path=path,
                )
            )
            continue

        assert converted is not None
        _register_surface_ids(converted, surface_ids_used)

        out_slides.append(converted)
        dispositions.append(
            SlideDisposition(
                slide_number=slide_number,
                legacy_input=legacy_input,
                classification=entry.classification,
                status="resolved",
                target=converted["layout_type"],
                proof_result="passed",
                source_path=path,
            )
        )

    src_formats = raw.get("number_formats")
    if isinstance(src_formats, dict):
        referenced = _referenced_format_ids(out_slides)
        for k, v in src_formats.items():
            if isinstance(k, str) and is_semantic_id(k) and k in referenced:
                number_formats[k] = v

    inventory_report = []
    for key in sorted(LEGACY_INVENTORY.keys(), key=lambda k: (k == "", k)):
        e = LEGACY_INVENTORY[key]
        used = key in seen_inputs
        slide_rows = [d for d in dispositions if d.legacy_input == key]
        if slide_rows:
            if all(d.status == "resolved" for d in slide_rows):
                decision_status = "resolved"
            else:
                decision_status = "unresolved"
            proof = (
                "passed"
                if decision_status == "resolved"
                else ("failed" if e.classification == "deterministic" else "n/a")
            )
        else:
            decision_status = "not_present"
            proof = "n/a"
        target_label = e.target
        if e.target and e.chart_family:
            target_label = f"{e.target}/{e.chart_family}"
        inventory_report.append(
            {
                "legacy_input": key,
                "classification": e.classification,
                "target": target_label,
                "candidates": list(e.candidates),
                "proof": e.proof or e.reason,
                "proof_result": proof,
                "present_in_source": used,
                "decision_status": decision_status,
                "source_paths": [d.source_path for d in slide_rows],
            }
        )

    candidate: Optional[dict[str, Any]] = None
    version_marked = False
    validation_errors: list[str] = []

    def _envelope(meta: dict[str, Any], slides: list[dict[str, Any]]) -> dict[str, Any]:
        # Ensure every referenced section_id is registered (no invented labels).
        sec = dict(sections)
        for s in slides:
            sid = s.get("section_id") or (s.get("payload") or {}).get("section_id")
            if isinstance(sid, str) and sid not in sec:
                sec[sid] = sid
        return {
            "meta": meta,
            "sections": [{"section_id": sid, "label": lab} for sid, lab in sec.items()],
            "number_formats": number_formats,
            "evidence_registry": evidence_registry,
            "slides": slides,
        }

    # Build candidate only when every slide resolved.
    all_resolved = bool(dispositions) and all(d.status == "resolved" for d in dispositions)
    if all_resolved and not unresolved:
        draft = _envelope({"handoff_schema_version": 1}, out_slides)
        # D121: generated schema is the machine-readable contract the migrator
        # consumes via the same typed models that produce it (validate_handoff).
        try:
            result = validate_handoff(draft, strict=True)
            candidate = json.loads(result.deck.model_dump_json(exclude_none=True))
            candidate["meta"] = {"handoff_schema_version": 1}
            version_marked = True
        except RendererValidationError as exc:
            validation_errors = [
                f"{ev.code} {ev.path}: {ev.expected.contract if ev.expected else ''}"
                for ev in exc.events
            ]
            unresolved.append(
                UnresolvedDecision(
                    None,
                    "/meta/handoff_schema_version",
                    "schema_v1",
                    "Candidate failed schema-v1 validation; v1 marker withheld. "
                    + "; ".join(validation_errors[:5]),
                )
            )
            candidate = _envelope({"migration_candidate": True}, out_slides)
            version_marked = False
    else:
        candidate = _envelope({"migration_candidate": True}, out_slides)
        candidate["unresolved_decisions"] = [asdict(u) for u in unresolved]
        version_marked = False

    ok = version_marked and not unresolved and not validation_errors
    wrote = False
    out_path = Path(out_dir) if out_dir is not None else None

    if not check and out_path is not None:
        out_path.mkdir(parents=True, exist_ok=True)
        for stale in ("handoff_v1.json", "handoff_candidate.json"):
            (out_path / stale).unlink(missing_ok=True)
        report = {
            "inventory": inventory_report,
            "slide_dispositions": [asdict(d) for d in dispositions],
            "unresolved_decisions": [asdict(u) for u in unresolved],
            "version_marked": version_marked,
            "validation_errors": validation_errors,
            "source": str(src),
        }
        (out_path / "migration_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        if version_marked and candidate is not None:
            (out_path / "handoff_v1.json").write_text(
                json.dumps(candidate, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        elif candidate is not None:
            (out_path / "handoff_candidate.json").write_text(
                json.dumps(candidate, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        wrote = True
    elif check:
        wrote = False

    exit_code = 0 if ok else 1
    return MigrationResult(
        ok=ok,
        exit_code=exit_code,
        wrote=wrote,
        version_marked=version_marked,
        candidate=candidate if version_marked else (candidate if not check else None),
        unresolved=unresolved,
        slide_dispositions=dispositions,
        inventory_report=inventory_report,
        validation_errors=validation_errors,
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m impact_slides.renderer_v3.migrate",
        description=(
            "Offline legacy→schema-v1 migration (D119/D313). "
            "Never modifies the source handoff."
        ),
    )
    p.add_argument("--handoff", required=True, help="unversioned legacy handoff JSON")
    p.add_argument(
        "--out",
        default=None,
        help="output directory for candidate + migration_report.json",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit 0 only when fully resolved and validated",
    )
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(sys.argv[1:] if argv is None else argv))
    if not args.check and not args.out:
        print("error: --out is required unless --check", file=sys.stderr)
        return 2
    try:
        result = migrate_handoff(args.handoff, out_dir=args.out, check=bool(args.check))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    summary = {
        "ok": result.ok,
        "version_marked": result.version_marked,
        "unresolved": len(result.unresolved),
        "slides": len(result.slide_dispositions),
        "wrote": result.wrote,
    }
    print(json.dumps(summary, indent=2))
    if result.unresolved:
        for u in result.unresolved[:20]:
            print(
                f"  unresolved slide={u.slide_number} input={u.legacy_input!r} "
                f"path={u.path}: {u.reason}",
                file=sys.stderr,
            )
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
