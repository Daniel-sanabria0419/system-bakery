"""Etapa 4: al entrar / al Pagar, revalidar carrito vs catálogo; volver no vacía."""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication

from bakery.app.money import format_cop
from bakery.desktop.main import create_window
from bakery.desktop.ui import ConfirmSaleDialog, SaleSavedDialog
from tests.test_stage4_desktop import (
    FakeApiClient,
    _click,
    _find,
    _line_text,
    _purchase_list_text,
    _select_payment,
)


def test_volver_preserves_cart_without_clearing(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_1"))
    _click(qtbot, _find(window, "agregar_button"))
    assert _purchase_list_text(window) == _line_text("Pan", 5000)

    _click(qtbot, _find(window, "back_button"))
    _click(qtbot, _find(window, "menu_register_button"))
    assert _purchase_list_text(window) == _line_text("Pan", 5000)
    assert _find(window, "sale_feedback").text() == ""
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(5000)}"


def test_reenter_updates_changed_price_and_feedback(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_1"))
    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(5000)}"

    _click(qtbot, _find(window, "back_button"))
    for product in api.products:
        if product["id_producto"] == 1:
            product["precio"] = 5500
            break

    _click(qtbot, _find(window, "menu_register_button"))
    assert _purchase_list_text(window) == _line_text("Pan", 5500)
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(5500)}"
    feedback = _find(window, "sale_feedback").text()
    assert "Pan" in feedback
    assert "cambió" in feedback


def test_reenter_removes_inactive_product_with_feedback(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_1"))
    _click(qtbot, _find(window, "agregar_button"))
    _click(qtbot, _find(window, "sale_product_2"))
    _click(qtbot, _find(window, "agregar_button"))
    assert "Pan" in _purchase_list_text(window)
    assert "Café" in _purchase_list_text(window)

    _click(qtbot, _find(window, "back_button"))
    for product in api.products:
        if product["id_producto"] == 1:
            product["id_estado"] = 0
            break

    _click(qtbot, _find(window, "menu_register_button"))
    assert "Pan" not in _purchase_list_text(window)
    assert _purchase_list_text(window) == _line_text("Café", 3000)
    feedback = _find(window, "sale_feedback").text()
    assert "Pan" in feedback
    assert "quitó" in feedback
    assert _find(window, "purchase_total").text() == f"Total: {format_cop(3000)}"


def test_pagar_revalidates_before_post(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_1"))
    _click(qtbot, _find(window, "agregar_button"))
    _select_payment(qtbot, window, 1)

    for product in api.products:
        if product["id_producto"] == 1:
            product["precio"] = 6000
            break

    seen_total = {"ok": False}

    def accept_flow() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ConfirmSaleDialog):
                # Pantalla y diálogo ya muestran el total revalidado.
                assert _find(window, "purchase_total").text() == (
                    f"Total: {format_cop(6000)}"
                )
                confirm_value = widget.findChild(QObject, "confirm_value_label")
                assert confirm_value is not None
                assert format_cop(6000) in confirm_value.text()
                seen_total["ok"] = True
                widget.accept()

                def accept_saved() -> None:
                    for saved in QApplication.topLevelWidgets():
                        if isinstance(saved, SaleSavedDialog):
                            saved.accept()
                            return

                QTimer.singleShot(0, accept_saved)
                return

    QTimer.singleShot(0, accept_flow)
    _click(qtbot, _find(window, "submit_sale_button"))
    qtbot.waitUntil(lambda: len(api.sales) == 1, timeout=2000)
    assert seen_total["ok"] is True
    sale = api.sales[0]
    assert sale["valor_total"] == 6000
    assert sale["lineas"][0]["precio_aplicado"] == 6000
