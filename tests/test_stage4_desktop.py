import json
from typing import Any, List, Mapping

import httpx
from fastapi.testclient import TestClient
from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from bakery.api.app import create_app
from bakery.app.money import format_cop
from bakery.app.promotions import (
    compute_cart_line_subtotals,
    is_active_cantidad_por_monto,
    use_promociones_table,
)
from bakery.desktop import style
from bakery.desktop.main import create_window
from bakery.desktop.ui import (
    ConfirmSaleDialog,
    SaleSavedDialog,
    SelectPaymentMethodDialog,
)
from bakery.persistence.connection import connect
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    PROMOCION_PAN_PEQUENO_CONFIG,
    TIPO_PROMOCION_CANTIDAD_POR_MONTO,
)

_PAN_PROMO_FIELDS = {
    "promocion_id": 1,
    "promocion_tipo": TIPO_PROMOCION_CANTIDAD_POR_MONTO,
    "promocion_configuracion": json.dumps(
        PROMOCION_PAN_PEQUENO_CONFIG, separators=(",", ":"), sort_keys=True
    ),
    "promocion_activo": ESTADO_ACTIVO,
}

_PRODUCT_ID_SEQ = {"n": 1}


class FakeApiClient:
    def __init__(
        self,
        methods: List[Mapping[str, Any]] = None,
        *,
        categories: List[Mapping[str, Any]] = None,
        products: List[Mapping[str, Any]] = None,
    ) -> None:
        self.request_count = 0
        self.sales: List[Mapping[str, Any]] = []
        self.methods = methods or [
            {"id_medio_pago": 1, "nombre": "Efectivo", "id_estado": 1},
            {"id_medio_pago": 2, "nombre": "Nequi", "id_estado": 1},
        ]
        self.categories = categories or [
            {"id_categoria": 1, "nombre": "Panadería"},
            {"id_categoria": 2, "nombre": "Bebidas"},
            {"id_categoria": 6, "nombre": NOMBRE_CATEGORIA_PAN_PEQUENO},
        ]
        self.products = products or [
            {
                "id_producto": 1,
                "nombre": "Pan",
                "precio": 5000,
                "id_categoria": 1,
                "descripcion": None,
                "id_estado": 1,
            },
            {
                "id_producto": 2,
                "nombre": "Café",
                "precio": 3000,
                "id_categoria": 2,
                "descripcion": None,
                "id_estado": 1,
            },
            {
                "id_producto": 3,
                "nombre": "Pan 2",
                "precio": 5000,
                "id_categoria": 1,
                "descripcion": None,
                "id_estado": 1,
            },
            {
                "id_producto": 4,
                "nombre": "Pan rollo",
                "precio": 300,
                "id_categoria": 6,
                "descripcion": None,
                "id_estado": 1,
                **_PAN_PROMO_FIELDS,
            },
            {
                "id_producto": 5,
                "nombre": "Torta",
                "precio": 20000,
                "id_categoria": 1,
                "descripcion": None,
                "id_estado": 1,
            },
            {
                "id_producto": 99,
                "nombre": "Inactivo",
                "precio": 5000,
                "id_categoria": 1,
                "descripcion": None,
                "id_estado": 0,
            },
        ]

    def list_payment_methods(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        return list(self.methods)

    def list_categories(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        return list(self.categories)

    def list_products(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        return [dict(p) for p in self.products]

    def list_active_products(
        self,
        *,
        id_categoria: int = None,
        precio: int = None,
    ) -> List[Mapping[str, Any]]:
        self.request_count += 1
        rows = [p for p in self.products if p["id_estado"] == 1]
        if id_categoria is not None:
            rows = [p for p in rows if p["id_categoria"] == id_categoria]
        if precio is not None:
            rows = [p for p in rows if p["precio"] == precio]
        return [dict(p) for p in rows]

    def create_sale(
        self, id_medio_pago: int, lineas: List[Mapping[str, Any]]
    ) -> Mapping[str, Any]:
        self.request_count += 1
        prod_by_id = {p["id_producto"]: p for p in self.products}
        if use_promociones_table():
            valor_total = self._valor_total_promociones(lineas, prod_by_id)
        else:
            valor_total = sum(
                int(line["precio_aplicado"]) * int(line["cantidad"]) for line in lineas
            )
        sale = {
            "id_venta": "11111111-1111-4111-8111-111111111111",
            "valor_total": valor_total,
            "fecha_venta": "2026-10-15T12:00:00",
            "id_medio_pago": id_medio_pago,
            "caja": 1,
            "tendero": 1,
            "lineas": list(lineas),
        }
        self.sales.append(sale)
        return sale

    def _valor_total_promociones(
        self,
        lineas: List[Mapping[str, Any]],
        prod_by_id: Mapping[int, Mapping[str, Any]],
    ) -> int:
        pending: List[Mapping[str, Any]] = []
        promos_by_id: dict = {}
        for line in lineas:
            product = prod_by_id.get(int(line["id_producto"]))
            promo_id = None
            promo = None
            if product is not None:
                promo_id = product.get("promocion_id")
                if isinstance(promo_id, int) and not isinstance(promo_id, bool):
                    promo = {
                        "id": promo_id,
                        "tipo": product.get(
                            "promocion_tipo", TIPO_PROMOCION_CANTIDAD_POR_MONTO
                        ),
                        "configuracion": product.get("promocion_configuracion"),
                        "activo": product.get("promocion_activo", ESTADO_ACTIVO),
                    }
                    if is_active_cantidad_por_monto(promo):
                        promos_by_id[promo_id] = promo
                    else:
                        promo = None
            pending.append(
                {
                    "id_producto": int(line["id_producto"]),
                    "cantidad": int(line["cantidad"]),
                    "precio_aplicado": int(line["precio_aplicado"]),
                    "promocion_id": promo_id if promo is not None else None,
                }
            )
        return sum(
            compute_cart_line_subtotals(pending, promos_by_id=promos_by_id)
        )


def _click(qtbot, widget) -> None:
    qtbot.mouseClick(widget, Qt.LeftButton)


def _find(window, name: str):
    widget = window.findChild(QObject, name)
    assert widget is not None, f"No se encontró {name}"
    return widget


def _line_text(nombre: str, precio: int, cantidad: int = 1) -> str:
    return f"{nombre} × {cantidad} — {format_cop(precio * cantidad)}"


def _select_draft_product(
    window, *, precio: int, nombre: str = "Producto", id_producto: int = None
) -> None:
    if id_producto is None:
        id_producto = _PRODUCT_ID_SEQ["n"]
        _PRODUCT_ID_SEQ["n"] += 1
    window._register._draft.select_product(
        {"id_producto": id_producto, "nombre": nombre, "precio": precio}
    )


def _enter_amount_and_agregar(
    qtbot, window, digits: str, *, nombre: str = "Producto", id_producto: int = None
) -> None:
    """Selecciona producto (UI o draft) y agrega con el pad."""
    precio = int(digits)
    product_button = None
    if id_producto is not None:
        product_button = window.findChild(QObject, f"sale_product_{id_producto}")
    if product_button is None:
        for product in getattr(window._register, "_active_products", []):
            if product["precio"] == precio and product["nombre"] == nombre:
                product_button = window.findChild(
                    QObject, f"sale_product_{product['id_producto']}"
                )
                break
    if product_button is not None:
        _click(qtbot, product_button)
    else:
        _select_draft_product(window, precio=precio, nombre=nombre, id_producto=id_producto)
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


def test_menu_button_top_left_green_and_opens_register(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.resize(800, 600)
    window.show()

    assert _find(window, "menu_grid") is not None
    button = _find(window, "menu_register_button")
    assert button.text() == "Registrar venta"
    assert button.property("class") == "menu-button"
    assert "#2E7D32" in style.load_theme_qss()
    assert style.MENU_BUTTON_COLOR == "#2E7D32"
    assert style.MENU_MARGIN == 20

    # Arriba a la izquierda respecto a MenuPage, con margen ~20 px.
    pos = button.mapTo(window._menu, button.rect().topLeft())
    assert pos.x() <= style.MENU_MARGIN + 5
    assert pos.y() <= style.MENU_MARGIN + 5

    assert api.request_count == 0
    _click(qtbot, button)
    assert window.centralWidget().currentWidget() is window._register
    # medios-pago + categorías + productos activos
    assert api.request_count == 3


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
    assert api.request_count == 3

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


def test_register_layout_detail_scroll_and_pad_stretch(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    assert _find(window, "purchase_list_scroll") is not None
    assert _find(window, "pad_panel") is not None
    assert _find(window, "purchase_list") is not None

    left = _find(window, "left_column")
    left_layout = left.layout()
    assert left_layout.stretch(0) == style.PURCHASE_PANEL_STRETCH
    assert left_layout.stretch(1) == style.PAD_PANEL_STRETCH
    assert style.PAD_PANEL_STRETCH == 2 * style.PURCHASE_PANEL_STRETCH

    for amount in ("1000", "2000", "3000", "4000", "5000", "6000", "7000", "8000"):
        _enter_amount_and_agregar(qtbot, window, amount)
    assert _find(window, "purchase_list").text().count("\n") == 7
    assert _find(window, "purchase_total").text() == "Total: $ 36.000"


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

    _select_draft_product(window, precio=500, nombre="Producto")
    _click(qtbot, _find(window, "agregar_button"))
    assert _find(window, "purchase_list").text() == _line_text("Producto", 500)
    assert _find(window, "purchase_total").text() == "Total: $ 500"
    assert api.request_count == after_load


def test_back_button_returns_to_menu_without_pending_purchase(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    _click(qtbot, _find(window, "menu_register_button"))
    assert window.centralWidget().currentWidget() is window._register

    back = _find(window, "back_button")
    assert back.text() != "Volver"
    assert back.text() == "←"
    assert back.minimumWidth() >= style.BACK_BUTTON_MIN_WIDTH
    assert back.minimumHeight() >= style.BACK_BUTTON_MIN_HEIGHT
    assert back.minimumWidth() > back.minimumHeight()

    _click(qtbot, back)
    assert window.centralWidget().currentWidget() is window._menu
    assert _find(window, "sale_display").text() == "$ 0"
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
    assert api.request_count == requests_before_reenter + 3

    assert _find(window, "purchase_list").text() == _line_text("Producto", 5000)
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

    _enter_amount_and_agregar(qtbot, window, "5000")
    _enter_amount_and_agregar(qtbot, window, "2000")

    assert api.request_count == after_load
    assert _find(window, "sale_display").text() == "$ 0"
    assert _find(window, "purchase_list").text() == (
        f"{_line_text('Producto', 5000)}\n{_line_text('Producto', 2000)}"
    )
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
    assert _find(window, "purchase_list").text() == _line_text("Producto", 5000)
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

    assert _find(window, "sale_display").text() == "$ 0"
    assert _find(window, "purchase_list").text() == ""
    assert _find(window, "purchase_total").text() == "Total: $ 0"
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
    assert not submit.isEnabled()  # sin producto seleccionado no agrega

    _select_draft_product(window, precio=5000, nombre="Producto")
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
        and _find(window, "purchase_list").text() == _line_text("Producto", 5000)
        and _find(window, "purchase_total").text() == "Total: $ 5.000"
    )
    assert api.sales == []
    assert _find(window, "sale_display").text() == "$ 0"
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
    assert _find(window, "sale_display").text() == "$ 0"
    assert _find(window, "purchase_list").text() == ""
    assert _find(window, "purchase_total").text() == "Total: $ 0"
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
        def create_sale(
            self, id_medio_pago: int, lineas: List[Mapping[str, Any]]
        ) -> Mapping[str, Any]:
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
        and _find(window, "purchase_list").text() == _line_text("Producto", 5000)
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

    def list_categories(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        response = self._client.get("/categorias")
        response.raise_for_status()
        return response.json()

    def list_products(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        response = self._client.get("/productos")
        response.raise_for_status()
        return response.json()

    def list_active_products(
        self,
        *,
        id_categoria: int = None,
        precio: int = None,
    ) -> List[Mapping[str, Any]]:
        self.request_count += 1
        params = {}
        if id_categoria is not None:
            params["id_categoria"] = id_categoria
        if precio is not None:
            params["precio"] = precio
        response = self._client.get("/productos/activos", params=params or None)
        response.raise_for_status()
        return response.json()

    def create_product(
        self,
        *,
        nombre: str,
        precio: int,
        id_categoria: int,
        descripcion: str = None,
    ) -> Mapping[str, Any]:
        self.request_count += 1
        response = self._client.post(
            "/productos",
            json={
                "nombre": nombre,
                "precio": precio,
                "id_categoria": id_categoria,
                "descripcion": descripcion,
            },
        )
        response.raise_for_status()
        return response.json()

    def create_sale(
        self, id_medio_pago: int, lineas: List[Mapping[str, Any]]
    ) -> Mapping[str, Any]:
        self.request_count += 1
        response = self._client.post(
            "/ventas",
            json={"id_medio_pago": id_medio_pago, "lineas": list(lineas)},
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
        product = api.create_product(nombre="Pan", precio=5000, id_categoria=1)
        _click(qtbot, _find(window, "menu_register_button"))
        _select_draft_product(
            window,
            precio=5000,
            nombre="Pan",
            id_producto=product["id_producto"],
        )
        for digit in "5000":
            _click(qtbot, _find(window, f"digit_{digit}"))
        _click(qtbot, _find(window, "agregar_button"))
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
