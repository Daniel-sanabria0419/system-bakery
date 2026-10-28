"""Smoke Beta 2.0.3: menú → venta → categoría → producto → volver → Todos → cobro."""

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication

from bakery.app.money import format_cop
from bakery.desktop import style
from bakery.desktop.main import create_window
from bakery.desktop.ui import ConfirmSaleDialog, SaleSavedDialog
from bakery.persistence.schema import ESTADO_ACTIVO
from tests.test_stage4_desktop import FakeApiClient, _click, _find, _select_payment


def test_smoke_vista_a_b_volver_todos_checkout(qtbot) -> None:
    api = FakeApiClient(
        categories=[
            {"id_categoria": 1, "nombre": "Panadería"},
            {"id_categoria": 2, "nombre": "Bebidas"},
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
        ],
    )
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    _click(qtbot, _find(window, "menu_register_button"))
    QApplication.processEvents()
    assert window._stack.currentWidget() is window._register
    assert window._register._catalog_view == "categories"
    assert _find(window, "catalog_categories_section").isVisible()
    assert not _find(window, "catalog_products_section").isVisible()
    assert _find(window, "sale_category_todos").property("class") == "category-chip"

    _click(qtbot, _find(window, "sale_category_1"))
    QApplication.processEvents()
    assert window._register._catalog_view == "products"
    assert not _find(window, "catalog_categories_section").isVisible()
    assert _find(window, "catalog_products_section").isVisible()
    back = _find(window, "catalog_back_to_categories")
    assert back.width() == style.PRODUCT_CHIP_WIDTH
    assert back.height() == style.PRODUCT_CHIP_HEIGHT
    assert window.findChild(QObject, "sale_product_1") is not None
    assert window.findChild(QObject, "sale_product_2") is None

    _click(qtbot, _find(window, "sale_product_1"))
    assert _find(window, "selected_product_label").text() == "Pan"
    _click(qtbot, _find(window, "agregar_button"))
    assert "Pan" in _find(window, "purchase_list").text()

    _click(qtbot, back)
    QApplication.processEvents()
    assert window._register._catalog_view == "categories"
    assert _find(window, "catalog_categories_section").isVisible()
    assert not _find(window, "catalog_products_section").isVisible()

    _click(qtbot, _find(window, "sale_category_todos"))
    QApplication.processEvents()
    assert window.findChild(QObject, "sale_product_1") is not None
    assert window.findChild(QObject, "sale_product_2") is not None
    _click(qtbot, _find(window, "sale_product_2"))
    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(8000)}"

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
    assert api.sales[0]["valor_total"] == 8000
    assert window._register._catalog_view == "categories"
