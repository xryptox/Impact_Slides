"""Allowlisted non-strict repairs (D123 / D311 kernel subset)."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable  # Callable used by typography surface resolvers

from .diagnostics import DiagnosticEvent, event

RepairFn = Callable[[Any, list[DiagnosticEvent]], Any]


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
        elif layout == "data_table":
            allowed = common | {
                "section_id",
                "title",
                "content",
                "takeaway",
                "disclosure",
                "source_footer",
            }
            payload_allowed = {"table"}
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
            elif layout in ("narrative", "data_table"):
                allowed = common | {
                    "section_id",
                    "title",
                    "content",
                    "takeaway",
                    "disclosure",
                    "source_footer",
                }
                protected = frozenset()
            else:
                # Unknown/unimplemented layout: only strip truly global noise keys
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
            if isinstance(payload, dict) and layout == "data_table":
                _drop_unknown_object(
                    payload,
                    allowed={"table"},
                    path=f"/slides/{i}/payload",
                    events=events,
                    role="data_table_payload",
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


def discard_inapplicable_typography(raw: Any, events: list[DiagnosticEvent]) -> Any:
    if not isinstance(raw, dict) or not isinstance(raw.get("slides"), list):
        return raw
    out = deepcopy(raw)
    for i, slide in enumerate(out["slides"]):
        if not isinstance(slide, dict):
            continue
        layout = slide.get("layout_type")
        if layout not in ("narrative", "data_table"):
            continue

        def _content(s: dict) -> dict | None:
            c = s.get("content")
            return c if isinstance(c, dict) else None

        def _takeaway(s: dict) -> dict | None:
            t = s.get("takeaway")
            return t if isinstance(t, dict) else None

        def _payload(s: dict) -> dict | None:
            p = s.get("payload")
            return p if isinstance(p, dict) else None

        def _table(s: dict) -> dict | None:
            p = s.get("payload")
            if not isinstance(p, dict):
                return None
            t = p.get("table")
            return t if isinstance(t, dict) else None

        surfaces_spec: list[tuple[str, str, str, int, int, Callable[[dict], dict | None]]] = [
            ("content", "subtitle_font_size", "body_font_size|table_font_size", 22, 26, _content),
            ("takeaway", "body_font_size", "subtitle_font_size|table_font_size", 22, 28, _takeaway),
        ]
        if layout == "narrative":
            surfaces_spec.append(
                ("payload", "body_font_size", "subtitle_font_size|table_font_size", 22, 28, _payload)
            )
        else:
            surfaces_spec.append(
                ("table", "table_font_size", "body_font_size|subtitle_font_size", 20, 24, _table)
            )
        for owner, size_field, forbidden_csv, floor, ceiling, resolve in surfaces_spec:
            surface = resolve(slide)
            if surface is None:
                continue
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
                    f"/slides/{i}/payload/table/typography"
                    if owner == "table"
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
        if not isinstance(slide, dict) or slide.get("layout_type") not in (
            "narrative",
            "data_table",
        ):
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


# Closed registry: name → transform (D123).
REPAIR_REGISTRY: dict[str, RepairFn] = {
    "assume_schema_v1": assume_schema_v1,
    "drop_unknown_fields": drop_unknown_fields,
    "discard_inapplicable_typography": discard_inapplicable_typography,
    "repair_disclosure_sections": repair_disclosure_sections,
    "repair_source_footer_names": repair_source_footer_names,
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
