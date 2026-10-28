"""Beta 2.0.5: motor híbrido exacto por SKU + pool todo_o_nada."""

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
            4000,
        ),
        (
            [
                {"id_producto": 1, "cantidad": 4},
                {"id_producto": 2, "cantidad": 3},
            ],
            2000,
        ),
        ([{"id_producto": 1, "cantidad": 8}], 3000),
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
            3000,
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
    assert amount_for_cart_group(lines, CANONICAL) == expected


def test_same_sku_two_lines_aggregate_to_exact() -> None:
    """4+3 del mismo id_producto → qty 7 exacta → 2000."""
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


def test_draft_7_plus_5_is_4000() -> None:
    draft = SaleDraft()
    draft.select_product(_pan(1, "Chino"))
    draft.set_quantity(7)
    assert draft.add_to_purchase() is True
    draft.select_product(_pan(2, "Calado"))
    draft.set_quantity(5)
    assert draft.add_to_purchase() is True
    assert draft.total() == 4000
    assert sum(item.subtotal for item in draft.purchase.items()) == 4000


def test_draft_4_plus_3_still_2000() -> None:
    draft = SaleDraft()
    draft.select_product(_pan(1, "A"))
    draft.set_quantity(4)
    draft.add_to_purchase()
    draft.select_product(_pan(2, "B"))
    draft.set_quantity(3)
    draft.add_to_purchase()
    assert draft.total() == 2000


def test_draft_eight_alone_3000() -> None:
    draft = SaleDraft()
    draft.select_product(_pan(1, "A"))
    draft.set_quantity(8)
    draft.add_to_purchase()
    assert draft.total() == 3000
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
    assert draft.current_subtotal() == 1000  # selección sola, antes de agrupar
    assert draft.add_to_purchase() is True
    assert draft.total() == 2000


def test_compute_subtotals_sum_matches_hybrid() -> None:
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
    assert sum(subs) == 4000
