"""Etapa 5: id_venta del cliente; reintento con el mismo UUID no duplica."""

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from bakery.api.app import create_app
from bakery.app.products import create_product
from bakery.app.sales import SaleValidationError, register_sale
from bakery.persistence import initialize
from bakery.persistence.connection import connect
import pytest


def _db(tmp_path: Path):
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    return connect(path)


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(tmp_path / "bakery.sqlite3"))


def test_register_sale_retry_same_id_returns_existing(tmp_path: Path) -> None:
    connection = _db(tmp_path)
    try:
        product = create_product(
            connection, nombre="Pan", precio=3000, id_categoria=1
        )
        sale_id = str(uuid4())
        lineas = [
            {
                "id_producto": product["id_producto"],
                "cantidad": 2,
                "precio_aplicado": 3000,
            }
        ]
        first = register_sale(connection, 1, lineas, id_venta=sale_id)
        # Reintento "tras timeout": mismo id, cuerpo distinto no inserta otra.
        second = register_sale(
            connection,
            1,
            [
                {
                    "id_producto": product["id_producto"],
                    "cantidad": 99,
                    "precio_aplicado": 3000,
                }
            ],
            id_venta=sale_id,
        )
        assert second == first
        assert second["id_venta"] == sale_id
        assert second["valor_total"] == 6000
        count = connection.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
        assert count == 1
        lines = connection.execute(
            "SELECT COUNT(*) FROM venta_lineas WHERE id_venta = ?",
            (sale_id,),
        ).fetchone()[0]
        assert lines == 1
    finally:
        connection.close()


def test_new_payment_uses_another_uuid(tmp_path: Path) -> None:
    connection = _db(tmp_path)
    try:
        product = create_product(
            connection, nombre="Pan", precio=1000, id_categoria=1
        )
        lineas = [
            {
                "id_producto": product["id_producto"],
                "cantidad": 1,
                "precio_aplicado": 1000,
            }
        ]
        first = register_sale(connection, 1, lineas, id_venta=str(uuid4()))
        second = register_sale(connection, 1, lineas, id_venta=str(uuid4()))
        assert first["id_venta"] != second["id_venta"]
        count = connection.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
        assert count == 2
    finally:
        connection.close()


def test_register_sale_rejects_invalid_id_venta(tmp_path: Path) -> None:
    connection = _db(tmp_path)
    try:
        product = create_product(
            connection, nombre="Pan", precio=1000, id_categoria=1
        )
        with pytest.raises(SaleValidationError, match="id_venta"):
            register_sale(
                connection,
                1,
                [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 1000,
                    }
                ],
                id_venta="no-es-uuid",
            )
    finally:
        connection.close()


def test_post_ventas_idempotent_retry(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        product = client.post(
            "/productos",
            json={"nombre": "Pan", "precio": 2500, "id_categoria": 1},
        ).json()
        sale_id = str(uuid4())
        body = {
            "id_venta": sale_id,
            "id_medio_pago": 1,
            "lineas": [
                {
                    "id_producto": product["id_producto"],
                    "cantidad": 1,
                    "precio_aplicado": 2500,
                }
            ],
        }
        first = client.post("/ventas", json=body)
        assert first.status_code == 200
        assert first.json()["id_venta"] == sale_id
        assert first.json()["valor_total"] == 2500

        retry = client.post("/ventas", json=body)
        assert retry.status_code == 200
        assert retry.json() == first.json()

        connection = connect(db_path)
        try:
            count = connection.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
            assert count == 1
        finally:
            connection.close()


def test_post_ventas_requires_id_venta(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        product = client.post(
            "/productos",
            json={"nombre": "Pan", "precio": 1000, "id_categoria": 1},
        ).json()
        response = client.post(
            "/ventas",
            json={
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 1000,
                    }
                ],
            },
        )
        assert response.status_code == 400
