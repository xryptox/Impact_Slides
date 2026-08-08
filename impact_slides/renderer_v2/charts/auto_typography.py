"""Deterministic density-aware auto chart typography (#150).

Shared resolver for Chart.js + SVG. Opt-in via chart_config.typography.mode=auto.
Does not expose heuristic weights/floors/ceilings as public config.
"""
from __future__ import annotations

import html
import json
import math
import re
import sys
from dataclasses import dataclass, field
import contextvars
from typing import Any, Callable, Mapping, Sequence

# Auto candidate ranges (inclusive, whole px). Not public config.
AUTO_X_LO, AUTO_X_HI = 12, 24
AUTO_Y_LO, AUTO_Y_HI = 12, 28
AUTO_DL_LO, AUTO_DL_HI = 11, 32

# Supported chart types for auto v1.
AUTO_CHART_TYPES = frozenset(
    {
        "line_chart",
        "grouped_bar_chart",
        "stacked_bar_chart",
        "horizontal_bar_chart",
        "combo_chart",
        "waterfall_chart",
    }
)

# Plot furniture reservations (px) subtracted before fitting.
_LEGEND_H = 28.0
_X_AXIS_GAP = 6.0
_Y_AXIS_GAP = 8.0
_DL_GAP = 4.0
_ROT_PAD = 4.0

# Conservative host when recipe cannot provide reliable dimensions.
CONSERVATIVE_PLOT_W = 420.0
CONSERVATIVE_PLOT_H = 280.0

# Wrap: at most two lines, whitespace/punctuation boundaries only.
_WRAP_SPLIT_RE = re.compile(r"(\s+|(?<=[/\-–,;:·])|(?=[/\-–,;:·]))")

# Context for diagnostics collected during a render.
_AUTO_DIAG: contextvars.ContextVar[list[dict[str, Any]] | None] = contextvars.ContextVar(
    "rv2_auto_typography_diagnostics", default=None
)


def begin_auto_diagnostics() -> contextvars.Token:
    return _AUTO_DIAG.set([])


def take_auto_diagnostics(token: contextvars.Token) -> list[dict[str, Any]]:
    out = list(_AUTO_DIAG.get() or [])
    _AUTO_DIAG.reset(token)
    return out


def record_auto_diagnostic(entry: Mapping[str, Any]) -> None:
    bucket = _AUTO_DIAG.get()
    if bucket is not None:
        bucket.append(dict(entry))


def _warn(msg: str) -> None:
    """Stderr only for information loss / reduced confidence (#150)."""
    print(f"[auto-typography] {msg}", file=sys.stderr)
    try:
        from .typography import _warn as typo_warn

        typo_warn(msg)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Font metrics (normalized advances, calibrated for boardroom fonts)
# ---------------------------------------------------------------------------

# Advances are fractions of em from Chromium canvas of the vendored WOFF2
# faces. Class values are fallbacks for unlisted glyphs (not class maxima —
# maxima over-estimate ordinary labels). Additive pad in measure_text_width
# covers FreeType vs DirectWrite DOM-box drift on CI hosts.
_FONT_METRICS: dict[str, dict[str, float]] = {
    "source_sans_3": {
        "digit": 0.513,
        "upper": 0.58,
        "lower": 0.50,
        "space": 0.20,
        "punct": 0.40,
        "other": 0.60,
        "avg": 0.55,
        # OS/2 typo metrics (USE_TYPO_METRICS); DOM line-box uses rounded px.
        "ascender": 1.024,
        "descender": 0.400,
        "line_gap": 0.0,
    },
    "ibm_plex_sans": {
        "digit": 0.600,
        "upper": 0.66,
        "lower": 0.54,
        "space": 0.236,
        "punct": 0.45,
        "other": 0.65,
        "avg": 0.60,
        "ascender": 1.025,
        "descender": 0.275,
        "line_gap": 0.0,
    },
    # Unknown theme fonts — conservative (wider) fallback.
    "_fallback": {
        "digit": 0.62,
        "upper": 0.72,
        "lower": 0.58,
        "space": 0.30,
        "punct": 0.36,
        "other": 0.66,
        "avg": 0.60,
        "ascender": 1.00,
        "descender": 0.28,
        "line_gap": 0.16,
    },
}

_GLYPH_ADVANCES = {
    "source_sans_3": {
        " ": .200, "!": .315, "%": .841, "&": .639, "'": .275, "+": .513,
        ",": .275, "-": .322, ".": .275, "/": .344, "0": .513, "1": .513,
        "2": .513, "3": .513, "4": .513, "5": .513, "6": .513, "7": .513,
        "8": .513, "9": .513, ":": .275, ";": .275, "?": .444,
        "A": .558, "B": .597, "C": .576, "D": .625, "E": .538, "F": .510,
        "G": .628, "H": .663, "I": .282, "J": .494, "K": .597, "L": .502,
        "M": .745, "N": .657, "O": .674, "P": .582, "Q": .674, "R": .592,
        "S": .545, "T": .546, "U": .655, "V": .536, "W": .800, "X": .541,
        "Y": .501, "Z": .540,
        "a": .516, "b": .563, "c": .462, "d": .564, "e": .507, "f": .317,
        "g": .520, "h": .558, "i": .262, "j": .263, "k": .522, "l": .271,
        "m": .843, "n": .560, "o": .549, "p": .564, "q": .564, "r": .373,
        "s": .431, "t": .361, "u": .556, "v": .495, "w": .748, "x": .481,
        "y": .495, "z": .443,
    },
    "ibm_plex_sans": {
        " ": .236, "!": .309, "%": .960, "&": .713, "'": .260, "+": .600,
        ",": .299, "-": .402, ".": .299, "/": .437, "0": .600, "1": .600,
        "2": .600, "3": .600, "4": .600, "5": .600, "6": .600, "7": .600,
        "8": .600, "9": .600, ":": .319, ";": .319, "?": .493,
        "A": .672, "B": .663, "C": .642, "D": .689, "E": .600, "F": .577,
        "G": .712, "H": .719, "I": .423, "J": .545, "K": .678, "L": .521,
        "M": .817, "N": .719, "O": .712, "P": .641, "Q": .712, "R": .664,
        "S": .611, "T": .580, "U": .689, "V": .638, "W": .949, "X": .655,
        "Y": .632, "Z": .599,
        "a": .559, "b": .600, "c": .513, "d": .600, "e": .558, "f": .350,
        "g": .545, "h": .588, "i": .275, "j": .275, "k": .562, "l": .294,
        "m": .888, "n": .588, "o": .563, "p": .600, "q": .600, "r": .393,
        "s": .499, "t": .374, "u": .588, "v": .524, "w": .819, "x": .544,
        "y": .524, "z": .502,
    },
}

_FONT_ALIASES = {
    "source sans 3": "source_sans_3",
    "source sans": "source_sans_3",
    "sourcesans3": "source_sans_3",
    "ibm plex sans": "ibm_plex_sans",
    "ibm plex": "ibm_plex_sans",
    "ibmplexsans": "ibm_plex_sans",
}


def normalize_font_key(name: str | None) -> tuple[str, bool]:
    """Return (metrics_key, is_fallback)."""
    if not name:
        return "source_sans_3", False
    raw = str(name).strip().lower().replace('"', "").replace("'", "")
    # First family in a CSS stack.
    first = raw.split(",")[0].strip()
    key = _FONT_ALIASES.get(first)
    if key:
        return key, False
    if first in _FONT_METRICS:
        return first, False
    return "_fallback", True


def _char_class(ch: str) -> str:
    if ch.isspace():
        return "space"
    if ch.isdigit():
        return "digit"
    if ch.isupper():
        return "upper"
    if ch.islower():
        return "lower"
    # Common punctuation / currency
    if ch in ".,;:!?%/+-–—()[]{}'\"$€£¥#@*&_=<>|\\":
        return "punct"
    return "other"


def measure_text_width(
    text: str,
    font_size: float,
    *,
    font: str | None = "source_sans_3",
    weight: str | int | None = None,
) -> float:
    """Estimated advance width in px (conservative)."""
    key, _ = normalize_font_key(font)
    m = _FONT_METRICS[key]
    if not text:
        return 0.0
    fs = float(font_size)
    total = 0.0
    # FreeType/Linux CI snaps each glyph advance to whole px; DirectWrite keeps
    # subpixel sums. Cover both with max(subpixel, hinted) inside the #150 band.
    hinted = 0
    glyphs = _GLYPH_ADVANCES.get(key, {})
    for ch in text:
        adv = glyphs.get(ch, m[_char_class(ch)])
        total += adv
        hinted += int(adv * fs + 0.5)
    subpixel = math.ceil(total * fs * 4.0) / 4.0 + 0.25
    return max(subpixel, float(hinted))


def measure_text_height(
    font_size: float,
    *,
    font: str | None = "source_sans_3",
    lines: int = 1,
) -> float:
    key, _ = normalize_font_key(font)
    m = _FONT_METRICS[key]
    fs = float(font_size)
    # Chromium font-bounding box: round each side to px then sum (matches DOM).
    line_h = float(
        int(m["ascender"] * fs + 0.5)
        + int(m["descender"] * fs + 0.5)
        + int(m["line_gap"] * fs + 0.5)
    )
    return line_h * max(int(lines), 1)


def measure_label_box(
    text: str,
    font_size: float,
    *,
    font: str | None = "source_sans_3",
    weight: str | int | None = None,
    lines: Sequence[str] | None = None,
    rotation_deg: float = 0.0,
) -> tuple[float, float]:
    """Return (width, height) of the axis-aligned bounding box after rotation."""
    if lines is None:
        segs = [text] if text else [""]
    else:
        segs = list(lines) or [""]
    w = max(measure_text_width(s, font_size, font=font, weight=weight) for s in segs)
    h = measure_text_height(font_size, font=font, lines=len(segs))
    rot = abs(float(rotation_deg)) % 180.0
    if rot > 90.0:
        rot = 180.0 - rot
    if rot < 0.5:
        return w, h
    rad = math.radians(rot)
    # AABB of rotated rectangle. 0.01px covers float32 layout vs float64 trig.
    aw = abs(w * math.cos(rad)) + abs(h * math.sin(rad)) + 0.01
    ah = abs(w * math.sin(rad)) + abs(h * math.cos(rad)) + 0.01
    return aw, ah


# ---------------------------------------------------------------------------
# Label adaptation helpers
# ---------------------------------------------------------------------------


def wrap_label(text: str, *, max_lines: int = 2) -> list[str]:
    """Wrap at whitespace/punctuation; never split words; ≤ max_lines."""
    text = (text or "").strip()
    if not text or max_lines <= 1:
        return [text] if text else [""]
    # Prefer natural break near midpoint.
    tokens = [t for t in re.split(r"(\s+)", text) if t != ""]
    if len(tokens) == 1:
        # Try punctuation soft-break without eating the char into both sides.
        parts = re.split(r"(?<=[/\-–,;:·])", text)
        parts = [p for p in parts if p]
        if len(parts) >= 2:
            mid = max(1, len(parts) // 2)
            left = "".join(parts[:mid]).strip()
            right = "".join(parts[mid:]).strip()
            if left and right:
                return [left, right]
        return [text]
    # Greedy pack into two lines by char budget ≈ half.
    budget = max(1, (len(text) + 1) // 2)
    line1: list[str] = []
    n = 0
    i = 0
    while i < len(tokens):
        t = tokens[i]
        add = len(t)
        if line1 and n + add > budget and not t.isspace():
            break
        line1.append(t)
        n += add
        i += 1
    left = "".join(line1).strip()
    right = "".join(tokens[i:]).strip()
    if not right:
        return [left] if left else [text]
    if not left:
        return [right]
    return [left, right]


def ellipsize(text: str, font_size: float, max_width: float, *, font: str | None = None) -> str:
    """Final axis-label resort: truncate with ellipsis to fit max_width."""
    text = text or ""
    if measure_text_width(text, font_size, font=font) <= max_width:
        return text
    ell = "…"
    if measure_text_width(ell, font_size, font=font) > max_width:
        return ""
    lo, hi = 0, len(text)
    best = ell
    while lo <= hi:
        mid = (lo + hi) // 2
        cand = text[:mid].rstrip() + ell
        if measure_text_width(cand, font_size, font=font) <= max_width:
            best = cand
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def skip_indices(n: int, keep_step: int) -> list[int]:
    """Evenly skip ticks; always retain first and last. keep_step≥1 shows every k-th."""
    if n <= 0:
        return []
    if keep_step <= 1 or n <= 2:
        return list(range(n))
    kept = {0, n - 1}
    for i in range(0, n, keep_step):
        kept.add(i)
    return sorted(kept)


def _x_slot_width(plot_w: float, n: int) -> float:
    if n <= 0:
        return plot_w
    return plot_w / n


@dataclass
class AxisLabelPlan:
    """Per-category display plan for the category (x) axis."""

    texts: list[str]  # display text (may be short/ellipsized); "" = skipped
    full_texts: list[str]  # accessibility / diagnostics full labels
    lines: list[list[str]]  # wrapped lines per category (display)
    rotation_deg: float = 0.0
    used_short: bool = False
    used_wrap: bool = False
    used_skip: bool = False
    used_ellipsis: bool = False
    skipped_count: int = 0
    short_count: int = 0
    ellipsis_count: int = 0


@dataclass
class AutoTypoPlan:
    """Resolved auto typography for one chart pane."""

    enabled: bool = False
    chart_type: str = ""
    x_tick_font_size: int = 13
    y_tick_font_size: int = 13
    datalabel_font_size: int = 11
    x_tick_font_size_set: int = 0  # 1 if explicit override
    y_tick_font_size_set: int = 0
    datalabel_font_size_set: int = 0
    x_explicit: bool = False
    y_explicit: bool = False
    dl_explicit: bool = False
    plot_w: float = 0.0
    plot_h: float = 0.0
    host_w: float = 0.0
    host_h: float = 0.0
    used_fallback_dims: bool = False
    used_fallback_font: bool = False
    x_labels: AxisLabelPlan | None = None
    y_tick_values: list[float] = field(default_factory=list)
    y_tick_labels: list[str] = field(default_factory=list)
    secondary_y_tick_values: list[float] = field(default_factory=list)
    secondary_y_tick_labels: list[str] = field(default_factory=list)
    y_domain_min: float | None = None
    y_domain_max: float | None = None
    secondary_y_domain_min: float | None = None
    secondary_y_domain_max: float | None = None
    y_ticks_reduced: bool = False
    secondary_y_ticks_reduced: bool = False
    datalabels_suppressed: bool = False
    datalabel_suppress_count: int = 0
    warnings: list[str] = field(default_factory=list)
    confidence: str = "high"  # high | reduced

    def to_typo_dict(self) -> dict[str, int]:
        return {
            "x_tick_font_size": int(self.x_tick_font_size),
            "y_tick_font_size": int(self.y_tick_font_size),
            "datalabel_font_size": int(self.datalabel_font_size),
            "x_tick_font_size_set": 1 if (self.enabled or self.x_explicit) else 0,
            "y_tick_font_size_set": 1 if (self.enabled or self.y_explicit) else 0,
            "datalabel_font_size_set": 1
            if (self.enabled and not self.datalabels_suppressed) or self.dl_explicit
            else 0,
        }

    def diagnostic_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "mode": "auto" if self.enabled else "off",
            "chart_type": self.chart_type,
            "x_tick_font_size": self.x_tick_font_size,
            "y_tick_font_size": self.y_tick_font_size,
            "datalabel_font_size": (
                0 if self.datalabels_suppressed else self.datalabel_font_size
            ),
            "plot_w": round(self.plot_w, 1),
            "plot_h": round(self.plot_h, 1),
            "host_w": round(self.host_w, 1),
            "host_h": round(self.host_h, 1),
            "x_explicit": self.x_explicit,
            "y_explicit": self.y_explicit,
            "dl_explicit": self.dl_explicit,
            "used_fallback_dims": self.used_fallback_dims,
            "used_fallback_font": self.used_fallback_font,
            "y_ticks_reduced": self.y_ticks_reduced,
            "secondary_y_ticks_reduced": self.secondary_y_ticks_reduced,
            "y_tick_count": len(self.y_tick_values),
            "secondary_y_tick_count": len(self.secondary_y_tick_values),
            "y_domain_min": self.y_domain_min,
            "y_domain_max": self.y_domain_max,
            "secondary_y_domain_min": self.secondary_y_domain_min,
            "secondary_y_domain_max": self.secondary_y_domain_max,
            "datalabels_suppressed": self.datalabels_suppressed,
            "datalabel_suppress_count": self.datalabel_suppress_count,
            "confidence": self.confidence,
        }
        if self.x_labels is not None:
            xl = self.x_labels
            d.update(
                {
                    "x_rotation_deg": xl.rotation_deg,
                    "x_used_wrap": xl.used_wrap,
                    "x_used_short": xl.used_short,
                    "x_used_skip": xl.used_skip,
                    "x_used_ellipsis": xl.used_ellipsis,
                    "x_skipped_count": xl.skipped_count,
                    "x_short_count": xl.short_count,
                    "x_ellipsis_count": xl.ellipsis_count,
                    "x_display_labels": list(xl.texts),
                    "x_full_labels": list(xl.full_texts),
                }
            )
        if self.warnings:
            d["warnings"] = list(self.warnings)
        return d


def _try_x_fit(
    labels: Sequence[str],
    font_size: int,
    plot_w: float,
    bottom_budget: float,
    *,
    font: str,
    rotation: float,
    wrap: bool,
    positions: Sequence[int] | None = None,
    total_slots: int | None = None,
) -> tuple[bool, list[list[str]], float]:
    """Return (fits, lines_per_label, used_height)."""
    n = len(labels)
    if n == 0:
        return True, [], 0.0
    slots = total_slots or n
    slot = _x_slot_width(plot_w, slots)
    pos = list(positions) if positions is not None else list(range(n))
    if len(pos) != n:
        return False, [], 0.0

    def nearest_gap(i: int) -> float:
        gaps = []
        if i:
            gaps.append(pos[i] - pos[i - 1])
        if i + 1 < n:
            gaps.append(pos[i + 1] - pos[i])
        return min(gaps, default=slots) * slot

    def edge_clearance(i: int) -> float:
        return min(pos[i] + 0.5, slots - pos[i] - 0.5) * slot

    lines_out: list[list[str]] = []
    rotated_half_widths: list[float] = []
    max_h = 0.0
    for label_i, lab in enumerate(labels):
        label_max_w = nearest_gap(label_i) * (1.35 if rotation >= 30 else 0.95)
        segs = wrap_label(lab, max_lines=2) if wrap else [lab]
        if not wrap:
            segs = [lab]
        if not lab:
            lines_out.append([])
            continue
        # If wrap produced 2 lines, each line must fit slot width.
        ok_lines = True
        for s in segs:
            bw, bh = measure_label_box(
                s, font_size, font=font, rotation_deg=rotation if len(segs) == 1 else 0.0
            )
            # Multi-line unrotated: width is max line; height sums.
            if rotation < 0.5:
                if measure_text_width(s, font_size, font=font) > label_max_w:
                    ok_lines = False
                    break
            else:
                if bw > label_max_w * 1.1 and measure_text_width(s, font_size, font=font) > label_max_w:
                    # Allow tall rotated labels; width along baseline limited by slot diagonal.
                    baseline_w = measure_text_width(s, font_size, font=font)
                    # Projected horizontal footprint.
                    rad = math.radians(rotation)
                    foot = baseline_w * math.cos(rad) + measure_text_height(font_size, font=font) * math.sin(rad)
                    if foot > nearest_gap(label_i) * 1.25:
                        ok_lines = False
                        break
        if not ok_lines:
            return False, [], 0.0
        if rotation < 0.5:
            h = measure_text_height(font_size, font=font, lines=len(segs))
            w = max(measure_text_width(s, font_size, font=font) for s in segs)
            if w > min(label_max_w, edge_clearance(label_i) * 2):
                return False, [], 0.0
        else:
            # Single-line rotated only in our stages.
            segs = [lab]
            w, h = measure_label_box(lab, font_size, font=font, rotation_deg=rotation)
            if w > plot_w and n == 1:
                return False, [], 0.0
            # Neighbor overlap: projected half-widths must fit half-slot with pad.
            rad = math.radians(rotation)
            baseline_w = measure_text_width(lab, font_size, font=font)
            half_foot = 0.5 * (
                baseline_w * math.cos(rad)
                + measure_text_height(font_size, font=font) * math.sin(rad)
            )
            rotated_half_widths.append(half_foot)
        lines_out.append(segs)
        max_h = max(max_h, h if rotation >= 0.5 else measure_text_height(font_size, font=font, lines=len(segs)))
    if rotation >= 0.5:
        for i, (left, right) in enumerate(zip(rotated_half_widths, rotated_half_widths[1:])):
            if left + right + _ROT_PAD > (pos[i + 1] - pos[i]) * slot:
                return False, [], 0.0
    used_h = max_h + _X_AXIS_GAP
    if used_h > bottom_budget + 1e-6:
        return False, [], 0.0
    # Adjacent unrotated overlap check.
    if rotation < 0.5 and n >= 2:
        for i, segs in enumerate(lines_out):
            if not segs:
                continue
            w = max(measure_text_width(s, font_size, font=font) for s in segs)
            if w > min(nearest_gap(i) - 2.0, edge_clearance(i) * 2):
                return False, [], 0.0
    return True, lines_out, used_h


def _fit_x_labels(
    full_labels: Sequence[str],
    short_labels: Sequence[str | None],
    font_size: int,
    plot_w: float,
    bottom_budget: float,
    *,
    font: str = "source_sans_3",
    allow_rotation: bool = True,
) -> AxisLabelPlan | None:
    """Adaptation order from the issue. Returns plan or None if nothing fits."""
    n = len(full_labels)
    if n == 0:
        return AxisLabelPlan(texts=[], full_texts=[], lines=[])

    def attempt(labels: Sequence[str], *, rotation: float, wrap: bool) -> AxisLabelPlan | None:
        ok, lines, _h = _try_x_fit(
            labels, font_size, plot_w, bottom_budget, font=font, rotation=rotation, wrap=wrap
        )
        if not ok:
            return None
        return AxisLabelPlan(
            texts=list(labels),
            full_texts=list(full_labels),
            lines=lines,
            rotation_deg=float(rotation),
            used_wrap=wrap and any(len(L) > 1 for L in lines),
        )

    # Stages 1–3: full labels
    stages = [(False, 0.0), (True, 0.0)]
    if allow_rotation:
        stages.extend([(False, 30.0), (False, 45.0)])
    for wrap, rotation in stages:
        plan = attempt(full_labels, rotation=rotation, wrap=wrap)
        if plan is not None:
            return plan

    # Stage 4: short_label, repeat 1–3
    shorts = []
    any_short = False
    for i, full in enumerate(full_labels):
        s = short_labels[i] if i < len(short_labels) else None
        if s is not None and str(s).strip():
            shorts.append(str(s).strip())
            any_short = True
        else:
            shorts.append(full)
    if any_short:
        for wrap, rotation in stages:
            plan = attempt(shorts, rotation=rotation, wrap=wrap)
            if plan is not None:
                plan.used_short = True
                plan.short_count = sum(
                    1
                    for i, s in enumerate(shorts)
                    if short_labels[i] is not None
                    and str(short_labels[i] or "").strip()
                    and s != full_labels[i]
                )
                return plan

    # Stage 5: evenly skip full labels. short_label is only a way to avoid
    # information loss, never a substitute on an already-skipped axis.
    base = list(full_labels)
    for step in range(2, n):
        kept = set(skip_indices(n, step))
        trial = [base[i] if i in kept else "" for i in range(n)]
        for wrap, rotation in stages:
            kept_labs = [trial[i] for i in range(n) if trial[i]]
            if not kept_labs:
                continue
            ok, lines_kept, _h = _try_x_fit(
                kept_labs,
                font_size,
                plot_w,
                bottom_budget,
                font=font,
                rotation=rotation,
                wrap=wrap,
                positions=sorted(kept),
                total_slots=n,
            )
            if not ok:
                continue
            lines_full: list[list[str]] = []
            ki = 0
            texts: list[str] = []
            for i in range(n):
                if trial[i]:
                    lines_full.append(lines_kept[ki])
                    texts.append(trial[i])
                    ki += 1
                else:
                    lines_full.append([])
                    texts.append("")
            return AxisLabelPlan(
                texts=texts,
                full_texts=list(full_labels),
                lines=lines_full,
                rotation_deg=float(rotation),
                used_wrap=wrap and any(len(L) > 1 for L in lines_kept),
                used_skip=True,
                skipped_count=n - len(kept),
            )

    # Stage 6: ellipsis as final axis resort (unrotated, no skip first).
    # Budget must match _try_x_fit unrotated adjacent limit (gap - 2), not only
    # the 0.95*slot line-width cap — otherwise ellipsize can emit a label that
    # still fails the neighbor check (tight 2-slot cases on Linux FreeType).
    def _ellipsis_budget(slots: int) -> float:
        raw = _x_slot_width(plot_w, slots)
        line_cap = raw * 0.95
        if slots >= 2:
            return min(line_cap, raw - 2.0)
        return line_cap

    slot = _ellipsis_budget(n)
    ellipsed = [ellipsize(full_labels[i], font_size, slot, font=font) for i in range(n)]
    plan = attempt(ellipsed, rotation=0.0, wrap=False)
    if plan is not None:
        plan.used_ellipsis = True
        plan.ellipsis_count = sum(
            1 for i, t in enumerate(ellipsed) if t != full_labels[i]
        )
        return plan

    # Last ditch: skip + ellipsis
    for step in range(2, n + 1):
        kept = set(skip_indices(n, step))
        slot_k = _ellipsis_budget(n)
        texts = []
        for i in range(n):
            if i in kept:
                texts.append(ellipsize(full_labels[i], font_size, slot_k, font=font))
            else:
                texts.append("")
        kept_labs = [t for t in texts if t]
        ok, lines_kept, _h = _try_x_fit(
            kept_labs,
            font_size,
            plot_w,
            bottom_budget,
            font=font,
            rotation=0.0,
            wrap=False,
            positions=sorted(kept),
            total_slots=n,
        )
        if not ok:
            continue
        lines_full = []
        ki = 0
        for t in texts:
            if t:
                lines_full.append(lines_kept[ki])
                ki += 1
            else:
                lines_full.append([])
        return AxisLabelPlan(
            texts=texts,
            full_texts=list(full_labels),
            lines=lines_full,
            rotation_deg=0.0,
            used_skip=True,
            used_ellipsis=True,
            skipped_count=n - len(kept),
            ellipsis_count=sum(
                1 for i, t in enumerate(texts) if t and t != full_labels[i]
            ),
        )
    return None


def _fit_y_ticks(
    tick_labels: Sequence[str],
    tick_values: Sequence[float],
    font_size: int,
    plot_h: float,
    left_budget: float,
    *,
    domain: tuple[float | None, float | None] | None = None,
    font: str = "source_sans_3",
    weight: str | int = "bold",
    horizontal_axis: bool = False,
) -> tuple[bool, list[float], list[str], bool]:
    """Return (fits, values, labels, reduced); may drop interior ticks at the floor."""
    if not tick_labels:
        return True, [], [], False

    def fits(vals: Sequence[float], labs: Sequence[str]) -> bool:
        if not labs:
            return True
        max_w = max(
            measure_text_width(s, font_size, font=font, weight=weight) for s in labs
        )
        h = measure_text_height(font_size, font=font, lines=1)
        if horizontal_axis:
            if h + _Y_AXIS_GAP > left_budget + 1e-6:
                return False
        elif max_w + _Y_AXIS_GAP > left_budget + 1e-6:
            return False
        if len(vals) >= 2:
            ymin, ymax = domain or (min(vals), max(vals))
            ymin = min(vals) if ymin is None else ymin
            ymax = max(vals) if ymax is None else ymax
            span = ymax - ymin or 1.0
            positions = [plot_h * (v - ymin) / span for v in vals]
            positions_sorted = sorted(zip(positions, labs))
            for (a, a_lab), (b, b_lab) in zip(positions_sorted, positions_sorted[1:]):
                # +3px neighbor pad: rounded OS/2 line-boxes are ~1px tighter
                # than prior class metrics; keep dense authored ticks thinning.
                required = (
                    (measure_text_width(a_lab, font_size, font=font, weight=weight)
                     + measure_text_width(b_lab, font_size, font=font, weight=weight)) / 2
                    + 2.0
                    if horizontal_axis
                    else h + 3.0
                )
                if abs(b - a) < required:
                    return False
        return True

    vals = list(tick_values)
    labs = list(tick_labels)
    if fits(vals, labs):
        return True, vals, labs, False

    # Only reduce count at the floor (caller enforces).
    if font_size > AUTO_Y_LO:
        return False, vals, labs, False

    # Preserve endpoints + zero if in domain.
    if len(vals) <= 2:
        return fits(vals, labs), vals, labs, False

    ymin, ymax = vals[0], vals[-1]
    # Keep order of original list.
    zero_in = any(abs(v) < 1e-12 for v in vals) and ymin < 0 < ymax
    # Try progressively fewer interior ticks.
    for keep_total in range(len(vals) - 1, 1, -1):
        if keep_total == 2:
            new_vals = [vals[0], vals[-1]]
        else:
            # Evenly sample including ends.
            idxs = [round(i * (len(vals) - 1) / (keep_total - 1)) for i in range(keep_total)]
            idxs = sorted(set(idxs))
            new_vals = [vals[i] for i in idxs]
            if zero_in and not any(abs(v) < 1e-12 for v in new_vals):
                # Insert zero, drop nearest interior.
                new_vals.append(0.0)
                new_vals = sorted(set(new_vals))
                while len(new_vals) > keep_total:
                    # Drop interior non-zero closest to another tick.
                    interior = [v for v in new_vals if v not in (new_vals[0], new_vals[-1]) and abs(v) > 1e-12]
                    if not interior:
                        break
                    victim = interior[len(interior) // 2]
                    new_vals = [v for v in new_vals if v != victim]
        new_labs = []
        for v in new_vals:
            # Map back to original label if present else format.
            lab = None
            for ov, ol in zip(vals, labs):
                if abs(ov - v) < 1e-9:
                    lab = ol
                    break
            new_labs.append(lab if lab is not None else f"{v:g}")
        if fits(new_vals, new_labs):
            return True, new_vals, new_labs, True
    return False, vals, labs, False


def _fit_datalabels(
    label_texts: Sequence[str],
    font_size: int,
    plot_w: float,
    plot_h: float,
    n_cats: int,
    n_series: int,
    *,
    font: str = "ibm_plex_sans",
    weight: str | int = "bold",
) -> tuple[bool, int]:
    """Ordinary datalabel fit. Returns (fits, suppress_count estimate)."""
    if not label_texts:
        return True, 0
    n_cats = max(n_cats, 1)
    n_series = max(n_series, 1)
    slot_w = plot_w / n_cats / max(n_series, 1)
    slot_h = max(plot_h / max(n_cats * 2, 1), font_size * 2)
    h = measure_text_height(font_size, font=font, lines=1)
    suppress = 0
    for t in label_texts:
        w = measure_text_width(t, font_size, font=font, weight=weight)
        if w + _DL_GAP > slot_w or h + _DL_GAP > slot_h:
            suppress += 1
    # Fit if majority of labels fit; collision path can suppress the rest.
    if suppress == 0:
        return True, 0
    if suppress < len(label_texts):
        # Partial — still accept size; painter/collision suppresses.
        return True, suppress
    return False, suppress


def estimate_plot_box(
    *,
    host_w: float,
    host_h: float,
    chart_type: str,
    has_legend: bool,
    exterior_lane: float = 0.0,
    pad_l: float | None = None,
    pad_r: float | None = None,
    pad_t: float | None = None,
    pad_b: float | None = None,
) -> tuple[float, float, float, float, float, float]:
    """Return (plot_w, plot_h, pad_l, pad_r, pad_t, pad_b) inside host."""
    # Default pads mirror geometry.py / painters (scaled to host, not SVG units).
    defaults = {
        "line_chart": (0.09, 0.04, 0.08, 0.12),
        "grouped_bar_chart": (0.08, 0.03, 0.08, 0.12),
        "stacked_bar_chart": (0.08, 0.03, 0.08, 0.12),
        "combo_chart": (80 / 900, 80 / 900, 40 / 480, 60 / 480),
        "horizontal_bar_chart": (140 / 960, 24 / 960, 16 / 540, 40 / 540),
        "waterfall_chart": (0.06, 0.04, 0.08, 0.14),
    }
    fr = defaults.get(chart_type, (0.08, 0.04, 0.08, 0.12))
    pl = float(pad_l if pad_l is not None else host_w * fr[0])
    pr = float(pad_r if pad_r is not None else host_w * fr[1])
    pt = float(pad_t if pad_t is not None else host_h * fr[2])
    pb = float(pad_b if pad_b is not None else host_h * fr[3])
    if has_legend:
        pt += _LEGEND_H
    if exterior_lane > 0:
        pr += exterior_lane
    plot_w = max(0.0, host_w - pl - pr)
    plot_h = max(0.0, host_h - pt - pb)
    return plot_w, plot_h, pl, pr, pt, pb


def resolve_auto_typography(
    *,
    chart_type: str,
    host_w: float | None,
    host_h: float | None,
    categories: Sequence[str],
    short_labels: Sequence[str | None] | None = None,
    series_count: int = 1,
    y_tick_values: Sequence[float] | None = None,
    y_tick_labels: Sequence[str] | None = None,
    secondary_y_tick_values: Sequence[float] | None = None,
    secondary_y_tick_labels: Sequence[str] | None = None,
    y_domain: tuple[float | None, float | None] | None = None,
    secondary_y_domain: tuple[float | None, float | None] | None = None,
    datalabel_texts: Sequence[str] | None = None,
    has_legend: bool = False,
    want_datalabels: bool = False,
    x_explicit: int | None = None,
    y_explicit: int | None = None,
    dl_explicit: int | None = None,
    font_x: str | None = "source_sans_3",
    font_y: str | None = "ibm_plex_sans",
    font_dl: str | None = "ibm_plex_sans",
    horizontal: bool | None = None,
    allow_y_tick_reduction: bool = True,
) -> AutoTypoPlan:
    """Largest whole-px sizes that fit; axes beat ordinary datalabels."""
    ct = (chart_type or "").lower().strip()
    plan = AutoTypoPlan(enabled=True, chart_type=ct)
    if ct not in AUTO_CHART_TYPES:
        plan.enabled = False
        plan.confidence = "reduced"
        plan.warnings.append(f"auto typography skipped for unsupported type {ct!r}")
        return plan

    is_hbar = horizontal if horizontal is not None else ct == "horizontal_bar_chart"
    used_fb = False
    if host_w is None or host_h is None or host_w <= 0 or host_h <= 0:
        host_w = CONSERVATIVE_PLOT_W
        host_h = CONSERVATIVE_PLOT_H
        used_fb = True
        plan.warnings.append(
            f"fallback dimensions {CONSERVATIVE_PLOT_W:.0f}x{CONSERVATIVE_PLOT_H:.0f}"
        )
        _warn(plan.warnings[-1])

    plan.host_w = float(host_w)
    plan.host_h = float(host_h)
    plan.used_fallback_dims = used_fb

    fx, fb_x = normalize_font_key(font_x)
    fy, fb_y = normalize_font_key(font_y)
    fd, fb_d = normalize_font_key(font_dl)
    if fb_x or fb_y or fb_d:
        plan.used_fallback_font = True
        plan.confidence = "reduced"
        plan.warnings.append("unknown font metrics; using conservative fallback")
        _warn(plan.warnings[-1])

    plot_w, plot_h, pad_l, pad_r, pad_t, pad_b = estimate_plot_box(
        host_w=plan.host_w,
        host_h=plan.host_h,
        chart_type=ct,
        has_legend=has_legend,
    )
    plan.plot_w = plot_w
    plan.plot_h = plot_h

    cats = [str(c) for c in categories]
    shorts = list(short_labels) if short_labels is not None else [None] * len(cats)
    if len(shorts) < len(cats):
        shorts = list(shorts) + [None] * (len(cats) - len(shorts))

    y_vals = list(y_tick_values or [])
    y_labs = list(y_tick_labels or [])
    if y_vals and not y_labs:
        y_labs = [f"{v:g}" for v in y_vals]
    secondary_y_vals = list(secondary_y_tick_values or [])
    secondary_y_labs = list(secondary_y_tick_labels or [])
    if secondary_y_vals and not secondary_y_labs:
        secondary_y_labs = [f"{v:g}" for v in secondary_y_vals]
    dl_texts = list(datalabel_texts or [])

    # Explicit channels are never silently resized.
    plan.x_explicit = x_explicit is not None
    plan.y_explicit = y_explicit is not None
    plan.dl_explicit = dl_explicit is not None
    if plan.x_explicit:
        plan.x_tick_font_size = int(x_explicit)  # type: ignore[arg-type]
        plan.x_tick_font_size_set = 1
    if plan.y_explicit:
        plan.y_tick_font_size = int(y_explicit)  # type: ignore[arg-type]
        plan.y_tick_font_size_set = 1
    if plan.dl_explicit:
        plan.datalabel_font_size = int(dl_explicit)  # type: ignore[arg-type]
        plan.datalabel_font_size_set = 1

    bottom_budget = pad_b
    left_budget = pad_l

    # --- X ticks (category axis; for hbar categories sit on Y visually but
    #     still use x_tick channel naming per chart_config / issue scope) ---
    # Spec channels: x_tick_font_size, y_tick_font_size, ordinary datalabel.
    # For hbar: category labels use y_tick in SVG painters historically; auto
    # keeps semantic channels: category density → x channel for vertical charts
    # and y channel for horizontal charts' category side.
    cat_is_x = not is_hbar

    def choose_cat_size(explicit: int | None) -> tuple[int, AxisLabelPlan | None]:
        if explicit is not None:
            size = int(explicit)
            # Still compute adaptation at fixed size.
            # Category axis budget: bottom for vertical, left for hbar.
            if cat_is_x:
                p = _fit_x_labels(
                    cats, shorts, size, plot_w, bottom_budget, font=fx
                )
            else:
                p = _fit_x_labels(
                    cats,
                    shorts,
                    size,
                    left_budget * max(len(cats), 1),
                    plot_h / max(len(cats), 1),
                    font=fy,
                    allow_rotation=False,
                )
            if p is None:
                # Force ellipsis plan
                p = AxisLabelPlan(
                    texts=[ellipsize(c, size, max(left_budget, bottom_budget) * 0.9, font=fx) for c in cats],
                    full_texts=list(cats),
                    lines=[[ellipsize(c, size, max(left_budget, bottom_budget) * 0.9, font=fx)] for c in cats],
                    used_ellipsis=True,
                )
                plan.warnings.append("category labels ellipsized under explicit size")
                _warn(plan.warnings[-1])
            return size, p
        lo, hi = (AUTO_X_LO, AUTO_X_HI) if cat_is_x else (AUTO_Y_LO, AUTO_Y_HI)
        def fit_at(size: int) -> AxisLabelPlan | None:
            return _fit_x_labels(
                cats,
                shorts,
                size,
                plot_w if cat_is_x else left_budget * max(len(cats), 1),
                bottom_budget if cat_is_x else plot_h / max(len(cats), 1),
                font=fx if cat_is_x else fy,
                allow_rotation=cat_is_x,
            )

        # Adaptation order outranks point size: full (wrap/rot) first, then
        # short/skip, and only then ellipsis — a 24px ellipsis must not beat a
        # 12px short_label that keeps readable text.
        best: tuple[int, AxisLabelPlan | None] = (lo, None)
        for size in range(hi, lo - 1, -1):
            p = fit_at(size)
            if p is not None and not (p.used_short or p.used_skip or p.used_ellipsis):
                best = (size, p)
                break
        if best[1] is None:
            for size in range(hi, lo - 1, -1):
                p = fit_at(size)
                if p is not None and not p.used_ellipsis:
                    best = (size, p)
                    break
        if best[1] is None:
            for size in range(hi, lo - 1, -1):
                p = fit_at(size)
                if p is not None:
                    best = (size, p)
                    break
        if best[1] is None:
            # Floor with whatever adaptation we can.
            size = lo
            p = fit_at(size)
            if p is None:
                p = AxisLabelPlan(
                    texts=list(cats),
                    full_texts=list(cats),
                    lines=[[c] for c in cats],
                )
                plan.warnings.append("unresolved category label overflow at floor")
                _warn(plan.warnings[-1])
                plan.confidence = "reduced"
            best = (size, p)
        return best

    def choose_val_size(
        explicit: int | None,
        labels: Sequence[str],
        values: Sequence[float],
    ) -> tuple[int, list[float], list[str], bool, list[float], list[str], bool]:
        def fit(size: int, labs: Sequence[str], vals: Sequence[float]):
            return _fit_y_ticks(
                labs, vals, size, plot_h if cat_is_x else plot_w,
                left_budget if cat_is_x else bottom_budget,
                domain=y_domain,
                font=fy if cat_is_x else fx,
                horizontal_axis=not cat_is_x,
            )

        def at(size: int):
            ok, vv, ll, red = fit(size, labels, values)
            ok2, vv2, ll2, red2 = _fit_y_ticks(
                secondary_y_labs, secondary_y_vals, size,
                plot_h if cat_is_x else plot_w,
                left_budget if cat_is_x else bottom_budget,
                domain=secondary_y_domain,
                font=fy if cat_is_x else fx,
                horizontal_axis=not cat_is_x,
            )
            return ok and ok2, vv, ll, red, vv2, ll2, red2

        if explicit is not None:
            return (int(explicit), *at(int(explicit))[1:])
        lo, hi = (AUTO_Y_LO, AUTO_Y_HI) if cat_is_x else (AUTO_X_LO, AUTO_X_HI)
        best = (lo, list(values), list(labels), False, list(secondary_y_vals), list(secondary_y_labs), False)
        for size in range(hi, lo - 1, -1):
            ok, vv, ll, red, vv2, ll2, red2 = at(size)
            if ok and (allow_y_tick_reduction or not (red or red2)):
                best = (size, vv, ll, red, vv2, ll2, red2)
                break
        return best

    cat_size, cat_plan = choose_cat_size(x_explicit if cat_is_x else y_explicit)
    val_size, vv, ll, red, vv2, ll2, red2 = choose_val_size(
        y_explicit if cat_is_x else x_explicit, y_labs, y_vals
    )

    if cat_is_x:
        plan.x_tick_font_size = cat_size
        plan.y_tick_font_size = val_size
        plan.x_labels = cat_plan
    else:
        plan.y_tick_font_size = cat_size
        plan.x_tick_font_size = val_size
        plan.x_labels = cat_plan  # category plan still stored here

    plan.y_tick_values = vv
    plan.y_tick_labels = ll
    plan.secondary_y_tick_values = vv2
    plan.secondary_y_tick_labels = ll2
    plan.y_ticks_reduced = red
    plan.secondary_y_ticks_reduced = red2
    if y_domain is not None:
        plan.y_domain_min, plan.y_domain_max = y_domain
    if secondary_y_domain is not None:
        plan.secondary_y_domain_min, plan.secondary_y_domain_max = secondary_y_domain
    if red or red2:
        plan.warnings.append("y tick count reduced at floor to preserve endpoints")
        _warn(plan.warnings[-1])

    if cat_plan is not None:
        if cat_plan.used_skip:
            plan.warnings.append(
                f"category ticks skipped: {cat_plan.skipped_count}"
            )
            _warn(plan.warnings[-1])
        if cat_plan.used_short:
            plan.warnings.append(
                f"short_label substituted: {cat_plan.short_count}"
            )
            _warn(plan.warnings[-1])
        if cat_plan.used_ellipsis:
            plan.warnings.append(
                f"category labels ellipsized: {cat_plan.ellipsis_count}"
            )
            _warn(plan.warnings[-1])

    # --- Ordinary datalabels (priority below axes) ---
    if plan.dl_explicit:
        size = int(dl_explicit)  # type: ignore[arg-type]
        ok, sup = _fit_datalabels(
            dl_texts,
            size,
            plot_w,
            plot_h,
            len(cats),
            series_count,
            font=fd,
        )
        plan.datalabel_font_size = size
        if not ok:
            plan.datalabels_suppressed = True
            plan.datalabel_suppress_count = len(dl_texts)
            plan.warnings.append("ordinary datalabels suppressed under explicit size")
            _warn(plan.warnings[-1])
        elif sup:
            plan.datalabel_suppress_count = sup
    elif want_datalabels and dl_texts:
        chosen = AUTO_DL_LO
        suppressed = False
        sup_count = 0
        for size in range(AUTO_DL_HI, AUTO_DL_LO - 1, -1):
            ok, sup = _fit_datalabels(
                dl_texts, size, plot_w, plot_h, len(cats), series_count, font=fd
            )
            if ok:
                chosen = size
                sup_count = sup
                break
        else:
            # Floor still overflows → suppress ordinary datalabels (axes win).
            suppressed = True
            sup_count = len(dl_texts)
            plan.warnings.append("ordinary datalabels suppressed to preserve axes")
            _warn(plan.warnings[-1])
        plan.datalabel_font_size = chosen
        plan.datalabels_suppressed = suppressed
        plan.datalabel_suppress_count = sup_count
        if not suppressed:
            plan.datalabel_font_size_set = 1
    else:
        # No ordinary datalabels requested — leave size at legacy default marker.
        plan.datalabel_font_size = AUTO_DL_LO
        plan.datalabel_font_size_set = 0

    if not plan.x_explicit:
        plan.x_tick_font_size_set = 1  # auto chose a real size
    if not plan.y_explicit:
        plan.y_tick_font_size_set = 1

    return plan


def sync_sibling_plans(plans: Sequence[AutoTypoPlan]) -> list[AutoTypoPlan]:
    """Largest common auto size per channel across sibling panes.

    Explicit overrides stay local and are excluded from that channel's sync.
    """
    items = list(plans)
    if len(items) <= 1:
        return items

    def common(attr: str, explicit_attr: str, lo: int) -> int | None:
        auto_sizes = [
            int(getattr(p, attr))
            for p in items
            if p.enabled and not getattr(p, explicit_attr)
        ]
        if not auto_sizes:
            return None
        return max(lo, min(auto_sizes))

    cx = common("x_tick_font_size", "x_explicit", AUTO_X_LO)
    cy = common("y_tick_font_size", "y_explicit", AUTO_Y_LO)
    cd = common("datalabel_font_size", "dl_explicit", AUTO_DL_LO)

    out: list[AutoTypoPlan] = []
    for p in items:
        if not p.enabled:
            out.append(p)
            continue
        # Re-fit adaptation at the synced sizes when this channel is auto.
        new = AutoTypoPlan(**{**p.__dict__})
        if cx is not None and not p.x_explicit:
            new.x_tick_font_size = cx
        if cy is not None and not p.y_explicit:
            new.y_tick_font_size = cy
        if cd is not None and not p.dl_explicit and not p.datalabels_suppressed:
            new.datalabel_font_size = cd
        # Note: per-pane rotation/skip/wrap stay independent (already on plan).
        # If synced size is smaller, existing adaptation still fits; if we ever
        # synced upward (we don't — min of sizes), we'd re-fit.
        out.append(new)
    return out


def full_label_aria_suffix(plan: AutoTypoPlan | None) -> str:
    """Accessible full category labels retained when display labels are shortened."""
    if not plan or not plan.enabled or plan.x_labels is None:
        return ""
    labels = [label for label in plan.x_labels.full_texts if label]
    return f"; categories: {', '.join(labels)}" if labels else ""


def plan_to_data_attrs(plan: AutoTypoPlan, *, value_axis_visible: bool = True) -> str:
    """Compact data-* attribute string for chart wrappers."""
    if not plan.enabled:
        return ""
    d = plan.diagnostic_dict()
    # Compact subset for DOM.
    keys = (
        ("data-auto-typo", "1"),
        ("data-auto-x-tick", str(d["x_tick_font_size"])),
        ("data-auto-y-tick", str(d["y_tick_font_size"])),
        ("data-auto-datalabel", str(d["datalabel_font_size"])),
        ("data-auto-plot", f"{d['plot_w']}x{d['plot_h']}"),
        ("data-auto-x-rot", str(d.get("x_rotation_deg", 0))),
        ("data-auto-x-wrap", str(int(bool(d.get("x_used_wrap"))))),
        ("data-auto-x-skip", str(d.get("x_skipped_count", 0))),
        ("data-auto-y-reduced", str(int(bool(d.get("y_ticks_reduced"))))),
        ("data-auto-y-ticks", str(0 if plan.chart_type == "waterfall_chart" or not value_axis_visible else len(plan.y_tick_values))),
        ("data-auto-y1-ticks", str(0 if not value_axis_visible else len(plan.secondary_y_tick_values))),
        ("data-auto-x-labels", html.escape(json.dumps(["\n".join(lines) for lines in plan.x_labels.lines if lines] if plan.x_labels else []), quote=True)),
        ("data-auto-x-full-labels", html.escape(json.dumps(plan.x_labels.full_texts if plan.x_labels else []), quote=True)),
        ("data-auto-x-short", str(d.get("x_short_count", 0))),
        ("data-auto-x-ellipsis", str(d.get("x_ellipsis_count", 0))),
        ("data-auto-dl-suppress", str(d.get("datalabel_suppress_count", 0))),
        ("data-auto-confidence", str(d.get("confidence", "high"))),
    )
    return "".join(f' {k}="{v}"' for k, v in keys)


def chart_host_dimensions(layout: str) -> tuple[int, int]:
    """Canonical canvas dimensions for direct Chart.js/SVG chart layouts."""
    return {
        "horizontal_bar_chart": (960, 540),
        "waterfall_chart": (1200, 520),
    }.get(layout, (900, 480))


def svg_viewport_dimensions(
    layout: str, host_w: float | None = None
) -> tuple[float, float]:
    """Rendered dimensions for a fixed-aspect SVG fallback."""
    default_w, default_h = chart_host_dimensions(layout)
    width = float(default_w if host_w is None else host_w)
    return width, width * default_h / default_w


def svg_label_transform(plan: AutoTypoPlan | None, x: float, y: float) -> str:
    """SVG equivalent of the plan's Chart.js category-axis rotation."""
    rotation = plan.x_labels.rotation_deg if plan and plan.x_labels else 0.0
    return f' transform="rotate(-{rotation:g} {x:.1f} {y:.1f})"' if rotation else ""


def axis_config_after_break(
    cfg: Mapping[str, Any], *, break_overrides_min: bool = False
) -> dict[str, Any]:
    """Return a chart config whose domain excludes a configured break band."""
    effective = dict(cfg)
    axis_break = cfg.get("y_axis_break")
    if not isinstance(axis_break, Mapping) or axis_break.get("to") is None:
        return effective
    try:
        minimum = float(axis_break["to"])
    except (TypeError, ValueError):
        return effective
    if break_overrides_min or cfg.get("y_axis_min") is None:
        effective["y_axis_min"] = minimum
    else:
        return effective
    ticks = cfg.get("y_axis_ticks")
    if not isinstance(ticks, (list, tuple)):
        return effective
    try:
        retained = [float(tick) for tick in ticks if float(tick) >= minimum]
    except (TypeError, ValueError):
        return effective
    maximum = effective.get("y_axis_max")
    if maximum is not None:
        try:
            retained = [tick for tick in retained if tick <= float(maximum)]
        except (TypeError, ValueError):
            return effective
    if len(retained) >= 2:
        effective["y_axis_ticks"] = retained
        effective["force_ticks"] = bool(cfg.get("force_ticks"))
    else:
        effective.pop("y_axis_ticks", None)
        effective["force_ticks"] = False
    return effective


def svg_auto_axis_view(
    plan: AutoTypoPlan | None,
    *,
    labels: Sequence[str],
    ticks: Sequence[float],
    format_tick: Callable[[float], str],
) -> tuple[list[list[str]], list[tuple[float, str]]]:
    """Return the stashed plan's SVG category lines and value-axis ticks."""
    category_lines = [[str(label)] for label in labels]
    value_ticks = [(float(tick), format_tick(float(tick))) for tick in ticks]
    if not plan or not plan.enabled:
        return category_lines, value_ticks
    if plan.x_labels is not None and len(plan.x_labels.lines) == len(labels):
        category_lines = [list(lines) for lines in plan.x_labels.lines]
    if plan.y_tick_values:
        value_ticks = list(zip(plan.y_tick_values, plan.y_tick_labels))
    return category_lines, value_ticks


def apply_plan_to_chartjs_options(
    options: dict[str, Any],
    plan: AutoTypoPlan,
    *,
    labels: Sequence[str] | None = None,
    horizontal: bool = False,
    category_offset: bool = False,
) -> dict[str, Any]:
    """Mutate Chart.js options with resolved sizes + axis adaptation."""
    if not plan.enabled:
        return options
    options["_rv2AutoTypography"] = True
    scales = options.setdefault("scales", {})
    x = scales.setdefault("x", {})
    y = scales.setdefault("y", {})
    x_ticks = x.setdefault("ticks", {})
    y_ticks = y.setdefault("ticks", {})

    x_font = x_ticks.setdefault("font", {})
    y_font = y_ticks.setdefault("font", {})
    if isinstance(x_font, dict):
        x_font["size"] = plan.x_tick_font_size
    if isinstance(y_font, dict):
        y_font["size"] = plan.y_tick_font_size
        if plan.y_tick_font_size != 13:
            y_font["weight"] = "bold"

    # Category axis adaptation.
    cat_scale = y if horizontal else x
    cat_ticks = cat_scale.setdefault("ticks", {})
    xl = plan.x_labels
    if xl is not None:
        rot = float(xl.rotation_deg or 0.0)
        if not horizontal:
            cat_ticks["maxRotation"] = rot
            cat_ticks["minRotation"] = rot
            if category_offset:
                cat_scale["offset"] = True
        cat_ticks["autoSkip"] = False
        display = []
        for i, t in enumerate(xl.texts):
            if not t:
                display.append("")
            elif xl.lines and i < len(xl.lines) and len(xl.lines[i]) > 1:
                display.append(list(xl.lines[i]))
            else:
                display.append(t)
        # Chart.js callback can't be a Python callable in JSON — emit parallel
        # label array via afterBuildTicks-unfriendly path: replace data labels.
        cat_ticks["_rv2DisplayLabels"] = display
        cat_ticks["_rv2FullLabels"] = list(xl.full_texts)

    if plan.y_tick_values:
        val_scale = x if horizontal else y
        val_ticks = val_scale.setdefault("ticks", {})
        val_ticks["_rv2Values"] = list(plan.y_tick_values)
        val_ticks["_rv2Labels"] = list(plan.y_tick_labels)
        val_ticks["autoSkip"] = False
        if plan.y_domain_min is not None:
            val_scale["min"] = plan.y_domain_min
        if plan.y_domain_max is not None:
            val_scale["max"] = plan.y_domain_max
        val_ticks.pop("stepSize", None)
    if plan.secondary_y_tick_values:
        secondary = scales.get("y1")
        if isinstance(secondary, dict):
            secondary_ticks = secondary.setdefault("ticks", {})
            secondary_ticks["_rv2Values"] = list(plan.secondary_y_tick_values)
            secondary_ticks["_rv2Labels"] = list(plan.secondary_y_tick_labels)
            secondary_ticks["autoSkip"] = False
            secondary_ticks.pop("stepSize", None)
            if plan.secondary_y_domain_min is not None:
                secondary["min"] = plan.secondary_y_domain_min
            if plan.secondary_y_domain_max is not None:
                secondary["max"] = plan.secondary_y_domain_max

    return options


def merge_plan_into_typo(base: Mapping[str, int], plan: AutoTypoPlan) -> dict[str, int]:
    """Overlay auto plan onto resolve_typography output."""
    out = dict(base)
    if not plan.enabled:
        return out
    td = plan.to_typo_dict()
    out.update(td)
    if plan.datalabels_suppressed:
        out["datalabel_font_size_set"] = 0
    return out


def combo_overlay_domain(
    overlay: Mapping[str, Any], values: Sequence[float],
) -> tuple[float, float]:
    """Return a non-empty overlay axis domain containing its values."""
    numeric = [float(value) for value in values]
    low = min(numeric, default=0.0)
    high = max(numeric, default=10.0)
    try:
        line_min = float(overlay["y_axis_min"]) if overlay.get("y_axis_min") is not None else min(0.0, low * 1.15)
        line_max = float(overlay["y_axis_max"]) if overlay.get("y_axis_max") is not None else max(0.0, high * 1.15)
    except (TypeError, ValueError):
        line_min, line_max = min(0.0, low * 1.15), max(0.0, high * 1.15)
    line_min, line_max = min(line_min, low), max(line_max, high)
    if line_min == line_max:
        padding = max(abs(line_min), 1.0) * 0.15
        return line_min - padding, line_max + padding
    return line_min, line_max


def _extract_categories_and_shorts(
    slide: Mapping[str, Any],
    chart_type: str,
) -> tuple[list[str], list[str | None], int, list[float], list[str], list[float], list[str], list[str], tuple[float | None, float | None], tuple[float | None, float | None]]:
    """Categories, ticks, data labels, and the painters' effective domains."""
    from .bars import _bar_axes, _bar_matrix
    from .core import _chart_config
    from .format import _fmt_unit, _fmt_value_label
    from .lines import _combo_bar_data, _combo_line_data, _line_data

    cfg = _chart_config(slide)
    ct = (chart_type or "").lower().strip()
    from ..slide_view import primary_visual

    cats: list[str] = []
    shorts: list[str | None] = []
    series_count = 1
    values_flat: list[float] = []
    primary_domain: tuple[float | None, float | None] = (None, None)
    secondary_domain: tuple[float | None, float | None] = (None, None)

    from ..slide_view import steps

    pv = primary_visual(slide)
    raw_steps = steps(slide)

    def _short_of(item: Any) -> str | None:
        if isinstance(item, Mapping):
            s = item.get("short_label")
            if s is None:
                return None
            t = str(s).strip()
            return t or None
        return None

    if ct in {
        "grouped_bar_chart",
        "stacked_bar_chart",
        "horizontal_bar_chart",
        "waterfall_chart",
    }:
        labels, series, rows, _pc = _bar_matrix(slide)
        cats = list(labels)
        series_count = max(len(series), 1)
        if ct == "waterfall_chart":
            renderable = [
                i for i, row in enumerate(rows)
                if row and row[0] is not None
            ]
            cats = [cats[i] for i in renderable]
            rows = [rows[i] for i in renderable]
            raw_steps = [raw_steps[i] for i in renderable if i < len(raw_steps)]
        if ct == "stacked_bar_chart":
            values_flat = [
                value
                for row in rows
                for value in (
                    sum(v for v in row if v is not None and v > 0),
                    sum(v for v in row if v is not None and v < 0),
                )
            ]
        else:
            for r in rows:
                for v in r:
                    if v is not None:
                        values_flat.append(float(v))
        for i, item in enumerate(raw_steps):
            if i >= len(cats):
                break
            shorts.append(_short_of(item))
        while len(shorts) < len(cats):
            shorts.append(None)
    elif ct == "line_chart":
        pts = _line_data(slide)
        # _line_data returns list of series dicts or points — support both shapes.
        if pts and isinstance(pts[0], dict) and "points" in pts[0]:
            # multi-series form
            series_count = len(pts)
            first_pts = pts[0].get("points") or []
            cats = [str(p.get("label") or "") for p in first_pts if isinstance(p, dict)]
            for p in first_pts:
                if isinstance(p, dict):
                    shorts.append(_short_of(p))
                    v = p.get("value")
                    if isinstance(v, (int, float)):
                        values_flat.append(float(v))
            for s in pts[1:]:
                for p in s.get("points") or []:
                    if isinstance(p, dict) and isinstance(p.get("value"), (int, float)):
                        values_flat.append(float(p["value"]))
        else:
            cats = [
                str(p.get("label") or p.get("category") or "")
                for p in pts
                if isinstance(p, dict)
            ]
            series_keys: set[str] = set()
            for p in pts:
                if not isinstance(p, dict):
                    continue
                shorts.append(_short_of(p))
                for key, v in p.items():
                    if key == "value" or key.startswith("series_"):
                        if isinstance(v, (int, float)):
                            values_flat.append(float(v))
                        if key.startswith("series_"):
                            series_keys.add(key)
            series_count += len(series_keys)
        while len(shorts) < len(cats):
            shorts.append(None)
    elif ct == "combo_chart":
        labels, series, rows, _pc = _combo_bar_data(slide)
        cats = list(labels)
        series_count = max(len(series), 1)
        values_flat = [
            value
            for row in rows
            for value in (
                sum(v for v in row if v is not None and v > 0),
                sum(v for v in row if v is not None and v < 0),
            )
        ]
        for i, item in enumerate(raw_steps):
            if i >= len(cats):
                break
            shorts.append(_short_of(item))
        while len(shorts) < len(cats):
            shorts.append(None)
    else:
        return [], [], 1, [], [], [], [], [], (None, None), (None, None)

    unit = str(cfg.get("y_axis_unit") if cfg.get("y_axis_unit") is not None else ("%" if ct == "line_chart" else ""))
    if ct == "line_chart":
        from .lines import _line_axis
        _y_min, _y_max, y_ticks = _line_axis(
            axis_config_after_break(cfg, break_overrides_min=True), values_flat
        )
        primary_domain = (_y_min, _y_max)
    elif values_flat:
        axis_cfg = axis_config_after_break(cfg) if ct == "horizontal_bar_chart" else cfg
        _y_max, _y_min, y_ticks = _bar_axes(
            axis_cfg, max(values_flat), min(values_flat),
            nonzero_min_ticks=ct == "horizontal_bar_chart",
        )
        primary_domain = (_y_min, _y_max)
    else:
        y_ticks = list(cfg.get("y_axis_ticks") or [0, 1])
        primary_domain = _plan_domain(cfg, y_ticks)
    unit_pos = str(cfg.get("y_axis_unit_position") or "suffix")
    y_labs = [_fmt_unit(v, unit, unit_pos) for v in y_ticks]
    secondary_y_ticks: list[float] = []
    secondary_y_labs: list[str] = []

    if ct == "combo_chart":
        line_points = _combo_line_data(slide)
        vs = slide.get("visual_spec") or {}
        overlay = vs.get("line_overlay") if isinstance(vs, Mapping) else None
        if line_points:
            series_count += 1
        if line_points and isinstance(overlay, Mapping):
            line_values = [float(p["value"]) for p in line_points]
            if overlay.get("dual_axis", True) is False:
                values_flat.extend(line_values)
                _y_max, _y_min, y_ticks = _bar_axes(cfg, max(values_flat), min(values_flat))
                primary_domain = (_y_min, _y_max)
                y_labs = [_fmt_unit(v, unit, unit_pos) for v in y_ticks]
            else:
                line_min, line_max = combo_overlay_domain(overlay, line_values)
                line_ticks = overlay.get("y_axis_ticks")
                if line_ticks is None:
                    step = (line_max - line_min) / 4
                    line_ticks = [line_min + i * step for i in range(5)]
                secondary_domain = (line_min, line_max)
                overlay_unit = str(overlay.get("y_axis_unit") or "")
                overlay_unit_pos = str(overlay.get("y_axis_unit_position") or "suffix")
                secondary_y_ticks, secondary_y_labs = _bound_tick_view(
                    [float(tick) for tick in line_ticks if isinstance(tick, (int, float))],
                    [_fmt_unit(float(tick), overlay_unit, overlay_unit_pos) for tick in line_ticks if isinstance(tick, (int, float))],
                    *secondary_domain,
                    lambda value: _fmt_unit(value, overlay_unit, overlay_unit_pos),
                )
                if not secondary_y_ticks:
                    secondary_y_ticks, secondary_y_labs = _bound_tick_view(
                        [], [], *secondary_domain,
                        lambda value: _fmt_unit(value, overlay_unit, overlay_unit_pos),
                        include_bounds=True,
                    )

    dl_texts: list[str] = []
    want = bool(cfg.get("point_labels") or cfg.get("show_point_labels"))
    if want and values_flat:
        pos = str(cfg.get("y_axis_unit_position") or "")
        # One label per plotted value (ordinary path).
        for v in values_flat:
            dl_texts.append(_fmt_value_label(v, unit, pos))

    return cats, shorts, series_count, list(y_ticks), y_labs, secondary_y_ticks, secondary_y_labs, dl_texts, primary_domain, secondary_domain


def _plan_domain(cfg: Mapping[str, Any], ticks: Sequence[float]) -> tuple[float | None, float | None]:
    if not ticks:
        return None, None
    try:
        lo = float(cfg["y_axis_min"]) if cfg.get("y_axis_min") is not None else min(ticks)
        hi = float(cfg["y_axis_max"]) if cfg.get("y_axis_max") is not None else max(ticks)
    except (TypeError, ValueError):
        return min(ticks), max(ticks)
    return lo, hi


def _bound_tick_view(
    ticks: Sequence[float], labels: Sequence[str], lo: float | None, hi: float | None,
    format_tick: Callable[[float], str], *, include_bounds: bool = False,
) -> tuple[list[float], list[str]]:
    pairs = [(float(v), str(label)) for v, label in zip(ticks, labels) if (lo is None or v >= lo) and (hi is None or v <= hi)]
    if include_bounds:
        for bound in (lo, hi):
            if bound is not None and not any(math.isclose(value, bound) for value, _label in pairs):
                pairs.append((bound, format_tick(bound)))
    if not pairs and lo is not None and hi is not None:
        pairs = [(lo, format_tick(lo))]
        if not math.isclose(lo, hi):
            pairs.append((hi, format_tick(hi)))
    pairs.sort(key=lambda pair: pair[0])
    return [value for value, _label in pairs], [label for _value, label in pairs]


def compute_auto_plan_for_slide(
    slide: Mapping[str, Any],
    chart_type: str,
    *,
    host_w: float | None = None,
    host_h: float | None = None,
    chart_cfg: Mapping[str, Any] | None = None,
) -> AutoTypoPlan | None:
    """Build an AutoTypoPlan when typography.mode=auto; else None.

    Honours a pre-stashed ``chart_cfg['_auto_typo_plan']`` (sibling sync).
    """
    from .core import _chart_config
    from .typography import resolve_typography

    cfg = dict(chart_cfg) if isinstance(chart_cfg, Mapping) else dict(_chart_config(slide))
    stashed = cfg.get("_auto_typo_plan")
    if isinstance(stashed, AutoTypoPlan):
        return stashed
    if isinstance(stashed, Mapping) and stashed.get("enabled"):
        # Rehydrate minimal plan from diagnostic dict (tests / sync).
        p = AutoTypoPlan(
            enabled=True,
            chart_type=str(stashed.get("chart_type") or chart_type),
            x_tick_font_size=int(stashed.get("x_tick_font_size") or AUTO_X_LO),
            y_tick_font_size=int(stashed.get("y_tick_font_size") or AUTO_Y_LO),
            datalabel_font_size=int(stashed.get("datalabel_font_size") or AUTO_DL_LO),
            y_tick_values=[float(v) for v in stashed.get("y_tick_values", [])],
            y_tick_labels=[str(v) for v in stashed.get("y_tick_labels", [])],
            secondary_y_tick_values=[float(v) for v in stashed.get("secondary_y_tick_values", [])],
            secondary_y_tick_labels=[str(v) for v in stashed.get("secondary_y_tick_labels", [])],
            y_domain_min=stashed.get("y_domain_min"),
            y_domain_max=stashed.get("y_domain_max"),
            secondary_y_domain_min=stashed.get("secondary_y_domain_min"),
            secondary_y_domain_max=stashed.get("secondary_y_domain_max"),
            y_ticks_reduced=bool(stashed.get("y_ticks_reduced")),
            secondary_y_ticks_reduced=bool(stashed.get("secondary_y_ticks_reduced")),
            x_explicit=bool(stashed.get("x_explicit")),
            y_explicit=bool(stashed.get("y_explicit")),
            dl_explicit=bool(stashed.get("dl_explicit")),
            plot_w=float(stashed.get("plot_w") or 0),
            plot_h=float(stashed.get("plot_h") or 0),
            host_w=float(stashed.get("host_w") or 0),
            host_h=float(stashed.get("host_h") or 0),
            datalabels_suppressed=bool(stashed.get("datalabels_suppressed")),
            datalabel_suppress_count=int(stashed.get("datalabel_suppress_count") or 0),
            confidence=str(stashed.get("confidence") or "high"),
        )
        p.x_tick_font_size_set = 1
        p.y_tick_font_size_set = 1
        if not p.datalabels_suppressed:
            p.datalabel_font_size_set = 1
        return p

    typo = resolve_typography(cfg, chart_type=chart_type)
    if not typo.get("auto_mode"):
        return None

    ct = (chart_type or slide.get("layout_type") or "").lower().strip()
    if ct not in AUTO_CHART_TYPES:
        return None

    cats, shorts, series_count, y_vals, y_labs, secondary_y_vals, secondary_y_labs, dl_texts, primary_domain, secondary_domain = _extract_categories_and_shorts(
        slide, ct
    )
    has_legend = cfg.get("show_legend") is not False
    want_dl = bool(cfg.get("point_labels") or cfg.get("show_point_labels"))
    # Ordinary datalabels only on grouped_bar / line (uses_ordinary_datalabels).
    if ct not in ("grouped_bar_chart", "line_chart"):
        want_dl = False
        dl_texts = []

    x_ex = int(typo["x_tick_font_size"]) if typo.get("x_tick_font_size_set") else None
    y_ex = int(typo["y_tick_font_size"]) if typo.get("y_tick_font_size_set") else None
    dl_ex = int(typo["datalabel_font_size"]) if typo.get("datalabel_font_size_set") else None

    # Host size: prefer caller, then chart_cfg stash, else conservative.
    hw = host_w if host_w is not None else cfg.get("_auto_host_w")
    hh = host_h if host_h is not None else cfg.get("_auto_host_h")
    try:
        hw_f = float(hw) if hw is not None else None
    except (TypeError, ValueError):
        hw_f = None
    try:
        hh_f = float(hh) if hh is not None else None
    except (TypeError, ValueError):
        hh_f = None

    from .format import _fmt_unit

    unit = str(cfg.get("y_axis_unit") if cfg.get("y_axis_unit") is not None else ("%" if ct == "line_chart" else ""))
    unit_pos = str(cfg.get("y_axis_unit_position") or "suffix")
    if ct in {"line_chart", "grouped_bar_chart", "stacked_bar_chart", "horizontal_bar_chart", "combo_chart"}:
        line_ticks = (
            axis_config_after_break(cfg, break_overrides_min=True).get("y_axis_ticks")
            if ct == "line_chart"
            else None
        )
        y_vals, y_labs = _bound_tick_view(
            y_vals, y_labs, *primary_domain,
            lambda value: _fmt_unit(value, unit, unit_pos),
            include_bounds=ct != "line_chart" or isinstance(cfg.get("y_axis_break"), Mapping),
        )
    plan = resolve_auto_typography(
        chart_type=ct,
        host_w=hw_f,
        host_h=hh_f,
        categories=cats,
        short_labels=shorts,
        series_count=series_count,
        y_tick_values=y_vals,
        y_tick_labels=y_labs,
        secondary_y_tick_values=secondary_y_vals,
        secondary_y_tick_labels=secondary_y_labs,
        y_domain=primary_domain,
        secondary_y_domain=secondary_domain,
        datalabel_texts=dl_texts,
        has_legend=has_legend,
        want_datalabels=want_dl,
        x_explicit=x_ex,
        y_explicit=y_ex,
        dl_explicit=dl_ex,
        horizontal=(ct == "horizontal_bar_chart"),
        allow_y_tick_reduction=True,
    )
    return plan


def typography_with_auto(
    slide: Mapping[str, Any],
    chart_type: str,
    *,
    chart_cfg: Mapping[str, Any] | None = None,
    host_w: float | None = None,
    host_h: float | None = None,
) -> tuple[dict[str, int], AutoTypoPlan | None]:
    """resolve_typography + optional auto plan overlay (shared Chart.js/SVG entry)."""
    from .core import _chart_config
    from .typography import resolve_typography

    cfg = chart_cfg if isinstance(chart_cfg, Mapping) else _chart_config(slide)
    base = resolve_typography(cfg, chart_type=chart_type)
    plan = compute_auto_plan_for_slide(
        slide, chart_type, host_w=host_w, host_h=host_h, chart_cfg=cfg
    )
    if plan is None:
        return base, None
    return merge_plan_into_typo(base, plan), plan
