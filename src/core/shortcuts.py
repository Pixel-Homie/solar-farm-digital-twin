"""Configurable keyboard shortcuts for registered QActions."""

from typing import Dict, Optional

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction

from src.core.preferences import SHORTCUT_DEFINITIONS, AppPreferences


class ShortcutManager:
    def __init__(self):
        self._actions: Dict[str, QAction] = {}
        self._base_tooltips: Dict[str, str] = {}

    def register(self, action_id: str, action: QAction, base_tooltip: str = ""):
        self._actions[action_id] = action
        label = SHORTCUT_DEFINITIONS.get(action_id, (action_id, ""))[0]
        self._base_tooltips[action_id] = base_tooltip or action.toolTip() or label

    def apply_all(self, prefs: AppPreferences):
        for action_id, action in self._actions.items():
            seq_str = prefs.shortcuts.get(
                action_id,
                SHORTCUT_DEFINITIONS.get(action_id, ("", ""))[1],
            )
            if seq_str and seq_str.strip():
                action.setShortcut(QKeySequence(seq_str))
            else:
                action.setShortcut(QKeySequence())
            base = self._base_tooltips.get(action_id, "")
            key_display = seq_str if seq_str else "—"
            if base:
                action.setToolTip(f"{base}  ({key_display})")
            else:
                action.setToolTip(key_display)

    def get_action(self, action_id: str) -> Optional[QAction]:
        return self._actions.get(action_id)
