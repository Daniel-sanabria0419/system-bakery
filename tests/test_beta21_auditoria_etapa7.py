"""Beta 2.1 Etapa 7: auditoría completa create/edit + GET /ventas/{id}/cambios."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from bakery.api.app import create_app
from bakery.persistence.connection import connect
from bakery.persistence.repositories import (
    TIPO_CAMBIO_CREACION,
    TIPO_CAMBIO_EDICION,
    list_venta_cambios,
)
from bakery.persistence import initialize


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


def test_get_cambios_after_one_edit_has_creacion_and_edicion(tmp_path: Path) -> None:
    """Tras 1 edición: 2 filas; JSON con medios y líneas (ejemplo Daniel)."""
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

        put = client.put(
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
        assert put.status_code == 200, put.text

        response = client.get(f"/ventas/{created['id_venta']}/cambios")
        assert response.status_code == 200, response.text
        cambios = response.json()
        assert len(cambios) == 2

        assert cambios[0]["tipo"] == TIPO_CAMBIO_CREACION
        assert cambios[0]["antes"] is None
        despues_creacion = cambios[0]["despues"]
        assert despues_creacion["id_medio_pago"] == 1
        assert despues_creacion["nombre_medio"] == "Efectivo"
        assert despues_creacion["valor_total"] == 5000
        assert len(despues_creacion["lineas"]) == 1
        assert despues_creacion["lineas"][0]["nombre_producto"] == "Producto A"
        assert despues_creacion["lineas"][0]["cantidad"] == 1
        assert despues_creacion["lineas"][0]["precio_aplicado"] == 5000
        assert despues_creacion["lineas"][0]["total"] == 5000

        assert cambios[1]["tipo"] == TIPO_CAMBIO_EDICION
        antes = cambios[1]["antes"]
        despues = cambios[1]["despues"]
        assert antes["valor_total"] == 5000
        assert antes["id_medio_pago"] == 1
        assert antes["nombre_medio"] == "Efectivo"
        assert antes["lineas"][0]["cantidad"] == 1
        assert despues["valor_total"] == 10000
        assert despues["id_medio_pago"] == 2
        assert despues["nombre_medio"] == "Daviplata"
        assert despues["lineas"][0]["cantidad"] == 2
        assert despues["lineas"][0]["nombre_producto"] == "Producto A"
        assert despues["lineas"][0]["total"] == 10000

        # Filas de auditoría no se borran al reemplazar líneas.
        connection = connect(db_path)
        try:
            persisted = list_venta_cambios(connection, created["id_venta"])
            assert len(persisted) == 2
        finally:
            connection.close()


def test_get_cambios_404_unknown_sale(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        response = client.get(f"/ventas/{uuid.uuid4()}/cambios")
        assert response.status_code == 404


def test_catalog_rename_does_not_alter_audit_snapshots(tmp_path: Path) -> None:
    """Renombrar producto en catálogo no muta snapshots ya guardados en auditoría."""
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Nombre original", precio=3000)
        created = _post_sale(
            client,
            id_producto=pan["id_producto"],
            precio=3000,
            cantidad=1,
            id_medio_pago=1,
        )

        rename = client.put(
            f"/productos/{pan['id_producto']}",
            json={
                "nombre": "Nombre renombrado",
                "precio": 3000,
                "id_categoria": pan["id_categoria"],
            },
        )
        assert rename.status_code == 200, rename.text
        assert rename.json()["nombre"] == "Nombre renombrado"

        response = client.get(f"/ventas/{created['id_venta']}/cambios")
        assert response.status_code == 200, response.text
        cambios = response.json()
        assert len(cambios) == 1
        assert cambios[0]["tipo"] == TIPO_CAMBIO_CREACION
        line = cambios[0]["despues"]["lineas"][0]
        assert line["nombre_producto"] == "Nombre original"
        assert line["id_producto"] == pan["id_producto"]

        detail = client.get(f"/ventas/{created['id_venta']}")
        assert detail.status_code == 200
        assert detail.json()["lineas"][0]["nombre_producto"] == "Nombre original"


def test_create_only_exposes_creacion_via_get_cambios(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Solo create", precio=1500)
        created = _post_sale(
            client,
            id_producto=pan["id_producto"],
            precio=1500,
            cantidad=2,
            id_medio_pago=1,
        )
        response = client.get(f"/ventas/{created['id_venta']}/cambios")
        assert response.status_code == 200
        cambios = response.json()
        assert len(cambios) == 1
        assert cambios[0]["tipo"] == TIPO_CAMBIO_CREACION
        assert cambios[0]["antes"] is None
        assert cambios[0]["despues"]["valor_total"] == 3000
        assert cambios[0]["despues"]["lineas"][0]["cantidad"] == 2
