"""
theme.py — Application-wide QSS stylesheets.
Apply with: QApplication.instance().setStyleSheet(THEMES['default'])
"""

_SCROLLBAR_DEFAULT = """
        QScrollBar:horizontal {
            background: #181825;
            height: 10px;
            margin: 0;
        }
        QScrollBar::handle:horizontal {
            background: #45475a;
            border-radius: 5px;
            min-width: 24px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0; height: 0;
        }
        QAbstractScrollArea::corner {
            background: #11111b;
        }
"""

_SCROLLBAR_CHARCOAL = """
        QScrollBar:horizontal {
            background: #323232;
            height: 8px;
        }
        QScrollBar::handle:horizontal {
            background: #808080;
            border-radius: 4px;
            min-width: 24px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0; height: 0;
        }
        QAbstractScrollArea::corner {
            background: #292929;
        }
"""

_TITLEBAR_COMMON = """
        QWidget#AppTitleBar {
            border-bottom: 1px solid #45475a;
        }
        QLabel#AppTitleLabel {
            font-weight: bold;
        }
        QToolButton#WindowControlButton, QToolButton#DockCloseButton {
            border: none;
            background: transparent;
            padding: 0;
            margin: 0;
        }
        QLabel#AppLogoLabel {
            background: transparent;
            padding: 0;
            margin: 0;
        }
        QWidget#LogoContainer {
            background: transparent;
            padding: 0;
            margin: 0;
        }
"""

_TITLEBAR_CHARCOAL = _TITLEBAR_COMMON + """
        QWidget#AppChromeContainer {
            background-color: #323232;
        }
        QWidget#AppTitleBar {
            background-color: #323232;
            border-bottom: 1px solid #808080;
        }
        QWidget#AppDragStrip {
            background: transparent;
        }
        QToolBar#WorkshopToolbar, QWidget#WorkshopToolbar {
            background-color: #323232;
            border-bottom: 1px solid #808080;
            spacing: 6px;
            padding: 4px 8px;
        }
        QToolBar#WorkshopToolbar QToolButton, QWidget#WorkshopToolbar QToolButton {
            background: transparent;
            border: none;
            padding: 2px;
        }
        QWidget#DockTitleBar {
            background-color: #323232;
            border-bottom: 1px solid #808080;
            min-height: 28px;
        }
        QLabel#DockTitleLabel {
            color: #808080;
            font-weight: bold;
            text-transform: lowercase;
        }
"""

_TITLEBAR_LIGHT = _TITLEBAR_COMMON + """
        QWidget#AppChromeContainer {
            background-color: #f0f0f0;
        }
        QWidget#AppTitleBar {
            background-color: #f0f0f0;
            border-bottom: 1px solid #d0d0d0;
        }
        QWidget#AppDragStrip {
            background: transparent;
        }
        QToolBar#WorkshopToolbar, QWidget#WorkshopToolbar {
            background-color: #f0f0f0;
            border-bottom: 1px solid #d0d0d0;
            spacing: 6px;
            padding: 4px 8px;
        }
        QToolBar#WorkshopToolbar QToolButton, QWidget#WorkshopToolbar QToolButton {
            background: transparent;
            border: none;
            padding: 2px;
        }
        QWidget#DockTitleBar {
            background-color: #e8e8e8;
            border-bottom: 1px solid #d0d0d0;
            min-height: 28px;
        }
        QLabel#DockTitleLabel {
            color: #1a1a1a;
            font-weight: bold;
        }
"""

_TITLEBAR_BLACK = _TITLEBAR_COMMON + """
        QWidget#AppChromeContainer {
            background-color: #1a1a1a;
        }
        QWidget#AppTitleBar {
            background-color: #1a1a1a;
            border-bottom: 1px solid #333333;
        }
        QWidget#AppDragStrip {
            background: transparent;
        }
        QToolBar#WorkshopToolbar, QWidget#WorkshopToolbar {
            background-color: #1a1a1a;
            border-bottom: 1px solid #333333;
            spacing: 6px;
            padding: 4px 8px;
        }
        QToolBar#WorkshopToolbar QToolButton, QWidget#WorkshopToolbar QToolButton {
            background: transparent;
            border: none;
            padding: 2px;
        }
        QLabel#AppTitleLabel {
            color: #e0e0e0;
        }
        QWidget#DockTitleBar {
            background-color: #222222;
            border-bottom: 1px solid #333333;
            min-height: 28px;
        }
        QLabel#DockTitleLabel {
            color: #e0e0e0;
            font-weight: bold;
        }
"""

_SCROLLBAR_LIGHT = """
        QScrollBar:horizontal {
            background: #e8e8e8;
            height: 8px;
        }
        QScrollBar::handle:horizontal {
            background: #b0b0b0;
            border-radius: 4px;
            min-width: 24px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0; height: 0;
        }
        QAbstractScrollArea::corner {
            background: #f5f5f5;
        }
"""

_SCROLLBAR_BLACK = """
        QScrollBar:horizontal {
            background: #1a1a1a;
            height: 8px;
        }
        QScrollBar::handle:horizontal {
            background: #444444;
            border-radius: 4px;
            min-width: 24px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0; height: 0;
        }
        QAbstractScrollArea::corner {
            background: #0d0d0d;
        }
"""

THEME_ALIASES = {
    "default": "charcoal",
    "design": "charcoal",
    "dark": "black",
}

_PANEL_BORDERS_CHARCOAL = """
        QDockWidget#CatalogueDock {
            border: 1px solid #5a7a9a;
        }
        QDockWidget#PropertiesDock {
            border: 1px solid #9d88bf;
        }
        QDockWidget#TerminalDock {
            border: 1px solid #5dbe85;
        }
        QFrame#ChromeSeparator {
            background: #808080;
            max-width: 1px;
        }
        QToolButton#ChromeMenuButton {
            background: transparent;
            color: #808080;
            border: none;
            padding: 6px 12px;
            font-size: 12px;
        }
        QToolButton#ChromeMenuButton:hover {
            background: #292929;
            color: #cccccc;
        }
        QToolButton#ChromeMenuButton::menu-indicator {
            image: none;
            width: 0;
        }
        QToolButton#WorkshopToolButton {
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 2px;
        }
        QToolButton#WorkshopToolButton:checked {
            background-color: #292929;
            border: 1px solid #808080;
        }
        QToolButton#PanelToggleButton {
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 2px;
        }
        QToolButton#PanelToggleButton:checked {
            background-color: #292929;
            border: 1px solid #5dbe85;
        }
"""

_PANEL_BORDERS_LIGHT = """
        QDockWidget#CatalogueDock {
            border: 1px solid #7a9ec4;
        }
        QDockWidget#PropertiesDock {
            border: 1px solid #b39ddb;
        }
        QDockWidget#TerminalDock {
            border: 1px solid #81c784;
        }
        QFrame#ChromeSeparator {
            background: #cccccc;
            max-width: 1px;
        }
        QToolButton#ChromeMenuButton {
            background: transparent;
            color: #333333;
            border: none;
            padding: 6px 12px;
            font-size: 12px;
        }
        QToolButton#ChromeMenuButton:hover {
            background: #e8e8e8;
            color: #1a1a1a;
        }
        QToolButton#ChromeMenuButton::menu-indicator {
            image: none;
            width: 0;
        }
        QToolButton#WorkshopToolButton {
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 2px;
        }
        QToolButton#WorkshopToolButton:checked {
            background-color: #e0e0e0;
            border: 1px solid #666666;
        }
        QToolButton#PanelToggleButton {
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 2px;
        }
        QToolButton#PanelToggleButton:checked {
            background-color: #e8f5e9;
            border: 1px solid #81c784;
        }
"""

THEMES = {
    "charcoal": """
        QMainWindow, QWidget, QDialog {
            background-color: #323232;
            color: #808080;
        }
        QMenuBar {
            background-color: #323232;
            color: #808080;
            border-bottom: 1px solid #808080;
        }
        QMenuBar::item:selected { background: #292929; }
        QMenu {
            background-color: #323232;
            color: #808080;
            border: 1px solid #808080;
        }
        QMenu::item:selected { background: #292929; }
        QToolBar {
            background-color: #323232;
            border: none;
            spacing: 4px;
        }
        QDockWidget {
            color: #808080;
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
        }
        QDockWidget::title {
            height: 0px;
            padding: 0px;
            background: transparent;
        }
        CataloguePanel, PropertiesPanel, TerminalPanel {
            background-color: #323232;
            color: #808080;
        }
        QGraphicsView {
            background-color: #292929;
            border: 1px solid #808080;
        }
        QListWidget {
            background-color: #292929;
            color: #808080;
            border: none;
        }
        QListWidget::item { padding: 6px; }
        QListWidget::item:selected { background: #323232; border: 1px solid #808080; }
        QListWidget::item:hover { background: #323232; }
        QPushButton {
            background-color: #292929;
            color: #808080;
            border: 1px solid #808080;
            border-radius: 14px;
            padding: 4px 12px;
        }
        QPushButton:hover { background-color: #323232; }
        QPushButton:pressed { background-color: #292929; }
        QPushButton:checked { background-color: #323232; border: 1px solid #808080; }
        QToolButton {
            background-color: transparent;
            border: none;
            border-radius: 4px;
            padding: 4px;
        }
        QToolButton:checked { background-color: #292929; }
        QPushButton#SimulateButton {
            background-color: #292929;
            color: #808080;
            border: 1px solid #808080;
            border-radius: 16px;
            padding: 6px 22px;
            font-weight: bold;
            min-height: 28px;
        }
        QPushButton#SimulateButton:hover {
            background-color: #323232;
            color: #808080;
        }
        QPushButton#SimulateButton:pressed {
            background-color: #292929;
        }
        QPushButton#SimulateButton:disabled {
            color: #505050;
            background-color: #292929;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox {
            background-color: #292929;
            color: #808080;
            border: 1px solid #808080;
            border-radius: 14px;
            padding: 4px 10px;
        }
        QTextEdit, QPlainTextEdit {
            background-color: #292929;
            color: #808080;
            border: none;
            font-family: Consolas, monospace;
        }
        QLabel { color: #808080; }
        QLabel#SectionLabel, QLabel#sectionTitle {
            color: #808080;
            font-weight: bold;
            font-size: 11px;
        }
        QFrame#CatalogueDivider {
            color: #808080;
            max-height: 1px;
        }
        QCheckBox { color: #808080; }
        QComboBox {
            background: #292929;
            color: #808080;
            border: 1px solid #808080;
            border-radius: 8px;
            padding: 2px 8px;
        }
        QScrollBar:vertical {
            background: #323232;
            width: 8px;
        }
        QScrollBar::handle:vertical {
            background: #808080;
            border-radius: 4px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
""" + _SCROLLBAR_CHARCOAL + _TITLEBAR_CHARCOAL + _PANEL_BORDERS_CHARCOAL + """
        ColorTagButton {
            border-radius: 8px;
            min-width: 28px;
            min-height: 28px;
        }
    """,

    "light": """
        QMainWindow, QWidget, QDialog {
            background-color: #f5f5f5;
            color: #333333;
        }
        QMenuBar {
            background-color: #f0f0f0;
            color: #1a1a1a;
            border-bottom: 1px solid #d0d0d0;
        }
        QMenuBar::item:selected { background: #e0e0e0; }
        QMenu {
            background-color: #ffffff;
            color: #1a1a1a;
            border: 1px solid #d0d0d0;
        }
        QMenu::item:selected { background: #e8e8e8; }
        QToolBar {
            background-color: #f0f0f0;
            border-bottom: 1px solid #d0d0d0;
            spacing: 4px;
        }
        QDockWidget { color: #1a1a1a; }
        QDockWidget::title {
            height: 0px;
            padding: 0px;
            background: transparent;
        }
        CataloguePanel, PropertiesPanel, TerminalPanel {
            background-color: #f5f5f5;
            color: #333333;
        }
        QGraphicsView {
            background-color: #ffffff;
            border: 1px solid #cccccc;
        }
        QListWidget {
            background-color: #ffffff;
            color: #1a1a1a;
            border: none;
        }
        QListWidget::item { padding: 6px; }
        QListWidget::item:selected { background: #d8e4f0; }
        QListWidget::item:hover { background: #ececec; }
        QPushButton {
            background-color: #ffffff;
            color: #1a1a1a;
            border: 1px solid #cccccc;
            border-radius: 14px;
            padding: 4px 12px;
        }
        QPushButton:hover { background-color: #ececec; }
        QPushButton:pressed { background-color: #dddddd; }
        QPushButton:checked { background-color: #d0d0d0; border: 1px solid #999999; }
        QToolButton {
            background-color: #f0f0f0;
            border: none;
            border-radius: 4px;
            padding: 4px;
        }
        QToolButton:checked { background-color: #d0d0d0; }
        QToolBar#MainToolbar QToolButton {
            background-color: transparent;
            border: none;
            padding: 4px;
        }
        QPushButton#SimulateButton {
            background-color: #2d6a4f;
            color: #ffffff;
            border: 1px solid #1b4332;
            border-radius: 16px;
            padding: 6px 22px;
            font-weight: bold;
            min-height: 28px;
        }
        QPushButton#SimulateButton:hover { background-color: #40916c; }
        QPushButton#SimulateButton:pressed { background-color: #1b4332; }
        QPushButton#SimulateButton:disabled {
            color: #888888;
            background-color: #cccccc;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox {
            background-color: #ffffff;
            color: #1a1a1a;
            border: 1px solid #cccccc;
            border-radius: 14px;
            padding: 4px 10px;
        }
        QTextEdit, QPlainTextEdit {
            background-color: #fafafa;
            color: #1a472a;
            border: none;
            font-family: Consolas, monospace;
        }
        QLabel { color: #333333; }
        QLabel#SectionLabel, QLabel#sectionTitle {
            color: #1a1a1a;
            font-weight: bold;
            font-size: 11px;
        }
        QFrame#CatalogueDivider { color: #d0d0d0; max-height: 1px; }
        QCheckBox { color: #333333; }
        QComboBox {
            background: #ffffff;
            color: #1a1a1a;
            border: 1px solid #cccccc;
            border-radius: 8px;
            padding: 2px 8px;
        }
        QScrollBar:vertical {
            background: #f0f0f0;
            width: 8px;
        }
        QScrollBar::handle:vertical {
            background: #b0b0b0;
            border-radius: 4px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    """ + _SCROLLBAR_LIGHT + _TITLEBAR_LIGHT + _PANEL_BORDERS_LIGHT + """
        ColorTagButton {
            border-radius: 8px;
            min-width: 28px;
            min-height: 28px;
        }
    """,

    "black": """
        QMainWindow, QWidget, QDialog {
            background-color: #141414;
            color: #b0b0b0;
        }
        QMenuBar {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border-bottom: 1px solid #333333;
        }
        QMenuBar::item:selected { background: #2a2a2a; }
        QMenu {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border: 1px solid #333333;
        }
        QMenu::item:selected { background: #2a2a2a; }
        QToolBar {
            background-color: #1a1a1a;
            border-bottom: 1px solid #333333;
            spacing: 4px;
        }
        QDockWidget {
            color: #e0e0e0;
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
        }
        QDockWidget::title {
            height: 0px;
            padding: 0px;
            background: transparent;
        }
        CataloguePanel, PropertiesPanel, TerminalPanel {
            background-color: #141414;
            color: #b0b0b0;
        }
        QGraphicsView {
            background-color: #0d0d0d;
            border: 1px solid #333333;
        }
        QListWidget {
            background-color: #0d0d0d;
            color: #e0e0e0;
            border: none;
        }
        QListWidget::item { padding: 6px; }
        QListWidget::item:selected { background: #2a2a2a; }
        QListWidget::item:hover { background: #222222; }
        QPushButton {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border: 1px solid #333333;
            border-radius: 14px;
            padding: 4px 12px;
        }
        QPushButton:hover { background-color: #2a2a2a; }
        QPushButton:pressed { background-color: #333333; }
        QPushButton:checked { background-color: #333333; border: 1px solid #555555; }
        QToolButton {
            background-color: #1a1a1a;
            border: none;
            border-radius: 4px;
            padding: 4px;
        }
        QToolButton:checked { background-color: #333333; }
        QToolBar#MainToolbar QToolButton {
            background-color: transparent;
            border: none;
            padding: 4px;
        }
        QPushButton#SimulateButton {
            background-color: #333333;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 16px;
            padding: 6px 22px;
            font-weight: bold;
            min-height: 28px;
        }
        QPushButton#SimulateButton:hover { background-color: #444444; }
        QPushButton#SimulateButton:pressed { background-color: #2a2a2a; }
        QPushButton#SimulateButton:disabled {
            color: #666666;
            background-color: #222222;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox {
            background-color: #0d0d0d;
            color: #e0e0e0;
            border: 1px solid #333333;
            border-radius: 14px;
            padding: 4px 10px;
        }
        QTextEdit, QPlainTextEdit {
            background-color: #0d0d0d;
            color: #a8a8a8;
            border: none;
            font-family: Consolas, monospace;
        }
        QLabel { color: #b0b0b0; }
        QLabel#SectionLabel, QLabel#sectionTitle {
            color: #e0e0e0;
            font-weight: bold;
            font-size: 11px;
        }
        QFrame#CatalogueDivider { color: #333333; max-height: 1px; }
        QCheckBox { color: #b0b0b0; }
        QComboBox {
            background: #0d0d0d;
            color: #e0e0e0;
            border: 1px solid #333333;
            border-radius: 8px;
            padding: 2px 8px;
        }
        QScrollBar:vertical {
            background: #1a1a1a;
            width: 8px;
        }
        QScrollBar::handle:vertical {
            background: #444444;
            border-radius: 4px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    """ + _SCROLLBAR_BLACK + _TITLEBAR_BLACK + _PANEL_BORDERS_CHARCOAL + """
        ColorTagButton {
            border-radius: 8px;
            min-width: 28px;
            min-height: 28px;
        }
    """,
}


def normalize_theme(theme: str) -> str:
    """Map legacy keys and validate theme name."""
    theme = THEME_ALIASES.get(theme, theme)
    if theme not in THEMES:
        return "charcoal"
    return theme


# ── Matplotlib chart palettes (match app theme) ─────────────────────────────
CHART_PALETTES = {
    "charcoal": {
        "figure": "#292929",
        "axes": "#323232",
        "grid": "#505050",
        "text": "#cccccc",
        "muted": "#808080",
        "orange": "#e8a54b",
        "green": "#5dbe85",
        "blue": "#6495ce",
        "lavender": "#9d88bf",
        "red": "#f05959",
    },
    "light": {
        "figure": "#f5f5f5",
        "axes": "#ffffff",
        "grid": "#d0d0d0",
        "text": "#1a1a1a",
        "muted": "#555555",
        "orange": "#c45c00",
        "green": "#2d6a4f",
        "blue": "#1d4e89",
        "lavender": "#6c5b7b",
        "red": "#c1121f",
    },
    "black": {
        "figure": "#0d0d0d",
        "axes": "#1a1a1a",
        "grid": "#333333",
        "text": "#e0e0e0",
        "muted": "#888888",
        "orange": "#e8a54b",
        "green": "#5dbe85",
        "blue": "#6495ce",
        "lavender": "#9d88bf",
        "red": "#f05959",
    },
}

_active_chart_palette = CHART_PALETTES["charcoal"]


class _ChartPaletteProxy:
    """Dict-like access so matplotlib code can use _CHART['key'] dynamically."""

    def __getitem__(self, key: str):
        return _active_chart_palette[key]

    def get(self, key: str, default=None):
        return _active_chart_palette.get(key, default)


def get_chart_palette() -> dict:
    return _active_chart_palette


def apply_active_chart_palette(theme: str) -> dict:
    global _active_chart_palette
    key = normalize_theme(theme)
    _active_chart_palette = CHART_PALETTES.get(key, CHART_PALETTES["charcoal"])
    return _active_chart_palette


def chart_dialog_stylesheet(theme: str = None) -> str:
    """QSS for chart / preferences dialogs — matches chart palette (no white strips)."""
    key = normalize_theme(theme or "charcoal")
    p = CHART_PALETTES.get(key, CHART_PALETTES["charcoal"])
    return f"""
        QDialog {{
            background-color: {p['figure']};
            color: {p['text']};
        }}
        QWidget {{
            background-color: {p['figure']};
            color: {p['text']};
        }}
        QWidget#ChartTabPage, QWidget#ChartControlsBar, QWidget#ChartCanvasHolder {{
            background-color: {p['axes']};
            color: {p['text']};
        }}
        QWidget#LogoContainer {{
            background: transparent;
        }}
        QLabel {{
            background: transparent;
            color: {p['text']};
        }}
        QLabel#ChartHintLabel {{
            color: {p['muted']};
            font-size: 10px;
            background: transparent;
        }}
        QLabel#ChartHeaderLabel {{
            color: {p['text']};
            font-size: 11px;
            background: transparent;
        }}
        QTabWidget::pane {{
            border: 1px solid {p['grid']};
            background: {p['axes']};
            top: -1px;
        }}
        QTabBar::tab {{
            background: {p['figure']};
            color: {p['muted']};
            padding: 6px 14px;
            border: 1px solid {p['grid']};
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background: {p['axes']};
            color: {p['text']};
        }}
        QComboBox, QSpinBox, QDoubleSpinBox {{
            background: {p['axes']};
            color: {p['text']};
            border: 1px solid {p['grid']};
            padding: 3px 8px;
            border-radius: 4px;
        }}
        QComboBox QAbstractItemView {{
            background: {p['axes']};
            color: {p['text']};
            selection-background-color: {p['grid']};
        }}
        QPushButton {{
            background: {p['axes']};
            color: {p['text']};
            border: 1px solid {p['grid']};
            padding: 5px 14px;
            border-radius: 6px;
        }}
        QPushButton:hover {{
            background: {p['grid']};
        }}
        QGroupBox {{
            color: {p['text']};
            border: 1px solid {p['grid']};
            margin-top: 8px;
            padding-top: 8px;
            background: {p['axes']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
        }}
        QCheckBox {{
            color: {p['text']};
            background: transparent;
        }}
        QScrollArea, QScrollArea > QWidget > QWidget {{
            background: {p['figure']};
            border: none;
        }}
        QKeySequenceEdit {{
            background: {p['axes']};
            color: {p['text']};
            border: 1px solid {p['grid']};
        }}
    """


def matplotlib_toolbar_stylesheet(theme: str = None) -> str:
    p = CHART_PALETTES.get(normalize_theme(theme or "charcoal"), CHART_PALETTES["charcoal"])
    return f"""
        QToolBar {{
            background: {p['axes']};
            border: none;
            spacing: 2px;
        }}
        QToolButton {{
            background: transparent;
            color: {p['text']};
            border: none;
            padding: 3px;
        }}
        QToolButton:hover {{
            background: {p['grid']};
        }}
        QLabel {{
            background: {p['axes']};
            color: {p['muted']};
            padding: 2px 6px;
        }}
    """