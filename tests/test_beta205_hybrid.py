"""Cobro cantidad_por_monto por línea (cada cantidad se cobra sola)."""

from __future__ import annotations

import json

import pytest

from bakery.app.promotions import amount_for_quantity, compute_cart_line_subtotals
from bakery.app.purchase import SaleDraft
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    PROMOCION_PAN_PEQUENO_CONFIG,
    TIPO_PROMOCION_CANTIDAD_POR_MONTO,
)

CANONICAL = PROMOCION_PAN_PEQUENO_CONFIG


def _line_amounts(lines) -> int:
    return sum(amount_for_quantity(line["cantidad"], CANONICAL) for line in lines)


def _promo() -> dict:
    return {
        "id": 1,
        "tipo": TIPO_PROMOCION_CANTIDAD_POR_MONTO,
        "configuracion": json.dumps(CANONICAL),
        "activo": ESTADO_ACTIVO,
    }


def _pan(id_producto: int, nombre: str) -> dict:
    return {
        "id_producto": id_producto,
        "nombre": nombre,
        "precio": 300,
        "promocion_id": 1,
        "promocion_tipo": TIPO_PROMOCION_CANTIDAD_POR_MONTO,
        "promocion_configuracion": json.dumps(CANONICAL),
        "promocion_activo": ESTADO_ACTIVO,
    }


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        (
            [
                {"id_producto": 1, "cantidad": 7},
                {"id_producto": 2, "cantidad": 5},
            ],
            3500,
        ),
        (
            [
                {"id_producto": 1, "cantidad": 4},
                {"id_producto": 2, "cantidad": 3},
            ],
            1900,
        ),
        ([{"id_producto": 1, "cantidad": 8}], 2400),
        ([{"id_producto": 1, "cantidad": 17}], 5000),
        ([{"id_producto": 1, "cantidad": 24}], 7000),
        ([{"id_producto": 1, "cantidad": 27}], 8000),
        ([{"id_producto": 1, "cantidad": 34}], 10000),
        (
            [
                {"id_producto": 1, "cantidad": 7},
                {"id_producto": 2, "cantidad": 7},
            ],
            4000,
        ),
        (
            [
                {"id_producto": 1, "cantidad": 4},
                {"id_producto": 2, "cantidad": 4},
            ],
            2000,
        ),
        (
            [
                {"id_producto": 1, "cantidad": 10},
                {"id_producto": 2, "cantidad": 4},
            ],
            4000,
        ),
    ],
)
def test_ceil_scale_amount_cases(lines, expected) -> None:
    assert _line_amounts(lines) == expected


def test_same_sku_two_lines_stay_separate() -> None:
    """4 y 3 del mismo id_producto no se juntan: 1000 + 900."""
    assert (
        _line_amounts(
            [
                {"id_producto": 1, "cantidad": 4},
                {"id_producto": 1, "cantidad": 3},
            ]
        )
        == 1900
    )


def test_draft_7_plus_5_keeps_each_line() -> None:
    draft = SaleDraft()
    draft.select_product(_pan(1, "Chino"))
    draft.set_quantity(7)
    assert draft.add_to_purchase() is True
    draft.select_product(_pan(2, "Calado"))
    draft.set_quantity(5)
    assert draft.add_to_purchase() is True
    items = draft.purchase.items()
    assert items[0].subtotal == 2000
    assert items[1].subtotal == 1500
    assert draft.total() == 3500


def test_draft_17_plus_5_keeps_promo_on_first_line() -> None:
    """17 sigue en 5000 al agregar 5; no se arma un grupo de 22."""
    draft = SaleDraft()
    draft.select_product(_pan(1, "A"))
    draft.set_quantity(17)
    assert draft.add_to_purchase() is True
    assert draft.purchase.items()[0].subtotal == 5000
    draft.select_product(_pan(2, "B"))
    draft.set_quantity(5)
    assert draft.add_to_purchase() is True
    items = draft.purchase.items()
    assert items[0].cantidad == 17
    assert items[0].subtotal == 5000
    assert items[1].cantidad == 5
    assert items[1].subtotal == 1500
    assert draft.total() == 6500


def test_draft_4_plus_3_stays_per_line() -> None:
    draft = SaleDraft()
    draft.select_product(_pan(1, "A"))
    draft.set_quantity(4)
    draft.add_to_purchase()
    draft.select_product(_pan(2, "B"))
    draft.set_quantity(3)
    draft.add_to_purchase()
    assert draft.total() == 1900


def test_draft_eight_alone_2400() -> None:
    draft = SaleDraft()
    draft.select_product(_pan(1, "A"))
    draft.set_quantity(8)
    draft.add_to_purchase()
    assert draft.total() == 2400
    assert draft.discount() == 0


def test_draft_17_24_27_34_ceil_scale() -> None:
    for qty, expected in ((17, 5000), (24, 7000), (27, 8000), (34, 10000)):
        draft = SaleDraft()
        draft.select_product(_pan(1, "A"))
        draft.set_quantity(qty)
        assert draft.add_to_purchase() is True
        assert draft.total() == expected
        assert draft.discount() == qty * 300 - expected


def test_preview_selection_unchanged_before_add() -> None:
    """Pad/preview: subtotal de selección como si fuera sola (2.0.4)."""
    draft = SaleDraft()
    draft.select_product(_pan(1, "A"))
    draft.set_quantity(4)
    draft.add_to_purchase()
    draft.select_product(_pan(2, "B"))
    draft.set_quantity(3)
    assert draft.current_subtotal() == 900  # 3 × 300, selección sola
    assert draft.add_to_purchase() is True
    assert draft.total() == 1900


def test_compute_subtotals_17_plus_5() -> None:
    lines = [
        {
            "id_producto": 1,
            "cantidad": 7,
            "precio_aplicado": 300,
            "promocion_id": 1,
        },
        {
            "id_producto": 2,
            "cantidad": 5,
            "precio_aplicado": 300,
            "promocion_id": 1,
        },
    ]
    subs = compute_cart_line_subtotals(lines, promos_by_id={1: _promo()})
    assert subs == [2000, 1500]
    assert sum(subs) == 3500
