"""Etapa 5: chips de catálogo, Todos primero, filtro y medios intactos."""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout

from bakery.desktop import style
from bakery.desktop.main import create_window
from bakery.desktop.ui import SelectPaymentMethodDialog
from tests.test_stage4_desktop import FakeApiClient, _click, _find


def _layout_widget(layout: QVBoxLayout, object_name: str):
    for index in range(layout.count()):
        widget = layout.itemAt(index).widget()
        if widget is not None and widget.objectName() == object_name:
            return widget
    return None


def _product_object_names(window) -> list:
    names = []
    layout = window._register._products_layout
    for index in range(layout.count()):
        widget = layout.itemAt(index).widget()
        if widget is not None and widget.objectName():
            names.append(widget.objectName())
    return names


def test_todos_first_and_category_chip_metrics(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    layout = window._register._categories_layout
    first = layout.itemAt(0).widget()
    assert first is not None
    assert first.objectName() == "sale_category_todos"
    assert first.text() == "Todos"
    assert first.width() == style.CATEGORY_CHIP_WIDTH
    assert first.height() == style.CATEGORY_CHIP_HEIGHT
    assert first.property("class") == "category-chip-selected"

    category = _layout_widget(layout, "sale_category_1")
    assert category is not None
    assert category.width() == style.CATEGORY_CHIP_WIDTH
    assert category.height() == style.CATEGORY_CHIP_HEIGHT
    assert category.property("class") == "category-chip"


def test_category_filter_and_todos_shows_all(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    names = _product_object_names(window)
    assert "sale_product_1" in names
    assert "sale_product_2" in names

    _click(qtbot, _layout_widget(window._register._categories_layout, "sale_category_2"))
    QApplication.processEvents()
    names = _product_object_names(window)
    assert "sale_product_1" not in names
    assert "sale_product_2" in names
    cats = window._register._categories_layout
    assert _layout_widget(cats, "sale_category_2").property("class") == (
        "category-chip-selected"
    )
    assert _layout_widget(cats, "sale_category_todos").property("class") == (
        "category-chip"
    )

    _click(qtbot, _layout_widget(cats, "sale_category_todos"))
    QApplication.processEvents()
    names = _product_object_names(window)
    assert "sale_product_1" in names
    assert "sale_product_2" in names
    assert _layout_widget(
        window._register._categories_layout, "sale_category_todos"
    ).property("class") == "category-chip-selected"


def test_product_chip_size_selected_and_not_payment_class(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    product = _layout_widget(window._register._products_layout, "sale_product_1")
    assert product is not None
    assert product.width() == style.PRODUCT_CHIP_WIDTH
    assert product.height() == style.PRODUCT_CHIP_HEIGHT
    assert product.property("class") == "product-chip"

    _click(qtbot, product)
    QApplication.processEvents()
    selected = _layout_widget(window._register._products_layout, "sale_product_1")
    assert selected is not None
    assert selected.property("class") == "product-chip-selected"

    assert style.CATALOG_BACKGROUND == "#F5F0E8"
    assert style.CATALOG_CHIP_COLOR == "#64c466"
    category = _layout_widget(window._register._categories_layout, "sale_category_1")
    assert category.property("class") != "payment-method-button"
    assert selected.property("class") != "payment-method-button"


def test_payment_method_popup_still_uses_black_buttons(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    seen = {}

    def capture() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, SelectPaymentMethodDialog) and widget.isVisible():
                for child in widget.findChildren(QPushButton):
                    if child.property("class") == "payment-method-button":
                        seen["class"] = child.property("class")
                        seen["name"] = child.objectName()
                        widget.accept()
                        return

    QTimer.singleShot(0, capture)
    _click(qtbot, _find(window, "payment_button"))
    qtbot.waitUntil(lambda: "class" in seen, timeout=2000)
    assert seen["class"] == "payment-method-button"
