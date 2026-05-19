import json

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QAbstractItemView, QLineEdit, QToolButton,
    QFormLayout, QDoubleSpinBox, QSpinBox, QButtonGroup,
    QFrame,
)
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal, QSize
from PyQt5.QtGui import QDrag

from src.acquisition.loader import CatalogLoader
from src.core.design_tokens import COLOR_TAGS
from src.presentation.ui_assets import left_panel_icon, color_swatch_icon
from src.presentation.workspace import ComponentItem, ensure_color_tag


class DraggableList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def startDrag(self, supported_actions):
        items = self.selectedItems()
        if not items:
            return
        item = items[0]
        data = item.data(Qt.UserRole)
        if not data:
            return
        mime = QMimeData()
        mime.setText(data)
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec_(Qt.CopyAction)


class _SectionLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("SectionLabel")


class CataloguePanel(QWidget):
    CAT_GENERATION = "generation"
    CAT_STORAGE = "storage"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CataloguePanel")

        self._category = self.CAT_GENERATION
        self._all_items: list[tuple[str, str, str]] = []  # (json, label, category)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        rail = QVBoxLayout()
        rail.setContentsMargins(4, 8, 4, 8)
        rail.setSpacing(6)
        self._rail_buttons: dict[str, QToolButton] = {}
        for key, tip in (
            (self.CAT_STORAGE, "Storage"),
            (self.CAT_GENERATION, "Generation"),
        ):
            btn = QToolButton()
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setToolTip(tip)
            btn.setIcon(left_panel_icon(key, "idle"))
            btn.setIconSize(QSize(28, 28))
            btn.setFixedSize(36, 36)
            btn.clicked.connect(lambda checked, k=key: self._set_category(k))
            rail.addWidget(btn)
            self._rail_buttons[key] = btn
        rail.addStretch()
        root.addLayout(rail)

        body = QVBoxLayout()
        body.setContentsMargins(8, 8, 8, 8)
        body.setSpacing(8)

        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        zoom_btn = QToolButton()
        zoom_btn.setIcon(left_panel_icon("search", size=20))
        zoom_btn.setIconSize(QSize(20, 20))
        zoom_btn.setEnabled(False)
        zoom_btn.setFixedSize(24, 24)
        search_row.addWidget(zoom_btn)

        self._search = QLineEdit()
        self._search.setObjectName("CatalogueSearch")
        self._search.setPlaceholderText("Search Components ....")
        self._search.textChanged.connect(self._apply_filter)
        search_row.addWidget(self._search, stretch=1)
        body.addLayout(search_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("CatalogueDivider")
        sep.setFrameShadow(QFrame.Plain)
        body.addWidget(sep)

        self._empty_label = QLabel("No components in this category.")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setWordWrap(True)
        self._empty_label.hide()

        self.list_widget = DraggableList()
        self.list_widget.setObjectName("CatalogueList")
        body.addWidget(self.list_widget, stretch=1)
        body.addWidget(self._empty_label)

        root.addLayout(body, stretch=1)

        self._load_items()
        self._set_category(self.CAT_GENERATION)

    def _set_category(self, category: str):
        self._category = category
        for key, btn in self._rail_buttons.items():
            active = key == category
            btn.setChecked(active)
            btn.setIcon(left_panel_icon(key, "active" if active else "idle"))
        self._apply_filter()

    def _load_items(self):
        loader = CatalogLoader()
        panels, batteries = loader.load_catalogue()
        if not panels and not batteries:
            self._empty_label.setText(
                f"No components found.\nExpected catalogue at:\n{loader.file_path}"
            )
        self._all_items.clear()

        for p in panels:
            label = f"{p['name']} ({int(p['rated_power_w'])}W)"
            self._all_items.append((json.dumps(p), label, self.CAT_GENERATION))

        for b in batteries:
            label = f"{b['name']} ({int(b['capacity_wh'])}Wh)"
            self._all_items.append((json.dumps(b), label, self.CAT_STORAGE))

    def _apply_filter(self):
        query = self._search.text().strip().lower()
        self.list_widget.clear()

        self.list_widget.show()
        shown = 0
        for data_json, label, cat in self._all_items:
            if cat != self._category:
                continue
            if query and query not in label.lower():
                continue
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, data_json)
            self.list_widget.addItem(item)
            shown += 1

        if shown == 0:
            self._empty_label.setText("No components match your search.")
            self._empty_label.show()
        else:
            self._empty_label.hide()


class PropertiesPanel(QWidget):
    property_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PropertiesPanel")
        self._item: ComponentItem | None = None
        self._block_updates = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(10)

        self._placeholder = QLabel("Select a component on the canvas.")
        self._placeholder.setWordWrap(True)
        self._placeholder.setAlignment(Qt.AlignTop)
        outer.addWidget(self._placeholder)

        self._form_host = QWidget()
        form_outer = QVBoxLayout(self._form_host)
        form_outer.setContentsMargins(0, 0, 0, 0)
        form_outer.setSpacing(12)

        form_outer.addWidget(_SectionLabel("Identity"))
        identity = QFormLayout()
        identity.setSpacing(6)
        self._fld_id = QLabel("—")
        self._fld_type = QLabel("—")
        self._name = QLineEdit()
        self._name.editingFinished.connect(self._on_name_changed)
        identity.addRow("ID", self._fld_id)
        identity.addRow("Name", self._name)
        identity.addRow("Type", self._fld_type)
        form_outer.addLayout(identity)

        form_outer.addWidget(_SectionLabel("Electrical"))
        electrical = QFormLayout()
        electrical.setSpacing(6)
        self._rated_power = QDoubleSpinBox()
        self._rated_power.setRange(0, 1_000_000)
        self._rated_power.setSuffix(" W")
        self._rated_power.valueChanged.connect(self._on_rated_power)
        self._efficiency = QDoubleSpinBox()
        self._efficiency.setRange(0.01, 1.0)
        self._efficiency.setDecimals(3)
        self._efficiency.setSingleStep(0.01)
        self._efficiency.valueChanged.connect(self._on_efficiency)
        self._capacity = QDoubleSpinBox()
        self._capacity.setRange(0, 1_000_000)
        self._capacity.setSuffix(" Wh")
        self._capacity.valueChanged.connect(self._on_capacity)
        self._lbl_rated = QLabel("Rated Power")
        self._lbl_eff = QLabel("Efficiency")
        self._lbl_cap = QLabel("Capacity")
        electrical.addRow(self._lbl_rated, self._rated_power)
        electrical.addRow(self._lbl_eff, self._efficiency)
        electrical.addRow(self._lbl_cap, self._capacity)
        form_outer.addLayout(electrical)

        form_outer.addWidget(_SectionLabel("Position"))
        position = QFormLayout()
        position.setSpacing(6)
        self._pos_x = QDoubleSpinBox()
        self._pos_x.setRange(-10000, 10000)
        self._pos_x.setDecimals(1)
        self._pos_x.valueChanged.connect(self._on_position)
        self._pos_y = QDoubleSpinBox()
        self._pos_y.setRange(-10000, 10000)
        self._pos_y.setDecimals(1)
        self._pos_y.valueChanged.connect(self._on_position)
        position.addRow("X", self._pos_x)
        position.addRow("Y", self._pos_y)
        form_outer.addLayout(position)

        form_outer.addWidget(_SectionLabel("Color Tag"))
        swatch_row = QHBoxLayout()
        swatch_row.setSpacing(4)
        self._tag_group = QButtonGroup(self)
        self._tag_group.setExclusive(True)
        self._tag_buttons: dict[int, QToolButton] = {}
        for tag_id in sorted(COLOR_TAGS.keys()):
            btn = QToolButton()
            btn.setCheckable(True)
            btn.setIcon(color_swatch_icon(tag_id, 24))
            btn.setIconSize(QSize(24, 24))
            btn.setFixedSize(32, 32)
            btn.setToolTip(f"Tag {tag_id}")
            btn.clicked.connect(lambda checked, t=tag_id: self._on_tag(t))
            self._tag_group.addButton(btn, tag_id)
            swatch_row.addWidget(btn)
            self._tag_buttons[tag_id] = btn
        swatch_row.addStretch()
        form_outer.addLayout(swatch_row)

        form_outer.addStretch()
        outer.addWidget(self._form_host)
        outer.addStretch()

        self._form_host.hide()

    def update_properties(self, item):
        self._item = item if isinstance(item, ComponentItem) else None
        if self._item is None:
            self._placeholder.show()
            self._form_host.hide()
            return

        self._placeholder.hide()
        self._form_host.show()
        self._block_updates = True
        d = self._item.data_dict
        tag = ensure_color_tag(d)

        self._fld_id.setText(self._item.instance_id[:8] + "…")
        self._fld_type.setText(d.get("type", "—"))
        self._name.setText(d.get("name", ""))

        is_panel = d.get("type") == "PANEL"
        self._rated_power.setValue(float(d.get("rated_power_w", 0)))
        self._efficiency.setValue(float(d.get("efficiency", 0.18)))
        self._capacity.setValue(float(d.get("capacity_wh", 0)))

        self._set_field_visible(self._lbl_rated, self._rated_power, is_panel)
        self._set_field_visible(self._lbl_eff, self._efficiency, is_panel)
        self._set_field_visible(self._lbl_cap, self._capacity, not is_panel)

        pos = self._item.pos()
        self._pos_x.setValue(pos.x())
        self._pos_y.setValue(pos.y())

        for tid, btn in self._tag_buttons.items():
            btn.setChecked(tid == tag)

        self._block_updates = False

    def _set_field_visible(self, label, field, visible: bool):
        label.setVisible(visible)
        field.setVisible(visible)

    def _emit_change(self):
        if not self._block_updates:
            self.property_changed.emit()

    def _on_name_changed(self):
        if not self._item:
            return
        self._item.apply_properties({"name": self._name.text()})
        self._emit_change()

    def _on_rated_power(self, val):
        if not self._item or self._block_updates:
            return
        self._item.apply_properties({"rated_power_w": val})
        self._emit_change()

    def _on_efficiency(self, val):
        if not self._item or self._block_updates:
            return
        self._item.apply_properties({"efficiency": val})
        self._emit_change()

    def _on_capacity(self, val):
        if not self._item or self._block_updates:
            return
        self._item.apply_properties({"capacity_wh": val})
        self._emit_change()

    def _on_position(self):
        if not self._item or self._block_updates:
            return
        self._item.apply_properties({
            "x": self._pos_x.value(),
            "y": self._pos_y.value(),
        })
        self._emit_change()

    def _on_tag(self, tag_id: int):
        if not self._item or self._block_updates:
            return
        self._item.apply_color_tag(tag_id)
        self._emit_change()
