"""Chips de catálogo, Todos primero, wrap, fondos sección y medios intactos."""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QFrame, QLayout, QPushButton

from bakery.desktop import style
from bakery.desktop.main import create_window
from bakery.desktop.ui import SelectPaymentMethodDialog
from bakery.desktop.ui_helpers import FlowLayout, catalog_chips_per_row
from tests.test_stage4_desktop import FakeApiClient, _click, _find


def _layout_widget(layout: QLayout, object_name: str):
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
    # Vista A: ningún chip seleccionado (Todos tampoco).
    assert first.property("class") == "category-chip"

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

    # Vista B vía Todos: todos los activos.
    _click(qtbot, _find(window, "sale_category_todos"))
    QApplication.processEvents()
    names = _product_object_names(window)
    assert "sale_product_1" in names
    assert "sale_product_2" in names

    _click(qtbot, _find(window, "catalog_back_to_categories"))
    _click(qtbot, _layout_widget(window._register._categories_layout, "sale_category_2"))
    QApplication.processEvents()
    names = _product_object_names(window)
    assert "sale_product_1" not in names
    assert "sale_product_2" in names
    # En Vista B las categorías están ocultas; el filtro sigue aplicado.
    assert window._register._selected_category_id == 2

    _click(qtbot, _find(window, "catalog_back_to_categories"))
    cats = window._register._categories_layout
    assert _layout_widget(cats, "sale_category_todos").property("class") == (
        "category-chip"
    )
    _click(qtbot, _layout_widget(cats, "sale_category_todos"))
    QApplication.processEvents()
    names = _product_object_names(window)
    assert "sale_product_1" in names
    assert "sale_product_2" in names


def test_product_chip_size_selected_and_not_payment_class(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    _click(qtbot, _find(window, "sale_category_todos"))
    QApplication.processEvents()

    back = _layout_widget(
        window._register._products_layout, "catalog_back_to_categories"
    )
    assert back is not None
    assert back.width() == style.PRODUCT_CHIP_WIDTH
    assert back.height() == style.PRODUCT_CHIP_HEIGHT
    assert back.property("class") == "product-chip"
    assert window._register._products_layout.itemAt(0).widget() is back

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

    assert style.CATALOG_SECTION_BACKGROUND == "#d7d4ce"
    assert style.CATALOG_CHIP_COLOR == "#64c466"
    _click(qtbot, _find(window, "catalog_back_to_categories"))
    category = _layout_widget(window._register._categories_layout, "sale_category_1")
    assert category.property("class") != "payment-method-button"
    assert selected.property("class") != "payment-method-button"


def test_catalog_sections_background_divider_and_flow_layout(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    window.resize(1200, 800)
    _click(qtbot, _find(window, "menu_register_button"))
    QApplication.processEvents()

    assert _find(window, "catalog_categories_section").isVisibleTo(window)
    assert not _find(window, "catalog_products_section").isVisibleTo(window)
    divider = _find(window, "catalog_sections_divider")
    assert divider is not None
    assert isinstance(divider, QFrame)
    assert divider.frameShape() == QFrame.HLine
    # 2.0.3: nunca ambas secciones a la vez → divisor oculto.
    assert not divider.isVisibleTo(window)

    assert isinstance(window._register._categories_layout, FlowLayout)
    assert isinstance(window._register._products_layout, FlowLayout)

    host_width = max(window._register._categories_host.width(), 400)
    expected = catalog_chips_per_row(host_width, style.CATEGORY_CHIP_WIDTH)
    assert expected >= 1
    assert style.CATALOG_WRAP_REFERENCE_COLUMNS == 6


def test_catalog_chips_per_row_not_hardcoded_six() -> None:
    narrow = catalog_chips_per_row(200, style.CATEGORY_CHIP_WIDTH)
    wide = catalog_chips_per_row(700, style.CATEGORY_CHIP_WIDTH)
    assert narrow >= 1
    assert wide > narrow


def test_chip_font_constants_injected_into_theme_qss() -> None:
    """Daniel edita fuentes en style.py; load_theme_qss las inyecta en el QSS."""
    assert style.CATEGORY_CHIP_FONT_SIZE >= 14
    assert style.PRODUCT_CHIP_FONT_SIZE >= 14
    assert style.CATEGORY_CHIP_WIDTH >= 100
    assert style.PRODUCT_CHIP_WIDTH >= 100
    qss = style.load_theme_qss()
    assert f"font-size: {style.CATEGORY_CHIP_FONT_SIZE}px" in qss
    assert f"font-size: {style.PRODUCT_CHIP_FONT_SIZE}px" in qss
    assert "__CATEGORY_CHIP_FONT_SIZE__" not in qss
    assert "__PRODUCT_CHIP_FONT_SIZE__" not in qss


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
