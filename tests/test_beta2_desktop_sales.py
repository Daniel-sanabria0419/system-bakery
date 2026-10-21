from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtWidgets import QApplication

from bakery.desktop.main import create_window
from bakery.desktop.ui import ConfirmSaleDialog, SaleSavedDialog
from tests.test_stage4_desktop import (
    FakeApiClient,
    _click,
    _find,
    _line_text,
    _select_payment,
)


def test_reject_agregar_without_product_shows_feedback(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    for digit in "5000":
        _click(qtbot, _find(window, f"digit_{digit}"))
    _click(qtbot, _find(window, "agregar_button"))

    assert "Seleccione un producto" in _find(window, "sale_feedback").text()
    assert _find(window, "purchase_list").text() == ""
    assert _find(window, "purchase_total").text() == "Total: $0.00"


def test_inactive_products_not_listed(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    assert window.findChild(QObject, "sale_product_99") is None
    assert _find(window, "sale_product_1") is not None
    names = [p["nombre"] for p in window._register._active_products]
    assert "Inactivo" not in names


def test_multi_product_flow_with_quantity_and_price_search(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_1"))
    _click(qtbot, _find(window, "sale_product_1"))
    _click(qtbot, _find(window, "quantity_plus_button"))
    assert _find(window, "quantity_label").text() == "2"
    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_list").text() == _line_text("Pan", 5000, 2)
    assert _find(window, "sale_feedback").text() == ""

    for digit in "3000":
        _click(qtbot, _find(window, f"digit_{digit}"))
    assert _find(window, "price_search_product_2") is not None
    _click(qtbot, _find(window, "price_search_product_2"))
    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_list").text() == (
        f"{_line_text('Pan', 5000, 2)}\n{_line_text('Café', 3000)}"
    )
    assert _find(window, "purchase_total").text() == "Total: $ 13.000"


def test_volver_keeps_draft_success_clears(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_product_1"))
    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_list").text() == _line_text("Pan", 5000)

    _click(qtbot, _find(window, "back_button"))
    assert window._stack.currentWidget() is window._menu
    _click(qtbot, _find(window, "menu_register_button"))
    assert _find(window, "purchase_list").text() == _line_text("Pan", 5000)

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
    assert api.sales[0]["valor_total"] == 5000
    assert api.sales[0]["lineas"][0]["id_producto"] == 1
    assert _find(window, "selected_product_label").text() == "Sin producto seleccionado"
    assert _find(window, "sale_feedback").text() == ""
    assert _find(window, "quantity_label").text() == "1"
