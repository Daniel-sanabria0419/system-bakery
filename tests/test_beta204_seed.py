"""Beta 2.0.4 Etapa 2: seed promociones + backfill productos Pan pequeño."""

from __future__ import annotations

import json
from pathlib import Path

from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.repositories import (
    get_categoria_by_nombre,
    get_producto,
    get_promocion,
    insert_producto,
    list_promociones,
)
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    NOMBRE_PROMOCION_PAN_PEQUENO,
    PROMOCION_PAN_PEQUENO_CONFIG,
    TIPO_PROMOCION_CANTIDAD_POR_MONTO,
    ensure_promocion_pan_pequeno,
    promocion_pan_pequeno_config_json,
)

def _db(tmp_path: Path) -> Path:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    return path


def test_seed_promocion_pan_pequeno_config(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        promos = list_promociones(connection)
        assert len(promos) == 1
        promo = promos[0]
        assert promo["nombre"] == NOMBRE_PROMOCION_PAN_PEQUENO
        assert promo["tipo"] == TIPO_PROMOCION_CANTIDAD_POR_MONTO
        assert promo["activo"] == ESTADO_ACTIVO
        config = json.loads(promo["configuracion"])
        assert config == PROMOCION_PAN_PEQUENO_CONFIG
        assert config["precio_base"] == 300
        assert config["grupo_cantidad"] == 7
        assert config["grupo_monto"] == 2000
        assert config["modo"] == "ceil"
        assert "politica_resto" not in config
        assert "ajuste_manual" not in config
        assert promo["configuracion"] == promocion_pan_pequeno_config_json()
    finally:
        connection.close()


def test_seed_promocion_is_idempotent(tmp_path: Path) -> None:
    path = _db(tmp_path)
    initialize(path)
    initialize(path)
    connection = connect(path)
    try:
        assert len(list_promociones(connection)) == 1
        first_id = ensure_promocion_pan_pequeno(connection)
        second_id = ensure_promocion_pan_pequeno(connection)
        connection.commit()
        assert first_id == second_id
        assert len(list_promociones(connection)) == 1
    finally:
        connection.close()


def test_backfill_assigns_promocion_id_to_pan_pequeno_products(
    tmp_path: Path,
) -> None:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    connection = connect(path)
    try:
        pan = get_categoria_by_nombre(connection, NOMBRE_CATEGORIA_PAN_PEQUENO)
        assert pan is not None
        id_pan = int(pan["id_categoria"])
        other = get_categoria_by_nombre(connection, "Panadería")
        assert other is not None
        id_other = int(other["id_categoria"])

        pan_product = insert_producto(
            connection,
            nombre="Pan prueba",
            precio=300,
            id_categoria=id_pan,
            descripcion=None,
            id_estado=ESTADO_ACTIVO,
        )
        other_product = insert_producto(
            connection,
            nombre="Baguette",
            precio=2500,
            id_categoria=id_other,
            descripcion=None,
            id_estado=ESTADO_ACTIVO,
        )
        connection.commit()
    finally:
        connection.close()

    initialize(path)  # backfill

    connection = connect(path)
    try:
        promos = list_promociones(connection)
        assert len(promos) == 1
        promo_id = int(promos[0]["id"])
        linked = get_producto(connection, pan_product)
        assert linked is not None
        assert linked["promocion_id"] == promo_id
        assert linked["precio"] == PROMOCION_PAN_PEQUENO_CONFIG["precio_base"]
        untouched = get_producto(connection, other_product)
        assert untouched is not None
        assert untouched["promocion_id"] is None
        promo = get_promocion(connection, promo_id)
        assert promo is not None
        assert promo["nombre"] == NOMBRE_PROMOCION_PAN_PEQUENO
    finally:
        connection.close()


def test_backfill_on_reinit_exposes_fk_in_api(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from bakery.api.app import create_app

    db_path = tmp_path / "api.sqlite3"
    with TestClient(create_app(db_path)) as client:
        categories = client.get("/categorias").json()
        pan = next(c for c in categories if c["nombre"] == NOMBRE_CATEGORIA_PAN_PEQUENO)
        created = client.post(
            "/productos",
            json={
                "nombre": "Pan API",
                "precio": 300,
                "id_categoria": pan["id_categoria"],
            },
        )
        assert created.status_code == 200
        body = created.json()
        # Cutover: create/update asigna FK de promo canónica al instante.
        assert body["promocion_id"] is not None
        assert body["promocion_tipo"] == TIPO_PROMOCION_CANTIDAD_POR_MONTO

    connection = connect(db_path)
    try:
        promos = list_promociones(connection)
        assert len(promos) == 1
        assert body["promocion_id"] == promos[0]["id"]
    finally:
        connection.close()
