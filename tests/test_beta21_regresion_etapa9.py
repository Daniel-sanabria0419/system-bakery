"""Beta 2.1 Etapa 9: regresión 2.0.x + bordes (legado, ventana exacta, carrera POST)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from PySide6.QtWidgets import QPushButton

from bakery.api.app import create_app
from bakery.app.product_images import (
    ensure_imagenes_dirs,
    imagenes_categorias_dir,
    imagenes_productos_dir,
)
from bakery.app.products import create_product
from bakery.app.purchase import SaleDraft
from bakery.app.sales import register_sale
import bakery.app.sales as sales_module
from bakery.desktop.main import create_window
from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.repositories import (
    EDITABLE_WINDOW_SECONDS,
    get_categoria_by_nombre,
    get_promocion,
    insert_sale,
    list_venta_lineas,
    sale_is_editable,
)
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    NOMBRE_PROMOCION_PAN_PEQUENO,
)
from tests.test_stage4_desktop import FakeApiClient, _click, _find


def _db(tmp_path: Path):
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    return connect(path)


def _create_product_api(
    client: TestClient, *, nombre: str, precio: int, id_categoria: int = 1
) -> dict:
    response = client.post(
        "/productos",
        json={"nombre": nombre, "precio": precio, "id_categoria": id_categoria},
    )
    assert response.status_code == 200, response.text
    return response.json()


# --- Ventana exacta: editable solo si elapsed < 3600 s ---


def test_editable_boundary_strictly_less_than_one_hour() -> None:
    fecha = "2026-10-30T12:00:00"
    fecha_dt = datetime.fromisoformat(fecha)
    assert sale_is_editable(
        fecha, now=fecha_dt + timedelta(seconds=EDITABLE_WINDOW_SECONDS - 1)
    )
    assert not sale_is_editable(
        fecha, now=fecha_dt + timedelta(seconds=EDITABLE_WINDOW_SECONDS)
    )
    assert EDITABLE_WINDOW_SECONDS == 3600


def test_update_sale_boundary_exact_3600_not_editable(tmp_path: Path) -> None:
    """editable si elapsed < 3600; en exactamente 3600 s → SaleNotEditableError."""
    from bakery.app.sales import SaleNotEditableError, update_sale

    connection = _db(tmp_path)
    try:
        product = create_product(
            connection, nombre="Pan", precio=5000, id_categoria=1
        )
        fecha = "2026-10-30T10:00:00"
        sale_id = str(uuid.uuid4())
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
            id_venta=sale_id,
            fecha_venta=fecha,
        )
        now_exact = datetime.fromisoformat(fecha) + timedelta(
            seconds=EDITABLE_WINDOW_SECONDS
        )
        try:
            update_sale(
                connection,
                sale_id,
                2,
                [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 2,
                        "precio_aplicado": 5000,
                    }
                ],
                now=now_exact,
            )
            raise AssertionError("expected SaleNotEditableError at elapsed==3600")
        except SaleNotEditableError:
            pass

        now_inside = datetime.fromisoformat(fecha) + timedelta(
            seconds=EDITABLE_WINDOW_SECONDS - 1
        )
        updated = update_sale(
            connection,
            sale_id,
            2,
            [
                {
                    "id_producto": product["id_producto"],
                    "cantidad": 2,
                    "precio_aplicado": 5000,
                }
            ],
            now=now_inside,
        )
        assert updated["valor_total"] == 10000
        assert updated["id_medio_pago"] == 2
    finally:
        connection.close()


# --- Legado value-only ---


def test_legado_historial_detail_no_invented_lines(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        connection = connect(db_path)
        try:
            # Reciente: dentro de ventana para probar rechazo de líneas inventadas.
            insert_sale(
                connection,
                id_venta="legado-reg-1",
                valor_total=8500,
                fecha_venta=datetime.now()
                .replace(microsecond=0)
                .isoformat(timespec="seconds"),
                id_medio_pago=1,
            )
            # Viejo: fuera de ventana.
            insert_sale(
                connection,
                id_venta="legado-reg-old",
                valor_total=5000,
                fecha_venta="2026-09-15T09:30:00",
                id_medio_pago=1,
            )
            connection.commit()
        finally:
            connection.close()

        listed = client.get("/ventas").json()
        row = next(r for r in listed if r["id_venta"] == "legado-reg-1")
        assert row["es_legado"] is True
        assert row["cantidad_lineas"] == 0
        assert row["valor_total"] == 8500

        detail = client.get("/ventas/legado-reg-1").json()
        assert detail["es_legado"] is True
        assert detail["lineas"] == []
        assert detail["valor_total"] == 8500
        assert detail["editable"] is True

        # No inventar líneas en PUT (dentro de ventana).
        rejected = client.put(
            "/ventas/legado-reg-1",
            json={
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": 1,
                        "cantidad": 1,
                        "precio_aplicado": 8500,
                    }
                ],
            },
        )
        assert rejected.status_code == 400
        assert "legado" in rejected.json()["detail"].lower()

        # Medio solo permitido en legado editable.
        medio_ok = client.put(
            "/ventas/legado-reg-1",
            json={"id_medio_pago": 2, "lineas": []},
        )
        assert medio_ok.status_code == 200
        assert medio_ok.json()["id_medio_pago"] == 2
        assert client.get("/ventas/legado-reg-1").json()["lineas"] == []

        # Legado fuera de ventana → 409 aunque solo cambie medio.
        medio_old = client.put(
            "/ventas/legado-reg-old",
            json={"id_medio_pago": 2, "lineas": []},
        )
        assert medio_old.status_code == 409


# --- Carrera idempotente POST ---


def test_register_sale_integrity_race_returns_existing(tmp_path: Path) -> None:
    """Simula carrera: get_sale ve None, insert choca PK, se devuelve el ganador."""
    connection = _db(tmp_path)
    try:
        product = create_product(
            connection, nombre="Pan", precio=3000, id_categoria=1
        )
        sale_id = str(uuid.uuid4())
        lineas = [
            {
                "id_producto": product["id_producto"],
                "cantidad": 2,
                "precio_aplicado": 3000,
            }
        ]
        winner = register_sale(connection, 1, lineas, id_venta=sale_id)
        assert winner["valor_total"] == 6000

        calls = {"n": 0}
        real_get = sales_module.get_sale

        def get_sale_race(conn, id_v):
            calls["n"] += 1
            if calls["n"] == 1:
                return None
            return real_get(conn, id_v)

        with patch.object(sales_module, "get_sale", side_effect=get_sale_race):
            raced = register_sale(
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

        assert raced["id_venta"] == winner["id_venta"]
        assert raced["valor_total"] == 6000
        count = connection.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
        assert count == 1
        lines = connection.execute(
            "SELECT COUNT(*), SUM(cantidad) FROM venta_lineas WHERE id_venta = ?",
            (sale_id,),
        ).fetchone()
        assert lines[0] == 1
        assert lines[1] == 2
    finally:
        connection.close()


def test_post_ventas_retry_same_uuid_ignores_body(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product_api(client, nombre="Pan", precio=2500)
        sale_id = str(uuid.uuid4())
        body = {
            "id_venta": sale_id,
            "id_medio_pago": 1,
            "lineas": [
                {
                    "id_producto": pan["id_producto"],
                    "cantidad": 1,
                    "precio_aplicado": 2500,
                }
            ],
        }
        first = client.post("/ventas", json=body)
        assert first.status_code == 200
        retry = client.post(
            "/ventas",
            json={
                **body,
                "id_medio_pago": 2,
                "lineas": [
                    {
                        "id_producto": pan["id_producto"],
                        "cantidad": 50,
                        "precio_aplicado": 2500,
                    }
                ],
            },
        )
        assert retry.status_code == 200
        assert retry.json() == first.json()
        connection = connect(db_path)
        try:
            assert connection.execute("SELECT COUNT(*) FROM ventas").fetchone()[0] == 1
        finally:
            connection.close()


# --- Checklist cobro / catálogo / productos (#61–#66) ---


def test_line_subtotal_total_and_promo_snapshot_only_with_discount(
    tmp_path: Path,
) -> None:
    """#61 subtotal/total; #62 snapshot promo solo con descuento; promo por línea."""
    connection = _db(tmp_path)
    try:
        id_cat = get_categoria_by_nombre(
            connection, NOMBRE_CATEGORIA_PAN_PEQUENO
        )["id_categoria"]
        rollo = create_product(
            connection,
            nombre="Rollo",
            precio=300,
            id_categoria=id_cat,
        )
        promo_id = rollo["promocion_id"]
        assert promo_id is not None
        promo = get_promocion(connection, promo_id)
        assert promo is not None
        assert promo["nombre"] == NOMBRE_PROMOCION_PAN_PEQUENO

        sale7 = register_sale(
            connection,
            1,
            [
                {
                    "id_producto": rollo["id_producto"],
                    "cantidad": 7,
                    "precio_aplicado": 300,
                }
            ],
            id_venta=str(uuid.uuid4()),
        )
        assert sale7["valor_total"] == 2000
        line7 = list_venta_lineas(connection, sale7["id_venta"])[0]
        assert line7["subtotal"] == 2100
        assert line7["total"] == 2000
        assert line7["precio_aplicado"] == 300
        assert line7["id_promocion"] == promo_id
        assert line7["nombre_promocion"] == NOMBRE_PROMOCION_PAN_PEQUENO

        sale8 = register_sale(
            connection,
            1,
            [
                {
                    "id_producto": rollo["id_producto"],
                    "cantidad": 8,
                    "precio_aplicado": 300,
                }
            ],
            id_venta=str(uuid.uuid4()),
        )
        assert sale8["valor_total"] == 2400
        line8 = list_venta_lineas(connection, sale8["id_venta"])[0]
        assert line8["subtotal"] == 2400
        assert line8["total"] == 2400
        assert line8["id_promocion"] is None
        assert line8["nombre_promocion"] is None
    finally:
        connection.close()


def test_list_price_mismatch_rejected(tmp_path: Path) -> None:
    """#63: precio_aplicado debe coincidir con precio de lista vigente."""
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        pan = _create_product_api(client, nombre="Pan", precio=5000)
        response = client.post(
            "/ventas",
            json={
                "id_venta": str(uuid.uuid4()),
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": pan["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 4999,
                    }
                ],
            },
        )
        assert response.status_code == 400
        assert "precio" in response.json()["detail"].lower()


def test_cart_revalidate_price_change_updates_line() -> None:
    """#64: revalidación de carrito ante cambio de precio de catálogo."""
    draft = SaleDraft()
    product = {
        "id_producto": 10,
        "nombre": "Torta",
        "precio": 4500,
        "id_estado": ESTADO_ACTIVO,
        "nombre_categoria": "Pastelería",
    }
    assert draft.select_product(product)
    assert draft.set_quantity(2)
    assert draft.add_to_purchase()
    updated = {**product, "precio": 5000}
    result = draft.revalidate_against_catalog([updated])
    assert result.changed is True
    assert draft.purchase.items()[0].precio_aplicado == 5000


def test_initialize_ensures_imagenes_dirs(tmp_path: Path, monkeypatch) -> None:
    """#66: initialize llama ensure_imagenes_dirs (idempotente)."""
    root = tmp_path / "proj"
    root.mkdir()
    monkeypatch.setattr(
        "bakery.app.product_images.project_root", lambda: root
    )
    db_path = tmp_path / "bakery.sqlite3"
    initialize(db_path)
    assert imagenes_categorias_dir().is_dir()
    assert imagenes_productos_dir().is_dir()
    ensure_imagenes_dirs()  # idempotente
    assert imagenes_categorias_dir().is_dir()


def test_post_create_still_works_with_historial_menu(qtbot) -> None:
    """Menú: Registrar + Productos + Historial; cobro multi-línea intacto."""
    api = FakeApiClient(
        products=[
            {
                "id_producto": 1,
                "nombre": "Pan",
                "precio": 5000,
                "id_categoria": 1,
                "descripcion": None,
                "id_estado": ESTADO_ACTIVO,
            },
            {
                "id_producto": 2,
                "nombre": "Café",
                "precio": 3000,
                "id_categoria": 2,
                "descripcion": None,
                "id_estado": ESTADO_ACTIVO,
            },
        ]
    )
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    assert isinstance(_find(window, "menu_register_button"), QPushButton)
    assert isinstance(_find(window, "menu_products_button"), QPushButton)
    assert isinstance(_find(window, "menu_historial_button"), QPushButton)

    _click(qtbot, _find(window, "menu_historial_button"))
    assert window._stack.currentWidget() is window._historial
    _click(qtbot, _find(window, "historial_back_button"))

    _click(qtbot, _find(window, "menu_register_button"))
    assert window._stack.currentWidget() is window._register
