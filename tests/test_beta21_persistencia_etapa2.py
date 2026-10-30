"""Beta 2.1 Etapa 2: list/detail de ventas + helper ventana 1 h (persistencia)."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.repositories import (
    EDITABLE_WINDOW_SECONDS,
    ORIGEN_OBSERVACION_DURANTE_VENTA,
    ORIGEN_OBSERVACION_POSTERIOR,
    TIPO_CAMBIO_CREACION,
    get_sale_detail,
    insert_producto,
    insert_sale,
    insert_venta_cambio,
    insert_venta_linea,
    insert_venta_observacion,
    list_venta_cambios,
    list_ventas,
    sale_is_editable,
)
from bakery.persistence.schema import ESTADO_ACTIVO


def _db(tmp_path: Path) -> Path:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    return path


def _medio_efectivo_id(connection) -> int:
    row = connection.execute(
        "SELECT id_medio_pago FROM medios_pago WHERE nombre = ?",
        ("Efectivo",),
    ).fetchone()
    assert row is not None
    return int(row["id_medio_pago"])


def _medio_nequi_id(connection) -> int:
    row = connection.execute(
        "SELECT id_medio_pago FROM medios_pago WHERE nombre = ?",
        ("Nequi",),
    ).fetchone()
    assert row is not None
    return int(row["id_medio_pago"])


def _categoria_id(connection) -> int:
    row = connection.execute(
        "SELECT id_categoria FROM categorias ORDER BY id_categoria LIMIT 1"
    ).fetchone()
    assert row is not None
    return int(row["id_categoria"])


def test_list_ventas_orders_by_fecha_desc(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        medio = _medio_efectivo_id(connection)
        insert_sale(
            connection,
            id_venta="venta-antigua",
            valor_total=1000,
            fecha_venta="2026-10-01T09:00:00",
            id_medio_pago=medio,
        )
        insert_sale(
            connection,
            id_venta="venta-nueva",
            valor_total=2000,
            fecha_venta="2026-10-30T12:00:00",
            id_medio_pago=medio,
        )
        insert_sale(
            connection,
            id_venta="venta-media",
            valor_total=1500,
            fecha_venta="2026-10-15T10:00:00",
            id_medio_pago=medio,
        )
        connection.commit()

        rows = list_ventas(connection)
        assert [r["id_venta"] for r in rows] == [
            "venta-nueva",
            "venta-media",
            "venta-antigua",
        ]
    finally:
        connection.close()


def test_list_ventas_joins_medio_and_line_count(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        medio_efectivo = _medio_efectivo_id(connection)
        medio_nequi = _medio_nequi_id(connection)
        id_categoria = _categoria_id(connection)
        id_producto = insert_producto(
            connection,
            nombre="Pan",
            precio=5000,
            id_categoria=id_categoria,
            descripcion=None,
            id_estado=ESTADO_ACTIVO,
        )
        insert_sale(
            connection,
            id_venta="con-lineas",
            valor_total=5000,
            fecha_venta="2026-10-30T11:00:00",
            id_medio_pago=medio_efectivo,
        )
        insert_venta_linea(
            connection,
            id_venta="con-lineas",
            id_producto=id_producto,
            nombre_producto="Pan",
            precio_aplicado=5000,
            cantidad=1,
            subtotal=5000,
            total=5000,
        )
        insert_sale(
            connection,
            id_venta="legado",
            valor_total=8000,
            fecha_venta="2026-10-29T11:00:00",
            id_medio_pago=medio_nequi,
        )
        connection.commit()

        rows = {r["id_venta"]: r for r in list_ventas(connection)}
        assert rows["con-lineas"]["nombre_medio"] == "Efectivo"
        assert rows["con-lineas"]["cantidad_lineas"] == 1
        assert rows["legado"]["nombre_medio"] == "Nequi"
        assert rows["legado"]["cantidad_lineas"] == 0
    finally:
        connection.close()


def test_get_sale_detail_with_lines_and_observaciones(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        medio = _medio_efectivo_id(connection)
        id_categoria = _categoria_id(connection)
        id_producto = insert_producto(
            connection,
            nombre="Cafe",
            precio=3000,
            id_categoria=id_categoria,
            descripcion=None,
            id_estado=ESTADO_ACTIVO,
        )
        insert_sale(
            connection,
            id_venta="detalle-1",
            valor_total=3000,
            fecha_venta="2026-10-30T10:00:00",
            id_medio_pago=medio,
        )
        insert_venta_linea(
            connection,
            id_venta="detalle-1",
            id_producto=id_producto,
            nombre_producto="Cafe",
            precio_aplicado=3000,
            cantidad=1,
            subtotal=3000,
            total=3000,
        )
        id_cambio = insert_venta_cambio(
            connection,
            id_venta="detalle-1",
            fecha_cambio="2026-10-30T10:00:00",
            tipo=TIPO_CAMBIO_CREACION,
            despues_json='{"valor_total":3000}',
        )
        insert_venta_observacion(
            connection,
            id_venta="detalle-1",
            texto="Sin azucar",
            origen=ORIGEN_OBSERVACION_DURANTE_VENTA,
            fecha_creacion="2026-10-30T10:00:00",
            id_cambio=id_cambio,
        )
        insert_venta_observacion(
            connection,
            id_venta="detalle-1",
            texto="Cliente llamo",
            origen=ORIGEN_OBSERVACION_POSTERIOR,
            fecha_creacion="2026-10-30T10:30:00",
        )
        connection.commit()

        detail = get_sale_detail(connection, "detalle-1")
        assert detail is not None
        assert detail["id_venta"] == "detalle-1"
        assert detail["valor_total"] == 3000
        assert detail["nombre_medio"] == "Efectivo"
        assert len(detail["lineas"]) == 1
        assert detail["lineas"][0]["nombre_producto"] == "Cafe"
        assert [o["texto"] for o in detail["observaciones"]] == [
            "Sin azucar",
            "Cliente llamo",
        ]
        assert detail["observaciones"][0]["origen"] == ORIGEN_OBSERVACION_DURANTE_VENTA
        assert detail["observaciones"][1]["origen"] == ORIGEN_OBSERVACION_POSTERIOR
        assert list_venta_cambios(connection, "detalle-1")[0]["tipo"] == TIPO_CAMBIO_CREACION
    finally:
        connection.close()


def test_get_sale_detail_legado_sin_lineas(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        medio = _medio_nequi_id(connection)
        insert_sale(
            connection,
            id_venta="legado-only",
            valor_total=12000,
            fecha_venta="2026-09-01T08:00:00",
            id_medio_pago=medio,
        )
        connection.commit()

        detail = get_sale_detail(connection, "legado-only")
        assert detail is not None
        assert detail["nombre_medio"] == "Nequi"
        assert detail["lineas"] == []
        assert detail["observaciones"] == []
        assert detail["valor_total"] == 12000
    finally:
        connection.close()


def test_get_sale_detail_missing_returns_none(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        assert get_sale_detail(connection, "no-existe") is None
    finally:
        connection.close()


def test_sale_is_editable_59_and_61_minutes() -> None:
    fecha = "2026-10-30T10:00:00"
    fecha_dt = datetime.fromisoformat(fecha)

    assert sale_is_editable(fecha, now=fecha_dt + timedelta(minutes=59)) is True
    assert sale_is_editable(fecha, now=fecha_dt + timedelta(minutes=61)) is False

    # Inclusive boundary: editable solo si elapsed < 3600 s.
    assert sale_is_editable(
        fecha, now=fecha_dt + timedelta(seconds=EDITABLE_WINDOW_SECONDS - 1)
    ) is True
    assert sale_is_editable(
        fecha, now=fecha_dt + timedelta(seconds=EDITABLE_WINDOW_SECONDS)
    ) is False


def test_sale_is_editable_accepts_iso_now_string() -> None:
    fecha = "2026-10-30T10:00:00"
    assert sale_is_editable(fecha, now="2026-10-30T10:30:00") is True
    assert sale_is_editable(fecha, now="2026-10-30T11:01:00") is False
