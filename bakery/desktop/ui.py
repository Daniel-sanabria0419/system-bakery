from pathlib import Path
from typing import List, Mapping, Optional

import httpx
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
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
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from bakery.app.money import format_cop
from bakery.app.product_images import (
    category_image_path,
    resolve_relative_image,
    save_product_image,
)
from bakery.app.purchase import SaleDraft, candidates_by_exact_price
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


def _apply_catalog_chip_icon(button: QToolButton, image_path: Optional[Path]) -> None:
    if image_path is None:
        button.setIcon(QIcon())
        return
    button.setIcon(QIcon(str(image_path)))
    button.setIconSize(QSize(36, 28))


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
        self._categories: List[Mapping] = []
        self._active_products: List[Mapping] = []
        self._selected_category_id: Optional[int] = None

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

        catalog = QWidget()
        catalog.setObjectName("future_panel")
        catalog.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        catalog_layout = QVBoxLayout(catalog)
        catalog_layout.setContentsMargins(8, 8, 8, 8)
        catalog_layout.setSpacing(style.PAGE_SPACING)

        self._selection_label = QLabel("Sin producto seleccionado")
        self._selection_label.setObjectName("selected_product_label")
        self._selection_label.setWordWrap(True)
        catalog_layout.addWidget(self._selection_label)

        self._feedback = QLabel("")
        self._feedback.setObjectName("sale_feedback")
        self._feedback.setWordWrap(True)
        catalog_layout.addWidget(self._feedback)

        qty_section = QWidget()
        qty_section.setObjectName("quantity_section")
        qty_section_layout = QVBoxLayout(qty_section)
        qty_section_layout.setContentsMargins(0, 0, 0, 0)
        qty_section_layout.setSpacing(style.PAGE_SPACING)

        qty_row = QHBoxLayout()
        qty_caption = QLabel("Cantidad")
        qty_caption.setObjectName("quantity_caption")
        qty_row.addWidget(qty_caption)
        minus = QPushButton("−")
        minus.setObjectName("quantity_minus_button")
        style.apply_class(minus, "payment-method-button")
        minus.clicked.connect(self._quantity_minus)
        qty_row.addWidget(minus)
        self._quantity_label = QLabel("1")
        self._quantity_label.setObjectName("quantity_label")
        self._quantity_label.setAlignment(Qt.AlignCenter)
        qty_row.addWidget(self._quantity_label)
        plus = QPushButton("+")
        plus.setObjectName("quantity_plus_button")
        style.apply_class(plus, "payment-method-button")
        plus.clicked.connect(self._quantity_plus)
        qty_row.addWidget(plus)
        self._quantity_value_label = QLabel("")
        self._quantity_value_label.setObjectName("quantity_value_label")
        qty_row.addWidget(self._quantity_value_label)
        qty_row.addStretch(1)
        qty_section_layout.addLayout(qty_row)

        self._value_preview_label = QLabel("")
        self._value_preview_label.setObjectName("sale_value_preview")
        self._value_preview_label.setWordWrap(True)
        qty_section_layout.addWidget(self._value_preview_label)
        catalog_layout.addWidget(qty_section)

        catalog_layout.addWidget(QLabel("Categorías"))
        self._categories_host = QWidget()
        self._categories_host.setObjectName("categories_list")
        self._categories_layout = QVBoxLayout(self._categories_host)
        self._categories_layout.setContentsMargins(0, 0, 0, 0)
        self._categories_layout.setSpacing(style.PAGE_SPACING)
        categories_scroll = QScrollArea()
        categories_scroll.setObjectName("categories_scroll")
        categories_scroll.setWidgetResizable(True)
        categories_scroll.setFrameShape(QFrame.NoFrame)
        categories_scroll.setWidget(self._categories_host)
        catalog_layout.addWidget(categories_scroll, stretch=1)

        catalog_layout.addWidget(QLabel("Productos"))
        self._products_host = QWidget()
        self._products_host.setObjectName("sale_products_list")
        self._products_layout = QVBoxLayout(self._products_host)
        self._products_layout.setContentsMargins(0, 0, 0, 0)
        self._products_layout.setSpacing(style.PAGE_SPACING)
        products_scroll = QScrollArea()
        products_scroll.setObjectName("sale_products_scroll")
        products_scroll.setWidgetResizable(True)
        products_scroll.setFrameShape(QFrame.NoFrame)
        products_scroll.setWidget(self._products_host)
        catalog_layout.addWidget(products_scroll, stretch=2)

        self._search_caption = QLabel("Búsqueda por precio")
        self._search_caption.setObjectName("price_search_caption")
        catalog_layout.addWidget(self._search_caption)
        self._search_host = QWidget()
        self._search_host.setObjectName("price_search_list")
        self._search_layout = QVBoxLayout(self._search_host)
        self._search_layout.setContentsMargins(0, 0, 0, 0)
        self._search_layout.setSpacing(style.PAGE_SPACING)
        self._search_scroll = QScrollArea()
        self._search_scroll.setObjectName("price_search_scroll")
        self._search_scroll.setWidgetResizable(True)
        self._search_scroll.setFrameShape(QFrame.NoFrame)
        self._search_scroll.setWidget(self._search_host)
        catalog_layout.addWidget(self._search_scroll, stretch=1)

        columns.addWidget(left, style.LEFT_COLUMN_STRETCH)
        columns.addWidget(catalog, style.RIGHT_COLUMN_STRETCH)
        root.addLayout(columns, stretch=1)

        self._refresh_display()
        self._refresh_submit()
        self._refresh_selection_ui()
        self._sync_quantity_section()
        self._refresh_mode_ui()

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

    def load_catalog(self) -> None:
        self._categories = list(self._api.list_categories())
        self._active_products = list(self._api.list_active_products())
        self._rebuild_categories()
        self._rebuild_products()
        self._rebuild_search()
        self._refresh_selection_ui()
        self._sync_quantity_section()
        self._refresh_mode_ui()

    def reset_form(self) -> None:
        self._draft.clear_purchase()
        self._clear_payment_selection()
        self._selected_category_id = None
        self._feedback.setText("")
        self._rebuild_categories()
        self._rebuild_products()
        self._rebuild_search()
        self._refresh_display()
        self._refresh_selection_ui()
        self._sync_quantity_section()
        self._refresh_mode_ui()
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
        self._feedback.setText("")
        self._on_entry_changed()
        self._refresh_display()
        self._refresh_submit()

    def _action(self, name: str) -> None:
        if name == "agregar":
            if self._draft.selected_product() is None:
                self._feedback.setText(
                    "Seleccione un producto antes de agregar."
                )
            elif not self._draft.add_to_purchase():
                self._feedback.setText("No se pudo agregar la línea.")
            else:
                self._feedback.setText("")
                self._refresh_selection_ui()
                self._sync_quantity_section()
                self._refresh_mode_ui()
                self._rebuild_search()
        elif name == "clear":
            self._draft.clear_purchase()
            self._selected_category_id = None
            self._feedback.setText("")
            self._rebuild_categories()
            self._rebuild_products()
            self._rebuild_search()
            self._refresh_selection_ui()
            self._sync_quantity_section()
            self._refresh_mode_ui()
        elif name == "borrar":
            self._draft.entry.backspace()
            self._feedback.setText("")
            self._on_entry_changed()
        elif name == "zeros":
            self._draft.entry.press_zeros()
            self._feedback.setText("")
            self._on_entry_changed()
        self._refresh_display()
        self._refresh_submit()

    def _on_entry_changed(self) -> None:
        """Tras dígitos: Pan pequeño convierte valor→cantidad; si no, busca precio."""
        if self._draft.selected_is_pan_pequeno():
            amount = self._draft.entry.current_amount()
            if amount is not None and amount > 0:
                self._draft.apply_value(amount)
            self._sync_quantity_section()
            self._refresh_mode_ui()
            return
        self._rebuild_search()

    def _quantity_minus(self) -> None:
        current = self._draft.quantity()
        if current <= 1:
            return
        self._draft.set_quantity(current - 1)
        self._draft.entry.clear_entry()
        self._feedback.setText("")
        self._sync_quantity_section()
        self._refresh_mode_ui()
        self._refresh_display()

    def _quantity_plus(self) -> None:
        self._draft.set_quantity(self._draft.quantity() + 1)
        self._draft.entry.clear_entry()
        self._feedback.setText("")
        self._sync_quantity_section()
        self._refresh_mode_ui()
        self._refresh_display()

    def _sync_quantity_section(self) -> None:
        self._quantity_label.setText(str(self._draft.quantity()))
        subtotal = self._draft.current_subtotal()
        if subtotal is None:
            self._quantity_value_label.setText("")
        else:
            self._quantity_value_label.setText(format_cop(subtotal))

    def _categoria_nombre(self, id_categoria: object) -> Optional[str]:
        if not isinstance(id_categoria, int) or isinstance(id_categoria, bool):
            return None
        for category in self._categories:
            if category.get("id_categoria") == id_categoria:
                nombre = category.get("nombre")
                return nombre if isinstance(nombre, str) else None
        return None

    def _product_for_draft(self, product: Mapping) -> Mapping:
        enriched = dict(product)
        nombre_categoria = self._categoria_nombre(product.get("id_categoria"))
        if nombre_categoria is not None:
            enriched["nombre_categoria"] = nombre_categoria
        return enriched

    def _select_all_categories(self) -> None:
        self._selected_category_id = None
        self._feedback.setText("")
        self._rebuild_categories()
        self._rebuild_products()

    def _select_category(self, id_categoria: int) -> None:
        self._selected_category_id = id_categoria
        self._feedback.setText("")
        self._rebuild_categories()
        self._rebuild_products()

    def _select_product(self, product: Mapping) -> None:
        enriched = self._product_for_draft(product)
        self._draft.select_product(enriched)
        self._draft.entry.clear_entry()
        self._draft.set_quantity(1)
        self._feedback.setText("")
        self._refresh_selection_ui()
        self._rebuild_products()
        self._sync_quantity_section()
        self._refresh_mode_ui()
        if not self._draft.selected_is_pan_pequeno():
            self._rebuild_search()
        self._refresh_display()

    def _refresh_selection_ui(self) -> None:
        selected = self._draft.selected_product()
        if selected is None:
            self._selection_label.setText("Sin producto seleccionado")
        else:
            self._selection_label.setText(
                f"Seleccionado: {selected['nombre']} — {format_cop(selected['precio'])}"
            )

    def _refresh_mode_ui(self) -> None:
        """Preview Pan pequeño y visibilidad de búsqueda por precio."""
        pan_mode = self._draft.selected_is_pan_pequeno()
        self._search_caption.setVisible(not pan_mode)
        self._search_scroll.setVisible(not pan_mode)
        if not pan_mode:
            self._value_preview_label.setText("")
            return

        quantity = self._draft.quantity()
        subtotal = self._draft.current_subtotal()
        if subtotal is None:
            self._value_preview_label.setText("")
            return

        amount = self._draft.entry.current_amount()
        if amount is not None and amount > 0 and amount != subtotal:
            self._value_preview_label.setText(
                f"{format_cop(amount)} → {format_cop(subtotal)} = {quantity} panes "
                f"(redondeo)"
            )
        else:
            self._value_preview_label.setText(
                f"{format_cop(subtotal)} = {quantity} panes"
            )

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _rebuild_categories(self) -> None:
        self._clear_layout(self._categories_layout)
        todos = QToolButton()
        todos.setText("Todos")
        todos.setObjectName("sale_category_todos")
        todos.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        todos.setFixedSize(style.CATEGORY_CHIP_WIDTH, style.CATEGORY_CHIP_HEIGHT)
        style.apply_class(
            todos,
            "category-chip-selected"
            if self._selected_category_id is None
            else "category-chip",
        )
        todos.clicked.connect(self._select_all_categories)
        self._categories_layout.addWidget(todos)

        for category in self._categories:
            button = QToolButton()
            button.setText(str(category["nombre"]))
            button.setObjectName(f"sale_category_{category['id_categoria']}")
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setFixedSize(style.CATEGORY_CHIP_WIDTH, style.CATEGORY_CHIP_HEIGHT)
            _apply_catalog_chip_icon(
                button, category_image_path(int(category["id_categoria"]))
            )
            selected = category["id_categoria"] == self._selected_category_id
            style.apply_class(
                button, "category-chip-selected" if selected else "category-chip"
            )
            button.clicked.connect(
                lambda checked=False, cid=category["id_categoria"]: self._select_category(
                    cid
                )
            )
            self._categories_layout.addWidget(button)
        self._categories_layout.addStretch(1)

    def _rebuild_products(self) -> None:
        self._clear_layout(self._products_layout)
        products = self._active_products
        if self._selected_category_id is not None:
            products = [
                product
                for product in products
                if product["id_categoria"] == self._selected_category_id
            ]
        selected = self._draft.selected_product()
        selected_id = selected["id_producto"] if selected is not None else None
        for product in products:
            button = QToolButton()
            button.setText(str(product["nombre"]))
            button.setObjectName(f"sale_product_{product['id_producto']}")
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setFixedSize(style.PRODUCT_CHIP_WIDTH, style.PRODUCT_CHIP_HEIGHT)
            _apply_catalog_chip_icon(
                button, resolve_relative_image(product.get("ruta_imagen"))
            )
            is_selected = product["id_producto"] == selected_id
            style.apply_class(
                button, "product-chip-selected" if is_selected else "product-chip"
            )
            button.clicked.connect(
                lambda checked=False, p=product: self._select_product(p)
            )
            self._products_layout.addWidget(button)
        self._products_layout.addStretch(1)

    def _rebuild_search(self) -> None:
        self._clear_layout(self._search_layout)
        amount = self._draft.entry.current_amount()
        if amount is None or amount <= 0:
            empty = QLabel("Escriba un precio para buscar")
            empty.setObjectName("price_search_empty")
            self._search_layout.addWidget(empty)
            self._search_layout.addStretch(1)
            return
        matches = candidates_by_exact_price(self._active_products, amount)
        if not matches:
            empty = QLabel("Sin productos a ese precio")
            empty.setObjectName("price_search_empty")
            self._search_layout.addWidget(empty)
        selected = self._draft.selected_product()
        selected_id = selected["id_producto"] if selected is not None else None
        for product in matches:
            button = QToolButton()
            button.setText(str(product["nombre"]))
            button.setObjectName(f"price_search_product_{product['id_producto']}")
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setFixedSize(style.PRODUCT_CHIP_WIDTH, style.PRODUCT_CHIP_HEIGHT)
            _apply_catalog_chip_icon(
                button, resolve_relative_image(product.get("ruta_imagen"))
            )
            is_selected = product["id_producto"] == selected_id
            style.apply_class(
                button, "product-chip-selected" if is_selected else "product-chip"
            )
            button.clicked.connect(
                lambda checked=False, p=product: self._select_product(p)
            )
            self._search_layout.addWidget(button)
        self._search_layout.addStretch(1)

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
        lineas = [
            {
                "id_producto": line.id_producto,
                "cantidad": line.cantidad,
                "precio_aplicado": line.precio_aplicado,
            }
            for line in self._draft.purchase.items()
        ]
        try:
            self._api.create_sale(payment_id, lineas)
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
        self._pending_image_path: Optional[Path] = None
        self._image_changed = False
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

        image_row = QHBoxLayout()
        self._image_status = QLabel("")
        self._image_status.setObjectName("product_image_status")
        style.apply_class(self._image_status, "dialog-text")
        image_row.addWidget(self._image_status, stretch=1)
        pick_image = QPushButton("Elegir imagen")
        pick_image.setObjectName("product_image_button")
        style.apply_class(pick_image, "payment-method-button")
        pick_image.clicked.connect(self._on_pick_image)
        image_row.addWidget(pick_image)
        layout.addLayout(image_row)

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
            existing = product.get("ruta_imagen")
            if isinstance(existing, str) and existing.strip():
                self._image_status.setText(f"Imagen: {existing.strip()}")
            else:
                self._image_status.setText("Sin imagen")
        else:
            self._estado_label.setText("Estado: Activo")
            self._image_status.setText("Sin imagen")

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

    def _on_pick_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.webp *.gif)",
        )
        if not path:
            return
        selected = Path(path)
        self._pending_image_path = selected
        self._image_changed = True
        self._image_status.setText(f"Nueva imagen: {selected.name}")

    def pending_image_path(self) -> Optional[Path]:
        return self._pending_image_path

    def image_changed(self) -> bool:
        return self._image_changed

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
        self._register.load_catalog()
        self._stack.setCurrentWidget(self._register)

    def open_products(self) -> None:
        self._products.reload()
        self._stack.setCurrentWidget(self._products)

    def go_back_to_menu(self) -> None:
        self._stack.setCurrentWidget(self._menu)
