"""Beta 2.0.4 Etapa 1: schema promociones + productos.promocion_id."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.migrations import (
    CURRENT_SCHEMA_VERSION,
    get_schema_version,
)
from bakery.persistence.repositories import (
    get_producto,
    get_promocion,
    insert_producto,
    insert_promocion,
    list_promociones,
    set_producto_promocion_id,
)
from bakery.persistence.schema import ESTADO_ACTIVO, ESTADO_INACTIVO, SEED_CATEGORIAS


def _db(tmp_path: Path) -> Path:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    return path


def _v1_shaped_db(tmp_path: Path) -> Path:
    """DB like post–Beta 2.0.1: schema_version=1, sin promociones ni promocion_id."""
    path = tmp_path / "v1.sqlite3"
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """
            CREATE TABLE medios_pago (
                id_medio_pago INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                id_estado INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE ventas (
                id_venta TEXT PRIMARY KEY,
                valor_total INTEGER NOT NULL CHECK (valor_total > 0),
                fecha_venta TEXT NOT NULL,
                id_medio_pago INTEGER NOT NULL REFERENCES medios_pago(id_medio_pago),
                caja INTEGER NOT NULL DEFAULT 1,
                tendero INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE categorias (
                id_categoria INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE productos (
                id_producto INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                precio INTEGER NOT NULL CHECK (precio > 0),
                id_categoria INTEGER NOT NULL REFERENCES categorias(id_categoria),
                descripcion TEXT,
                id_estado INTEGER NOT NULL,
                ruta_imagen TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE venta_lineas (
                id_linea INTEGER PRIMARY KEY,
                id_venta TEXT NOT NULL REFERENCES ventas(id_venta),
                id_producto INTEGER NOT NULL REFERENCES productos(id_producto),
                nombre_producto TEXT NOT NULL,
                precio_aplicado INTEGER NOT NULL CHECK (precio_aplicado > 0),
                cantidad INTEGER NOT NULL CHECK (cantidad > 0),
                subtotal INTEGER NOT NULL CHECK (subtotal > 0)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE schema_version (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version INTEGER NOT NULL CHECK (version >= 0)
            )
            """
        )
        connection.execute(
            "INSERT INTO schema_version (id, version) VALUES (1, 1)"
        )
        connection.execute(
            "INSERT INTO medios_pago (nombre, id_estado) VALUES (?, ?)",
            ("Efectivo", ESTADO_ACTIVO),
        )
        for nombre in SEED_CATEGORIAS:
            connection.execute(
                "INSERT INTO categorias (nombre) VALUES (?)",
                (nombre,),
            )
        connection.execute(
            """
            INSERT INTO productos (
                nombre, precio, id_categoria, descripcion, id_estado, ruta_imagen
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("Torta", 20000, 2, None, ESTADO_ACTIVO, None),
        )
        connection.commit()
    finally:
        connection.close()
    return path


def test_new_db_has_promociones_and_promocion_id(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "promociones" in tables
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(productos)").fetchall()
        }
        assert "promocion_id" in columns
        assert get_schema_version(connection) == CURRENT_SCHEMA_VERSION
        assert CURRENT_SCHEMA_VERSION == 2
        assert list_promociones(connection) == []
        product_id = insert_producto(
            connection,
            nombre="Pan rollo",
            precio=300,
            id_categoria=1,
            descripcion=None,
            id_estado=ESTADO_ACTIVO,
        )
        connection.commit()
        product = get_producto(connection, product_id)
        assert product is not None
        assert product["promocion_id"] is None
    finally:
        connection.close()


def test_migrate_v1_to_v2_round_trip_idempotent(tmp_path: Path) -> None:
    path = _v1_shaped_db(tmp_path)
    connection = connect(path)
    try:
        assert get_schema_version(connection) == 1
        tables_before = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "promociones" not in tables_before
        columns_before = {
            row[1]
            for row in connection.execute("PRAGMA table_info(productos)").fetchall()
        }
        assert "promocion_id" not in columns_before
    finally:
        connection.close()

    initialize(path)
    initialize(path)  # idempotente

    connection = connect(path)
    try:
        assert get_schema_version(connection) == 2
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "promociones" in tables
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(productos)").fetchall()
        }
        assert "promocion_id" in columns
        product = get_producto(connection, 1)
        assert product is not None
        assert product["nombre"] == "Torta"
        assert product["promocion_id"] is None
        assert list_promociones(connection) == []
    finally:
        connection.close()


def test_promocion_repo_and_nullable_fk(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        config = json.dumps(
            {
                "precio_base": 300,
                "grupo_cantidad": 7,
                "grupo_monto": 2000,
                "modo": "ceil",
                "politica_resto": "todo_o_nada",
            },
            separators=(",", ":"),
        )
        promo_id = insert_promocion(
            connection,
            nombre="Pan pequeño 7 por 2000",
            tipo="cantidad_por_monto",
            configuracion=config,
            activo=ESTADO_INACTIVO,
        )
        connection.commit()
        promo = get_promocion(connection, promo_id)
        assert promo is not None
        assert promo["nombre"] == "Pan pequeño 7 por 2000"
        assert promo["tipo"] == "cantidad_por_monto"
        assert promo["activo"] == ESTADO_INACTIVO
        assert json.loads(promo["configuracion"])["grupo_cantidad"] == 7

        product_id = insert_producto(
            connection,
            nombre="Pan prueba",
            precio=300,
            id_categoria=1,
            descripcion=None,
            id_estado=ESTADO_ACTIVO,
        )
        set_producto_promocion_id(connection, product_id, promo_id)
        connection.commit()
        linked = get_producto(connection, product_id)
        assert linked is not None
        assert linked["promocion_id"] == promo_id

        set_producto_promocion_id(connection, product_id, None)
        connection.commit()
        cleared = get_producto(connection, product_id)
        assert cleared is not None
        assert cleared["promocion_id"] is None
    finally:
        connection.close()


def test_api_product_exposes_promocion_id_null(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from bakery.api.app import create_app

    db_path = tmp_path / "api.sqlite3"
    with TestClient(create_app(db_path)) as client:
        created = client.post(
            "/productos",
            json={
                "nombre": "Galleta",
                "precio": 1500,
                "id_categoria": 1,
            },
        )
        assert created.status_code == 200
        body = created.json()
        assert "promocion_id" in body
        assert body["promocion_id"] is None

        listed = client.get("/productos")
        assert listed.status_code == 200
        assert listed.json()[0]["promocion_id"] is None
