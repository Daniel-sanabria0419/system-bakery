"""Beta 2.1 Etapa 6: PUT /ventas/{id} + ventana 1 h + recalc promo + auditoría mínima."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from bakery.api.app import create_app
from bakery.app.products import create_product
from bakery.app.sales import (
    SaleNotEditableError,
    register_sale,
    update_sale,
)
from bakery.persistence.connection import connect
from bakery.persistence.repositories import (
    EDITABLE_WINDOW_SECONDS,
    TIPO_CAMBIO_CREACION,
    TIPO_CAMBIO_EDICION,
    get_categoria_by_nombre,
    list_venta_cambios,
    list_venta_lineas,
    set_producto_promocion_id,
)
from bakery.app.pan_pequeno_pricing import PRECIO_UNITARIO_PAN_PEQUENO
from bakery.persistence import initialize
from bakery.persistence.schema import (
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    NOMBRE_PROMOCION_PAN_PEQUENO,
    ensure_promocion_pan_pequeno,
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
    id_venta: str | None = None,
) -> dict:
    sale_id = id_venta or str(uuid.uuid4())
    response = client.post(
        "/ventas",
        json={
            "id_venta": sale_id,
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


def test_put_edit_within_window_qty_and_medio_daniel_example(tmp_path: Path) -> None:
    """A×1 $5000 efectivo → A×2 $10000 Daviplata (ejemplo Daniel)."""
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Producto A", precio=5000)
        created = _post_sale(
            client,
            id_producto=pan["id_producto"],
            precio=5000,
            cantidad=1,
            id_medio_pago=1,
        )
        assert created["valor_total"] == 5000
        assert created["id_medio_pago"] == 1

        response = client.put(
            f"/ventas/{created['id_venta']}",
            json={
                "id_medio_pago": 2,
                "lineas": [
                    {
                        "id_producto": pan["id_producto"],
                        "cantidad": 2,
                        "precio_aplicado": 5000,
                    }
                ],
            },
        )
        assert response.status_code == 200, response.text
        updated = response.json()
        assert updated["valor_total"] == 10000
        assert updated["id_medio_pago"] == 2
        assert updated["fecha_venta"] == created["fecha_venta"]
        assert updated["id_venta"] == created["id_venta"]
        assert updated["caja"] == created["caja"]
        assert updated["tendero"] == created["tendero"]

        detail = client.get(f"/ventas/{created['id_venta']}")
        assert detail.status_code == 200
        body = detail.json()
        assert body["valor_total"] == 10000
        assert body["nombre_medio"] == "Daviplata"
        assert len(body["lineas"]) == 1
        assert body["lineas"][0]["cantidad"] == 2
        assert body["lineas"][0]["total"] == 10000

        connection = connect(db_path)
        try:
            cambios = list_venta_cambios(connection, created["id_venta"])
            assert len(cambios) == 2
            assert cambios[0]["tipo"] == TIPO_CAMBIO_CREACION
            assert cambios[1]["tipo"] == TIPO_CAMBIO_EDICION
            antes = json.loads(cambios[1]["antes_json"])
            despues = json.loads(cambios[1]["despues_json"])
            assert antes["valor_total"] == 5000
            assert antes["id_medio_pago"] == 1
            assert antes["nombre_medio"] == "Efectivo"
            assert despues["valor_total"] == 10000
            assert despues["id_medio_pago"] == 2
            assert despues["nombre_medio"] == "Daviplata"
            assert despues["lineas"][0]["cantidad"] == 2
        finally:
            connection.close()


def test_put_recalculates_promo_nudo(tmp_path: Path) -> None:
    """Editar cantidad a múltiplo promo recalcula total con motor vigente."""
    db_path = tmp_path / "bakery.sqlite3"
    initialize(db_path)
    connection = connect(db_path)
    try:
        cat = get_categoria_by_nombre(connection, NOMBRE_CATEGORIA_PAN_PEQUENO)
        assert cat is not None
        promo_id = ensure_promocion_pan_pequeno(connection)
        rollo = create_product(
            connection,
            nombre="Pan rollo edit",
            precio=PRECIO_UNITARIO_PAN_PEQUENO,
            id_categoria=cat["id_categoria"],
        )
        set_producto_promocion_id(connection, rollo["id_producto"], promo_id)
        connection.commit()

        created = register_sale(
            connection,
            1,
            [
                {
                    "id_producto": rollo["id_producto"],
                    "cantidad": 1,
                    "precio_aplicado": PRECIO_UNITARIO_PAN_PEQUENO,
                }
            ],
            id_venta=str(uuid.uuid4()),
        )
        assert created["valor_total"] == 300

        updated = update_sale(
            connection,
            created["id_venta"],
            1,
            [
                {
                    "id_producto": rollo["id_producto"],
                    "cantidad": 7,
                    "precio_aplicado": PRECIO_UNITARIO_PAN_PEQUENO,
                }
            ],
        )
        assert updated["valor_total"] == 2000
        lines = list_venta_lineas(connection, created["id_venta"])
        assert len(lines) == 1
        assert lines[0]["cantidad"] == 7
        assert lines[0]["subtotal"] == 2100
        assert lines[0]["total"] == 2000
        assert lines[0]["id_promocion"] == promo_id
        assert lines[0]["nombre_promocion"] == NOMBRE_PROMOCION_PAN_PEQUENO
    finally:
        connection.close()


def test_put_outside_window_returns_409(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        created = _post_sale(
            client, id_producto=pan["id_producto"], precio=5000
        )
        past = (
            datetime.now() - timedelta(seconds=EDITABLE_WINDOW_SECONDS + 60)
        ).replace(microsecond=0).isoformat(timespec="seconds")
        _set_fecha_venta(db_path, created["id_venta"], past)

        response = client.put(
            f"/ventas/{created['id_venta']}",
            json={
                "id_medio_pago": 2,
                "lineas": [
                    {
                        "id_producto": pan["id_producto"],
                        "cantidad": 2,
                        "precio_aplicado": 5000,
                    }
                ],
            },
        )
        assert response.status_code == 409
        assert "primera hora" in response.json()["detail"].lower()

        detail = client.get(f"/ventas/{created['id_venta']}")
        assert detail.json()["valor_total"] == 5000
        assert detail.json()["id_medio_pago"] == 1


def test_put_rejects_fecha_venta_from_client(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        created = _post_sale(
            client, id_producto=pan["id_producto"], precio=5000
        )
        response = client.put(
            f"/ventas/{created['id_venta']}",
            json={
                "id_medio_pago": 1,
                "fecha_venta": "2099-01-01T00:00:00",
                "lineas": [
                    {
                        "id_producto": pan["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 5000,
                    }
                ],
            },
        )
        assert response.status_code == 400


def test_put_rejects_inactive_product(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        other = _create_product(client, nombre="Cafe", precio=3000)
        created = _post_sale(
            client, id_producto=pan["id_producto"], precio=5000
        )
        deactivated = client.post(f"/productos/{other['id_producto']}/desactivar")
        assert deactivated.status_code == 200

        response = client.put(
            f"/ventas/{created['id_venta']}",
            json={
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": other["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 3000,
                    }
                ],
            },
        )
        assert response.status_code == 400
        assert "activo" in response.json()["detail"].lower()


def test_put_legado_rejects_invented_lineas(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        connection = connect(db_path)
        try:
            from bakery.persistence.repositories import insert_sale

            insert_sale(
                connection,
                id_venta="legado-edit-1",
                valor_total=9000,
                fecha_venta=datetime.now()
                .replace(microsecond=0)
                .isoformat(timespec="seconds"),
                id_medio_pago=1,
            )
            connection.commit()
        finally:
            connection.close()

        response = client.put(
            "/ventas/legado-edit-1",
            json={
                "id_medio_pago": 2,
                "lineas": [
                    {
                        "id_producto": pan["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 5000,
                    }
                ],
            },
        )
        assert response.status_code == 400
        assert "legado" in response.json()["detail"].lower()


def test_put_legado_allows_medio_only(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        connection = connect(db_path)
        try:
            from bakery.persistence.repositories import insert_sale

            insert_sale(
                connection,
                id_venta="legado-edit-2",
                valor_total=9000,
                fecha_venta=datetime.now()
                .replace(microsecond=0)
                .isoformat(timespec="seconds"),
                id_medio_pago=1,
            )
            connection.commit()
        finally:
            connection.close()

        response = client.put(
            "/ventas/legado-edit-2",
            json={"id_medio_pago": 3, "lineas": []},
        )
        assert response.status_code == 200, response.text
        updated = response.json()
        assert updated["valor_total"] == 9000
        assert updated["id_medio_pago"] == 3
        detail = client.get("/ventas/legado-edit-2")
        assert detail.json()["lineas"] == []
        assert detail.json()["es_legado"] is True


def test_post_idempotent_unchanged_after_put_exists(tmp_path: Path) -> None:
    """POST con mismo UUID sigue siendo create idempotente (no muta)."""
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        sale_id = str(uuid.uuid4())
        created = _post_sale(
            client,
            id_producto=pan["id_producto"],
            precio=5000,
            id_venta=sale_id,
        )
        client.put(
            f"/ventas/{sale_id}",
            json={
                "id_medio_pago": 2,
                "lineas": [
                    {
                        "id_producto": pan["id_producto"],
                        "cantidad": 2,
                        "precio_aplicado": 5000,
                    }
                ],
            },
        )
        # Reintento POST con cuerpo distinto: no debe sobrescribir la edición.
        retry = client.post(
            "/ventas",
            json={
                "id_venta": sale_id,
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": pan["id_producto"],
                        "cantidad": 99,
                        "precio_aplicado": 5000,
                    }
                ],
            },
        )
        assert retry.status_code == 200
        assert retry.json()["valor_total"] == 10000
        assert retry.json()["id_medio_pago"] == 2


def test_update_sale_not_editable_at_exact_window(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    initialize(db_path)
    connection = connect(db_path)
    try:
        product = create_product(
            connection, nombre="Pan", precio=5000, id_categoria=1
        )
        fecha = "2026-10-30T10:00:00"
        created = register_sale(
            connection,
            1,
            [
                {
                    "id_producto": product["id_producto"],
                    "cantidad": 1,
                    "precio_aplicado": 5000,
                }
            ],
            id_venta=str(uuid.uuid4()),
            fecha_venta=fecha,
        )
        now_at_limit = (
            datetime.fromisoformat(fecha)
            + timedelta(seconds=EDITABLE_WINDOW_SECONDS)
        )
        try:
            update_sale(
                connection,
                created["id_venta"],
                2,
                [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 2,
                        "precio_aplicado": 5000,
                    }
                ],
                now=now_at_limit,
            )
            raise AssertionError("expected SaleNotEditableError")
        except SaleNotEditableError:
            pass
    finally:
        connection.close()


def test_put_404_unknown_sale(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        response = client.put(
            f"/ventas/{uuid.uuid4()}",
            json={"id_medio_pago": 1, "lineas": []},
        )
        assert response.status_code == 404


def test_put_with_observacion_venta_appends_durante(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        created = client.post(
            "/ventas",
            json={
                "id_venta": str(uuid.uuid4()),
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": pan["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 5000,
                    }
                ],
                "observacion": "Original",
            },
        ).json()

        response = client.put(
            f"/ventas/{created['id_venta']}",
            json={
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": pan["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 5000,
                    }
                ],
                "observacion_venta": "Corregida",
            },
        )
        assert response.status_code == 200, response.text
        detail = client.get(f"/ventas/{created['id_venta']}").json()
        textos = [o["texto"] for o in detail["observaciones"]]
        assert textos == ["Original", "Corregida"]
        assert all(
            o["origen"] == "durante_venta" for o in detail["observaciones"]
        )
