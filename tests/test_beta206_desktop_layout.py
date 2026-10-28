"""Beta 2.0.6 Etapa 2: layout sin pad; Agregar / Medio / Borrar todo / Pagar."""

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from bakery.app.money import format_cop
from bakery.desktop.main import create_window
from tests.test_stage4_desktop import FakeApiClient, _click, _find, _line_text, _select_payment


def test_no_pad_panel_or_digits(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    assert window.findChild(QObject, "pad_panel") is None
    assert window.findChild(QObject, "digit_1") is None
    assert window.findChild(QObject, "digit_00") is None
    assert window.findChild(QObject, "sale_display") is None
    assert window.findChild(QObject, "clear_button") is None
    assert window.findChild(QObject, "borrar_button") is None


def test_stable_action_object_names(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    assert _find(window, "agregar_button").text() == "Agregar"
    assert _find(window, "payment_button") is not None
    assert _find(window, "borrar_todo_button").text() == "Borrar todo"
    assert _find(window, "submit_sale_button").text() == "Pagar"
    assert _find(window, "sale_actions_panel") is not None
    assert _find(window, "selected_product_panel") is not None
    assert _find(window, "left_column") is not None
    assert _find(window, "future_panel") is not None


def test_flow_qty_agregar_medio_pagar(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_1"))
    _click(qtbot, _find(window, "quantity_plus_button"))
    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_list").text() == _line_text("Pan", 5000, 2)
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(10000)}"

    assert not _find(window, "submit_sale_button").isEnabled()
    _select_payment(qtbot, window, 1)
    assert _find(window, "submit_sale_button").isEnabled()


def test_borrar_todo_keeps_selection_and_payment(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_1"))
    _click(qtbot, _find(window, "quantity_plus_button"))
    _click(qtbot, _find(window, "agregar_button"))
    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_2"))
    assert _find(window, "selected_product_label").text() == "Café"
    assert _find(window, "quantity_label").text() == "1"
    _select_payment(qtbot, window, 1)

    _click(qtbot, _find(window, "borrar_todo_button"))

    assert _find(window, "purchase_list").text() == ""
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(0)}"
    assert _find(window, "selected_product_label").text() == "Café"
    assert _find(window, "quantity_label").text() == "1"
    assert _find(window, "payment_button").text() == "Medio de pago: Efectivo"
    assert not _find(window, "submit_sale_button").isEnabled()


def test_vista_a_b_intact_without_pad(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    QApplication.processEvents()

    assert window._register._catalog_view == "categories"
    assert _find(window, "catalog_categories_section").isVisible()
    assert not _find(window, "catalog_products_section").isVisible()

    _click(qtbot, _find(window, "sale_category_1"))
    QApplication.processEvents()
    assert window._register._catalog_view == "products"
    assert _find(window, "catalog_back_to_categories") is not None
    assert _find(window, "sale_product_1") is not None

    _click(qtbot, _find(window, "catalog_back_to_categories"))
    QApplication.processEvents()
    assert window._register._catalog_view == "categories"
    assert _find(window, "catalog_categories_section").isVisible()
