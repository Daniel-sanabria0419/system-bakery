from typing import Any, List, Mapping

from fastapi.testclient import TestClient
from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtWidgets import QApplication

from bakery.api.app import create_app
from bakery.desktop.main import create_window
from bakery.desktop.ui import ConfirmSaleDialog
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
        "add_button",
        "digit_2",
        "digit_0",
        "digit_0",
        "digit_0",
    ):
        _click(qtbot, _find(window, name))

    assert api.request_count == after_load
    assert _find(window, "sale_display").text() == "$ 7.000"
    assert _find(window, "sale_expression").text() == "5000 + 2000"


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

    _find(window, "payment_combo").setCurrentIndex(1)
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
    for digit in "5000":
        _click(qtbot, _find(window, f"digit_{digit}"))
    _find(window, "payment_combo").setCurrentIndex(1)

    def reject_dialog() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ConfirmSaleDialog):
                widget.reject()
                return

    QTimer.singleShot(0, reject_dialog)
    _click(qtbot, _find(window, "submit_sale_button"))
    qtbot.waitUntil(
        lambda: api.sales == [] and _find(window, "sale_display").text() == "$ 5.000"
    )
    assert api.sales == []
    assert _find(window, "sale_expression").text() == "5000"


def test_confirm_sale_posts_and_resets_form(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    for digit in "25000":
        _click(qtbot, _find(window, f"digit_{digit}"))
    _find(window, "payment_combo").setCurrentIndex(1)

    def accept_dialog() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ConfirmSaleDialog):
                assert (
                    widget.findChild(QObject, "confirm_value_label").text()
                    == "Valor total: $ 25.000"
                )
                assert (
                    widget.findChild(QObject, "confirm_payment_label").text()
                    == "Medio de pago: Efectivo"
                )
                widget.accept()
                return

    QTimer.singleShot(0, accept_dialog)
    _click(qtbot, _find(window, "submit_sale_button"))
    qtbot.waitUntil(lambda: len(api.sales) == 1)

    assert api.sales[0]["valor_total"] == 25000
    assert api.sales[0]["id_medio_pago"] == 1
    assert _find(window, "sale_display").text() == ""
    assert _find(window, "sale_expression").text() == ""
    assert _find(window, "payment_combo").currentIndex() == 0
    assert not _find(window, "submit_sale_button").isEnabled()
    assert window.centralWidget().currentWidget() is window._register


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
        for digit in "5000":
            _click(qtbot, _find(window, f"digit_{digit}"))
        _find(window, "payment_combo").setCurrentIndex(1)

        def accept_dialog() -> None:
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, ConfirmSaleDialog):
                    widget.accept()
                    return

        def sale_count() -> int:
            connection = connect(db_path)
            try:
                return connection.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
            finally:
                connection.close()

        QTimer.singleShot(0, accept_dialog)
        _click(qtbot, _find(window, "submit_sale_button"))
        qtbot.waitUntil(lambda: sale_count() == 1, timeout=3000)

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
