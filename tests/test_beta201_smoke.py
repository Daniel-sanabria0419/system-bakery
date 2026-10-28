"""Smoke Beta 2.0.1: menú → productos → venta (Pan pequeño) → cobro."""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from bakery.app.money import format_cop
from bakery.desktop.main import create_window
from bakery.desktop.ui import ConfirmSaleDialog, SaleSavedDialog
from bakery.persistence.schema import ESTADO_ACTIVO, NOMBRE_CATEGORIA_PAN_PEQUENO
from tests.test_stage4_desktop import (
    FakeApiClient,
    _PAN_PROMO_FIELDS,
    _click,
    _find,
    _select_payment,
)


def test_smoke_menu_products_pan_pequeno_checkout(qtbot) -> None:
    api = FakeApiClient(
        categories=[
            {"id_categoria": 1, "nombre": "Panadería"},
            {"id_categoria": 6, "nombre": NOMBRE_CATEGORIA_PAN_PEQUENO},
        ],
        products=[
            {
                "id_producto": 1,
                "nombre": "Torta",
                "precio": 20000,
                "id_categoria": 1,
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

    _click(qtbot, _find(window, "menu_products_button"))
    assert window._stack.currentWidget() is window._products
    assert _find(window, "products_page") is not None
    _click(qtbot, _find(window, "products_back_button"))

    _click(qtbot, _find(window, "menu_register_button"))
    assert window._stack.currentWidget() is window._register
    assert _find(window, "sale_category_todos") is not None

    _click(qtbot, _find(window, "sale_category_6"))
    _click(qtbot, _find(window, "sale_product_4"))
    for digit in "2000":
        _click(qtbot, _find(window, f"digit_{digit}"))
    preview = _find(window, "sale_value_preview").text()
    assert format_cop(2000) in preview
    assert "7" in _find(window, "quantity_label").text()
    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_list").text() == (
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
        lambda: len(api.sales) == 1 and _find(window, "purchase_list").text() == "",
        timeout=2000,
    )

    assert api.sales[0]["valor_total"] == 2000
    assert api.sales[0]["lineas"][0]["cantidad"] == 7
    assert api.sales[0]["lineas"][0]["precio_aplicado"] == 300
    assert window._stack.currentWidget() is window._register
