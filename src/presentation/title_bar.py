"""Application chrome — logo row, menus, workshop toolbar."""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy,
    QPushButton, QFrame, QButtonGroup,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent

from src.presentation.icon_button import IconStateButton, TextMenuButton
from src.presentation.ui_assets import app_logo_pixmap, window_control_icon, workshop_icon_fn

_WIN_BTN_PX = 36
_CHROME_H = 48
_WORKSHOP_H = 48
_TOOL_PX = 32


def _v_separator() -> QFrame:
    line = QFrame()
    line.setObjectName("ChromeSeparator")
    line.setFrameShape(QFrame.VLine)
    line.setFrameShadow(QFrame.Plain)
    line.setFixedWidth(1)
    return line


class _DragStrip(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AppDragStrip")
        self._drag_pos = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setCursor(Qt.SizeAllCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            win = self.window()
            if win and win.windowFlags() & Qt.FramelessWindowHint:
                self._drag_pos = event.globalPos() - win.frameGeometry().topLeft()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton and self._drag_pos is not None:
            win = self.window()
            if win:
                win.move(event.globalPos() - self._drag_pos)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            win = self.window()
            if win:
                win.showNormal() if win.isMaximized() else win.showMaximized()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)


class AppChromeBar(QWidget):
    """Row 1: logo | Project View Window Settings Help | drag | − = ×"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AppTitleBar")
        self.setFixedHeight(_CHROME_H)
        self.setMinimumHeight(_CHROME_H)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 6, 0)
        lay.setSpacing(0)

        self._logo_box = QWidget()
        self._logo_box.setObjectName("LogoContainer")
        logo_lay = QHBoxLayout(self._logo_box)
        logo_lay.setContentsMargins(0, 0, 0, 0)
        logo_lay.setSpacing(0)
        self._logo = QLabel()
        self._logo.setObjectName("AppLogoLabel")
        self._logo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        logo_lay.addWidget(self._logo, 0, Qt.AlignLeft)
        self._refresh_logo()
        lay.addWidget(self._logo_box, 0, Qt.AlignLeft | Qt.AlignTop)

        lay.addSpacing(6)
        lay.addWidget(_v_separator())

        self._menu_strip = QHBoxLayout()
        self._menu_strip.setSpacing(2)
        lay.addLayout(self._menu_strip)

        lay.addWidget(_DragStrip(self), stretch=1)

        controls = QHBoxLayout()
        controls.setSpacing(2)
        self._btn_min = IconStateButton(
            lambda s: window_control_icon("minimize", s, _WIN_BTN_PX),
            size=_WIN_BTN_PX,
        )
        self._btn_min.setObjectName("WindowControlButton")
        self._btn_min.clicked.connect(self._on_minimize)
        self._btn_max = IconStateButton(
            lambda s: window_control_icon("maximize", s, _WIN_BTN_PX),
            size=_WIN_BTN_PX,
        )
        self._btn_max.setObjectName("WindowControlButton")
        self._btn_max.clicked.connect(self._on_maximize)
        self._btn_close = IconStateButton(
            lambda s: window_control_icon("close", s, _WIN_BTN_PX),
            size=_WIN_BTN_PX,
        )
        self._btn_close.setObjectName("WindowControlButton")
        self._btn_close.clicked.connect(self._on_close)
        controls.addWidget(self._btn_min)
        controls.addWidget(self._btn_max)
        controls.addWidget(self._btn_close)
        lay.addLayout(controls)

    def _refresh_logo(self):
        pm = app_logo_pixmap()
        if pm.isNull():
            self._logo_box.hide()
            return
        self._logo_box.show()
        self._logo.setPixmap(pm)
        self._logo.setFixedSize(pm.width(), pm.height())
        self._logo_box.setFixedSize(pm.width(), pm.height())

    def setup_menu_buttons(self, entries: list):
        while self._menu_strip.count():
            item = self._menu_strip.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for title, menu in entries:
            self._menu_strip.addWidget(TextMenuButton(title, menu, self))

    def _on_minimize(self):
        self.window().showMinimized()

    def _on_maximize(self):
        w = self.window()
        if w.isMaximized():
            w.showNormal()
        else:
            w.showMaximized()

    def _on_close(self):
        self.window().close()


class WorkshopToolbar(QWidget):
    """Row 2: select, zoom, grid, text, wire, delete + Simulate."""

    mode_changed = pyqtSignal(int)
    grid_toggled = pyqtSignal(bool)

    MODE_SELECT = 0
    MODE_WIRE = 1
    MODE_DELETE = 2
    MODE_ZOOM = 3
    MODE_TEXT = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WorkshopToolbar")
        self.setFixedHeight(_WORKSHOP_H)
        self.setMinimumHeight(_WORKSHOP_H)

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(6)

        tools = QHBoxLayout()
        tools.setSpacing(4)

        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)
        self._mode_buttons: dict[int, IconStateButton] = {}
        self._current_mode = self.MODE_SELECT

        mode_specs = (
            ("select", self.MODE_SELECT, "Select / move components (Del removes selection)"),
            ("zoom", self.MODE_ZOOM, "Zoom — click or scroll wheel"),
            ("grid", None, "Toggle workspace grid"),
            ("text", self.MODE_TEXT, "Click to add text — double-click to edit"),
            ("wire", self.MODE_WIRE, "Draw connections between components"),
            ("delete", self.MODE_DELETE, "Click items on the canvas to remove them"),
        )

        for key, mode_id, tip in mode_specs:
            if key == "grid":
                self._btn_grid = IconStateButton(workshop_icon_fn("grid", _TOOL_PX), size=_TOOL_PX)
                self._btn_grid.setObjectName("WorkshopToolButton")
                self._btn_grid.setCheckable(True)
                self._btn_grid.setChecked(True)
                self._btn_grid.setToolTip(tip)
                self._btn_grid.set_visual_checked(True)
                self._btn_grid.clicked.connect(self._on_grid)
                tools.addWidget(self._btn_grid)
                continue
            btn = IconStateButton(workshop_icon_fn(key, _TOOL_PX), size=_TOOL_PX)
            btn.setObjectName("WorkshopToolButton")
            btn.setCheckable(True)
            btn.setToolTip(tip)
            btn.clicked.connect(
                lambda checked, m=mode_id, b=btn: self._select_mode(m, b, checked)
            )
            self._mode_group.addButton(btn)
            self._mode_buttons[mode_id] = btn
            tools.addWidget(btn)

        root.addLayout(tools, stretch=1)

        self._btn_simulate = QPushButton("Simulate")
        self._btn_simulate.setObjectName("SimulateButton")
        self._btn_simulate.setFixedHeight(36)
        self._btn_simulate.setMinimumWidth(108)
        root.addWidget(self._btn_simulate, 0, Qt.AlignVCenter)

        root.addStretch(1)

        self._mode_buttons[self.MODE_SELECT].setChecked(True)
        self._mode_buttons[self.MODE_SELECT].set_visual_checked(True)

    def simulate_button(self) -> QPushButton:
        return self._btn_simulate

    def set_mode(self, mode_id: int):
        btn = self._mode_buttons.get(mode_id)
        if btn:
            btn.setChecked(True)
            self._select_mode(mode_id, btn, True)

    def _select_mode(self, mode_id: int, button: IconStateButton, checked: bool):
        if not checked:
            button.setChecked(True)
            return
        self._current_mode = mode_id
        for mid, btn in self._mode_buttons.items():
            btn.set_visual_checked(mid == mode_id)
        self.mode_changed.emit(mode_id)

    def _on_grid(self, checked: bool):
        self._btn_grid.set_visual_checked(checked)
        self.grid_toggled.emit(checked)


class DockTitleBar(QWidget):
    def __init__(self, title: str, dock_widget, parent=None):
        super().__init__(parent)
        self.setObjectName("DockTitleBar")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 4, 4, 4)
        self._label = QLabel(title)
        self._label.setObjectName("DockTitleLabel")
        self._label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        lay.addWidget(self._label)

        hide_btn = QPushButton("−")
        hide_btn.setObjectName("DockHideButton")
        hide_btn.setFixedSize(22, 22)
        hide_btn.setToolTip("Hide panel (open from Window menu)")
        hide_btn.clicked.connect(dock_widget.hide)
        lay.addWidget(hide_btn)


class AppChromeContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AppChromeContainer")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.chrome_bar = AppChromeBar(self)
        self.workshop = WorkshopToolbar(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.chrome_bar)
        lay.addWidget(self.workshop)
