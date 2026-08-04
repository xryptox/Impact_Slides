"""Chart + icon_grid paint — in-repo painters only.

Package facade: family modules hold the implementations; this module
re-exports every name so ``from impact_slides.renderer_v2.charts import X``
and ``charts.X`` keep working (same object identity for mock.patch).
"""
from __future__ import annotations

from .format import _BOARDROOM_SERIES, _NAVY, _NAVY_SOFT, _WHITE, _series_color, _BAR_SERIES_COLORS, _series_colors, _fmt_unit, _bar_num, _fmt_value_label, _fmt_bar, _fmt_chart_num, _nice_max, _nice_step
from .callouts import _align_overlay_to_labels, _CALLOUT_TYPES, _value_anchor_pct, _merge_callout_bands, _elbow_stem_html, _build_callout_overlays, _build_side_callout_html, _build_side_callout_svg, _resolve_side_callout, side_callout_active
from .geometry import _CHART_GEOMETRY, chart_geometry, chart_column_interval
from .core import is_chart_layout, _icon_svg, _steps, _chart_config, build_icon_grid_html, _fallback_icon_grid, _svg_fallback_for_layout, build_chart_html
from .bars import _bar_matrix, _bar_axes, _vbar_pad_t, _bar_group_brackets, _vbar_frame, _build_grouped_bar_svg, _build_stacked_bar_svg, _build_hbar_svg
from .lines import _line_data, _combo_bar_data, _combo_line_data, _build_line_chart_svg, _build_combo_chart_svg
from .matrix import _fallback_matrix_chart, _build_heatmap_html, _build_waterfall_svg
from .chartjs import _datalabels_cfg, _next_chart_id, _chartjs_common_options, _apply_bar_density_knobs, _chartjs_bar_config, _chartjs_hbar_config, _chartjs_line_config, _chartjs_combo_config, _build_chartjs_html

__all__ = [
    '_BAR_SERIES_COLORS',
    '_BOARDROOM_SERIES',
    '_CALLOUT_TYPES',
    '_CHART_GEOMETRY',
    '_NAVY',
    '_NAVY_SOFT',
    '_WHITE',
    '_align_overlay_to_labels',
    '_apply_bar_density_knobs',
    '_bar_axes',
    '_bar_group_brackets',
    '_bar_matrix',
    '_bar_num',
    '_build_callout_overlays',
    '_build_side_callout_html',
    '_build_side_callout_svg',
    '_build_chartjs_html',
    '_build_combo_chart_svg',
    '_build_grouped_bar_svg',
    '_build_hbar_svg',
    '_build_heatmap_html',
    '_build_line_chart_svg',
    '_build_stacked_bar_svg',
    '_build_waterfall_svg',
    '_chart_config',
    '_chartjs_bar_config',
    '_chartjs_combo_config',
    '_chartjs_common_options',
    '_chartjs_hbar_config',
    '_chartjs_line_config',
    '_combo_bar_data',
    '_combo_line_data',
    '_datalabels_cfg',
    '_elbow_stem_html',
    '_fallback_icon_grid',
    '_fallback_matrix_chart',
    '_fmt_bar',
    '_fmt_chart_num',
    '_fmt_unit',
    '_fmt_value_label',
    '_icon_svg',
    '_line_data',
    '_merge_callout_bands',
    '_resolve_side_callout',
    '_next_chart_id',
    '_nice_max',
    '_nice_step',
    '_series_color',
    '_series_colors',
    '_steps',
    '_svg_fallback_for_layout',
    '_value_anchor_pct',
    '_vbar_frame',
    '_vbar_pad_t',
    'build_chart_html',
    'build_icon_grid_html',
    'chart_column_interval',
    'chart_geometry',
    'is_chart_layout',
    'side_callout_active',
]
