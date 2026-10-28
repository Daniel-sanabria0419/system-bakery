"""Motor cantidad_por_monto por línea (sin dual-path ni pool)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bakery.app.promotions import (
    amount_for_quantity,
    compute_cart_line_subtotals,
    parse_cantidad_por_monto_config,
)
from bakery.app.purchase import SaleDraft
from bakery.app.sales import register_sale
from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.repositories import (
    get_categoria_by_nombre,
    insert_producto,
    list_promociones,
)
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    PROMOCION_PAN_PEQUENO_CONFIG,
    TIPO_PROMOCION_CANTIDAD_POR_MONTO,
)


CANONICAL = PROMOCION_PAN_PEQUENO_CONFIG


def _line_amounts(lines, config) -> int:
    return sum(amount_for_quantity(line["cantidad"], config) for line in lines)


@pytest.mark.parametrize(
    ("cantidad", "subtotal"),
    [
        (1, 300),
        (3, 900),
        (4, 1000),
        (5, 1500),
        (6, 1800),
        (7, 2000),
        (8, 2400),
        (9, 2700),
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
def test_amount_for_quantity_knots_and_plain(
    cantidad: int, subtotal: int
) -> None:
    assert amount_for_quantity(cantidad, CANONICAL) == subtotal


def test_parse_config_rejects_invalid() -> None:
    with pytest.raises(ValueError):
        parse_cantidad_por_monto_config("{")
    with pytest.raises(ValueError):
        parse_cantidad_por_monto_config({**CANONICAL, "modo": "floor"})
    with pytest.raises(ValueError):
        parse_cantidad_por_monto_config({**CANONICAL, "grupo_cantidad": 7})
    with pytest.raises(ValueError):
        parse_cantidad_por_monto_config({**CANONICAL, "grupo_monto": 2000})
    with pytest.raises(ValueError):
        parse_cantidad_por_monto_config({**CANONICAL, "politica_resto": "greedy"})
    with pytest.raises(ValueError):
        parse_cantidad_por_monto_config({**CANONICAL, "ajuste_manual": {"8000": 28}})


def test_parse_slim_json_keeps_only_precio_base_and_modo() -> None:
    cfg = parse_cantidad_por_monto_config({"precio_base": 300, "modo": "ceil"})
    assert cfg == {"precio_base": 300, "modo": "ceil"}


def test_per_line_4_plus_3_and_4_plus_4() -> None:
    assert (
        _line_amounts(
            [
                {"id_producto": 1, "cantidad": 4},
                {"id_producto": 2, "cantidad": 3},
            ],
            CANONICAL,
        )
        == 1900
    )
    assert (
        _line_amounts(
            [
                {"id_producto": 1, "cantidad": 4},
                {"id_producto": 2, "cantidad": 4},
            ],
            CANONICAL,
        )
        == 2000
    )


def test_per_line_7_plus_5() -> None:
    """7 y 5 por línea: 2000 + 1500."""
    assert (
        _line_amounts(
            [
                {"id_producto": 1, "cantidad": 7},
                {"id_producto": 2, "cantidad": 5},
            ],
            CANONICAL,
        )
        == 3500
    )


def test_per_line_eight_alone_is_2400() -> None:
    assert _line_amounts([{"id_producto": 1, "cantidad": 8}], CANONICAL) == 2400


def test_compute_cart_line_subtotals_mixed() -> None:
    promo = {
        "id": 1,
        "tipo": TIPO_PROMOCION_CANTIDAD_POR_MONTO,
        "configuracion": json.dumps(CANONICAL),
        "activo": ESTADO_ACTIVO,
    }
    lines = [
        {
            "id_producto": 1,
            "cantidad": 4,
            "precio_aplicado": 300,
            "promocion_id": 1,
        },
        {
            "id_producto": 2,
            "cantidad": 3,
            "precio_aplicado": 300,
            "promocion_id": 1,
        },
        {
            "id_producto": 3,
            "cantidad": 2,
            "precio_aplicado": 1500,
            "promocion_id": None,
        },
    ]
    subs = compute_cart_line_subtotals(lines, promos_by_id={1: promo})
    assert subs[0] == 1000
    assert subs[1] == 900
    assert subs[2] == 3000
    assert sum(subs) == 4900


def test_compute_cart_line_subtotals_7_plus_5() -> None:
    promo = {
        "id": 1,
        "tipo": TIPO_PROMOCION_CANTIDAD_POR_MONTO,
        "configuracion": json.dumps(CANONICAL),
        "activo": ESTADO_ACTIVO,
    }
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
    subs = compute_cart_line_subtotals(lines, promos_by_id={1: promo})
    assert subs == [2000, 1500]


def test_draft_4_plus_3_is_per_line() -> None:
    draft = SaleDraft()
    config_json = json.dumps(CANONICAL)
    product = {
        "id_producto": 1,
        "nombre": "Pan A",
        "precio": 300,
        "promocion_id": 1,
        "promocion_tipo": TIPO_PROMOCION_CANTIDAD_POR_MONTO,
        "promocion_configuracion": config_json,
        "promocion_activo": ESTADO_ACTIVO,
    }
    draft.select_product(product)
    draft.set_quantity(4)
    assert draft.add_to_purchase() is True
    draft.select_product({**product, "id_producto": 2, "nombre": "Pan B"})
    draft.set_quantity(3)
    assert draft.add_to_purchase() is True
    assert draft.total() == 1900
    assert [item.subtotal for item in draft.purchase.items()] == [1000, 900]


def test_draft_4_plus_4_is_2000() -> None:
    draft = SaleDraft()
    config_json = json.dumps(CANONICAL)
    product = {
        "id_producto": 1,
        "nombre": "Pan A",
        "precio": 300,
        "promocion_id": 1,
        "promocion_tipo": TIPO_PROMOCION_CANTIDAD_POR_MONTO,
        "promocion_configuracion": config_json,
        "promocion_activo": ESTADO_ACTIVO,
    }
    draft.select_product(product)
    draft.set_quantity(4)
    draft.add_to_purchase()
    draft.select_product({**product, "id_producto": 2, "nombre": "Pan B"})
    draft.set_quantity(4)
    draft.add_to_purchase()
    assert draft.total() == 2000


def test_quantity_preview_promo() -> None:
    draft = SaleDraft()
    draft.select_product(
        {
            "id_producto": 1,
            "nombre": "Pan",
            "precio": 300,
            "promocion_id": 1,
            "promocion_tipo": TIPO_PROMOCION_CANTIDAD_POR_MONTO,
            "promocion_configuracion": json.dumps(CANONICAL),
            "promocion_activo": ESTADO_ACTIVO,
        }
    )
    draft.set_quantity(7)
    assert draft.current_subtotal() == 2000


def test_register_sale_4_plus_3_is_per_line(tmp_path: Path) -> None:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    connection = connect(path)
    try:
        pan = get_categoria_by_nombre(connection, NOMBRE_CATEGORIA_PAN_PEQUENO)
        assert pan is not None
        id_a = insert_producto(
            connection,
            nombre="Pan A",
            precio=300,
            id_categoria=int(pan["id_categoria"]),
            descripcion=None,
            id_estado=ESTADO_ACTIVO,
        )
        id_b = insert_producto(
            connection,
            nombre="Pan B",
            precio=300,
            id_categoria=int(pan["id_categoria"]),
            descripcion=None,
            id_estado=ESTADO_ACTIVO,
        )
        connection.commit()
    finally:
        connection.close()
    initialize(path)
    connection = connect(path)
    try:
        promos = list_promociones(connection)
        assert len(promos) == 1
        sale = register_sale(
            connection,
            1,
            [
                {"id_producto": id_a, "cantidad": 4, "precio_aplicado": 300},
                {"id_producto": id_b, "cantidad": 3, "precio_aplicado": 300},
            ],
        )
        assert sale["valor_total"] == 1900
    finally:
        connection.close()


def test_api_enrich_promo_fields(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from bakery.api.app import create_app

    db_path = tmp_path / "api.sqlite3"
    initialize(db_path)
    connection = connect(db_path)
    try:
        pan = get_categoria_by_nombre(connection, NOMBRE_CATEGORIA_PAN_PEQUENO)
        assert pan is not None
        insert_producto(
            connection,
            nombre="Pan API",
            precio=300,
            id_categoria=int(pan["id_categoria"]),
            descripcion=None,
            id_estado=ESTADO_ACTIVO,
        )
        connection.commit()
    finally:
        connection.close()
    initialize(db_path)

    with TestClient(create_app(db_path)) as client:
        products = client.get("/productos").json()
        pan_products = [p for p in products if p["nombre"] == "Pan API"]
        assert pan_products[0]["promocion_tipo"] == TIPO_PROMOCION_CANTIDAD_POR_MONTO
        assert pan_products[0]["promocion_activo"] == ESTADO_ACTIVO
        config = json.loads(pan_products[0]["promocion_configuracion"])
        assert config == {"modo": "ceil", "precio_base": 300}
        assert "grupo_cantidad" not in config
