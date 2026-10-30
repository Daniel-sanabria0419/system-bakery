from typing import Any, List, Mapping, Optional

from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtWidgets import QApplication, QDialog

from bakery.desktop import style
from bakery.desktop.main import create_window
from bakery.desktop.style import load_theme_qss
from bakery.desktop.ui import ProductFormDialog
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    ESTADO_INACTIVO,
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    SEED_CATEGORIAS,
)


class FakeProductsApiClient:
    def __init__(self) -> None:
        self.request_count = 0
        self.methods = [
            {"id_medio_pago": 1, "nombre": "Efectivo", "id_estado": 1},
        ]
        category_names = list(SEED_CATEGORIAS) + [NOMBRE_CATEGORIA_PAN_PEQUENO]
        self.categories = [
            {"id_categoria": index + 1, "nombre": name}
            for index, name in enumerate(category_names)
        ]
        self.products: List[Mapping[str, Any]] = []
        self._next_id = 1
        self.sales: List[Mapping[str, Any]] = []

    def list_payment_methods(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        return list(self.methods)

    def create_sale(
        self,
        id_medio_pago: int,
        lineas: List[Mapping[str, Any]],
        *,
        id_venta: str,
    ) -> Mapping[str, Any]:
        self.request_count += 1
        valor_total = sum(
            int(line["precio_aplicado"]) * int(line["cantidad"]) for line in lineas
        )
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

    def list_categories(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        return list(self.categories)

    def list_products(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        return [dict(product) for product in self.products]

    def list_active_products(
        self,
        *,
        id_categoria: Optional[int] = None,
        precio: Optional[int] = None,
    ) -> List[Mapping[str, Any]]:
        self.request_count += 1
        rows = [p for p in self.products if p["id_estado"] == ESTADO_ACTIVO]
        if id_categoria is not None:
            rows = [p for p in rows if p["id_categoria"] == id_categoria]
        if precio is not None:
            rows = [p for p in rows if p["precio"] == precio]
        return [dict(p) for p in rows]

    def create_product(
        self,
        *,
        nombre: str,
        precio: int,
        id_categoria: int,
        descripcion: Optional[str] = None,
        ruta_imagen: Optional[str] = None,
    ) -> Mapping[str, Any]:
        self.request_count += 1
        product = {
            "id_producto": self._next_id,
            "nombre": nombre,
            "precio": precio,
            "id_categoria": id_categoria,
            "descripcion": descripcion,
            "id_estado": ESTADO_ACTIVO,
            "ruta_imagen": ruta_imagen,
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
        ruta_imagen: Optional[str] = None,
        actualizar_ruta_imagen: bool = False,
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
                if actualizar_ruta_imagen:
                    updated["ruta_imagen"] = ruta_imagen
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


def test_products_list_background_is_white(qtbot) -> None:
    """Etapa 5: listado Productos blanco; payment-method-button sigue negro."""
    assert style.PRODUCTS_LIST_BACKGROUND == "#FFFFFF"
    qss = load_theme_qss()
    assert "QWidget#products_list" in qss
    assert "QScrollArea#products_list_scroll" in qss
    products_block = qss.split("QWidget#products_page")[1].split(
        "QLabel[class=\"dialog-text\"]"
    )[0]
    assert "background-color: #FFFFFF" in products_block
    assert (
        'QPushButton[class="payment-method-button"]' in qss
        and "background-color: #1A1A1A" in qss
    )

    api = FakeProductsApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_products_button"))
    assert _find(window, "products_page") is not None
    assert _find(window, "products_list") is not None
    assert _find(window, "products_list_scroll") is not None
