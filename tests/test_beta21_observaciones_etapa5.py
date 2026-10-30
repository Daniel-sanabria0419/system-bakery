"""Beta 2.1 Etapa 5: observaciones durante/posterior + trazabilidad mínima."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from bakery.api.app import create_app
from bakery.persistence.connection import connect
from bakery.persistence.repositories import (
    ORIGEN_OBSERVACION_DURANTE_VENTA,
    ORIGEN_OBSERVACION_POSTERIOR,
    TIPO_CAMBIO_CREACION,
    TIPO_CAMBIO_OBSERVACION_POSTERIOR,
    list_venta_cambios,
    list_venta_observaciones,
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
    observacion: str | None = None,
    id_venta: str | None = None,
) -> dict:
    payload = {
        "id_venta": id_venta or str(uuid.uuid4()),
        "id_medio_pago": id_medio_pago,
        "lineas": [
            {
                "id_producto": id_producto,
                "cantidad": cantidad,
                "precio_aplicado": precio,
            }
        ],
    }
    if observacion is not None:
        payload["observacion"] = observacion
    response = client.post("/ventas", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_create_sale_without_observacion_writes_creacion_audit(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        created = _post_sale(
            client, id_producto=pan["id_producto"], precio=5000
        )

        detail = client.get(f"/ventas/{created['id_venta']}")
        assert detail.status_code == 200
        assert detail.json()["observaciones"] == []

        connection = connect(db_path)
        try:
            cambios = list_venta_cambios(connection, created["id_venta"])
            assert len(cambios) == 1
            assert cambios[0]["tipo"] == TIPO_CAMBIO_CREACION
            assert cambios[0]["antes_json"] is None
            payload = json.loads(cambios[0]["despues_json"])
            assert payload["valor_total"] == 5000
            assert payload["id_medio_pago"] == 1
            assert payload["nombre_medio"] == "Efectivo"
            assert payload["observaciones"] == []
            assert len(payload["lineas"]) == 1
            assert list_venta_observaciones(connection, created["id_venta"]) == []
        finally:
            connection.close()


def test_create_sale_with_observacion_durante_venta(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        created = _post_sale(
            client,
            id_producto=pan["id_producto"],
            precio=5000,
            observacion="  Sin bolsas  ",
        )

        detail = client.get(f"/ventas/{created['id_venta']}")
        assert detail.status_code == 200
        obs = detail.json()["observaciones"]
        assert len(obs) == 1
        assert obs[0]["texto"] == "Sin bolsas"
        assert obs[0]["origen"] == ORIGEN_OBSERVACION_DURANTE_VENTA
        assert obs[0]["id_cambio"] is not None

        connection = connect(db_path)
        try:
            cambios = list_venta_cambios(connection, created["id_venta"])
            assert len(cambios) == 1
            assert cambios[0]["tipo"] == TIPO_CAMBIO_CREACION
            assert cambios[0]["id_cambio"] == obs[0]["id_cambio"]
            payload = json.loads(cambios[0]["despues_json"])
            assert payload["observaciones"] == [
                {
                    "texto": "Sin bolsas",
                    "origen": ORIGEN_OBSERVACION_DURANTE_VENTA,
                }
            ]
        finally:
            connection.close()


def test_create_sale_blank_observacion_is_omitted(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        created = _post_sale(
            client,
            id_producto=pan["id_producto"],
            precio=5000,
            observacion="   ",
        )
        detail = client.get(f"/ventas/{created['id_venta']}")
        assert detail.status_code == 200
        assert detail.json()["observaciones"] == []


def test_post_observacion_posterior_always_allowed(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        created = _post_sale(
            client,
            id_producto=pan["id_producto"],
            precio=5000,
            observacion="Al momento",
        )

        response = client.post(
            f"/ventas/{created['id_venta']}/observaciones",
            json={"texto": "  Cliente llamó  "},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["texto"] == "Cliente llamó"
        assert body["origen"] == ORIGEN_OBSERVACION_POSTERIOR
        assert body["id_cambio"] is not None
        assert body["id_venta"] == created["id_venta"]

        detail = client.get(f"/ventas/{created['id_venta']}")
        assert detail.status_code == 200
        obs = detail.json()["observaciones"]
        assert [o["texto"] for o in obs] == ["Al momento", "Cliente llamó"]
        assert obs[0]["origen"] == ORIGEN_OBSERVACION_DURANTE_VENTA
        assert obs[1]["origen"] == ORIGEN_OBSERVACION_POSTERIOR

        connection = connect(db_path)
        try:
            cambios = list_venta_cambios(connection, created["id_venta"])
            assert [c["tipo"] for c in cambios] == [
                TIPO_CAMBIO_CREACION,
                TIPO_CAMBIO_OBSERVACION_POSTERIOR,
            ]
            assert cambios[1]["id_cambio"] == body["id_cambio"]
            payload = json.loads(cambios[1]["despues_json"])
            assert payload["texto"] == "Cliente llamó"
            assert payload["origen"] == ORIGEN_OBSERVACION_POSTERIOR
        finally:
            connection.close()


def test_post_observacion_empty_text_400(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        created = _post_sale(
            client, id_producto=pan["id_producto"], precio=5000
        )
        for texto in ("", "   "):
            response = client.post(
                f"/ventas/{created['id_venta']}/observaciones",
                json={"texto": texto},
            )
            assert response.status_code == 400, response.text
            assert "vacía" in response.json()["detail"].lower()


def test_post_observacion_unknown_sale_404(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        response = client.post(
            f"/ventas/{uuid.uuid4()}/observaciones",
            json={"texto": "Hola"},
        )
        assert response.status_code == 404


def test_idempotent_create_does_not_duplicate_observacion(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        id_venta = str(uuid.uuid4())
        first = _post_sale(
            client,
            id_producto=pan["id_producto"],
            precio=5000,
            observacion="Primera",
            id_venta=id_venta,
        )
        second = client.post(
            "/ventas",
            json={
                "id_venta": id_venta,
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": pan["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 5000,
                    }
                ],
                "observacion": "Segunda distinta",
            },
        )
        assert second.status_code == 200
        assert second.json()["id_venta"] == first["id_venta"]

        detail = client.get(f"/ventas/{id_venta}")
        obs = detail.json()["observaciones"]
        assert [o["texto"] for o in obs] == ["Primera"]

        connection = connect(db_path)
        try:
            assert len(list_venta_cambios(connection, id_venta)) == 1
        finally:
            connection.close()
