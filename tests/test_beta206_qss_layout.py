"""Beta 2.0.6 Etapa 4: stretch catálogo/acciones, QSS sin pad, colores mockup."""

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from bakery.desktop import style
from bakery.desktop.main import create_window
from tests.test_stage4_desktop import FakeApiClient, _click, _find


def test_theme_qss_has_no_pad_selectors() -> None:
    qss = style.load_theme_qss()
    assert "pad-button" not in qss
    assert "#pad_panel" not in qss
    assert "#sale_display" not in qss
    assert "entry_separator" not in qss
    assert style.PAGAR_BUTTON_COLOR in qss
    assert style.BORRAR_TODO_BUTTON_COLOR in qss
    assert str(style.FOOTER_TOTALS_FONT_SIZE) in qss


def test_pad_metrics_removed_from_style() -> None:
    assert not hasattr(style, "PAD_PANEL_STRETCH")
    assert not hasattr(style, "PAD_SPACING")
    assert not hasattr(style, "PAD_BUTTON_MIN_WIDTH")
    assert not hasattr(style, "PAD_BUTTON_MIN_HEIGHT")
    assert style.ACTIONS_PANEL_STRETCH == 0
    assert style.CATALOG_SECTION_STRETCH >= 1


def test_action_buttons_classes_and_min_height(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    QApplication.processEvents()

    pagar = _find(window, "submit_sale_button")
    borrar = _find(window, "borrar_todo_button")
    medio = _find(window, "payment_button")
    assert pagar.property("class") == "pagar-button"
    assert borrar.property("class") == "borrar-todo-button"
    assert medio.property("class") == "payment-button"
    assert pagar.minimumHeight() >= style.ACTION_BUTTON_MIN_HEIGHT
    assert borrar.minimumHeight() >= style.ACTION_BUTTON_MIN_HEIGHT
    assert medio.minimumHeight() >= style.ACTION_BUTTON_MIN_HEIGHT


def test_actions_panel_stretch_zero_vs_catalog(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    QApplication.processEvents()

    right = _find(window, "future_panel")
    layout = right.layout()
    actions = _find(window, "sale_actions_panel")
    actions_index = layout.indexOf(actions)
    assert actions_index >= 0
    assert layout.stretch(actions_index) == style.ACTIONS_PANEL_STRETCH

    categories = _find(window, "catalog_categories_section")
    cat_index = layout.indexOf(categories)
    assert layout.stretch(cat_index) == style.CATALOG_SECTION_STRETCH


def test_vista_a_b_with_actions_visible(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    QApplication.processEvents()

    assert _find(window, "sale_actions_panel").isVisible()
    assert _find(window, "catalog_categories_section").isVisible()

    _click(qtbot, _find(window, "sale_category_1"))
    QApplication.processEvents()
    assert window._register._catalog_view == "products"
    assert _find(window, "sale_actions_panel").isVisible()
    assert _find(window, "catalog_back_to_categories") is not None
    assert window.findChild(QObject, "sale_product_1") is not None

    _click(qtbot, _find(window, "catalog_back_to_categories"))
    QApplication.processEvents()
    assert window._register._catalog_view == "categories"
    assert _find(window, "sale_actions_panel").isVisible()


def test_chips_have_no_plus_overlay_text(qtbot) -> None:
    """Mockup dibuja «+» en chips; 2.0.6 lo ignora — chips solo nombre."""
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    QApplication.processEvents()
    _click(qtbot, _find(window, "sale_category_todos"))
    QApplication.processEvents()

    product = _find(window, "sale_product_1")
    assert "+" not in product.text()
    assert product.text() == "Pan"
