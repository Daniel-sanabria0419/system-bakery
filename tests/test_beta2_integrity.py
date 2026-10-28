"""Integridad histórica y validaciones Beta 2 (scope §13 / Etapa 8)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bakery.api.app import create_app
from bakery.app.products import (
    create_product,
    deactivate_product,
    find_active_products_by_price,
    list_active_products,
    update_product,
)
from bakery.app.purchase import Purchase, PurchaseLine, candidates_by_exact_price
from bakery.app.sales import SaleValidationError, register_sale
from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.repositories import get_producto, list_venta_lineas
from bakery.persistence.schema import ESTADO_INACTIVO


def _db(tmp_path: Path):
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    return connect(path)


def _api(tmp_path: Path) -> TestClient:
    return TestClient(create_app(tmp_path / "bakery.sqlite3"))


def test_deactivate_after_sale_keeps_snapshot_and_hides_from_new_sales(
    tmp_path: Path,
) -> None:
    connection = _db(tmp_path)
    try:
        product = create_product(
            connection,
            nombre="Pan de chocolate",
            precio=5000,
            id_categoria=1,
        )
        sale = register_sale(
            connection,
            1,
            [
                {
                    "id_producto": product["id_producto"],
                    "cantidad": 2,
                    "precio_aplicado": 5000,
                }
            ],
        )
        deactivate_product(connection, product["id_producto"])

        stored = get_producto(connection, product["id_producto"])
        assert stored is not None
        assert stored["id_estado"] == ESTADO_INACTIVO

        lines = list_venta_lineas(connection, sale["id_venta"])
        assert len(lines) == 1
        assert lines[0]["nombre_producto"] == "Pan de chocolate"
        assert lines[0]["precio_aplicado"] == 5000
        assert lines[0]["subtotal"] == 10000

        assert list_active_products(connection) == []
        assert find_active_products_by_price(connection, 5000) == []

        with pytest.raises(SaleValidationError, match="activo"):
            register_sale(
                connection,
                1,
                [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 5000,
                    }
                ],
            )
    finally:
        connection.close()


def test_rename_and_reprice_do_not_change_historical_lines(tmp_path: Path) -> None:
    connection = _db(tmp_path)
    try:
        product = create_product(
            connection, nombre="Pan", precio=5000, id_categoria=1
        )
        sale = register_sale(
            connection,
            1,
            [
                {
                    "id_producto": product["id_producto"],
                    "cantidad": 1,
                    "precio_aplicado": 5000,
                }
            ],
        )
        update_product(
            connection,
            product["id_producto"],
            nombre="Pan integral",
            precio=7000,
            id_categoria=1,
            descripcion="nuevo",
        )

        lines = list_venta_lineas(connection, sale["id_venta"])
        assert lines[0]["nombre_producto"] == "Pan"
        assert lines[0]["precio_aplicado"] == 5000
        assert lines[0]["subtotal"] == 5000

        # Nueva venta usa precio actual.
        sale2 = register_sale(
            connection,
            1,
            [
                {
                    "id_producto": product["id_producto"],
                    "cantidad": 1,
                    "precio_aplicado": 7000,
                }
            ],
        )
        lines2 = list_venta_lineas(connection, sale2["id_venta"])
        assert lines2[0]["nombre_producto"] == "Pan integral"
        assert lines2[0]["precio_aplicado"] == 7000
    finally:
        connection.close()


def test_candidates_and_api_search_only_actives(tmp_path: Path) -> None:
    connection = _db(tmp_path)
    try:
        active = create_product(
            connection, nombre="Activo", precio=2500, id_categoria=1
        )
        inactive = create_product(
            connection, nombre="Inactivo", precio=2500, id_categoria=1
        )
        deactivate_product(connection, inactive["id_producto"])

        matches = candidates_by_exact_price(
            [
                get_producto(connection, active["id_producto"]),
                get_producto(connection, inactive["id_producto"]),
            ],
            2500,
        )
        assert [m["nombre"] for m in matches] == ["Activo"]
        assert find_active_products_by_price(connection, 2500) == [
            get_producto(connection, active["id_producto"])
        ]
    finally:
        connection.close()

    with _api(tmp_path) as client:
        # Misma DB: buscar por API solo activos.
        payload = client.get("/productos/activos", params={"precio": 2500}).json()
        assert [p["nombre"] for p in payload] == ["Activo"]


def test_subtotal_and_total_are_computed_not_client_editable(tmp_path: Path) -> None:
    purchase = Purchase()
    assert purchase.add(
        id_producto=1, nombre="Pan", precio_aplicado=5000, cantidad=3
    )
    line = purchase.items()[0]
    assert isinstance(line, PurchaseLine)
    assert line.subtotal == 15000
    assert purchase.total() == 15000
    with pytest.raises(Exception):
        line.subtotal = 1  # type: ignore[misc]  # frozen

    with _api(tmp_path) as client:
        product = client.post(
            "/productos",
            json={"nombre": "Pan", "precio": 5000, "id_categoria": 1},
        ).json()
        # El 400 lo provoca subtotal en la línea, no un valor_total extra.
        bad = client.post(
            "/ventas",
            json={
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 2,
                        "precio_aplicado": 5000,
                        "subtotal": 1,
                    }
                ],
            },
        )
        assert bad.status_code == 400
        assert "subtotal" in bad.json()["detail"]

        bad_total = client.post(
            "/ventas",
            json={
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 2,
                        "precio_aplicado": 5000,
                        "total": 1,
                    }
                ],
            },
        )
        assert bad_total.status_code == 400
        assert "total" in bad_total.json()["detail"]

        ok = client.post(
            "/ventas",
            json={
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 2,
                        "precio_aplicado": 5000,
                    }
                ],
            },
        )
        assert ok.status_code == 200
        assert ok.json()["valor_total"] == 10000


def test_used_product_is_not_hard_deleted(tmp_path: Path) -> None:
    import bakery.app.products as products_module
    import bakery.api.app as api_module

    assert not hasattr(products_module, "delete_product")
    assert not hasattr(api_module, "delete_product")

    with _api(tmp_path) as client:
        product = client.post(
            "/productos",
            json={"nombre": "Empanada", "precio": 2000, "id_categoria": 1},
        ).json()
        sale = client.post(
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
        assert sale.status_code == 200
        assert (
            client.delete(f"/productos/{product['id_producto']}").status_code == 405
        )
        assert (
            client.post(f"/productos/{product['id_producto']}/desactivar").status_code
            == 200
        )
        # Fila y líneas siguen existiendo.
        connection = connect(tmp_path / "bakery.sqlite3")
        try:
            row = get_producto(connection, product["id_producto"])
            assert row is not None
            assert row["id_estado"] == ESTADO_INACTIVO
            lines = list_venta_lineas(connection, sale.json()["id_venta"])
            assert lines[0]["nombre_producto"] == "Empanada"
        finally:
            connection.close()


def test_price_mismatch_rejected_after_reprice(tmp_path: Path) -> None:
    connection = _db(tmp_path)
    try:
        product = create_product(
            connection, nombre="Café", precio=3000, id_categoria=3
        )
        update_product(
            connection,
            product["id_producto"],
            nombre="Café",
            precio=3500,
            id_categoria=3,
        )
        with pytest.raises(SaleValidationError, match="precio"):
            register_sale(
                connection,
                1,
                [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 3000,
                    }
                ],
            )
    finally:
        connection.close()
