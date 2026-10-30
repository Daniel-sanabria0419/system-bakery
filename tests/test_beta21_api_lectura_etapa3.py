"""Beta 2.1 Etapa 3: GET /ventas y GET /ventas/{id} con flag editable."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from bakery.api.app import create_app
from bakery.persistence.connection import connect
from bakery.persistence.repositories import (
    EDITABLE_WINDOW_SECONDS,
    ORIGEN_OBSERVACION_DURANTE_VENTA,
    ORIGEN_OBSERVACION_POSTERIOR,
    insert_sale,
    insert_venta_observacion,
)


def _create_product(
    client: TestClient, *, nombre: str, precio: int, id_categoria: int = 1
) -> dict:
    response = client.post(
        "/productos",
        json={"nombre": nombre, "precio": precio, "id_categoria": id_categoria},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _post_sale(
    client: TestClient,
    *,
    id_producto: int,
    precio: int,
    cantidad: int = 1,
    id_medio_pago: int = 1,
) -> dict:
    response = client.post(
        "/ventas",
        json={
            "id_venta": str(uuid.uuid4()),
            "id_medio_pago": id_medio_pago,
            "lineas": [
                {
                    "id_producto": id_producto,
                    "cantidad": cantidad,
                    "precio_aplicado": precio,
                }
            ],
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _set_fecha_venta(db_path: Path, id_venta: str, fecha_venta: str) -> None:
    connection = connect(db_path)
    try:
        connection.execute(
            "UPDATE ventas SET fecha_venta = ? WHERE id_venta = ?",
            (fecha_venta, id_venta),
        )
        connection.commit()
    finally:
        connection.close()


def test_get_ventas_lists_newest_first_with_medio(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        first = _post_sale(client, id_producto=pan["id_producto"], precio=5000)
        second = _post_sale(
            client, id_producto=pan["id_producto"], precio=5000, cantidad=2
        )
        _set_fecha_venta(db_path, first["id_venta"], "2026-10-01T09:00:00")
        _set_fecha_venta(db_path, second["id_venta"], "2026-10-30T12:00:00")

        response = client.get("/ventas")
        assert response.status_code == 200
        rows = response.json()
        assert [r["id_venta"] for r in rows] == [
            second["id_venta"],
            first["id_venta"],
        ]
        assert rows[0]["nombre_medio"] == "Efectivo"
        assert rows[0]["cantidad_lineas"] == 1
        assert rows[0]["es_legado"] is False
        assert "editable" in rows[0]


def test_get_venta_detail_with_lines(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        cafe = _create_product(client, nombre="Cafe", precio=3000)
        created = client.post(
            "/ventas",
            json={
                "id_venta": str(uuid.uuid4()),
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": pan["id_producto"],
                        "cantidad": 2,
                        "precio_aplicado": 5000,
                    },
                    {
                        "id_producto": cafe["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 3000,
                    },
                ],
            },
        )
        assert created.status_code == 200
        id_venta = created.json()["id_venta"]

        response = client.get(f"/ventas/{id_venta}")
        assert response.status_code == 200
        detail = response.json()
        assert detail["id_venta"] == id_venta
        assert detail["valor_total"] == 13000
        assert detail["nombre_medio"] == "Efectivo"
        assert detail["es_legado"] is False
        assert len(detail["lineas"]) == 2
        assert detail["lineas"][0]["nombre_producto"] == "Pan"
        assert detail["lineas"][0]["cantidad"] == 2
        assert detail["lineas"][0]["precio_aplicado"] == 5000
        assert detail["lineas"][0]["subtotal"] == 10000
        assert detail["lineas"][0]["total"] == 10000
        assert detail["lineas"][1]["nombre_producto"] == "Cafe"
        assert detail["observaciones"] == []
        assert isinstance(detail["editable"], bool)


def test_get_venta_detail_legado_sin_lineas(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        connection = connect(db_path)
        try:
            insert_sale(
                connection,
                id_venta="legado-api-1",
                valor_total=12000,
                fecha_venta="2026-09-01T08:00:00",
                id_medio_pago=1,
            )
            connection.commit()
        finally:
            connection.close()

        response = client.get("/ventas/legado-api-1")
        assert response.status_code == 200
        detail = response.json()
        assert detail["valor_total"] == 12000
        assert detail["lineas"] == []
        assert detail["observaciones"] == []
        assert detail["es_legado"] is True
        assert detail["editable"] is False

        listed = client.get("/ventas").json()
        legado = next(r for r in listed if r["id_venta"] == "legado-api-1")
        assert legado["cantidad_lineas"] == 0
        assert legado["es_legado"] is True


def test_get_venta_404(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        response = client.get("/ventas/no-existe")
        assert response.status_code == 404
        assert "no encontrada" in response.json()["detail"].lower()


def test_editable_true_within_window_false_after(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        recent = _post_sale(client, id_producto=pan["id_producto"], precio=5000)
        old = _post_sale(client, id_producto=pan["id_producto"], precio=5000)

        now = datetime.now().replace(microsecond=0)
        _set_fecha_venta(
            db_path,
            recent["id_venta"],
            (now - timedelta(minutes=59)).isoformat(timespec="seconds"),
        )
        _set_fecha_venta(
            db_path,
            old["id_venta"],
            (now - timedelta(minutes=61)).isoformat(timespec="seconds"),
        )

        recent_detail = client.get(f"/ventas/{recent['id_venta']}").json()
        old_detail = client.get(f"/ventas/{old['id_venta']}").json()
        assert recent_detail["editable"] is True
        assert old_detail["editable"] is False

        listed = {r["id_venta"]: r for r in client.get("/ventas").json()}
        assert listed[recent["id_venta"]]["editable"] is True
        assert listed[old["id_venta"]]["editable"] is False


def test_editable_boundary_exactly_one_hour(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        sale = _post_sale(client, id_producto=pan["id_producto"], precio=5000)
        now = datetime.now().replace(microsecond=0)
        _set_fecha_venta(
            db_path,
            sale["id_venta"],
            (now - timedelta(seconds=EDITABLE_WINDOW_SECONDS)).isoformat(
                timespec="seconds"
            ),
        )
        detail = client.get(f"/ventas/{sale['id_venta']}").json()
        assert detail["editable"] is False


def test_detail_includes_observaciones_ordered(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        sale = _post_sale(client, id_producto=pan["id_producto"], precio=5000)
        connection = connect(db_path)
        try:
            insert_venta_observacion(
                connection,
                id_venta=sale["id_venta"],
                texto="Durante",
                origen=ORIGEN_OBSERVACION_DURANTE_VENTA,
                fecha_creacion="2026-10-30T10:00:00",
            )
            insert_venta_observacion(
                connection,
                id_venta=sale["id_venta"],
                texto="Posterior",
                origen=ORIGEN_OBSERVACION_POSTERIOR,
                fecha_creacion="2026-10-30T10:30:00",
            )
            connection.commit()
        finally:
            connection.close()

        detail = client.get(f"/ventas/{sale['id_venta']}").json()
        assert [o["texto"] for o in detail["observaciones"]] == [
            "Durante",
            "Posterior",
        ]
        assert detail["observaciones"][0]["origen"] == ORIGEN_OBSERVACION_DURANTE_VENTA
        assert detail["observaciones"][1]["origen"] == ORIGEN_OBSERVACION_POSTERIOR


def test_post_ventas_unaffected_by_get_endpoints(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        created = _post_sale(
            client, id_producto=pan["id_producto"], precio=5000, cantidad=3
        )
        assert created["valor_total"] == 15000
        assert client.get("/ventas").status_code == 200
        assert client.get(f"/ventas/{created['id_venta']}").status_code == 200
        again = _post_sale(client, id_producto=pan["id_producto"], precio=5000)
        assert again["valor_total"] == 5000
