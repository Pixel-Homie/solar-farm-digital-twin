"""Load Interface/ SVG assets as QIcons and pixmaps."""

import os

from PyQt5.QtCore import QSize, Qt, QRectF
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer

from src.core.paths import resource_path

_INTERFACE = resource_path("Interface")

_LEFT_ICONS = {
    "generation": ("generation icon {state}.svg", "left panel"),
    "storage": ("storage icon {state}.svg", "left panel"),
    "wiring": ("wiring icon {state}.svg", "left panel"),
    "search": ("mini zoom icon for search components box.svg", "left panel"),
}

_WINDOW_CONTROLS = {
    "close": "x button {state}.svg",
    "minimize": "_ button {state}.svg",
    "maximize": "= button {state}.svg",
}

_WORKSHOP_ICONS = {
    "select": ("upper panel", "cursor icon {state}.svg"),
    "zoom": ("upper panel", "zoom icon {state}.svg"),
    "grid": ("upper panel", "grid icon {state}.svg"),
    "text": ("upper panel", "text icon {state}.svg"),
    "wire": ("left panel", "wiring icon {state}.svg"),
    "delete": ("upper panel", "delete icon {state}.svg"),
}

_PANEL_ICONS = {
    "catalogue": ("left panel", "generation icon {state}.svg"),
    "properties": ("left panel", "storage icon {state}.svg"),
    "terminal": ("left panel", "wiring icon {state}.svg"),
}

_ICON_ALIASES = {
    ("upper panel", "zoom icon idle.svg"): "zoom icon idli.svg",
    ("upper panel", "delete icon idle.svg"): "Delete idle (2).svg",
    ("upper panel", "delete icon active.svg"): "Delete active (3).svg",
}

# Keys that use full-square button SVGs (window controls)
_SQUARE_KEYS = frozenset({"close", "minimize", "maximize"})


def interface_path(area: str, filename: str) -> str:
    return os.path.join(_INTERFACE, area, "SVG", filename)


def _resolve_svg(area: str, filename: str) -> str:
    path = interface_path(area, filename)
    if os.path.isfile(path):
        return path
    alt = _ICON_ALIASES.get((area, filename))
    if alt:
        path = interface_path(area, alt)
    return path if os.path.isfile(path) else ""


def _pixmap_from_svg_square(svg_path: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    if not svg_path or not os.path.isfile(svg_path):
        return _fallback_square(size, svg_path == "")
    renderer = QSvgRenderer(svg_path)
    if not renderer.isValid():
        return _fallback_square(size, True)
    painter = QPainter(pm)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return pm


def _fallback_square(size: int, draw_glyph: bool) -> QPixmap:
    """Simple placeholder if SVG missing."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    if not draw_glyph:
        return pm
    p = QPainter(pm)
    p.setPen(QColor("#808080"))
    p.drawRect(2, 2, size - 4, size - 4)
    p.end()
    return pm


def _pixmap_from_svg(svg_path: str, size: int = 32, *, height=None) -> QPixmap:
    if not svg_path or not os.path.isfile(svg_path):
        return QPixmap()
    renderer = QSvgRenderer(svg_path)
    if not renderer.isValid():
        return QPixmap()
    def_size = renderer.defaultSize()
    src_w = max(def_size.width(), 1)
    src_h = max(def_size.height(), 1)
    if height is not None:
        out_h = height
        out_w = max(1, int(src_w * height / src_h))
    else:
        out_w = size
        out_h = max(1, int(src_h * size / src_w))
    pm = QPixmap(out_w, out_h)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    renderer.render(painter, QRectF(0, 0, out_w, out_h))
    painter.end()
    return pm


def icon_from_file(area: str, filename: str, size: int = 32) -> QIcon:
    path = _resolve_svg(area, filename)
    return QIcon(_pixmap_from_svg(path, size))


def left_panel_icon(key: str, state: str = "idle", size: int = 32) -> QIcon:
    template, area = _LEFT_ICONS[key]
    return _make_icon(area, template, state, size, square=False)


def window_control_icon(key: str, state: str = "idle", size: int = 36) -> QIcon:
    template = _WINDOW_CONTROLS[key]
    path = _resolve_svg("upper panel", template.format(state=state))
    if not path and state == "active":
        path = _resolve_svg("upper panel", template.format(state="idle"))
    return QIcon(_pixmap_from_svg_square(path, size))


def window_control_pixmap(key: str, state: str = "idle", size: int = 36) -> QPixmap:
    return window_control_icon(key, state, size).pixmap(QSize(size, size))


def _make_icon(area: str, template: str, state: str, size: int, square: bool) -> QIcon:
    fname = template.format(state=state)
    path = _resolve_svg(area, fname)
    if not path and state == "active":
        path = _resolve_svg(area, template.format(state="idle"))
    if square:
        return QIcon(_pixmap_from_svg_square(path, size))
    if path:
        return QIcon(_pixmap_from_svg(path, size))
    return QIcon(_fallback_square(size, True))


def workshop_icon_fn(name: str, size: int = 28):
    """Return callable(state) -> QIcon for IconStateButton."""
    area, template = _WORKSHOP_ICONS[name]
    square = name in _SQUARE_KEYS

    def getter(state: str) -> QIcon:
        return _make_icon(area, template, state, size, square)

    return getter


def workshop_icon(name: str, state: str = "idle", size: int = 28) -> QIcon:
    return workshop_icon_fn(name, size)(state)


def panel_icon_fn(name: str, size: int = 28):
    area, template = _PANEL_ICONS[name]

    def getter(state: str) -> QIcon:
        return _make_icon(area, template, state, size, square=False)

    return getter


def toolbar_icon(name: str, state: str = "idle", size: int = 26) -> QIcon:
    return workshop_icon(name, state, size)


_LOGO_BAR_HEIGHT = 40


def app_logo_pixmap(height: int = _LOGO_BAR_HEIGHT) -> QPixmap:
    path = _resolve_svg("upper panel", "logo.svg")
    return _pixmap_from_svg(path, height=height) if path else QPixmap()


def graph_logo_pixmap(height: int = 36) -> QPixmap:
    for area, name in (
        ("logo for graphs window", "Layer 4.svg"),
        ("logo for graphs", "Layer 4.svg"),
    ):
        path = _resolve_svg(area, name)
        if path:
            return _pixmap_from_svg(path, height=height)
    return QPixmap()


def app_logo_icon(height: int = 32) -> QIcon:
    return QIcon(app_logo_pixmap(height))


def color_swatch_icon(tag_id: int, size: int = 28) -> QIcon:
    return icon_from_file("right panel", f"color{tag_id}.svg", size)
