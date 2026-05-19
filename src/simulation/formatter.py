from collections import defaultdict
from datetime import datetime
from enum import Enum

import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QVBoxLayout, QWidget,
)

from src.core.preferences import AppPreferences
from src.core.datatypes import EnergyResult, GraphSelection
from src.core.theme import (
    apply_active_chart_palette,
    chart_dialog_stylesheet,
    get_chart_palette,
    matplotlib_toolbar_stylesheet,
    normalize_theme,
)
from src.presentation.ui_assets import app_logo_icon, graph_logo_pixmap


class _ChartPaletteProxy:
    def __getitem__(self, key: str):
        return get_chart_palette()[key]

    def get(self, key: str, default=None):
        return get_chart_palette().get(key, default)


_CHART = _ChartPaletteProxy()


class ChartStyle(str, Enum):
    CURVE = "Curve"
    BARS = "Bars"
    AREA = "Filled area"
    STRIPED = "Striped fill"


class Resolution(str, Enum):
    AUTO = "Auto"
    HOURLY = "Hourly"
    DAILY = "Daily"
    MONTHLY = "Monthly"


def _parse_pvgis_timestamp(ts: str):
    try:
        return datetime.strptime(ts.strip(), "%Y%m%d:%H%M")
    except Exception:
        return None


def _style_axes(ax, *, ylabel: str, title: str, subtitle: str = ""):
    ax.set_facecolor(_CHART["axes"])
    title_text = title if not subtitle else f"{title}\n{subtitle}"
    ax.set_title(
        title_text, fontsize=12, fontweight="bold",
        color=_CHART["text"], pad=12 if subtitle else 10,
    )
    ax.set_ylabel(ylabel, color=_CHART["text"], fontsize=10)
    ax.tick_params(colors=_CHART["muted"], labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(_CHART["grid"])
    ax.grid(True, linestyle="--", linewidth=0.6, color=_CHART["grid"], alpha=0.65)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6, prune="both"))


def _style_figure(fig: Figure):
    fig.patch.set_facecolor(_CHART["figure"])


def _add_stats_box(ax, lines: list[str], loc="upper left"):
    ax.text(
        0.02, 0.98, "\n".join(lines),
        transform=ax.transAxes, va="top", ha="left", fontsize=8.5,
        color=_CHART["text"],
        bbox=dict(
            boxstyle="round,pad=0.45", facecolor=_CHART["axes"],
            edgecolor=_CHART["grid"], alpha=0.92,
        ),
    )


def _apply_smart_time_axis(ax, dates: list, *, max_tick_labels: int = 8):
    """Pick tick density from span — never label every month when crowded."""
    if not dates:
        return
    span_days = (dates[-1] - dates[0]).days
    n = len(dates)

    if span_days <= 45 or n <= 20:
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=max_tick_labels))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    elif span_days <= 400:
        interval = max(1, (n + max_tick_labels - 1) // max_tick_labels)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=interval))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    elif span_days <= 1200:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    for label in ax.get_xticklabels():
        label.set_rotation(28)
        label.set_ha("right")
    ax.set_xlabel("Date", color=_CHART["text"], fontsize=10)


def _apply_monthly_axis(ax, months: list):
    n = len(months)
    if n <= 14:
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        rotation = 35
    elif n <= 36:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        rotation = 35
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        rotation = 0

    for label in ax.get_xticklabels():
        label.set_rotation(rotation)
        label.set_ha("right" if rotation else "center")
    ax.set_xlabel("Period", color=_CHART["text"], fontsize=10)


def _bar_width_days(n_points: int, span_days: float) -> float:
    if n_points <= 1:
        return 20.0
    avg_spacing = max(span_days / n_points, 1.0)
    return max(4.0, min(avg_spacing * 0.75, 28.0))


def _nearest_index(dates: list, x_num: float) -> int:
    if not dates:
        return 0
    x = mdates.num2date(x_num).replace(tzinfo=None)
    return min(range(len(dates)), key=lambda i: abs(dates[i] - x))


class GraphData:
    """Parsed and aggregated series for chart builders."""

    def __init__(self, res: EnergyResult):
        self.res = res
        topo = res.topology_summary or {}
        self.battery_capacity_wh = float(
            res.battery_capacity_wh or topo.get("effective_battery_wh", 0) or 0
        )
        self._hourly: list[tuple[datetime, float, float]] = []
        for row in res.hourly_production:
            dt = _parse_pvgis_timestamp(row["timestamp"])
            if dt is None:
                continue
            self._hourly.append((dt, row["power_w"], row["soc"]))

    @property
    def valid(self) -> bool:
        return len(self._hourly) > 1

    @property
    def span_days(self) -> int:
        if len(self._hourly) < 2:
            return 0
        return (self._hourly[-1][0] - self._hourly[0][0]).days

    def default_style(self, chart: str) -> ChartStyle:
        if chart == "monthly":
            return ChartStyle.BARS
        if self.span_days > 400:
            return ChartStyle.BARS
        if self.span_days > 90:
            return ChartStyle.AREA
        return ChartStyle.CURVE

    def power_display(
        self, style: ChartStyle, resolution: Resolution = Resolution.AUTO,
    ) -> tuple[list, list, str, str]:
        agg = self._resolve_aggregation(style, resolution)
        if agg == "hourly":
            d = [t for t, p, _ in self._hourly]
            v = [p for _, p, _ in self._hourly]
            return d, v, "Power (W)", "Hourly PV output"
        if agg == "daily":
            d, v = self._daily_buckets(power=True)
            return d, v, "Avg power (W)", "Daily average PV power"
        d, v = self.monthly_kwh()
        return d, v, "Energy (kWh)", "Monthly total energy"

    def soc_display(
        self, style: ChartStyle, resolution: Resolution = Resolution.AUTO,
    ) -> tuple[list, list, str, str]:
        agg = self._resolve_aggregation(style, resolution)
        if agg == "hourly":
            d = [t for t, _, s in self._hourly]
            v = [s for _, _, s in self._hourly]
            return d, v, "Stored energy (Wh)", "Hourly battery SOC"
        if agg == "daily":
            d, v = self._daily_buckets(power=False)
            return d, v, "Stored energy (Wh)", "End-of-day battery SOC"
        d, v = self._monthly_soc()
        return d, v, "Stored energy (Wh)", "End-of-month battery SOC"

    def monthly_kwh(self) -> tuple[list, list]:
        buckets: dict = defaultdict(float)
        for dt, power, _ in self._hourly:
            key = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            buckets[key] += power / 1000.0
        months = sorted(buckets.keys())
        return months, [buckets[m] for m in months]

    def _resolve_aggregation(self, style: ChartStyle, resolution: Resolution) -> str:
        if resolution != Resolution.AUTO:
            return resolution.value.lower()
        days = self.span_days
        if style == ChartStyle.BARS:
            if days > 120:
                return "monthly"
            if days > 21:
                return "daily"
            return "hourly"
        if days > 730:
            return "monthly"
        if days > 90:
            return "daily"
        return "hourly"

    def _daily_buckets(self, *, power: bool) -> tuple[list, list]:
        buckets: dict = defaultdict(list)
        soc_end: dict = {}
        for dt, p, s in self._hourly:
            day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            buckets[day].append(p)
            soc_end[day] = s
        days = sorted(buckets.keys())
        if power:
            values = [sum(buckets[d]) / len(buckets[d]) for d in days]
        else:
            values = [soc_end[d] for d in days]
        return days, values

    def _monthly_soc(self) -> tuple[list, list]:
        last: dict = {}
        for dt, _, s in self._hourly:
            key = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last[key] = s
        months = sorted(last.keys())
        return months, [last[m] for m in months]


class GraphGenerator:
    def generate_figures(self, res: EnergyResult, sel: GraphSelection) -> list:
        if not sel.generate_graphs or not res.hourly_production:
            return []
        data = GraphData(res)
        if not data.valid:
            return []
        canvases = []
        if "Power Curve" in sel.selected_types:
            canvases.append(FigureCanvasQTAgg(
                self.build_power_figure(data, data.default_style("power"))
            ))
        if "Battery SOC" in sel.selected_types:
            canvases.append(FigureCanvasQTAgg(
                self.build_soc_figure(data, data.default_style("soc"))
            ))
        if "Monthly Summary" in sel.selected_types:
            canvases.append(FigureCanvasQTAgg(
                self.build_monthly_figure(data)
            ))
        return canvases

    def build_power_figure(
        self, data: GraphData, style: ChartStyle,
        resolution: Resolution = Resolution.AUTO,
    ) -> Figure:
        dates, values, ylabel, subtitle = data.power_display(style, resolution)
        fig = Figure(figsize=(9, 4.5), dpi=100)
        _style_figure(fig)
        ax = fig.add_subplot(111)
        _style_axes(ax, ylabel=ylabel, title="PV Power Generation", subtitle=subtitle)

        color = _CHART["orange"]
        self._draw_series(ax, dates, values, style, color, "PV output")

        if values:
            peak = max(values)
            peak_i = values.index(peak)
            ax.scatter(
                [dates[peak_i]], [peak], color=_CHART["red"], s=40, zorder=5,
                label=f"Peak {peak:,.0f}",
            )
            mean = sum(values) / len(values)
            ax.axhline(
                mean, color=_CHART["lavender"], linestyle=":", linewidth=1.0,
                label=f"Mean {mean:,.0f}",
            )

        _apply_smart_time_axis(ax, dates)
        ax.legend(loc="upper right", fontsize=8, framealpha=0.9,
                  facecolor=_CHART["axes"], edgecolor=_CHART["grid"],
                  labelcolor=_CHART["text"])
        _add_stats_box(ax, [
            f"Total energy : {data.res.total_energy_kwh:,.1f} kWh",
            f"Peak power   : {data.res.peak_power_w:,.0f} W",
            f"Capacity factor : {data.res.capacity_factor:.1f} %",
        ])
        fig.tight_layout()
        self._bind_hover(fig, dates, values, _format_power_tooltip)
        return fig

    def build_soc_figure(
        self, data: GraphData, style: ChartStyle,
        resolution: Resolution = Resolution.AUTO,
    ) -> Figure:
        dates, values_wh, _, subtitle = data.soc_display(style, resolution)
        cap_wh = data.battery_capacity_wh
        fig = Figure(figsize=(9, 4.5), dpi=100)
        _style_figure(fig)
        ax = fig.add_subplot(111)

        if cap_wh <= 0:
            _style_axes(
                ax, ylabel="SOC (%)",
                title="Battery State of Charge",
                subtitle="No battery linked to PV in the wiring layout",
            )
            ax.text(
                0.5, 0.5,
                "Wire at least one battery to your PV strings\n"
                "(same connected cluster) to model storage.",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=11, color=_CHART["muted"],
            )
            ax.set_ylim(0, 100)
            ax.set_xlim(0, 1)
            fig.tight_layout()
            return fig

        values = [
            min(100.0, max(0.0, v / cap_wh * 100.0)) for v in values_wh
        ]
        ylabel = "State of charge (%)"
        subtitle = f"{subtitle} · {cap_wh:,.0f} Wh bank"
        _style_axes(ax, ylabel=ylabel, title="Battery State of Charge", subtitle=subtitle)

        self._draw_series(ax, dates, values, style, _CHART["green"], "SOC")
        ax.axhline(
            100.0, color=_CHART["blue"], linestyle="--", linewidth=1.0,
            label="100% (full)",
        )
        ax.set_ylim(0, 100)

        _apply_smart_time_axis(ax, dates)
        ax.legend(loc="upper right", fontsize=8, framealpha=0.9,
                  facecolor=_CHART["axes"], edgecolor=_CHART["grid"],
                  labelcolor=_CHART["text"])
        mean_pct = sum(values) / len(values) if values else 0.0
        peak_wh = max(values_wh) if values_wh else 0.0
        stats = [
            f"Bank size  : {cap_wh:,.0f} Wh",
            f"Mean SOC   : {mean_pct:.1f} %",
            f"Peak SOC   : {max(values):.1f} %" if values else "Peak SOC   : —",
            f"End SOC    : {values[-1]:.1f} %" if values else "End SOC    : —",
        ]
        if peak_wh <= 0 and data.res.total_energy_kwh < data.res.total_load_kwh:
            stats.append("Note: site load exceeds PV — battery stays empty")
        _add_stats_box(ax, stats)
        fig.tight_layout()

        def _fmt(dt, pct):
            wh = pct / 100.0 * cap_wh
            return f"{dt.strftime('%d %b %Y')}  —  {pct:.1f} % ({wh:,.0f} Wh)"

        self._bind_hover(fig, dates, values, _fmt)
        return fig

    def build_monthly_figure(self, data: GraphData) -> Figure:
        months, kwh = data.monthly_kwh()
        fig = Figure(figsize=(9, 4.5), dpi=100)
        _style_figure(fig)
        ax = fig.add_subplot(111)
        _style_axes(
            ax, ylabel="Energy (kWh)",
            title="Monthly Energy Production",
            subtitle="Total kWh per calendar month",
        )

        if not months:
            ax.text(
                0.5, 0.5, "No monthly data available",
                ha="center", va="center", transform=ax.transAxes,
                color=_CHART["muted"], fontsize=11,
            )
            fig.tight_layout()
            return fig

        span = (months[-1] - months[0]).days if len(months) > 1 else 30
        width = _bar_width_days(len(months), span)
        ax.bar(
            months, kwh, width=width,
            color=_CHART["blue"], edgecolor=_CHART["lavender"],
            linewidth=0.6, alpha=0.9, label="Monthly total",
        )

        if len(months) <= 14:
            for m, val in zip(months, kwh):
                ax.text(
                    m, val, f"{val:,.0f}", ha="center", va="bottom",
                    fontsize=7.5, color=_CHART["text"],
                )

        _apply_monthly_axis(ax, months)
        total = sum(kwh)
        best_i = kwh.index(max(kwh))
        _add_stats_box(ax, [
            f"Months : {len(months)}",
            f"Total  : {total:,.1f} kWh",
            f"Best   : {kwh[best_i]:,.1f} kWh ({months[best_i].strftime('%b %Y')})",
        ], loc="upper right")
        ax.legend(loc="upper left", fontsize=8, framealpha=0.9,
                  facecolor=_CHART["axes"], edgecolor=_CHART["grid"],
                  labelcolor=_CHART["text"])
        fig.tight_layout()
        self._bind_hover(fig, months, kwh, _format_monthly_tooltip)
        return fig

    def _draw_series(
        self, ax, dates: list, values: list, style: ChartStyle,
        color: str, label: str,
    ):
        if not dates:
            return

        if style == ChartStyle.BARS:
            span = (dates[-1] - dates[0]).days if len(dates) > 1 else 1
            width = _bar_width_days(len(dates), span)
            ax.bar(dates, values, width=width, color=color,
                   edgecolor=_CHART["lavender"], linewidth=0.5,
                   alpha=0.9, label=label)
            return

        ax.plot(dates, values, color=color, linewidth=1.4, label=label, zorder=3)

        if style == ChartStyle.AREA:
            ax.fill_between(dates, values, alpha=0.25, color=color, zorder=2)
        elif style == ChartStyle.STRIPED:
            ax.fill_between(
                dates, values, alpha=0.35, color=color, zorder=2,
                hatch="///", edgecolor=_CHART["lavender"], linewidth=0.4,
            )

    @staticmethod
    def _bind_hover(fig, dates, values, fmt_fn):
        fig._hover_dates = dates
        fig._hover_values = values
        fig._hover_fmt = fmt_fn
        fig._hover_annotation = None

    @staticmethod
    def hover_message(fig, event) -> str:
        if event.inaxes is None or not getattr(fig, "_hover_dates", None):
            return ""
        dates = fig._hover_dates
        values = fig._hover_values
        if event.xdata is None:
            return ""
        idx = _nearest_index(dates, event.xdata)
        return fig._hover_fmt(dates[idx], values[idx])


def _format_power_tooltip(dt: datetime, value: float) -> str:
    return f"{dt.strftime('%d %b %Y')}  —  {value:,.1f} W"


def _format_soc_tooltip(dt: datetime, value: float) -> str:
    return f"{dt.strftime('%d %b %Y')}  —  {value:,.1f} Wh stored"


def _format_monthly_tooltip(dt: datetime, value: float) -> str:
    return f"{dt.strftime('%B %Y')}  —  {value:,.1f} kWh"


class _ChartToolbar(NavigationToolbar2QT):
    """Show nearest data value instead of raw mouse coordinates."""

    def __init__(self, canvas, parent, fig):
        super().__init__(canvas, parent)
        self._fig = fig

    def set_message(self, s):
        pass

    def mouse_move(self, event):
        super().mouse_move(event)
        msg = GraphGenerator.hover_message(self._fig, event)
        if not hasattr(self, "message"):
            return
        if msg:
            self.message.emit(msg)
        elif event.inaxes is None:
            self.message.emit("")


class GraphDialog(QDialog):
    """Post-simulation chart viewer with style controls and data tooltips."""

    _TAB_SPECS = (
        ("Power Curve", "PV Output", "power", "build_power_figure"),
        ("Battery SOC", "Battery SOC", "soc", "build_soc_figure"),
        ("Monthly Summary", "Monthly Energy", "monthly", "build_monthly_figure"),
    )

    def __init__(self, res: EnergyResult, sel: GraphSelection, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Simulation Charts")
        self.setMinimumSize(980, 620)
        self.resize(1040, 680)

        self._generator = GraphGenerator()
        self._data = GraphData(res)
        self._tab_state: list[dict] = []
        prefs = AppPreferences.load()
        self._default_style = prefs.chart_default_style
        theme_key = normalize_theme(prefs.theme)
        apply_active_chart_palette(theme_key)
        palette = get_chart_palette()
        self.setWindowIcon(app_logo_icon())
        self.setStyleSheet(chart_dialog_stylesheet(theme_key))

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        logo_pm = graph_logo_pixmap()
        if not logo_pm.isNull():
            logo_wrap = QWidget()
            logo_wrap.setObjectName("LogoContainer")
            logo_lay = QHBoxLayout(logo_wrap)
            logo_lay.setContentsMargins(0, 0, 8, 0)
            logo_lbl = QLabel()
            logo_lbl.setObjectName("AppLogoLabel")
            logo_lbl.setPixmap(logo_pm)
            logo_lbl.setFixedSize(logo_pm.size())
            logo_lay.addWidget(logo_lbl, 0, Qt.AlignLeft)
            header_row.addWidget(logo_wrap, 0, Qt.AlignLeft)
        header = QLabel(
            f"<b>Solar Farm Digital Twin</b> — "
            f"{res.total_energy_kwh:,.1f} kWh PV · "
            f"load {res.total_load_kwh:,.1f} kWh · "
            f"peak {res.peak_power_w:,.0f} W · "
            f"CF {res.capacity_factor:.1f}%"
        )
        header.setObjectName("ChartHeaderLabel")
        header.setTextFormat(Qt.RichText)
        header_row.addWidget(header, stretch=1)
        root.addLayout(header_row)

        hint = QLabel(
            "Hover over the chart to see the value at that date. "
            "Use <b>Display</b> to switch curve, bars, or filled styles."
        )
        hint.setObjectName("ChartHintLabel")
        hint.setTextFormat(Qt.RichText)
        root.addWidget(hint)

        self._tabs = QTabWidget()
        root.addWidget(self._tabs, stretch=1)

        if not self._data.valid:
            empty = QLabel("Not enough hourly data to render charts.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setObjectName("ChartHintLabel")
            self._tabs.addTab(empty, "No data")
        else:
            selected = set(sel.selected_types) if sel else set()
            for key, tab_label, kind, builder_name in self._TAB_SPECS:
                if selected and key not in selected:
                    continue
                self._add_chart_tab(tab_label, kind, builder_name)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton("Close")
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        root.addLayout(btn_row)

    def _add_chart_tab(self, label: str, kind: str, builder_name: str):
        container = QWidget()
        container.setObjectName("ChartTabPage")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        controls_bar = QWidget()
        controls_bar.setObjectName("ChartControlsBar")
        controls = QHBoxLayout(controls_bar)
        controls.setContentsMargins(6, 6, 6, 6)
        controls.addWidget(QLabel("Display:"))
        style_combo = QComboBox()
        res_combo = QComboBox()
        if kind == "monthly":
            style_combo.addItem(ChartStyle.BARS.value)
            style_combo.setEnabled(False)
            res_combo.addItem(Resolution.MONTHLY.value)
            res_combo.setEnabled(False)
        elif kind == "soc":
            for st in ChartStyle:
                style_combo.addItem(st.value)
            for res in Resolution:
                res_combo.addItem(res.value)
            style_combo.setCurrentText(ChartStyle.CURVE.value)
            res_combo.setCurrentText(Resolution.HOURLY.value)
        else:
            for st in ChartStyle:
                style_combo.addItem(st.value)
            for res in Resolution:
                res_combo.addItem(res.value)
            try:
                style_combo.setCurrentText(self._default_style)
            except Exception:
                style_combo.setCurrentText(self._data.default_style(kind).value)
        controls.addWidget(style_combo)
        controls.addWidget(QLabel("Resolution:"))
        controls.addWidget(res_combo)
        btn_export = QPushButton("Export PNG…")
        controls.addWidget(btn_export)
        controls.addStretch()
        layout.addWidget(controls_bar)

        canvas_holder = QWidget()
        canvas_holder.setObjectName("ChartCanvasHolder")
        canvas_layout = QVBoxLayout(canvas_holder)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(canvas_holder, stretch=1)

        state = {
            "kind": kind,
            "builder_name": builder_name,
            "style_combo": style_combo,
            "res_combo": res_combo,
            "canvas_holder": canvas_holder,
            "canvas_layout": canvas_layout,
            "canvas": None,
            "toolbar": None,
            "fig": None,
        }
        self._tab_state.append(state)
        btn_export.clicked.connect(lambda checked=False, s=state: self._export_png(s))

        if kind != "monthly":
            style_combo.currentTextChanged.connect(
                lambda _text, s=state: self._redraw_tab(s)
            )
            res_combo.currentTextChanged.connect(
                lambda _text, s=state: self._redraw_tab(s)
            )

        self._redraw_tab(state)
        self._tabs.addTab(container, label)

    def _redraw_tab(self, state: dict):
        prefs = AppPreferences.load()
        theme_key = normalize_theme(prefs.theme)
        apply_active_chart_palette(theme_key)
        layout = state["canvas_layout"]
        if state["canvas"] is not None:
            layout.removeWidget(state["toolbar"])
            layout.removeWidget(state["canvas"])
            state["toolbar"].deleteLater()
            state["canvas"].deleteLater()

        kind = state["kind"]
        resolution = Resolution(state["res_combo"].currentText())
        if kind == "monthly":
            fig = self._generator.build_monthly_figure(self._data)
        else:
            style = ChartStyle(state["style_combo"].currentText())
            builder = getattr(self._generator, state["builder_name"])
            fig = builder(self._data, style, resolution)

        state["fig"] = fig
        canvas = FigureCanvasQTAgg(fig)
        toolbar = _ChartToolbar(canvas, state["canvas_holder"], fig)
        toolbar.setStyleSheet(matplotlib_toolbar_stylesheet(theme_key))
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        state["canvas"] = canvas
        state["toolbar"] = toolbar

    def _export_png(self, state: dict):
        fig = state.get("fig")
        if fig is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Chart", "", "PNG Image (*.png);;All Files (*)"
        )
        if path:
            if not path.lower().endswith(".png"):
                path += ".png"
            fig.savefig(path, dpi=150, facecolor=fig.get_facecolor())


class ResultFormatter:
    @staticmethod
    def format(res: EnergyResult) -> str:
        topo = res.topology_summary or {}
        self_pct = 0.0
        if res.total_load_kwh > 0:
            self_pct = (res.total_self_consumed_kwh / res.total_load_kwh) * 100.0
        lines = [
            "=========================================",
            "  SOLAR FARM DIGITAL TWIN — RESULTS",
            "=========================================",
            "SYSTEM (from wiring layout):",
            f"  Active PV capacity     : {res.effective_pv_w:,.0f} W",
            f"  Panels in service      : {topo.get('active_panel_count', 0)} / "
            f"{topo.get('total_panel_count', 0)}",
            f"  Wired PV+battery groups: {topo.get('wired_cluster_count', 0)}",
            "",
            "ENERGY BALANCE:",
            f"  PV generated           : {res.total_energy_kwh:,.2f} kWh",
            f"  Site load (consumption): {res.total_load_kwh:,.2f} kWh",
            f"  Self-consumed on site  : {res.total_self_consumed_kwh:,.2f} kWh "
            f"({self_pct:.1f}% of load)",
            f"  Supplied from battery  : {res.energy_from_battery_kwh:,.2f} kWh",
            f"  Curtailed (full batt.) : {res.curtailed_kwh:,.2f} kWh",
            f"  Unserved load          : {res.unserved_kwh:,.2f} kWh",
            "",
            "PERFORMANCE:",
            f"  Peak power             : {res.peak_power_w:,.0f} W",
            f"  Capacity factor        : {res.capacity_factor:.2f} %",
            "=========================================",
        ]
        if topo.get("orphan_panels", 0) > 0:
            lines.insert(
                10,
                f"  Unwired panels (0 output): {topo['orphan_panels']}",
            )
        if topo.get("idle_wired_panels", 0) > 0:
            lines.insert(
                11,
                f"  Panels not linked to battery: {topo['idle_wired_panels']}",
            )
        return "\n".join(lines) + "\n"
