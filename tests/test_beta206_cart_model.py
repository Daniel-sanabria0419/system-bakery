"""Beta 2.0.6 Etapa 1: carrito qty-only, Subtotal/Descuento/Total, clear_cart, remove_line."""

from __future__ import annotations

import json

import pytest

from bakery.app import promotions as promotions_mod
from bakery.app.purchase import SaleDraft
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    PROMOCION_PAN_PEQUENO_CONFIG,
    TIPO_PROMOCION_CANTIDAD_POR_MONTO,
)

CANONICAL = PROMOCION_PAN_PEQUENO_CONFIG


@pytest.fixture(autouse=True)
def _flag_on(monkeypatch):
    monkeypatch.delenv("BAKERY_USE_PROMOCIONES_TABLE", raising=False)
    monkeypatch.setattr(promotions_mod, "USE_PROMOCIONES_TABLE", True)


def _pan(id_producto: int, nombre: str = "Pan") -> dict:
    return {
        "id_producto": id_producto,
        "nombre": nombre,
        "precio": 300,
        "promocion_id": 1,
        "promocion_tipo": TIPO_PROMOCION_CANTIDAD_POR_MONTO,
        "promocion_configuracion": json.dumps(CANONICAL),
        "promocion_activo": ESTADO_ACTIVO,
    }


def _plain(id_producto: int = 10, nombre: str = "Torta", precio: int = 4500) -> dict:
    return {
        "id_producto": id_producto,
        "nombre": nombre,
        "precio": precio,
        "nombre_categoria": "Pastelería",
    }


def _add(draft: SaleDraft, product: dict, quantity: int) -> None:
    assert draft.select_product(product) is True
    assert draft.set_quantity(quantity) is True
    assert draft.add_to_purchase() is True


def test_formula_7_panes_descuento_100() -> None:
    draft = SaleDraft()
    _add(draft, _pan(1), 7)
    assert draft.list_subtotal() == 2100
    assert draft.total() == 2000
    assert draft.discount() == 100


def test_formula_8_panes_descuento_0() -> None:
    draft = SaleDraft()
    _add(draft, _pan(1), 8)
    assert draft.list_subtotal() == 2400
    assert draft.total() == 2400
    assert draft.discount() == 0


def test_formula_4_plus_3_descuento_100() -> None:
    draft = SaleDraft()
    _add(draft, _pan(1, "A"), 4)
    _add(draft, _pan(2, "B"), 3)
    assert draft.list_subtotal() == 2100
    assert draft.total() == 1900
    assert draft.discount() == 200


def test_formula_7_plus_5_descuento_100() -> None:
    draft = SaleDraft()
    _add(draft, _pan(1, "A"), 7)
    _add(draft, _pan(2, "B"), 5)
    assert draft.list_subtotal() == 3600
    assert draft.total() == 3500
    assert draft.discount() == 100


def test_formula_sin_promo_descuento_0() -> None:
    draft = SaleDraft()
    _add(draft, _plain(), 2)
    assert draft.list_subtotal() == 9000
    assert draft.total() == 9000
    assert draft.discount() == 0


def test_remove_line_recalculates_hybrid() -> None:
    draft = SaleDraft()
    _add(draft, _pan(1, "A"), 4)
    _add(draft, _pan(2, "B"), 3)
    assert draft.total() == 1900
    assert draft.discount() == 200

    assert draft.remove_line(0) is True
    assert len(draft.purchase.items()) == 1
    assert draft.purchase.items()[0].id_producto == 2
    assert draft.list_subtotal() == 900
    assert draft.total() == 900
    assert draft.discount() == 0


def test_remove_line_rejects_bad_index() -> None:
    draft = SaleDraft()
    _add(draft, _plain(), 1)
    assert draft.remove_line(-1) is False
    assert draft.remove_line(1) is False
    assert draft.remove_line(True) is False  # type: ignore[arg-type]
    assert len(draft.purchase.items()) == 1


def test_clear_cart_preserves_selection_and_quantity() -> None:
    draft = SaleDraft()
    _add(draft, _pan(1), 7)
    assert draft.select_product(_pan(2, "Otro")) is True
    assert draft.set_quantity(5) is True

    draft.clear_cart()
    assert draft.purchase.items() == []
    assert draft.total() == 0
    assert draft.list_subtotal() == 0
    assert draft.discount() == 0
    selected = draft.selected_product()
    assert selected is not None
    assert selected["id_producto"] == 2
    assert draft.quantity() == 5


def test_clear_purchase_resets_selection() -> None:
    draft = SaleDraft()
    _add(draft, _pan(1), 7)
    assert draft.select_product(_pan(2)) is True
    draft.set_quantity(3)
    draft.clear_purchase()
    assert draft.purchase.items() == []
    assert draft.selected_product() is None
    assert draft.quantity() == 1


def test_no_tipado_apis_on_draft() -> None:
    from bakery.app.purchase import PurchaseLine

    draft = SaleDraft()
    assert not hasattr(draft, "entry")
    assert not hasattr(draft, "apply_value")
    assert not hasattr(draft, "pad_display_amount")
    assert "cobro_fijo" not in PurchaseLine.__dataclass_fields__
