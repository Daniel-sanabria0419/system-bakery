from pathlib import Path

from fastapi.testclient import TestClient

from bakery.api.app import create_app
from bakery.persistence.connection import connect


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(tmp_path / "bakery.sqlite3"))


def _create_product(
    client: TestClient, *, nombre: str, precio: int, id_categoria: int = 1
) -> dict:
    response = client.post(
        "/productos",
        json={"nombre": nombre, "precio": precio, "id_categoria": id_categoria},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_multi_line_sale_total_and_snapshots(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product(client, nombre="Pan", precio=5000)
        cafe = _create_product(client, nombre="Café", precio=3000)
        response = client.post(
            "/ventas",
            json={
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
        assert response.status_code == 200
        assert response.json()["valor_total"] == 13000

        connection = connect(db_path)
        try:
            lines = connection.execute(
                """
                SELECT nombre_producto, precio_aplicado, cantidad, subtotal
                FROM venta_lineas
                WHERE id_venta = ?
                ORDER BY id_linea
                """,
                (response.json()["id_venta"],),
            ).fetchall()
            assert len(lines) == 2
            assert lines[0]["nombre_producto"] == "Pan"
            assert lines[0]["subtotal"] == 10000
            assert lines[1]["nombre_producto"] == "Café"
            assert lines[1]["subtotal"] == 3000
        finally:
            connection.close()

        # Renombrar/cambiar precio no altera el snapshot.
        assert (
            client.put(
                f"/productos/{pan['id_producto']}",
                json={
                    "nombre": "Pan nuevo",
                    "precio": 9999,
                    "id_categoria": 1,
                },
            ).status_code
            == 200
        )
        connection = connect(db_path)
        try:
            snap = connection.execute(
                """
                SELECT nombre_producto, precio_aplicado
                FROM venta_lineas
                WHERE id_venta = ?
                ORDER BY id_linea
                LIMIT 1
                """,
                (response.json()["id_venta"],),
            ).fetchone()
            assert snap["nombre_producto"] == "Pan"
            assert snap["precio_aplicado"] == 5000
        finally:
            connection.close()


def test_rejects_inactive_product(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        product = _create_product(client, nombre="Viejo", precio=2000)
        assert (
            client.post(f"/productos/{product['id_producto']}/desactivar").status_code
            == 200
        )
        response = client.post(
            "/ventas",
            json={
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 2000,
                    }
                ],
            },
        )
        assert response.status_code == 400
        assert "activo" in response.json()["detail"].lower()


def test_rejects_price_mismatch(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        product = _create_product(client, nombre="Pan", precio=5000)
        response = client.post(
            "/ventas",
            json={
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 4000,
                    }
                ],
            },
        )
        assert response.status_code == 400
        assert "precio" in response.json()["detail"].lower()


def test_legacy_sale_without_lines_remains_readable(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        connection = connect(db_path)
        try:
            connection.execute(
                """
                INSERT INTO ventas (
                    id_venta, valor_total, fecha_venta, id_medio_pago, caja, tendero
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                    15000,
                    "2026-10-01T10:00:00",
                    1,
                    1,
                    1,
                ),
            )
            connection.commit()
            row = connection.execute(
                "SELECT valor_total FROM ventas WHERE id_venta = ?",
                ("cccccccc-cccc-4ccc-8ccc-cccccccccccc",),
            ).fetchone()
            assert row["valor_total"] == 15000
            line_count = connection.execute(
                "SELECT COUNT(*) FROM venta_lineas WHERE id_venta = ?",
                ("cccccccc-cccc-4ccc-8ccc-cccccccccccc",),
            ).fetchone()[0]
            assert line_count == 0
        finally:
            connection.close()

        # Nueva venta con líneas no afecta la antigua.
        product = _create_product(client, nombre="Pan", precio=1000)
        assert (
            client.post(
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
            ).status_code
            == 200
        )
