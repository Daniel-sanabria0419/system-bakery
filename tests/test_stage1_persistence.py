import sqlite3
from pathlib import Path

import pytest

from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.migrations import (
    CURRENT_SCHEMA_VERSION,
    get_schema_version,
)
from bakery.persistence.repositories import (
    get_categoria_by_nombre,
    get_producto,
    insert_producto,
    insert_sale,
    list_active_payment_methods,
    list_categorias,
    set_producto_ruta_imagen,
)
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    SEED_CATEGORIAS,
    SEED_MEDIOS_PAGO,
)


def _expected_category_names() -> list:
    return list(SEED_CATEGORIAS) + [NOMBRE_CATEGORIA_PAN_PEQUENO]


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
        assert {
            "categorias",
            "productos",
            "venta_lineas",
            "medios_pago",
            "ventas",
            "schema_version",
        } <= tables
        names = [
            row[0]
            for row in connection.execute(
                "SELECT nombre FROM categorias ORDER BY id_categoria"
            ).fetchall()
        ]
        assert names == _expected_category_names()
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(productos)").fetchall()
        }
        assert "ruta_imagen" in columns
        assert get_schema_version(connection) == CURRENT_SCHEMA_VERSION
    finally:
        connection.close()


def test_schema_version_migration_from_beta2_without_meta(tmp_path: Path) -> None:
    path = _beta2_five_categories_db(tmp_path)
    connection = connect(path)
    try:
        assert get_schema_version(connection) == 0
        columns_before = {
            row[1]
            for row in connection.execute("PRAGMA table_info(productos)").fetchall()
        }
        assert "ruta_imagen" not in columns_before
    finally:
        connection.close()

    initialize(path)
    initialize(path)  # idempotente

    connection = connect(path)
    try:
        assert get_schema_version(connection) == CURRENT_SCHEMA_VERSION
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(productos)").fetchall()
        }
        assert "ruta_imagen" in columns
    finally:
        connection.close()


def test_seed_categorias_is_idempotent(tmp_path: Path) -> None:
    path = _db(tmp_path)
    initialize(path)
    connection = connect(path)
    try:
        count = connection.execute("SELECT COUNT(*) FROM categorias").fetchone()[0]
        assert count == len(_expected_category_names())
        names = [c["nombre"] for c in list_categorias(connection)]
        assert names.count(NOMBRE_CATEGORIA_PAN_PEQUENO) == 1
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
        assert category_count == len(_expected_category_names())
        assert get_categoria_by_nombre(connection, NOMBRE_CATEGORIA_PAN_PEQUENO) is not None
    finally:
        connection.close()


def _beta2_five_categories_db(tmp_path: Path) -> Path:
    """DB like Beta 2.0 after seed: five categories, productos without ruta_imagen."""
    path = tmp_path / "beta2.sqlite3"
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
                id_estado INTEGER NOT NULL
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
            INSERT INTO productos (nombre, precio, id_categoria, descripcion, id_estado)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Torta", 20000, 2, None, ESTADO_ACTIVO),
        )
        connection.execute(
            """
            INSERT INTO ventas (
                id_venta, valor_total, fecha_venta, id_medio_pago, caja, tendero
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                20000,
                "2026-10-24T12:00:00",
                1,
                1,
                1,
            ),
        )
        connection.execute(
            """
            INSERT INTO venta_lineas (
                id_venta, id_producto, nombre_producto,
                precio_aplicado, cantidad, subtotal
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                1,
                "Torta",
                20000,
                1,
                20000,
            ),
        )
        connection.commit()
    finally:
        connection.close()
    return path


def test_ensure_pan_pequeno_on_existing_five_categories(tmp_path: Path) -> None:
    path = _beta2_five_categories_db(tmp_path)
    initialize(path)
    connection = connect(path)
    try:
        names = [c["nombre"] for c in list_categorias(connection)]
        assert names[:5] == list(SEED_CATEGORIAS)
        assert NOMBRE_CATEGORIA_PAN_PEQUENO in names
        assert names.count(NOMBRE_CATEGORIA_PAN_PEQUENO) == 1
        pan = get_categoria_by_nombre(connection, NOMBRE_CATEGORIA_PAN_PEQUENO)
        assert pan is not None
        assert pan["nombre"] == NOMBRE_CATEGORIA_PAN_PEQUENO
        sale = connection.execute(
            "SELECT id_venta, valor_total FROM ventas WHERE id_venta = ?",
            ("cccccccc-cccc-4ccc-8ccc-cccccccccccc",),
        ).fetchone()
        assert sale["valor_total"] == 20000
        line = connection.execute(
            "SELECT nombre_producto, subtotal FROM venta_lineas WHERE id_venta = ?",
            ("cccccccc-cccc-4ccc-8ccc-cccccccccccc",),
        ).fetchone()
        assert line["nombre_producto"] == "Torta"
        assert line["subtotal"] == 20000
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(productos)").fetchall()
        }
        assert "ruta_imagen" in columns
        product = get_producto(connection, 1)
        assert product is not None
        assert product["ruta_imagen"] is None
    finally:
        connection.close()


def test_ruta_imagen_nullable_and_writable(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        id_producto = insert_producto(
            connection,
            nombre="Pan rollo",
            precio=300,
            id_categoria=1,
            descripcion=None,
            id_estado=ESTADO_ACTIVO,
        )
        connection.commit()
        product = get_producto(connection, id_producto)
        assert product is not None
        assert product["ruta_imagen"] is None
        set_producto_ruta_imagen(
            connection, id_producto, "imagenes/productos/pan_rollo.png"
        )
        connection.commit()
        updated = get_producto(connection, id_producto)
        assert updated is not None
        assert updated["ruta_imagen"] == "imagenes/productos/pan_rollo.png"
        set_producto_ruta_imagen(connection, id_producto, None)
        connection.commit()
        cleared = get_producto(connection, id_producto)
        assert cleared is not None
        assert cleared["ruta_imagen"] is None
    finally:
        connection.close()


def test_imagenes_dirs_exist_after_initialize(tmp_path: Path) -> None:
    initialize(tmp_path / "bakery.sqlite3")
    root = Path(__file__).resolve().parents[1]
    assert (root / "imagenes" / "categorias").is_dir()
    assert (root / "imagenes" / "productos").is_dir()


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
