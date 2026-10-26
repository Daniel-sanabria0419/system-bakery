"""Etapa 4: UI cobro — modo valor Pan pequeño y preview de redondeo."""

from PySide6.QtCore import Qt

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

    _click(qtbot, _find(window, "sale_product_4"))
    assert _find(window, "price_search_scroll").isHidden() is True
    assert _find(window, "price_search_caption").isHidden() is True
    assert _find(window, "quantity_label").text() == "1"
    assert _find(window, "quantity_value_label").text() == format_cop(300)

    for digit in "1900":
        _click(qtbot, _find(window, f"digit_{digit}"))

    preview = _find(window, "sale_value_preview").text()
    assert format_cop(1900) in preview
    assert format_cop(2000) in preview
    assert "7 panes" in preview
    assert "redondeo" in preview
    assert _find(window, "quantity_label").text() == "7"
    assert _find(window, "quantity_value_label").text() == format_cop(2000)
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

    _click(qtbot, _find(window, "sale_product_4"))
    for _ in range(5):
        _click(qtbot, _find(window, "quantity_plus_button"))
    assert _find(window, "quantity_label").text() == "6"
    assert _find(window, "quantity_value_label").text() == format_cop(1800)
    assert "6 panes" in _find(window, "sale_value_preview").text()

    _click(qtbot, _find(window, "quantity_plus_button"))
    assert _find(window, "quantity_label").text() == "7"
    assert _find(window, "quantity_value_label").text() == format_cop(2000)

    _click(qtbot, _find(window, "quantity_plus_button"))
    assert _find(window, "quantity_label").text() == "8"
    assert _find(window, "quantity_value_label").text() == format_cop(2400)

    _click(qtbot, _find(window, "quantity_minus_button"))
    assert _find(window, "quantity_label").text() == "7"
    assert _find(window, "quantity_value_label").text() == format_cop(2000)


def test_other_category_keeps_price_search_and_no_promo(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_product_5"))
    assert _find(window, "price_search_scroll").isHidden() is False
    assert _find(window, "price_search_caption").isHidden() is False
    assert NOMBRE_CATEGORIA_PAN_PEQUENO not in (
        _find(window, "selected_product_label").text()
    )
    _click(qtbot, _find(window, "quantity_plus_button"))
    _click(qtbot, _find(window, "quantity_plus_button"))
    assert _find(window, "quantity_label").text() == "3"
    assert _find(window, "quantity_value_label").text() == format_cop(60000)
    assert _find(window, "sale_value_preview").text() == ""

    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_list").text() == _line_text("Torta", 20000, 3)
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(60000)}"

    for digit in "5000":
        _click(qtbot, _find(window, f"digit_{digit}"))
    assert _find(window, "price_search_product_1") is not None


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
