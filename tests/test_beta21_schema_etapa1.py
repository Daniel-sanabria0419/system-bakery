"""Beta 2.1 Etapa 1: schema venta_observaciones + venta_cambios (v6)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.migrations import CURRENT_SCHEMA_VERSION, get_schema_version


def _table_sql(connection: sqlite3.Connection, name: str) -> str:
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
        (name,),
    ).fetchone()
    assert row is not None
    return str(row[0])


def _v5_db_with_sale(tmp_path: Path) -> Path:
    """DB at schema_version=5 with one legacy sale (no lines)."""
    path = tmp_path / "v5.sqlite3"
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
                total INTEGER NOT NULL CHECK (total > 0),
                id_promocion INTEGER REFERENCES promociones(id),
                nombre_promocion TEXT
            );
            CREATE TABLE schema_version (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version INTEGER NOT NULL CHECK (version >= 0)
            );
            INSERT INTO schema_version (id, version) VALUES (1, 5);
            INSERT INTO medios_pago (nombre, id_estado) VALUES ('Efectivo', 1);
            INSERT INTO ventas (
                id_venta, valor_total, fecha_venta, id_medio_pago, caja, tendero
            ) VALUES (
                'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
                15000,
                '2026-10-01T10:00:00',
                1,
                1,
                1
            );
            """
        )
        connection.commit()
    finally:
        connection.close()
    return path


def test_current_schema_version_is_6() -> None:
    assert CURRENT_SCHEMA_VERSION == 6


def test_fresh_db_has_observaciones_and_cambios(tmp_path: Path) -> None:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    connection = connect(path)
    try:
        assert get_schema_version(connection) == 6
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "venta_observaciones" in tables
        assert "venta_cambios" in tables

        cambios_sql = _table_sql(connection, "venta_cambios")
        assert "REFERENCES ventas(id_venta)" in cambios_sql
        assert "'creacion'" in cambios_sql
        assert "'edicion'" in cambios_sql
        assert "'observacion_posterior'" in cambios_sql
        assert "'observacion_correccion'" in cambios_sql
        assert "despues_json TEXT NOT NULL" in cambios_sql

        obs_sql = _table_sql(connection, "venta_observaciones")
        assert "REFERENCES ventas(id_venta)" in obs_sql
        assert "REFERENCES venta_cambios(id_cambio)" in obs_sql
        assert "length(trim(texto)) > 0" in obs_sql
        assert "'durante_venta'" in obs_sql
        assert "'posterior'" in obs_sql
    finally:
        connection.close()


def test_reinitialize_does_not_duplicate_tables(tmp_path: Path) -> None:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    initialize(path)
    connection = connect(path)
    try:
        assert get_schema_version(connection) == CURRENT_SCHEMA_VERSION
        count_cambios = connection.execute(
            "SELECT COUNT(*) FROM venta_cambios"
        ).fetchone()[0]
        count_obs = connection.execute(
            "SELECT COUNT(*) FROM venta_observaciones"
        ).fetchone()[0]
        assert count_cambios == 0
        assert count_obs == 0
    finally:
        connection.close()


def test_migrate_v5_to_v6_preserves_existing_sales(tmp_path: Path) -> None:
    path = _v5_db_with_sale(tmp_path)
    connection = connect(path)
    try:
        assert get_schema_version(connection) == 5
        assert "venta_observaciones" not in {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    finally:
        connection.close()

    initialize(path)
    initialize(path)
    connection = connect(path)
    try:
        assert get_schema_version(connection) == 6
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "venta_observaciones" in tables
        assert "venta_cambios" in tables
        sale = connection.execute(
            """
            SELECT id_venta, valor_total, fecha_venta, id_medio_pago
            FROM ventas
            WHERE id_venta = ?
            """,
            ("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",),
        ).fetchone()
        assert sale is not None
        assert sale["valor_total"] == 15000
        assert sale["fecha_venta"] == "2026-10-01T10:00:00"
        assert sale["id_medio_pago"] == 1
        line_count = connection.execute(
            "SELECT COUNT(*) FROM venta_lineas WHERE id_venta = ?",
            ("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",),
        ).fetchone()[0]
        assert line_count == 0
    finally:
        connection.close()


def test_checks_reject_empty_texto_and_invalid_origen(tmp_path: Path) -> None:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    connection = connect(path)
    try:
        connection.execute(
            """
            INSERT INTO ventas (
                id_venta, valor_total, fecha_venta, id_medio_pago, caja, tendero
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                1000,
                "2026-10-30T12:00:00",
                1,
                1,
                1,
            ),
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO venta_observaciones (
                    id_venta, texto, origen, fecha_creacion
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                    "   ",
                    "durante_venta",
                    "2026-10-30T12:00:01",
                ),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO venta_observaciones (
                    id_venta, texto, origen, fecha_creacion
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                    "ok",
                    "otro",
                    "2026-10-30T12:00:01",
                ),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO venta_cambios (
                    id_venta, fecha_cambio, tipo, antes_json, despues_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                    "2026-10-30T12:00:01",
                    "borrar",
                    None,
                    "{}",
                ),
            )
        connection.execute(
            """
            INSERT INTO venta_cambios (
                id_venta, fecha_cambio, tipo, antes_json, despues_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                "2026-10-30T12:00:01",
                "creacion",
                None,
                '{"valor_total":1000}',
            ),
        )
        id_cambio = connection.execute(
            "SELECT id_cambio FROM venta_cambios"
        ).fetchone()[0]
        connection.execute(
            """
            INSERT INTO venta_observaciones (
                id_venta, texto, origen, fecha_creacion, id_cambio
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                "cliente habitual",
                "durante_venta",
                "2026-10-30T12:00:01",
                id_cambio,
            ),
        )
        connection.commit()
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM venta_observaciones"
            ).fetchone()[0]
            == 1
        )
        assert (
            connection.execute("SELECT COUNT(*) FROM venta_cambios").fetchone()[0]
            == 1
        )
    finally:
        connection.close()


def test_fk_rejects_unknown_venta(tmp_path: Path) -> None:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    connection = connect(path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO venta_cambios (
                    id_venta, fecha_cambio, tipo, despues_json
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    "does-not-exist",
                    "2026-10-30T12:00:00",
                    "creacion",
                    "{}",
                ),
            )
    finally:
        connection.close()
