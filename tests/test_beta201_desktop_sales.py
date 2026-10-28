"""UI cobro — cantidad −/+, sin pad (Beta 2.0.6 Etapa 2)."""

import pytest
from PySide6.QtCore import QObject

from bakery.app.money import format_cop
from bakery.desktop.main import create_window
from bakery.persistence.schema import NOMBRE_CATEGORIA_PAN_PEQUENO
from tests.test_stage4_desktop import FakeApiClient, _click, _find, _line_text, _purchase_list_text


def test_pan_pequeno_qty_only_with_plus(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_4"))
    assert window.findChild(QObject, "pad_panel") is None
    assert window.findChild(QObject, "price_search_scroll") is None
    assert _find(window, "quantity_label").text() == "1"
    assert _find(window, "selected_product_label").text() == "Pan rollo"
    assert _find(window, "selected_product_unit_price").text() == (
        f"Unitario: {format_cop(300)}"
    )
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(300)}"
    )

    for _ in range(6):
        _click(qtbot, _find(window, "quantity_plus_button"))
    assert _find(window, "quantity_label").text() == "7"
    preview = _find(window, "sale_value_preview").text()
    assert preview == f"{format_cop(2000)} = 7 panes"
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(2000)}"
    )

    _click(qtbot, _find(window, "agregar_button"))
    assert _purchase_list_text(window) == (
        f"Pan rollo × 7 — {format_cop(2000)}"
    )
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(2000)}"


def test_pan_pequeno_plus_minus_transitions_6_7_8(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_4"))
    for _ in range(5):
        _click(qtbot, _find(window, "quantity_plus_button"))
    assert _find(window, "quantity_label").text() == "6"
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(1800)}"
    )
    assert "6 panes" in _find(window, "sale_value_preview").text()

    _click(qtbot, _find(window, "quantity_plus_button"))
    assert _find(window, "quantity_label").text() == "7"
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(2000)}"
    )

    _click(qtbot, _find(window, "quantity_plus_button"))
    assert _find(window, "quantity_label").text() == "8"
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(2300)}"
    )

    _click(qtbot, _find(window, "quantity_minus_button"))
    assert _find(window, "quantity_label").text() == "7"
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(2000)}"
    )


def test_other_category_qty_only_no_promo(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_5"))
    assert window.findChild(QObject, "price_search_scroll") is None
    assert _find(window, "selected_product_label").text() == "Torta"
    assert NOMBRE_CATEGORIA_PAN_PEQUENO not in (
        _find(window, "selected_product_label").text()
    )
    assert _find(window, "selected_product_unit_price").text() == (
        f"Unitario: {format_cop(20000)}"
    )
    _click(qtbot, _find(window, "quantity_plus_button"))
    _click(qtbot, _find(window, "quantity_plus_button"))
    assert _find(window, "quantity_label").text() == "3"
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(60000)}"
    )
    assert _find(window, "sale_value_preview").text() == ""

    _click(qtbot, _find(window, "agregar_button"))
    assert _purchase_list_text(window) == _line_text("Torta", 20000, 3)
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(60000)}"


@pytest.mark.parametrize(
    ("quantity", "expected_subtotal"),
    [
        (17, 4900),
        (27, 7800),
        (34, 9800),
    ],
)
def test_pan_pequeno_qty_uses_promo_formula(
    qtbot, quantity: int, expected_subtotal: int
) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_4"))

    for _ in range(quantity - 1):
        _click(qtbot, _find(window, "quantity_plus_button"))

    assert _find(window, "quantity_label").text() == str(quantity)
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(expected_subtotal)}"
    )
    preview = _find(window, "sale_value_preview").text()
    assert preview == f"{format_cop(expected_subtotal)} = {quantity} panes"

    _click(qtbot, _find(window, "agregar_button"))
    assert _purchase_list_text(window) == (
        f"Pan rollo × {quantity} — {format_cop(expected_subtotal)}"
    )
    assert _find(window, "purchase_total").text() == (
        f"Total: {format_cop(expected_subtotal)}"
    )


def test_reject_agregar_without_product_still_works(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "agregar_button"))
    assert "Seleccione un producto" in _find(window, "sale_feedback").text()
    assert _purchase_list_text(window) == ""


def test_catalog_shows_full_grid_without_price_prefix(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    assert _find(window, "sale_product_1") is not None
    assert _find(window, "sale_product_2") is not None
    assert _find(window, "sale_product_4") is not None

    _click(qtbot, _find(window, "catalog_back_to_categories"))
    _click(qtbot, _find(window, "sale_category_2"))
    assert _find(window, "sale_product_2") is not None
    assert window.findChild(QObject, "sale_product_4") is None


def test_selected_panel_image_unit_subtotal_and_qty_order(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    panel = _find(window, "selected_product_panel")
    assert panel is not None
    assert _find(window, "selected_product_image") is not None
    assert _find(window, "selected_product_label").text() == (
        "Sin producto seleccionado"
    )
    assert _find(window, "selected_product_unit_price").text() == ""
    assert _find(window, "quantity_value_label").text() == ""

    qty_hbox = _find(window, "quantity_section").layout().itemAt(0).layout()
    assert qty_hbox.itemAt(0).widget().objectName() == "quantity_label"
    assert qty_hbox.itemAt(1).widget().objectName() == "quantity_minus_button"
    assert qty_hbox.itemAt(2).widget().objectName() == "quantity_plus_button"

    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_1"))
    assert _find(window, "selected_product_label").text() == "Pan"
    assert _find(window, "selected_product_unit_price").text() == (
        f"Unitario: {format_cop(5000)}"
    )
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(5000)}"
    )
    image = _find(window, "selected_product_image")
    pixmap = image.pixmap()
    assert pixmap is None or pixmap.isNull()
