"""Beta 2.1 Etapa 5: desktop obs en confirmar + agregar en historial."""

from __future__ import annotations

import uuid
from typing import Any, List, Mapping, Optional

from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtWidgets import QApplication, QLineEdit

from bakery.desktop.dialogs import AddObservacionDialog, ConfirmSaleDialog, SaleSavedDialog
from bakery.desktop.main import create_window
from bakery.persistence.schema import ESTADO_ACTIVO
from tests.test_stage4_desktop import _click, _find, _select_payment


class ObsFakeApiClient:
    def __init__(self) -> None:
        self.request_count = 0
        self.methods = [
            {"id_medio_pago": 1, "nombre": "Efectivo", "id_estado": ESTADO_ACTIVO},
        ]
        self.categories = [{"id_categoria": 1, "nombre": "Panadería"}]
        self.products = [
            {
                "id_producto": 1,
                "nombre": "Pan",
                "precio": 5000,
                "id_categoria": 1,
                "descripcion": None,
                "id_estado": ESTADO_ACTIVO,
            }
        ]
        self.sales: List[Mapping[str, Any]] = []
        self._details: dict[str, Mapping[str, Any]] = {}
        self.last_create_observacion: Optional[str] = None
        self.posted_observaciones: List[tuple[str, str]] = []

    def list_payment_methods(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        return list(self.methods)

    def list_categories(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        return list(self.categories)

    def list_products(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        return [dict(p) for p in self.products]

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

    def create_sale(
        self,
        id_medio_pago: int,
        lineas: List[Mapping[str, Any]],
        *,
        id_venta: str,
        observacion: Optional[str] = None,
    ) -> Mapping[str, Any]:
        self.request_count += 1
        self.last_create_observacion = observacion
        valor_total = sum(
            int(line["precio_aplicado"]) * int(line["cantidad"]) for line in lineas
        )
        detail_lineas = []
        for index, line in enumerate(lineas):
            product = next(
                (p for p in self.products if p["id_producto"] == line["id_producto"]),
                None,
            )
            nombre = product["nombre"] if product else f"#{line['id_producto']}"
            precio = int(line["precio_aplicado"])
            cantidad = int(line["cantidad"])
            subtotal = precio * cantidad
            detail_lineas.append(
                {
                    "id_linea": index + 1,
                    "id_venta": id_venta,
                    "id_producto": line["id_producto"],
                    "nombre_producto": nombre,
                    "precio_aplicado": precio,
                    "cantidad": cantidad,
                    "subtotal": subtotal,
                    "total": subtotal,
                    "id_promocion": None,
                    "nombre_promocion": None,
                }
            )
        observaciones: List[Mapping[str, Any]] = []
        if observacion:
            observaciones.append(
                {
                    "id_observacion": 1,
                    "id_venta": id_venta,
                    "texto": observacion,
                    "origen": "durante_venta",
                    "fecha_creacion": "2026-10-30T12:00:00",
                    "id_cambio": 1,
                }
            )
        detail = {
            "id_venta": id_venta,
            "valor_total": valor_total,
            "fecha_venta": "2026-10-30T12:00:00",
            "id_medio_pago": id_medio_pago,
            "nombre_medio": "Efectivo",
            "caja": 1,
            "tendero": 1,
            "lineas": detail_lineas,
            "observaciones": observaciones,
            "es_legado": False,
            "editable": True,
        }
        self._details[id_venta] = detail
        list_row = {
            "id_venta": id_venta,
            "valor_total": valor_total,
            "fecha_venta": "2026-10-30T12:00:00",
            "id_medio_pago": id_medio_pago,
            "nombre_medio": "Efectivo",
            "caja": 1,
            "tendero": 1,
            "cantidad_lineas": len(detail_lineas),
            "es_legado": False,
            "editable": True,
        }
        self.sales.append(list_row)
        return {
            "id_venta": id_venta,
            "valor_total": valor_total,
            "fecha_venta": "2026-10-30T12:00:00",
            "id_medio_pago": id_medio_pago,
            "caja": 1,
            "tendero": 1,
        }

    def list_sales(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        return [dict(row) for row in self.sales]

    def get_sale(self, id_venta: str) -> Mapping[str, Any]:
        self.request_count += 1
        return dict(self._details[id_venta])

    def add_sale_observacion(self, id_venta: str, texto: str) -> Mapping[str, Any]:
        self.request_count += 1
        self.posted_observaciones.append((id_venta, texto))
        detail = dict(self._details[id_venta])
        observaciones = list(detail.get("observaciones") or [])
        new_obs = {
            "id_observacion": len(observaciones) + 1,
            "id_venta": id_venta,
            "texto": texto,
            "origen": "posterior",
            "fecha_creacion": "2026-10-30T13:00:00",
            "id_cambio": 10 + len(observaciones),
        }
        observaciones.append(new_obs)
        detail["observaciones"] = observaciones
        self._details[id_venta] = detail
        return new_obs

    def close(self) -> None:
        return None


def test_confirm_dialog_exposes_optional_observacion(qtbot) -> None:
    dialog = ConfirmSaleDialog(5000, "Efectivo")
    qtbot.addWidget(dialog)
    dialog.show()
    field = dialog.findChild(QLineEdit, "confirm_observacion_input")
    assert field is not None
    assert dialog.observacion() is None
    field.setText("  Con bolsa  ")
    assert dialog.observacion() == "Con bolsa"


def test_confirm_posts_observacion_when_filled(qtbot) -> None:
    api = ObsFakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    _click(qtbot, _find(window, "sale_category_todos"))
    _click(qtbot, _find(window, "sale_product_1"))
    _click(qtbot, _find(window, "agregar_button"))
    _select_payment(qtbot, window, 1)

    def accept_flow() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ConfirmSaleDialog):
                field = widget.findChild(QLineEdit, "confirm_observacion_input")
                assert field is not None
                field.setText("Sin bolsas")
                widget.accept()

                def accept_saved() -> None:
                    for saved in QApplication.topLevelWidgets():
                        if isinstance(saved, SaleSavedDialog):
                            saved.accept()
                            return

                QTimer.singleShot(0, accept_saved)
                return

    QTimer.singleShot(0, accept_flow)
    _click(qtbot, _find(window, "submit_sale_button"))
    qtbot.waitUntil(lambda: len(api.sales) == 1, timeout=2000)
    assert api.last_create_observacion == "Sin bolsas"


def test_historial_add_observacion_button(qtbot) -> None:
    api = ObsFakeApiClient()
    id_venta = str(uuid.uuid4())
    api.create_sale(
        1,
        [{"id_producto": 1, "cantidad": 1, "precio_aplicado": 5000}],
        id_venta=id_venta,
        observacion="Durante",
    )
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_historial_button"))
    qtbot.waitUntil(
        lambda: window.findChild(QObject, f"historial_row_{id_venta}") is not None
    )
    _click(qtbot, _find(window, f"historial_row_{id_venta}"))
    qtbot.waitUntil(
        lambda: window.findChild(QObject, "historial_add_observacion_button")
        is not None
    )

    def accept_obs() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, AddObservacionDialog):
                field = widget.findChild(QLineEdit, "add_observacion_input")
                assert field is not None
                field.setText("Posterior desde UI")
                widget.accept()
                return

    QTimer.singleShot(0, accept_obs)
    _click(qtbot, _find(window, "historial_add_observacion_button"))
    qtbot.waitUntil(lambda: len(api.posted_observaciones) == 1, timeout=2000)

    assert api.posted_observaciones == [(id_venta, "Posterior desde UI")]
    obs_label = window.findChild(QObject, "historial_detail_obs_1")
    assert obs_label is not None
    assert "Posterior" in obs_label.text()
    assert "Posterior desde UI" in obs_label.text()
