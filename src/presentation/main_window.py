import json
import time

from PyQt5.QtWidgets import (
    QMainWindow, QAction, QDockWidget,
    QDialog, QMenu, QFileDialog, QMessageBox,
    QApplication, QProgressDialog, QLabel, QDialogButtonBox,
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt, QTimer

from src.presentation.title_bar import AppChromeContainer, DockTitleBar, WorkshopToolbar
from src.presentation.icon_button import clone_menu
from src.presentation.ui_assets import app_logo_icon

from src.presentation.workspace import WorkspaceCanvas, MODE_SELECT
from src.presentation.panels import CataloguePanel, PropertiesPanel
from src.presentation.widgets import TerminalPanel, ErrorNotificationWindow, ExportHandler
from src.presentation.dialogs import MapDialog, ConfigDialog, SettingsDialog
from src.simulation.formatter import GraphDialog
from src.simulation.controller import SimulationController
from src.simulation.worker import SimulationWorker
from src.core.exceptions import SolarTwinError
from src.core.theme import THEMES, normalize_theme, apply_active_chart_palette
from src.core.preferences import AppPreferences, SHORTCUT_DEFINITIONS
from src.core.shortcuts import ShortcutManager


class ShortcutsHelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumWidth(420)
        prefs = AppPreferences.load()
        lines = ["<b>Current keyboard shortcuts</b><br><br><table>"]
        for aid, (label, _) in SHORTCUT_DEFINITIONS.items():
            seq = prefs.shortcuts.get(aid, "")
            lines.append(
                f"<tr><td style='padding:4px 12px 4px 0'>{label}</td>"
                f"<td><code>{seq or '—'}</code></td></tr>"
            )
        lines.append("</table>")
        lbl = QLabel("".join(lines))
        lbl.setTextFormat(Qt.RichText)
        lbl.setWordWrap(True)
        lay = QVBoxLayout(self)
        lay.addWidget(lbl)
        box = QDialogButtonBox(QDialogButtonBox.Ok)
        box.accepted.connect(self.accept)
        lay.addWidget(box)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Solar Farm Digital Twin")
        self.resize(1400, 900)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setWindowIcon(app_logo_icon(32))

        self.prefs = AppPreferences.load()
        self.sim_controller = SimulationController()
        self.shortcuts = ShortcutManager()
        self._actions: dict[str, QAction] = {}

        self.workspace_canvas = WorkspaceCanvas()
        self.last_sim_result_text = ""
        self.last_sim_result = None
        self.last_graph_sel = None
        self._last_sim_meta = {}
        self._current_file = None
        self._unsaved_changes = False
        self._saved_simulation = {}
        self._worker = None
        self._progress = None

        # menuBar() must be created BEFORE setMenuWidget() on frameless windows
        # (calling menuBar() after setMenuWidget crashes Qt on Windows).
        self._init_menubar()
        self._init_chrome()
        self._init_panels()
        self._build_app_menu()
        self._init_escape_shortcut()
        self.apply_preferences()
        QTimer.singleShot(0, self._apply_dock_layout)

    def _register(self, action_id: str, action: QAction, tooltip: str = ""):
        self._actions[action_id] = action
        self.shortcuts.register(action_id, action, tooltip)

    def _init_chrome(self):
        self._chrome = AppChromeContainer(self)
        self.setMenuWidget(self._chrome)
        # Hide native menu row; actions remain for keyboard shortcuts.
        self._menu_bar.hide()
        self._title_bar = self._chrome.chrome_bar
        self._workshop = self._chrome.workshop

        self._workshop.mode_changed.connect(self._on_workshop_mode)
        self._workshop.grid_toggled.connect(self.workspace_canvas.set_grid_visible)
        self._workshop.simulate_button().clicked.connect(self.on_simulate_requested)
        self._act_simulate = self._workshop.simulate_button()
        self._register_simulate_action(self._act_simulate)

        for aid, (label, default) in SHORTCUT_DEFINITIONS.items():
            if aid.startswith("mode_"):
                act = QAction(label, self)
                seq = self.prefs.shortcuts.get(aid, default)
                if seq:
                    act.setShortcut(QKeySequence(seq))
                if aid == "mode_select":
                    act.triggered.connect(lambda: self._workshop.set_mode(WorkshopToolbar.MODE_SELECT))
                elif aid == "mode_wire":
                    act.triggered.connect(lambda: self._workshop.set_mode(WorkshopToolbar.MODE_WIRE))
                elif aid == "mode_zoom":
                    act.triggered.connect(lambda: self._workshop.set_mode(WorkshopToolbar.MODE_ZOOM))
                elif aid == "mode_text":
                    act.triggered.connect(lambda: self._workshop.set_mode(WorkshopToolbar.MODE_TEXT))
                elif aid == "mode_delete":
                    act.triggered.connect(
                        lambda: self._workshop.set_mode(WorkshopToolbar.MODE_DELETE)
                    )
                self.addAction(act)
                self._register(aid, act, label)

    def _init_menubar(self):
        self._menu_bar = self.menuBar()
        mb = self._menu_bar
        project_menu = mb.addMenu("&Project")

        act_new = QAction("&New Project", self)
        act_new.triggered.connect(self.on_new_project)
        project_menu.addAction(act_new)
        self._register("new_project", act_new, "New project")

        project_menu.addSeparator()

        act_save = QAction("&Save Project", self)
        act_save.triggered.connect(self.on_save_project)
        project_menu.addAction(act_save)
        self._register("save_project", act_save, "Save project")

        act_save_as = QAction("Save Project &As…", self)
        act_save_as.triggered.connect(self.on_save_project_as)
        project_menu.addAction(act_save_as)
        self._register("save_as", act_save_as, "Save project as")

        act_load = QAction("&Load Project…", self)
        act_load.triggered.connect(self.on_load_project)
        project_menu.addAction(act_load)
        self._register("open_project", act_load, "Open project")

        project_menu.addSeparator()

        act_export = QAction("&Export Results…", self)
        act_export.triggered.connect(self.on_export_requested)
        project_menu.addAction(act_export)
        self._register("export_results", act_export, "Export results")

        project_menu.addSeparator()

        act_quit = QAction("&Quit", self)
        act_quit.triggered.connect(self.close)
        project_menu.addAction(act_quit)
        self._register("quit", act_quit, "Quit")

        self._view_menu = mb.addMenu("&View")

        act_charts = QAction("Open Simulation &Charts", self)
        act_charts.triggered.connect(self.on_open_charts)
        act_charts.setEnabled(False)
        self._view_menu.addAction(act_charts)
        self._act_open_charts = act_charts
        self._register("open_charts", act_charts, "Open simulation charts")

        self._window_menu = mb.addMenu("&Window")

        settings_menu = mb.addMenu("&Settings")
        act_prefs = QAction("&Preferences…", self)
        act_prefs.triggered.connect(self.on_open_settings)
        settings_menu.addAction(act_prefs)
        self._register("preferences", act_prefs, "Preferences")

        self._help_menu = mb.addMenu("&Help")
        act_shortcuts = QAction("&Keyboard Shortcuts…", self)
        act_shortcuts.triggered.connect(self._show_shortcuts_help)
        self._help_menu.addAction(act_shortcuts)

        self._project_menu = project_menu
        self._settings_menu = settings_menu

    def _build_app_menu(self):
        """Standalone menus for chrome (avoids crash with hidden menu bar)."""
        self._chrome_menus = {
            "Project": clone_menu(self._project_menu, self),
            "View": clone_menu(self._view_menu, self),
            "Window": clone_menu(self._window_menu, self),
            "Settings": clone_menu(self._settings_menu, self),
            "Help": clone_menu(self._help_menu, self),
        }
        self._title_bar.setup_menu_buttons([
            (title, menu) for title, menu in self._chrome_menus.items()
        ])

    def _toggle_dock(self, dock: QDockWidget, visible: bool):
        dock.setVisible(visible)
        if visible:
            dock.raise_()

    def _delete_selection_shortcut(self):
        self.workspace_canvas.set_mode(WorkshopToolbar.MODE_SELECT)
        self._workshop.set_mode(WorkshopToolbar.MODE_SELECT)
        self.workspace_canvas.delete_selection()

    def _on_workshop_mode(self, mode_id: int):
        self.workspace_canvas.set_mode(mode_id)

    def _register_simulate_action(self, widget):
        """Register simulate for shortcuts without QAction."""
        aid = "simulate"
        act = QAction("Simulate", self)
        act.triggered.connect(self.on_simulate_requested)
        self._actions[aid] = act
        self.shortcuts.register(aid, act, "Run simulation")

    def _init_escape_shortcut(self):
        from PyQt5.QtWidgets import QShortcut
        esc = QShortcut(QKeySequence(), self)
        self._esc_shortcut = esc
        esc.activated.connect(self._escape_to_select)

    def _escape_to_select(self):
        self.workspace_canvas.set_mode(MODE_SELECT)
        self._workshop.set_mode(WorkshopToolbar.MODE_SELECT)

    def _apply_dock_layout(self):
        try:
            self._cat_dock.setVisible(True)
            self._prop_dock.setVisible(True)
            self._term_dock.setVisible(True)
            self.resizeDocks([self._cat_dock], [260], Qt.Horizontal)
            self.resizeDocks([self._prop_dock], [300], Qt.Horizontal)
            self.resizeDocks([self._term_dock], [200], Qt.Vertical)
        except Exception:
            pass

    def _init_panels(self):
        self.setCentralWidget(self.workspace_canvas)

        self.catalogue_panel = CataloguePanel()
        self._cat_dock = QDockWidget("Catalogue", self)
        self._cat_dock.setObjectName("CatalogueDock")
        self._cat_dock.setWidget(self.catalogue_panel)
        self._cat_dock.setTitleBarWidget(DockTitleBar("Catalogue", self._cat_dock))
        self._cat_dock.setMinimumWidth(220)
        self._cat_dock.setFeatures(
            QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self._cat_dock)

        self.properties_panel = PropertiesPanel()
        self._prop_dock = QDockWidget("properties", self)
        self._prop_dock.setObjectName("PropertiesDock")
        self._prop_dock.setWidget(self.properties_panel)
        self._prop_dock.setTitleBarWidget(DockTitleBar("properties", self._prop_dock))
        self._prop_dock.setMinimumWidth(280)
        self._prop_dock.setFeatures(
            QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable
        )
        self.addDockWidget(Qt.RightDockWidgetArea, self._prop_dock)

        self.terminal_panel = TerminalPanel()
        self._term_dock = QDockWidget("Terminal", self)
        self._term_dock.setObjectName("TerminalDock")
        self._term_dock.setWidget(self.terminal_panel)
        self._term_dock.setTitleBarWidget(DockTitleBar("Terminal", self._term_dock))
        self._term_dock.setMinimumHeight(140)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._term_dock)

        self._dock_panel_actions = []
        for dock, label in (
            (self._cat_dock, "Catalogue"),
            (self._prop_dock, "Properties"),
            (self._term_dock, "Terminal"),
        ):
            act = QAction(label, self, checkable=True, checked=True)
            act.triggered.connect(
                lambda checked, d=dock: self._toggle_dock(d, checked)
            )
            dock.visibilityChanged.connect(act.setChecked)
            self._window_menu.addAction(act)
            self._dock_panel_actions.append((dock, act))

        self.workspace_canvas.component_selected_signal.connect(
            self.properties_panel.update_properties
        )
        self.workspace_canvas.component_moved_signal.connect(
            self._on_component_moved
        )
        self.properties_panel.property_changed.connect(self._mark_dirty)

    def apply_preferences(self):
        self.prefs = AppPreferences.load()
        theme = normalize_theme(self.prefs.theme)
        self.prefs.theme = theme
        QApplication.instance().setStyleSheet(THEMES.get(theme, ""))
        apply_active_chart_palette(theme)
        self.shortcuts.apply_all(self.prefs)
        esc_seq = self.prefs.shortcuts.get("escape_select", "Esc")
        self._esc_shortcut.setKey(QKeySequence(esc_seq) if esc_seq else QKeySequence())
        self.sim_controller.apply_preferences(self.prefs)
        self.terminal_panel.apply_preferences(self.prefs)

    def _show_shortcuts_help(self):
        ShortcutsHelpDialog(self).exec_()

    def _restore_theme(self):
        self.apply_preferences()

    def _on_component_moved(self, item):
        self._mark_dirty()
        if self.properties_panel._item is item:
            self.properties_panel.update_properties(item)

    def _mark_dirty(self):
        self._unsaved_changes = True
        base = self._current_file or "Untitled"
        self.setWindowTitle(f"Solar Farm Digital Twin — {base} *")

    def _mark_clean(self, filepath=None):
        self._unsaved_changes = False
        if filepath:
            self._current_file = filepath
        base = self._current_file or "Untitled"
        self.setWindowTitle(f"Solar Farm Digital Twin — {base}")

    def _confirm_discard(self) -> bool:
        if not self._unsaved_changes:
            return True
        reply = QMessageBox.question(
            self, "Unsaved Changes",
            "You have unsaved changes. Save before continuing?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )
        if reply == QMessageBox.Save:
            return self.on_save_project()
        if reply == QMessageBox.Discard:
            return True
        return False

    def _build_project_document(self) -> dict:
        doc = {"workspace": self.workspace_canvas.save_state()}
        if self._saved_simulation:
            doc["simulation"] = self._saved_simulation
        return doc

    def on_new_project(self):
        if not self._confirm_discard():
            return
        self.workspace_canvas.clear_canvas()
        self.terminal_panel.set_status("New project created.")
        self.last_sim_result_text = ""
        self.last_sim_result = None
        self.last_graph_sel = None
        self._saved_simulation = {}
        self._last_sim_meta = {}
        self._act_open_charts.setEnabled(False)
        self._current_file = None
        self._mark_clean()
        self.setWindowTitle("Solar Farm Digital Twin — Untitled")

    def on_save_project(self) -> bool:
        if self._current_file is None:
            return self.on_save_project_as()
        return self._do_save(self._current_file)

    def on_save_project_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "",
            "Solar Farm Twin Project (*.sftwin);;All Files (*)"
        )
        if not path:
            return False
        if not path.endswith(".sftwin"):
            path += ".sftwin"
        return self._do_save(path)

    def _do_save(self, path: str) -> bool:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._build_project_document(), f, indent=2)
            self._mark_clean(path)
            self.terminal_panel.set_status(f"Project saved → {path}")
            return True
        except Exception as e:
            ErrorNotificationWindow.show_error(self, "Save Error", str(e))
            return False

    def on_load_project(self):
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Project", "",
            "Solar Farm Twin Project (*.sftwin);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                doc = json.load(f)
            if "workspace" in doc:
                self.workspace_canvas.load_state(doc["workspace"])
            else:
                self.workspace_canvas.load_state(doc)
            self._saved_simulation = doc.get("simulation", {})
            self._mark_clean(path)
            self.terminal_panel.set_status(f"Project loaded ← {path}")
        except Exception as e:
            ErrorNotificationWindow.show_error(self, "Load Error", str(e))

    def on_open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self.apply_preferences()

    def on_open_charts(self):
        if not self.last_sim_result or not self.last_graph_sel:
            ErrorNotificationWindow.show_error(
                self, "Charts", "No simulation results available. Run a simulation first."
            )
            return
        self.graph_dlg = GraphDialog(
            self.last_sim_result, self.last_graph_sel, parent=self,
        )
        self.graph_dlg.show()

    def on_simulate_requested(self):
        circuit = self.workspace_canvas.serialize_circuit()
        if not circuit or not circuit.panels:
            ErrorNotificationWindow.show_error(
                self, "Validation Error",
                "Workspace requires at least one Panel to simulate."
            )
            return

        map_dlg = MapDialog(self, self.prefs)
        if map_dlg.exec_() != QDialog.Accepted:
            return
        coords = map_dlg.get_coordinates()
        lat, lon = coords[0]

        self.prefs.map_last_lat = lat
        self.prefs.map_last_lon = lon
        self.prefs.save()

        self.terminal_panel.set_status("Querying PVGIS data availability for this location…")
        QApplication.processEvents()
        try:
            year_bounds = self.sim_controller.pvgis_client.fetch_year_bounds(lat, lon)
        except SolarTwinError as e:
            self.on_error_caught(e)
            return

        cfg_dlg = ConfigDialog(
            self, year_bounds=year_bounds, prefs=self.prefs,
            saved_sim=self._saved_simulation,
        )
        if cfg_dlg.exec_() != QDialog.Accepted:
            return

        cfg_dlg.apply_load_to_preferences(self.prefs)
        self.prefs.save()

        params = cfg_dlg.get_params(coords)
        graph_sel = cfg_dlg.get_graph_selection()

        self._saved_simulation = {
            "last_lat": lat,
            "last_lon": lon,
            "start_year": params.start_year,
            "end_year": params.end_year,
            "year_bounds": {
                "year_min": year_bounds.year_min,
                "year_max": year_bounds.year_max,
                "radiation_db": year_bounds.radiation_db,
            },
        }

        self._act_simulate.setEnabled(False)
        self._progress = QProgressDialog(
            "Running simulation…", None, 0, 0, self,
        )
        self._progress.setWindowTitle("Simulation")
        self._progress.setWindowModality(Qt.WindowModal)
        self._progress.setMinimumDuration(0)
        self._progress.show()

        self._worker = SimulationWorker(
            self.sim_controller, circuit, params, graph_sel, self,
        )
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.finished_ok.connect(self._on_worker_finished)
        self._worker.failed.connect(self._on_worker_failed)
        self._sim_t0 = time.time()
        self._pending_graph_sel = graph_sel
        self._pending_meta = {
            "radiation_db": year_bounds.radiation_db,
            "start_year": params.start_year,
            "end_year": params.end_year,
        }
        self._worker.start()

    def _on_worker_progress(self, msg: str):
        self.terminal_panel.set_status(msg)
        if self._progress:
            self._progress.setLabelText(msg)

    def _on_worker_finished(self, sim_result, figures):
        if self._progress:
            self._progress.close()
            self._progress = None
        self._act_simulate.setEnabled(True)
        elapsed = time.time() - getattr(self, "_sim_t0", time.time())
        n_hours = len(sim_result.energy_result.hourly_production)
        meta = getattr(self, "_pending_meta", {})
        self._last_sim_meta = {**meta, "hours": n_hours, "elapsed_sec": elapsed}
        self.last_graph_sel = getattr(self, "_pending_graph_sel", None)
        self.on_simulation_finished(sim_result, figures, self.last_graph_sel)

    def _on_worker_failed(self, err):
        if self._progress:
            self._progress.close()
            self._progress = None
        self._act_simulate.setEnabled(True)
        self.on_error_caught(err)

    def on_simulation_finished(self, res, figures, graph_sel=None):
        self.terminal_panel.set_status("Complete")
        self.terminal_panel.append_text(res.formatted_text)
        meta = self._last_sim_meta
        if meta:
            self.terminal_panel.append_text(
                f"\n[PVGIS: {meta.get('radiation_db', '?')} | "
                f"{meta.get('start_year')}–{meta.get('end_year')} | "
                f"{meta.get('hours', 0):,} hours | "
                f"{meta.get('elapsed_sec', 0):.1f}s]\n"
            )
        self.last_sim_result_text = res.formatted_text
        energy = res.energy_result
        self.last_sim_result = energy
        self._mark_dirty()
        self._act_open_charts.setEnabled(True)

        prefs = AppPreferences.load()
        if (
            graph_sel and graph_sel.generate_graphs
            and energy.hourly_production
            and prefs.chart_auto_open
        ):
            self.graph_dlg = GraphDialog(energy, graph_sel, parent=self)
            self.graph_dlg.show()

    def on_export_requested(self):
        if not self.last_sim_result_text:
            ErrorNotificationWindow.show_error(
                self, "Export Error", "No simulation results to export."
            )
            return
        ExportHandler.export_results(
            self, self.last_sim_result_text, self.last_sim_result,
        )

    def on_error_caught(self, err):
        self.terminal_panel.set_status("Error")
        ErrorNotificationWindow.show_error(self, err.__class__.__name__, str(err))

    def closeEvent(self, event):
        if self._unsaved_changes:
            if not self._confirm_discard():
                event.ignore()
                return
        event.accept()
