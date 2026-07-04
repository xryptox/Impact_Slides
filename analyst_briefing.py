"""
Analyst Briefing Generator (v4 #26)
===================================

Produces a condensed strategic handoff for the Impact Slide Analyst GPT (Step 2):

  - ``analyst_briefing.md``  — human + LLM friendly Markdown summary
  - ``analyst_briefing.json`` — structured version for agents/tooling

It consumes the data structures the v4 preprocessor already builds (the
evidence register, the coverage map, and the cross-file relationship evidence)
and *interprets* them — it never re-derives raw insights, so there is no
duplication of v3/v4 profiling logic.

Two stages:

1. ``NarrativeScorer`` — calculates the **Narrative Readiness Score** (0-100
   composite + per-stage sub-scores) and identifies **ranked Focus Areas** via
   multi-signal theme detection + multi-factor scoring.

2. ``AnalystBriefingGenerator`` — orchestrates the scorer, surfaces the top
   cross-file relationships, derives quality flags + slide-building
   recommendations, and renders both the Markdown and JSON artefacts.

Design rules (matching the rest of the codebase):

  - **Decoupled**: this module imports nothing from the preprocessor. It takes
    plain dicts/lists so it is fully unit-testable in isolation.
  - **Graceful degradation**: pydantic is optional (validation skipped if
    absent); rapidfuzz is optional (falls back to stdlib ``difflib``).
  - **Single source of truth**: the output shapes mirror the Pydantic models
    in ``schemas.py`` (``AnalystBriefing`` / ``NarrativeReadiness`` /
    ``FocusArea`` / ``StageScore``). ``--emit-schema`` therefore covers them.
  - **No magic numbers in call sites**: the readiness + focus weights live in
    module-level tables so YAML can override them (Phase 2).
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

# --- optional: pydantic for output-shape validation ----------------------- #
try:
    from schemas import (AnalystBriefing, NarrativeReadiness, FocusArea,
                         StageScore, NARRATIVE_STAGES)
    _HAS_PYDANTIC = True
except ImportError:  # pragma: no cover - graceful degradation
    AnalystBriefing = NarrativeReadiness = FocusArea = StageScore = None
    NARRATIVE_STAGES = {"Why", "What", "How", "Now"}
    _HAS_PYDANTIC = False

# --- optional: rapidfuzz for near-duplicate theme merging ------------------ #
try:
    from rapidfuzz import fuzz as _rf_fuzz
    _HAS_RAPIDFUZZ = True
except ImportError:  # pragma: no cover - graceful degradation
    import difflib
    _HAS_RAPIDFUZZ = False

    class _RfShim:  # mimics rapidfuzz.fuzz.ratio signature (returns 0-100)
        @staticmethod
        def ratio(a: str, b: str) -> float:
            return difflib.SequenceMatcher(None, a, b).ratio() * 100.0

    _rf_fuzz = _RfShim()


__version__ = "4.0.0"

# --------------------------------------------------------------------------- #
# Weight tables (single source of truth; overridable via YAML in Phase 2).
# These mirror §6.1 / §6.2 of the Analyst Briefing Implementation Plan.
# --------------------------------------------------------------------------- #
READINESS_WEIGHTS: Dict[str, float] = {
    "coverage_balance":         0.30,   # evenness across Why/What/How/Now
    "priority_quality":         0.25,   # avg priority + high-priority fraction
    "cross_file_connectivity":  0.20,   # strength + volume of cross-file links
    "recommendation_strength":  0.15,   # volume + quality of "Now" evidence
    "signal_ratio":             0.10,   # 1 - noise fraction (low-confidence)
}

FOCUS_WEIGHTS: Dict[str, float] = {
    "avg_priority":               0.30,
    "cross_file_strength":        0.25,
    "insight_quality_boost":      0.20,   # derived insight types (trend/agg/...)
    "source_diversity":           0.15,
    "business_relevance_signals": 0.10,
}

# Derived / analytical insight types — the analytical "gold" that should
# boost a theme's focus score (v3 #1, #11, #25).
DERIVED_INSIGHT_TYPES = {
    "trend_insight", "period_trend_insight", "aggregate_insight",
    "outlier_insight", "correlation_insight",
}

# Default business keyword set used by theme detection signal 4 (extendable
# via YAML ``business_keywords`` in Phase 2). Lower-cased.
DEFAULT_BUSINESS_KEYWORDS = {
    "growth", "revenue", "profit", "margin", "cost", "market", "customer",
    "product", "region", "segment", "performance", "target", "goal",
    "strategy", "risk", "opportunity", "investment", "sales", "churn",
    "retention", "conversion", "adoption", "expansion", "efficiency",
    "quality", "satisfaction", "loyalty", "recommendation", "next step",
    "roadmap", "priority", "initiative", "outcome", "impact", "driver",
    "trend", "forecast", "benchmark", "kpi", "roi",
}

# Cross-file relationship evidence is surfaced "as-is" in the briefing; cap
# how many we list so the briefing stays compact.
TOP_CROSS_FILE_CAP = 6


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _norm_key(s: str) -> str:
    """Normalise a theme/entity name for near-duplicate comparison."""
    s = (s or "").strip().lower()
    # collapse whitespace and strip leading "the "
    s = re.sub(r"\s+", " ", s)
    if s.startswith("the "):
        s = s[4:]
    return s


def _similarity(a: str, b: str) -> float:
    """0-100 string similarity (rapidfuzz or difflib fallback)."""
    return float(_rf_fuzz.ratio(_norm_key(a), _norm_key(b)))


def _mean(values: List[float], default: float = 0.0) -> float:
    return sum(values) / len(values) if values else default


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


# --------------------------------------------------------------------------- #
# NarrativeScorer
# --------------------------------------------------------------------------- #
class NarrativeScorer:
    """Calculates the Narrative Readiness Score and Focus Areas.

    Pure: no I/O, no imports of the preprocessor. Constructed from the
    already-built evidence register, cross-file relationship list, and the
    coverage map. Designed so every sub-metric is independently testable.
    """

    def __init__(
        self,
        evidence: List[Dict[str, Any]],
        cross_file_relationships: Optional[List[Dict[str, Any]]] = None,
        coverage_map: Optional[Dict[str, Any]] = None,
        boost_keywords: Optional[List[str]] = None,
        business_keywords: Optional[List[str]] = None,
        readiness_weights: Optional[Dict[str, float]] = None,
        focus_weights: Optional[Dict[str, float]] = None,
    ):
        self.evidence = evidence or []
        self.cross_file = cross_file_relationships or []
        self.coverage_map = coverage_map or {}
        # Keyword sets are lower-cased on the way in.
        self.boost_keywords = {k.lower().strip() for k in (boost_keywords or []) if k}
        self.business_keywords = set(DEFAULT_BUSINESS_KEYWORDS)
        self.business_keywords |= {k.lower().strip() for k in (business_keywords or []) if k}
        # Allow caller-supplied weight overrides (Phase 2 YAML) but validate
        # they are complete so a partial override never silently re-weights.
        self.readiness_weights = self._check_weights(
            readiness_weights, READINESS_WEIGHTS, "readiness_weights")
        self.focus_weights = self._check_weights(
            focus_weights, FOCUS_WEIGHTS, "focus_weights")

    @staticmethod
    def _check_weights(supplied, defaults, name):
        if not supplied:
            return dict(defaults)
        if set(supplied.keys()) != set(defaults.keys()):
            raise ValueError(
                f"{name} override must contain exactly the keys "
                f"{sorted(defaults.keys())}; got {sorted(supplied.keys())}"
            )
        total = sum(supplied.values())
        if not (0.999 <= total <= 1.001):
            raise ValueError(f"{name} override weights must sum to 1.0; got {total}")
        return dict(supplied)

    # ------------------------------------------------------------------ #
    # Stage helpers
    # ------------------------------------------------------------------ #
    def _stage_counts(self) -> Dict[str, int]:
        cm = self.coverage_map.get("by_narrative_stage") if self.coverage_map else None
        if cm:
            return {s: int(cm.get(s, 0)) for s in ("Why", "What", "How", "Now")}
        # Fallback: derive from evidence if coverage_map absent.
        counts = Counter()
        for e in self.evidence:
            for s in e.get("suggested_narrative_use", []):
                counts[s] += 1
        return {s: counts.get(s, 0) for s in ("Why", "What", "How", "Now")}

    def _evidence_for_stage(self, stage: str) -> List[Dict[str, Any]]:
        return [e for e in self.evidence
                if stage in (e.get("suggested_narrative_use") or [])]

    # ------------------------------------------------------------------ #
    # Readiness sub-metrics (each returns 0-100)
    # ------------------------------------------------------------------ #
    def _coverage_balance(self) -> float:
        """How evenly evidence is distributed across Why/What/How/Now.

        Combines *presence* (all four stages populated?) with *balance*
        (coefficient-of-variation low?). A single dominant stage or any empty
        stage drags the score down — exactly the gap signal the analyst needs.
        """
        counts = self._stage_counts()
        vals = list(counts.values())
        total = sum(vals)
        if total == 0:
            return 0.0
        present = sum(1 for v in vals if v > 0)
        present_ratio = present / 4.0
        ideal = total / 4.0
        variance = sum((v - ideal) ** 2 for v in vals) / 4.0
        cv = (math.sqrt(variance) / ideal) if ideal > 0 else 0.0
        balance = max(0.0, 1.0 - min(1.0, cv))
        return round(_clip(present_ratio * balance) * 100, 1)

    def _priority_quality(self) -> float:
        """Average priority + fraction of high-priority (>=0.8) evidence."""
        if not self.evidence:
            return 0.0
        priorities = [e.get("priority_score", 0.0) for e in self.evidence]
        avg = _mean(priorities)
        high_frac = sum(1 for p in priorities if p >= 0.8) / len(priorities)
        return round(_clip(0.6 * avg + 0.4 * high_frac) * 100, 1)

    def _cross_file_connectivity(self) -> float:
        """Strength + volume of cross-file links (saturates at 5 links)."""
        n = len(self.cross_file)
        if n == 0:
            return 0.0
        avg_p = _mean([e.get("priority_score", 0.0) for e in self.cross_file])
        # Volume term (saturates at 5) weighted by the links' own quality.
        return round(_clip(min(1.0, n / 5.0) * (0.5 + 0.5 * avg_p)) * 100, 1)

    def _recommendation_strength(self) -> float:
        """Volume + quality of "Now" stage evidence (the recommendation stage)."""
        now_evs = self._evidence_for_stage("Now")
        if not now_evs:
            return 0.0
        now_avg = _mean([e.get("priority_score", 0.0) for e in now_evs])
        volume = min(1.0, len(now_evs) / 5.0)
        return round(_clip(volume * (0.5 + 0.5 * now_avg)) * 100, 1)

    def _signal_ratio(self) -> float:
        """1 - noise fraction, where noise = low-confidence evidence."""
        if not self.evidence:
            return 0.0
        low = sum(1 for e in self.evidence
                  if (e.get("confidence") or "low") == "low")
        return round(_clip(1.0 - low / len(self.evidence)) * 100, 1)

    # ------------------------------------------------------------------ #
    # Stage sub-scores
    # ------------------------------------------------------------------ #
    def _stage_score(self, stage: str) -> Dict[str, Any]:
        evs = self._evidence_for_stage(stage)
        count = len(evs)
        if count == 0:
            return {
                "stage": stage, "score": 0, "evidence_count": 0,
                "avg_priority": 0.0, "note": "no evidence in this stage",
            }
        avg_p = _mean([e.get("priority_score", 0.0) for e in evs])
        # 40 (presence) + up to 30 (volume, saturating at 10) + up to 30 (priority)
        score = round(40 + 30 * min(1.0, count / 10.0) + 30 * avg_p)
        score = max(0, min(100, score))
        return {
            "stage": stage, "score": score, "evidence_count": count,
            "avg_priority": round(avg_p, 3), "note": None,
        }

    # ------------------------------------------------------------------ #
    # Public: readiness
    # ------------------------------------------------------------------ #
    def calculate_narrative_readiness(self) -> Dict[str, Any]:
        components = {
            "coverage_balance": self._coverage_balance(),
            "priority_quality": self._priority_quality(),
            "cross_file_connectivity": self._cross_file_connectivity(),
            "recommendation_strength": self._recommendation_strength(),
            "signal_ratio": self._signal_ratio(),
        }
        w = self.readiness_weights
        overall = round(
            w["coverage_balance"] * components["coverage_balance"]
            + w["priority_quality"] * components["priority_quality"]
            + w["cross_file_connectivity"] * components["cross_file_connectivity"]
            + w["recommendation_strength"] * components["recommendation_strength"]
            + w["signal_ratio"] * components["signal_ratio"]
        )
        overall = max(0, min(100, overall))
        stage_scores = {s: self._stage_score(s) for s in ("Why", "What", "How", "Now")}
        return {
            "overall_score": overall,
            "components": components,
            "stage_scores": stage_scores,
            "explanation": self._readiness_explanation(overall, components, stage_scores),
        }

    def _readiness_explanation(self, overall, components, stage_scores) -> str:
        parts = []
        if overall >= 75:
            parts.append("Strong narrative readiness")
        elif overall >= 50:
            parts.append("Moderate narrative readiness")
        else:
            parts.append("Low narrative readiness")
        # Weakest component
        weakest = min(components.items(), key=lambda kv: kv[1])
        parts.append(f"weakest component is '{weakest[0]}' ({weakest[1]:.0f}/100)")
        # Empty stages
        empty = [s for s, sc in stage_scores.items() if sc["evidence_count"] == 0]
        if empty:
            parts.append(f"stages with no evidence: {', '.join(empty)}")
        return "; ".join(parts) + "."

    # ------------------------------------------------------------------ #
    # Theme detection (multi-signal) + merging
    # ------------------------------------------------------------------ #
    def _theme_keys_for(self, ev: Dict[str, Any]) -> List[str]:
        """Extract candidate theme keys from one evidence entry."""
        keys: List[str] = []

        # Signal 1: column name (Excel) — the most precise theme signal.
        col = ev.get("column_name") or ev.get("column")
        if col and str(col).strip() and str(col).strip().lower() not in ("nan", "none"):
            keys.append(str(col).strip())

        # Signal 2: "X by Y" metric-by-dimension patterns in the text.
        text = ev.get("text", "") or ""
        for m in re.finditer(r"\b([A-Za-z][\w\s&/-]{1,40}?)\s+by\s+([A-Za-z][\w\s&/-]{1,40})", text, re.I):
            keys.append(f"{m.group(1).strip()} by {m.group(2).strip()}")

        # Signal 3: cross-file entity — when the entry IS a cross-file metric,
        # the entity is the theme (e.g. "EMEA mentioned in 2 files").
        if ev.get("insight_type") == "cross_file_metric":
            m = re.search(r"'([^']+)'", text)
            if m:
                keys.append(m.group(1))

        return [k for k in keys if k]

    def _merge_themes(self, themes: Dict[str, List[Dict[str, Any]]]
                      ) -> Dict[str, List[Dict[str, Any]]]:
        """Greedy near-duplicate theme merging (rapidfuzz/difflib, >=82%)."""
        if len(themes) < 2:
            return themes
        keys = list(themes.keys())
        merged: Dict[str, List[Dict[str, Any]]] = {}
        used: set = set()
        # Process longer/canonical keys first so the survivor is the most
        # descriptive name (e.g. "Total Revenue" survives over "revenue").
        for k in sorted(keys, key=lambda x: (-len(x), x)):
            if k in used:
                continue
            canonical = k
            bucket = list(themes[k])
            used.add(k)
            for other in keys:
                if other in used:
                    continue
                if _similarity(canonical, other) >= 82.0:
                    bucket.extend(themes[other])
                    used.add(other)
            merged[canonical] = bucket
        return merged

    def _evidence_files(self) -> set:
        return {e.get("source_file") for e in self.evidence if e.get("source_file")}

    def _dominant_stages(self, evs: List[Dict[str, Any]]) -> List[str]:
        c = Counter()
        for e in evs:
            for s in (e.get("suggested_narrative_use") or []):
                c[s] += 1
        if not c:
            return []
        top = c.most_common()
        best = top[0][1]
        return [s for s, n in top if n == best]

    # ------------------------------------------------------------------ #
    # Public: focus areas
    # ------------------------------------------------------------------ #
    def identify_focus_areas(self, top_n: int = 5) -> List[Dict[str, Any]]:
        if not self.evidence:
            return []
        # Group evidence by candidate theme key.
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for ev in self.evidence:
            keys = self._theme_keys_for(ev)
            if not keys:
                continue  # not themeable — counted in readiness, not focus areas
            for k in keys:
                grouped[k].append(ev)
        # Merge near-duplicate themes.
        merged = self._merge_themes(grouped)
        all_files = self._evidence_files()
        cross_entities = {
            _norm_key(self._cross_entity_name(e)) for e in self.cross_file
            if self._cross_entity_name(e)
        }
        w = self.focus_weights
        scored = []
        for area, evs in merged.items():
            n = len(evs)
            if n == 0:
                continue
            avg_priority = _mean([e.get("priority_score", 0.0) for e in evs])
            # cross_file_strength: fraction of cross-file evidence in the theme,
            # plus a bonus if the theme name itself is a cross-file entity.
            cf_frac = sum(1 for e in evs if e.get("insight_type") == "cross_file_metric") / n
            entity_bonus = 1.0 if _norm_key(area) in cross_entities else 0.0
            cross_file_strength = _clip(0.5 * cf_frac + 0.5 * entity_bonus)
            # insight_quality_boost: fraction of derived insight types.
            quality_frac = sum(1 for e in evs
                               if e.get("insight_type") in DERIVED_INSIGHT_TYPES) / n
            # source_diversity: distinct source files in theme / total files.
            theme_files = {e.get("source_file") for e in evs if e.get("source_file")}
            source_diversity = _clip(len(theme_files) / max(1, len(all_files)))
            # business_relevance_signals: fraction of evidence whose text
            # mentions a business keyword.
            biz_frac = 0
            for e in evs:
                t = (e.get("text", "") or "").lower()
                if any(kw in t for kw in self.business_keywords):
                    biz_frac += 1
            biz_frac = biz_frac / n
            score = (
                w["avg_priority"] * avg_priority
                + w["cross_file_strength"] * cross_file_strength
                + w["insight_quality_boost"] * quality_frac
                + w["source_diversity"] * source_diversity
                + w["business_relevance_signals"] * biz_frac
            ) * 100.0
            scored.append({
                "area": area,
                "score": round(min(100.0, max(0.0, score)), 1),
                "reason": self._focus_reason(avg_priority, cf_frac, quality_frac,
                                             source_diversity, biz_frac, len(theme_files)),
                "evidence_count": n,
                "dominant_stages": self._dominant_stages(evs),
                "top_evidence_ids": [e.get("evidence_id", "?") for e in
                                     sorted(evs, key=lambda x: x.get("priority_score", 0),
                                            reverse=True)[:3]],
            })
        scored.sort(key=lambda a: a["score"], reverse=True)
        # Stamp ranks.
        for i, a in enumerate(scored[:top_n], 1):
            a["rank"] = i
        return scored[:top_n]

    @staticmethod
    def _cross_entity_name(e: Dict[str, Any]) -> str:
        m = re.search(r"'([^']+)'", e.get("text", "") or "")
        return m.group(1) if m else ""

    @staticmethod
    def _focus_reason(avg_p, cf_frac, quality_frac, src_div, biz_frac, n_files) -> str:
        bits = []
        bits.append(f"avg priority {avg_p:.2f}")
        if cf_frac > 0:
            bits.append(f"{int(cf_frac * 100)}% cross-file")
        if quality_frac > 0:
            bits.append(f"{int(quality_frac * 100)}% derived/analytical")
        if n_files > 1:
            bits.append(f"spans {n_files} source files")
        if biz_frac > 0.5:
            bits.append("strong business-keyword signal")
        return "; ".join(bits) + "."


# --------------------------------------------------------------------------- #
# AnalystBriefingGenerator
# --------------------------------------------------------------------------- #
class AnalystBriefingGenerator:
    """Main orchestrator: consumes existing v4 data structures and renders the
    ``analyst_briefing.md`` + ``analyst_briefing.json`` artefacts."""

    def __init__(
        self,
        evidence: List[Dict[str, Any]],
        coverage_map: Optional[Dict[str, Any]] = None,
        cross_file: Optional[List[Dict[str, Any]]] = None,
        run_metadata: Optional[Dict[str, Any]] = None,
        boost_keywords: Optional[List[str]] = None,
        business_keywords: Optional[List[str]] = None,
        readiness_weights: Optional[Dict[str, float]] = None,
        focus_weights: Optional[Dict[str, float]] = None,
        focus_areas_count: int = 5,
    ):
        self.evidence = evidence or []
        self.coverage_map = coverage_map or {}
        self.cross_file = cross_file or []
        self.run_metadata = run_metadata or {}
        self.focus_areas_count = max(1, int(focus_areas_count or 5))
        self.scorer = NarrativeScorer(
            evidence=self.evidence,
            cross_file_relationships=self.cross_file,
            coverage_map=self.coverage_map,
            boost_keywords=boost_keywords,
            business_keywords=business_keywords,
            readiness_weights=readiness_weights,
            focus_weights=focus_weights,
        )

    # ------------------------------------------------------------------ #
    def generate(self) -> Dict[str, Any]:
        readiness = self.scorer.calculate_narrative_readiness()
        focus_areas = self.scorer.identify_focus_areas(self.focus_areas_count)
        avg_priority = round(_mean([e.get("priority_score", 0.0)
                                    for e in self.evidence]), 3)
        briefing = {
            "run_id": self.run_metadata.get("run_id", "unknown"),
            "source_folder": str(self.run_metadata.get("source_folder", "")),
            "total_evidence": len(self.evidence),
            "average_priority": avg_priority,
            "narrative_readiness": readiness,
            "top_cross_file_relationships": self._top_cross_file_relationships(),
            "suggested_focus_areas": focus_areas,
            "quality_flags": self._extract_quality_flags(readiness),
            "recommendations": self._generate_recommendations(readiness, focus_areas),
        }
        # Optional shape validation (graceful: never fatal).
        if _HAS_PYDANTIC:
            try:
                AnalystBriefing(**briefing)
            except Exception:
                pass  # validation is advisory — the dict is the contract
        return briefing

    # ------------------------------------------------------------------ #
    def _top_cross_file_relationships(self) -> List[Dict[str, Any]]:
        """Surface the top cross-file relationships compactly for the briefing."""
        if not self.cross_file:
            return []
        out = []
        for e in self.cross_file[:TOP_CROSS_FILE_CAP]:
            out.append({
                "evidence_id": e.get("evidence_id"),
                "text": e.get("text", ""),
                "priority_score": e.get("priority_score"),
                "related_files": e.get("related_files", []),
            })
        return out

    # ------------------------------------------------------------------ #
    def _extract_quality_flags(self, readiness: Dict[str, Any]) -> List[str]:
        flags: List[str] = []
        total = len(self.evidence)
        if total == 0:
            flags.append("no_evidence")
            return flags
        stage_scores = readiness.get("stage_scores", {})
        for stage, sc in stage_scores.items():
            if sc.get("evidence_count", 0) == 0:
                flags.append(f"missing_{stage.lower()}_stage")
        if readiness.get("overall_score", 0) < 40:
            flags.append("low_coverage_overall")
        if readiness.get("components", {}).get("signal_ratio", 100) < 70:
            flags.append("high_noise_ratio")
        if not self.cross_file:
            flags.append("no_cross_file_links")
        if len({e.get("source_file") for e in self.evidence if e.get("source_file")}) <= 1:
            flags.append("single_source")
        return flags

    # ------------------------------------------------------------------ #
    def _generate_recommendations(self, readiness: Dict[str, Any],
                                  focus_areas: List[Dict[str, Any]]) -> List[str]:
        recs: List[str] = []
        total = len(self.evidence)
        if total == 0:
            return ["No source evidence found — add business source files (Excel, PPTX, PDF, DOCX) and re-run."]
        stage_scores = readiness.get("stage_scores", {})
        empty = [s for s, sc in stage_scores.items() if sc.get("evidence_count", 0) == 0]
        # Stage-specific slide-building advice.
        if "Now" in empty:
            recs.append("Add a 'Now' slide with recommendations / next steps — current evidence has no 'Now' stage content.")
        if "Why" in empty:
            recs.append("Add context for the 'Why' — current evidence lacks the 'Why' stage (mission/problem framing).")
        if "How" in empty:
            recs.append("Add 'How' detail (method/process) — current evidence lacks the 'How' stage.")
        if "What" in empty:
            recs.append("Add 'What' facts/metrics — current evidence lacks the 'What' stage.")
        # Lead with the strongest focus area.
        if focus_areas:
            top = focus_areas[0]
            recs.append(
                f"Lead with '{top['area']}' — it has the strongest multi-signal "
                f"evidence (score {top['score']:.0f}/100, {top['evidence_count']} items)."
            )
        # Cross-file leverage.
        if self.cross_file:
            recs.append(f"Leverage the {len(self.cross_file)} cross-file link(s) to connect data to narrative.")
        else:
            recs.append("No cross-file links found — if multiple source files are present, align entity names so relationships surface.")
        # Readiness-level guidance.
        overall = readiness.get("overall_score", 0)
        if overall < 50:
            missing = [s for s in ("Why", "What", "How", "Now") if s in empty] or ["balanced stage coverage"]
            recs.append(f"Narrative readiness is low ({overall}/100). Add source material covering {', '.join(missing)}.")
        elif overall < 75:
            recs.append(f"Narrative readiness is moderate ({overall}/100). Strengthen the weakest stage before finalizing slides.")
        else:
            recs.append(f"Narrative readiness is strong ({overall}/100). Focus on narrative flow and emphasis.")
        return recs

    # ------------------------------------------------------------------ #
    def render_markdown(self, briefing: Dict[str, Any]) -> str:
        return _render_briefing_markdown(briefing)

    def to_json(self, briefing: Dict[str, Any]) -> Dict[str, Any]:
        return briefing


# --------------------------------------------------------------------------- #
# Markdown renderer (kept module-level so it's independently testable)
# --------------------------------------------------------------------------- #
def _render_briefing_markdown(b: Dict[str, Any]) -> str:
    L: List[str] = []
    L.append("# Analyst Briefing\n")
    L.append(f"**Run:** `{b.get('run_id', 'unknown')}`  ")
    L.append(f"**Source folder:** `{b.get('source_folder', '')}`  ")
    L.append(f"**Evidence entries:** {b.get('total_evidence', 0)}  ")
    L.append(f"**Average priority:** {b.get('average_priority', 0):.3f}\n")

    readiness = b.get("narrative_readiness", {})
    overall = readiness.get("overall_score", 0)
    L.append(f"## Narrative Readiness Score: {overall}/100\n")

    stage_scores = readiness.get("stage_scores", {})
    if stage_scores:
        L.append("| Stage | Score | Evidence | Avg Priority |")
        L.append("|-------|------:|---------:|-------------:|")
        for s in ("Why", "What", "How", "Now"):
            sc = stage_scores.get(s, {})
            L.append(f"| {s} | {sc.get('score', 0)} | {sc.get('evidence_count', 0)} | {sc.get('avg_priority', 0):.3f} |")
        L.append("")

    components = readiness.get("components", {})
    w = READINESS_WEIGHTS
    if components:
        L.append("### Score Components\n")
        labels = {
            "coverage_balance": "Coverage Balance",
            "priority_quality": "Priority Quality",
            "cross_file_connectivity": "Cross-File Connectivity",
            "recommendation_strength": "Recommendation Strength",
            "signal_ratio": "Signal Ratio",
        }
        for k in ("coverage_balance", "priority_quality",
                  "cross_file_connectivity", "recommendation_strength",
                  "signal_ratio"):
            L.append(f"- **{labels[k]}:** {components.get(k, 0):.0f}/100 "
                     f"(weight {int(w[k] * 100)}%)")
        L.append("")
    expl = readiness.get("explanation", "")
    if expl:
        L.append(f"> {expl}\n")

    focus = b.get("suggested_focus_areas", [])
    if focus:
        L.append("## Suggested Focus Areas\n")
        for fa in focus:
            stages = ", ".join(fa.get("dominant_stages", [])) or "—"
            L.append(f"{fa.get('rank', 0)}. **{fa.get('area', '?')}** "
                      f"(score {fa.get('score', 0):.0f}/100)")
            L.append(f"   - Stages: {stages} | Evidence: {fa.get('evidence_count', 0)}")
            L.append(f"   - {fa.get('reason', '')}")
            ids = fa.get("top_evidence_ids", [])
            if ids:
                L.append(f"   - Top evidence: {', '.join(ids)}")
        L.append("")

    cross = b.get("top_cross_file_relationships", [])
    if cross:
        L.append("## Top Cross-File Relationships\n")
        for c in cross:
            L.append(f"- **{c.get('evidence_id', '?')}** "
                     f"(priority {c.get('priority_score', 0):.2f}): "
                     f"{c.get('text', '')}")
        L.append("")
    else:
        L.append("## Top Cross-File Relationships\n")
        L.append("_No cross-file relationships detected._\n")

    flags = b.get("quality_flags", [])
    if flags:
        L.append("## Quality Flags\n")
        for f in flags:
            L.append(f"- `{f}`")
        L.append("")

    recs = b.get("recommendations", [])
    if recs:
        L.append("## Recommendations\n")
        for r in recs:
            L.append(f"- {r}")
        L.append("")

    return "\n".join(L)


__all__ = [
    "NarrativeScorer",
    "AnalystBriefingGenerator",
    "READINESS_WEIGHTS",
    "FOCUS_WEIGHTS",
    "DERIVED_INSIGHT_TYPES",
    "DEFAULT_BUSINESS_KEYWORDS",
    "render_briefing_markdown",
]


def render_briefing_markdown(briefing: Dict[str, Any]) -> str:
    """Module-level convenience wrapper around the renderer."""
    return _render_briefing_markdown(briefing)
