from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from bakery.api.app import create_app
from bakery.desktop.client import ApiClient
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    ESTADO_INACTIVO,
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    SEED_CATEGORIAS,
)


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(tmp_path / "bakery.sqlite3"))


class _TestClientTransport(httpx.BaseTransport):
    """Sync bridge so ApiClient can talk to FastAPI TestClient."""

    def __init__(self, client: TestClient) -> None:
        self._client = client

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.url.query:
            path = f"{path}?{request.url.query}"
        response = self._client.request(
            request.method,
            path,
            content=request.content,
            headers={
                key: value
                for key, value in request.headers.items()
                if key.lower() != "host"
            },
        )
        return httpx.Response(
            status_code=response.status_code,
            headers=response.headers,
            content=response.content,
            request=request,
        )


def _create_sample(client: TestClient, **overrides) -> dict:
    body = {
        "nombre": "Pan de chocolate",
        "precio": 5000,
        "id_categoria": 1,
        "descripcion": "relleno",
    }
    body.update(overrides)
    response = client.post("/productos", json=body)
    assert response.status_code == 200, response.text
    return response.json()


def test_list_categories(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        response = client.get("/categorias")
        assert response.status_code == 200
        assert [item["nombre"] for item in response.json()] == list(SEED_CATEGORIAS) + [
            NOMBRE_CATEGORIA_PAN_PEQUENO
        ]


def test_create_edit_deactivate_and_listings(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        created = _create_sample(client)
        assert created["id_estado"] == ESTADO_ACTIVO
        assert created["precio"] == 5000

        updated = client.put(
            f"/productos/{created['id_producto']}",
            json={
                "nombre": "Pan integral",
                "precio": 2500,
                "id_categoria": 2,
                "descripcion": None,
            },
        )
        assert updated.status_code == 200
        assert updated.json()["nombre"] == "Pan integral"
        assert updated.json()["precio"] == 2500

        other = _create_sample(
            client, nombre="Torta", precio=2500, id_categoria=2, descripcion=None
        )
        _create_sample(client, nombre="Café", precio=4000, id_categoria=3)

        by_price = client.get("/productos/activos", params={"precio": 2500})
        assert by_price.status_code == 200
        assert [p["nombre"] for p in by_price.json()] == ["Pan integral", "Torta"]

        by_cat = client.get("/productos/activos", params={"id_categoria": 2})
        assert [p["nombre"] for p in by_cat.json()] == ["Pan integral", "Torta"]

        deactivated = client.post(f"/productos/{created['id_producto']}/desactivar")
        assert deactivated.status_code == 200
        assert deactivated.json()["id_estado"] == ESTADO_INACTIVO

        active = client.get("/productos/activos").json()
        assert "Pan integral" not in [p["nombre"] for p in active]
        assert "Torta" in [p["nombre"] for p in active]

        by_price_after = client.get("/productos/activos", params={"precio": 2500}).json()
        assert [p["nombre"] for p in by_price_after] == ["Torta"]

        all_products = client.get("/productos").json()
        assert len(all_products) == 3
        assert any(p["nombre"] == "Pan integral" and p["id_estado"] == ESTADO_INACTIVO for p in all_products)

        activated = client.post(f"/productos/{created['id_producto']}/activar")
        assert activated.json()["id_estado"] == ESTADO_ACTIVO


def test_create_rejects_invalid_price_and_category(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        zero = client.post(
            "/productos",
            json={"nombre": "Pan", "precio": 0, "id_categoria": 1},
        )
        assert zero.status_code == 400
        assert "precio" in zero.json()["detail"].lower()

        bad_cat = client.post(
            "/productos",
            json={"nombre": "Pan", "precio": 1000, "id_categoria": 999},
        )
        assert bad_cat.status_code == 400
        assert "categoría" in bad_cat.json()["detail"].lower()


def test_medios_pago_and_ventas_with_lines(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        methods = client.get("/medios-pago")
        assert methods.status_code == 200
        assert methods.json()[0]["nombre"] == "Efectivo"

        product = _create_sample(client, nombre="Pan", precio=12000, descripcion=None)
        sale = client.post(
            "/ventas",
            json={
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 12000,
                    }
                ],
            },
        )
        assert sale.status_code == 200
        assert sale.json()["valor_total"] == 12000
        assert sale.json()["caja"] == 1


def test_api_client_product_methods(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as test_client:
        api = ApiClient(
            base_url="http://test",
            transport=_TestClientTransport(test_client),
        )
        try:
            categories = api.list_categories()
            assert [c["nombre"] for c in categories] == list(SEED_CATEGORIAS) + [
                NOMBRE_CATEGORIA_PAN_PEQUENO
            ]

            product = api.create_product(
                nombre="Galleta",
                precio=1500,
                id_categoria=4,
                descripcion="dulce",
            )
            assert product["nombre"] == "Galleta"

            fetched = api.get_product(product["id_producto"])
            assert fetched["precio"] == 1500

            updated = api.update_product(
                product["id_producto"],
                nombre="Galleta mantequilla",
                precio=1800,
                id_categoria=4,
            )
            assert updated["precio"] == 1800

            api.create_product(nombre="Otra", precio=1800, id_categoria=4)
            matches = api.list_active_products(precio=1800)
            assert len(matches) == 2

            api.deactivate_product(product["id_producto"])
            active = api.list_active_products(id_categoria=4)
            assert [p["nombre"] for p in active] == ["Otra"]
            assert len(api.list_products()) == 2
        finally:
            api.close()
