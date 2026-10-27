"""Beta 2.0.3 Etapa 1: Vista A categorías / Vista B productos + volver."""

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from bakery.desktop import style
from bakery.desktop.main import create_window
from tests.test_stage4_desktop import FakeApiClient, _click, _find


def test_vista_a_on_open_hides_products_shows_categories(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    QApplication.processEvents()

    assert _find(window, "catalog_categories_section").isVisibleTo(window)
    assert not _find(window, "catalog_products_section").isVisibleTo(window)
    assert not _find(window, "catalog_sections_divider").isVisibleTo(window)
    assert not _find(window, "catalog_back_to_categories").isVisibleTo(window)
    # Vista A: Todos y categorías sin estilo seleccionado.
    todos = _find(window, "sale_category_todos")
    assert todos.property("class") == "category-chip"
    assert _find(window, "sale_category_1").property("class") == "category-chip"
    # El ← de página (menú) sigue presente y distinto del volver-catálogo.
    assert _find(window, "back_button").isVisibleTo(window)


def test_category_and_todos_enter_vista_b_with_back(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_2"))
    QApplication.processEvents()
    assert not _find(window, "catalog_categories_section").isVisibleTo(window)
    assert _find(window, "catalog_products_section").isVisibleTo(window)
    back = _find(window, "catalog_back_to_categories")
    assert back.isVisibleTo(window)
    assert back.width() == style.PRODUCT_CHIP_WIDTH
    assert back.height() == style.PRODUCT_CHIP_HEIGHT
    assert back.property("class") == "product-chip"
    assert window._register._products_layout.itemAt(0).widget() is back
    assert window.findChild(QObject, "sale_product_2") is not None
    assert window.findChild(QObject, "sale_product_1") is None

    _click(qtbot, back)
    QApplication.processEvents()
    assert _find(window, "catalog_categories_section").isVisibleTo(window)
    assert not _find(window, "catalog_products_section").isVisibleTo(window)
    assert _find(window, "sale_category_todos").property("class") == "category-chip"

    _click(qtbot, _find(window, "sale_category_todos"))
    QApplication.processEvents()
    assert not _find(window, "catalog_categories_section").isVisibleTo(window)
    assert _find(window, "catalog_products_section").isVisibleTo(window)
    assert window.findChild(QObject, "sale_product_1") is not None
    assert window.findChild(QObject, "sale_product_2") is not None


def test_back_to_categories_clears_category_filter_for_next_pick(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_2"))
    QApplication.processEvents()
    assert window.findChild(QObject, "sale_product_1") is None

    _click(qtbot, _find(window, "catalog_back_to_categories"))
    _click(qtbot, _find(window, "sale_category_1"))
    QApplication.processEvents()
    assert window.findChild(QObject, "sale_product_1") is not None
    assert window.findChild(QObject, "sale_product_2") is None


def test_page_back_button_still_returns_to_menu(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    assert window._stack.currentWidget() is window._register

    _click(qtbot, _find(window, "sale_category_todos"))
    QApplication.processEvents()
    assert _find(window, "catalog_back_to_categories").isVisibleTo(window)

    _click(qtbot, _find(window, "back_button"))
    assert window._stack.currentWidget() is window._menu
