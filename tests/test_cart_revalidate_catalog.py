"""Etapa 4: revalidar carrito contra catálogo vigente (precio / inactivo)."""

from __future__ import annotations

import json

from bakery.app.purchase import SaleDraft
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    PROMOCION_PAN_PEQUENO_CONFIG,
    TIPO_PROMOCION_CANTIDAD_POR_MONTO,
)

CANONICAL = PROMOCION_PAN_PEQUENO_CONFIG


def _pan(id_producto: int = 1, nombre: str = "Pan rollo", precio: int = 300) -> dict:
    return {
        "id_producto": id_producto,
        "nombre": nombre,
        "precio": precio,
        "id_estado": ESTADO_ACTIVO,
        "promocion_id": 1,
        "promocion_tipo": TIPO_PROMOCION_CANTIDAD_POR_MONTO,
        "promocion_configuracion": json.dumps(CANONICAL),
        "promocion_activo": ESTADO_ACTIVO,
    }


def _plain(
    id_producto: int = 10,
    nombre: str = "Torta",
    precio: int = 4500,
) -> dict:
    return {
        "id_producto": id_producto,
        "nombre": nombre,
        "precio": precio,
        "id_estado": ESTADO_ACTIVO,
        "nombre_categoria": "Pastelería",
    }


def _add(draft: SaleDraft, product: dict, quantity: int) -> None:
    assert draft.select_product(product) is True
    assert draft.set_quantity(quantity) is True
    assert draft.add_to_purchase() is True


def test_revalidate_same_price_keeps_line() -> None:
    draft = SaleDraft()
    _add(draft, _plain(), 2)
    result = draft.revalidate_against_catalog([_plain()])
    assert result.changed is False
    assert result.price_changed == []
    assert result.removed == []
    assert len(draft.purchase.items()) == 1
    assert draft.purchase.items()[0].precio_aplicado == 4500
    assert draft.total() == 9000


def test_revalidate_price_change_updates_line_and_total() -> None:
    draft = SaleDraft()
    _add(draft, _plain(precio=4500), 2)
    assert draft.total() == 9000

    updated = _plain(precio=5000)
    result = draft.revalidate_against_catalog([updated])
    assert result.price_changed == ["Torta"]
    assert result.removed == []
    line = draft.purchase.items()[0]
    assert line.precio_aplicado == 5000
    assert line.cantidad == 2
    assert draft.list_subtotal() == 10000
    assert draft.total() == 10000


def test_revalidate_inactive_or_missing_removes_line() -> None:
    draft = SaleDraft()
    _add(draft, _plain(id_producto=10, nombre="Torta"), 1)
    _add(draft, _plain(id_producto=11, nombre="Café", precio=3000), 1)
    assert len(draft.purchase.items()) == 2

    # Solo Café sigue activo en catálogo.
    result = draft.revalidate_against_catalog(
        [_plain(id_producto=11, nombre="Café", precio=3000)]
    )
    assert result.removed == ["Torta"]
    assert result.price_changed == []
    assert len(draft.purchase.items()) == 1
    assert draft.purchase.items()[0].nombre == "Café"
    assert draft.total() == 3000


def test_revalidate_skips_inactive_estado_in_payload() -> None:
    draft = SaleDraft()
    _add(draft, _plain(id_producto=10, nombre="Torta"), 1)
    inactive = _plain(id_producto=10, nombre="Torta", precio=4500)
    inactive["id_estado"] = 0
    result = draft.revalidate_against_catalog([inactive])
    assert result.removed == ["Torta"]
    assert draft.purchase.items() == []
    assert draft.total() == 0


def test_revalidate_price_and_remove_together() -> None:
    draft = SaleDraft()
    _add(draft, _plain(id_producto=10, nombre="Torta", precio=4500), 1)
    _add(draft, _plain(id_producto=11, nombre="Café", precio=3000), 2)
    result = draft.revalidate_against_catalog(
        [_plain(id_producto=10, nombre="Torta", precio=5000)]
    )
    assert result.price_changed == ["Torta"]
    assert result.removed == ["Café"]
    assert len(draft.purchase.items()) == 1
    assert draft.total() == 5000


def test_revalidate_promo_line_same_price_keeps_promo_total() -> None:
    draft = SaleDraft()
    _add(draft, _pan(), 7)
    assert draft.total() == 2000
    result = draft.revalidate_against_catalog([_pan()])
    assert result.changed is False
    assert draft.purchase.items()[0].precio_aplicado == 300
    assert draft.list_subtotal() == 2100
    assert draft.total() == 2000


def test_revalidate_does_not_clear_selection() -> None:
    draft = SaleDraft()
    _add(draft, _plain(id_producto=10), 1)
    assert draft.select_product(_plain(id_producto=11, nombre="Café", precio=3000))
    draft.set_quantity(4)
    draft.revalidate_against_catalog([])
    assert draft.purchase.items() == []
    selected = draft.selected_product()
    assert selected is not None
    assert selected["id_producto"] == 11
    assert draft.quantity() == 4
