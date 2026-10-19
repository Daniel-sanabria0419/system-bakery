"""Layout metrics and QSS helpers for the desktop.

Colores y tipografía viven en theme.qss.
objectName y clases QSS: docs/beta-1.2/visual-guide.md.
"""

from pathlib import Path

from PySide6.QtWidgets import QWidget

# Layouts de página (menú y registrar venta)
PAGE_MARGIN = 5
PAGE_SPACING = 5

# Menú principal (Beta 1.2 etapa 4): margen ~20 px arriba-izquierda
MENU_MARGIN = 20
MENU_BUTTON_COLOR = "#2E7D32"

# Columna izquierda (operativa) vs derecha (futuro)
LEFT_COLUMN_STRETCH = 2
RIGHT_COLUMN_STRETCH = 3

# Registrar venta: detalle ~1/3, pad ~2/3 de la columna operativa (Beta 1.2 etapa 3)
PURCHASE_PANEL_STRETCH = 1
PAD_PANEL_STRETCH = 2

# Teclado numérico
PAD_SPACING = 6
PAD_BUTTON_MIN_WIDTH = 64
PAD_BUTTON_MIN_HEIGHT = 90
# Si PAD_BUTTON_MIN_* es 0, no se fuerza tamaño mínimo (comportamiento Qt por defecto).

# Botones del popup de medio de pago (Beta 1.2)
PAYMENT_METHOD_BUTTON_MIN_WIDTH = 120
PAYMENT_METHOD_BUTTON_MIN_HEIGHT = 72

# Diálogos confirmar / éxito (Beta 1.2 etapa 1)
DIALOG_ACTION_BUTTON_MIN_HEIGHT = 80
DIALOG_ACTION_BUTTON_MIN_WIDTH = 160
DIALOG_MIN_WIDTH = 480
DIALOG_MIN_HEIGHT = 240
DIALOG_CONTENT_MARGIN = 28
DIALOG_CONTENT_SPACING = 20

# Botón volver (Beta 1.2 etapa 2): rectángulo un poco más ancho que alto
BACK_BUTTON_MIN_WIDTH = 96
BACK_BUTTON_MIN_HEIGHT = 72

_THEME_PATH = Path(__file__).with_name("theme.qss")


def load_theme_qss() -> str:
    return _THEME_PATH.read_text(encoding="utf-8")


def apply_class(widget: QWidget, class_name: str) -> None:
    widget.setProperty("class", class_name)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
