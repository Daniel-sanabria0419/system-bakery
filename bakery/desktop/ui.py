from typing import List, Mapping, Optional

import httpx
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from bakery.app.calculator import Calculator
from bakery.app.money import format_cop
from bakery.desktop.client import ApiClient


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


class MenuPage(QWidget):
    def __init__(self, on_register) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        button = QPushButton("Registrar venta")
        button.setObjectName("menu_register_button")
        button.clicked.connect(on_register)
        layout.addWidget(button)


class RegisterSalePage(QWidget):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self._api = api_client
        self._calculator = Calculator()
        self._payment_methods: List[Mapping] = []

        layout = QVBoxLayout(self)

        self._display = QLabel("")
        self._display.setObjectName("sale_display")
        self._display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self._display)

        self._expression = QLabel("")
        self._expression.setObjectName("sale_expression")
        self._expression.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self._expression)

        pad = QGridLayout()
        buttons = [
            ("7", 0, 0),
            ("8", 0, 1),
            ("9", 0, 2),
            ("⌫", 0, 3),
            ("4", 1, 0),
            ("5", 1, 1),
            ("6", 1, 2),
            ("C", 1, 3),
            ("1", 2, 0),
            ("2", 2, 1),
            ("3", 2, 2),
            ("+", 2, 3),
            ("0", 3, 0),
            ("-", 3, 3),
        ]
        for text, row, column in buttons:
            button = QPushButton(text)
            if text.isdigit():
                button.setObjectName(f"digit_{text}")
                button.clicked.connect(lambda checked=False, d=text: self._digit(d))
            elif text == "+":
                button.setObjectName("add_button")
                button.clicked.connect(lambda: self._action("add"))
            elif text == "-":
                button.setObjectName("subtract_button")
                button.clicked.connect(lambda: self._action("subtract"))
            elif text == "C":
                button.setObjectName("clear_button")
                button.clicked.connect(lambda: self._action("clear"))
            elif text == "⌫":
                button.setObjectName("backspace_button")
                button.clicked.connect(lambda: self._action("backspace"))
            pad.addWidget(button, row, column)
        layout.addLayout(pad)

        self._payment_combo = QComboBox()
        self._payment_combo.setObjectName("payment_combo")
        self._payment_combo.currentIndexChanged.connect(self._refresh_submit)
        layout.addWidget(self._payment_combo)

        self._submit = QPushButton("Registrar venta")
        self._submit.setObjectName("submit_sale_button")
        self._submit.clicked.connect(self._on_submit)
        layout.addWidget(self._submit)

        self._refresh_display()
        self._refresh_submit()

    def load_payment_methods(self) -> None:
        self._payment_methods = list(self._api.list_payment_methods())
        self._payment_combo.blockSignals(True)
        self._payment_combo.clear()
        self._payment_combo.addItem("Seleccione medio de pago", None)
        for method in self._payment_methods:
            self._payment_combo.addItem(method["nombre"], method["id_medio_pago"])
        self._payment_combo.blockSignals(False)
        self._refresh_submit()

    def reset_form(self) -> None:
        self._calculator.clear()
        self._payment_combo.setCurrentIndex(0)
        self._refresh_display()
        self._refresh_submit()

    def _digit(self, digit: str) -> None:
        self._calculator.press_digit(digit)
        self._refresh_display()
        self._refresh_submit()

    def _action(self, name: str) -> None:
        if name == "add":
            self._calculator.press_add()
        elif name == "subtract":
            self._calculator.press_subtract()
        elif name == "clear":
            self._calculator.clear()
        elif name == "backspace":
            self._calculator.backspace()
        self._refresh_display()
        self._refresh_submit()

    def _refresh_display(self) -> None:
        value = self._calculator.value()
        expression = self._calculator.expression()
        self._expression.setText(expression)
        if value is None:
            self._display.setText("")
        else:
            self._display.setText(format_cop(value))

    def _selected_payment_id(self) -> Optional[int]:
        return self._payment_combo.currentData()

    def _selected_payment_name(self) -> str:
        return self._payment_combo.currentText()

    def _refresh_submit(self) -> None:
        ready = (
            self._calculator.value() is not None
            and self._selected_payment_id() is not None
        )
        self._submit.setEnabled(ready)

    def _on_submit(self) -> None:
        value = self._calculator.value()
        payment_id = self._selected_payment_id()
        if value is None or payment_id is None:
            return
        dialog = ConfirmSaleDialog(value, self._selected_payment_name(), self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            self._api.create_sale(value, payment_id)
        except httpx.HTTPError as error:
            QMessageBox.warning(self, "Error", f"No se pudo guardar la venta.\n{error}")
            return
        self.reset_form()


class MainWindow(QMainWindow):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.setWindowTitle("Panadería")
        self.resize(420, 560)
        self._api = api_client

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._menu = MenuPage(self.open_register_sale)
        self._register = RegisterSalePage(api_client)
        self._stack.addWidget(self._menu)
        self._stack.addWidget(self._register)
        self._stack.setCurrentWidget(self._menu)

    def open_register_sale(self) -> None:
        self._register.load_payment_methods()
        self._stack.setCurrentWidget(self._register)
