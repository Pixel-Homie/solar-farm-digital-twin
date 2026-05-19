import math
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QMessageBox, QSpinBox, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QSizePolicy, QComboBox, QGroupBox,
    QFormLayout, QApplication, QFrame, QTabWidget, QKeySequenceEdit,
    QDoubleSpinBox, QScrollArea, QWidget, QGridLayout,
)
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QPixmap, QPen, QColor, QBrush, QFont, QKeySequence
from src.core.datatypes import SimulationParams, GraphSelection, PvgisYearBounds
from src.core.theme import THEMES, normalize_theme, chart_dialog_stylesheet, apply_active_chart_palette
from src.presentation.ui_assets import app_logo_icon
from src.core.preferences import (
    AppPreferences, SHORTCUT_DEFINITIONS, CHART_STYLES, EXPORT_FORMATS,
)

TILE_SIZE = 256


# ─────────────────────────────────────────────────────────────────────────────
# Web Mercator helpers
# ─────────────────────────────────────────────────────────────────────────────
def _ll_to_tile(lat, lon, zoom):
    n  = 2 ** zoom
    tx = int((lon + 180) / 360 * n)
    lr = math.radians(max(-85.05, min(85.05, lat)))
    ty = int((1 - math.log(math.tan(lr) + 1 / math.cos(lr)) / math.pi) / 2 * n)
    return tx, ty


def _scene_to_ll(sx, sy, origin_tx, origin_ty, zoom):
    n   = 2 ** zoom
    gpx = origin_tx * TILE_SIZE + sx
    gpy = origin_ty * TILE_SIZE + sy
    lon = gpx / (n * TILE_SIZE) * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * gpy / (n * TILE_SIZE)))))
    return round(lat, 5), round(lon, 5)


def _ll_to_scene(lat, lon, origin_tx, origin_ty, zoom):
    n   = 2 ** zoom
    lr  = math.radians(max(-85.05, min(85.05, lat)))
    gpx = (lon + 180) / 360 * n * TILE_SIZE
    gpy = (1 - math.log(math.tan(lr) + 1 / math.cos(lr)) / math.pi) / 2 * n * TILE_SIZE
    return gpx - origin_tx * TILE_SIZE, gpy - origin_ty * TILE_SIZE


# ─────────────────────────────────────────────────────────────────────────────
# Tile Map Widget
# ─────────────────────────────────────────────────────────────────────────────
class TileMapWidget(QGraphicsView):
    """
    Interactive OpenStreetMap tile map — no WebEngine required.
    Controls:
      Left-click  → place marker
      Right-drag  → pan
      Scroll      → zoom in / out
    """
    coord_changed = pyqtSignal(float, float)

    TILES_W  = 7
    TILES_H  = 6
    ZOOM_MIN = 3
    ZOOM_MAX = 14

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setMinimumSize(620, 430)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.NoDrag)

        self._nam = QNetworkAccessManager(self)
        self._nam.finished.connect(self._on_tile_loaded)
        self._pending: dict = {}

        self._zoom       = 5
        self._center_lat = 28.0
        self._center_lon = 3.0
        self._origin_tx  = 0
        self._origin_ty  = 0

        self._sel_lat    = None
        self._sel_lon    = None
        self._marker     = None
        self._marker_lbl = None
        self._pan_last   = None

        self._load_tiles()

    # ── tile management ───────────────────────────────────────────────────────
    def _load_tiles(self):
        cx, cy = _ll_to_tile(self._center_lat, self._center_lon, self._zoom)
        self._origin_tx = cx - self.TILES_W // 2
        self._origin_ty = cy - self.TILES_H // 2

        for reply in list(self._pending):
            reply.abort()
        self._pending.clear()

        self._scene.clear()
        self._marker     = None
        self._marker_lbl = None

        w = self.TILES_W * TILE_SIZE
        h = self.TILES_H * TILE_SIZE
        self._scene.setSceneRect(0, 0, w, h)
        self._scene.addRect(0, 0, w, h, QPen(Qt.NoPen), QBrush(QColor("#ede8e0")))

        n = 2 ** self._zoom
        for dy in range(self.TILES_H):
            for dx in range(self.TILES_W):
                tx = self._origin_tx + dx
                ty = self._origin_ty + dy
                if not (0 <= tx < n and 0 <= ty < n):
                    continue
                url = f"https://tile.openstreetmap.org/{self._zoom}/{tx}/{ty}.png"
                req = QNetworkRequest(QUrl(url))
                req.setRawHeader(b"User-Agent", b"SolarFarmDigitalTwin/1.0")
                reply = self._nam.get(req)
                self._pending[reply] = (dx, dy)

        if self._sel_lat is not None:
            self._draw_marker(self._sel_lat, self._sel_lon)

    def _on_tile_loaded(self, reply):
        if reply not in self._pending:
            reply.deleteLater()
            return
        dx, dy = self._pending.pop(reply)
        data   = reply.readAll()
        reply.deleteLater()

        px = QPixmap()
        if not px.loadFromData(data):
            return

        item = QGraphicsPixmapItem(px)
        item.setPos(dx * TILE_SIZE, dy * TILE_SIZE)
        item.setZValue(0)
        self._scene.addItem(item)

        if self._marker:
            self._marker.setZValue(10)
        if self._marker_lbl:
            self._marker_lbl.setZValue(11)

    # ── interaction ───────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            sp  = self.mapToScene(event.pos())
            lat, lon = _scene_to_ll(
                sp.x(), sp.y(), self._origin_tx, self._origin_ty, self._zoom
            )
            self._sel_lat = lat
            self._sel_lon = lon
            self._draw_marker(lat, lon)
            self.coord_changed.emit(lat, lon)
        elif event.button() == Qt.RightButton:
            self._pan_last = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan_last is not None:
            delta           = event.pos() - self._pan_last
            self._pan_last  = event.pos()
            n               = 2 ** self._zoom
            self._center_lon -= delta.x() / (TILE_SIZE * n) * 360
            self._center_lat  = max(-85, min(85,
                self._center_lat + delta.y() / (TILE_SIZE * n) * 180
            ))
            self._load_tiles()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self._pan_last = None
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0 and self._zoom < self.ZOOM_MAX:
            self._zoom += 1
        elif delta < 0 and self._zoom > self.ZOOM_MIN:
            self._zoom -= 1
        else:
            return
        self._load_tiles()

    # ── marker ────────────────────────────────────────────────────────────────
    def _draw_marker(self, lat, lon):
        if self._marker:
            self._scene.removeItem(self._marker)
        if self._marker_lbl:
            self._scene.removeItem(self._marker_lbl)

        sx, sy = _ll_to_scene(lat, lon, self._origin_tx, self._origin_ty, self._zoom)
        r = 8
        self._marker = self._scene.addEllipse(
            sx - r, sy - r, r * 2, r * 2,
            QPen(QColor("#c0392b"), 2),
            QBrush(QColor(231, 76, 60, 200)),
        )
        self._marker.setZValue(10)

        lbl = self._scene.addText(f"  {lat:.4f}, {lon:.4f}")
        lbl.setDefaultTextColor(QColor("#1a1a2e"))
        f = QFont("Consolas", 8)
        f.setBold(True)
        lbl.setFont(f)
        lbl.setPos(sx + r + 3, sy - 10)
        lbl.setZValue(11)
        self._marker_lbl = lbl

    # ── public API ────────────────────────────────────────────────────────────
    def zoom_in(self):
        if self._zoom < self.ZOOM_MAX:
            self._zoom += 1
            self._load_tiles()

    def zoom_out(self):
        if self._zoom > self.ZOOM_MIN:
            self._zoom -= 1
            self._load_tiles()

    def get_selected(self):
        return self._sel_lat, self._sel_lon


# ─────────────────────────────────────────────────────────────────────────────
# MapDialog
# ─────────────────────────────────────────────────────────────────────────────
class MapDialog(QDialog):
    def __init__(self, parent=None, prefs: AppPreferences = None):
        super().__init__(parent)
        self.setWindowTitle("Select Farm Location")
        self.resize(700, 580)
        self._prefs = prefs or AppPreferences.load()

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        hint = QLabel(
            "🖱  Left-click to place marker   |   "
            "Right-drag to pan   |   Scroll to zoom"
        )
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color:#666; font-size:11px; padding:2px;")
        layout.addWidget(hint)

        self._map = TileMapWidget(self)
        self._map._center_lat = self._prefs.map_last_lat
        self._map._center_lon = self._prefs.map_last_lon
        self._map._load_tiles()
        self._map.coord_changed.connect(self._on_coord)
        layout.addWidget(self._map)

        self._coord_lbl = QLabel("No location selected — click on the map")
        self._coord_lbl.setAlignment(Qt.AlignCenter)
        self._apply_coord_style()
        layout.addWidget(self._coord_lbl)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 4, 0, 0)

        btn_zi = QPushButton("  +  ")
        btn_zo = QPushButton("  −  ")
        for b in (btn_zi, btn_zo):
            b.setFixedWidth(42)
            b.setFixedHeight(28)
        btn_zi.clicked.connect(self._map.zoom_in)
        btn_zo.clicked.connect(self._map.zoom_out)

        self._btn_confirm = QPushButton("✔  Confirm Location")
        self._btn_confirm.setEnabled(False)
        self._btn_confirm.setFixedHeight(32)
        self._btn_confirm.setDefault(True)
        self._btn_confirm.clicked.connect(self._on_confirm)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(32)
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(QLabel("Zoom:"))
        btn_row.addWidget(btn_zo)
        btn_row.addWidget(btn_zi)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_confirm)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def _apply_coord_style(self):
        if self._prefs.theme == "light":
            self._coord_lbl.setStyleSheet(
                "font-family:Consolas; font-size:12px; font-weight:bold;"
                "background:#f5f5f5; color:#1a1a2e; border:1px solid #ddd;"
                "border-radius:4px; padding:5px;"
            )
        elif self._prefs.theme == "black":
            self._coord_lbl.setStyleSheet(
                "font-family:Consolas; font-size:12px; font-weight:bold;"
                "background:#0d0d0d; color:#e0e0e0; border:1px solid #333333;"
                "border-radius:4px; padding:5px;"
            )
        else:
            self._coord_lbl.setStyleSheet(
                "font-family:Consolas; font-size:12px; font-weight:bold;"
                "background:#2D2D2D; color:#cccccc; border:1px solid #58595a;"
                "border-radius:4px; padding:5px;"
            )

    def _on_coord(self, lat, lon):
        self._coord_lbl.setText(f"📍  Lat {lat:.5f}   |   Lon {lon:.5f}")
        self._btn_confirm.setEnabled(True)

    def _on_confirm(self):
        lat, lon = self._map.get_selected()
        if lat is None:
            QMessageBox.warning(self, "No Location",
                                "Click the map to select a location first.")
            return
        self.accept()

    def get_coordinates(self):
        lat, lon = self._map.get_selected()
        return [(lat, lon)] if lat is not None else [(36.0, 5.0)]


# ─────────────────────────────────────────────────────────────────────────────
# ConfigDialog  (year limits enforced + Monthly Summary checkbox added)
# ─────────────────────────────────────────────────────────────────────────────
class ConfigDialog(QDialog):
    def __init__(
        self, parent=None, year_bounds: PvgisYearBounds = None,
        prefs: AppPreferences = None, saved_sim: dict = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Simulation Configuration")
        self.setMinimumWidth(360)
        self._bounds = year_bounds
        self._prefs = prefs or AppPreferences.load()
        self._saved_sim = saved_sim or {}

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(14, 14, 14, 14)

        # ── Year range ────────────────────────────────────────────────────────
        db_label = year_bounds.radiation_db if year_bounds else "PVGIS"
        self._yr_box = QGroupBox(f"Simulation Period  ({db_label})")
        yr_form = QFormLayout(self._yr_box)
        yr_form.setSpacing(6)

        self.start_yr = QSpinBox()
        yr_form.addRow("Start year:", self.start_yr)

        self._end_yr_label = QLabel("End year:")
        self.end_yr = QSpinBox()
        yr_form.addRow(self._end_yr_label, self.end_yr)

        self._yr_note = QLabel()
        self._yr_note.setTextFormat(Qt.RichText)
        self._yr_note.setStyleSheet("color: #888; font-size: 10px;")
        self._yr_note.setWordWrap(True)
        yr_form.addRow(self._yr_note)

        self.start_yr.valueChanged.connect(
            lambda v: self.end_yr.setValue(max(self.end_yr.value(), v + 1))
        )
        self.end_yr.valueChanged.connect(
            lambda v: self.start_yr.setValue(min(self.start_yr.value(), v - 1))
        )

        if year_bounds:
            self._apply_year_bounds(year_bounds)
            if self._saved_sim.get("start_year") and self._saved_sim.get("end_year"):
                ymin, ymax = year_bounds.year_min, year_bounds.year_max
                sy = max(ymin, min(self._saved_sim["start_year"], ymax - 1))
                ey = max(ymin + 1, min(self._saved_sim["end_year"], ymax))
                self.start_yr.setValue(sy)
                self.end_yr.setValue(ey)

        preset_row = QHBoxLayout()
        for label, years in (("Last 1 year", 1), ("Last 3 years", 3), ("Last 5 years", 5)):
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked=False, n=years: self._apply_preset(n))
            preset_row.addWidget(btn)
        yr_form.addRow("Quick range:", preset_row)

        root.addWidget(self._yr_box)

        load_box = QGroupBox("Site load (consumption)")
        load_form = QFormLayout(load_box)
        self._load_kw = QDoubleSpinBox()
        self._load_kw.setRange(0, 500)
        self._load_kw.setDecimals(2)
        self._load_kw.setSuffix(" kW")
        self._load_kw.setValue(self._prefs.base_load_kw)
        load_form.addRow("Average load:", self._load_kw)
        self._load_profile = QComboBox()
        self._load_profile.addItems([
            "Constant",
            "Evening peak",
            "Daytime peak",
        ])
        profile_map = {
            "constant": 0,
            "evening_peak": 1,
            "daytime_peak": 2,
        }
        self._load_profile.setCurrentIndex(
            profile_map.get(self._prefs.load_profile, 0)
        )
        load_form.addRow("Load profile:", self._load_profile)
        load_note = QLabel(
            "Load is applied every simulated hour. Wire panels to batteries "
            "so only connected strings contribute to production."
        )
        load_note.setWordWrap(True)
        load_note.setStyleSheet("color: #888; font-size: 10px;")
        load_form.addRow(load_note)
        root.addWidget(load_box)

        # ── Graph selection ───────────────────────────────────────────────────
        graph_box = QGroupBox("Post-simulation Graphs")
        graph_layout = QVBoxLayout(graph_box)
        graph_layout.setSpacing(4)

        self.chk_graphs = QCheckBox("Generate graphs after simulation")
        self.chk_graphs.setChecked(self._prefs.chart_auto_open)
        graph_layout.addWidget(self.chk_graphs)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        graph_layout.addWidget(sep)

        self.chk_power   = QCheckBox("Power Curve  (hourly PV output)")
        self.chk_soc     = QCheckBox("Battery SOC  (state of charge over time)")
        self.chk_monthly = QCheckBox("Monthly Summary  (total kWh per month)")

        self.chk_power.setChecked(self._prefs.graph_power)
        self.chk_soc.setChecked(self._prefs.graph_soc)
        self.chk_monthly.setChecked(self._prefs.graph_monthly)
        for chk in (self.chk_power, self.chk_soc, self.chk_monthly):
            graph_layout.addWidget(chk)

        def _toggle_graph_checks(enabled):
            for chk in (self.chk_power, self.chk_soc, self.chk_monthly):
                chk.setEnabled(enabled)

        self.chk_graphs.toggled.connect(_toggle_graph_checks)
        root.addWidget(graph_box)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_run = QPushButton("▶  Run Simulation")
        btn_run.setFixedHeight(34)
        btn_run.setDefault(True)
        btn_run.clicked.connect(self._validate_and_accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_run)
        root.addLayout(btn_row)

    def _apply_preset(self, num_years: int):
        if not self._bounds:
            return
        ymax = self._bounds.year_max
        ymin = self._bounds.year_min
        start = max(ymin, ymax - num_years + 1)
        self.start_yr.setValue(start)
        self.end_yr.setValue(ymax)

    def _apply_year_bounds(self, bounds: PvgisYearBounds):
        self._bounds = bounds
        ymin, ymax = bounds.year_min, bounds.year_max
        self._yr_box.setTitle(f"Simulation Period  ({bounds.radiation_db})")

        self.start_yr.blockSignals(True)
        self.end_yr.blockSignals(True)
        self.start_yr.setRange(ymin, ymax - 1)
        self.end_yr.setRange(ymin + 1, ymax)
        default_start = max(ymin, ymax - 5)
        self.start_yr.setValue(default_start)
        self.end_yr.setValue(ymax)
        self.start_yr.blockSignals(False)
        self.end_yr.blockSignals(False)

        self._end_yr_label.setText(f"End year  (max {ymax}):")
        self._yr_note.setText(
            f"PVGIS database <b>{bounds.radiation_db}</b> at this location.\n"
            f"Available years: {ymin}–{ymax}. Start year must be less than end year."
        )

    def _validate_and_accept(self):
        if self.start_yr.value() >= self.end_yr.value():
            QMessageBox.warning(
                self, "Invalid Range",
                "Start year must be strictly less than End year."
            )
            return
        self.accept()

    def get_params(self, coords):
        return SimulationParams(
            coordinates=coords,
            start_year=self.start_yr.value(),
            end_year=self.end_yr.value(),
            simulation_time=0.0,
        )

    def apply_load_to_preferences(self, prefs: AppPreferences):
        prefs.base_load_kw = self._load_kw.value()
        idx = self._load_profile.currentIndex()
        prefs.load_profile = ("constant", "evening_peak", "daytime_peak")[idx]

    def get_graph_selection(self):
        types = []
        if self.chk_power.isChecked():
            types.append("Power Curve")
        if self.chk_soc.isChecked():
            types.append("Battery SOC")
        if self.chk_monthly.isChecked():
            types.append("Monthly Summary")
        return GraphSelection(
            generate_graphs=self.chk_graphs.isChecked(),
            selected_types=types,
        )


# ─────────────────────────────────────────────────────────────────────────────
# SettingsDialog
# ─────────────────────────────────────────────────────────────────────────────
class SettingsDialog(QDialog):
    """Tabbed application preferences."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumSize(520, 460)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowIcon(app_logo_icon())

        self._prefs = AppPreferences.load()
        self._original_theme = self._prefs.theme
        self._key_edits: dict = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        tabs = QTabWidget()

        # Appearance
        appear = QWidget()
        appear_form = QFormLayout(appear)
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Design", "Light", "Dark"])
        _theme_idx = {
            "charcoal": 0, "default": 0, "design": 0,
            "light": 1,
            "black": 2, "dark": 2,
        }.get(normalize_theme(self._prefs.theme), 0)
        self._theme_combo.setCurrentIndex(_theme_idx)
        self._theme_combo.currentIndexChanged.connect(self._preview_theme)
        appear_form.addRow("UI Theme:", self._theme_combo)
        self._font_spin = QSpinBox()
        self._font_spin.setRange(8, 18)
        self._font_spin.setValue(self._prefs.terminal_font_size)
        appear_form.addRow("Terminal font size:", self._font_spin)
        tabs.addTab(appear, "Appearance")

        # Keyboard
        kb_page = QWidget()
        kb_layout = QVBoxLayout(kb_page)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        kb_inner = QWidget()
        kb_grid = QGridLayout(kb_inner)
        kb_grid.setColumnStretch(1, 1)
        row = 0
        for aid, (label, default) in SHORTCUT_DEFINITIONS.items():
            kb_grid.addWidget(QLabel(label), row, 0)
            edit = QKeySequenceEdit()
            seq = self._prefs.shortcuts.get(aid, default)
            if seq:
                edit.setKeySequence(QKeySequence(seq))
            kb_grid.addWidget(edit, row, 1)
            self._key_edits[aid] = edit
            row += 1
        scroll.setWidget(kb_inner)
        kb_layout.addWidget(scroll)
        btn_reset_keys = QPushButton("Reset all shortcuts to defaults")
        btn_reset_keys.clicked.connect(self._reset_shortcuts)
        kb_layout.addWidget(btn_reset_keys)
        tabs.addTab(kb_page, "Keyboard")

        # Simulation
        sim = QWidget()
        sim_form = QFormLayout(sim)
        self._loss_spin = QDoubleSpinBox()
        self._loss_spin.setRange(0, 30)
        self._loss_spin.setSuffix(" %")
        self._loss_spin.setValue(self._prefs.system_loss_pct)
        sim_form.addRow("System loss:", self._loss_spin)
        self._idle_spin = QDoubleSpinBox()
        self._idle_spin.setRange(0, 20)
        self._idle_spin.setSuffix(" % / day")
        self._idle_spin.setValue(self._prefs.battery_idle_loss_pct)
        sim_form.addRow("Battery idle loss:", self._idle_spin)
        self._base_load_spin = QDoubleSpinBox()
        self._base_load_spin.setRange(0, 500)
        self._base_load_spin.setDecimals(2)
        self._base_load_spin.setSuffix(" kW")
        self._base_load_spin.setValue(self._prefs.base_load_kw)
        sim_form.addRow("Default site load:", self._base_load_spin)
        self._load_profile_combo = QComboBox()
        self._load_profile_combo.addItems([
            "Constant", "Evening peak", "Daytime peak",
        ])
        _lp = {"constant": 0, "evening_peak": 1, "daytime_peak": 2}
        self._load_profile_combo.setCurrentIndex(
            _lp.get(self._prefs.load_profile, 0)
        )
        sim_form.addRow("Default load profile:", self._load_profile_combo)
        self._chk_require_wire = QCheckBox(
            "Only count PV wired to a battery (recommended)"
        )
        self._chk_require_wire.setChecked(self._prefs.require_wired_to_battery)
        sim_form.addRow(self._chk_require_wire)
        self._charge_eff = QDoubleSpinBox()
        self._charge_eff.setRange(50, 100)
        self._charge_eff.setSuffix(" %")
        self._charge_eff.setValue(self._prefs.battery_charge_efficiency * 100)
        sim_form.addRow("Battery charge efficiency:", self._charge_eff)
        self._discharge_eff = QDoubleSpinBox()
        self._discharge_eff.setRange(50, 100)
        self._discharge_eff.setSuffix(" %")
        self._discharge_eff.setValue(self._prefs.battery_discharge_efficiency * 100)
        sim_form.addRow("Battery discharge efficiency:", self._discharge_eff)
        self._c_rate_spin = QDoubleSpinBox()
        self._c_rate_spin.setRange(0.05, 2.0)
        self._c_rate_spin.setDecimals(2)
        self._c_rate_spin.setSingleStep(0.05)
        self._c_rate_spin.setValue(self._prefs.battery_max_c_rate)
        sim_form.addRow("Max battery C-rate (per hour):", self._c_rate_spin)
        self._timeout_spin = QSpinBox()
        self._timeout_spin.setRange(10, 120)
        self._timeout_spin.setSuffix(" s")
        self._timeout_spin.setValue(self._prefs.pvgis_timeout_sec)
        sim_form.addRow("PVGIS timeout:", self._timeout_spin)
        self._chk_auto_charts = QCheckBox("Auto-open charts after simulation")
        self._chk_auto_charts.setChecked(self._prefs.chart_auto_open)
        sim_form.addRow(self._chk_auto_charts)
        tabs.addTab(sim, "Simulation")

        # Charts & export
        charts = QWidget()
        charts_form = QFormLayout(charts)
        self._style_combo = QComboBox()
        self._style_combo.addItems(CHART_STYLES)
        idx = self._style_combo.findText(self._prefs.chart_default_style)
        if idx >= 0:
            self._style_combo.setCurrentIndex(idx)
        charts_form.addRow("Default chart style:", self._style_combo)
        self._chk_g_power = QCheckBox("Power Curve")
        self._chk_g_power.setChecked(self._prefs.graph_power)
        self._chk_g_soc = QCheckBox("Battery SOC")
        self._chk_g_soc.setChecked(self._prefs.graph_soc)
        self._chk_g_monthly = QCheckBox("Monthly Summary")
        self._chk_g_monthly.setChecked(self._prefs.graph_monthly)
        charts_form.addRow("Default graph tabs:", self._chk_g_power)
        charts_form.addRow("", self._chk_g_soc)
        charts_form.addRow("", self._chk_g_monthly)
        self._export_combo = QComboBox()
        self._export_combo.addItems(["Text (.txt)", "CSV (.csv)", "Report folder"])
        fmt_map = {"txt": 0, "csv": 1, "report": 2}
        self._export_combo.setCurrentIndex(fmt_map.get(self._prefs.export_format, 0))
        charts_form.addRow("Default export format:", self._export_combo)
        tabs.addTab(charts, "Charts && Export")

        root.addWidget(tabs)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self._on_cancel)
        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(self._on_apply)
        btn_ok = QPushButton("OK")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self._on_ok)
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_apply)
        btn_row.addWidget(btn_ok)
        root.addLayout(btn_row)
        self._preview_theme()

    def _selected_theme_key(self) -> str:
        keys = ("charcoal", "light", "black")
        idx = self._theme_combo.currentIndex()
        return keys[idx] if 0 <= idx < len(keys) else "charcoal"

    def _preview_theme(self):
        key = normalize_theme(self._selected_theme_key())
        QApplication.instance().setStyleSheet(THEMES.get(key, ""))
        apply_active_chart_palette(key)
        self.setStyleSheet(chart_dialog_stylesheet(key))

    def _reset_shortcuts(self):
        defaults = AppPreferences.default_shortcuts()
        for aid, edit in self._key_edits.items():
            edit.setKeySequence(QKeySequence(defaults.get(aid, "")))

    def _collect_prefs(self) -> AppPreferences:
        p = AppPreferences.load()
        p.theme = self._selected_theme_key()
        p.terminal_font_size = self._font_spin.value()
        p.system_loss_pct = self._loss_spin.value()
        p.battery_idle_loss_pct = self._idle_spin.value()
        p.base_load_kw = self._base_load_spin.value()
        p.load_profile = ("constant", "evening_peak", "daytime_peak")[
            self._load_profile_combo.currentIndex()
        ]
        p.require_wired_to_battery = self._chk_require_wire.isChecked()
        p.battery_charge_efficiency = self._charge_eff.value() / 100.0
        p.battery_discharge_efficiency = self._discharge_eff.value() / 100.0
        p.battery_max_c_rate = self._c_rate_spin.value()
        p.pvgis_timeout_sec = self._timeout_spin.value()
        p.chart_auto_open = self._chk_auto_charts.isChecked()
        p.chart_default_style = self._style_combo.currentText()
        p.graph_power = self._chk_g_power.isChecked()
        p.graph_soc = self._chk_g_soc.isChecked()
        p.graph_monthly = self._chk_g_monthly.isChecked()
        fmt_idx = self._export_combo.currentIndex()
        p.export_format = EXPORT_FORMATS[fmt_idx]
        p.shortcuts = {}
        for aid, edit in self._key_edits.items():
            p.shortcuts[aid] = edit.keySequence().toString(QKeySequence.PortableText)
        return p

    def _on_apply(self):
        prefs = self._collect_prefs()
        dups = prefs.find_duplicate_shortcuts()
        if dups:
            seq, _, aids = dups[0]
            QMessageBox.warning(
                self, "Duplicate shortcut",
                f"The key '{seq}' is assigned to multiple actions: {', '.join(aids)}.",
            )
            return
        prefs.save()
        QApplication.instance().setStyleSheet(THEMES.get(prefs.theme, ""))
        mw = self.parent()
        if mw and hasattr(mw, "apply_preferences"):
            mw.apply_preferences()

    def _on_ok(self):
        self._on_apply()
        self.accept()

    def _on_cancel(self):
        key = normalize_theme(self._original_theme)
        QApplication.instance().setStyleSheet(THEMES.get(key, ""))
        apply_active_chart_palette(key)
        self.reject()