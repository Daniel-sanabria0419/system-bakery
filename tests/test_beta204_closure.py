"""Beta 2.0.4 Etapas 6–7: snapshot venta_lineas + huecos de regresión."""

from __future__ import annotations

from pathlib import Path
import uuid

from bakery.app.products import create_product
from bakery.app.purchase import SaleDraft
from bakery.app.sales import register_sale
from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.migrations import CURRENT_SCHEMA_VERSION, get_schema_version
from bakery.persistence.repositories import (
    get_categoria_by_nombre,
    get_promocion,
    list_venta_lineas,
)
from bakery.persistence.schema import (
    ESTADO_INACTIVO,
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    NOMBRE_PROMOCION_PAN_PEQUENO,
)
from tests.test_beta201_sales_pricing import _pan_pequeno_product


def test_schema_version_is_3_with_venta_lineas_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    connection = connect(path)
    try:
        assert CURRENT_SCHEMA_VERSION >= 5
        assert get_schema_version(connection) == CURRENT_SCHEMA_VERSION
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(venta_lineas)"
            ).fetchall()
        }
        assert "id_promocion" in columns
        assert "nombre_promocion" in columns
    finally:
        connection.close()


def test_register_sale_persists_promo_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    connection = connect(path)
    try:
        pan = get_categoria_by_nombre(connection, NOMBRE_CATEGORIA_PAN_PEQUENO)
        assert pan is not None
        product = create_product(
            connection,
            nombre="Pan snap",
            precio=300,
            id_categoria=int(pan["id_categoria"]),
        )
        sale = register_sale(
            connection,
            1,
            [
                {
                    "id_producto": product["id_producto"],
                    "cantidad": 7,
                    "precio_aplicado": 300,
                }
            ],
            id_venta=str(uuid.uuid4()),
        )
        lines = list_venta_lineas(connection, sale["id_venta"])
        assert len(lines) == 1
        assert lines[0]["subtotal"] == 2100
        assert lines[0]["total"] == 2000
        assert lines[0]["id_promocion"] == product["promocion_id"]
        assert lines[0]["nombre_promocion"] == NOMBRE_PROMOCION_PAN_PEQUENO
    finally:
        connection.close()


def test_snapshot_stable_after_rename_and_deactivate(tmp_path: Path) -> None:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    connection = connect(path)
    try:
        pan = get_categoria_by_nombre(connection, NOMBRE_CATEGORIA_PAN_PEQUENO)
        assert pan is not None
        product = create_product(
            connection,
            nombre="Pan hist",
            precio=300,
            id_categoria=int(pan["id_categoria"]),
        )
        sale = register_sale(
            connection,
            1,
            [
                {
                    "id_producto": product["id_producto"],
                    "cantidad": 7,
                    "precio_aplicado": 300,
                }
            ],
            id_venta=str(uuid.uuid4()),
        )
        promo_id = product["promocion_id"]
        assert promo_id is not None
        connection.execute(
            "UPDATE promociones SET nombre = ?, activo = ? WHERE id = ?",
            ("Promo renombrada", ESTADO_INACTIVO, promo_id),
        )
        connection.commit()
        lines = list_venta_lineas(connection, sale["id_venta"])
        assert lines[0]["id_promocion"] == promo_id
        assert lines[0]["nombre_promocion"] == NOMBRE_PROMOCION_PAN_PEQUENO
        assert lines[0]["subtotal"] == 2100
        assert lines[0]["total"] == 2000
        promo = get_promocion(connection, int(promo_id))
        assert promo is not None
        assert promo["nombre"] == "Promo renombrada"
        assert promo["activo"] == ESTADO_INACTIVO
    finally:
        connection.close()


def test_cart_seven_alone_and_mix_with_normal() -> None:
    draft = SaleDraft()
    draft.select_product(_pan_pequeno_product(id_producto=1, nombre="Pan A"))
    draft.set_quantity(7)
    assert draft.add_to_purchase() is True
    assert draft.total() == 2000

    draft.select_product(
        {
            "id_producto": 99,
            "nombre": "Torta",
            "precio": 1500,
            "nombre_categoria": "Pastelería",
        }
    )
    draft.set_quantity(2)
    assert draft.add_to_purchase() is True
    assert draft.total() == 2000 + 3000
    items = draft.purchase.items()
    assert items[0].subtotal == 2000
    assert items[1].subtotal == 3000
    assert items[0].promocion_id == 1
    assert items[1].promocion_id is None


def test_migrate_v2_to_v3_adds_snapshot_columns(tmp_path: Path) -> None:
    import sqlite3

    path = tmp_path / "v2.sqlite3"
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
                subtotal INTEGER NOT NULL CHECK (subtotal > 0)
            );
            CREATE TABLE schema_version (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version INTEGER NOT NULL CHECK (version >= 0)
            );
            INSERT INTO schema_version (id, version) VALUES (1, 2);
            INSERT INTO medios_pago (nombre, id_estado) VALUES ('Efectivo', 1);
            """
        )
        connection.commit()
    finally:
        connection.close()

    initialize(path)
    initialize(path)
    connection = connect(path)
    try:
        assert get_schema_version(connection) == CURRENT_SCHEMA_VERSION
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(venta_lineas)"
            ).fetchall()
        }
        assert "id_promocion" in columns
        assert "nombre_promocion" in columns
        row = connection.execute(
            "SELECT configuracion FROM promociones WHERE nombre = ?",
            ("Pan pequeño 7 por 2000",),
        ).fetchone()
        assert row is not None
        assert row[0] == '{"modo":"ceil","precio_base":300}'
    finally:
        connection.close()
