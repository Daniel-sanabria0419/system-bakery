from typing import Any, List, Mapping

import httpx
from fastapi.testclient import TestClient
from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from bakery.api.app import create_app
from bakery.desktop.main import create_window
from bakery.desktop.ui import ConfirmSaleDialog, SaleSavedDialog
from bakery.persistence.connection import connect


class FakeApiClient:
    def __init__(self, methods: List[Mapping[str, Any]] = None) -> None:
        self.request_count = 0
        self.sales: List[Mapping[str, Any]] = []
        self.methods = methods or [
            {"id_medio_pago": 1, "nombre": "Efectivo", "id_estado": 1},
            {"id_medio_pago": 2, "nombre": "Nequi", "id_estado": 1},
        ]

    def list_payment_methods(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        return list(self.methods)

    def create_sale(self, valor_total: int, id_medio_pago: int) -> Mapping[str, Any]:
        self.request_count += 1
        sale = {
            "id_venta": "11111111-1111-4111-8111-111111111111",
            "valor_total": valor_total,
            "fecha_venta": "2026-10-15T12:00:00",
            "id_medio_pago": id_medio_pago,
            "caja": 1,
            "tendero": 1,
        }
        self.sales.append(sale)
        return sale


def _click(qtbot, widget) -> None:
    qtbot.mouseClick(widget, Qt.LeftButton)


def _find(window, name: str):
    widget = window.findChild(QObject, name)
    assert widget is not None, f"No se encontró {name}"
    return widget


def _enter_amount_and_agregar(qtbot, window, digits: str) -> None:
    for digit in digits:
        _click(qtbot, _find(window, f"digit_{digit}"))
    _click(qtbot, _find(window, "agregar_button"))


def _accept_confirm_then_saved(assertions=None) -> None:
    def accept_saved() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, SaleSavedDialog):
                assert (
                    widget.findChild(QObject, "sale_saved_message").text()
                    == "Venta guardada correctamente"
                )
                widget.accept()
                return

    for widget in QApplication.topLevelWidgets():
        if isinstance(widget, ConfirmSaleDialog):
            if assertions is not None:
                assertions(widget)
            widget.accept()
            QTimer.singleShot(0, accept_saved)
            return


def test_menu_opens_register_and_loads_payment_methods(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    assert api.request_count == 0
    _click(qtbot, _find(window, "menu_register_button"))
    combo = _find(window, "payment_combo")
    assert combo.count() == 3
    assert combo.itemText(1) == "Efectivo"
    assert api.request_count == 1


def test_plus_minus_buttons_absent(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    assert window.findChild(QObject, "add_button") is None
    assert window.findChild(QObject, "subtract_button") is None
    assert _find(window, "agregar_button") is not None
    assert _find(window, "borrar_button") is not None


def test_back_button_returns_to_menu_without_pending_purchase(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    _click(qtbot, _find(window, "menu_register_button"))
    assert window.centralWidget().currentWidget() is window._register

    _click(qtbot, _find(window, "back_button"))
    assert window.centralWidget().currentWidget() is window._menu
    assert _find(window, "sale_display").text() == ""
    assert _find(window, "purchase_list").text() == ""


def test_back_preserves_pending_purchase_and_payment(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    _click(qtbot, _find(window, "menu_register_button"))
    _enter_amount_and_agregar(qtbot, window, "5000")
    for digit in "300":
        _click(qtbot, _find(window, f"digit_{digit}"))
    _find(window, "payment_combo").setCurrentIndex(1)

    _click(qtbot, _find(window, "back_button"))
    assert window.centralWidget().currentWidget() is window._menu

    requests_before_reenter = api.request_count
    _click(qtbot, _find(window, "menu_register_button"))
    assert window.centralWidget().currentWidget() is window._register
    assert api.request_count == requests_before_reenter + 1

    assert _find(window, "purchase_list").text() == "$ 5.000"
    assert _find(window, "purchase_total").text() == "Total: $ 5.000"
    assert _find(window, "sale_display").text() == "$ 300"
    assert _find(window, "payment_combo").currentData() == 1
    assert _find(window, "submit_sale_button").isEnabled()


def test_calculator_keys_do_not_call_api(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    after_load = api.request_count

    for name in (
        "digit_5",
        "digit_0",
        "digit_0",
        "digit_0",
        "agregar_button",
        "digit_2",
        "digit_0",
        "digit_0",
        "digit_0",
        "agregar_button",
    ):
        _click(qtbot, _find(window, name))

    assert api.request_count == after_load
    assert _find(window, "sale_display").text() == ""
    assert _find(window, "purchase_list").text() == "$ 5.000\n$ 2.000"
    assert _find(window, "purchase_total").text() == "Total: $ 7.000"


def test_realtime_money_format_while_typing(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    after_load = api.request_count

    for digit, expected in [
        ("1", "$ 1"),
        ("2", "$ 12"),
        ("5", "$ 125"),
        ("0", "$ 1.250"),
        ("0", "$ 12.500"),
    ]:
        _click(qtbot, _find(window, f"digit_{digit}"))
        assert _find(window, "sale_display").text() == expected

    assert api.request_count == after_load


def test_borrar_removes_digit_not_purchase_items(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    after_load = api.request_count

    _enter_amount_and_agregar(qtbot, window, "5000")
    for digit in "3000":
        _click(qtbot, _find(window, f"digit_{digit}"))
    assert _find(window, "sale_display").text() == "$ 3.000"

    _click(qtbot, _find(window, "borrar_button"))
    assert _find(window, "sale_display").text() == "$ 300"
    assert _find(window, "purchase_list").text() == "$ 5.000"
    assert _find(window, "purchase_total").text() == "Total: $ 5.000"
    assert api.request_count == after_load


def test_clear_resets_entire_purchase(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    after_load = api.request_count

    _enter_amount_and_agregar(qtbot, window, "5000")
    _enter_amount_and_agregar(qtbot, window, "3000")
    for digit in "100":
        _click(qtbot, _find(window, f"digit_{digit}"))

    _click(qtbot, _find(window, "clear_button"))

    assert _find(window, "sale_display").text() == ""
    assert _find(window, "purchase_list").text() == ""
    assert _find(window, "purchase_total").text() == ""
    assert api.request_count == after_load


def test_submit_disabled_without_value_or_payment(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    submit = _find(window, "submit_sale_button")
    assert not submit.isEnabled()

    for digit in "5000":
        _click(qtbot, _find(window, f"digit_{digit}"))
    _find(window, "payment_combo").setCurrentIndex(1)
    assert not submit.isEnabled()

    _click(qtbot, _find(window, "agregar_button"))
    assert submit.isEnabled()

    _find(window, "payment_combo").setCurrentIndex(0)
    assert not submit.isEnabled()
    assert api.sales == []


def test_cancel_confirmation_does_not_save(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    _enter_amount_and_agregar(qtbot, window, "5000")
    _find(window, "payment_combo").setCurrentIndex(1)

    def reject_dialog() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ConfirmSaleDialog):
                widget.reject()
                return

    QTimer.singleShot(0, reject_dialog)
    _click(qtbot, _find(window, "submit_sale_button"))
    qtbot.waitUntil(
        lambda: api.sales == []
        and _find(window, "purchase_list").text() == "$ 5.000"
        and _find(window, "purchase_total").text() == "Total: $ 5.000"
    )
    assert api.sales == []
    assert _find(window, "sale_display").text() == ""
    assert window.findChild(QObject, "sale_saved_dialog") is None


def test_confirm_sale_posts_and_resets_form(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    _enter_amount_and_agregar(qtbot, window, "25000")
    _find(window, "payment_combo").setCurrentIndex(1)

    def assert_confirm(dialog: ConfirmSaleDialog) -> None:
        assert (
            dialog.findChild(QObject, "confirm_value_label").text()
            == "Valor total: $ 25.000"
        )
        assert (
            dialog.findChild(QObject, "confirm_payment_label").text()
            == "Medio de pago: Efectivo"
        )

    QTimer.singleShot(0, lambda: _accept_confirm_then_saved(assert_confirm))
    _click(qtbot, _find(window, "submit_sale_button"))
    qtbot.waitUntil(
        lambda: len(api.sales) == 1 and _find(window, "purchase_list").text() == ""
    )

    assert api.sales[0]["valor_total"] == 25000
    assert api.sales[0]["id_medio_pago"] == 1
    assert _find(window, "sale_display").text() == ""
    assert _find(window, "purchase_list").text() == ""
    assert _find(window, "purchase_total").text() == ""
    assert _find(window, "payment_combo").currentIndex() == 0
    assert not _find(window, "submit_sale_button").isEnabled()
    assert window.centralWidget().currentWidget() is window._register


def test_confirm_sale_posts_accumulated_total(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    _enter_amount_and_agregar(qtbot, window, "5000")
    _enter_amount_and_agregar(qtbot, window, "3000")
    _find(window, "payment_combo").setCurrentIndex(1)

    def assert_confirm(dialog: ConfirmSaleDialog) -> None:
        assert (
            dialog.findChild(QObject, "confirm_value_label").text()
            == "Valor total: $ 8.000"
        )

    QTimer.singleShot(0, lambda: _accept_confirm_then_saved(assert_confirm))
    _click(qtbot, _find(window, "submit_sale_button"))
    qtbot.waitUntil(
        lambda: len(api.sales) == 1 and _find(window, "purchase_list").text() == ""
    )
    assert api.sales[0]["valor_total"] == 8000


def test_api_error_does_not_show_success_popup(qtbot) -> None:
    class FailingApiClient(FakeApiClient):
        def create_sale(self, valor_total: int, id_medio_pago: int) -> Mapping[str, Any]:
            self.request_count += 1
            raise httpx.HTTPError("fallo de red")

    api = FailingApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    _enter_amount_and_agregar(qtbot, window, "5000")
    _find(window, "payment_combo").setCurrentIndex(1)

    def accept_confirm_then_dismiss_error() -> None:
        def dismiss_error() -> None:
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMessageBox):
                    widget.accept()
                    return

        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ConfirmSaleDialog):
                widget.accept()
                QTimer.singleShot(0, dismiss_error)
                return

    QTimer.singleShot(0, accept_confirm_then_dismiss_error)
    _click(qtbot, _find(window, "submit_sale_button"))
    qtbot.waitUntil(
        lambda: api.request_count >= 2
        and _find(window, "purchase_list").text() == "$ 5.000"
    )

    assert api.sales == []
    assert window.findChild(QObject, "sale_saved_dialog") is None
    assert _find(window, "purchase_total").text() == "Total: $ 5.000"
    assert _find(window, "payment_combo").currentIndex() == 1


class DesktopApiViaTestClient:
    """Cliente de escritorio respaldado por TestClient (sin red real)."""

    def __init__(self, db_path) -> None:
        self.request_count = 0
        self._context = TestClient(create_app(db_path))
        self._client = self._context.__enter__()

    def list_payment_methods(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        response = self._client.get("/medios-pago")
        response.raise_for_status()
        return response.json()

    def create_sale(self, valor_total: int, id_medio_pago: int) -> Mapping[str, Any]:
        self.request_count += 1
        response = self._client.post(
            "/ventas",
            json={"valor_total": valor_total, "id_medio_pago": id_medio_pago},
        )
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._context.__exit__(None, None, None)


def test_happy_path_persists_sale_through_api(qtbot, tmp_path) -> None:
    db_path = tmp_path / "bakery.sqlite3"
    api = DesktopApiViaTestClient(db_path)
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    try:
        _click(qtbot, _find(window, "menu_register_button"))
        _enter_amount_and_agregar(qtbot, window, "5000")
        _find(window, "payment_combo").setCurrentIndex(1)

        def sale_count() -> int:
            connection = connect(db_path)
            try:
                return connection.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
            finally:
                connection.close()

        QTimer.singleShot(0, _accept_confirm_then_saved)
        _click(qtbot, _find(window, "submit_sale_button"))
        qtbot.waitUntil(
            lambda: sale_count() == 1 and _find(window, "purchase_list").text() == "",
            timeout=3000,
        )

        connection = connect(db_path)
        try:
            row = connection.execute("SELECT * FROM ventas").fetchone()
            assert row["valor_total"] == 5000
            assert row["id_medio_pago"] == 1
            assert row["caja"] == 1
            assert row["tendero"] == 1
            assert len(row["id_venta"]) == 36
        finally:
            connection.close()
    finally:
        api.close()
