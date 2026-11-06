"""Layout metrics and QSS helpers for the desktop.

Métricas de layout y tipografía de chips de cobro: este archivo.
Colores / tokens visuales: constantes abajo + theme.qss (inyección vía load_theme_qss).
objectName y clases QSS: docs/beta-1.2/visual-guide.md.
"""

from pathlib import Path

from PySide6.QtWidgets import QWidget

# Layouts de página (menú y registrar venta)
PAGE_MARGIN = 5
PAGE_SPACING = 5

# Menú principal (Beta 1.2 etapa 4): margen ~20 px arriba-izquierda
# INTACTO en rediseño visual — no cambiar valores ni selectores menu-button.
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

# Formularios Crear/Editar producto (Beta 2.0.1 Etapa 7) — QSS product-form INTACTO.
APP_BACKGROUND = "#F5F0E8"
# Listado CRUD Productos (Beta 2.0.2 Etapa 5)
PRODUCTS_LIST_BACKGROUND = "#FFFFFF"
PRODUCT_FORM_FIELD_TEXT = "#000000"
# Placeholder más oscuro que el fondo de la app (#F5F0E8) para diferenciarse.
PRODUCT_FORM_PLACEHOLDER = "#5C5346"
PRODUCT_FORM_FIELD_CLASS = "product-form-field"
PRODUCT_FORM_LABEL_CLASS = "product-form-label"

# ---------------------------------------------------------------------------
# Tokens visuales globales (rediseño visual post 2.1 — Etapa 0)
# Centralizados aquí; theme.qss los inyecta. Menú y product-form no usan
# estos placeholders (siguen con valores fijos en QSS). Etapas 1+ aplicarán
# RADIUS_BASE / tipografía a pantallas B/C/E/F sin tocar menú ni forms.
# ---------------------------------------------------------------------------
COLOR_PAGE_BG = APP_BACKGROUND  # crema app / diálogos
COLOR_SURFACE = PRODUCTS_LIST_BACKGROUND  # paneles blancos
COLOR_TEXT = "#1A1A1A"
COLOR_TEXT_STRONG = "#000000"
COLOR_TEXT_ON_DARK = "#FFFFFF"
COLOR_BORDER = "#C4B8A8"
COLOR_ACCENT_CYAN = PAGAR_BUTTON_COLOR  # volver / pagar
COLOR_ACCENT_GREEN = MENU_BUTTON_COLOR  # chips selected (menú = hardcode QSS)
COLOR_CHIP = CATALOG_CHIP_COLOR
COLOR_DESTRUCTIVE = BORRAR_TODO_BUTTON_COLOR
COLOR_PAYMENT_IDLE = "#9E9E9E"
COLOR_BUTTON_DARK = "#1A1A1A"
COLOR_DISABLED_BG = "#BDBDBD"
COLOR_DISABLED_TEXT = "#757575"
# Pressed: un tono más oscuro que el fondo normal (feedback táctil; no hover).
COLOR_ACCENT_CYAN_PRESSED = "#3A9DB8"
COLOR_DESTRUCTIVE_PRESSED = "#8E1B1B"
COLOR_BUTTON_DARK_PRESSED = "#000000"
COLOR_PAYMENT_IDLE_PRESSED = "#757575"
COLOR_CHIP_PRESSED = "#4CAF50"
COLOR_CHIP_SELECTED_PRESSED = "#1B5E20"
RADIUS_BASE = 8  # px; documentado para etapas siguientes (no aplica a menú/forms)
FONT_SIZE_BODY = 16  # px
FONT_SIZE_TITLE = 22  # px

_THEME_PATH = Path(__file__).with_name("theme.qss")


def load_theme_qss() -> str:
    """Carga theme.qss e inyecta tokens / tipografía desde las constantes de arriba."""
    text = _THEME_PATH.read_text(encoding="utf-8")
    replacements = {
        "__CATEGORY_CHIP_FONT_SIZE__": str(CATEGORY_CHIP_FONT_SIZE),
        "__PRODUCT_CHIP_FONT_SIZE__": str(PRODUCT_CHIP_FONT_SIZE),
        "__FOOTER_TOTALS_FONT_SIZE__": str(FOOTER_TOTALS_FONT_SIZE),
        "__PAGAR_BUTTON_COLOR__": PAGAR_BUTTON_COLOR,
        "__BORRAR_TODO_BUTTON_COLOR__": BORRAR_TODO_BUTTON_COLOR,
        "__COLOR_PAGE_BG__": COLOR_PAGE_BG,
        "__COLOR_SURFACE__": COLOR_SURFACE,
        "__COLOR_TEXT__": COLOR_TEXT,
        "__COLOR_TEXT_STRONG__": COLOR_TEXT_STRONG,
        "__COLOR_TEXT_ON_DARK__": COLOR_TEXT_ON_DARK,
        "__COLOR_BORDER__": COLOR_BORDER,
        "__COLOR_ACCENT_CYAN__": COLOR_ACCENT_CYAN,
        "__COLOR_ACCENT_GREEN__": COLOR_ACCENT_GREEN,
        "__COLOR_CHIP__": COLOR_CHIP,
        "__COLOR_DESTRUCTIVE__": COLOR_DESTRUCTIVE,
        "__COLOR_PAYMENT_IDLE__": COLOR_PAYMENT_IDLE,
        "__COLOR_BUTTON_DARK__": COLOR_BUTTON_DARK,
        "__COLOR_DISABLED_BG__": COLOR_DISABLED_BG,
        "__COLOR_DISABLED_TEXT__": COLOR_DISABLED_TEXT,
        "__COLOR_ACCENT_CYAN_PRESSED__": COLOR_ACCENT_CYAN_PRESSED,
        "__COLOR_DESTRUCTIVE_PRESSED__": COLOR_DESTRUCTIVE_PRESSED,
        "__COLOR_BUTTON_DARK_PRESSED__": COLOR_BUTTON_DARK_PRESSED,
        "__COLOR_PAYMENT_IDLE_PRESSED__": COLOR_PAYMENT_IDLE_PRESSED,
        "__COLOR_CHIP_PRESSED__": COLOR_CHIP_PRESSED,
        "__COLOR_CHIP_SELECTED_PRESSED__": COLOR_CHIP_SELECTED_PRESSED,
        "__RADIUS_BASE__": str(RADIUS_BASE),
        "__FONT_SIZE_BODY__": str(FONT_SIZE_BODY),
        "__FONT_SIZE_TITLE__": str(FONT_SIZE_TITLE),
    }
    # Claves más largas primero para no romper p. ej. __COLOR_TEXT_ON_DARK__
    # al sustituir __COLOR_TEXT__.
    for placeholder, value in sorted(
        replacements.items(), key=lambda item: len(item[0]), reverse=True
    ):
        text = text.replace(placeholder, value)
    return text


def apply_class(widget: QWidget, class_name: str) -> None:
    widget.setProperty("class", class_name)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
