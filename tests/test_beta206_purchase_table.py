"""Beta 2.0.6 Etapa 3: tabla de compra, X por fila, footer Subtotal/Descuento/Total."""

from __future__ import annotations

import json

from bakery.app import promotions as promotions_mod
from bakery.app.money import format_cop
from bakery.desktop.main import create_window
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    PROMOCION_PAN_PEQUENO_CONFIG,
    TIPO_PROMOCION_CANTIDAD_POR_MONTO,
)
from tests.test_stage4_desktop import (
    FakeApiClient,
    _click,
    _find,
    _purchase_list_text,
    _purchase_row_count,
)


def _promo_fields() -> dict:
    return {
        "promocion_id": 1,
        "promocion_tipo": TIPO_PROMOCION_CANTIDAD_POR_MONTO,
        "promocion_configuracion": json.dumps(
            PROMOCION_PAN_PEQUENO_CONFIG, separators=(",", ":"), sort_keys=True
        ),
        "promocion_activo": ESTADO_ACTIVO,
    }


def _api_pan() -> FakeApiClient:
    promo = _promo_fields()
    return FakeApiClient(
        categories=[
            {"id_categoria": 1, "nombre": "Panadería"},
            {"id_categoria": 6, "nombre": NOMBRE_CATEGORIA_PAN_PEQUENO},
        ],
        products=[
            {
                "id_producto": 10,
                "nombre": "Pan A",
                "precio": 300,
                "id_categoria": 6,
                "descripcion": None,
                "id_estado": 1,
                **promo,
            },
            {
                "id_producto": 11,
                "nombre": "Pan B",
                "precio": 300,
                "id_categoria": 6,
                "descripcion": None,
                "id_estado": 1,
                **promo,
            },
            {
                "id_producto": 20,
                "nombre": "Torta",
                "precio": 4500,
                "id_categoria": 1,
                "descripcion": None,
                "id_estado": 1,
            },
        ],
    )


def _set_quantity(qtbot, window, quantity: int) -> None:
    current = int(_find(window, "quantity_label").text())
    while current < quantity:
        _click(qtbot, _find(window, "quantity_plus_button"))
        current += 1
    while current > quantity:
        _click(qtbot, _find(window, "quantity_minus_button"))
        current -= 1


def _assert_footer(window, *, subtotal: int, discount: int, total: int) -> None:
    assert _find(window, "purchase_subtotal").text() == (
        f"Subtotal: {format_cop(subtotal)}"
    )
    assert _find(window, "purchase_discount").text() == (
        f"Descuento: {format_cop(discount)}"
    )
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(total)}"


def test_table_headers_visible(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    assert _find(window, "purchase_table_header") is not None
    assert _find(window, "purchase_header_producto").text() == "Producto"
    assert _find(window, "purchase_header_cantidad").text() == "Cantidad"
    assert _find(window, "purchase_header_precio").text() == "Precio c/u"
    assert _find(window, "purchase_header_total").text() == "Total"
    _assert_footer(window, subtotal=0, discount=0, total=0)


def test_footer_7_panes_descuento_100(qtbot, monkeypatch) -> None:
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", True)
    api = _api_pan()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_10"))
    _set_quantity(qtbot, window, 7)
    _click(qtbot, _find(window, "agregar_button"))

    assert _purchase_row_count(window) == 1
    assert _find(window, "purchase_row_0_producto").text() == "Pan A"
    assert _find(window, "purchase_row_0_cantidad").text() == "7"
    assert _find(window, "purchase_row_0_precio").text() == format_cop(300)
    assert _find(window, "purchase_row_0_total").text() == format_cop(2000)
    assert _find(window, "purchase_row_0_delete") is not None
    _assert_footer(window, subtotal=2100, discount=100, total=2000)


def test_footer_8_panes_descuento_0(qtbot, monkeypatch) -> None:
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", True)
    api = _api_pan()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_10"))
    _set_quantity(qtbot, window, 8)
    _click(qtbot, _find(window, "agregar_button"))
    _assert_footer(window, subtotal=2400, discount=0, total=3000)


def test_footer_4_plus_3_and_delete_recalculates(qtbot, monkeypatch) -> None:
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", True)
    api = _api_pan()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_10"))
    _set_quantity(qtbot, window, 4)
    _click(qtbot, _find(window, "agregar_button"))
    _click(qtbot, _find(window, "sale_product_11"))
    _set_quantity(qtbot, window, 3)
    _click(qtbot, _find(window, "agregar_button"))

    assert _purchase_row_count(window) == 2
    _assert_footer(window, subtotal=2100, discount=100, total=2000)

    _click(qtbot, _find(window, "sale_product_20"))
    assert _find(window, "selected_product_label").text() == "Torta"

    _click(qtbot, _find(window, "purchase_row_0_delete"))
    assert _purchase_row_count(window) == 1
    assert _find(window, "purchase_row_0_producto").text() == "Pan B"
    _assert_footer(window, subtotal=900, discount=0, total=1000)
    # X no toca selección ni medio.
    assert _find(window, "selected_product_label").text() == "Torta"


def test_footer_sin_promo_descuento_0(qtbot, monkeypatch) -> None:
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", True)
    api = _api_pan()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_20"))
    _set_quantity(qtbot, window, 2)
    _click(qtbot, _find(window, "agregar_button"))
    assert _purchase_list_text(window) == (
        f"Torta × 2 — {format_cop(9000)}"
    )
    _assert_footer(window, subtotal=9000, discount=0, total=9000)
