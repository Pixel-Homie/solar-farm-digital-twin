"""Tool buttons with idle/active SVG states (press, hover, checked)."""

from typing import Callable

from PyQt5.QtCore import Qt, QSize, QObject, QEvent, QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QToolButton, QMenu, QWidget


class IconStateFilter(QObject):
    """Swap icon on press (active) and release/hover-leave (idle)."""

    def __init__(self, button: QToolButton, apply_fn: Callable[[str], None]):
        super().__init__(button)
        self._button = button
        self._apply = apply_fn
        button.installEventFilter(self)
        self._apply("idle")

    def eventFilter(self, obj, event):
        if obj is self._button:
            if event.type() == QEvent.MouseButtonPress:
                self._apply("active")
            elif event.type() in (QEvent.MouseButtonRelease, QEvent.Leave):
                if self._button.isCheckable() and self._button.isChecked():
                    self._apply("active")
                else:
                    self._apply("idle")
        return False


class IconStateButton(QToolButton):
    """Square icon button — active while pressed; optional checkable active state."""

    def __init__(
        self,
        icon_fn: Callable[[str], QIcon],
        size: int = 32,
        parent=None,
    ):
        super().__init__(parent)
        self._icon_fn = icon_fn
        self._px = size
        self.setFixedSize(size, size)
        self.setAutoRaise(True)
        self.setStyleSheet(
            "QToolButton { border: none; background: transparent; padding: 0; margin: 0; }"
        )

        def apply_state(state: str):
            self.setIcon(self._icon_fn(state))
            self.setIconSize(QSize(self._px, self._px))

        self._state_filter = IconStateFilter(self, apply_state)
        apply_state("idle")

    def set_visual_checked(self, checked: bool):
        state = "active" if checked else "idle"
        self.setIcon(self._icon_fn(state))
        self.setIconSize(QSize(self._px, self._px))


class TextMenuButton(QToolButton):
    """Top menu label — opens a standalone QMenu safely on frameless windows."""

    def __init__(self, label: str, menu: QMenu, parent=None):
        super().__init__(parent)
        self.setObjectName("ChromeMenuButton")
        self.setText(label)
        self.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.setCursor(Qt.PointingHandCursor)
        self.setAutoRaise(True)
        self._menu = menu
        self.clicked.connect(self._open_menu)

    def _open_menu(self):
        if self._menu is None:
            return
        win = self.window()
        if win is not None:
            self._menu.setParent(win)
        pos = self.mapToGlobal(QPoint(0, self.height()))
        self._menu.popup(pos)


def clone_menu(source: QMenu, parent: QWidget) -> QMenu:
    """Copy menu structure; re-use QAction instances (safe for triggers)."""
    menu = QMenu(parent)
    for action in source.actions():
        if action.isSeparator():
            menu.addSeparator()
        elif action.menu() is not None:
            sub = clone_menu(action.menu(), parent)
            sub.setTitle(action.text())
            menu.addMenu(sub)
        else:
            menu.addAction(action)
    return menu
