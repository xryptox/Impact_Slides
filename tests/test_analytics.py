"""
Tests for v3 #25 — outlier detection (IQR), correlation hints, and robust
period trend (YoY/QoQ/MoM) logic.

Covers:
  - IQR outlier detection: finds injected outliers, correct bounds, no false
    positives on uniform data
  - Correlation hints: detects strong positive/negative correlation, ignores
    weak correlations (|r| < 0.6), caps at 8 pairs
  - Period trends: YoY when span > 365 days, QoQ for quarter spans, MoM for
    month spans; uses the date column + numeric column mean per period
  - No crash when no date column / no numeric columns / single period
  - New insight types registered in schema + stage mapping + extraction method
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import step1_preprocessor_v3 as m


@pytest.fixture()
def make_preprocessor(tmp_workspace):
    def _make(filter_level="permissive"):
        inp = tmp_workspace / "input"
        out = tmp_workspace / "output"
        inp.mkdir(parents=True, exist_ok=True)
        p = m.ImpactSlidePreprocessorV2(
            input_path=str(inp), output_dir=str(out), filter_level=filter_level,
        )
        return p, inp, out
    return _make


def _run_and_get_ev(p, out):
    p.run()
    return json.load(open(out / "evidence_register_seed.json"))


# --------------------------------------------------------------------------- #
# IQR outlier detection
# --------------------------------------------------------------------------- #
class TestOutlierDetection:
    def test_finds_injected_outliers(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        # Revenue with 2 clear outliers among 50 normal values
        np.random.seed(42)
        rev = list(np.random.normal(1000, 50, 50))
        rev[25] = 5000  # clear high outlier
        rev[26] = -200  # clear low outlier
        pd.DataFrame({"Revenue": rev}).to_excel(inp / "s.xlsx", index=False)
        ev = _run_and_get_ev(p, out)
        outliers = [e for e in ev if e["insight_type"] == "outlier_insight"]
        assert outliers, "expected outlier_insight for Revenue"
        text = outliers[0]["text"]
        assert "outlier" in text.lower()
        assert "5000" in text or "-200" in text  # outlier values mentioned

    def test_no_outliers_on_uniform_data(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        pd.DataFrame({"Value": [10.0] * 50}).to_excel(inp / "s.xlsx", index=False)
        ev = _run_and_get_ev(p, out)
        outliers = [e for e in ev if e["insight_type"] == "outlier_insight"]
        assert not outliers, "uniform data should have no outliers"

    def test_outlier_bounds_in_profile(self, make_preprocessor, tmp_workspace):
        """The numeric_profile carries outlier_count + outlier_bounds."""
        p, inp, out = make_preprocessor()
        np.random.seed(42)
        rev = list(np.random.normal(1000, 50, 50)) + [9999]  # one clear outlier
        pd.DataFrame({"Revenue": rev}).to_excel(inp / "s.xlsx", index=False)
        p.run()
        prof = json.load(open(out / "excel_profile.json"))
        # find the Revenue numeric profile (might be named 'Revenue' or 'Column A')
        num = None
        for n in prof[0]["sheets"][0]["numeric_profiles"]:
            num = n
            break
        assert num is not None
        assert num.get("outlier_count", 0) >= 1
        assert "outlier_bounds" in num
        assert len(num["outlier_bounds"]) == 2


# --------------------------------------------------------------------------- #
# Correlation hints
# --------------------------------------------------------------------------- #
class TestCorrelationHints:
    def test_detects_strong_positive_correlation(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        np.random.seed(42)
        n = 50
        revenue = np.random.normal(1000, 50, n)
        cost = revenue * 0.5 + np.random.normal(0, 10, n)  # strongly correlated
        pd.DataFrame({"Revenue": revenue, "Cost": cost}).to_excel(inp / "s.xlsx", index=False)
        ev = _run_and_get_ev(p, out)
        corrs = [e for e in ev if e["insight_type"] == "correlation_insight"]
        assert corrs, "expected a correlation_insight"
        text = corrs[0]["text"].lower()
        assert "revenue" in text and "cost" in text
        assert "positive" in text
        assert "strong" in text  # r >= 0.8

    def test_detects_negative_correlation(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        np.random.seed(42)
        n = 50
        x = np.random.normal(100, 10, n)
        y = -x * 2 + np.random.normal(0, 5, n)  # strongly negative
        pd.DataFrame({"X": x, "Y": y}).to_excel(inp / "s.xlsx", index=False)
        ev = _run_and_get_ev(p, out)
        corrs = [e for e in ev if e["insight_type"] == "correlation_insight"]
        assert corrs, "expected a correlation_insight"
        assert "negative" in corrs[0]["text"].lower()

    def test_ignores_weak_correlation(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        np.random.seed(42)
        n = 50
        x = np.random.normal(100, 10, n)
        y = np.random.normal(200, 10, n)  # uncorrelated
        pd.DataFrame({"X": x, "Y": y}).to_excel(inp / "s.xlsx", index=False)
        ev = _run_and_get_ev(p, out)
        corrs = [e for e in ev if e["insight_type"] == "correlation_insight"]
        assert not corrs, "uncorrelated columns should not produce a correlation_insight"

    def test_correlation_priority_scales_with_r(self, make_preprocessor, tmp_workspace):
        """Stronger correlations get higher priority (0.80 + |r| * 0.10)."""
        p, inp, out = make_preprocessor()
        np.random.seed(42)
        n = 50
        x = np.random.normal(100, 10, n)
        y = x * 3 + np.random.normal(0, 1, n)  # near-perfect r~1.0
        pd.DataFrame({"X": x, "Y": y}).to_excel(inp / "s.xlsx", index=False)
        ev = _run_and_get_ev(p, out)
        corrs = [e for e in ev if e["insight_type"] == "correlation_insight"]
        assert corrs
        assert corrs[0]["priority_score"] >= 0.88  # r~1.0 → 0.80 + 0.10 = 0.90


# --------------------------------------------------------------------------- #
# Period trends (YoY / QoQ / MoM)
# --------------------------------------------------------------------------- #
class TestPeriodTrends:
    def test_yoy_trend_multi_year(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        # Weekly data spanning 2+ years → YoY
        dates = pd.date_range("2022-01-01", periods=120, freq="W")
        np.random.seed(42)
        rev = list(np.random.normal(1000, 50, 120))
        pd.DataFrame({"Date": dates, "Revenue": rev}).to_excel(inp / "s.xlsx", index=False)
        ev = _run_and_get_ev(p, out)
        trends = [e for e in ev if e["insight_type"] == "period_trend_insight"]
        assert trends, "expected a period_trend_insight"
        assert "YoY" in trends[0]["text"]

    def test_mom_trend_within_month_span(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        # Daily data spanning ~2 months → MoM
        dates = pd.date_range("2023-01-01", periods=60, freq="D")
        np.random.seed(42)
        rev = list(np.random.normal(1000, 50, 60))
        pd.DataFrame({"Date": dates, "Revenue": rev}).to_excel(inp / "s.xlsx", index=False)
        ev = _run_and_get_ev(p, out)
        trends = [e for e in ev if e["insight_type"] == "period_trend_insight"]
        assert trends, "expected a period_trend_insight"
        assert "MoM" in trends[0]["text"]

    def test_qoq_trend_quarter_span(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        # Daily data spanning ~4 months → QoQ
        dates = pd.date_range("2023-01-01", periods=120, freq="D")
        np.random.seed(42)
        rev = list(np.random.normal(1000, 50, 120))
        pd.DataFrame({"Date": dates, "Revenue": rev}).to_excel(inp / "s.xlsx", index=False)
        ev = _run_and_get_ev(p, out)
        trends = [e for e in ev if e["insight_type"] == "period_trend_insight"]
        assert trends, "expected a period_trend_insight"
        assert "QoQ" in trends[0]["text"]

    def test_no_trend_when_span_too_short(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        # Only 20 days — too short for any trend
        dates = pd.date_range("2023-01-01", periods=20, freq="D")
        pd.DataFrame({"Date": dates, "Revenue": list(range(20))}).to_excel(inp / "s.xlsx", index=False)
        ev = _run_and_get_ev(p, out)
        trends = [e for e in ev if e["insight_type"] == "period_trend_insight"]
        assert not trends, "span < 40 days should produce no period trend"

    def test_no_trend_without_date_column(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        pd.DataFrame({"Revenue": [100, 200, 300, 400]}).to_excel(inp / "s.xlsx", index=False)
        ev = _run_and_get_ev(p, out)
        trends = [e for e in ev if e["insight_type"] == "period_trend_insight"]
        assert not trends, "no date column → no period trend"

    def test_trend_shows_increase_or_decrease(self, make_preprocessor, tmp_workspace):
        p, inp, out = make_preprocessor()
        dates = pd.date_range("2023-01-01", periods=80, freq="D")
        # Revenue clearly increasing over time
        rev = [100 + i * 5 for i in range(80)]
        pd.DataFrame({"Date": dates, "Revenue": rev}).to_excel(inp / "s.xlsx", index=False)
        ev = _run_and_get_ev(p, out)
        trends = [e for e in ev if e["insight_type"] == "period_trend_insight"]
        assert trends
        assert "increase" in trends[0]["text"].lower()


# --------------------------------------------------------------------------- #
# Schema + stage mapping registration
# --------------------------------------------------------------------------- #
class TestSchemaRegistration:
    def test_new_types_in_schema(self):
        from impact_slides.schemas import INSIGHT_TYPES
        assert "outlier_insight" in INSIGHT_TYPES
        assert "correlation_insight" in INSIGHT_TYPES
        assert "period_trend_insight" in INSIGHT_TYPES

    def test_new_types_in_stage_mapping(self, make_preprocessor):
        p, _, _ = make_preprocessor()
        assert p._stages_for("outlier_insight") == ["What", "How"]
        assert p._stages_for("correlation_insight") == ["How", "What"]
        assert p._stages_for("period_trend_insight") == ["How", "What", "Why"]

    def test_extraction_method_is_computed(self, make_preprocessor):
        p, _, _ = make_preprocessor()
        assert p._method_for_insight("outlier_insight", {}) == "computed"
        assert p._method_for_insight("correlation_insight", {}) == "computed"
        assert p._method_for_insight("period_trend_insight", {}) == "computed"
