"""Beta 2.0.4 Etapa 4: UI lista/total tras recálculo de grupo (flag on)."""

from __future__ import annotations

import json
import re

from bakery.app import promotions as promotions_mod
from bakery.app.money import format_cop
from bakery.desktop.main import create_window
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    PROMOCION_PAN_PEQUENO_CONFIG,
    TIPO_PROMOCION_CANTIDAD_POR_MONTO,
)
from tests.test_stage4_desktop import FakeApiClient, _click, _find


def _promo_fields() -> dict:
    return {
        "promocion_id": 1,
        "promocion_tipo": TIPO_PROMOCION_CANTIDAD_POR_MONTO,
        "promocion_configuracion": json.dumps(
            PROMOCION_PAN_PEQUENO_CONFIG, separators=(",", ":"), sort_keys=True
        ),
        "promocion_activo": ESTADO_ACTIVO,
    }


def _api_with_two_pan_products() -> FakeApiClient:
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
                "precio": 20000,
                "id_categoria": 1,
                "descripcion": None,
                "id_estado": 1,
            },
        ],
    )


def _parse_line_subtotals(list_text: str) -> list[int]:
    """Extrae montos enteros de líneas ``nombre × qty — $ X.XXX``."""
    amounts: list[int] = []
    for raw_line in list_text.splitlines():
        if "—" not in raw_line:
            continue
        money = raw_line.split("—", 1)[1].strip()
        digits = re.sub(r"[^\d]", "", money)
        assert digits, f"sin monto en {raw_line!r}"
        amounts.append(int(digits))
    return amounts


def _set_quantity(qtbot, window, quantity: int) -> None:
    current = int(_find(window, "quantity_label").text())
    while current < quantity:
        _click(qtbot, _find(window, "quantity_plus_button"))
        current += 1
    while current > quantity:
        _click(qtbot, _find(window, "quantity_minus_button"))
        current -= 1


def test_desktop_flag_on_4_plus_3_list_and_total_2000(qtbot, monkeypatch) -> None:
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", True)
    api = _api_with_two_pan_products()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_10"))
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(300)}"
    )
    _set_quantity(qtbot, window, 4)
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(1200)}"
    )
    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(1200)}"

    _click(qtbot, _find(window, "sale_product_11"))
    _set_quantity(qtbot, window, 3)
    assert _find(window, "quantity_value_label").text() == (
        f"Subtotal: {format_cop(900)}"
    )
    _click(qtbot, _find(window, "agregar_button"))

    list_text = _find(window, "purchase_list").text()
    assert "Pan A × 4" in list_text
    assert "Pan B × 3" in list_text
    subtotals = _parse_line_subtotals(list_text)
    assert len(subtotals) == 2
    assert sum(subtotals) == 2000
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(2000)}"


def test_desktop_flag_on_4_plus_4_total_2400(qtbot, monkeypatch) -> None:
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", True)
    api = _api_with_two_pan_products()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_10"))
    _set_quantity(qtbot, window, 4)
    _click(qtbot, _find(window, "agregar_button"))
    _click(qtbot, _find(window, "sale_product_11"))
    _set_quantity(qtbot, window, 4)
    _click(qtbot, _find(window, "agregar_button"))

    subtotals = _parse_line_subtotals(_find(window, "purchase_list").text())
    assert sum(subtotals) == 2400
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(2400)}"


def test_desktop_flag_off_4_plus_3_plain_2100(qtbot, monkeypatch) -> None:
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", False)
    monkeypatch.delenv("BAKERY_USE_PROMOCIONES_TABLE", raising=False)
    api = _api_with_two_pan_products()
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

    # Flag off: precio × cantidad (sin agrupación ni path por categoría)
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(2100)}"
    subtotals = _parse_line_subtotals(_find(window, "purchase_list").text())
    assert subtotals == [1200, 900]


def test_env_enables_promociones_path(monkeypatch) -> None:
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", False)
    monkeypatch.setenv("BAKERY_USE_PROMOCIONES_TABLE", "1")
    assert promotions_mod.use_promociones_table() is True
    monkeypatch.setenv("BAKERY_USE_PROMOCIONES_TABLE", "0")
    assert promotions_mod.use_promociones_table() is False
