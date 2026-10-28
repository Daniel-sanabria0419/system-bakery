"""Pruebas Pan pequeño: cobro por escala ceil + valor→qty."""

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
    assert is_pan_pequeno("pan pequeño") is False


@pytest.mark.parametrize(
    ("cantidad", "subtotal"),
    [
        (1, 1000),
        (2, 1000),
        (6, 2000),
        (8, 3000),
        (13, 4000),
        (15, 5000),
    ],
)
def test_subtotal_cantidades_normales(cantidad: int, subtotal: int) -> None:
    assert subtotal_for_quantity(cantidad) == subtotal


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
    assert subtotal_for_quantity(cantidad) == subtotal


@pytest.mark.parametrize(
    ("valor", "cantidad", "subtotal_ref"),
    [
        (1800, 6, 2000),
        (2000, 7, 2000),
        (2400, 8, 3000),
        (9000, 30, 9000),
        (10000, 34, 10000),
    ],
)
def test_quantity_from_value_exacta(
    valor: int, cantidad: int, subtotal_ref: int
) -> None:
    assert quantity_from_value(valor) == (cantidad, subtotal_ref)


@pytest.mark.parametrize(
    ("valor", "cantidad", "subtotal_ref"),
    [
        (1900, 7, 2000),
        (2100, 7, 2000),
        (3950, 14, 4000),
        (5000, 17, 5000),
        (7000, 24, 7000),
        (8000, 27, 8000),
        (9950, 34, 10000),
    ],
)
def test_quantity_from_value_redondeo_ceil(
    valor: int, cantidad: int, subtotal_ref: int
) -> None:
    assert quantity_from_value(valor) == (cantidad, subtotal_ref)


@pytest.mark.parametrize(
    ("cantidad", "subtotal"),
    [
        (6, 2000),
        (7, 2000),
        (8, 3000),
        (13, 4000),
        (14, 4000),
        (15, 5000),
        (17, 5000),
        (20, 6000),
        (21, 7000),
        (22, 7000),
        (24, 7000),
        (27, 8000),
        (28, 9000),
        (29, 9000),
        (34, 10000),
        (35, 11000),
        (36, 11000),
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
    """Qty = ceil(valor/300); el cobro es la escala de esa qty."""
    assert quantity_from_value(1900) == (7, 2000)
    assert quantity_from_value(2100) == (7, 2000)
    assert quantity_from_value(5000) == (17, 5000)
    assert quantity_from_value(7000) == (24, 7000)
    assert quantity_from_value(8000) == (27, 8000)
    assert quantity_from_value(10000) == (34, 10000)
    assert quantity_from_value(9950) == (34, 10000)
    for valor, cantidad, _ref in (
        (1900, 7, 2000),
        (5000, 17, 5000),
        (10000, 34, 10000),
    ):
        assert cantidad == (valor + 299) // 300
        assert quantity_from_value(valor)[1] == subtotal_for_quantity(cantidad)


def test_daniel_ceil_table_value_to_qty() -> None:
    """Tabla ceil(monto/300) de Daniel: valor→qty sin cambio."""
    table = {
        1000: 4,
        2000: 7,
        3000: 10,
        4000: 14,
        5000: 17,
        6000: 20,
        7000: 24,
        8000: 27,
        9000: 30,
        10000: 34,
    }
    for valor, qty in table.items():
        got, _ref = quantity_from_value(valor)
        assert got == qty
        assert got == (valor + 299) // 300
