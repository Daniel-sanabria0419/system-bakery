"""Página Productos (listado / CRUD UI)."""

from pathlib import Path
from typing import List, Mapping, Optional

import httpx
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from bakery.app.money import format_cop
from bakery.app.product_images import save_product_image
from bakery.desktop import style
from bakery.desktop.client import ApiClient
from bakery.desktop.dialogs import ProductFormDialog
from bakery.desktop.ui_helpers import _BACK_BUTTON_ARROW, _apply_page_layout
from bakery.persistence.schema import ESTADO_ACTIVO

class ProductsPage(QWidget):
    def __init__(self, api_client: ApiClient, on_back=None) -> None:
        super().__init__()
        self.setObjectName("products_page")
        self._api = api_client
        self._categories: List[Mapping] = []
        self._category_names: Mapping[int, str] = {}

        root = QVBoxLayout(self)
        _apply_page_layout(root)

        top_bar = QHBoxLayout()
        back = QPushButton(_BACK_BUTTON_ARROW)
        back.setObjectName("products_back_button")
        style.apply_class(back, "back-button")
        back.setMinimumSize(
            style.BACK_BUTTON_MIN_WIDTH,
            style.BACK_BUTTON_MIN_HEIGHT,
        )
        back.setToolTip("Volver")
        if on_back is not None:
            back.clicked.connect(on_back)
        top_bar.addWidget(back)

        title = QLabel("Productos")
        title.setObjectName("products_title")
        style.apply_class(title, "dialog-text")
        top_bar.addWidget(title)
        top_bar.addStretch(1)

        new_button = QPushButton("Nuevo producto")
        new_button.setObjectName("new_product_button")
        style.apply_class(new_button, "menu-button")
        new_button.clicked.connect(self._on_new_product)
        top_bar.addWidget(new_button)
        root.addLayout(top_bar)

        self._list_host = QWidget()
        self._list_host.setObjectName("products_list")
        self._list_layout = QVBoxLayout(self._list_host)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(style.PAGE_SPACING)
        self._list_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setObjectName("products_list_scroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self._list_host)
        root.addWidget(scroll, stretch=1)

    def reload(self) -> None:
        self._categories = list(self._api.list_categories())
        self._category_names = {
            category["id_categoria"]: category["nombre"]
            for category in self._categories
        }
        products = list(self._api.list_products())
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for product in products:
            self._list_layout.addWidget(self._make_row(product))
        self._list_layout.addStretch(1)

    def _make_row(self, product: Mapping) -> QWidget:
        row = QWidget()
        row.setObjectName(f"product_row_{product['id_producto']}")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(style.PAGE_SPACING)

        estado = "Activo" if product["id_estado"] == ESTADO_ACTIVO else "Inactivo"
        categoria = self._category_names.get(product["id_categoria"], "?")
        descripcion = product.get("descripcion") or ""
        summary = (
            f"{product['nombre']} — {format_cop(product['precio'])} — "
            f"{categoria} — {estado}"
        )
        if descripcion:
            summary = f"{summary} — {descripcion}"
        label = QLabel(summary)
        label.setObjectName(f"product_summary_{product['id_producto']}")
        label.setWordWrap(True)
        layout.addWidget(label, stretch=1)

        edit = QPushButton("Editar")
        edit.setObjectName(f"edit_product_{product['id_producto']}")
        style.apply_class(edit, "payment-method-button")
        edit.clicked.connect(
            lambda checked=False, p=product: self._on_edit_product(p)
        )
        layout.addWidget(edit)

        if product["id_estado"] == ESTADO_ACTIVO:
            toggle = QPushButton("Desactivar")
            toggle.setObjectName(f"deactivate_product_{product['id_producto']}")
            toggle.clicked.connect(
                lambda checked=False, pid=product["id_producto"]: self._on_deactivate(
                    pid
                )
            )
        else:
            toggle = QPushButton("Activar")
            toggle.setObjectName(f"activate_product_{product['id_producto']}")
            toggle.clicked.connect(
                lambda checked=False, pid=product["id_producto"]: self._on_activate(pid)
            )
        style.apply_class(toggle, "payment-method-button")
        layout.addWidget(toggle)
        return row

    def _persist_product_image(
        self, id_producto: int, source: Path, values: Mapping
    ) -> None:
        relative = save_product_image(int(id_producto), source)
        self._api.update_product(
            id_producto,
            nombre=values["nombre"],
            precio=values["precio"],
            id_categoria=values["id_categoria"],
            descripcion=values.get("descripcion"),
            ruta_imagen=relative,
            actualizar_ruta_imagen=True,
        )

    def _on_new_product(self) -> None:
        dialog = ProductFormDialog(self._categories, self)
        if dialog.exec() != QDialog.Accepted:
            return
        values = dialog.form_values()
        if values is None or not values["nombre"]:
            QMessageBox.warning(
                self, "Error", "Nombre obligatorio y precio entero mayor que 0."
            )
            return
        try:
            created = self._api.create_product(**values)
            if dialog.image_changed() and dialog.pending_image_path() is not None:
                self._persist_product_image(
                    created["id_producto"],
                    dialog.pending_image_path(),
                    values,
                )
        except (httpx.HTTPError, ValueError, OSError) as error:
            QMessageBox.warning(
                self, "Error", f"No se pudo crear el producto.\n{error}"
            )
            return
        self.reload()

    def _on_edit_product(self, product: Mapping) -> None:
        dialog = ProductFormDialog(self._categories, self, product=product)
        if dialog.exec() != QDialog.Accepted:
            return
        values = dialog.form_values()
        if values is None or not values["nombre"]:
            QMessageBox.warning(
                self, "Error", "Nombre obligatorio y precio entero mayor que 0."
            )
            return
        try:
            if dialog.image_changed() and dialog.pending_image_path() is not None:
                self._persist_product_image(
                    product["id_producto"],
                    dialog.pending_image_path(),
                    values,
                )
            else:
                self._api.update_product(
                    product["id_producto"],
                    **values,
                    actualizar_ruta_imagen=False,
                )
        except (httpx.HTTPError, ValueError, OSError) as error:
            QMessageBox.warning(
                self, "Error", f"No se pudo actualizar el producto.\n{error}"
            )
            return
        self.reload()

    def _on_activate(self, id_producto: int) -> None:
        try:
            self._api.activate_product(id_producto)
        except httpx.HTTPError as error:
            QMessageBox.warning(
                self, "Error", f"No se pudo activar el producto.\n{error}"
            )
            return
        self.reload()

    def _on_deactivate(self, id_producto: int) -> None:
        try:
            self._api.deactivate_product(id_producto)
        except httpx.HTTPError as error:
            QMessageBox.warning(
                self, "Error", f"No se pudo desactivar el producto.\n{error}"
            )
            return
        self.reload()

