"""Pruebas Pan pequeño: categoría, precio $300 y cobro por nudos."""

import pytest

from bakery.app.pan_pequeno_pricing import (
    PRECIO_UNITARIO_PAN_PEQUENO,
    is_pan_pequeno,
    is_pan_pequeno_nombre,
)
from bakery.app.promotions import amount_for_quantity
from bakery.persistence.schema import (
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    PROMOCION_PAN_PEQUENO_CONFIG,
)


def test_constants() -> None:
    assert PRECIO_UNITARIO_PAN_PEQUENO == 300


def test_is_pan_pequeno_by_name_and_mapping() -> None:
    assert is_pan_pequeno(NOMBRE_CATEGORIA_PAN_PEQUENO) is True
    assert is_pan_pequeno_nombre(NOMBRE_CATEGORIA_PAN_PEQUENO) is True
    assert is_pan_pequeno({"nombre": NOMBRE_CATEGORIA_PAN_PEQUENO, "id_categoria": 6}) is True
    assert is_pan_pequeno("Panadería") is False
    assert is_pan_pequeno({"nombre": "Bebidas"}) is False
    assert is_pan_pequeno(None) is False
    assert is_pan_pequeno_nombre(None) is False
    assert is_pan_pequeno("pan pequeño") is False


@pytest.mark.parametrize(
    ("cantidad", "subtotal"),
    [
        (1, 300),
        (2, 600),
        (3, 900),
        (5, 1500),
        (6, 1800),
        (8, 2400),
        (9, 2700),
        (12, 3600),
    ],
)
def test_subtotal_cantidades_normales(cantidad: int, subtotal: int) -> None:
    assert amount_for_quantity(cantidad, PROMOCION_PAN_PEQUENO_CONFIG) == subtotal


@pytest.mark.parametrize(
    ("cantidad", "subtotal"),
    [
        (4, 1000),
        (7, 2000),
        (10, 3000),
        (14, 4000),
        (17, 5000),
        (20, 6000),
        (24, 7000),
        (27, 8000),
        (30, 9000),
        (34, 10000),
    ],
)
def test_subtotal_tabla_ceil(cantidad: int, subtotal: int) -> None:
    assert amount_for_quantity(cantidad, PROMOCION_PAN_PEQUENO_CONFIG) == subtotal


@pytest.mark.parametrize(
    ("cantidad", "subtotal"),
    [
        (6, 1800),
        (7, 2000),
        (8, 2400),
        (13, 3900),
        (14, 4000),
        (15, 4500),
        (17, 5000),
        (20, 6000),
        (21, 6300),
        (22, 6600),
        (24, 7000),
        (27, 8000),
        (28, 8400),
        (29, 8700),
        (34, 10000),
        (35, 10500),
        (36, 10800),
    ],
)
def test_subtotal_transiciones_plus_minus(cantidad: int, subtotal: int) -> None:
    assert amount_for_quantity(cantidad, PROMOCION_PAN_PEQUENO_CONFIG) == subtotal


def test_subtotal_rejects_non_positive_and_non_int() -> None:
    with pytest.raises(ValueError):
        amount_for_quantity(0, PROMOCION_PAN_PEQUENO_CONFIG)
    with pytest.raises(ValueError):
        amount_for_quantity(-1, PROMOCION_PAN_PEQUENO_CONFIG)
    with pytest.raises(ValueError):
        amount_for_quantity(True, PROMOCION_PAN_PEQUENO_CONFIG)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        amount_for_quantity(2.5, PROMOCION_PAN_PEQUENO_CONFIG)  # type: ignore[arg-type]
