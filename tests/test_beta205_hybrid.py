"""Promo greedy packs + agrupación de carrito por promocion_id."""

from __future__ import annotations

import json

import pytest

from bakery.app import promotions as promotions_mod
from bakery.app.promotions import amount_for_cart_group, compute_cart_line_subtotals
from bakery.app.purchase import SaleDraft
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    PROMOCION_PAN_PEQUENO_CONFIG,
    TIPO_PROMOCION_CANTIDAD_POR_MONTO,
)

CANONICAL = PROMOCION_PAN_PEQUENO_CONFIG


@pytest.fixture(autouse=True)
def _flag_on(monkeypatch):
    monkeypatch.delenv("BAKERY_USE_PROMOCIONES_TABLE", raising=False)
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", True)


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
            2000,
        ),
        ([{"id_producto": 1, "cantidad": 8}], 2300),
        ([{"id_producto": 1, "cantidad": 17}], 4900),
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
            2300,
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
def test_greedy_amount_cases(lines, expected) -> None:
    assert amount_for_cart_group(lines, CANONICAL) == expected


def test_same_sku_two_lines_aggregate_to_exact() -> None:
    """4+3 del mismo id_producto → qty 7 → 2000."""
    assert (
        amount_for_cart_group(
            [
                {"id_producto": 1, "cantidad": 4},
                {"id_producto": 1, "cantidad": 3},
            ],
            CANONICAL,
        )
        == 2000
    )


def test_draft_7_plus_5_is_3500() -> None:
    draft = SaleDraft()
    draft.select_product(_pan(1, "Chino"))
    draft.set_quantity(7)
    assert draft.add_to_purchase() is True
    draft.select_product(_pan(2, "Calado"))
    draft.set_quantity(5)
    assert draft.add_to_purchase() is True
    assert draft.total() == 3500
    assert sum(item.subtotal for item in draft.purchase.items()) == 3500


def test_draft_4_plus_3_still_2000() -> None:
    draft = SaleDraft()
    draft.select_product(_pan(1, "A"))
    draft.set_quantity(4)
    draft.add_to_purchase()
    draft.select_product(_pan(2, "B"))
    draft.set_quantity(3)
    draft.add_to_purchase()
    assert draft.total() == 2000


def test_draft_eight_alone_2300() -> None:
    draft = SaleDraft()
    draft.select_product(_pan(1, "A"))
    draft.set_quantity(8)
    draft.add_to_purchase()
    assert draft.total() == 2300
    assert draft.discount() == 100


def test_draft_seventeen_is_4900() -> None:
    draft = SaleDraft()
    draft.select_product(_pan(1, "A"))
    draft.set_quantity(17)
    draft.add_to_purchase()
    assert draft.total() == 4900
    assert draft.list_subtotal() == 5100
    assert draft.discount() == 200


def test_preview_selection_unchanged_before_add() -> None:
    """Preview de selección como si fuera sola; total definitivo tras Agregar."""
    draft = SaleDraft()
    draft.select_product(_pan(1, "A"))
    draft.set_quantity(4)
    draft.add_to_purchase()
    draft.select_product(_pan(2, "B"))
    draft.set_quantity(3)
    assert draft.current_subtotal() == 900  # 3×300 preview sola
    assert draft.add_to_purchase() is True
    assert draft.total() == 2000


def test_compute_subtotals_sum_matches_greedy() -> None:
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
    assert sum(subs) == 3500
