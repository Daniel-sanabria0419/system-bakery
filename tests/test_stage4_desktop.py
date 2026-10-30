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
        self,
        id_medio_pago: int,
        lineas: List[Mapping[str, Any]],
        *,
        id_venta: str,
    ) -> Mapping[str, Any]:
        self.request_count += 1
        prod_by_id = {p["id_producto"]: p for p in self.products}
        valor_total = self._valor_total_promociones(lineas, prod_by_id)
        sale = {
            "id_venta": id_venta,
            "valor_total": valor_total,
            "fecha_venta": "2026-10-15T12:00:00",
            "id_medio_pago": id_medio_pago,
            "caja": 1,
            "tendero": 1,
            "lineas": list(lineas),
        }
        self.sales.append(sale)
        return sale

    def list_sales(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        rows = []
        for sale in self.sales:
            lineas = list(sale.get("lineas") or [])
            rows.append(
                {
                    "id_venta": sale["id_venta"],
                    "valor_total": sale["valor_total"],
                    "fecha_venta": sale["fecha_venta"],
                    "id_medio_pago": sale["id_medio_pago"],
                    "nombre_medio": next(
                        (
                            m["nombre"]
                            for m in self.methods
                            if m["id_medio_pago"] == sale["id_medio_pago"]
                        ),
                        "",
                    ),
                    "caja": sale.get("caja", 1),
                    "tendero": sale.get("tendero", 1),
                    "cantidad_lineas": len(lineas),
                    "es_legado": len(lineas) == 0,
                    "editable": True,
                }
            )
        return list(reversed(rows))

    def get_sale(self, id_venta: str) -> Mapping[str, Any]:
        self.request_count += 1
        for sale in self.sales:
            if sale["id_venta"] == id_venta:
                lineas = list(sale.get("lineas") or [])
                detail_lineas = []
                for index, line in enumerate(lineas):
                    product = next(
                        (
                            p
                            for p in self.products
                            if p["id_producto"] == line["id_producto"]
                        ),
                        None,
                    )
                    nombre = product["nombre"] if product else f"#{line['id_producto']}"
                    precio = int(line["precio_aplicado"])
                    cantidad = int(line["cantidad"])
                    subtotal = precio * cantidad
                    detail_lineas.append(
                        {
                            "id_linea": index + 1,
                            "id_venta": id_venta,
                            "id_producto": line["id_producto"],
                            "nombre_producto": nombre,
                            "precio_aplicado": precio,
                            "cantidad": cantidad,
                            "subtotal": subtotal,
                            "total": subtotal,
                            "id_promocion": None,
                            "nombre_promocion": None,
                        }
                    )
                return {
                    "id_venta": sale["id_venta"],
                    "valor_total": sale["valor_total"],
                    "fecha_venta": sale["fecha_venta"],
                    "id_medio_pago": sale["id_medio_pago"],
                    "nombre_medio": next(
                        (
                            m["nombre"]
                            for m in self.methods
                            if m["id_medio_pago"] == sale["id_medio_pago"]
                        ),
                        "",
                    ),
                    "caja": sale.get("caja", 1),
                    "tendero": sale.get("tendero", 1),
                    "lineas": detail_lineas,
                    "observaciones": list(sale.get("observaciones") or []),
                    "es_legado": len(detail_lineas) == 0,
                    "editable": True,
                }
        raise httpx.HTTPStatusError(
            "Venta no encontrada.",
            request=httpx.Request("GET", f"/ventas/{id_venta}"),
            response=httpx.Response(404),
        )

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
        if not pending:
            return 0
        return sum(compute_cart_line_subtotals(pending, promos_by_id=promos_by_id))


def _click(qtbot, widget) -> None:
    qtbot.mouseClick(widget, Qt.LeftButton)


def _find(window, name: str):
    widget = window.findChild(QObject, name)
    assert widget is not None, f"No se encontró {name}"
    return widget


def _line_text(nombre: str, precio: int, cantidad: int = 1) -> str:
    return f"{nombre} × {cantidad} — {format_cop(precio * cantidad)}"


def _purchase_list_text(window) -> str:
    """Resumen multilínea de la tabla (compat con el viejo QLabel)."""
    lines: list = []
    index = 0
    while True:
        nombre = window.findChild(QObject, f"purchase_row_{index}_producto")
        if nombre is None:
            break
        cantidad = window.findChild(QObject, f"purchase_row_{index}_cantidad")
        total = window.findChild(QObject, f"purchase_row_{index}_total")
        assert cantidad is not None and total is not None
        lines.append(f"{nombre.text()} × {cantidad.text()} — {total.text()}")
        index += 1
    return "\n".join(lines)


def _purchase_row_count(window) -> int:
    count = 0
    while window.findChild(QObject, f"purchase_row_{count}") is not None:
        count += 1
    return count


def _select_draft_product(
    window, *, precio: int, nombre: str = "Producto", id_producto: int = None
) -> None:
    api = getattr(window, "_api", None)
    products = getattr(api, "products", None) if api is not None else None
    if id_producto is None:
        # Evitar colisión con IDs del catálogo seed (p. ej. Pan rollo id=4 + promo).
        next_id = _PRODUCT_ID_SEQ["n"]
        if isinstance(products, list) and products:
            max_existing = max(int(p["id_producto"]) for p in products)
            next_id = max(next_id, max_existing + 1)
        id_producto = next_id
        _PRODUCT_ID_SEQ["n"] = id_producto + 1
    product = {
        "id_producto": id_producto,
        "nombre": nombre,
        "precio": precio,
        "id_categoria": 1,
        "descripcion": None,
        "id_estado": 1,
    }
    # Registrar en FakeApiClient para que la revalidación del carrito no lo quite.
    if isinstance(products, list):
        existing = next(
            (p for p in products if p.get("id_producto") == id_producto),
            None,
        )
        if existing is None:
            products.append(dict(product))
        else:
            existing["nombre"] = nombre
            existing["precio"] = precio
            existing["id_estado"] = 1
    window._register._draft.select_product(
        {"id_producto": id_producto, "nombre": nombre, "precio": precio}
    )


def _enter_amount_and_agregar(
    qtbot, window, digits: str, *, nombre: str = "Producto", id_producto: int = None
) -> None:
    """Selecciona producto (UI o draft) a precio=digits y agrega qty 1 (−/+ only)."""
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


def test_plus_minus_and_action_buttons_present(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    assert window.findChild(QObject, "add_button") is None
    assert window.findChild(QObject, "subtract_button") is None
    assert window.findChild(QObject, "pad_panel") is None
    assert window.findChild(QObject, "digit_1") is None
    assert window.findChild(QObject, "borrar_button") is None
    assert _find(window, "agregar_button") is not None
    assert _find(window, "quantity_minus_button") is not None
    assert _find(window, "quantity_plus_button") is not None
    assert _find(window, "borrar_todo_button") is not None
    assert _find(window, "payment_button") is not None
    assert _find(window, "submit_sale_button").text() == "Pagar"


def test_register_layout_two_columns_without_pad(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    assert _find(window, "purchase_panel") is not None
    assert _find(window, "total_separator") is not None
    assert _find(window, "future_panel") is not None
    assert _find(window, "selected_product_panel") is not None
    assert _find(window, "sale_actions_panel") is not None
    assert window.findChild(QObject, "pad_panel") is None
    assert window.findChild(QObject, "sale_display") is None
    submit = _find(window, "submit_sale_button")
    assert submit.text() == "Pagar"


def test_register_layout_purchase_scroll_and_many_lines(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    assert _find(window, "purchase_list_scroll") is not None
    assert window.findChild(QObject, "pad_panel") is None
    assert _find(window, "purchase_list") is not None
    assert _find(window, "left_column") is not None

    for amount in ("1000", "2000", "3000", "4000", "5000", "6000", "7000", "8000"):
        _enter_amount_and_agregar(qtbot, window, amount)
    assert _purchase_list_text(window).count("\n") == 7
    assert _find(window, "purchase_total").text() == "Total: $ 36.000"


def test_agregar_without_http_local_draft(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    after_load = api.request_count

    _select_draft_product(window, precio=500, nombre="Producto")
    _click(qtbot, _find(window, "agregar_button"))
    assert _purchase_list_text(window) == _line_text("Producto", 500)
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
    assert _purchase_list_text(window) == ""


def test_back_preserves_pending_purchase_and_payment(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    _click(qtbot, _find(window, "menu_register_button"))
    _enter_amount_and_agregar(qtbot, window, "5000")
    _select_payment(qtbot, window, 1)

    _click(qtbot, _find(window, "back_button"))
    assert window.centralWidget().currentWidget() is window._menu

    requests_before_reenter = api.request_count
    _click(qtbot, _find(window, "menu_register_button"))
    assert window.centralWidget().currentWidget() is window._register
    assert api.request_count == requests_before_reenter + 3

    assert _purchase_list_text(window) == _line_text("Producto", 5000)
    assert _find(window, "purchase_total").text() == "Total: $ 5.000"
    assert _find(window, "payment_button").text() == "Medio de pago: Efectivo"
    assert _find(window, "submit_sale_button").isEnabled()


def test_agregar_does_not_call_api(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    after_load = api.request_count

    _enter_amount_and_agregar(qtbot, window, "5000")
    _enter_amount_and_agregar(qtbot, window, "2000")

    assert api.request_count == after_load
    assert _purchase_list_text(window) == (
        f"{_line_text('Producto', 5000)}\n{_line_text('Producto', 2000)}"
    )
    assert _find(window, "purchase_total").text() == "Total: $ 7.000"


def test_borrar_todo_clears_cart_keeps_selection(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    after_load = api.request_count

    _enter_amount_and_agregar(qtbot, window, "5000")
    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_1"))
    assert _find(window, "selected_product_label").text() == "Pan"
    assert _find(window, "quantity_label").text() == "1"

    _click(qtbot, _find(window, "borrar_todo_button"))

    assert _purchase_list_text(window) == ""
    assert _find(window, "purchase_total").text() == "Total: $ 0"
    assert _find(window, "selected_product_label").text() == "Pan"
    assert _find(window, "quantity_label").text() == "1"
    assert api.request_count == after_load


def test_submit_disabled_without_value_or_payment(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    submit = _find(window, "submit_sale_button")
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
        and _purchase_list_text(window) == _line_text("Producto", 5000)
        and _find(window, "purchase_total").text() == "Total: $ 5.000"
    )
    assert api.sales == []
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
        lambda: len(api.sales) == 1 and _purchase_list_text(window) == ""
    )

    assert api.sales[0]["valor_total"] == 25000
    assert api.sales[0]["id_medio_pago"] == 1
    assert _purchase_list_text(window) == ""
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
        lambda: len(api.sales) == 1 and _purchase_list_text(window) == ""
    )
    assert api.sales[0]["valor_total"] == 8000


def test_api_error_does_not_show_success_popup(qtbot) -> None:
    class FailingApiClient(FakeApiClient):
        def create_sale(
            self,
            id_medio_pago: int,
            lineas: List[Mapping[str, Any]],
            *,
            id_venta: str,
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
        and _purchase_list_text(window) == _line_text("Producto", 5000)
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
        self,
        id_medio_pago: int,
        lineas: List[Mapping[str, Any]],
        *,
        id_venta: str,
    ) -> Mapping[str, Any]:
        self.request_count += 1
        response = self._client.post(
            "/ventas",
            json={
                "id_venta": id_venta,
                "id_medio_pago": id_medio_pago,
                "lineas": list(lineas),
            },
        )
        response.raise_for_status()
        return response.json()

    def list_sales(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        response = self._client.get("/ventas")
        response.raise_for_status()
        return response.json()

    def get_sale(self, id_venta: str) -> Mapping[str, Any]:
        self.request_count += 1
        response = self._client.get(f"/ventas/{id_venta}")
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
            lambda: sale_count() == 1 and _purchase_list_text(window) == "",
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
