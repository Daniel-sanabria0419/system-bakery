"""Smoke Etapa 9: menú → productos → registrar venta → cobro."""

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication

from bakery.desktop.main import create_window
from bakery.desktop.ui import ConfirmSaleDialog, SaleSavedDialog
from bakery.persistence.schema import ESTADO_ACTIVO
from tests.test_stage4_desktop import FakeApiClient, _click, _find, _line_text, _select_payment


def test_smoke_menu_products_sale_checkout(qtbot) -> None:
    api = FakeApiClient(
        products=[
            {
                "id_producto": 1,
                "nombre": "Pan",
                "precio": 5000,
                "id_categoria": 1,
                "descripcion": None,
                "id_estado": ESTADO_ACTIVO,
            },
            {
                "id_producto": 2,
                "nombre": "Café",
                "precio": 3000,
                "id_categoria": 2,
                "descripcion": None,
                "id_estado": ESTADO_ACTIVO,
            },
        ]
    )
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    # Menú → Productos (CRUD táctil)
    _click(qtbot, _find(window, "menu_products_button"))
    assert window._stack.currentWidget() is window._products
    assert _find(window, "products_page") is not None
    _click(qtbot, _find(window, "products_back_button"))

    # Menú → Registrar venta → catálogo + cobro
    _click(qtbot, _find(window, "menu_register_button"))
    assert window._stack.currentWidget() is window._register
    assert _find(window, "sale_product_1") is not None

    _click(qtbot, _find(window, "sale_category_1"))
    _click(qtbot, _find(window, "sale_product_1"))
    _click(qtbot, _find(window, "quantity_plus_button"))
    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_list").text() == _line_text("Pan", 5000, 2)

    for digit in "3000":
        _click(qtbot, _find(window, f"digit_{digit}"))
    _click(qtbot, _find(window, "price_search_product_2"))
    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_total").text() == "Total: $ 13.000"

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
        lambda: len(api.sales) == 1 and _find(window, "purchase_list").text() == "",
        timeout=2000,
    )

    assert api.sales[0]["valor_total"] == 13000
    assert len(api.sales[0]["lineas"]) == 2
    assert window._stack.currentWidget() is window._register
    assert _find(window, "payment_button").text() == "Seleccionar medio de pago"
