"""Application preferences — defaults and QSettings persistence."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from PyQt5.QtCore import QSettings

from src.core.theme import normalize_theme

ORG = "SolarTwin"
APP = "App"

# action_id -> (label, default portable key sequence)
SHORTCUT_DEFINITIONS: Dict[str, Tuple[str, str]] = {
    "new_project": ("New project", "Ctrl+N"),
    "open_project": ("Open project", "Ctrl+O"),
    "save_project": ("Save project", "Ctrl+S"),
    "save_as": ("Save project as", "Ctrl+Shift+S"),
    "export_results": ("Export results", "Ctrl+E"),
    "quit": ("Quit", "Ctrl+Q"),
    "preferences": ("Preferences", "Ctrl+,"),
    "simulate": ("Run simulation", "F5"),
    "open_charts": ("Open simulation charts", "Ctrl+G"),
    "mode_select": ("Select mode", "S"),
    "mode_wire": ("Wire mode", "W"),
    "mode_delete": ("Delete mode", "Del"),
    "escape_select": ("Return to select mode", "Esc"),
}

CHART_STYLES = ["Curve", "Bars", "Filled area", "Striped fill"]
EXPORT_FORMATS = ["txt", "csv", "report"]


@dataclass
class AppPreferences:
    theme: str = "charcoal"
    terminal_font_size: int = 10
    system_loss_pct: float = 14.0
    pvgis_timeout_sec: int = 30
    battery_idle_loss_pct: float = 0.0
    base_load_kw: float = 2.0
    load_profile: str = "constant"
    require_wired_to_battery: bool = True
    battery_charge_efficiency: float = 0.95
    battery_discharge_efficiency: float = 0.95
    battery_max_c_rate: float = 0.5
    chart_auto_open: bool = True
    chart_default_style: str = "Bars"
    graph_power: bool = True
    graph_soc: bool = True
    graph_monthly: bool = True
    export_format: str = "txt"
    map_last_lat: float = 28.0
    map_last_lon: float = 3.0
    shortcuts: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.shortcuts:
            self.shortcuts = {
                aid: default for aid, (_, default) in SHORTCUT_DEFINITIONS.items()
            }

    @classmethod
    def load(cls) -> "AppPreferences":
        s = QSettings(ORG, APP)
        shortcuts = {}
        for aid, (_, default) in SHORTCUT_DEFINITIONS.items():
            shortcuts[aid] = s.value(f"shortcut/{aid}", default, type=str) or default

        return cls(
            theme=normalize_theme(s.value("theme", "charcoal", type=str) or "charcoal"),
            terminal_font_size=int(s.value("terminal_font_size", 10)),
            system_loss_pct=float(s.value("system_loss_pct", 14.0)),
            pvgis_timeout_sec=int(s.value("pvgis_timeout_sec", 30)),
            battery_idle_loss_pct=float(s.value("battery_idle_loss_pct", 0.0)),
            base_load_kw=float(s.value("base_load_kw", 2.0)),
            load_profile=s.value("load_profile", "constant", type=str) or "constant",
            require_wired_to_battery=s.value("require_wired_to_battery", True, type=bool),
            battery_charge_efficiency=float(s.value("battery_charge_efficiency", 0.95)),
            battery_discharge_efficiency=float(s.value("battery_discharge_efficiency", 0.95)),
            battery_max_c_rate=float(s.value("battery_max_c_rate", 0.5)),
            chart_auto_open=s.value("chart_auto_open", True, type=bool),
            chart_default_style=s.value("chart_default_style", "Bars", type=str) or "Bars",
            graph_power=s.value("graph_power", True, type=bool),
            graph_soc=s.value("graph_soc", True, type=bool),
            graph_monthly=s.value("graph_monthly", True, type=bool),
            export_format=s.value("export_format", "txt", type=str) or "txt",
            map_last_lat=float(s.value("map_last_lat", 28.0)),
            map_last_lon=float(s.value("map_last_lon", 3.0)),
            shortcuts=shortcuts,
        )

    def save(self):
        s = QSettings(ORG, APP)
        s.setValue("theme", self.theme)
        s.setValue("terminal_font_size", self.terminal_font_size)
        s.setValue("system_loss_pct", self.system_loss_pct)
        s.setValue("pvgis_timeout_sec", self.pvgis_timeout_sec)
        s.setValue("battery_idle_loss_pct", self.battery_idle_loss_pct)
        s.setValue("base_load_kw", self.base_load_kw)
        s.setValue("load_profile", self.load_profile)
        s.setValue("require_wired_to_battery", self.require_wired_to_battery)
        s.setValue("battery_charge_efficiency", self.battery_charge_efficiency)
        s.setValue("battery_discharge_efficiency", self.battery_discharge_efficiency)
        s.setValue("battery_max_c_rate", self.battery_max_c_rate)
        s.setValue("chart_auto_open", self.chart_auto_open)
        s.setValue("chart_default_style", self.chart_default_style)
        s.setValue("graph_power", self.graph_power)
        s.setValue("graph_soc", self.graph_soc)
        s.setValue("graph_monthly", self.graph_monthly)
        s.setValue("export_format", self.export_format)
        s.setValue("map_last_lat", self.map_last_lat)
        s.setValue("map_last_lon", self.map_last_lon)
        for aid, seq in self.shortcuts.items():
            s.setValue(f"shortcut/{aid}", seq)

    def reset_shortcuts(self):
        self.shortcuts = {
            aid: default for aid, (_, default) in SHORTCUT_DEFINITIONS.items()
        }

    @staticmethod
    def default_shortcuts() -> Dict[str, str]:
        return {aid: default for aid, (_, default) in SHORTCUT_DEFINITIONS.items()}

    def find_duplicate_shortcuts(self) -> List[Tuple[str, str, List[str]]]:
        """Return list of (sequence, first_id, [all_ids]) for duplicates."""
        by_seq: Dict[str, List[str]] = {}
        for aid, seq in self.shortcuts.items():
            key = (seq or "").strip()
            if not key:
                continue
            by_seq.setdefault(key, []).append(aid)
        dups = []
        for seq, aids in by_seq.items():
            if len(aids) > 1:
                dups.append((seq, aids[0], aids))
        return dups
