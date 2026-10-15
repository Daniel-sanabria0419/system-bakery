import sqlite3
from pathlib import Path

import pytest

from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.repositories import insert_sale, list_active_payment_methods
from bakery.persistence.schema import SEED_MEDIOS_PAGO


def _db(tmp_path: Path) -> Path:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
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
