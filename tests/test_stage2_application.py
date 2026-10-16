from pathlib import Path

import pytest

from bakery.app.calculator import Calculator
from bakery.app.money import format_cop
from bakery.app.purchase import Purchase, SaleDraft
from bakery.app.sales import SaleValidationError, register_sale
from bakery.persistence import initialize
from bakery.persistence.connection import connect


def _enter_digits(calculator: Calculator, digits: str) -> None:
    for character in digits:
        calculator.press_digit(character)


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


def test_display_text_empty_when_no_digits() -> None:
    assert Calculator().display_text() == ""


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
        "",
    ]
    for expected in expected_after_backspace:
        calculator.backspace()
        assert calculator.display_text() == expected


def test_display_text_zero_entry() -> None:
    calculator = Calculator()
    calculator.press_digit("0")
    assert calculator.display_text() == "$ 0"


def test_purchase_add_and_total() -> None:
    purchase = Purchase()
    assert purchase.add(5000) is True
    assert purchase.add(3000) is True
    assert purchase.items() == [5000, 3000]
    assert purchase.total() == 8000


def test_purchase_rejects_invalid_amounts() -> None:
    purchase = Purchase()
    for amount in (0, -1000, True, 25.0):
        assert purchase.add(amount) is False  # type: ignore[arg-type]
    assert purchase.items() == []
    assert purchase.total() == 0


def test_purchase_clear() -> None:
    purchase = Purchase()
    purchase.add(5000)
    purchase.add(3000)
    purchase.clear()
    assert purchase.items() == []
    assert purchase.total() == 0


def test_add_to_purchase_accumulates_and_clears_entry() -> None:
    draft = SaleDraft()
    _enter_digits(draft.entry, "5000")
    assert draft.add_to_purchase() is True
    assert draft.entry.current_amount() is None
    assert draft.purchase.items() == [5000]
    assert draft.total() == 5000

    _enter_digits(draft.entry, "3000")
    assert draft.add_to_purchase() is True
    assert draft.entry.digits() == ""
    assert draft.purchase.items() == [5000, 3000]
    assert draft.total() == 8000


def test_add_to_purchase_invalid_is_noop() -> None:
    draft = SaleDraft()
    assert draft.add_to_purchase() is False
    assert draft.purchase.items() == []
    assert draft.total() == 0

    draft.entry.press_digit("0")
    assert draft.add_to_purchase() is False
    assert draft.entry.digits() == "0"
    assert draft.purchase.items() == []


def test_add_to_purchase_keeps_previous_items_on_invalid() -> None:
    draft = SaleDraft()
    _enter_digits(draft.entry, "5000")
    draft.add_to_purchase()
    assert draft.add_to_purchase() is False
    assert draft.purchase.items() == [5000]
    assert draft.total() == 5000


def test_clear_purchase_resets_entry_and_items() -> None:
    draft = SaleDraft()
    _enter_digits(draft.entry, "5000")
    draft.add_to_purchase()
    _enter_digits(draft.entry, "3000")
    draft.clear_purchase()
    assert draft.entry.digits() == ""
    assert draft.purchase.items() == []
    assert draft.total() == 0


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


def test_register_sale_persists_uuid_and_defaults(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    try:
        sale = register_sale(
            connection,
            25000,
            1,
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
    finally:
        connection.close()


def test_register_sale_rejects_invalid_values(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
    try:
        for value in (0, -1000, True, 25.0):
            with pytest.raises(SaleValidationError):
                register_sale(connection, value, 1)  # type: ignore[arg-type]
        count = connection.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
        assert count == 0
    finally:
        connection.close()


def test_register_sale_rejects_inactive_or_unknown_payment_method(tmp_path: Path) -> None:
    connection = _connection(tmp_path)
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
        with pytest.raises(SaleValidationError):
            register_sale(connection, 1000, inactive_id)
        with pytest.raises(SaleValidationError):
            register_sale(connection, 1000, 999)
        count = connection.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
        assert count == 0
    finally:
        connection.close()
