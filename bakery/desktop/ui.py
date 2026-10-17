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
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from bakery.app.money import format_cop
from bakery.app.purchase import SaleDraft
from bakery.desktop import style
from bakery.desktop.client import ApiClient


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


def _make_separator(object_name: str) -> QFrame:
    line = QFrame()
    line.setObjectName(object_name)
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Plain)
    line.setFixedHeight(2)
    return line


class ConfirmSaleDialog(QDialog):
    def __init__(self, valor_total: int, payment_name: str, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("confirm_dialog")
        self.setWindowTitle("Confirmar venta")

        layout = QVBoxLayout(self)
        value_label = QLabel(f"Valor total: {format_cop(valor_total)}")
        value_label.setObjectName("confirm_value_label")
        payment_label = QLabel(f"Medio de pago: {payment_name}")
        payment_label.setObjectName("confirm_payment_label")
        layout.addWidget(value_label)
        layout.addWidget(payment_label)

        buttons = QDialogButtonBox()
        confirm = buttons.addButton("Confirmar", QDialogButtonBox.AcceptRole)
        confirm.setObjectName("confirm_button")
        cancel = buttons.addButton("No", QDialogButtonBox.RejectRole)
        cancel.setObjectName("cancel_button")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class SaleSavedDialog(QDialog):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("sale_saved_dialog")
        self.setWindowTitle("Venta guardada")

        layout = QVBoxLayout(self)
        message = QLabel("Venta guardada correctamente")
        message.setObjectName("sale_saved_message")
        layout.addWidget(message)

        buttons = QDialogButtonBox()
        ok = buttons.addButton("Aceptar", QDialogButtonBox.AcceptRole)
        ok.setObjectName("sale_saved_ok_button")
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class MenuPage(QWidget):
    def __init__(self, on_register) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        _apply_page_layout(layout)
        layout.setAlignment(Qt.AlignCenter)
        button = QPushButton("Registrar venta")
        button.setObjectName("menu_register_button")
        style.apply_class(button, "menu-button")
        button.clicked.connect(on_register)
        layout.addWidget(button)


class RegisterSalePage(QWidget):
    def __init__(self, api_client: ApiClient, on_back=None) -> None:
        super().__init__()
        self._api = api_client
        self._draft = SaleDraft()
        self._payment_methods: List[Mapping] = []

        root = QVBoxLayout(self)
        _apply_page_layout(root)

        top_bar = QHBoxLayout()
        top_bar.addStretch(1)
        back = QPushButton("Volver")
        back.setObjectName("back_button")
        style.apply_class(back, "back-button")
        if on_back is not None:
            back.clicked.connect(on_back)
        top_bar.addWidget(back)
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
        self._purchase_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        style.apply_class(self._purchase_list, "money-text")
        panel_layout.addWidget(self._purchase_list, stretch=1)

        panel_layout.addWidget(_make_separator("total_separator"))

        footer = QHBoxLayout()
        self._payment_combo = QComboBox()
        self._payment_combo.setObjectName("payment_combo")
        style.apply_class(self._payment_combo, "combo-box")
    
        self._payment_combo.currentIndexChanged.connect(self._refresh_submit)
        footer.addWidget(self._payment_combo, stretch=1)

        self._purchase_total = QLabel("")
        self._purchase_total.setObjectName("purchase_total")
        self._purchase_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        style.apply_class(self._purchase_total, "money-text")
        footer.addWidget(self._purchase_total)
        panel_layout.addLayout(footer)

        left_layout.addWidget(purchase_panel, stretch=1)

        pad = QGridLayout()
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
                button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
                button.clicked.connect(self._on_submit)
                
                self._submit = button
            pad.addWidget(button, row, column, row_span, col_span)

        left_layout.addLayout(pad)

        future = QWidget()
        future.setObjectName("future_panel")
        future.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        columns.addWidget(left, style.LEFT_COLUMN_STRETCH)
        columns.addWidget(future, style.RIGHT_COLUMN_STRETCH)
        root.addLayout(columns, stretch=1)

        self._refresh_display()
        self._refresh_submit()

    def load_payment_methods(self) -> None:
        selected_id = self._selected_payment_id()
        self._payment_methods = list(self._api.list_payment_methods())
        self._payment_combo.blockSignals(True)
        self._payment_combo.clear()
        self._payment_combo.addItem("Seleccione medio de pago", None)
        for method in self._payment_methods:
            self._payment_combo.addItem(method["nombre"], method["id_medio_pago"])
        if selected_id is not None:
            index = self._payment_combo.findData(selected_id)
            if index >= 0:
                self._payment_combo.setCurrentIndex(index)
        self._payment_combo.blockSignals(False)
        self._refresh_submit()

    def reset_form(self) -> None:
        self._draft.clear_purchase()
        self._payment_combo.setCurrentIndex(0)
        self._refresh_display()
        self._refresh_submit()

    def _digit(self, digit: str) -> None:
        self._draft.entry.press_digit(digit)
        self._refresh_display()
        self._refresh_submit()

    def _action(self, name: str) -> None:
        if name == "agregar":
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
        self._purchase_list.setText("\n".join(format_cop(amount) for amount in items))
        total = self._draft.total()
        if total > 0:
            self._purchase_total.setText(f"Total: {format_cop(total)}")
        else:
            self._purchase_total.setText("Total: $0.00")

    def _selected_payment_id(self) -> Optional[int]:
        return self._payment_combo.currentData()

    def _selected_payment_name(self) -> str:
        return self._payment_combo.currentText()

    def _refresh_submit(self) -> None:
        ready = self._draft.total() > 0 and self._selected_payment_id() is not None
        self._submit.setEnabled(ready)

    def _on_submit(self) -> None:
        value = self._draft.total()
        payment_id = self._selected_payment_id()
        if value <= 0 or payment_id is None:
            return
        dialog = ConfirmSaleDialog(value, self._selected_payment_name(), self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            self._api.create_sale(value, payment_id)
        except httpx.HTTPError as error:
            QMessageBox.warning(self, "Error", f"No se pudo guardar la venta.\n{error}")
            return
        SaleSavedDialog(self).exec()
        self.reset_form()


class MainWindow(QMainWindow):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.setWindowTitle("Panadería")
        self.showFullScreen()
        self._api = api_client

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._menu = MenuPage(self.open_register_sale)
        self._register = RegisterSalePage(api_client, on_back=self.go_back_to_menu)
        self._stack.addWidget(self._menu)
        self._stack.addWidget(self._register)
        self._stack.setCurrentWidget(self._menu)

    def open_register_sale(self) -> None:
        self._register.load_payment_methods()
        self._stack.setCurrentWidget(self._register)

    def go_back_to_menu(self) -> None:
        self._stack.setCurrentWidget(self._menu)
