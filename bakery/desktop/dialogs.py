"""Diálogos táctiles del desktop."""

from pathlib import Path
from typing import List, Mapping, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from bakery.app.money import format_cop
from bakery.desktop import style
from bakery.desktop.ui_helpers import (
    _PAYMENT_METHODS_PER_ROW,
    _apply_dialog_action_button_size,
    _apply_touch_dialog_layout,
)
from bakery.persistence.schema import ESTADO_ACTIVO

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
        style.apply_class(self._nombre, style.PRODUCT_FORM_FIELD_CLASS)
        layout.addWidget(self._nombre)

        self._precio = QLineEdit()
        self._precio.setObjectName("product_precio_input")
        self._precio.setPlaceholderText("Precio (entero)")
        style.apply_class(self._precio, style.PRODUCT_FORM_FIELD_CLASS)
        layout.addWidget(self._precio)

        self._categoria = QComboBox()
        self._categoria.setObjectName("product_categoria_combo")
        style.apply_class(self._categoria, style.PRODUCT_FORM_FIELD_CLASS)
        for category in categories:
            self._categoria.addItem(category["nombre"], category["id_categoria"])
        layout.addWidget(self._categoria)

        self._descripcion = QLineEdit()
        self._descripcion.setObjectName("product_descripcion_input")
        self._descripcion.setPlaceholderText("Descripción (opcional)")
        style.apply_class(self._descripcion, style.PRODUCT_FORM_FIELD_CLASS)
        layout.addWidget(self._descripcion)

        image_row = QHBoxLayout()
        self._image_status = QLabel("")
        self._image_status.setObjectName("product_image_status")
        style.apply_class(self._image_status, style.PRODUCT_FORM_LABEL_CLASS)
        image_row.addWidget(self._image_status, stretch=1)
        pick_image = QPushButton("Elegir imagen")
        pick_image.setObjectName("product_image_button")
        style.apply_class(pick_image, "product-form-button")
        pick_image.clicked.connect(self._on_pick_image)
        image_row.addWidget(pick_image)
        layout.addLayout(image_row)

        self._estado_label = QLabel("")
        self._estado_label.setObjectName("product_estado_label")
        style.apply_class(self._estado_label, style.PRODUCT_FORM_LABEL_CLASS)
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

