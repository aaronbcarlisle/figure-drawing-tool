"""
Tabler Icons for the Figure Drawing Tool.
SVG icons from https://tabler.io/icons (MIT License)
"""

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtSvg import QSvgRenderer

# SVG template with stroke color placeholder
SVG_TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{path}</svg>'''

# Tabler icon paths (outline style)
ICON_PATHS = {
    "player_play": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 4v16l13 -8z" />',
    "player_pause": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M6 5m0 1a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v12a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1z" /><path d="M14 5m0 1a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v12a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1z" />',
    "player_stop": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M5 5m0 2a2 2 0 0 1 2 -2h10a2 2 0 0 1 2 2v10a2 2 0 0 1 -2 2h-10a2 2 0 0 1 -2 -2z" />',
    "player_skip_back": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M20 5v14l-12 -7z" /><path d="M4 5l0 14" />',
    "player_skip_forward": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M4 5v14l12 -7z" /><path d="M20 5l0 14" />',
    "refresh": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M20 11a8.1 8.1 0 0 0 -15.5 -2m-.5 -4v4h4" /><path d="M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4" />',
    "folder": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M5 4h4l3 3h7a2 2 0 0 1 2 2v8a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-11a2 2 0 0 1 2 -2" />',
    "folder_open": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M5 19l2.757 -7.351a1 1 0 0 1 .936 -.649h12.307a1 1 0 0 1 .986 1.164l-.996 5.211a2 2 0 0 1 -1.964 1.625h-14.026a2 2 0 0 1 -2 -2v-11a2 2 0 0 1 2 -2h4l3 3h7a2 2 0 0 1 2 2v2" />',
    "folder_plus": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 19h-7a2 2 0 0 1 -2 -2v-11a2 2 0 0 1 2 -2h4l3 3h7a2 2 0 0 1 2 2v3.5" /><path d="M16 19h6" /><path d="M19 16v6" />',
    "folder_search": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M11 19h-6a2 2 0 0 1 -2 -2v-11a2 2 0 0 1 2 -2h4l3 3h7a2 2 0 0 1 2 2v2.5" /><path d="M18 18m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0" /><path d="M20.2 20.2l1.8 1.8" />',
    "clock": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0" /><path d="M12 7v5l3 3" />',
    "stopwatch": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M5 13a7 7 0 1 0 14 0a7 7 0 0 0 -14 0z" /><path d="M14.5 10.5l-2.5 2.5" /><path d="M17 8l1 -1" /><path d="M14 3h-4" />',
    "chevron_down": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M6 9l6 6l6 -6" />',
    "chevron_up": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M6 15l6 -6l6 6" />',
    "flip_horizontal": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 12l18 0" /><path d="M7 16l10 0l-10 5l0 -5" /><path d="M7 8l10 0l-10 -5l0 5" />',
    "flip_vertical": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 3l0 18" /><path d="M16 7l0 10l5 0l-5 -10" /><path d="M8 7l0 10l-5 0l5 -10" />',
    "contrast": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 17a5 5 0 0 0 0 -10v10" />',
    "player_play_filled": '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M6 4v16a1 1 0 0 0 1.524 .852l13 -8a1 1 0 0 0 0 -1.704l-13 -8a1 1 0 0 0 -1.524 .852z" fill="{color}" stroke="none" />',
}


def create_icon(name: str, color: str = "#cacfd2", size: int = 24, disabled_color: str = "#555555") -> QIcon:
    """Create a QIcon from a Tabler icon name with normal and disabled states.

    Args:
        name: Icon name (e.g., "player_play", "folder")
        color: Hex color for the icon stroke (normal state)
        size: Icon size in pixels
        disabled_color: Hex color for the icon stroke (disabled state)

    Returns:
        QIcon ready for use in Qt widgets
    """
    if name not in ICON_PATHS:
        raise ValueError(f"Unknown icon: {name}")

    icon = QIcon()

    # Create normal state pixmap
    icon_path = ICON_PATHS[name].replace("{color}", color)
    svg_data = SVG_TEMPLATE.format(color=color, path=icon_path)
    renderer = QSvgRenderer(QByteArray(svg_data.encode()))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    icon.addPixmap(pixmap, QIcon.Mode.Normal)

    # Create disabled state pixmap
    icon_path_disabled = ICON_PATHS[name].replace("{color}", disabled_color)
    svg_data_disabled = SVG_TEMPLATE.format(color=disabled_color, path=icon_path_disabled)
    renderer_disabled = QSvgRenderer(QByteArray(svg_data_disabled.encode()))
    pixmap_disabled = QPixmap(size, size)
    pixmap_disabled.fill(Qt.GlobalColor.transparent)
    painter_disabled = QPainter(pixmap_disabled)
    renderer_disabled.render(painter_disabled)
    painter_disabled.end()
    icon.addPixmap(pixmap_disabled, QIcon.Mode.Disabled)

    return icon


def save_icon(name: str, filepath: str, color: str = "#cacfd2", size: int = 24) -> str:
    """Save an icon to a file for use in stylesheets.

    Args:
        name: Icon name
        filepath: Path to save the icon
        color: Hex color for the icon stroke
        size: Icon size in pixels

    Returns:
        The filepath for convenience
    """
    pixmap = create_pixmap(name, color, size)
    pixmap.save(filepath, "PNG")
    return filepath


def create_pixmap(name: str, color: str = "#cacfd2", size: int = 24) -> QPixmap:
    """Create a QPixmap from a Tabler icon name.

    Args:
        name: Icon name (e.g., "player_play", "folder")
        color: Hex color for the icon stroke
        size: Icon size in pixels

    Returns:
        QPixmap ready for use in Qt widgets
    """
    if name not in ICON_PATHS:
        raise ValueError(f"Unknown icon: {name}")

    # Replace color placeholder in path (for filled icons)
    icon_path = ICON_PATHS[name].replace("{color}", color)
    svg_data = SVG_TEMPLATE.format(color=color, path=icon_path)

    # Render SVG to pixmap
    renderer = QSvgRenderer(QByteArray(svg_data.encode()))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return pixmap
