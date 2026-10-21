from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from bakery.api.app import create_app
from bakery.persistence.connection import connect
from bakery.persistence.schema import SEED_MEDIOS_PAGO


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(tmp_path / "bakery.sqlite3"))


def _create_product(client: TestClient, *, nombre: str, precio: int, id_categoria: int = 1) -> dict:
    response = client.post(
        "/productos",
        json={
            "nombre": nombre,
            "precio": precio,
            "id_categoria": id_categoria,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_list_active_payment_methods(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        response = client.get("/medios-pago")
        assert response.status_code == 200
        payload = response.json()
        assert [item["nombre"] for item in payload] == list(SEED_MEDIOS_PAGO)
        assert all(item["id_estado"] == 1 for item in payload)


def test_list_payment_methods_excludes_inactive(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        connection = connect(db_path)
        try:
            connection.execute(
                "INSERT INTO medios_pago (nombre, id_estado) VALUES (?, ?)",
                ("Inactivo", 0),
            )
            connection.commit()
        finally:
            connection.close()

        names = [item["nombre"] for item in client.get("/medios-pago").json()]
        assert "Inactivo" not in names
        assert "Efectivo" in names


def test_create_sale_returns_uuid_and_persists_lines(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        product = _create_product(client, nombre="Pan", precio=25000)
        response = client.post(
            "/ventas",
            json={
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 25000,
                    }
                ],
            },
        )
        assert response.status_code == 200
        payload = response.json()
        UUID(payload["id_venta"])
        assert payload["valor_total"] == 25000
        assert payload["id_medio_pago"] == 1
        assert payload["caja"] == 1
        assert payload["tendero"] == 1
        assert "fecha_venta" in payload

        connection = connect(db_path)
        try:
            row = connection.execute(
                "SELECT * FROM ventas WHERE id_venta = ?",
                (payload["id_venta"],),
            ).fetchone()
            assert row is not None
            assert row["valor_total"] == 25000
            lines = connection.execute(
                "SELECT * FROM venta_lineas WHERE id_venta = ?",
                (payload["id_venta"],),
            ).fetchall()
            assert len(lines) == 1
            assert lines[0]["nombre_producto"] == "Pan"
            assert lines[0]["subtotal"] == 25000
        finally:
            connection.close()


def test_create_sale_rejects_legacy_valor_total_only(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        response = client.post(
            "/ventas",
            json={"valor_total": 25000, "id_medio_pago": 1},
        )
        assert response.status_code == 400
        assert "lineas" in response.json()["detail"].lower()
        assert client.get("/medios-pago").status_code == 200


def test_create_sale_rejects_empty_lineas(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        response = client.post(
            "/ventas",
            json={"id_medio_pago": 1, "lineas": []},
        )
        assert response.status_code == 400


def test_create_sale_rejects_inactive_payment_method(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        product = _create_product(client, nombre="Pan", precio=1000)
        connection = connect(db_path)
        try:
            connection.execute(
                "INSERT INTO medios_pago (nombre, id_estado) VALUES (?, ?)",
                ("Inactivo", 0),
            )
            connection.commit()
            inactive_id = connection.execute(
                "SELECT id_medio_pago FROM medios_pago WHERE nombre = ?",
                ("Inactivo",),
            ).fetchone()[0]
        finally:
            connection.close()

        response = client.post(
            "/ventas",
            json={
                "id_medio_pago": inactive_id,
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

        connection = connect(db_path)
        try:
            count = connection.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
            assert count == 0
        finally:
            connection.close()


def test_create_sale_rejects_unknown_payment_method(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        product = _create_product(client, nombre="Pan", precio=1000)
        response = client.post(
            "/ventas",
            json={
                "id_medio_pago": 999,
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


def test_no_calculator_endpoint(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        response = client.post("/calculadora/evaluar", json={"expression": "5000"})
        assert response.status_code == 404
