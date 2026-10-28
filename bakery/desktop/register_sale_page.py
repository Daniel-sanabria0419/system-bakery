"""Página Registrar venta."""

from typing import List, Mapping, Optional

import httpx
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from bakery.app.money import format_cop
from bakery.app.product_images import (
    category_image_path,
    resolve_relative_image,
)
from bakery.app.purchase import SaleDraft, candidates_by_price_prefix
from bakery.desktop import style
from bakery.desktop.client import ApiClient
from bakery.desktop.dialogs import (
    ConfirmSaleDialog,
    SaleSavedDialog,
    SelectPaymentMethodDialog,
)
from bakery.desktop.ui_helpers import (
    CatalogChipButton,
    FlowLayout,
    _BACK_BUTTON_ARROW,
    _PAYMENT_BUTTON_PLACEHOLDER,
    _apply_catalog_chip_icon,
    _apply_pad_button_size,
    _apply_page_layout,
    _make_separator,
)

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
        # Vista A = solo categorías; Vista B = productos + volver (Beta 2.0.3).
        self._catalog_view = "categories"

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

        selection_panel = QWidget()
        selection_panel.setObjectName("selected_product_panel")
        selection_row = QHBoxLayout(selection_panel)
        selection_row.setContentsMargins(0, 0, 0, 0)
        selection_row.setSpacing(style.PAGE_SPACING)

        self._selection_image = QLabel()
        self._selection_image.setObjectName("selected_product_image")
        self._selection_image.setFixedSize(
            style.SELECTED_PRODUCT_IMAGE_WIDTH,
            style.SELECTED_PRODUCT_IMAGE_HEIGHT,
        )
        self._selection_image.setAlignment(Qt.AlignCenter)
        self._selection_image.setScaledContents(False)
        selection_row.addWidget(self._selection_image)

        info_column = QVBoxLayout()
        info_column.setContentsMargins(0, 0, 0, 0)
        info_column.setSpacing(style.PAGE_SPACING)
        self._selection_label = QLabel("Sin producto seleccionado")
        self._selection_label.setObjectName("selected_product_label")
        self._selection_label.setWordWrap(True)
        info_column.addWidget(self._selection_label)
        self._selection_unit_label = QLabel("")
        self._selection_unit_label.setObjectName("selected_product_unit_price")
        info_column.addWidget(self._selection_unit_label)
        self._quantity_value_label = QLabel("")
        self._quantity_value_label.setObjectName("quantity_value_label")
        info_column.addWidget(self._quantity_value_label)
        info_column.addStretch(1)
        selection_row.addLayout(info_column, stretch=1)

        qty_section = QWidget()
        qty_section.setObjectName("quantity_section")
        qty_section_layout = QVBoxLayout(qty_section)
        qty_section_layout.setContentsMargins(0, 0, 0, 0)
        qty_section_layout.setSpacing(style.PAGE_SPACING)
        qty_row = QHBoxLayout()
        qty_row.setSpacing(style.PAGE_SPACING)
        # Orden scope: cantidad (número) luego −/+.
        self._quantity_label = QLabel("1")
        self._quantity_label.setObjectName("quantity_label")
        self._quantity_label.setAlignment(Qt.AlignCenter)
        qty_row.addWidget(self._quantity_label)
        minus = QPushButton("−")
        minus.setObjectName("quantity_minus_button")
        style.apply_class(minus, "payment-method-button")
        minus.clicked.connect(self._quantity_minus)
        qty_row.addWidget(minus)
        plus = QPushButton("+")
        plus.setObjectName("quantity_plus_button")
        style.apply_class(plus, "payment-method-button")
        plus.clicked.connect(self._quantity_plus)
        qty_row.addWidget(plus)
        qty_section_layout.addLayout(qty_row)
        qty_section_layout.addStretch(1)
        selection_row.addWidget(qty_section)
        catalog_layout.addWidget(selection_panel)

        self._value_preview_label = QLabel("")
        self._value_preview_label.setObjectName("sale_value_preview")
        self._value_preview_label.setWordWrap(True)
        catalog_layout.addWidget(self._value_preview_label)

        self._feedback = QLabel("")
        self._feedback.setObjectName("sale_feedback")
        self._feedback.setWordWrap(True)
        catalog_layout.addWidget(self._feedback)

        self._categories_section = QWidget()
        self._categories_section.setObjectName("catalog_categories_section")
        categories_section_layout = QVBoxLayout(self._categories_section)
        categories_section_layout.setContentsMargins(8, 8, 8, 8)
        categories_section_layout.setSpacing(style.PAGE_SPACING)
        categories_caption = QLabel("Categorías")
        categories_caption.setObjectName("categories_caption")
        categories_section_layout.addWidget(categories_caption)
        self._categories_host = QWidget()
        self._categories_host.setObjectName("categories_list")
        self._categories_layout = FlowLayout(self._categories_host)
        categories_scroll = QScrollArea()
        categories_scroll.setObjectName("categories_scroll")
        categories_scroll.setWidgetResizable(True)
        categories_scroll.setFrameShape(QFrame.NoFrame)
        categories_scroll.setWidget(self._categories_host)
        categories_section_layout.addWidget(categories_scroll, stretch=1)
        catalog_layout.addWidget(self._categories_section, stretch=1)

        self._catalog_sections_divider = _make_separator("catalog_sections_divider")
        catalog_layout.addWidget(self._catalog_sections_divider)

        self._products_section = QWidget()
        self._products_section.setObjectName("catalog_products_section")
        products_section_layout = QVBoxLayout(self._products_section)
        products_section_layout.setContentsMargins(8, 8, 8, 8)
        products_section_layout.setSpacing(style.PAGE_SPACING)
        products_caption = QLabel("Productos")
        products_caption.setObjectName("products_caption")
        products_section_layout.addWidget(products_caption)
        self._products_host = QWidget()
        self._products_host.setObjectName("sale_products_list")
        self._products_layout = FlowLayout(self._products_host)
        products_scroll = QScrollArea()
        products_scroll.setObjectName("sale_products_scroll")
        products_scroll.setWidgetResizable(True)
        products_scroll.setFrameShape(QFrame.NoFrame)
        products_scroll.setWidget(self._products_host)
        products_section_layout.addWidget(products_scroll, stretch=1)
        catalog_layout.addWidget(self._products_section, stretch=2)
        self._catalog_layout = catalog_layout

        columns.addWidget(left, style.LEFT_COLUMN_STRETCH)
        columns.addWidget(catalog, style.RIGHT_COLUMN_STRETCH)
        root.addLayout(columns, stretch=1)

        self._apply_catalog_view()
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
        self._catalog_view = "categories"
        self._rebuild_categories()
        self._rebuild_products()
        self._apply_catalog_view()
        self._refresh_selection_ui()
        self._sync_quantity_section()
        self._refresh_mode_ui()

    def reset_form(self) -> None:
        self._draft.clear_purchase()
        self._clear_payment_selection()
        self._selected_category_id = None
        self._catalog_view = "categories"
        self._feedback.setText("")
        self._rebuild_categories()
        self._rebuild_products()
        self._apply_catalog_view()
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

    def _digits_blocked_for_quantity_only(self) -> bool:
        """Producto no–Pan pequeño: cantidad solo con −/+ (Beta 2.0.2)."""
        return (
            self._draft.selected_product() is not None
            and not self._draft.selected_is_pan_pequeno()
        )

    def _digit(self, digit: str) -> None:
        if self._digits_blocked_for_quantity_only():
            self._feedback.setText("Use −/+ para la cantidad")
            return
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
                self._rebuild_products()
        elif name == "clear":
            self._draft.clear_purchase()
            self._selected_category_id = None
            self._catalog_view = "categories"
            self._feedback.setText("")
            self._rebuild_categories()
            self._rebuild_products()
            self._apply_catalog_view()
            self._refresh_selection_ui()
            self._sync_quantity_section()
            self._refresh_mode_ui()
        elif name == "borrar":
            if self._digits_blocked_for_quantity_only():
                self._feedback.setText("Use −/+ para la cantidad")
            else:
                self._draft.entry.backspace()
                self._feedback.setText("")
                self._on_entry_changed()
        elif name == "zeros":
            if self._digits_blocked_for_quantity_only():
                self._feedback.setText("Use −/+ para la cantidad")
            else:
                self._draft.entry.press_zeros()
                self._feedback.setText("")
                self._on_entry_changed()
        self._refresh_display()
        self._refresh_submit()

    def _on_entry_changed(self) -> None:
        """Tras dígitos: Pan pequeño = valor→cantidad; sin selección = prefijo; otro = qty."""
        if self._draft.selected_is_pan_pequeno():
            amount = self._draft.entry.current_amount()
            if amount is not None and amount > 0:
                self._draft.apply_value(amount)
            self._sync_quantity_section()
            self._refresh_mode_ui()
            return
        if self._draft.selected_product() is not None:
            # Otro producto: dígitos no filtran ni cambian cantidad.
            return
        self._rebuild_products()

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
        selected = self._draft.selected_product()
        subtotal = self._draft.current_subtotal()
        if selected is None or subtotal is None:
            self._selection_unit_label.setText("")
            self._quantity_value_label.setText("")
            return
        self._selection_unit_label.setText(
            f"Unitario: {format_cop(selected['precio'])}"
        )
        self._quantity_value_label.setText(f"Subtotal: {format_cop(subtotal)}")

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

    def _apply_catalog_view(self) -> None:
        """Vista A: solo categorías. Vista B: productos + volver; categorías ocultas."""
        show_categories = self._catalog_view == "categories"
        self._categories_section.setVisible(show_categories)
        self._products_section.setVisible(not show_categories)
        # Nunca ambas a la vez: el divisor no aporta en A ni en B.
        self._catalog_sections_divider.setVisible(False)
        if show_categories:
            self._catalog_layout.setStretch(
                self._catalog_layout.indexOf(self._categories_section), 1
            )
            self._catalog_layout.setStretch(
                self._catalog_layout.indexOf(self._products_section), 0
            )
        else:
            self._catalog_layout.setStretch(
                self._catalog_layout.indexOf(self._categories_section), 0
            )
            self._catalog_layout.setStretch(
                self._catalog_layout.indexOf(self._products_section), 1
            )

    def _show_catalog_products_view(self) -> None:
        self._catalog_view = "products"
        self._apply_catalog_view()

    def _back_to_categories(self) -> None:
        self._selected_category_id = None
        self._catalog_view = "categories"
        self._feedback.setText("")
        self._rebuild_categories()
        self._rebuild_products()
        self._apply_catalog_view()

    def _select_all_categories(self) -> None:
        self._selected_category_id = None
        self._feedback.setText("")
        self._rebuild_categories()
        self._rebuild_products()
        self._show_catalog_products_view()

    def _select_category(self, id_categoria: int) -> None:
        self._selected_category_id = id_categoria
        self._feedback.setText("")
        self._rebuild_categories()
        self._rebuild_products()
        self._show_catalog_products_view()

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
        self._refresh_display()

    def _refresh_selection_ui(self) -> None:
        selected = self._draft.selected_product()
        if selected is None:
            self._selection_label.setText("Sin producto seleccionado")
            self._selection_image.clear()
            self._selection_image.setText("")
            return
        self._selection_label.setText(str(selected["nombre"]))
        image_path = resolve_relative_image(selected.get("ruta_imagen"))
        if image_path is None:
            self._selection_image.clear()
            self._selection_image.setText("")
            return
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self._selection_image.clear()
            self._selection_image.setText("")
            return
        self._selection_image.setPixmap(
            pixmap.scaled(
                style.SELECTED_PRODUCT_IMAGE_WIDTH,
                style.SELECTED_PRODUCT_IMAGE_HEIGHT,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def _refresh_mode_ui(self) -> None:
        """Preview Pan pequeño (valor→cantidad); el monto tipado no se recalcula."""
        if not self._draft.selected_is_pan_pequeno():
            self._value_preview_label.setText("")
            return

        quantity = self._draft.quantity()
        subtotal = self._draft.current_subtotal()
        if subtotal is None:
            self._value_preview_label.setText("")
            return

        # Mientras hay valor tipado, current_subtotal ya es ese valor: no mostrar
        # flecha hacia qty*300 / todo_o_nada (p. ej. 5000→5100).
        self._value_preview_label.setText(
            f"{format_cop(subtotal)} = {quantity} panes"
        )

    def _clear_layout(self, layout: QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def _rebuild_categories(self) -> None:
        self._clear_layout(self._categories_layout)
        todos = CatalogChipButton()
        todos.setText("Todos")
        todos.setObjectName("sale_category_todos")
        todos.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        todos.setFixedSize(style.CATEGORY_CHIP_WIDTH, style.CATEGORY_CHIP_HEIGHT)
        # Vista A: ningún chip seleccionado (Todos tampoco).
        style.apply_class(todos, "category-chip")
        todos.clicked.connect(self._select_all_categories)
        self._categories_layout.addWidget(todos)

        for category in self._categories:
            button = CatalogChipButton()
            button.setText(str(category["nombre"]))
            button.setObjectName(f"sale_category_{category['id_categoria']}")
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setFixedSize(style.CATEGORY_CHIP_WIDTH, style.CATEGORY_CHIP_HEIGHT)
            _apply_catalog_chip_icon(
                button, category_image_path(int(category["id_categoria"]))
            )
            # Solo marcar categoría si aún estamos en Vista B (sección oculta);
            # en Vista A `_selected_category_id` es None → ninguna seleccionada.
            selected = (
                self._catalog_view == "products"
                and category["id_categoria"] == self._selected_category_id
            )
            style.apply_class(
                button, "category-chip-selected" if selected else "category-chip"
            )
            button.clicked.connect(
                lambda checked=False, cid=category["id_categoria"]: self._select_category(
                    cid
                )
            )
            self._categories_layout.addWidget(button)

    def _rebuild_products(self) -> None:
        self._clear_layout(self._products_layout)
        # Volver = chip en la misma grilla/wrap que los productos (no barra aparte).
        catalog_back = CatalogChipButton()
        catalog_back.setText("Volver")
        catalog_back.setObjectName("catalog_back_to_categories")
        catalog_back.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        catalog_back.setFixedSize(style.PRODUCT_CHIP_WIDTH, style.PRODUCT_CHIP_HEIGHT)
        catalog_back.setToolTip("Volver a categorías")
        style.apply_class(catalog_back, "product-chip")
        catalog_back.clicked.connect(self._back_to_categories)
        self._products_layout.addWidget(catalog_back)

        products = self._active_products
        if self._selected_category_id is not None:
            products = [
                product
                for product in products
                if product["id_categoria"] == self._selected_category_id
            ]
        # Prefijo solo sin producto seleccionado (categoría ∩ prefijo).
        if self._draft.selected_product() is None:
            prefix = self._draft.entry.digits()
            if prefix:
                products = candidates_by_price_prefix(products, prefix)
        selected = self._draft.selected_product()
        selected_id = selected["id_producto"] if selected is not None else None
        for product in products:
            button = CatalogChipButton()
            button.setText(str(product["nombre"]))
            button.setObjectName(f"sale_product_{product['id_producto']}")
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setFixedSize(style.PRODUCT_CHIP_WIDTH, style.PRODUCT_CHIP_HEIGHT)
            _apply_catalog_chip_icon(
                button,
                resolve_relative_image(product.get("ruta_imagen")),
                ensure_thumb=True,
            )
            is_selected = product["id_producto"] == selected_id
            style.apply_class(
                button, "product-chip-selected" if is_selected else "product-chip"
            )
            button.clicked.connect(
                lambda checked=False, p=product: self._select_product(p)
            )
            self._products_layout.addWidget(button)

    def _refresh_display(self) -> None:
        """Pad + lista de compra + total.

        Con flag de promociones on, ``line.subtotal`` y ``total`` ya vienen
        recalculados por grupo tras cada Agregar (Etapa 4).
        """
        self._display.setText(format_cop(self._draft.pad_display_amount()))
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
        self._purchase_total.setText(f"Total: {format_cop(total)}")

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

