"""Pruebas obligatorias del módulo Pan pequeño (scope Beta 2.0.1 §20)."""

import pytest

from bakery.app.pan_pequeno_pricing import (
    PRECIO_UNITARIO_PAN_PEQUENO,
    PROMO_CANTIDAD,
    PROMO_VALOR,
    is_pan_pequeno,
    is_pan_pequeno_nombre,
    quantity_from_value,
    subtotal_for_quantity,
)
from bakery.persistence.schema import NOMBRE_CATEGORIA_PAN_PEQUENO


def test_constants() -> None:
    assert PRECIO_UNITARIO_PAN_PEQUENO == 300
    assert PROMO_CANTIDAD == 7
    assert PROMO_VALOR == 2000


def test_is_pan_pequeno_by_name_and_mapping() -> None:
    assert is_pan_pequeno(NOMBRE_CATEGORIA_PAN_PEQUENO) is True
    assert is_pan_pequeno_nombre(NOMBRE_CATEGORIA_PAN_PEQUENO) is True
    assert is_pan_pequeno({"nombre": NOMBRE_CATEGORIA_PAN_PEQUENO, "id_categoria": 6}) is True
    assert is_pan_pequeno("Panadería") is False
    assert is_pan_pequeno({"nombre": "Bebidas"}) is False
    assert is_pan_pequeno(None) is False
    assert is_pan_pequeno_nombre(None) is False
    assert is_pan_pequeno("pan pequeño") is False  # exacto, no case-fold


# --- §20 cantidades normales ---


@pytest.mark.parametrize(
    ("cantidad", "subtotal"),
    [
        (1, 300),
        (2, 600),
        (6, 1800),
        (8, 2400),
        (13, 3900),
        (15, 4500),
    ],
)
def test_subtotal_cantidades_normales(cantidad: int, subtotal: int) -> None:
    assert subtotal_for_quantity(cantidad) == subtotal


# --- §20 promociones (solo múltiplos de 7) ---


@pytest.mark.parametrize(
    ("cantidad", "subtotal"),
    [
        (7, 2000),
        (14, 4000),
        (21, 6000),
        (28, 8000),
        (35, 10000),
    ],
)
def test_subtotal_promociones(cantidad: int, subtotal: int) -> None:
    assert subtotal_for_quantity(cantidad) == subtotal


# --- §20 entrada mediante valor (exacta) ---


@pytest.mark.parametrize(
    ("valor", "cantidad", "subtotal_ref"),
    [
        (1800, 6, 1800),
        (2000, 7, 2000),
        (2400, 8, 2400),
        (9000, 30, 9000),
        # ceil(10000/300)=34; ref todo_o_nada(34)=10200 (pad conserva tipado).
        (10000, 34, 10200),
    ],
)
def test_quantity_from_value_exacta(
    valor: int, cantidad: int, subtotal_ref: int
) -> None:
    assert quantity_from_value(valor) == (cantidad, subtotal_ref)


# --- §20 redondeo hacia arriba (ceil valor/precio_base) ---


@pytest.mark.parametrize(
    ("valor", "cantidad", "subtotal_ref"),
    [
        (1900, 7, 2000),  # ceil(1900/300)=7; ref todo_o_nada=2000
        (2100, 7, 2000),  # ceil(2100/300)=7 (ya no busca amount≥valor → 8)
        (3950, 14, 4000),
        (5000, 17, 5100),  # ceil(5000/300)=17
        (8000, 27, 8100),  # ceil(8000/300)=27
        (9950, 34, 10200),
    ],
)
def test_quantity_from_value_redondeo_ceil(
    valor: int, cantidad: int, subtotal_ref: int
) -> None:
    assert quantity_from_value(valor) == (cantidad, subtotal_ref)


# --- §20 transiciones +/- (cantidad → subtotal) ---


@pytest.mark.parametrize(
    ("cantidad", "subtotal"),
    [
        (6, 1800),
        (7, 2000),
        (8, 2400),
        (13, 3900),
        (14, 4000),
        (15, 4500),
        (20, 6000),
        (21, 6000),
        (22, 6600),
        (27, 8100),
        (28, 8000),
        (29, 8700),
        (34, 10200),
        (35, 10000),
        (36, 10800),
    ],
)
def test_subtotal_transiciones_plus_minus(cantidad: int, subtotal: int) -> None:
    assert subtotal_for_quantity(cantidad) == subtotal


def test_subtotal_rejects_non_positive_and_non_int() -> None:
    with pytest.raises(ValueError):
        subtotal_for_quantity(0)
    with pytest.raises(ValueError):
        subtotal_for_quantity(-1)
    with pytest.raises(ValueError):
        subtotal_for_quantity(True)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        subtotal_for_quantity(2.5)  # type: ignore[arg-type]


def test_quantity_from_value_rejects_invalid() -> None:
    with pytest.raises(ValueError):
        quantity_from_value(0)
    with pytest.raises(ValueError):
        quantity_from_value(-100)
    with pytest.raises(ValueError):
        quantity_from_value(True)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        quantity_from_value(1000.0)  # type: ignore[arg-type]


def test_quantity_from_value_is_ceil_precio_base() -> None:
    """Qty = ceil(valor/300); el 2.º valor es ref. todo_o_nada (puede ser < tipado)."""
    assert quantity_from_value(1900) == (7, 2000)
    assert quantity_from_value(2100) == (7, 2000)
    assert quantity_from_value(5000) == (17, 5100)
    assert quantity_from_value(8000) == (27, 8100)
    # 34 panes, no 35 packs exactos; ref cobro 10200 ≠ tipado 10000.
    assert quantity_from_value(10000) == (34, 10200)
    assert quantity_from_value(9950) == (34, 10200)
    for valor, cantidad, _ref in (
        (1900, 7, 2000),
        (2100, 7, 2000),
        (10000, 34, 10200),
    ):
        assert cantidad == (valor + 299) // 300
        assert quantity_from_value(valor)[1] == subtotal_for_quantity(cantidad)
