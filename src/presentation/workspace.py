from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsLineItem, QGraphicsItem,
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QBrush, QColor, QPen, QCursor, QPainter, QKeyEvent
from src.core.datatypes import CircuitDescription
from src.core.design_tokens import COLOR_TAGS, DEFAULT_TAG_BY_TYPE
import json
import uuid

MODE_SELECT = 0
MODE_WIRE   = 1
MODE_DELETE = 2
MODE_ZOOM   = 3
MODE_TEXT   = 5  # must match WorkshopToolbar.MODE_TEXT

_WIRE_COLOR   = QColor("#89b4fa")
_WIRE_HOVER   = QColor("#f38ba8")
_WIRE_PREVIEW = QColor("#a6adc8")
_COMP_BORDER  = QColor("#45475a")
_COMP_SELECT  = QColor("#89b4fa")


def default_color_tag(comp_type: str) -> int:
    return DEFAULT_TAG_BY_TYPE.get(comp_type, 1)


def ensure_color_tag(data_dict: dict) -> int:
    tag = data_dict.get("color_tag")
    if tag is None or tag not in COLOR_TAGS:
        tag = default_color_tag(data_dict.get("type", "PANEL"))
        data_dict["color_tag"] = tag
    return int(tag)


class ConnectionItem(QGraphicsLineItem):
    def __init__(self, source, target):
        super().__init__()
        self.source = source
        self.target = target
        self._normal_pen = QPen(_WIRE_COLOR, 3)
        self.setPen(self._normal_pen)
        self.setZValue(-1)
        self.setFlag(QGraphicsLineItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setLine(
            source.get_center().x(), source.get_center().y(),
            target.get_center().x(), target.get_center().y(),
        )

    def shape(self):
        from PyQt5.QtGui import QPainterPathStroker
        path = super().shape()
        stroker = QPainterPathStroker()
        stroker.setWidth(10)
        return stroker.createStroke(path)

    def hoverEnterEvent(self, event):
        self.setPen(QPen(_WIRE_HOVER, 3))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPen(self._normal_pen)
        super().hoverLeaveEvent(event)

    def update_endpoint(self, moving_item, new_center):
        line = self.line()
        if moving_item == self.source:
            line.setP1(new_center)
        elif moving_item == self.target:
            line.setP2(new_center)
        self.setLine(line)

    def itemChange(self, change, value):
        if change == QGraphicsLineItem.ItemSelectedChange:
            if value:
                self.setPen(QPen(_WIRE_HOVER, 3))
            else:
                self.setPen(self._normal_pen)
        return super().itemChange(change, value)


class ComponentItem(QGraphicsRectItem):
    def __init__(self, data_dict, x, y, instance_id: str = None):
        super().__init__(0, 0, 100, 50)
        self.setPos(x, y)

        self.data_dict   = data_dict
        self.instance_id = instance_id or str(uuid.uuid4())
        self.wires: list = []

        ensure_color_tag(self.data_dict)
        self._normal_pen = QPen(_COMP_BORDER, 1.5)
        self._select_pen = QPen(_COMP_SELECT, 2, Qt.DashLine)
        self._refresh_brush()
        self.setPen(self._normal_pen)
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges)

        self.text = QGraphicsTextItem(self.data_dict["name"][:12], self)
        self.text.setDefaultTextColor(QColor("white"))
        self.text.setPos(5, 15)

    def _refresh_brush(self):
        tag = ensure_color_tag(self.data_dict)
        hex_color = COLOR_TAGS.get(tag, "#8798b3")
        self.setBrush(QBrush(QColor(hex_color)))

    def apply_color_tag(self, tag_id: int):
        if tag_id in COLOR_TAGS:
            self.data_dict["color_tag"] = tag_id
            self._refresh_brush()

    def apply_properties(self, patch: dict):
        for key, val in patch.items():
            if key == "color_tag":
                self.apply_color_tag(int(val))
            elif key in ("x", "y"):
                pos = self.pos()
                self.setPos(
                    patch.get("x", pos.x()),
                    patch.get("y", pos.y()),
                )
            else:
                self.data_dict[key] = val
        if "name" in patch:
            self.text.setPlainText(str(self.data_dict["name"])[:12])

    def get_center(self):
        return self.pos() + QPointF(50, 25)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemSelectedChange:
            self.setPen(self._select_pen if value else self._normal_pen)
        elif change == QGraphicsRectItem.ItemPositionChange:
            new_center = value + QPointF(50, 25)
            for wire in self.wires:
                wire.update_endpoint(self, new_center)
        return super().itemChange(change, value)


class WorkspaceTextItem(QGraphicsTextItem):
    """Free text on the canvas — double-click to edit, drag to move."""

    def __init__(self, text: str = "Text", x: float = 0, y: float = 0, item_id: str = None):
        super().__init__(text)
        self.item_id = item_id or str(uuid.uuid4())
        self.setPos(x, y)
        self.setDefaultTextColor(QColor("#cccccc"))
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setZValue(10)

    def begin_edit(self):
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.setFocus(Qt.MouseFocusReason)

    def end_edit(self):
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.clearFocus()

    def mouseDoubleClickEvent(self, event):
        self.begin_edit()
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        self.end_edit()
        super().focusOutEvent(event)

    def to_dict(self) -> dict:
        pos = self.pos()
        return {
            "instance_id": self.item_id,
            "x": pos.x(),
            "y": pos.y(),
            "text": self.toPlainText(),
        }


class WorkspaceCanvas(QGraphicsView):
    component_selected_signal = pyqtSignal(object)
    component_moved_signal = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 2000, 2000)
        self.setScene(self.scene)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)

        self.items_list: list = []
        self.connections_list: list = []
        self.text_items: list = []

        self.current_mode = MODE_SELECT
        self._editing_text: WorkspaceTextItem | None = None
        self.temp_line = None
        self.wire_start_item = None
        self._show_grid = True
        self._grid_step = 40

        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setFocusPolicy(Qt.StrongFocus)

    def set_grid_visible(self, visible: bool):
        self._show_grid = visible
        self.viewport().update()

    def set_mode(self, mode: int):
        self.current_mode = mode
        if mode == MODE_SELECT:
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setCursor(Qt.ArrowCursor)
            for item in self.items_list:
                item.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        elif mode == MODE_ZOOM:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.SizeAllCursor)
            for item in self.items_list:
                item.setFlag(QGraphicsRectItem.ItemIsMovable, False)
        elif mode == MODE_TEXT:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.IBeamCursor)
            for item in self.items_list:
                item.setFlag(QGraphicsRectItem.ItemIsMovable, False)
        else:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.ArrowCursor)
            for item in self.items_list:
                item.setFlag(QGraphicsRectItem.ItemIsMovable, False)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def _drop_scene_pos(self, event) -> QPointF:
        """Reliable scene position at drop time (avoids viewport offset drift)."""
        vp_pt = self.viewport().mapFromGlobal(QCursor.pos())
        return self.mapToScene(vp_pt)

    def dropEvent(self, event):
        if event.mimeData().hasText():
            try:
                comp_data = json.loads(event.mimeData().text())
                ensure_color_tag(comp_data)
                pos = self._drop_scene_pos(event)
                item = ComponentItem(comp_data, pos.x() - 50, pos.y() - 25)
                item.setFlag(
                    QGraphicsRectItem.ItemIsMovable,
                    self.current_mode == MODE_SELECT,
                )
                self.scene.addItem(item)
                self.items_list.append(item)
                event.acceptProposedAction()
            except json.JSONDecodeError:
                event.ignore()

    def get_component_at(self, pos):
        item = self.scene.itemAt(pos, self.transform())
        if isinstance(item, QGraphicsTextItem) and isinstance(
            item.parentItem(), ComponentItem
        ):
            return item.parentItem()
        return item

    def get_text_at(self, pos):
        item = self.scene.itemAt(pos, self.transform())
        if isinstance(item, WorkspaceTextItem):
            return item
        return None

    def _finish_text_edit(self):
        if self._editing_text is not None:
            self._editing_text.end_edit()
            self._editing_text = None

    def delete_selection(self):
        self._finish_text_edit()
        for item in self.scene.selectedItems():
            if isinstance(item, ComponentItem):
                self._remove_component(item)
            elif isinstance(item, ConnectionItem):
                self._remove_wire(item)
            elif isinstance(item, WorkspaceTextItem):
                self._remove_text(item)

    def _remove_component(self, item: ComponentItem):
        for wire in list(item.wires):
            self._remove_wire(wire)
        self.scene.removeItem(item)
        if item in self.items_list:
            self.items_list.remove(item)
        self.component_selected_signal.emit(None)

    def _remove_wire(self, wire: ConnectionItem):
        if wire in wire.source.wires:
            wire.source.wires.remove(wire)
        if wire in wire.target.wires:
            wire.target.wires.remove(wire)
        self.scene.removeItem(wire)
        if wire in self.connections_list:
            self.connections_list.remove(wire)

    def _remove_text(self, text_item: WorkspaceTextItem):
        self.scene.removeItem(text_item)
        if text_item in self.text_items:
            self.text_items.remove(text_item)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace) and self.current_mode == MODE_SELECT:
            if self.scene.selectedItems():
                self.delete_selection()
                event.accept()
                return
        if event.key() == Qt.Key_Escape:
            self._finish_text_edit()
        super().keyPressEvent(event)

    def _emit_selection(self, item):
        if isinstance(item, ComponentItem):
            self.component_selected_signal.emit(item)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if not self._show_grid:
            return
        left = int(rect.left()) - (int(rect.left()) % self._grid_step)
        top = int(rect.top()) - (int(rect.top()) % self._grid_step)
        lines = []
        grid_pen = QPen(QColor("#3a3a3a"))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        x = left
        while x < rect.right():
            lines.append((x, rect.top(), x, rect.bottom()))
            x += self._grid_step
        y = top
        while y < rect.bottom():
            lines.append((rect.left(), y, rect.right(), y))
            y += self._grid_step
        for x1, y1, x2, y2 in lines:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        item = self.get_component_at(scene_pos)

        if self.current_mode == MODE_ZOOM:
            factor = 1.2 if event.button() == Qt.LeftButton else 1 / 1.2
            self.scale(factor, factor)
            event.accept()
            return

        if self.current_mode == MODE_TEXT and event.button() == Qt.LeftButton:
            hit = self.get_text_at(scene_pos)
            if hit is not None:
                self._finish_text_edit()
                self._editing_text = hit
                hit.begin_edit()
            else:
                self._finish_text_edit()
                text_item = WorkspaceTextItem("Enter text here", scene_pos.x(), scene_pos.y())
                self.scene.addItem(text_item)
                self.text_items.append(text_item)
                self._editing_text = text_item
                text_item.begin_edit()
            event.accept()
            return

        if self.current_mode != MODE_TEXT:
            self._finish_text_edit()

        super().mousePressEvent(event)

        if self.current_mode == MODE_SELECT:
            self._emit_selection(item)

        elif self.current_mode == MODE_WIRE:
            if isinstance(item, ComponentItem):
                self.wire_start_item = item
                self.temp_line = QGraphicsLineItem()
                self.temp_line.setPen(QPen(_WIRE_PREVIEW, 3, Qt.DashLine))
                center = item.get_center()
                self.temp_line.setLine(
                    center.x(), center.y(), center.x(), center.y()
                )
                self.scene.addItem(self.temp_line)

        elif self.current_mode == MODE_DELETE:
            if isinstance(item, ComponentItem):
                self._remove_component(item)
            elif isinstance(item, ConnectionItem):
                self._remove_wire(item)
            elif isinstance(item, WorkspaceTextItem):
                self._remove_text(item)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self.current_mode == MODE_WIRE and self.temp_line and self.wire_start_item:
            pos = self.mapToScene(event.pos())
            center = self.wire_start_item.get_center()
            self.temp_line.setLine(center.x(), center.y(), pos.x(), pos.y())

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.current_mode == MODE_SELECT:
            scene_pos = self.mapToScene(event.pos())
            item = self.get_component_at(scene_pos)
            if isinstance(item, ComponentItem):
                self.component_moved_signal.emit(item)

        if self.current_mode == MODE_WIRE and self.temp_line:
            self.temp_line.hide()
            scene_pos = self.mapToScene(event.pos())
            item = self.get_component_at(scene_pos)

            if isinstance(item, ComponentItem) and item != self.wire_start_item:
                already = any(
                    (w.source == self.wire_start_item and w.target == item)
                    or (w.source == item and w.target == self.wire_start_item)
                    for w in self.connections_list
                )
                if not already:
                    wire = ConnectionItem(self.wire_start_item, item)
                    self.scene.addItem(wire)
                    self.connections_list.append(wire)
                    self.wire_start_item.wires.append(wire)
                    item.wires.append(wire)

            self.scene.removeItem(self.temp_line)
            self.temp_line = None
            self.wire_start_item = None

    def clear_canvas(self):
        self.scene.clear()
        self.items_list.clear()
        self.connections_list.clear()
        self.text_items.clear()
        self.temp_line = None
        self.wire_start_item = None
        self._editing_text = None

    def serialize_circuit(self) -> CircuitDescription:
        if not self.items_list:
            return None

        panels = []
        batteries = []

        for item in self.items_list:
            d = item.data_dict
            if d["type"] == "PANEL":
                panels.append({
                    "instance_id": item.instance_id,
                    "panel_id": d["component_id"],
                    "rated_power_w": d["rated_power_w"],
                    "efficiency": d.get("efficiency", 0.18),
                    "quantity": 1,
                })
            else:
                batteries.append({
                    "instance_id": item.instance_id,
                    "battery_id": d["component_id"],
                    "capacity_wh": d["capacity_wh"],
                    "type": "Li-Ion",
                })

        connections = [
            {
                "source_id": wire.source.instance_id,
                "target_id": wire.target.instance_id,
            }
            for wire in self.connections_list
        ]

        return CircuitDescription(
            circuit_id=str(uuid.uuid4()),
            panels=panels,
            batteries=batteries,
            connections=connections,
        )

    def save_state(self) -> dict:
        items_data = []
        for item in self.items_list:
            items_data.append({
                "instance_id": item.instance_id,
                "x": item.pos().x(),
                "y": item.pos().y(),
                "data_dict": item.data_dict,
            })

        connections_data = [
            {
                "source_id": wire.source.instance_id,
                "target_id": wire.target.instance_id,
            }
            for wire in self.connections_list
        ]

        texts_data = [t.to_dict() for t in self.text_items]

        return {
            "items": items_data,
            "connections": connections_data,
            "texts": texts_data,
        }

    def load_state(self, state: dict):
        self.clear_canvas()

        id_map: dict[str, ComponentItem] = {}
        for item_data in state.get("items", []):
            dd = item_data["data_dict"]
            ensure_color_tag(dd)
            comp = ComponentItem(
                data_dict=dd,
                x=item_data["x"],
                y=item_data["y"],
                instance_id=item_data["instance_id"],
            )
            comp.setFlag(
                QGraphicsRectItem.ItemIsMovable,
                self.current_mode == MODE_SELECT,
            )
            self.scene.addItem(comp)
            self.items_list.append(comp)
            id_map[comp.instance_id] = comp

        for conn in state.get("connections", []):
            src = id_map.get(conn["source_id"])
            tgt = id_map.get(conn["target_id"])
            if src is None or tgt is None:
                continue
            wire = ConnectionItem(src, tgt)
            self.scene.addItem(wire)
            self.connections_list.append(wire)
            src.wires.append(wire)
            tgt.wires.append(wire)

        for td in state.get("texts", []):
            text_item = WorkspaceTextItem(
                text=td.get("text", ""),
                x=td.get("x", 0),
                y=td.get("y", 0),
                item_id=td.get("instance_id"),
            )
            self.scene.addItem(text_item)
            self.text_items.append(text_item)
