"""Página Historial de ventas (Beta 2.1: lectura + observación posterior)."""

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
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from bakery.app.money import format_cop
from bakery.desktop import style
from bakery.desktop.client import ApiClient
from bakery.desktop.dialogs import AddObservacionDialog
from bakery.desktop.ui_helpers import _BACK_BUTTON_ARROW, _apply_page_layout

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


class HistorialPage(QWidget):
    def __init__(self, api_client: ApiClient, on_back=None) -> None:
        super().__init__()
        self.setObjectName("historial_page")
        self._api = api_client
        self._on_back = on_back
        self._sales: List[Mapping] = []
        self._current_detail_id: Optional[str] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.setObjectName("historial_stack")
        root.addWidget(self._stack)

        self._list_page = self._build_list_page()
        self._detail_page = self._build_detail_page()
        self._stack.addWidget(self._list_page)
        self._stack.addWidget(self._detail_page)
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
        self._render_detail(detail)
        self._stack.setCurrentWidget(self._detail_page)

    def _clear_detail(self) -> None:
        while self._detail_layout.count():
            item = self._detail_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

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

        add_obs = QPushButton("Agregar observación")
        add_obs.setObjectName("historial_add_observacion_button")
        style.apply_class(add_obs, "dialog-action-button")
        add_obs.setMinimumHeight(style.DIALOG_ACTION_BUTTON_MIN_HEIGHT)
        add_obs.clicked.connect(self._on_add_observacion)
        self._detail_layout.addWidget(add_obs)

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
