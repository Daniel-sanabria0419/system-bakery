"""Layout metrics and QSS helpers for the desktop.

Colores y tipografía viven en theme.qss.
objectName y clases QSS: docs/beta-1.1/visual-guide.md.
"""

from pathlib import Path

from PySide6.QtWidgets import QWidget

# Layouts de página (menú y registrar venta)
PAGE_MARGIN = 5
PAGE_SPACING = 5

# Columna izquierda (operativa) vs derecha (futuro)
LEFT_COLUMN_STRETCH = 2
RIGHT_COLUMN_STRETCH = 3

# Teclado numérico
PAD_SPACING = 6
PAD_BUTTON_MIN_WIDTH = 64
PAD_BUTTON_MIN_HEIGHT = 90
# Si PAD_BUTTON_MIN_* es 0, no se fuerza tamaño mínimo (comportamiento Qt por defecto).

_THEME_PATH = Path(__file__).with_name("theme.qss")


def load_theme_qss() -> str:
    return _THEME_PATH.read_text(encoding="utf-8")


def apply_class(widget: QWidget, class_name: str) -> None:
    widget.setProperty("class", class_name)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
