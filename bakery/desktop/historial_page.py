"""Página Historial de ventas (Beta 2.1: lectura, edición ≤1 h, obs posterior)."""

from datetime import datetime, timedelta
from typing import List, Mapping, MutableMapping, Optional

import httpx
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from bakery.app.money import format_cop
from bakery.desktop import style
from bakery.desktop.client import ApiClient
from bakery.desktop.dialogs import (
    AddObservacionDialog,
    ConfirmEditDialog,
    SelectPaymentMethodDialog,
    SelectProductDialog,
)
from bakery.desktop.ui_helpers import (
    _BACK_BUTTON_ARROW,
    _PAYMENT_BUTTON_PLACEHOLDER,
    _apply_page_layout,
)

_LEGADO_SIN_LINEAS = "Sin detalle de productos (venta antigua)"
_ORIGEN_LABELS = {
    "durante_venta": "Durante la venta",
    "posterior": "Posterior",
}


def _split_fecha_hora(fecha_venta: str) -> tuple[str, str]:
    """Separa fecha y hora de un ISO local para presentación (sin lógica de negocio)."""
    text = (fecha_venta or "").strip()
    if "T" in text:
        date_part, time_part = text.split("T", 1)
        time_part = time_part.split(".", 1)[0]
        return date_part, time_part
    return text, ""


def _resumen_listado(sale: Mapping) -> str:
    if sale.get("es_legado"):
        return "Venta antigua (sin productos)"
    count = int(sale.get("cantidad_lineas") or 0)
    if count == 1:
        return "1 ítem"
    return f"{count} ítems"


def _last_durante_venta_texto(observaciones: List[Mapping]) -> Optional[str]:
    texto: Optional[str] = None
    for obs in observaciones:
        if obs.get("origen") == "durante_venta":
            value = str(obs.get("texto") or "").strip()
            if value:
                texto = value
    return texto


def _ventana_hasta_label(fecha_venta: str) -> str:
    """Texto informativo de fin de ventana (el backend decide editable)."""
    text = (fecha_venta or "").strip()
    if not text:
        return "Editable solo dentro de la primera hora."
    try:
        start = datetime.fromisoformat(text)
    except ValueError:
        return "Editable solo dentro de la primera hora."
    end = start + timedelta(hours=1)
    return f"Editable hasta {end.isoformat(timespec='seconds')} (informativo)."


class HistorialPage(QWidget):
    def __init__(self, api_client: ApiClient, on_back=None) -> None:
        super().__init__()
        self.setObjectName("historial_page")
        self._api = api_client
        self._on_back = on_back
        self._sales: List[Mapping] = []
        self._current_detail_id: Optional[str] = None
        self._current_detail: Optional[Mapping] = None
        self._edit_id: Optional[str] = None
        self._edit_es_legado = False
        self._edit_medio_id: Optional[int] = None
        self._edit_medio_nombre: Optional[str] = None
        self._edit_lines: List[MutableMapping] = []
        self._edit_products: List[Mapping] = []
        self._edit_payment_methods: List[Mapping] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.setObjectName("historial_stack")
        root.addWidget(self._stack)

        self._list_page = self._build_list_page()
        self._detail_page = self._build_detail_page()
        self._edit_page = self._build_edit_page()
        self._stack.addWidget(self._list_page)
        self._stack.addWidget(self._detail_page)
        self._stack.addWidget(self._edit_page)
        self._stack.setCurrentWidget(self._list_page)

    def reload(self) -> None:
        self._sales = list(self._api.list_sales())
        self._rebuild_list()
        self._stack.setCurrentWidget(self._list_page)

    def _build_list_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("historial_list_page")
        layout = QVBoxLayout(page)
        _apply_page_layout(layout)

        top_bar = QHBoxLayout()
        back = QPushButton(_BACK_BUTTON_ARROW)
        back.setObjectName("historial_back_button")
        style.apply_class(back, "back-button")
        back.setMinimumSize(
            style.BACK_BUTTON_MIN_WIDTH,
            style.BACK_BUTTON_MIN_HEIGHT,
        )
        back.setToolTip("Volver")
        if self._on_back is not None:
            back.clicked.connect(self._on_back)
        top_bar.addWidget(back)

        title = QLabel("Historial")
        title.setObjectName("historial_title")
        style.apply_class(title, "dialog-text")
        top_bar.addWidget(title)
        top_bar.addStretch(1)
        layout.addLayout(top_bar)

        self._list_host = QWidget()
        self._list_host.setObjectName("historial_list")
        self._list_layout = QVBoxLayout(self._list_host)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(style.PAGE_SPACING)
        self._list_layout.addStretch(1)

        self._empty_label = QLabel("No hay ventas registradas.")
        self._empty_label.setObjectName("historial_empty")
        self._empty_label.setWordWrap(True)
        self._empty_label.hide()
        layout.addWidget(self._empty_label)

        scroll = QScrollArea()
        scroll.setObjectName("historial_list_scroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self._list_host)
        layout.addWidget(scroll, stretch=1)
        return page

    def _build_detail_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("historial_detail_page")
        layout = QVBoxLayout(page)
        _apply_page_layout(layout)

        top_bar = QHBoxLayout()
        back = QPushButton(_BACK_BUTTON_ARROW)
        back.setObjectName("historial_detail_back_button")
        style.apply_class(back, "back-button")
        back.setMinimumSize(
            style.BACK_BUTTON_MIN_WIDTH,
            style.BACK_BUTTON_MIN_HEIGHT,
        )
        back.setToolTip("Volver al listado")
        back.clicked.connect(self._show_list)
        top_bar.addWidget(back)

        title = QLabel("Detalle de venta")
        title.setObjectName("historial_detail_title")
        style.apply_class(title, "dialog-text")
        top_bar.addWidget(title)
        top_bar.addStretch(1)
        layout.addLayout(top_bar)

        self._detail_host = QWidget()
        self._detail_host.setObjectName("historial_detail_content")
        self._detail_layout = QVBoxLayout(self._detail_host)
        self._detail_layout.setContentsMargins(0, 0, 0, 0)
        self._detail_layout.setSpacing(style.PAGE_SPACING)
        self._detail_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setObjectName("historial_detail_scroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self._detail_host)
        layout.addWidget(scroll, stretch=1)
        return page

    def _build_edit_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("historial_edit_page")
        layout = QVBoxLayout(page)
        _apply_page_layout(layout)

        top_bar = QHBoxLayout()
        back = QPushButton(_BACK_BUTTON_ARROW)
        back.setObjectName("historial_edit_back_button")
        style.apply_class(back, "back-button")
        back.setMinimumSize(
            style.BACK_BUTTON_MIN_WIDTH,
            style.BACK_BUTTON_MIN_HEIGHT,
        )
        back.setToolTip("Volver al detalle")
        back.clicked.connect(self._cancel_edit)
        top_bar.addWidget(back)

        title = QLabel("Editar venta")
        title.setObjectName("historial_edit_title")
        style.apply_class(title, "dialog-text")
        top_bar.addWidget(title)
        top_bar.addStretch(1)
        layout.addLayout(top_bar)

        self._edit_window_label = QLabel("")
        self._edit_window_label.setObjectName("historial_edit_window_label")
        self._edit_window_label.setWordWrap(True)
        style.apply_class(self._edit_window_label, "dialog-text")
        layout.addWidget(self._edit_window_label)

        medio_row = QHBoxLayout()
        self._edit_medio_button = QPushButton(_PAYMENT_BUTTON_PLACEHOLDER)
        self._edit_medio_button.setObjectName("historial_edit_medio_button")
        style.apply_class(self._edit_medio_button, "payment-method-button")
        self._edit_medio_button.setMinimumHeight(
            style.PAYMENT_METHOD_BUTTON_MIN_HEIGHT
        )
        self._edit_medio_button.clicked.connect(self._on_edit_change_medio)
        medio_row.addWidget(self._edit_medio_button)
        layout.addLayout(medio_row)

        obs_label = QLabel("Observación de venta")
        obs_label.setObjectName("historial_edit_obs_label")
        style.apply_class(obs_label, "dialog-text")
        layout.addWidget(obs_label)
        self._edit_obs_input = QLineEdit()
        self._edit_obs_input.setObjectName("historial_edit_obs_input")
        self._edit_obs_input.setPlaceholderText("Observación de la venta")
        style.apply_class(self._edit_obs_input, style.PRODUCT_FORM_FIELD_CLASS)
        layout.addWidget(self._edit_obs_input)

        self._edit_legado_label = QLabel(_LEGADO_SIN_LINEAS)
        self._edit_legado_label.setObjectName("historial_edit_legado_label")
        self._edit_legado_label.setWordWrap(True)
        style.apply_class(self._edit_legado_label, "dialog-text")
        self._edit_legado_label.hide()
        layout.addWidget(self._edit_legado_label)

        self._edit_lines_host = QWidget()
        self._edit_lines_host.setObjectName("historial_edit_lines")
        self._edit_lines_layout = QVBoxLayout(self._edit_lines_host)
        self._edit_lines_layout.setContentsMargins(0, 0, 0, 0)
        self._edit_lines_layout.setSpacing(style.PAGE_SPACING)

        lines_scroll = QScrollArea()
        lines_scroll.setObjectName("historial_edit_lines_scroll")
        lines_scroll.setWidgetResizable(True)
        lines_scroll.setFrameShape(QFrame.NoFrame)
        lines_scroll.setWidget(self._edit_lines_host)
        layout.addWidget(lines_scroll, stretch=1)

        self._edit_add_product_button = QPushButton("Agregar producto")
        self._edit_add_product_button.setObjectName(
            "historial_edit_add_product_button"
        )
        style.apply_class(self._edit_add_product_button, "dialog-action-button")
        self._edit_add_product_button.setMinimumHeight(
            style.DIALOG_ACTION_BUTTON_MIN_HEIGHT
        )
        self._edit_add_product_button.clicked.connect(self._on_edit_add_product)
        layout.addWidget(self._edit_add_product_button)

        save = QPushButton("Guardar cambios")
        save.setObjectName("historial_edit_save_button")
        style.apply_class(save, "dialog-action-button")
        save.setMinimumHeight(style.DIALOG_ACTION_BUTTON_MIN_HEIGHT)
        save.clicked.connect(self._on_edit_save)
        layout.addWidget(save)
        return page

    def _rebuild_list(self) -> None:
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not self._sales:
            self._empty_label.show()
            self._list_layout.addStretch(1)
            return

        self._empty_label.hide()
        for sale in self._sales:
            self._list_layout.addWidget(self._make_list_row(sale))
        self._list_layout.addStretch(1)

    def _make_list_row(self, sale: Mapping) -> QWidget:
        id_venta = str(sale["id_venta"])
        fecha, hora = _split_fecha_hora(str(sale.get("fecha_venta") or ""))
        medio = str(sale.get("nombre_medio") or "")
        total = format_cop(int(sale["valor_total"]))
        resumen = _resumen_listado(sale)

        row = QPushButton()
        row.setObjectName(f"historial_row_{id_venta}")
        style.apply_class(row, "payment-method-button")
        row.setMinimumHeight(style.PAYMENT_METHOD_BUTTON_MIN_HEIGHT)
        parts = [p for p in (fecha, hora) if p]
        when = " ".join(parts) if parts else id_venta
        row.setText(f"{when}  ·  {total}  ·  {medio}  ·  {resumen}")
        row.setStyleSheet("text-align: left; padding-left: 12px;")
        row.clicked.connect(
            lambda checked=False, sale_id=id_venta: self._open_detail(sale_id)
        )
        return row

    def _show_list(self) -> None:
        self._stack.setCurrentWidget(self._list_page)

    def _open_detail(self, id_venta: str) -> None:
        try:
            detail = self._api.get_sale(id_venta)
        except httpx.HTTPError as exc:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo cargar el detalle.\n{exc}",
            )
            return
        self._current_detail_id = id_venta
        self._current_detail = detail
        self._render_detail(detail)
        self._stack.setCurrentWidget(self._detail_page)

    def _clear_detail(self) -> None:
        while self._detail_layout.count():
            item = self._detail_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setObjectName("")
                for child in widget.findChildren(QWidget):
                    child.setObjectName("")
                widget.deleteLater()
            # Layouts anidados (p. ej. fila de acciones) no son widgets.
            child_layout = item.layout()
            if child_layout is not None:
                while child_layout.count():
                    nested = child_layout.takeAt(0)
                    nested_widget = nested.widget()
                    if nested_widget is not None:
                        nested_widget.setObjectName("")
                        for child in nested_widget.findChildren(QWidget):
                            child.setObjectName("")
                        nested_widget.deleteLater()

    def _add_detail_label(
        self, object_name: str, text: str, *, class_name: Optional[str] = None
    ) -> QLabel:
        label = QLabel(text)
        label.setObjectName(object_name)
        label.setWordWrap(True)
        if class_name:
            style.apply_class(label, class_name)
        self._detail_layout.addWidget(label)
        return label

    def _render_detail(self, detail: Mapping) -> None:
        self._clear_detail()

        id_venta = str(detail["id_venta"])
        fecha, hora = _split_fecha_hora(str(detail.get("fecha_venta") or ""))
        medio = str(detail.get("nombre_medio") or "")
        total = format_cop(int(detail["valor_total"]))
        editable = bool(detail.get("editable"))

        self._add_detail_label(
            "historial_detail_id",
            f"ID: {id_venta}",
            class_name="dialog-text",
        )
        self._add_detail_label(
            "historial_detail_fecha",
            f"Fecha: {fecha}" + (f"  Hora: {hora}" if hora else ""),
            class_name="dialog-text",
        )
        self._add_detail_label(
            "historial_detail_medio",
            f"Medio de pago: {medio}",
            class_name="dialog-text",
        )
        self._add_detail_label(
            "historial_detail_total",
            f"Total: {total}",
            class_name="dialog-text",
        )

        lineas = list(detail.get("lineas") or [])
        if detail.get("es_legado") or not lineas:
            self._add_detail_label(
                "historial_detail_legado",
                _LEGADO_SIN_LINEAS,
                class_name="dialog-text",
            )
        else:
            lines_title = self._add_detail_label(
                "historial_detail_lineas_title",
                "Productos",
                class_name="dialog-text",
            )
            lines_title.setStyleSheet("font-weight: bold;")
            for index, line in enumerate(lineas):
                nombre = str(line.get("nombre_producto") or "")
                cantidad = int(line.get("cantidad") or 0)
                precio = format_cop(int(line.get("precio_aplicado") or 0))
                subtotal = format_cop(int(line.get("subtotal") or 0))
                line_total = format_cop(int(line.get("total") or 0))
                text = (
                    f"{nombre} × {cantidad} — unitario {precio} — "
                    f"subtotal {subtotal} — cobrado {line_total}"
                )
                promo_nombre = line.get("nombre_promocion")
                if promo_nombre:
                    text = f"{text} — promo: {promo_nombre}"
                self._add_detail_label(
                    f"historial_detail_line_{index}",
                    text,
                )

        observaciones = list(detail.get("observaciones") or [])
        obs_title = self._add_detail_label(
            "historial_detail_obs_title",
            "Observaciones",
            class_name="dialog-text",
        )
        obs_title.setStyleSheet("font-weight: bold;")
        if not observaciones:
            self._add_detail_label(
                "historial_detail_obs_empty",
                "Sin observaciones.",
            )
        else:
            for index, obs in enumerate(observaciones):
                origen = str(obs.get("origen") or "")
                origen_label = _ORIGEN_LABELS.get(origen, origen)
                texto = str(obs.get("texto") or "")
                fecha_obs = str(obs.get("fecha_creacion") or "")
                self._add_detail_label(
                    f"historial_detail_obs_{index}",
                    f"[{origen_label}] {texto}"
                    + (f" ({fecha_obs})" if fecha_obs else ""),
                )

        actions = QHBoxLayout()
        if editable:
            edit = QPushButton("Editar")
            edit.setObjectName("historial_edit_button")
            style.apply_class(edit, "dialog-action-button")
            edit.setMinimumHeight(style.DIALOG_ACTION_BUTTON_MIN_HEIGHT)
            edit.clicked.connect(self._on_edit)
            actions.addWidget(edit)

        add_obs = QPushButton("Agregar observación")
        add_obs.setObjectName("historial_add_observacion_button")
        style.apply_class(add_obs, "dialog-action-button")
        add_obs.setMinimumHeight(style.DIALOG_ACTION_BUTTON_MIN_HEIGHT)
        add_obs.clicked.connect(self._on_add_observacion)
        actions.addWidget(add_obs)
        self._detail_layout.addLayout(actions)

        self._detail_layout.addStretch(1)

    def _on_add_observacion(self) -> None:
        id_venta = self._current_detail_id
        if not id_venta:
            return
        dialog = AddObservacionDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        texto = dialog.texto()
        if not texto:
            QMessageBox.warning(
                self,
                "Observación",
                "La observación no puede estar vacía.",
            )
            return
        try:
            self._api.add_sale_observacion(id_venta, texto)
        except httpx.HTTPError as exc:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo guardar la observación.\n{exc}",
            )
            return
        self._open_detail(id_venta)

    def _on_edit(self) -> None:
        detail = self._current_detail
        if detail is None or not detail.get("editable"):
            return
        id_venta = str(detail["id_venta"])
        try:
            products = list(self._api.list_active_products())
            methods = list(self._api.list_payment_methods())
        except httpx.HTTPError as exc:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo cargar datos para editar.\n{exc}",
            )
            return

        self._edit_id = id_venta
        self._edit_es_legado = bool(detail.get("es_legado")) or not list(
            detail.get("lineas") or []
        )
        self._edit_medio_id = int(detail["id_medio_pago"])
        self._edit_medio_nombre = str(detail.get("nombre_medio") or "")
        self._edit_products = products
        self._edit_payment_methods = methods
        self._edit_lines = []
        if not self._edit_es_legado:
            by_id = {int(p["id_producto"]): p for p in products}
            for line in detail.get("lineas") or []:
                id_producto = int(line["id_producto"])
                product = by_id.get(id_producto)
                precio = (
                    int(product["precio"])
                    if product is not None
                    else int(line.get("precio_aplicado") or 0)
                )
                nombre = (
                    str(product["nombre"])
                    if product is not None
                    else str(line.get("nombre_producto") or "")
                )
                self._edit_lines.append(
                    {
                        "id_producto": id_producto,
                        "nombre": nombre,
                        "precio_aplicado": precio,
                        "cantidad": int(line.get("cantidad") or 0),
                    }
                )

        self._edit_window_label.setText(
            _ventana_hasta_label(str(detail.get("fecha_venta") or ""))
        )
        self._edit_medio_button.setText(
            self._edit_medio_nombre or _PAYMENT_BUTTON_PLACEHOLDER
        )
        last_durante = _last_durante_venta_texto(
            list(detail.get("observaciones") or [])
        )
        self._edit_obs_input.setText(last_durante or "")
        self._edit_legado_label.setVisible(self._edit_es_legado)
        self._edit_add_product_button.setVisible(not self._edit_es_legado)
        self._edit_lines_host.setVisible(not self._edit_es_legado)
        self._rebuild_edit_lines()
        self._stack.setCurrentWidget(self._edit_page)

    def _cancel_edit(self) -> None:
        id_venta = self._edit_id or self._current_detail_id
        if id_venta:
            self._open_detail(id_venta)
        else:
            self._show_list()

    def _rebuild_edit_lines(self) -> None:
        while self._edit_lines_layout.count():
            item = self._edit_lines_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                # Evita que findChild encuentre filas pendientes de deleteLater.
                widget.setObjectName("")
                for child in widget.findChildren(QWidget):
                    child.setObjectName("")
                widget.deleteLater()

        if self._edit_es_legado:
            self._edit_lines_layout.addStretch(1)
            return

        for index, line in enumerate(self._edit_lines):
            self._edit_lines_layout.addWidget(self._make_edit_line_row(index, line))
        self._edit_lines_layout.addStretch(1)

    def _make_edit_line_row(self, index: int, line: Mapping) -> QWidget:
        row = QWidget()
        row.setObjectName(f"historial_edit_line_row_{index}")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(style.PAGE_SPACING)

        label = QLabel(
            f"{line['nombre']} · {format_cop(int(line['precio_aplicado']))}"
        )
        label.setObjectName(f"historial_edit_line_label_{index}")
        label.setWordWrap(True)
        style.apply_class(label, "dialog-text")
        layout.addWidget(label, stretch=1)

        qty = QLabel(str(int(line["cantidad"])))
        qty.setObjectName(f"historial_edit_line_qty_{index}")
        style.apply_class(qty, "dialog-text")
        layout.addWidget(qty)

        minus = QPushButton("−")
        minus.setObjectName(f"historial_edit_line_minus_{index}")
        style.apply_class(minus, "payment-method-button")
        minus.clicked.connect(
            lambda checked=False, i=index: self._edit_line_delta(i, -1)
        )
        layout.addWidget(minus)

        plus = QPushButton("+")
        plus.setObjectName(f"historial_edit_line_plus_{index}")
        style.apply_class(plus, "payment-method-button")
        plus.clicked.connect(
            lambda checked=False, i=index: self._edit_line_delta(i, 1)
        )
        layout.addWidget(plus)

        remove = QPushButton("Quitar")
        remove.setObjectName(f"historial_edit_line_remove_{index}")
        style.apply_class(remove, "payment-method-button")
        remove.clicked.connect(
            lambda checked=False, i=index: self._edit_line_remove(i)
        )
        layout.addWidget(remove)
        return row

    def _edit_line_delta(self, index: int, delta: int) -> None:
        if index < 0 or index >= len(self._edit_lines):
            return
        new_qty = int(self._edit_lines[index]["cantidad"]) + delta
        if new_qty <= 0:
            self._edit_line_remove(index)
            return
        self._edit_lines[index]["cantidad"] = new_qty
        self._rebuild_edit_lines()

    def _edit_line_remove(self, index: int) -> None:
        if index < 0 or index >= len(self._edit_lines):
            return
        del self._edit_lines[index]
        self._rebuild_edit_lines()

    def _on_edit_change_medio(self) -> None:
        methods = getattr(self, "_edit_payment_methods", None) or []
        if not methods:
            try:
                methods = list(self._api.list_payment_methods())
                self._edit_payment_methods = methods
            except httpx.HTTPError as exc:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"No se pudieron cargar medios de pago.\n{exc}",
                )
                return
        dialog = SelectPaymentMethodDialog(methods, self)
        if dialog.exec() != QDialog.Accepted:
            return
        method = dialog.selected_method()
        if method is None:
            return
        self._edit_medio_id = int(method["id_medio_pago"])
        self._edit_medio_nombre = str(method["nombre"])
        self._edit_medio_button.setText(self._edit_medio_nombre)

    def _on_edit_add_product(self) -> None:
        if self._edit_es_legado:
            return
        if not self._edit_products:
            QMessageBox.warning(
                self,
                "Productos",
                "No hay productos activos para agregar.",
            )
            return
        dialog = SelectProductDialog(self._edit_products, self)
        if dialog.exec() != QDialog.Accepted:
            return
        product = dialog.selected_product()
        if product is None:
            return
        id_producto = int(product["id_producto"])
        for line in self._edit_lines:
            if int(line["id_producto"]) == id_producto:
                line["cantidad"] = int(line["cantidad"]) + 1
                line["precio_aplicado"] = int(product["precio"])
                line["nombre"] = str(product["nombre"])
                self._rebuild_edit_lines()
                return
        self._edit_lines.append(
            {
                "id_producto": id_producto,
                "nombre": str(product["nombre"]),
                "precio_aplicado": int(product["precio"]),
                "cantidad": 1,
            }
        )
        self._rebuild_edit_lines()

    def _on_edit_save(self) -> None:
        id_venta = self._edit_id
        if not id_venta or self._edit_medio_id is None:
            return
        if not self._edit_es_legado and not self._edit_lines:
            QMessageBox.warning(
                self,
                "Edición",
                "Debe quedar al menos un producto.",
            )
            return

        if not self._edit_es_legado:
            try:
                fresh = list(self._api.list_active_products())
            except httpx.HTTPError as exc:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"No se pudo revalidar el catálogo.\n{exc}",
                )
                return
            by_id = {int(p["id_producto"]): p for p in fresh}
            for line in self._edit_lines:
                product = by_id.get(int(line["id_producto"]))
                if product is None:
                    QMessageBox.warning(
                        self,
                        "Edición",
                        f"El producto {line['nombre']} ya no está activo.",
                    )
                    return
                line["precio_aplicado"] = int(product["precio"])
                line["nombre"] = str(product["nombre"])

        line_summary = (
            _LEGADO_SIN_LINEAS
            if self._edit_es_legado
            else "; ".join(
                f"{line['nombre']} × {line['cantidad']}" for line in self._edit_lines
            )
        )
        confirm = ConfirmEditDialog(
            payment_name=self._edit_medio_nombre or "",
            line_summary=line_summary,
            parent=self,
        )
        if confirm.exec() != QDialog.Accepted:
            return

        lineas: List[Mapping] = []
        if not self._edit_es_legado:
            for line in self._edit_lines:
                lineas.append(
                    {
                        "id_producto": int(line["id_producto"]),
                        "cantidad": int(line["cantidad"]),
                        "precio_aplicado": int(line["precio_aplicado"]),
                    }
                )
        observacion = self._edit_obs_input.text().strip() or None
        try:
            self._api.update_sale(
                id_venta,
                id_medio_pago=int(self._edit_medio_id),
                lineas=lineas,
                observacion_venta=observacion,
            )
        except httpx.HTTPError as exc:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo guardar la edición.\n{exc}",
            )
            return
        self._open_detail(id_venta)
