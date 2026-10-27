"""UI cobro — modo valor Pan pequeño, prefijo sin selección, cantidad otras."""

from PySide6.QtCore import QObject

from bakery.app.money import format_cop
from bakery.desktop.main import create_window
from bakery.persistence.schema import NOMBRE_CATEGORIA_PAN_PEQUENO
from tests.test_stage4_desktop import FakeApiClient, _click, _find, _line_text


def test_pan_pequeno_value_1900_previews_ceil_before_add(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_4"))
    assert window.findChild(QObject, "price_search_scroll") is None
    assert window.findChild(QObject, "price_search_caption") is None
    assert _find(window, "quantity_label").text() == "1"
    assert _find(window, "selected_product_label").text() == "Pan rollo"
    assert _find(window, "selected_product_unit_price").text() == (
        f"Unitario: {format_cop(300)}"
    )
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(300)}"
    )

    for digit in "1900":
        _click(qtbot, _find(window, f"digit_{digit}"))

    preview = _find(window, "sale_value_preview").text()
    assert format_cop(1900) in preview
    assert format_cop(2000) in preview
    assert "7 panes" in preview
    assert "redondeo" in preview
    assert _find(window, "quantity_label").text() == "7"
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(2000)}"
    )
    assert _find(window, "purchase_list").text() == ""

    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_list").text() == (
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
        f"Subtotal: {format_cop(2400)}"
    )

    _click(qtbot, _find(window, "quantity_minus_button"))
    assert _find(window, "quantity_label").text() == "7"
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(2000)}"
    )


def test_other_category_qty_only_no_promo_and_prefix_after_add(qtbot) -> None:
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
    assert _find(window, "sale_display").text() == format_cop(20000)
    _click(qtbot, _find(window, "quantity_plus_button"))
    _click(qtbot, _find(window, "quantity_plus_button"))
    assert _find(window, "quantity_label").text() == "3"
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(60000)}"
    )
    assert _find(window, "sale_display").text() == format_cop(60000)
    assert _find(window, "sale_value_preview").text() == ""

    _click(qtbot, _find(window, "digit_5"))
    assert "Use −/+" in _find(window, "sale_feedback").text()
    assert _find(window, "sale_display").text() == format_cop(60000)
    assert _find(window, "quantity_label").text() == "3"

    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_list").text() == _line_text("Torta", 20000, 3)
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(60000)}"

    _click(qtbot, _find(window, "catalog_back_to_categories"))
    _click(qtbot, _find(window, "sale_category_todos"))
    for digit in "5000":
        _click(qtbot, _find(window, f"digit_{digit}"))
    assert _find(window, "sale_product_1") is not None
    assert window.findChild(QObject, "sale_product_2") is None
    assert window.findChild(QObject, "sale_product_5") is None


def test_pad_shows_subtotal_and_pan_pequeno_typed_value(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_5"))
    assert _find(window, "sale_display").text() == format_cop(20000)
    _click(qtbot, _find(window, "quantity_plus_button"))
    assert _find(window, "sale_display").text() == format_cop(40000)

    _click(qtbot, _find(window, "clear_button"))
    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_4"))
    assert _find(window, "sale_display").text() == format_cop(300)
    for digit in "2000":
        _click(qtbot, _find(window, f"digit_{digit}"))
    assert _find(window, "sale_display").text() == format_cop(2000)
    assert _find(window, "quantity_label").text() == "7"
    _click(qtbot, _find(window, "quantity_plus_button"))
    assert _find(window, "quantity_label").text() == "8"
    assert _find(window, "sale_display").text() == format_cop(2400)


def test_reject_agregar_without_product_still_works(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    for digit in "1900":
        _click(qtbot, _find(window, f"digit_{digit}"))
    _click(qtbot, _find(window, "agregar_button"))
    assert "Seleccione un producto" in _find(window, "sale_feedback").text()
    assert _find(window, "purchase_list").text() == ""


def test_prefix_filters_product_grid_without_selection(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    assert _find(window, "sale_product_1") is not None
    assert _find(window, "sale_product_2") is not None

    for digit in "3":
        _click(qtbot, _find(window, f"digit_{digit}"))
    assert _find(window, "sale_product_2") is not None
    assert _find(window, "sale_product_4") is not None
    assert window.findChild(QObject, "sale_product_1") is None

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
    # Sin imagen en fake: no crashea.
    image = _find(window, "selected_product_image")
    pixmap = image.pixmap()
    assert pixmap is None or pixmap.isNull()
