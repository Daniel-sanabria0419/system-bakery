"""Parámetros visuales editables para el desktop.

Cambia estos valores para ajustar tamaños, espaciados y márgenes.
No define colores ni tipografías: para eso usa setStyleSheet sobre los
objectName documentados en docs/beta-1.1/visual-guide.md.
"""

# Ventana principal
WINDOW_WIDTH = 420
WINDOW_HEIGHT = 560

# Layouts de página (menú y registrar venta)
PAGE_MARGIN_LEFT = 11
PAGE_MARGIN_TOP = 11
PAGE_MARGIN_RIGHT = 11
PAGE_MARGIN_BOTTOM = 11
PAGE_SPACING = 6

# Teclado numérico
PAD_SPACING = 6
PAD_BUTTON_MIN_WIDTH = 0
PAD_BUTTON_MIN_HEIGHT = 0
# Si PAD_BUTTON_MIN_* es 0, no se fuerza tamaño mínimo (comportamiento Qt por defecto).
