from pathlib import Path

import pytest

from bakery.app.calculator import Calculator
from bakery.app.money import format_cop
from bakery.app.products import create_product
from bakery.app.purchase import Purchase, SaleDraft, candidates_by_exact_price
from bakery.app.sales import SaleValidationError, register_sale
from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.repositories import list_venta_lineas


def _enter_digits(calculator: Calculator, digits: str) -> None:
    for character in digits:
        calculator.press_digit(character)


def _product(
    id_producto: int = 1,
    nombre: str = "Pan",
    precio: int = 5000,
    id_estado: int = 1,
) -> dict:
    return {
        "id_producto": id_producto,
        "nombre": nombre,
        "precio": precio,
        "id_estado": id_estado,
    }


def test_empty_entry_has_no_amount() -> None:
    assert Calculator().current_amount() is None
    assert Calculator().digits() == ""


def test_enter_single_amount() -> None:
    calculator = Calculator()
    _enter_digits(calculator, "5000")
    assert calculator.digits() == "5000"
    assert calculator.current_amount() == 5000


def test_leading_zero_is_replaced() -> None:
    calculator = Calculator()
    calculator.press_digit("0")
    calculator.press_digit("0")
    calculator.press_digit("5")
    assert calculator.digits() == "5"
    assert calculator.current_amount() == 5


def test_non_digit_is_ignored() -> None:
    calculator = Calculator()
    calculator.press_digit(".")
    calculator.press_digit("/")
    assert calculator.digits() == ""
    assert calculator.current_amount() is None


def test_backspace_deletes_last_digit() -> None:
    calculator = Calculator()
    _enter_digits(calculator, "5000")
    calculator.backspace()
    assert calculator.digits() == "500"
    assert calculator.current_amount() == 500


def test_backspace_until_empty() -> None:
    calculator = Calculator()
    _enter_digits(calculator, "12")
    calculator.backspace()
    calculator.backspace()
    assert calculator.digits() == ""
    assert calculator.current_amount() is None
    calculator.backspace()
    assert calculator.digits() == ""


def test_clear_entry_resets_digits() -> None:
    calculator = Calculator()
    _enter_digits(calculator, "5000")
    calculator.clear_entry()
    assert calculator.digits() == ""
    assert calculator.current_amount() is None


def test_press_zeros_appends_on_nonzero_entry() -> None:
    calculator = Calculator()
    calculator.press_digit("5")
    calculator.press_zeros()
    assert calculator.digits() == "500"
    assert calculator.current_amount() == 500


def test_press_zeros_on_empty_becomes_zero() -> None:
    calculator = Calculator()
    calculator.press_zeros()
    assert calculator.digits() == "0"
    assert calculator.current_amount() == 0


def test_press_zeros_on_single_zero_stays_zero() -> None:
    calculator = Calculator()
    calculator.press_digit("0")
    calculator.press_zeros()
    assert calculator.digits() == "0"
    assert calculator.current_amount() == 0


def test_display_text_empty_when_no_digits() -> None:
    assert Calculator().display_text() == "$ 0.00"


def test_display_text_formats_while_typing() -> None:
    calculator = Calculator()
    cases = [
        ("1", "$ 1"),
        ("10", "$ 10"),
        ("100", "$ 100"),
        ("1000", "$ 1.000"),
        ("10000", "$ 10.000"),
        ("12500", "$ 12.500"),
    ]
    for digits, expected in cases:
        calculator.clear_entry()
        _enter_digits(calculator, digits)
        assert calculator.display_text() == expected

    calculator.clear_entry()
    for digit, expected in [
        ("1", "$ 1"),
        ("2", "$ 12"),
        ("5", "$ 125"),
        ("0", "$ 1.250"),
        ("0", "$ 12.500"),
    ]:
        calculator.press_digit(digit)
        assert calculator.display_text() == expected


def test_display_text_updates_on_backspace() -> None:
    calculator = Calculator()
    _enter_digits(calculator, "12500")
    assert calculator.display_text() == "$ 12.500"
    expected_after_backspace = [
        "$ 1.250",
        "$ 125",
        "$ 12",
        "$ 1",
        "$ 0.00",
    ]
    for expected in expected_after_backspace:
        calculator.backspace()
        assert calculator.display_text() == expected


def test_display_text_zero_entry() -> None:
    calculator = Calculator()
    calculator.press_digit("0")
    assert calculator.display_text() == "$ 0"


def test_purchase_add_line_and_total() -> None:
    purchase = Purchase()
    assert (
        purchase.add(
            id_producto=1, nombre="Pan", precio_aplicado=5000, cantidad=1
        )
        is True
    )
    assert (
        purchase.add(
            id_producto=2, nombre="Café", precio_aplicado=3000, cantidad=2
        )
        is True
    )
    items = purchase.items()
    assert len(items) == 2
    assert items[0].subtotal == 5000
    assert items[1].subtotal == 6000
    assert items[1].cantidad == 2
    assert purchase.total() == 11000


def test_purchase_rejects_invalid_lines() -> None:
    purchase = Purchase()
    assert (
        purchase.add(
            id_producto=1, nombre="Pan", precio_aplicado=0, cantidad=1
        )
        is False
    )
    assert (
        purchase.add(
            id_producto=1, nombre="Pan", precio_aplicado=1000, cantidad=0
        )
        is False
    )
    assert (
        purchase.add(
            id_producto=1, nombre="  ", precio_aplicado=1000, cantidad=1
        )
        is False
    )
    assert purchase.items() == []
    assert purchase.total() == 0


def test_purchase_clear() -> None:
    purchase = Purchase()
    purchase.add(id_producto=1, nombre="Pan", precio_aplicado=5000, cantidad=1)
    purchase.add(id_producto=2, nombre="Café", precio_aplicado=3000, cantidad=1)
    purchase.clear()
    assert purchase.items() == []
    assert purchase.total() == 0


def test_add_to_purchase_requires_selected_product() -> None:
    draft = SaleDraft()
    _enter_digits(draft.entry, "5000")
    assert draft.add_to_purchase() is False
    assert draft.purchase.items() == []
    assert draft.entry.digits() == "5000"


def test_add_to_purchase_with_product_accumulates() -> None:
    draft = SaleDraft()
    assert draft.select_product(_product(1, "Pan", 5000)) is True
    assert draft.add_to_purchase() is True
    assert draft.entry.current_amount() is None
    assert draft.selected_product() is None
    items = draft.purchase.items()
    assert len(items) == 1
    assert items[0].nombre == "Pan"
    assert items[0].precio_aplicado == 5000
    assert items[0].cantidad == 1
    assert items[0].subtotal == 5000
    assert draft.total() == 5000

    assert draft.select_product(_product(2, "Café", 3000)) is True
    draft.set_quantity(2)
    assert draft.add_to_purchase() is True
    assert draft.quantity() == 1
    assert draft.total() == 11000
    assert [line.subtotal for line in draft.purchase.items()] == [5000, 6000]


def test_add_to_purchase_keeps_previous_items_without_product() -> None:
    draft = SaleDraft()
    draft.select_product(_product(1, "Pan", 5000))
    draft.add_to_purchase()
    _enter_digits(draft.entry, "3000")
    assert draft.add_to_purchase() is False
    assert len(draft.purchase.items()) == 1
    assert draft.total() == 5000
    assert draft.entry.digits() == "3000"


def test_clear_purchase_resets_entry_selection_and_items() -> None:
    draft = SaleDraft()
    draft.select_product(_product(1, "Pan", 5000))
    draft.add_to_purchase()
    draft.select_product(_product(2, "Café", 3000))
    draft.set_quantity(3)
    _enter_digits(draft.entry, "3000")
    draft.clear_purchase()
    assert draft.entry.digits() == ""
    assert draft.selected_product() is None
    assert draft.quantity() == 1
    assert draft.purchase.items() == []
    assert draft.total() == 0


def test_candidates_by_exact_price_filters_active() -> None:
    products = [
        _product(1, "Pan A", 2500, id_estado=1),
        _product(2, "Pan B", 2500, id_estado=1),
        _product(3, "Pan viejo", 2500, id_estado=0),
        _product(4, "Café", 4000, id_estado=1),
    ]
    matches = candidates_by_exact_price(products, 2500)
    assert [item["nombre"] for item in matches] == ["Pan A", "Pan B"]
    assert candidates_by_exact_price(products, 0) == []
    assert candidates_by_exact_price(products, 9999) == []


def test_format_cop() -> None:
    assert format_cop(5000) == "$ 5.000"
    assert format_cop(25000) == "$ 25.000"
    assert format_cop(1250000) == "$ 1.250.000"


def test_format_cop_rejects_non_integers() -> None:
    with pytest.raises(TypeError):
        format_cop(25.5)  # type: ignore[arg-type]


def _connection(tmp_path: Path):
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    return connect(path)


def test_register_sale_persists_uuid_lines_and_defaults(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    try:
        product = create_product(
            connection, nombre="Pan", precio=25000, id_categoria=1
        )
        sale = register_sale(
            connection,
            1,
            [
                {
                    "id_producto": product["id_producto"],
                    "cantidad": 1,
                    "precio_aplicado": 25000,
                }
            ],
            fecha_venta="2026-10-15T11:00:00",
        )
        row = connection.execute("SELECT * FROM ventas").fetchone()
        assert row["id_venta"] == sale["id_venta"]
        assert len(sale["id_venta"]) == 36
        assert row["valor_total"] == 25000
        assert row["fecha_venta"] == "2026-10-15T11:00:00"
        assert row["id_medio_pago"] == 1
        assert row["caja"] == 1
        assert row["tendero"] == 1
        lines = list_venta_lineas(connection, sale["id_venta"])
        assert len(lines) == 1
        assert lines[0]["nombre_producto"] == "Pan"
        assert lines[0]["subtotal"] == 25000
    finally:
        connection.close()


def test_register_sale_rejects_empty_or_invalid_lines(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    try:
        with pytest.raises(SaleValidationError):
            register_sale(connection, 1, [])
        with pytest.raises(SaleValidationError):
            register_sale(connection, 1, "x")  # type: ignore[arg-type]
        count = connection.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
        assert count == 0
    finally:
        connection.close()


def test_register_sale_rejects_inactive_or_unknown_payment_method(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    try:
        product = create_product(
            connection, nombre="Pan", precio=1000, id_categoria=1
        )
        line = {
            "id_producto": product["id_producto"],
            "cantidad": 1,
            "precio_aplicado": 1000,
        }
        connection.execute(
            "INSERT INTO medios_pago (nombre, id_estado) VALUES (?, ?)",
            ("Inactivo", 0),
        )
        connection.commit()
        inactive_id = connection.execute(
            "SELECT id_medio_pago FROM medios_pago WHERE nombre = ?",
            ("Inactivo",),
        ).fetchone()[0]
        with pytest.raises(SaleValidationError):
            register_sale(connection, inactive_id, [line])
        with pytest.raises(SaleValidationError):
            register_sale(connection, 999, [line])
        count = connection.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
        assert count == 0
    finally:
        connection.close()
