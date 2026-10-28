"""Smoke Beta 2.0.2: menú → productos → venta → prefijo → Pan pequeño → cobro."""

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication

from bakery.app.money import format_cop
from bakery.desktop import style
from bakery.desktop.main import create_window
from bakery.desktop.ui import ConfirmSaleDialog, SaleSavedDialog
from bakery.persistence.schema import ESTADO_ACTIVO, NOMBRE_CATEGORIA_PAN_PEQUENO
from tests.test_stage4_desktop import (
    FakeApiClient,
    _PAN_PROMO_FIELDS,
    _click,
    _find,
    _purchase_list_text,
    _select_payment,
)


def test_smoke_menu_products_prefix_pan_pequeno_checkout(qtbot) -> None:
    api = FakeApiClient(
        categories=[
            {"id_categoria": 1, "nombre": "Panadería"},
            {"id_categoria": 2, "nombre": "Bebidas"},
            {"id_categoria": 6, "nombre": NOMBRE_CATEGORIA_PAN_PEQUENO},
        ],
        products=[
            {
                "id_producto": 1,
                "nombre": "Pan",
                "precio": 5000,
                "id_categoria": 1,
                "descripcion": None,
                "id_estado": ESTADO_ACTIVO,
                "ruta_imagen": None,
            },
            {
                "id_producto": 2,
                "nombre": "Café",
                "precio": 3000,
                "id_categoria": 2,
                "descripcion": None,
                "id_estado": ESTADO_ACTIVO,
                "ruta_imagen": None,
            },
            {
                "id_producto": 4,
                "nombre": "Pan rollo",
                "precio": 300,
                "id_categoria": 6,
                "descripcion": None,
                "id_estado": ESTADO_ACTIVO,
                "ruta_imagen": None,
                **_PAN_PROMO_FIELDS,
            },
        ],
    )
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    # Menú → Productos (fondo blanco de listado)
    _click(qtbot, _find(window, "menu_products_button"))
    assert window._stack.currentWidget() is window._products
    assert _find(window, "products_page") is not None
    assert _find(window, "products_list") is not None
    assert style.PRODUCTS_LIST_BACKGROUND == "#FFFFFF"
    _click(qtbot, _find(window, "products_back_button"))

    # Registrar venta: sin UI de búsqueda por precio
    _click(qtbot, _find(window, "menu_register_button"))
    assert window._stack.currentWidget() is window._register
    assert window.findChild(QObject, "price_search_scroll") is None
    assert _find(window, "catalog_sections_divider") is not None
    assert _find(window, "selected_product_panel") is not None

    # Catálogo completo sin prefijo de precio (pad eliminado en 2.0.6)
    _click(qtbot, _find(window, "sale_category_todos"))
    assert _find(window, "sale_product_1") is not None
    assert _find(window, "sale_product_2") is not None
    assert _find(window, "sale_product_4") is not None

    # Categoría Bebidas: solo Café
    _click(qtbot, _find(window, "catalog_back_to_categories"))
    _click(qtbot, _find(window, "sale_category_2"))
    assert _find(window, "sale_product_2") is not None
    assert window.findChild(QObject, "sale_product_4") is None

    # Pan pequeño: cantidad solo −/+ (Beta 2.0.6)
    _click(qtbot, _find(window, "catalog_back_to_categories"))
    _click(qtbot, _find(window, "sale_category_6"))
    _click(qtbot, _find(window, "sale_product_4"))
    assert _find(window, "selected_product_label").text() == "Pan rollo"
    assert "Unitario:" in _find(window, "selected_product_unit_price").text()
    for _ in range(6):
        _click(qtbot, _find(window, "quantity_plus_button"))
    preview = _find(window, "sale_value_preview").text()
    assert format_cop(2000) in preview
    assert _find(window, "quantity_label").text() == "7"
    _click(qtbot, _find(window, "agregar_button"))
    assert _purchase_list_text(window) == (
        f"Pan rollo × 7 — {format_cop(2000)}"
    )

    _select_payment(qtbot, window, 1)

    def accept_flow() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ConfirmSaleDialog):
                widget.accept()

                def accept_saved() -> None:
                    for saved in QApplication.topLevelWidgets():
                        if isinstance(saved, SaleSavedDialog):
                            saved.accept()
                            return

                QTimer.singleShot(0, accept_saved)
                return

    QTimer.singleShot(0, accept_flow)
    _click(qtbot, _find(window, "submit_sale_button"))
    qtbot.waitUntil(
        lambda: len(api.sales) == 1 and _purchase_list_text(window) == "",
        timeout=2000,
    )

    assert api.sales[0]["valor_total"] == 2000
    assert api.sales[0]["lineas"][0]["cantidad"] == 7
    assert window._stack.currentWidget() is window._register
