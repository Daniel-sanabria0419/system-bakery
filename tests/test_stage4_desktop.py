from typing import Any, List, Mapping

import httpx
from fastapi.testclient import TestClient
from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from bakery.api.app import create_app
from bakery.desktop import style
from bakery.desktop.main import create_window
from bakery.desktop.ui import (
    ConfirmSaleDialog,
    SaleSavedDialog,
    SelectPaymentMethodDialog,
)
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


def _select_payment(qtbot, window, payment_id: int = 1) -> None:
    attempts = {"n": 0}

    def pick() -> None:
        attempts["n"] += 1
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, SelectPaymentMethodDialog) and widget.isVisible():
                button = widget.findChild(QObject, f"payment_method_{payment_id}")
                if button is not None:
                    button.click()
                    return
        if attempts["n"] < 50:
            QTimer.singleShot(20, pick)

    QTimer.singleShot(50, pick)
    _click(qtbot, _find(window, "payment_button"))


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
    payment_button = _find(window, "payment_button")
    assert payment_button.text() == "Seleccionar medio de pago"
    assert window.findChild(QObject, "payment_combo") is None
    assert api.request_count == 1

    attempts = {"n": 0}

    def inspect_and_choose() -> None:
        attempts["n"] += 1
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, SelectPaymentMethodDialog) and widget.isVisible():
                efectivo = widget.findChild(QObject, "payment_method_1")
                assert efectivo is not None
                assert efectivo.text() == "Efectivo"
                assert widget.findChild(QObject, "payment_method_2") is not None
                efectivo.click()
                return
        if attempts["n"] < 50:
            QTimer.singleShot(20, inspect_and_choose)

    QTimer.singleShot(50, inspect_and_choose)
    _click(qtbot, payment_button)
    qtbot.waitUntil(lambda: payment_button.text() == "Medio de pago: Efectivo")
    assert payment_button.text() == "Medio de pago: Efectivo"


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


def test_register_layout_has_panel_pad_and_future_space(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    assert _find(window, "purchase_panel") is not None
    assert _find(window, "entry_separator") is not None
    assert _find(window, "total_separator") is not None
    assert _find(window, "future_panel") is not None
    assert _find(window, "digit_00") is not None
    submit = _find(window, "submit_sale_button")
    assert submit.text() == "Pago"


def test_digit_00_appends_without_http(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    after_load = api.request_count

    _click(qtbot, _find(window, "digit_5"))
    _click(qtbot, _find(window, "digit_00"))
    assert _find(window, "sale_display").text() == "$ 500"
    assert api.request_count == after_load

    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_list").text() == "$ 500"
    assert _find(window, "purchase_total").text() == "Total: $ 500"
    assert api.request_count == after_load


def test_back_button_returns_to_menu_without_pending_purchase(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    _click(qtbot, _find(window, "menu_register_button"))
    assert window.centralWidget().currentWidget() is window._register

    _click(qtbot, _find(window, "back_button"))
    assert window.centralWidget().currentWidget() is window._menu
    assert _find(window, "sale_display").text() == "$ 0.00"
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
    _select_payment(qtbot, window, 1)

    _click(qtbot, _find(window, "back_button"))
    assert window.centralWidget().currentWidget() is window._menu

    requests_before_reenter = api.request_count
    _click(qtbot, _find(window, "menu_register_button"))
    assert window.centralWidget().currentWidget() is window._register
    assert api.request_count == requests_before_reenter + 1

    assert _find(window, "purchase_list").text() == "$ 5.000"
    assert _find(window, "purchase_total").text() == "Total: $ 5.000"
    assert _find(window, "sale_display").text() == "$ 300"
    assert _find(window, "payment_button").text() == "Medio de pago: Efectivo"
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
    assert _find(window, "sale_display").text() == "$ 0.00"
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

    assert _find(window, "sale_display").text() == "$ 0.00"
    assert _find(window, "purchase_list").text() == ""
    assert _find(window, "purchase_total").text() == "Total: $0.00"
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
    assert not submit.isEnabled()

    _click(qtbot, _find(window, "agregar_button"))
    assert not submit.isEnabled()

    _select_payment(qtbot, window, 1)
    assert submit.isEnabled()
    assert api.sales == []


def test_payment_dialog_reopen_changes_selection(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    _select_payment(qtbot, window, 1)
    assert _find(window, "payment_button").text() == "Medio de pago: Efectivo"

    _select_payment(qtbot, window, 2)
    assert _find(window, "payment_button").text() == "Medio de pago: Nequi"


def test_payment_dialog_layouts_max_five_per_row(qtbot) -> None:
    methods = [
        {"id_medio_pago": i, "nombre": f"M{i}", "id_estado": 1} for i in range(1, 7)
    ]
    api = FakeApiClient(methods=methods)
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    result = {"ok": False}
    attempts = {"n": 0}

    def inspect_layout() -> None:
        attempts["n"] += 1
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, SelectPaymentMethodDialog) and widget.isVisible():
                assert widget.objectName() == "select_payment_dialog"
                layout = widget.layout().itemAt(0).layout()
                assert layout.rowCount() == 2
                assert layout.columnCount() == 5
                assert layout.itemAtPosition(0, 4).widget().objectName() == "payment_method_5"
                assert layout.itemAtPosition(1, 0).widget().objectName() == "payment_method_6"
                assert layout.itemAtPosition(0, 5) is None
                widget.findChild(QObject, "payment_method_6").click()
                result["ok"] = True
                return
        if attempts["n"] < 50:
            QTimer.singleShot(20, inspect_layout)

    QTimer.singleShot(50, inspect_layout)
    _click(qtbot, _find(window, "payment_button"))
    qtbot.waitUntil(
        lambda: _find(window, "payment_button").text() == "Medio de pago: M6"
    )
    assert result["ok"]


def test_payment_dialog_escape_does_not_close(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    state = {"seen": False}
    attempts = {"n": 0}

    def press_escape_then_choose() -> None:
        attempts["n"] += 1
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, SelectPaymentMethodDialog) and widget.isVisible():
                state["seen"] = True
                widget.reject()
                assert widget.isVisible()
                widget.findChild(QObject, "payment_method_1").click()
                return
        if attempts["n"] < 50:
            QTimer.singleShot(20, press_escape_then_choose)

    QTimer.singleShot(50, press_escape_then_choose)
    _click(qtbot, _find(window, "payment_button"))
    qtbot.waitUntil(
        lambda: state["seen"]
        and _find(window, "payment_button").text() == "Medio de pago: Efectivo"
    )


def test_cancel_confirmation_does_not_save(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    _enter_amount_and_agregar(qtbot, window, "5000")
    _select_payment(qtbot, window, 1)

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
    assert _find(window, "sale_display").text() == "$ 0.00"
    assert window.findChild(QObject, "sale_saved_dialog") is None


def test_confirm_and_saved_dialogs_have_large_touch_controls(qtbot) -> None:
    confirm = ConfirmSaleDialog(5000, "Efectivo")
    qtbot.addWidget(confirm)
    confirm.show()
    assert confirm.minimumWidth() >= style.DIALOG_MIN_WIDTH
    assert confirm.minimumHeight() >= style.DIALOG_MIN_HEIGHT
    for name in ("confirm_button", "cancel_button"):
        button = confirm.findChild(QObject, name)
        assert button is not None
        assert button.minimumHeight() >= style.DIALOG_ACTION_BUTTON_MIN_HEIGHT

    saved = SaleSavedDialog()
    qtbot.addWidget(saved)
    saved.show()
    assert saved.minimumWidth() >= style.DIALOG_MIN_WIDTH
    assert saved.minimumHeight() >= style.DIALOG_MIN_HEIGHT
    ok = saved.findChild(QObject, "sale_saved_ok_button")
    assert ok is not None
    assert ok.minimumHeight() >= style.DIALOG_ACTION_BUTTON_MIN_HEIGHT


def test_confirm_sale_posts_and_resets_form(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    _enter_amount_and_agregar(qtbot, window, "25000")
    _select_payment(qtbot, window, 1)

    def assert_confirm(dialog: ConfirmSaleDialog) -> None:
        assert (
            dialog.findChild(QObject, "confirm_value_label").text()
            == "Valor total: $ 25.000"
        )
        assert (
            dialog.findChild(QObject, "confirm_payment_label").text()
            == "Medio de pago: Efectivo"
        )
        assert (
            dialog.findChild(QObject, "confirm_button").minimumHeight()
            >= style.DIALOG_ACTION_BUTTON_MIN_HEIGHT
        )

    def assert_saved_size() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, SaleSavedDialog):
                assert (
                    widget.findChild(QObject, "sale_saved_ok_button").minimumHeight()
                    >= style.DIALOG_ACTION_BUTTON_MIN_HEIGHT
                )
                widget.accept()
                return

    def accept_confirm_then_saved() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ConfirmSaleDialog):
                assert_confirm(widget)
                widget.accept()
                QTimer.singleShot(0, assert_saved_size)
                return

    QTimer.singleShot(0, accept_confirm_then_saved)
    _click(qtbot, _find(window, "submit_sale_button"))
    qtbot.waitUntil(
        lambda: len(api.sales) == 1 and _find(window, "purchase_list").text() == ""
    )

    assert api.sales[0]["valor_total"] == 25000
    assert api.sales[0]["id_medio_pago"] == 1
    assert _find(window, "sale_display").text() == "$ 0.00"
    assert _find(window, "purchase_list").text() == ""
    assert _find(window, "purchase_total").text() == "Total: $0.00"
    assert _find(window, "payment_button").text() == "Seleccionar medio de pago"
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
    _select_payment(qtbot, window, 1)

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
    _select_payment(qtbot, window, 1)

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
    assert _find(window, "payment_button").text() == "Medio de pago: Efectivo"


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
        _select_payment(qtbot, window, 1)

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
