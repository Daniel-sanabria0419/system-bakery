"""Etapa 3: compra/register_sale con Pan pequeño + §21 otras categorías."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bakery.api.app import create_app
import json

from bakery.app.pan_pequeno_pricing import PRECIO_UNITARIO_PAN_PEQUENO
from bakery.app.products import ProductValidationError, create_product, update_product
from bakery.app.purchase import Purchase, SaleDraft
from bakery.app.sales import SaleValidationError, register_sale
from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.repositories import (
    get_categoria_by_nombre,
    list_venta_lineas,
    set_producto_promocion_id,
)
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    PROMOCION_PAN_PEQUENO_CONFIG,
    TIPO_PROMOCION_CANTIDAD_POR_MONTO,
    ensure_promocion_pan_pequeno,
)


def _db(tmp_path: Path):
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    return connect(path)


def _pan_pequeno_id(connection) -> int:
    categoria = get_categoria_by_nombre(connection, NOMBRE_CATEGORIA_PAN_PEQUENO)
    assert categoria is not None
    return int(categoria["id_categoria"])


def _pan_pequeno_product(
    *,
    id_producto: int = 1,
    nombre: str = "Pan rollo",
    precio: int = PRECIO_UNITARIO_PAN_PEQUENO,
) -> dict:
    return {
        "id_producto": id_producto,
        "nombre": nombre,
        "precio": precio,
        "nombre_categoria": NOMBRE_CATEGORIA_PAN_PEQUENO,
        "promocion_id": 1,
        "promocion_tipo": TIPO_PROMOCION_CANTIDAD_POR_MONTO,
        "promocion_configuracion": json.dumps(
            PROMOCION_PAN_PEQUENO_CONFIG, separators=(",", ":"), sort_keys=True
        ),
        "promocion_activo": ESTADO_ACTIVO,
    }


# --- Draft / Purchase ---


def test_purchase_accepts_explicit_promo_subtotal() -> None:
    purchase = Purchase()
    assert (
        purchase.add(
            id_producto=1,
            nombre="Pan rollo",
            precio_aplicado=300,
            cantidad=7,
            subtotal=2000,
        )
        is True
    )
    line = purchase.items()[0]
    assert line.precio_aplicado == 300
    assert line.cantidad == 7
    assert line.subtotal == 2000
    assert purchase.total() == 2000


def test_draft_pan_pequeno_promo_and_normal_qty() -> None:
    draft = SaleDraft()
    assert draft.select_product(_pan_pequeno_product()) is True
    assert draft.selected_is_pan_pequeno() is True
    draft.set_quantity(7)
    assert draft.current_subtotal() == 2000
    assert draft.add_to_purchase() is True
    line = draft.purchase.items()[0]
    assert line.subtotal == 2000
    assert line.precio_aplicado == 300  # precio de lista del catálogo
    assert line.cantidad == 7

    draft.select_product(_pan_pequeno_product(id_producto=2))
    draft.set_quantity(8)
    assert draft.current_subtotal() == 2400  # preview de la selección sola
    assert draft.add_to_purchase() is True
    # 7 y 8 por línea: 2000 + 2400
    assert draft.total() == 4400
    assert [item.subtotal for item in draft.purchase.items()] == [2000, 2400]


def test_draft_precio_aplicado_is_catalog_list_price() -> None:
    """Con promo coincidente, precio_aplicado es la lista del producto."""
    draft = SaleDraft()
    product = _pan_pequeno_product(precio=300)
    assert draft.select_product(product) is True
    draft.set_quantity(8)
    assert draft.add_to_purchase() is True
    line = draft.purchase.items()[0]
    assert line.precio_aplicado == product["precio"]
    assert line.precio_aplicado == 300
    assert line.subtotal == 2400
    assert draft.add_error() is None


def test_draft_rejects_promo_when_list_price_ne_precio_base() -> None:
    """Lista ≠ precio_base: no agrega y deja mensaje (sin sustituir en silencio)."""
    draft = SaleDraft()
    product = _pan_pequeno_product(precio=350)
    assert draft.select_product(product) is True
    draft.set_quantity(7)
    assert draft.add_to_purchase() is False
    assert draft.purchase.items() == []
    assert draft.selected_product() is not None
    error = draft.add_error()
    assert error is not None
    assert "precio de lista" in error.lower()
    assert "precio_base" in error


def test_draft_pan_pequeno_quantity_only_preview() -> None:
    """Beta 2.0.6: cobro solo por cantidad (−/+); sin tipado valor→qty."""
    draft = SaleDraft()
    draft.select_product(_pan_pequeno_product())
    draft.set_quantity(7)
    assert draft.current_subtotal() == 2000
    draft.set_quantity(17)
    assert draft.current_subtotal() == 5000
    draft.set_quantity(24)
    assert draft.current_subtotal() == 7000
    draft.set_quantity(27)
    assert draft.current_subtotal() == 8000
    draft.set_quantity(34)
    assert draft.current_subtotal() == 10000


def test_draft_agregar_qty_uses_promo_formula() -> None:
    """Agregar con qty: escala ceil (17→5000)."""
    draft = SaleDraft()
    draft.select_product(_pan_pequeno_product())
    draft.set_quantity(17)
    assert draft.add_to_purchase() is True
    line = draft.purchase.items()[0]
    assert line.cantidad == 17
    assert line.subtotal == 5000
    assert draft.total() == 5000

    draft.select_product(_pan_pequeno_product(id_producto=2))
    draft.set_quantity(34)
    assert draft.add_to_purchase() is True
    items = draft.purchase.items()
    assert items[1].cantidad == 34
    # Cada línea conserva su nudo: 17→5000 y 34→10000
    assert items[0].subtotal == 5000
    assert items[1].subtotal == 10000
    assert draft.total() == 15000


def test_draft_other_category_stays_precio_times_cantidad() -> None:
    draft = SaleDraft()
    assert (
        draft.select_product(
            {
                "id_producto": 1,
                "nombre": "Torta",
                "precio": 20000,
                "nombre_categoria": "Pastelería",
            }
        )
        is True
    )
    assert draft.selected_is_pan_pequeno() is False
    draft.set_quantity(3)
    assert draft.current_subtotal() == 60000
    assert draft.add_to_purchase() is True
    assert draft.purchase.items()[0].subtotal == 60000


def test_draft_current_subtotal_modes() -> None:
    draft = SaleDraft()
    assert draft.current_subtotal() is None

    draft.select_product(
        {
            "id_producto": 1,
            "nombre": "Torta",
            "precio": 3000,
            "nombre_categoria": "Pastelería",
        }
    )
    assert draft.current_subtotal() == 3000
    draft.set_quantity(2)
    assert draft.current_subtotal() == 6000

    draft.clear_product_selection()
    draft.set_quantity(1)
    draft.select_product(_pan_pequeno_product())
    assert draft.current_subtotal() == 300
    draft.set_quantity(7)
    assert draft.current_subtotal() == 2000


# --- §21 otras categorías (persistencia) ---


def test_torta_quantities_no_promo(tmp_path: Path) -> None:
    connection = _db(tmp_path)
    try:
        torta = create_product(
            connection, nombre="Torta", precio=20000, id_categoria=2
        )
        for cantidad, expected in ((1, 20000), (2, 40000), (3, 60000)):
            sale = register_sale(
                connection,
                1,
                [
                    {
                        "id_producto": torta["id_producto"],
                        "cantidad": cantidad,
                        "precio_aplicado": 20000,
                    }
                ],
            )
            assert sale["valor_total"] == expected
            lines = list_venta_lineas(connection, sale["id_venta"])
            assert lines[0]["subtotal"] == expected
            assert lines[0]["subtotal"] == lines[0]["precio_aplicado"] * cantidad
    finally:
        connection.close()


# --- register_sale Pan pequeño ---


def test_register_sale_rejects_promo_list_ne_precio_base(tmp_path: Path) -> None:
    """Producto con promo cantidad_por_monto y lista ≠ precio_base → POST 400."""
    connection = _db(tmp_path)
    try:
        # Pastelería a 500 + promo canónica (precio_base 300): desalineado a propósito.
        product = create_product(
            connection, nombre="Torta promo", precio=500, id_categoria=2
        )
        promo_id = ensure_promocion_pan_pequeno(connection)
        set_producto_promocion_id(connection, product["id_producto"], promo_id)
        connection.commit()
        with pytest.raises(SaleValidationError, match="precio_base"):
            register_sale(
                connection,
                1,
                [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 7,
                        "precio_aplicado": 500,
                    }
                ],
            )
    finally:
        connection.close()


def test_register_sale_pan_pequeno_promo_and_normal(tmp_path: Path) -> None:
    connection = _db(tmp_path)
    try:
        id_cat = _pan_pequeno_id(connection)
        rollo = create_product(
            connection,
            nombre="Pan rollo",
            precio=PRECIO_UNITARIO_PAN_PEQUENO,
            id_categoria=id_cat,
        )
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
        )
        assert sale7["valor_total"] == 2000
        lines7 = list_venta_lineas(connection, sale7["id_venta"])
        assert lines7[0]["precio_aplicado"] == 300
        assert lines7[0]["cantidad"] == 7
        assert lines7[0]["subtotal"] == 300 * 7
        assert lines7[0]["total"] == 2000

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
        )
        assert sale8["valor_total"] == 2400
        lines8 = list_venta_lineas(connection, sale8["id_venta"])
        assert lines8[0]["subtotal"] == 2400
        assert lines8[0]["total"] == 2400
        assert lines8[0]["id_promocion"] is None
        assert lines8[0]["nombre_promocion"] is None
    finally:
        connection.close()


def test_pan_pequeno_snapshot_stable_after_rename(tmp_path: Path) -> None:
    connection = _db(tmp_path)
    try:
        id_cat = _pan_pequeno_id(connection)
        product = create_product(
            connection,
            nombre="Pan rollo",
            precio=300,
            id_categoria=id_cat,
        )
        sale = register_sale(
            connection,
            1,
            [
                {
                    "id_producto": product["id_producto"],
                    "cantidad": 7,
                    "precio_aplicado": 300,
                }
            ],
        )
        update_product(
            connection,
            product["id_producto"],
            nombre="Pan rollo XXL",
            precio=300,
            id_categoria=id_cat,
        )
        lines = list_venta_lineas(connection, sale["id_venta"])
        assert lines[0]["nombre_producto"] == "Pan rollo"
        assert lines[0]["precio_aplicado"] == 300
        assert lines[0]["subtotal"] == 2100
        assert lines[0]["total"] == 2000
    finally:
        connection.close()


def test_create_pan_pequeno_requires_precio_300(tmp_path: Path) -> None:
    connection = _db(tmp_path)
    try:
        id_cat = _pan_pequeno_id(connection)
        with pytest.raises(ProductValidationError, match="300"):
            create_product(
                connection, nombre="Pan rollo", precio=250, id_categoria=id_cat
            )
        ok = create_product(
            connection, nombre="Pan rollo", precio=300, id_categoria=id_cat
        )
        assert ok["precio"] == 300
        with pytest.raises(ProductValidationError, match="300"):
            update_product(
                connection,
                ok["id_producto"],
                nombre="Pan rollo",
                precio=350,
                id_categoria=id_cat,
            )
    finally:
        connection.close()


def test_api_pan_pequeno_sale_and_reject_bad_price(tmp_path: Path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as client:
        categories = client.get("/categorias").json()
        pan_id = next(
            c["id_categoria"]
            for c in categories
            if c["nombre"] == NOMBRE_CATEGORIA_PAN_PEQUENO
        )
        bad = client.post(
            "/productos",
            json={"nombre": "Rollo", "precio": 400, "id_categoria": pan_id},
        )
        assert bad.status_code == 400
        assert "300" in bad.json()["detail"]

        created = client.post(
            "/productos",
            json={"nombre": "Rollo", "precio": 300, "id_categoria": pan_id},
        )
        assert created.status_code == 200
        product = created.json()

        sale = client.post(
            "/ventas",
            json={
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 7,
                        "precio_aplicado": 300,
                    }
                ],
            },
        )
        assert sale.status_code == 200
        assert sale.json()["valor_total"] == 2000

        # Cobro qty-only: 17 panes → escala ceil 5000.
        by_qty = client.post(
            "/ventas",
            json={
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 17,
                        "precio_aplicado": 300,
                    }
                ],
            },
        )
        assert by_qty.status_code == 200
        assert by_qty.json()["valor_total"] == 5000
