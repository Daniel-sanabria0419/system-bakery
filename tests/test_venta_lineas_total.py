"""Schema v5: venta_lineas.total es el monto cobrado; subtotal es lista."""

from __future__ import annotations

import sqlite3
from pathlib import Path
import uuid

from bakery.app.products import create_product
from bakery.app.sales import register_sale
from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.migrations import CURRENT_SCHEMA_VERSION, get_schema_version
from bakery.persistence.repositories import get_categoria_by_nombre, list_venta_lineas
from bakery.persistence.schema import (
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    NOMBRE_PROMOCION_PAN_PEQUENO,
)


def _column_sql(connection: sqlite3.Connection) -> str:
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'venta_lineas'"
    ).fetchone()
    assert row is not None
    return str(row[0])


def test_new_db_total_column_is_required(tmp_path: Path) -> None:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    connection = connect(path)
    try:
        assert CURRENT_SCHEMA_VERSION == 5
        assert get_schema_version(connection) == 5
        info = {
            row[1]: row
            for row in connection.execute("PRAGMA table_info(venta_lineas)").fetchall()
        }
        assert info["total"][3] == 1  # NOT NULL
        assert info["total"][4] is None  # sin default
        assert "total INTEGER NOT NULL CHECK (total > 0)" in _column_sql(connection)
    finally:
        connection.close()


def test_migration_copies_old_subtotal_without_recomputing(tmp_path: Path) -> None:
    """7 panes cobrados a 2000: el subtotal viejo se queda; total lo copia."""
    path = tmp_path / "v4.sqlite3"
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE medios_pago (
                id_medio_pago INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                id_estado INTEGER NOT NULL
            );
            CREATE TABLE ventas (
                id_venta TEXT PRIMARY KEY,
                valor_total INTEGER NOT NULL CHECK (valor_total > 0),
                fecha_venta TEXT NOT NULL,
                id_medio_pago INTEGER NOT NULL REFERENCES medios_pago(id_medio_pago),
                caja INTEGER NOT NULL DEFAULT 1,
                tendero INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE categorias (
                id_categoria INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL
            );
            CREATE TABLE promociones (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                tipo TEXT NOT NULL,
                configuracion TEXT NOT NULL,
                activo INTEGER NOT NULL
            );
            CREATE TABLE productos (
                id_producto INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                precio INTEGER NOT NULL CHECK (precio > 0),
                id_categoria INTEGER NOT NULL REFERENCES categorias(id_categoria),
                descripcion TEXT,
                id_estado INTEGER NOT NULL,
                ruta_imagen TEXT,
                promocion_id INTEGER REFERENCES promociones(id)
            );
            CREATE TABLE venta_lineas (
                id_linea INTEGER PRIMARY KEY,
                id_venta TEXT NOT NULL REFERENCES ventas(id_venta),
                id_producto INTEGER NOT NULL REFERENCES productos(id_producto),
                nombre_producto TEXT NOT NULL,
                precio_aplicado INTEGER NOT NULL CHECK (precio_aplicado > 0),
                cantidad INTEGER NOT NULL CHECK (cantidad > 0),
                subtotal INTEGER NOT NULL CHECK (subtotal > 0),
                id_promocion INTEGER REFERENCES promociones(id),
                nombre_promocion TEXT
            );
            CREATE TABLE schema_version (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version INTEGER NOT NULL CHECK (version >= 0)
            );
            INSERT INTO schema_version (id, version) VALUES (1, 4);
            INSERT INTO medios_pago (nombre, id_estado) VALUES ('Efectivo', 1);
            INSERT INTO categorias (nombre) VALUES ('Pan pequeño');
            INSERT INTO promociones (nombre, tipo, configuracion, activo)
            VALUES (
                'Pan pequeño 7 por 2000',
                'cantidad_por_monto',
                '{"modo":"ceil","precio_base":300}',
                1
            );
            INSERT INTO productos (
                nombre, precio, id_categoria, descripcion, id_estado,
                ruta_imagen, promocion_id
            ) VALUES ('Pan rollo', 300, 1, NULL, 1, NULL, 1);
            INSERT INTO ventas (
                id_venta, valor_total, fecha_venta, id_medio_pago, caja, tendero
            ) VALUES (
                'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
                2000,
                '2026-10-27T10:00:00',
                1, 1, 1
            );
            INSERT INTO venta_lineas (
                id_venta, id_producto, nombre_producto,
                precio_aplicado, cantidad, subtotal,
                id_promocion, nombre_promocion
            ) VALUES (
                'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
                1, 'Pan rollo', 300, 7, 2000, 1, 'Pan pequeño 7 por 2000'
            );
            """
        )
        connection.commit()
    finally:
        connection.close()

    initialize(path)
    initialize(path)
    connection = connect(path)
    try:
        assert get_schema_version(connection) == 5
        row = connection.execute(
            """
            SELECT cantidad, precio_aplicado, subtotal, total
            FROM venta_lineas
            WHERE id_venta = ?
            """,
            ("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",),
        ).fetchone()
        assert row["cantidad"] == 7
        assert row["precio_aplicado"] == 300
        assert row["subtotal"] == 2000
        assert row["total"] == 2000
        assert row["subtotal"] != row["cantidad"] * row["precio_aplicado"]
    finally:
        connection.close()


def test_new_sale_splits_list_subtotal_and_charged_total(tmp_path: Path) -> None:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    connection = connect(path)
    try:
        pan = get_categoria_by_nombre(connection, NOMBRE_CATEGORIA_PAN_PEQUENO)
        assert pan is not None
        product = create_product(
            connection,
            nombre="Pan rollo",
            precio=300,
            id_categoria=int(pan["id_categoria"]),
        )
        product_id = product["id_producto"]

        def sell(cantidad: int) -> dict:
            sale = register_sale(
                connection,
                1,
                [
                    {
                        "id_producto": product_id,
                        "cantidad": cantidad,
                        "precio_aplicado": 300,
                    }
                ],
            id_venta=str(uuid.uuid4()),
        )
            line = list_venta_lineas(connection, sale["id_venta"])[0]
            return {
                "valor_total": sale["valor_total"],
                "subtotal": line["subtotal"],
                "total": line["total"],
                "id_promocion": line["id_promocion"],
                "nombre_promocion": line["nombre_promocion"],
            }

        promo_id = product["promocion_id"]
        eight = sell(8)
        assert eight == {
            "valor_total": 2400,
            "subtotal": 2400,
            "total": 2400,
            "id_promocion": None,
            "nombre_promocion": None,
        }

        seventeen = sell(17)
        assert seventeen == {
            "valor_total": 5000,
            "subtotal": 5100,
            "total": 5000,
            "id_promocion": promo_id,
            "nombre_promocion": NOMBRE_PROMOCION_PAN_PEQUENO,
        }

        five = sell(5)
        assert five == {
            "valor_total": 1500,
            "subtotal": 1500,
            "total": 1500,
            "id_promocion": None,
            "nombre_promocion": None,
        }

        mixed = register_sale(
            connection,
            1,
            [
                {
                    "id_producto": product_id,
                    "cantidad": 17,
                    "precio_aplicado": 300,
                },
                {
                    "id_producto": product_id,
                    "cantidad": 5,
                    "precio_aplicado": 300,
                },
            ],
            id_venta=str(uuid.uuid4()),
        )
        assert mixed["valor_total"] == 6500
        lines = list_venta_lineas(connection, mixed["id_venta"])
        assert [
            (line["subtotal"], line["total"], line["id_promocion"]) for line in lines
        ] == [
            (5100, 5000, promo_id),
            (1500, 1500, None),
        ]
        assert lines[0]["nombre_promocion"] == NOMBRE_PROMOCION_PAN_PEQUENO
        assert lines[1]["nombre_promocion"] is None
    finally:
        connection.close()
