from typing import Any, List, Mapping, Optional

from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtWidgets import QApplication, QDialog

from bakery.desktop.main import create_window
from bakery.desktop.ui import ProductFormDialog
from bakery.persistence.schema import ESTADO_ACTIVO, ESTADO_INACTIVO, SEED_CATEGORIAS


class FakeProductsApiClient:
    def __init__(self) -> None:
        self.request_count = 0
        self.methods = [
            {"id_medio_pago": 1, "nombre": "Efectivo", "id_estado": 1},
        ]
        self.categories = [
            {"id_categoria": index + 1, "nombre": name}
            for index, name in enumerate(SEED_CATEGORIAS)
        ]
        self.products: List[Mapping[str, Any]] = []
        self._next_id = 1
        self.sales: List[Mapping[str, Any]] = []

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

    def list_categories(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        return list(self.categories)

    def list_products(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        return [dict(product) for product in self.products]

    def create_product(
        self,
        *,
        nombre: str,
        precio: int,
        id_categoria: int,
        descripcion: Optional[str] = None,
    ) -> Mapping[str, Any]:
        self.request_count += 1
        product = {
            "id_producto": self._next_id,
            "nombre": nombre,
            "precio": precio,
            "id_categoria": id_categoria,
            "descripcion": descripcion,
            "id_estado": ESTADO_ACTIVO,
        }
        self._next_id += 1
        self.products.append(product)
        return dict(product)

    def update_product(
        self,
        id_producto: int,
        *,
        nombre: str,
        precio: int,
        id_categoria: int,
        descripcion: Optional[str] = None,
    ) -> Mapping[str, Any]:
        self.request_count += 1
        for index, product in enumerate(self.products):
            if product["id_producto"] == id_producto:
                updated = {
                    **product,
                    "nombre": nombre,
                    "precio": precio,
                    "id_categoria": id_categoria,
                    "descripcion": descripcion,
                }
                self.products[index] = updated
                return dict(updated)
        raise AssertionError(f"Producto {id_producto} no existe")

    def activate_product(self, id_producto: int) -> Mapping[str, Any]:
        return self._set_estado(id_producto, ESTADO_ACTIVO)

    def deactivate_product(self, id_producto: int) -> Mapping[str, Any]:
        return self._set_estado(id_producto, ESTADO_INACTIVO)

    def _set_estado(self, id_producto: int, id_estado: int) -> Mapping[str, Any]:
        self.request_count += 1
        for index, product in enumerate(self.products):
            if product["id_producto"] == id_producto:
                updated = {**product, "id_estado": id_estado}
                self.products[index] = updated
                return dict(updated)
        raise AssertionError(f"Producto {id_producto} no existe")


def _click(qtbot, widget) -> None:
    qtbot.mouseClick(widget, Qt.LeftButton)


def _find(window, name: str):
    widget = window.findChild(QObject, name)
    assert widget is not None, f"No se encontró {name}"
    return widget


def _fill_and_save_product_dialog(
    *,
    nombre: str,
    precio: str,
    id_categoria: int = 1,
    descripcion: str = "",
) -> None:
    def fill() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ProductFormDialog) and widget.isVisible():
                widget.findChild(QObject, "product_nombre_input").setText(nombre)
                widget.findChild(QObject, "product_precio_input").setText(precio)
                combo = widget.findChild(QObject, "product_categoria_combo")
                index = combo.findData(id_categoria)
                assert index >= 0
                combo.setCurrentIndex(index)
                widget.findChild(QObject, "product_descripcion_input").setText(
                    descripcion
                )
                widget.findChild(QObject, "product_save_button").click()
                return
        QTimer.singleShot(20, fill)

    QTimer.singleShot(50, fill)


def test_menu_opens_products_and_back(qtbot) -> None:
    api = FakeProductsApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    products_button = _find(window, "menu_products_button")
    assert products_button.text() == "Productos"
    assert api.request_count == 0

    _click(qtbot, products_button)
    assert window._stack.currentWidget() is window._products
    assert _find(window, "products_page") is not None
    assert api.request_count >= 2  # categories + products

    _click(qtbot, _find(window, "products_back_button"))
    assert window._stack.currentWidget() is window._menu


def test_create_edit_deactivate_product_via_ui(qtbot) -> None:
    api = FakeProductsApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    _click(qtbot, _find(window, "menu_products_button"))

    _fill_and_save_product_dialog(
        nombre="Pan de queso",
        precio="3000",
        id_categoria=1,
        descripcion="fresco",
    )
    _click(qtbot, _find(window, "new_product_button"))
    qtbot.waitUntil(lambda: len(api.products) == 1, timeout=2000)

    assert api.products[0]["nombre"] == "Pan de queso"
    assert api.products[0]["precio"] == 3000
    assert _find(window, "product_row_1") is not None

    _fill_and_save_product_dialog(
        nombre="Pan integral",
        precio="3500",
        id_categoria=2,
        descripcion="",
    )
    _click(qtbot, _find(window, "edit_product_1"))
    qtbot.waitUntil(
        lambda: api.products and api.products[0]["nombre"] == "Pan integral",
        timeout=2000,
    )
    assert api.products[0]["precio"] == 3500
    assert api.products[0]["id_categoria"] == 2

    _click(qtbot, _find(window, "deactivate_product_1"))
    qtbot.waitUntil(
        lambda: api.products[0]["id_estado"] == ESTADO_INACTIVO,
        timeout=2000,
    )
    assert _find(window, "activate_product_1") is not None


def test_register_sale_still_opens_from_menu(qtbot) -> None:
    api = FakeProductsApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    _click(qtbot, _find(window, "menu_register_button"))
    assert window._stack.currentWidget() is window._register
    assert _find(window, "submit_sale_button") is not None
    assert api.sales == []
