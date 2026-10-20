import sqlite3
from pathlib import Path

import pytest

from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.repositories import insert_sale, list_active_payment_methods
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    SEED_CATEGORIAS,
    SEED_MEDIOS_PAGO,
)


def _db(tmp_path: Path) -> Path:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    return path


def _legacy_medios_ventas_db(tmp_path: Path) -> Path:
    """DB shaped like Beta 1.x: only medios_pago and ventas."""
    path = tmp_path / "legacy.sqlite3"
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
            "INSERT INTO medios_pago (nombre, id_estado) VALUES (?, ?)",
            ("Efectivo", ESTADO_ACTIVO),
        )
        connection.execute(
            """
            INSERT INTO ventas (
                id_venta, valor_total, fecha_venta, id_medio_pago, caja, tendero
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                15000,
                "2026-10-01T10:00:00",
                1,
                1,
                1,
            ),
        )
        connection.commit()
    finally:
        connection.close()
    return path


def test_seed_creates_five_active_payment_methods(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        methods = list_active_payment_methods(connection)
        names = [method["nombre"] for method in methods]
        assert names == list(SEED_MEDIOS_PAGO)
        assert all(method["id_estado"] == 1 for method in methods)
    finally:
        connection.close()


def test_seed_is_idempotent(tmp_path: Path) -> None:
    path = _db(tmp_path)
    initialize(path)
    connection = connect(path)
    try:
        count = connection.execute("SELECT COUNT(*) FROM medios_pago").fetchone()[0]
        assert count == len(SEED_MEDIOS_PAGO)
    finally:
        connection.close()


def test_new_db_creates_catalog_and_line_tables(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {"categorias", "productos", "venta_lineas", "medios_pago", "ventas"} <= tables
        names = [
            row[0]
            for row in connection.execute(
                "SELECT nombre FROM categorias ORDER BY id_categoria"
            ).fetchall()
        ]
        assert names == list(SEED_CATEGORIAS)
    finally:
        connection.close()


def test_seed_categorias_is_idempotent(tmp_path: Path) -> None:
    path = _db(tmp_path)
    initialize(path)
    connection = connect(path)
    try:
        count = connection.execute("SELECT COUNT(*) FROM categorias").fetchone()[0]
        assert count == len(SEED_CATEGORIAS)
    finally:
        connection.close()


def test_migrate_legacy_db_keeps_old_ventas(tmp_path: Path) -> None:
    path = _legacy_medios_ventas_db(tmp_path)
    initialize(path)
    connection = connect(path)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {"categorias", "productos", "venta_lineas"} <= tables
        sale = connection.execute(
            "SELECT id_venta, valor_total FROM ventas"
        ).fetchone()
        assert sale["id_venta"] == "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        assert sale["valor_total"] == 15000
        line_count = connection.execute("SELECT COUNT(*) FROM venta_lineas").fetchone()[0]
        assert line_count == 0
        category_count = connection.execute(
            "SELECT COUNT(*) FROM categorias"
        ).fetchone()[0]
        assert category_count == len(SEED_CATEGORIAS)
    finally:
        connection.close()


def test_producto_requires_positive_price_and_category(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO productos (nombre, precio, id_categoria, id_estado)
                VALUES (?, ?, ?, ?)
                """,
                ("Pan", 0, 1, ESTADO_ACTIVO),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO productos (nombre, precio, id_categoria, id_estado)
                VALUES (?, ?, ?, ?)
                """,
                ("Pan", 1000, 999, ESTADO_ACTIVO),
            )
    finally:
        connection.close()


def test_venta_linea_checks_and_foreign_keys(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        connection.execute(
            """
            INSERT INTO productos (nombre, precio, id_categoria, descripcion, id_estado)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Pan de chocolate", 5000, 1, "opcional", ESTADO_ACTIVO),
        )
        insert_sale(
            connection,
            id_venta="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            valor_total=10000,
            fecha_venta="2026-10-20T11:00:00",
            id_medio_pago=1,
        )
        connection.execute(
            """
            INSERT INTO venta_lineas (
                id_venta, id_producto, nombre_producto,
                precio_aplicado, cantidad, subtotal
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                1,
                "Pan de chocolate",
                5000,
                2,
                10000,
            ),
        )
        connection.commit()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO venta_lineas (
                    id_venta, id_producto, nombre_producto,
                    precio_aplicado, cantidad, subtotal
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                    1,
                    "Pan de chocolate",
                    5000,
                    0,
                    5000,
                ),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO venta_lineas (
                    id_venta, id_producto, nombre_producto,
                    precio_aplicado, cantidad, subtotal
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "missing-sale",
                    1,
                    "Pan de chocolate",
                    5000,
                    1,
                    5000,
                ),
            )
    finally:
        connection.close()


def test_list_active_payment_methods_excludes_inactive(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        connection.execute(
            "INSERT INTO medios_pago (nombre, id_estado) VALUES (?, ?)",
            ("Inactivo", 0),
        )
        connection.commit()
        names = [method["nombre"] for method in list_active_payment_methods(connection)]
        assert "Inactivo" not in names
        assert "Efectivo" in names
    finally:
        connection.close()


def test_insert_sale_with_uuid(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        insert_sale(
            connection,
            id_venta="11111111-1111-4111-8111-111111111111",
            valor_total=25000,
            fecha_venta="2026-09-30T11:00:00",
            id_medio_pago=1,
        )
        connection.commit()
        row = connection.execute("SELECT * FROM ventas").fetchone()
        assert row["id_venta"] == "11111111-1111-4111-8111-111111111111"
        assert row["valor_total"] == 25000
        assert row["caja"] == 1
        assert row["tendero"] == 1
        assert row["id_medio_pago"] == 1
    finally:
        connection.close()


def test_rejects_value_zero(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        with pytest.raises(sqlite3.IntegrityError):
            insert_sale(
                connection,
                id_venta="22222222-2222-4222-8222-222222222222",
                valor_total=0,
                fecha_venta="2026-09-30T11:00:00",
                id_medio_pago=1,
            )
    finally:
        connection.close()


def test_rejects_negative_value(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        with pytest.raises(sqlite3.IntegrityError):
            insert_sale(
                connection,
                id_venta="33333333-3333-4333-8333-333333333333",
                valor_total=-1,
                fecha_venta="2026-09-30T11:00:00",
                id_medio_pago=1,
            )
    finally:
        connection.close()


def test_rejects_missing_value(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO ventas (id_venta, fecha_venta, id_medio_pago)
                VALUES (?, ?, ?)
                """,
                ("44444444-4444-4444-8444-444444444444", "2026-09-30T11:00:00", 1),
            )
    finally:
        connection.close()


def test_rejects_unknown_payment_method(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        with pytest.raises(sqlite3.IntegrityError):
            insert_sale(
                connection,
                id_venta="55555555-5555-4555-8555-555555555555",
                valor_total=1000,
                fecha_venta="2026-09-30T11:00:00",
                id_medio_pago=999,
            )
    finally:
        connection.close()
