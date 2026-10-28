"""Beta 2.0.4 Etapa 3: motor promotions + dual-path (flag off = legado)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bakery.app import promotions as promotions_mod
from bakery.app.pan_pequeno_pricing import (
    quantity_from_value as pan_quantity_from_value,
    subtotal_for_quantity as pan_subtotal_for_quantity,
)
from bakery.app.promotions import (
    allocate_group_subtotals,
    amount_for_cart_group,
    amount_for_quantity,
    compute_cart_line_subtotals,
    parse_cantidad_por_monto_config,
    quantity_from_value,
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


@pytest.fixture(autouse=True)
def _flag_off_by_default(monkeypatch):
    monkeypatch.delenv("BAKERY_USE_PROMOCIONES_TABLE", raising=False)
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", False)


CANONICAL = PROMOCION_PAN_PEQUENO_CONFIG


@pytest.mark.parametrize(
    ("cantidad", "subtotal"),
    [
        (6, 1800),
        (7, 2000),
        (8, 2400),
        (14, 4000),
    ],
)
def test_amount_for_quantity_parity_with_pan_pequeno(
    cantidad: int, subtotal: int
) -> None:
    assert amount_for_quantity(cantidad, CANONICAL) == subtotal
    assert amount_for_quantity(cantidad, CANONICAL) == pan_subtotal_for_quantity(
        cantidad
    )


def test_quantity_from_value_1900_ceil_parity() -> None:
    assert quantity_from_value(1900, CANONICAL) == (7, 2000)
    assert quantity_from_value(1900, CANONICAL) == pan_quantity_from_value(1900)


def test_parse_config_rejects_invalid() -> None:
    with pytest.raises(ValueError):
        parse_cantidad_por_monto_config("{")
    with pytest.raises(ValueError):
        parse_cantidad_por_monto_config({**CANONICAL, "modo": "floor"})
    with pytest.raises(ValueError):
        parse_cantidad_por_monto_config({**CANONICAL, "politica_resto": "ceil"})


def test_amount_for_cart_group_4_plus_3_and_4_plus_4() -> None:
    assert (
        amount_for_cart_group(
            [
                {"id_producto": 1, "cantidad": 4},
                {"id_producto": 2, "cantidad": 3},
            ],
            CANONICAL,
        )
        == 2000
    )
    assert (
        amount_for_cart_group(
            [
                {"id_producto": 1, "cantidad": 4},
                {"id_producto": 2, "cantidad": 4},
            ],
            CANONICAL,
        )
        == 2400
    )


def test_amount_for_cart_group_7_plus_5_hybrid() -> None:
    """SKU exacto 7 toma promo; el 5 queda a precio base → 3500."""
    assert (
        amount_for_cart_group(
            [
                {"id_producto": 1, "cantidad": 7},
                {"id_producto": 2, "cantidad": 5},
            ],
            CANONICAL,
        )
        == 3500
    )


def test_amount_for_cart_group_eight_alone_is_2400() -> None:
    assert amount_for_cart_group(
        [{"id_producto": 1, "cantidad": 8}], CANONICAL
    ) == 2400


def test_allocate_group_subtotals_sum_equals_monto() -> None:
    parts = allocate_group_subtotals(
        [{"cantidad": 4}, {"cantidad": 3}], 2000
    )
    assert sum(parts) == 2000
    assert parts == [1142, 858]  # 4/7 y residuo en última


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
    assert sum(subs[:2]) == 2000
    assert subs[2] == 3000
    assert sum(subs) == 5000


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
    assert sum(subs) == 3500


def test_flag_off_draft_uses_plain_precio_times_qty() -> None:
    draft = SaleDraft()
    product = {
        "id_producto": 1,
        "nombre": "Pan A",
        "precio": 300,
        "nombre_categoria": NOMBRE_CATEGORIA_PAN_PEQUENO,
        "promocion_id": 1,
        "promocion_tipo": TIPO_PROMOCION_CANTIDAD_POR_MONTO,
        "promocion_configuracion": json.dumps(CANONICAL),
        "promocion_activo": ESTADO_ACTIVO,
    }
    draft.select_product(product)
    draft.set_quantity(4)
    assert draft.add_to_purchase() is True
    draft.select_product({**product, "id_producto": 2, "nombre": "Pan B"})
    draft.set_quantity(3)
    assert draft.add_to_purchase() is True
    # Flag off tras cutover: sin montos por categoría → precio × cantidad
    assert draft.total() == 2100


def test_flag_on_draft_groups_cart_4_plus_3(monkeypatch) -> None:
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", True)
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
    assert draft.total() == 2000
    assert sum(item.subtotal for item in draft.purchase.items()) == 2000


def test_flag_on_draft_4_plus_4_is_2400(monkeypatch) -> None:
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", True)
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
    assert draft.total() == 2400


def test_flag_on_apply_value_ceil(monkeypatch) -> None:
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", True)
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
    assert draft.apply_value(1900) is True
    assert draft.quantity() == 7
    assert draft.current_subtotal() == 2000


def test_register_sale_flag_off_unchanged(tmp_path: Path) -> None:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    connection = connect(path)
    try:
        pan = get_categoria_by_nombre(connection, NOMBRE_CATEGORIA_PAN_PEQUENO)
        assert pan is not None
        id_producto = insert_producto(
            connection,
            nombre="Pan reg",
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
        sale = register_sale(
            connection,
            1,
            [
                {"id_producto": id_producto, "cantidad": 4, "precio_aplicado": 300},
                {"id_producto": id_producto, "cantidad": 3, "precio_aplicado": 300},
            ],
        )
        # Legado: 1200 + 900
        assert sale["valor_total"] == 2100
    finally:
        connection.close()


def test_register_sale_flag_on_groups_cart(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", True)
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
        assert sale["valor_total"] == 2000
    finally:
        connection.close()


def test_api_enrich_promo_fields_only_when_flag_on(
    tmp_path: Path, monkeypatch
) -> None:
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
        assert len(pan_products) == 1
        assert pan_products[0]["promocion_id"] is not None
        assert pan_products[0].get("promocion_tipo") is None

    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", True)
    with TestClient(create_app(db_path)) as client:
        products = client.get("/productos").json()
        pan_products = [p for p in products if p["nombre"] == "Pan API"]
        assert pan_products[0]["promocion_tipo"] == TIPO_PROMOCION_CANTIDAD_POR_MONTO
        assert pan_products[0]["promocion_activo"] == ESTADO_ACTIVO
        config = json.loads(pan_products[0]["promocion_configuracion"])
        assert config["grupo_cantidad"] == 7
