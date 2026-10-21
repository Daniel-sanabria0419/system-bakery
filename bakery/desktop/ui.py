from typing import List, Mapping, Optional

import httpx
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from bakery.app.money import format_cop
from bakery.app.purchase import SaleDraft
from bakery.desktop import style
from bakery.desktop.client import ApiClient
from bakery.persistence.schema import ESTADO_ACTIVO

_PAYMENT_BUTTON_PLACEHOLDER = "Seleccionar medio de pago"
_PAYMENT_METHODS_PER_ROW = 5
_BACK_BUTTON_ARROW = "←"


def _apply_page_layout(layout: QVBoxLayout) -> None:
    layout.setContentsMargins(
        style.PAGE_MARGIN,
        style.PAGE_MARGIN,
        style.PAGE_MARGIN,
        style.PAGE_MARGIN,
    )
    layout.setSpacing(style.PAGE_SPACING)


def _apply_pad_button_size(button: QPushButton) -> None:
    if style.PAD_BUTTON_MIN_WIDTH > 0 or style.PAD_BUTTON_MIN_HEIGHT > 0:
        button.setMinimumSize(style.PAD_BUTTON_MIN_WIDTH, style.PAD_BUTTON_MIN_HEIGHT)


def _apply_dialog_action_button_size(button: QPushButton) -> None:
    if (
        style.DIALOG_ACTION_BUTTON_MIN_WIDTH > 0
        or style.DIALOG_ACTION_BUTTON_MIN_HEIGHT > 0
    ):
        button.setMinimumSize(
            style.DIALOG_ACTION_BUTTON_MIN_WIDTH,
            style.DIALOG_ACTION_BUTTON_MIN_HEIGHT,
        )


def _apply_touch_dialog_layout(dialog: QDialog, layout: QVBoxLayout) -> None:
    layout.setContentsMargins(
        style.DIALOG_CONTENT_MARGIN,
        style.DIALOG_CONTENT_MARGIN,
        style.DIALOG_CONTENT_MARGIN,
        style.DIALOG_CONTENT_MARGIN,
    )
    layout.setSpacing(style.DIALOG_CONTENT_SPACING)
    if style.DIALOG_MIN_WIDTH > 0 or style.DIALOG_MIN_HEIGHT > 0:
        dialog.setMinimumSize(style.DIALOG_MIN_WIDTH, style.DIALOG_MIN_HEIGHT)


def _make_separator(object_name: str) -> QFrame:
    line = QFrame()
    line.setObjectName(object_name)
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Plain)
    line.setFixedHeight(2)
    return line


class SelectPaymentMethodDialog(QDialog):
    """Popup táctil de medios de pago. Solo se cierra al elegir un medio."""

    def __init__(self, methods: List[Mapping], parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("select_payment_dialog")
        self.setWindowTitle("Medio de pago")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self._selected: Optional[Mapping] = None

        layout = QVBoxLayout(self)
        layout.setSpacing(style.PAGE_SPACING)
        grid = QGridLayout()
        grid.setSpacing(style.PAGE_SPACING)

        for index, method in enumerate(methods):
            row, column = divmod(index, _PAYMENT_METHODS_PER_ROW)
            button = QPushButton(method["nombre"])
            button.setObjectName(f"payment_method_{method['id_medio_pago']}")
            style.apply_class(button, "payment-method-button")
            if (
                style.PAYMENT_METHOD_BUTTON_MIN_WIDTH > 0
                or style.PAYMENT_METHOD_BUTTON_MIN_HEIGHT > 0
            ):
                button.setMinimumSize(
                    style.PAYMENT_METHOD_BUTTON_MIN_WIDTH,
                    style.PAYMENT_METHOD_BUTTON_MIN_HEIGHT,
                )
            button.clicked.connect(
                lambda checked=False, m=method: self._choose(m)
            )
            grid.addWidget(button, row, column)

        layout.addLayout(grid)

    def selected_method(self) -> Optional[Mapping]:
        return self._selected

    def _choose(self, method: Mapping) -> None:
        self._selected = method
        self.accept()

    def reject(self) -> None:
        # Escape / rechazo del sistema no cierran sin elegir un medio.
        return


class ConfirmSaleDialog(QDialog):
    def __init__(self, valor_total: int, payment_name: str, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("confirm_dialog")
        self.setWindowTitle("Confirmar venta")

        layout = QVBoxLayout(self)
        _apply_touch_dialog_layout(self, layout)

        value_label = QLabel(f"Valor total: {format_cop(valor_total)}")
        value_label.setObjectName("confirm_value_label")
        style.apply_class(value_label, "dialog-text")
        payment_label = QLabel(f"Medio de pago: {payment_name}")
        payment_label.setObjectName("confirm_payment_label")
        style.apply_class(payment_label, "dialog-text")
        layout.addWidget(value_label)
        layout.addWidget(payment_label)

        buttons = QDialogButtonBox()
        buttons.setCenterButtons(True)

        confirm = buttons.addButton("Confirmar", QDialogButtonBox.AcceptRole)
        confirm.setObjectName("confirm_button")
        style.apply_class(confirm, "dialog-action-button")
        _apply_dialog_action_button_size(confirm)
        cancel = buttons.addButton("No", QDialogButtonBox.RejectRole)
        cancel.setObjectName("cancel_button")
        style.apply_class(cancel, "dialog-action-button")
        _apply_dialog_action_button_size(cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class SaleSavedDialog(QDialog):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("sale_saved_dialog")
        self.setWindowTitle("Venta guardada")

        layout = QVBoxLayout(self)
        _apply_touch_dialog_layout(self, layout)

        message = QLabel("Venta guardada correctamente")
        message.setObjectName("sale_saved_message")
        style.apply_class(message, "dialog-text")
        layout.addWidget(message)

        buttons = QDialogButtonBox()
        buttons.setCenterButtons(True)

        ok = buttons.addButton("Aceptar", QDialogButtonBox.AcceptRole)
        ok.setObjectName("sale_saved_ok_button")
        style.apply_class(ok, "dialog-action-button")
        _apply_dialog_action_button_size(ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class MenuPage(QWidget):
    def __init__(self, on_register, on_products) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(
            style.MENU_MARGIN,
            style.MENU_MARGIN,
            style.MENU_MARGIN,
            style.MENU_MARGIN,
        )
        root.setSpacing(style.PAGE_SPACING)

        menu_grid = QWidget()
        menu_grid.setObjectName("menu_grid")
        grid = QGridLayout(menu_grid)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(style.PAGE_SPACING)

        register_button = QPushButton("Registrar venta")
        register_button.setObjectName("menu_register_button")
        style.apply_class(register_button, "menu-button")
        register_button.clicked.connect(on_register)
        grid.addWidget(register_button, 0, 0, Qt.AlignLeft | Qt.AlignTop)

        products_button = QPushButton("Productos")
        products_button.setObjectName("menu_products_button")
        style.apply_class(products_button, "menu-button")
        products_button.clicked.connect(on_products)
        grid.addWidget(products_button, 0, 1, Qt.AlignLeft | Qt.AlignTop)

        grid.setColumnStretch(2, 1)
        grid.setRowStretch(1, 1)

        root.addWidget(menu_grid, stretch=1)


class RegisterSalePage(QWidget):
    def __init__(self, api_client: ApiClient, on_back=None) -> None:
        super().__init__()
        self._api = api_client
        self._draft = SaleDraft()
        self._payment_methods: List[Mapping] = []
        self._selected_payment_id: Optional[int] = None
        self._selected_payment_name: Optional[str] = None

        root = QVBoxLayout(self)
        _apply_page_layout(root)

        top_bar = QHBoxLayout()
        back = QPushButton(_BACK_BUTTON_ARROW)
        back.setObjectName("back_button")
        style.apply_class(back, "back-button")
        back.setMinimumSize(
            style.BACK_BUTTON_MIN_WIDTH,
            style.BACK_BUTTON_MIN_HEIGHT,
        )
        back.setToolTip("Volver")
        if on_back is not None:
            back.clicked.connect(on_back)
        top_bar.addWidget(back)
        top_bar.addStretch(1)

        root.addLayout(top_bar)

        columns = QHBoxLayout()
        columns.setSpacing(style.PAGE_SPACING)

        left = QWidget()
        left.setObjectName("left_column")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(style.PAGE_SPACING)

        purchase_panel = QWidget()
        purchase_panel.setObjectName("purchase_panel")
        panel_layout = QVBoxLayout(purchase_panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(8)

        self._display = QLabel("")
        self._display.setObjectName("sale_display")
        self._display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        style.apply_class(self._display, "money-text")
        panel_layout.addWidget(self._display)

        panel_layout.addWidget(_make_separator("entry_separator"))

        self._purchase_list = QLabel("")
        self._purchase_list.setObjectName("purchase_list")
        self._purchase_list.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self._purchase_list.setWordWrap(False)
        self._purchase_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        style.apply_class(self._purchase_list, "money-text")

        self._purchase_list_scroll = QScrollArea()
        self._purchase_list_scroll.setObjectName("purchase_list_scroll")
        self._purchase_list_scroll.setWidgetResizable(False)
        self._purchase_list_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._purchase_list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._purchase_list_scroll.setFrameShape(QFrame.NoFrame)
        self._purchase_list_scroll.setWidget(self._purchase_list)
        panel_layout.addWidget(self._purchase_list_scroll, stretch=1)

        panel_layout.addWidget(_make_separator("total_separator"))

        footer = QHBoxLayout()
        self._payment_button = QPushButton(_PAYMENT_BUTTON_PLACEHOLDER)
        self._payment_button.setObjectName("payment_button")
        style.apply_class(self._payment_button, "payment-button")
        self._payment_button.clicked.connect(self._open_payment_dialog)
        footer.addWidget(self._payment_button, stretch=1)

        self._purchase_total = QLabel("")
        self._purchase_total.setObjectName("purchase_total")
        self._purchase_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        style.apply_class(self._purchase_total, "money-text")
        footer.addWidget(self._purchase_total)
        panel_layout.addLayout(footer)

        left_layout.addWidget(purchase_panel, style.PURCHASE_PANEL_STRETCH)

        pad_panel = QWidget()
        pad_panel.setObjectName("pad_panel")
        pad = QGridLayout(pad_panel)
        pad.setContentsMargins(0, 0, 0, 0)
        pad.setSpacing(style.PAD_SPACING)
        pad_buttons = [
            ("1", 0, 0, 1, 1, "digit"),
            ("2", 0, 1, 1, 1, "digit"),
            ("3", 0, 2, 1, 1, "digit"),
            ("Borrar", 0, 3, 1, 1, "borrar"),
            ("4", 1, 0, 1, 1, "digit"),
            ("5", 1, 1, 1, 1, "digit"),
            ("6", 1, 2, 1, 1, "digit"),
            ("C", 1, 3, 1, 1, "clear"),
            ("7", 2, 0, 1, 1, "digit"),
            ("8", 2, 1, 1, 1, "digit"),
            ("9", 2, 2, 1, 1, "digit"),
            ("Pago", 2, 3, 2, 1, "pago"),
            ("0", 3, 0, 1, 1, "digit"),
            ("00", 3, 1, 1, 1, "zeros"),
            ("Agregar", 3, 2, 1, 1, "agregar"),
        ]
        for text, row, column, row_span, col_span, kind in pad_buttons:
            button = QPushButton(text)
            button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            _apply_pad_button_size(button)
            style.apply_class(button, "pad-button")
            if kind == "digit":
                button.setObjectName(f"digit_{text}")
                button.clicked.connect(lambda checked=False, d=text: self._digit(d))
            elif kind == "zeros":
                button.setObjectName("digit_00")
                button.clicked.connect(lambda: self._action("zeros"))
            elif kind == "agregar":
                button.setObjectName("agregar_button")
                button.clicked.connect(lambda: self._action("agregar"))
            elif kind == "clear":
                button.setObjectName("clear_button")
                button.clicked.connect(lambda: self._action("clear"))
            elif kind == "borrar":
                button.setObjectName("borrar_button")
                button.clicked.connect(lambda: self._action("borrar"))
            elif kind == "pago":
                button.setObjectName("submit_sale_button")
                button.clicked.connect(self._on_submit)
                
                self._submit = button
            pad.addWidget(button, row, column, row_span, col_span)

        left_layout.addWidget(pad_panel, style.PAD_PANEL_STRETCH)

        future = QWidget()
        future.setObjectName("future_panel")
        future.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        columns.addWidget(left, style.LEFT_COLUMN_STRETCH)
        columns.addWidget(future, style.RIGHT_COLUMN_STRETCH)
        root.addLayout(columns, stretch=1)

        self._refresh_display()
        self._refresh_submit()

    def load_payment_methods(self) -> None:
        selected_id = self._selected_payment_id
        self._payment_methods = list(self._api.list_payment_methods())
        if selected_id is not None:
            match = next(
                (
                    method
                    for method in self._payment_methods
                    if method["id_medio_pago"] == selected_id
                ),
                None,
            )
            if match is None:
                self._clear_payment_selection()
            else:
                self._selected_payment_name = match["nombre"]
                self._update_payment_button_text()
        self._refresh_submit()

    def reset_form(self) -> None:
        self._draft.clear_purchase()
        self._clear_payment_selection()
        self._refresh_display()
        self._refresh_submit()

    def _open_payment_dialog(self) -> None:
        dialog = SelectPaymentMethodDialog(self._payment_methods, self)
        if dialog.exec() != QDialog.Accepted:
            return
        method = dialog.selected_method()
        if method is None:
            return
        self._selected_payment_id = method["id_medio_pago"]
        self._selected_payment_name = method["nombre"]
        self._update_payment_button_text()
        self._refresh_submit()

    def _clear_payment_selection(self) -> None:
        self._selected_payment_id = None
        self._selected_payment_name = None
        self._update_payment_button_text()

    def _update_payment_button_text(self) -> None:
        if self._selected_payment_name:
            self._payment_button.setText(
                f"Medio de pago: {self._selected_payment_name}"
            )
        else:
            self._payment_button.setText(_PAYMENT_BUTTON_PLACEHOLDER)

    def _digit(self, digit: str) -> None:
        self._draft.entry.press_digit(digit)
        self._refresh_display()
        self._refresh_submit()

    def _action(self, name: str) -> None:
        if name == "agregar":
            # Etapa 5: exige producto seleccionado en el draft (UI de selección = Etapa 7).
            self._draft.add_to_purchase()
        elif name == "clear":
            self._draft.clear_purchase()
        elif name == "borrar":
            self._draft.entry.backspace()
        elif name == "zeros":
            self._draft.entry.press_zeros()
        self._refresh_display()
        self._refresh_submit()

    def _refresh_display(self) -> None:
        self._display.setText(self._draft.entry.display_text())
        items = self._draft.purchase.items()
        self._purchase_list.setText(
            "\n".join(
                f"{line.nombre} × {line.cantidad} — {format_cop(line.subtotal)}"
                for line in items
            )
        )
        viewport_width = self._purchase_list_scroll.viewport().width()
        if viewport_width > 0:
            self._purchase_list.setFixedWidth(viewport_width)
        self._purchase_list.adjustSize()
        self._purchase_list.setMinimumHeight(self._purchase_list.sizeHint().height())
        total = self._draft.total()
        if total > 0:
            self._purchase_total.setText(f"Total: {format_cop(total)}")
        else:
            self._purchase_total.setText("Total: $0.00")

    def _refresh_submit(self) -> None:
        ready = self._draft.total() > 0 and self._selected_payment_id is not None
        self._submit.setEnabled(ready)

    def _on_submit(self) -> None:
        value = self._draft.total()
        payment_id = self._selected_payment_id
        if value <= 0 or payment_id is None or not self._selected_payment_name:
            return
        dialog = ConfirmSaleDialog(value, self._selected_payment_name, self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            self._api.create_sale(value, payment_id)
        except httpx.HTTPError as error:
            QMessageBox.warning(self, "Error", f"No se pudo guardar la venta.\n{error}")
            return
        SaleSavedDialog(self).exec()
        self.reset_form()


class ProductFormDialog(QDialog):
    """Crear o editar producto. La validación de negocio la hace la API."""

    def __init__(
        self,
        categories: List[Mapping],
        parent: QWidget = None,
        *,
        product: Optional[Mapping] = None,
    ) -> None:
        super().__init__(parent)
        self._product = product
        self.setObjectName("product_form_dialog")
        self.setWindowTitle("Editar producto" if product else "Nuevo producto")
        self.setModal(True)

        layout = QVBoxLayout(self)
        _apply_touch_dialog_layout(self, layout)

        self._nombre = QLineEdit()
        self._nombre.setObjectName("product_nombre_input")
        self._nombre.setPlaceholderText("Nombre")
        layout.addWidget(self._nombre)

        self._precio = QLineEdit()
        self._precio.setObjectName("product_precio_input")
        self._precio.setPlaceholderText("Precio (entero)")
        layout.addWidget(self._precio)

        self._categoria = QComboBox()
        self._categoria.setObjectName("product_categoria_combo")
        for category in categories:
            self._categoria.addItem(category["nombre"], category["id_categoria"])
        layout.addWidget(self._categoria)

        self._descripcion = QLineEdit()
        self._descripcion.setObjectName("product_descripcion_input")
        self._descripcion.setPlaceholderText("Descripción (opcional)")
        layout.addWidget(self._descripcion)

        self._estado_label = QLabel("")
        self._estado_label.setObjectName("product_estado_label")
        style.apply_class(self._estado_label, "dialog-text")
        layout.addWidget(self._estado_label)

        if product is not None:
            self._nombre.setText(product["nombre"])
            self._precio.setText(str(product["precio"]))
            index = self._categoria.findData(product["id_categoria"])
            if index >= 0:
                self._categoria.setCurrentIndex(index)
            self._descripcion.setText(product.get("descripcion") or "")
            estado = (
                "Activo"
                if product.get("id_estado") == ESTADO_ACTIVO
                else "Inactivo"
            )
            self._estado_label.setText(f"Estado: {estado}")
        else:
            self._estado_label.setText("Estado: Activo")

        buttons = QDialogButtonBox()
        buttons.setCenterButtons(True)
        save = buttons.addButton("Guardar", QDialogButtonBox.AcceptRole)
        save.setObjectName("product_save_button")
        style.apply_class(save, "dialog-action-button")
        _apply_dialog_action_button_size(save)
        cancel = buttons.addButton("Cancelar", QDialogButtonBox.RejectRole)
        cancel.setObjectName("product_cancel_button")
        style.apply_class(cancel, "dialog-action-button")
        _apply_dialog_action_button_size(cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def form_values(self) -> Optional[Mapping]:
        nombre = self._nombre.text().strip()
        precio_text = self._precio.text().strip()
        if not precio_text.isdigit() or int(precio_text) <= 0:
            return None
        precio = int(precio_text)
        descripcion = self._descripcion.text().strip() or None
        return {
            "nombre": nombre,
            "precio": precio,
            "id_categoria": self._categoria.currentData(),
            "descripcion": descripcion,
        }


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
            self._api.create_product(**values)
        except httpx.HTTPError as error:
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
            self._api.update_product(product["id_producto"], **values)
        except httpx.HTTPError as error:
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


class MainWindow(QMainWindow):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.setWindowTitle("Panadería")
        self.showFullScreen()
        self._api = api_client

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._menu = MenuPage(self.open_register_sale, self.open_products)
        self._register = RegisterSalePage(api_client, on_back=self.go_back_to_menu)
        self._products = ProductsPage(api_client, on_back=self.go_back_to_menu)
        self._stack.addWidget(self._menu)
        self._stack.addWidget(self._register)
        self._stack.addWidget(self._products)
        self._stack.setCurrentWidget(self._menu)

    def open_register_sale(self) -> None:
        self._register.load_payment_methods()
        self._stack.setCurrentWidget(self._register)

    def open_products(self) -> None:
        self._products.reload()
        self._stack.setCurrentWidget(self._products)

    def go_back_to_menu(self) -> None:
        self._stack.setCurrentWidget(self._menu)
