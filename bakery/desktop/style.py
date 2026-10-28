"""Layout metrics and QSS helpers for the desktop.

Métricas de layout y tipografía de chips de cobro: este archivo.
Colores generales: theme.qss (la tipografía de chips se inyecta vía load_theme_qss).
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

# Columna izquierda (compra + selección) vs derecha (catálogo + acciones)
LEFT_COLUMN_STRETCH = 2
RIGHT_COLUMN_STRETCH = 3

# Registrar venta 2.0.6: panel de compra (izq) y zona de acciones (der)
PURCHASE_PANEL_STRETCH = 1
# Catálogo vs acciones en la columna derecha (acciones no se encogen).
CATALOG_SECTION_STRETCH = 1
ACTIONS_PANEL_STRETCH = 0
ACTION_BUTTON_MIN_HEIGHT = 64
ACTION_BUTTON_MIN_WIDTH = 120

# Colores de acciones (mockup 2.0.6) — también en theme.qss
PAGAR_BUTTON_COLOR = "#5ac4f6"
BORRAR_TODO_BUTTON_COLOR = "#C62828"
FOOTER_TOTALS_FONT_SIZE = 20  # px; tipografía Subtotal/Descuento/Total

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
BACK_BUTTON_MIN_WIDTH = 72
BACK_BUTTON_MIN_HEIGHT = 29

# ---------------------------------------------------------------------------
# Chips de cobro (Beta 2.0.3 Etapa 2) — EDITAR AQUÍ tamaños y tipografía.
# theme.qss sustituye __CATEGORY_CHIP_FONT_SIZE__ / __PRODUCT_CHIP_FONT_SIZE__
# al cargar (load_theme_qss). Ancho/alto los aplica register_sale_page.
# ---------------------------------------------------------------------------
CATEGORY_CHIP_WIDTH = 135
CATEGORY_CHIP_HEIGHT = 120
CATEGORY_CHIP_FONT_SIZE = 16  # px
PRODUCT_CHIP_WIDTH = 135
PRODUCT_CHIP_HEIGHT = 120
PRODUCT_CHIP_FONT_SIZE = 16  # px
# Separación de la foto: borde del chip y espacio hasta el nombre.
PRODUCT_CHIP_IMAGE_PADDING = 6
CATALOG_CHIP_COLOR = "#64c466"
# Secciones categorías/productos en cobro (Beta 2.0.2 Etapa 3)
CATALOG_SECTION_BACKGROUND = "#d7d4ce"
# Referencia visual ~6 chips/fila; el layout calcula por ancho (no fijo).
CATALOG_WRAP_REFERENCE_COLUMNS = 6

# Panel producto seleccionado (Beta 2.0.2 Etapa 4)
SELECTED_PRODUCT_IMAGE_WIDTH = 72
SELECTED_PRODUCT_IMAGE_HEIGHT = 72

# Formularios Crear/Editar producto (Beta 2.0.1 Etapa 7)
APP_BACKGROUND = "#F5F0E8"
# Listado CRUD Productos (Beta 2.0.2 Etapa 5)
PRODUCTS_LIST_BACKGROUND = "#FFFFFF"
PRODUCT_FORM_FIELD_TEXT = "#000000"
# Placeholder más oscuro que el fondo de la app (#F5F0E8) para diferenciarse.
PRODUCT_FORM_PLACEHOLDER = "#5C5346"
PRODUCT_FORM_FIELD_CLASS = "product-form-field"
PRODUCT_FORM_LABEL_CLASS = "product-form-label"

_THEME_PATH = Path(__file__).with_name("theme.qss")


def load_theme_qss() -> str:
    """Carga theme.qss e inyecta tipografía desde las constantes de arriba."""
    text = _THEME_PATH.read_text(encoding="utf-8")
    return (
        text.replace(
            "__CATEGORY_CHIP_FONT_SIZE__", str(CATEGORY_CHIP_FONT_SIZE)
        )
        .replace("__PRODUCT_CHIP_FONT_SIZE__", str(PRODUCT_CHIP_FONT_SIZE))
        .replace("__FOOTER_TOTALS_FONT_SIZE__", str(FOOTER_TOTALS_FONT_SIZE))
        .replace("__PAGAR_BUTTON_COLOR__", PAGAR_BUTTON_COLOR)
        .replace("__BORRAR_TODO_BUTTON_COLOR__", BORRAR_TODO_BUTTON_COLOR)
    )


def apply_class(widget: QWidget, class_name: str) -> None:
    widget.setProperty("class", class_name)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
