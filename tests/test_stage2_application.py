from pathlib import Path

import pytest

from bakery.app.calculator import Calculator
from bakery.app.money import format_cop
from bakery.app.sales import SaleValidationError, register_sale
from bakery.persistence import initialize
from bakery.persistence.connection import connect


def _enter(calculator: Calculator, expression: str) -> None:
    for character in expression:
        if character == " ":
            continue
        if character == "+":
            calculator.press_add()
        elif character == "-":
            calculator.press_subtract()
        elif character.isdigit():
            calculator.press_digit(character)


def test_valid_expressions() -> None:
    cases = {
        "5000": 5000,
        "5000 + 2000": 7000,
        "5000 + 2000 - 1000": 6000,
    }
    for expression, expected in cases.items():
        calculator = Calculator()
        _enter(calculator, expression)
        assert calculator.expression() == expression
        assert calculator.value() == expected


def test_incomplete_operations_have_no_value() -> None:
    for expression in ("5000 +", "5000 -", "5000 + 2000 -"):
        calculator = Calculator()
        _enter(calculator, expression)
        assert calculator.value() is None


def test_negative_result_has_no_value() -> None:
    calculator = Calculator()
    _enter(calculator, "5000 - 6000")
    assert calculator.value() is None


def test_zero_result_has_no_value() -> None:
    calculator = Calculator()
    _enter(calculator, "5000 - 5000")
    assert calculator.value() is None


def test_empty_calculator_has_no_value() -> None:
    assert Calculator().value() is None


def test_consecutive_operators_are_ignored() -> None:
    calculator = Calculator()
    _enter(calculator, "5000")
    calculator.press_add()
    calculator.press_add()
    calculator.press_subtract()
    assert calculator.expression() == "5000 +"
    assert calculator.value() is None


def test_operator_at_start_is_ignored() -> None:
    calculator = Calculator()
    calculator.press_subtract()
    calculator.press_add()
    assert calculator.expression() == ""


def test_clear_resets_expression() -> None:
    calculator = Calculator()
    _enter(calculator, "5000 + 2000")
    calculator.clear()
    assert calculator.expression() == ""
    assert calculator.value() is None


def test_backspace_deletes_last_digit() -> None:
    calculator = Calculator()
    _enter(calculator, "5000")
    calculator.backspace()
    assert calculator.expression() == "500"
    assert calculator.value() == 500


def test_backspace_does_not_delete_operator() -> None:
    calculator = Calculator()
    _enter(calculator, "5000 +")
    calculator.backspace()
    assert calculator.expression() == "5000 +"


def test_leading_zero_is_replaced() -> None:
    calculator = Calculator()
    calculator.press_digit("0")
    calculator.press_digit("0")
    calculator.press_digit("5")
    assert calculator.expression() == "5"
    assert calculator.value() == 5


def test_non_digit_is_ignored() -> None:
    calculator = Calculator()
    calculator.press_digit(".")
    calculator.press_digit("/")
    assert calculator.expression() == ""


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
