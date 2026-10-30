"""Beta 2.1 Etapa 4: desktop Historial + detalle (solo lectura)."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, List, Mapping, Optional

import httpx
from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import QApplication

from bakery.app.money import format_cop
from bakery.desktop.historial_page import _LEGADO_SIN_LINEAS
from bakery.desktop.main import create_window
from bakery.persistence.schema import ESTADO_ACTIVO


class HistorialFakeApiClient:
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
            }
        ]
        self._list_rows: List[Mapping[str, Any]] = []
        self._details: dict[str, Mapping[str, Any]] = {}

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
    ) -> Mapping[str, Any]:
        self.request_count += 1
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
        medio = next(
            (m["nombre"] for m in self.methods if m["id_medio_pago"] == id_medio_pago),
            "",
        )
        fecha = "2026-10-30T14:30:00"
        list_row = {
            "id_venta": id_venta,
            "valor_total": valor_total,
            "fecha_venta": fecha,
            "id_medio_pago": id_medio_pago,
            "nombre_medio": medio,
            "caja": 1,
            "tendero": 1,
            "cantidad_lineas": len(detail_lineas),
            "es_legado": False,
            "editable": True,
        }
        detail = {
            **list_row,
            "lineas": detail_lineas,
            "observaciones": [
                {
                    "id_observacion": 1,
                    "id_venta": id_venta,
                    "texto": "Cliente habitual",
                    "origen": "durante_venta",
                    "fecha_creacion": fecha,
                    "id_cambio": None,
                }
            ],
        }
        self._list_rows.insert(0, list_row)
        self._details[id_venta] = detail
        return {
            "id_venta": id_venta,
            "valor_total": valor_total,
            "fecha_venta": fecha,
            "id_medio_pago": id_medio_pago,
            "caja": 1,
            "tendero": 1,
        }

    def list_sales(self) -> List[Mapping[str, Any]]:
        self.request_count += 1
        return [dict(row) for row in self._list_rows]

    def get_sale(self, id_venta: str) -> Mapping[str, Any]:
        self.request_count += 1
        detail = self._details.get(id_venta)
        if detail is None:
            raise httpx.HTTPStatusError(
                "Venta no encontrada.",
                request=httpx.Request("GET", f"/ventas/{id_venta}"),
                response=httpx.Response(404),
            )
        return dict(detail)

    def seed_legado(self, id_venta: str = "legado-1") -> None:
        list_row = {
            "id_venta": id_venta,
            "valor_total": 8000,
            "fecha_venta": "2026-01-01T10:00:00",
            "id_medio_pago": 1,
            "nombre_medio": "Efectivo",
            "caja": 1,
            "tendero": 1,
            "cantidad_lineas": 0,
            "es_legado": True,
            "editable": False,
        }
        self._list_rows.insert(0, list_row)
        self._details[id_venta] = {
            **list_row,
            "lineas": [],
            "observaciones": [],
        }


def _click(qtbot, widget) -> None:
    qtbot.mouseClick(widget, Qt.LeftButton)


def _find(window, name: str):
    widget = window.findChild(QObject, name)
    assert widget is not None, f"No se encontró {name}"
    return widget


def test_menu_historial_button_opens_list(qtbot) -> None:
    api = HistorialFakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    button = _find(window, "menu_historial_button")
    assert button.text() == "Historial"
    _click(qtbot, button)

    assert window._stack.currentWidget() is window._historial
    assert _find(window, "historial_title").text() == "Historial"
    empty = _find(window, "historial_empty")
    assert not empty.isHidden()
    assert empty.text() == "No hay ventas registradas."


def test_historial_shows_sale_created_via_api_and_detail(qtbot) -> None:
    api = HistorialFakeApiClient()
    created = api.create_sale(
        1,
        [{"id_producto": 1, "cantidad": 2, "precio_aplicado": 5000}],
        id_venta=str(uuid.uuid4()),
    )
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    before = api.request_count
    _click(qtbot, _find(window, "menu_historial_button"))
    assert api.request_count == before + 1

    row = _find(window, f"historial_row_{created['id_venta']}")
    assert "2026-10-30" in row.text()
    assert "14:30:00" in row.text()
    assert format_cop(10000) in row.text()
    assert "Efectivo" in row.text()
    assert "1 ítem" in row.text()

    _click(qtbot, row)
    assert window._historial._stack.currentWidget() is window._historial._detail_page
    assert created["id_venta"] in _find(window, "historial_detail_id").text()
    assert "2026-10-30" in _find(window, "historial_detail_fecha").text()
    assert "14:30:00" in _find(window, "historial_detail_fecha").text()
    assert "Efectivo" in _find(window, "historial_detail_medio").text()
    assert format_cop(10000) in _find(window, "historial_detail_total").text()
    line = _find(window, "historial_detail_line_0")
    assert "Pan" in line.text()
    assert "× 2" in line.text()
    assert format_cop(5000) in line.text()
    obs = _find(window, "historial_detail_obs_0")
    assert "Durante la venta" in obs.text()
    assert "Cliente habitual" in obs.text()
    # Etapa 8: editable=true muestra Editar; obs posterior sigue disponible.
    assert window.findChild(QObject, "historial_edit_button") is not None
    assert window.findChild(QObject, "historial_add_observacion_button") is not None

    _click(qtbot, _find(window, "historial_detail_back_button"))
    assert window._historial._stack.currentWidget() is window._historial._list_page
    _click(qtbot, _find(window, "historial_back_button"))
    assert window._stack.currentWidget() is window._menu


def test_historial_legado_shows_fixed_message(qtbot) -> None:
    api = HistorialFakeApiClient()
    api.seed_legado("legado-ui-1")
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()

    _click(qtbot, _find(window, "menu_historial_button"))
    row = _find(window, "historial_row_legado-ui-1")
    assert "Venta antigua" in row.text()
    _click(qtbot, row)
    assert _find(window, "historial_detail_legado").text() == _LEGADO_SIN_LINEAS
    assert window.findChild(QObject, "historial_detail_line_0") is None


def test_api_client_list_and_get_sale(tmp_path: Path) -> None:
    """ApiClient.list_sales / get_sale contra la API real (Etapa 3)."""
    from fastapi.testclient import TestClient

    from bakery.api.app import create_app
    from bakery.desktop.client import ApiClient

    db_path = tmp_path / "bakery.sqlite3"
    with TestClient(create_app(db_path)) as test_client:
        product = test_client.post(
            "/productos",
            json={"nombre": "Pan", "precio": 5000, "id_categoria": 1},
        ).json()
        id_venta = str(uuid.uuid4())
        created = test_client.post(
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
        ).json()
        assert created["id_venta"] == id_venta

        def handler(request: httpx.Request) -> httpx.Response:
            method = request.method
            path = request.url.path
            if method == "GET" and path == "/ventas":
                upstream = test_client.get("/ventas")
            elif method == "GET" and path.startswith("/ventas/"):
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
            rows = client.list_sales()
            assert any(row["id_venta"] == id_venta for row in rows)
            detail = client.get_sale(id_venta)
            assert detail["id_venta"] == id_venta
            assert detail["lineas"][0]["nombre_producto"] == "Pan"
            assert "editable" in detail
            assert detail["es_legado"] is False
        finally:
            client.close()
