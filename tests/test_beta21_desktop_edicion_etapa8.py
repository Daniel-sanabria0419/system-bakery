"""Beta 2.1 Etapa 8: desktop edición ≤1 h + obs posterior."""

from __future__ import annotations

import uuid
from typing import Any, List, Mapping, Optional

import httpx
from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtWidgets import QApplication, QLineEdit, QMessageBox

from bakery.app.money import format_cop
from bakery.desktop.dialogs import (
    AddObservacionDialog,
    ConfirmEditDialog,
    SelectPaymentMethodDialog,
)
from bakery.desktop.main import create_window
from bakery.persistence.schema import ESTADO_ACTIVO
from tests.test_stage4_desktop import _click, _find


class EditFakeApiClient:
    def __init__(self) -> None:
        self.request_count = 0
        self.methods = [
            {"id_medio_pago": 1, "nombre": "Efectivo", "id_estado": ESTADO_ACTIVO},
            {"id_medio_pago": 2, "nombre": "Nequi", "id_estado": ESTADO_ACTIVO},
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
            },
            {
                "id_producto": 2,
                "nombre": "Café",
                "precio": 3000,
                "id_categoria": 1,
                "descripcion": None,
                "id_estado": ESTADO_ACTIVO,
            },
        ]
        self.sales: List[Mapping[str, Any]] = []
        self._details: dict[str, Mapping[str, Any]] = {}
        self.update_calls: List[Mapping[str, Any]] = []
        self.posted_observaciones: List[tuple[str, str]] = []
        self.force_update_error: Optional[httpx.HTTPStatusError] = None

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
        editable: bool = True,
    ) -> Mapping[str, Any]:
        self.request_count += 1
        medio = next(m for m in self.methods if m["id_medio_pago"] == id_medio_pago)
        detail_lineas = []
        valor_total = 0
        for index, line in enumerate(lineas):
            product = next(
                (p for p in self.products if p["id_producto"] == line["id_producto"]),
                None,
            )
            nombre = product["nombre"] if product else f"#{line['id_producto']}"
            precio = int(line["precio_aplicado"])
            cantidad = int(line["cantidad"])
            subtotal = precio * cantidad
            valor_total += subtotal
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
            "nombre_medio": medio["nombre"],
            "caja": 1,
            "tendero": 1,
            "lineas": detail_lineas,
            "observaciones": observaciones,
            "es_legado": False,
            "editable": editable,
        }
        self._details[id_venta] = detail
        self.sales.append(
            {
                "id_venta": id_venta,
                "valor_total": valor_total,
                "fecha_venta": "2026-10-30T12:00:00",
                "id_medio_pago": id_medio_pago,
                "nombre_medio": medio["nombre"],
                "caja": 1,
                "tendero": 1,
                "cantidad_lineas": len(detail_lineas),
                "es_legado": False,
                "editable": editable,
            }
        )
        return {
            "id_venta": id_venta,
            "valor_total": valor_total,
            "fecha_venta": "2026-10-30T12:00:00",
            "id_medio_pago": id_medio_pago,
            "caja": 1,
            "tendero": 1,
        }

    def seed_legado(self, id_venta: str, *, editable: bool) -> None:
        detail = {
            "id_venta": id_venta,
            "valor_total": 8000,
            "fecha_venta": "2026-10-30T10:00:00",
            "id_medio_pago": 1,
            "nombre_medio": "Efectivo",
            "caja": 1,
            "tendero": 1,
            "lineas": [],
            "observaciones": [],
            "es_legado": True,
            "editable": editable,
        }
        self._details[id_venta] = detail
        self.sales.append(
            {
                "id_venta": id_venta,
                "valor_total": 8000,
                "fecha_venta": "2026-10-30T10:00:00",
                "id_medio_pago": 1,
                "nombre_medio": "Efectivo",
                "caja": 1,
                "tendero": 1,
                "cantidad_lineas": 0,
                "es_legado": True,
                "editable": editable,
            }
        )

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

    def update_sale(
        self,
        id_venta: str,
        *,
        id_medio_pago: int,
        lineas: List[Mapping[str, Any]],
        observacion_venta: Optional[str] = None,
    ) -> Mapping[str, Any]:
        self.request_count += 1
        self.update_calls.append(
            {
                "id_venta": id_venta,
                "id_medio_pago": id_medio_pago,
                "lineas": list(lineas),
                "observacion_venta": observacion_venta,
            }
        )
        if self.force_update_error is not None:
            raise self.force_update_error

        detail = dict(self._details[id_venta])
        if not detail.get("editable"):
            request = httpx.Request("PUT", f"http://test/ventas/{id_venta}")
            response = httpx.Response(409, request=request)
            raise httpx.HTTPStatusError(
                "La venta solo se puede editar dentro de la primera hora.",
                request=request,
                response=response,
            )

        medio = next(m for m in self.methods if m["id_medio_pago"] == id_medio_pago)
        if detail.get("es_legado"):
            detail_lineas: List[Mapping[str, Any]] = []
            valor_total = int(detail["valor_total"])
        else:
            detail_lineas = []
            valor_total = 0
            for index, line in enumerate(lineas):
                product = next(
                    p
                    for p in self.products
                    if p["id_producto"] == line["id_producto"]
                )
                precio = int(line["precio_aplicado"])
                cantidad = int(line["cantidad"])
                subtotal = precio * cantidad
                valor_total += subtotal
                detail_lineas.append(
                    {
                        "id_linea": index + 1,
                        "id_venta": id_venta,
                        "id_producto": line["id_producto"],
                        "nombre_producto": product["nombre"],
                        "precio_aplicado": precio,
                        "cantidad": cantidad,
                        "subtotal": subtotal,
                        "total": subtotal,
                        "id_promocion": None,
                        "nombre_promocion": None,
                    }
                )

        observaciones = list(detail.get("observaciones") or [])
        if observacion_venta:
            last_durante = None
            for obs in observaciones:
                if obs.get("origen") == "durante_venta":
                    last_durante = obs.get("texto")
            if observacion_venta != last_durante:
                observaciones.append(
                    {
                        "id_observacion": len(observaciones) + 1,
                        "id_venta": id_venta,
                        "texto": observacion_venta,
                        "origen": "durante_venta",
                        "fecha_creacion": "2026-10-30T12:30:00",
                        "id_cambio": 20,
                    }
                )

        detail.update(
            {
                "valor_total": valor_total,
                "id_medio_pago": id_medio_pago,
                "nombre_medio": medio["nombre"],
                "lineas": detail_lineas,
                "observaciones": observaciones,
            }
        )
        self._details[id_venta] = detail
        for row in self.sales:
            if row["id_venta"] == id_venta:
                row["valor_total"] = valor_total
                row["id_medio_pago"] = id_medio_pago
                row["nombre_medio"] = medio["nombre"]
                row["cantidad_lineas"] = len(detail_lineas)
                break
        return {
            "id_venta": id_venta,
            "valor_total": valor_total,
            "fecha_venta": detail["fecha_venta"],
            "id_medio_pago": id_medio_pago,
            "caja": 1,
            "tendero": 1,
        }

    def close(self) -> None:
        return None


def _open_detail(qtbot, window, api, id_venta: str) -> None:
    _click(qtbot, _find(window, "menu_historial_button"))
    qtbot.waitUntil(
        lambda: window.findChild(QObject, f"historial_row_{id_venta}") is not None
    )
    _click(qtbot, _find(window, f"historial_row_{id_venta}"))
    qtbot.waitUntil(
        lambda: window.findChild(QObject, "historial_detail_id") is not None
    )


def test_editable_shows_edit_and_obs_actions(qtbot) -> None:
    api = EditFakeApiClient()
    id_venta = str(uuid.uuid4())
    api.create_sale(
        1,
        [{"id_producto": 1, "cantidad": 1, "precio_aplicado": 5000}],
        id_venta=id_venta,
        observacion="Durante",
        editable=True,
    )
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _open_detail(qtbot, window, api, id_venta)

    assert window.findChild(QObject, "historial_edit_button") is not None
    assert window.findChild(QObject, "historial_add_observacion_button") is not None


def test_not_editable_hides_edit_keeps_obs(qtbot) -> None:
    api = EditFakeApiClient()
    id_venta = str(uuid.uuid4())
    api.create_sale(
        1,
        [{"id_producto": 1, "cantidad": 1, "precio_aplicado": 5000}],
        id_venta=id_venta,
        editable=False,
    )
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _open_detail(qtbot, window, api, id_venta)

    assert window.findChild(QObject, "historial_edit_button") is None
    assert window.findChild(QObject, "historial_add_observacion_button") is not None


def test_edit_flow_updates_qty_medio_and_obs(qtbot) -> None:
    api = EditFakeApiClient()
    id_venta = str(uuid.uuid4())
    api.create_sale(
        1,
        [{"id_producto": 1, "cantidad": 1, "precio_aplicado": 5000}],
        id_venta=id_venta,
        observacion="Original",
        editable=True,
    )
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _open_detail(qtbot, window, api, id_venta)
    _click(qtbot, _find(window, "historial_edit_button"))
    qtbot.waitUntil(
        lambda: window.findChild(QObject, "historial_edit_page") is not None
        and window._historial._stack.currentWidget() is window._historial._edit_page
    )

    assert "informativo" in _find(window, "historial_edit_window_label").text()
    assert _find(window, "historial_edit_obs_input").text() == "Original"
    _click(qtbot, _find(window, "historial_edit_line_plus_0"))
    assert _find(window, "historial_edit_line_qty_0").text() == "2"

    def pick_nequi() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, SelectPaymentMethodDialog):
                _click(qtbot, _find(widget, "payment_method_2"))
                return

    QTimer.singleShot(0, pick_nequi)
    _click(qtbot, _find(window, "historial_edit_medio_button"))
    qtbot.waitUntil(
        lambda: _find(window, "historial_edit_medio_button").text() == "Nequi",
        timeout=2000,
    )

    _find(window, "historial_edit_obs_input").setText("Corregida")

    def accept_confirm() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ConfirmEditDialog):
                widget.accept()
                return

    QTimer.singleShot(0, accept_confirm)
    _click(qtbot, _find(window, "historial_edit_save_button"))
    qtbot.waitUntil(lambda: len(api.update_calls) == 1, timeout=2000)

    call = api.update_calls[0]
    assert call["id_venta"] == id_venta
    assert call["id_medio_pago"] == 2
    assert call["observacion_venta"] == "Corregida"
    assert call["lineas"] == [
        {"id_producto": 1, "cantidad": 2, "precio_aplicado": 5000}
    ]
    assert format_cop(10000) in _find(window, "historial_detail_total").text()
    assert "Nequi" in _find(window, "historial_detail_medio").text()


def test_edit_window_409_shows_error(qtbot) -> None:
    api = EditFakeApiClient()
    id_venta = str(uuid.uuid4())
    api.create_sale(
        1,
        [{"id_producto": 1, "cantidad": 1, "precio_aplicado": 5000}],
        id_venta=id_venta,
        editable=True,
    )
    request = httpx.Request("PUT", f"http://test/ventas/{id_venta}")
    response = httpx.Response(409, request=request)
    api.force_update_error = httpx.HTTPStatusError(
        "La venta solo se puede editar dentro de la primera hora.",
        request=request,
        response=response,
    )
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _open_detail(qtbot, window, api, id_venta)
    _click(qtbot, _find(window, "historial_edit_button"))
    qtbot.waitUntil(
        lambda: window._historial._stack.currentWidget()
        is window._historial._edit_page
    )

    seen: dict[str, str] = {}

    def accept_confirm_then_capture() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ConfirmEditDialog):
                widget.accept()

                def capture_box() -> None:
                    for box in QApplication.topLevelWidgets():
                        if isinstance(box, QMessageBox):
                            seen["text"] = box.text()
                            box.accept()
                            return

                QTimer.singleShot(0, capture_box)
                return

    QTimer.singleShot(0, accept_confirm_then_capture)
    _click(qtbot, _find(window, "historial_edit_save_button"))
    qtbot.waitUntil(lambda: "text" in seen, timeout=2000)
    assert "primera hora" in seen["text"]
    assert len(api.update_calls) == 1


def test_obs_posterior_available_when_not_editable(qtbot) -> None:
    api = EditFakeApiClient()
    id_venta = str(uuid.uuid4())
    api.create_sale(
        1,
        [{"id_producto": 1, "cantidad": 1, "precio_aplicado": 5000}],
        id_venta=id_venta,
        editable=False,
    )
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _open_detail(qtbot, window, api, id_venta)

    def accept_obs() -> None:
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, AddObservacionDialog):
                field = widget.findChild(QLineEdit, "add_observacion_input")
                assert field is not None
                field.setText("Fuera de ventana")
                widget.accept()
                return

    QTimer.singleShot(0, accept_obs)
    _click(qtbot, _find(window, "historial_add_observacion_button"))
    qtbot.waitUntil(lambda: len(api.posted_observaciones) == 1, timeout=2000)
    assert api.posted_observaciones == [(id_venta, "Fuera de ventana")]


def test_api_client_update_sale(tmp_path) -> None:
    from pathlib import Path

    from fastapi.testclient import TestClient

    from bakery.api.app import create_app
    from bakery.desktop.client import ApiClient

    db_path = Path(tmp_path) / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as test_client:
        product = test_client.post(
            "/productos",
            json={"nombre": "Pan", "precio": 5000, "id_categoria": 1},
        ).json()
        id_venta = str(uuid.uuid4())
        test_client.post(
            "/ventas",
            json={
                "id_venta": id_venta,
                "id_medio_pago": 1,
                "lineas": [
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 1,
                        "precio_aplicado": 5000,
                    }
                ],
            },
        )

        def handler(request: httpx.Request) -> httpx.Response:
            method = request.method
            path = request.url.path
            if method == "PUT" and path == f"/ventas/{id_venta}":
                upstream = test_client.put(path, content=request.content)
            elif method == "GET" and path == f"/ventas/{id_venta}":
                upstream = test_client.get(path)
            else:
                return httpx.Response(404, json={"detail": "not found"})
            return httpx.Response(
                upstream.status_code,
                content=upstream.content,
                headers={
                    "content-type": upstream.headers.get(
                        "content-type", "application/json"
                    )
                },
            )

        client = ApiClient(transport=httpx.MockTransport(handler))
        try:
            updated = client.update_sale(
                id_venta,
                id_medio_pago=2,
                lineas=[
                    {
                        "id_producto": product["id_producto"],
                        "cantidad": 2,
                        "precio_aplicado": 5000,
                    }
                ],
                observacion_venta="Desde cliente",
            )
            assert updated["id_medio_pago"] == 2
            assert updated["valor_total"] == 10000
            detail = client.get_sale(id_venta)
            assert detail["editable"] is True
            assert detail["id_medio_pago"] == 2
        finally:
            client.close()
