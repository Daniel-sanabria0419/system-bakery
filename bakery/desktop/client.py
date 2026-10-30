from typing import Any, List, Mapping, Optional

import httpx

from bakery.api.app import API_HOST, API_PORT


def _format_api_detail(detail: Any) -> Optional[str]:
    if isinstance(detail, str) and detail.strip():
        return detail.strip()
    if isinstance(detail, list):
        parts = []
        for item in detail:
            if isinstance(item, Mapping):
                msg = item.get("msg")
                if isinstance(msg, str) and msg.strip():
                    parts.append(msg.strip())
            elif isinstance(item, str) and item.strip():
                parts.append(item.strip())
        if parts:
            return "; ".join(parts)
    return None


def raise_for_api_status(response: httpx.Response) -> None:
    """Como raise_for_status, pero prioriza FastAPI `detail` legible."""
    if response.is_success:
        return
    message: Optional[str] = None
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, Mapping):
        message = _format_api_detail(payload.get("detail"))
    if not message:
        text = (response.text or "").strip()
        message = text or f"Error HTTP {response.status_code}"
    raise httpx.HTTPStatusError(
        message,
        request=response.request,
        response=response,
    )


class ApiClient:
    def __init__(
        self,
        base_url: str = None,
        *,
        transport: httpx.BaseTransport = None,
    ) -> None:
        self._base_url = (base_url or f"http://{API_HOST}:{API_PORT}").rstrip("/")
        self._client = httpx.Client(base_url=self._base_url, transport=transport, timeout=5.0)
        self.request_count = 0

    def close(self) -> None:
        self._client.close()

    def list_payment_methods(self) -> List[Mapping[str, Any]]:
        response = self._request("GET", "/medios-pago")
        raise_for_api_status(response)
        return response.json()

    def create_sale(
        self,
        id_medio_pago: int,
        lineas: List[Mapping[str, Any]],
        *,
        id_venta: str,
        observacion: Optional[str] = None,
    ) -> Mapping[str, Any]:
        payload: dict = {
            "id_venta": id_venta,
            "id_medio_pago": id_medio_pago,
            "lineas": list(lineas),
        }
        if observacion is not None:
            payload["observacion"] = observacion
        response = self._request("POST", "/ventas", json=payload)
        raise_for_api_status(response)
        return response.json()

    def list_sales(self) -> List[Mapping[str, Any]]:
        response = self._request("GET", "/ventas")
        raise_for_api_status(response)
        return response.json()

    def get_sale(self, id_venta: str) -> Mapping[str, Any]:
        response = self._request("GET", f"/ventas/{id_venta}")
        raise_for_api_status(response)
        return response.json()

    def add_sale_observacion(
        self, id_venta: str, texto: str
    ) -> Mapping[str, Any]:
        response = self._request(
            "POST",
            f"/ventas/{id_venta}/observaciones",
            json={"texto": texto},
        )
        raise_for_api_status(response)
        return response.json()

    def update_sale(
        self,
        id_venta: str,
        *,
        id_medio_pago: int,
        lineas: List[Mapping[str, Any]],
        observacion_venta: Optional[str] = None,
    ) -> Mapping[str, Any]:
        payload: dict = {
            "id_medio_pago": id_medio_pago,
            "lineas": list(lineas),
        }
        if observacion_venta is not None:
            payload["observacion_venta"] = observacion_venta
        response = self._request("PUT", f"/ventas/{id_venta}", json=payload)
        raise_for_api_status(response)
        return response.json()

    def list_categories(self) -> List[Mapping[str, Any]]:
        response = self._request("GET", "/categorias")
        raise_for_api_status(response)
        return response.json()

    def list_products(self) -> List[Mapping[str, Any]]:
        response = self._request("GET", "/productos")
        raise_for_api_status(response)
        return response.json()

    def list_active_products(
        self,
        *,
        id_categoria: Optional[int] = None,
        precio: Optional[int] = None,
    ) -> List[Mapping[str, Any]]:
        """Lista activos. ``precio`` es legado (match exacto); el cobro usa prefijo local."""
        params = {}
        if id_categoria is not None:
            params["id_categoria"] = id_categoria
        if precio is not None:
            params["precio"] = precio
        response = self._request("GET", "/productos/activos", params=params or None)
        raise_for_api_status(response)
        return response.json()

    def get_product(self, id_producto: int) -> Mapping[str, Any]:
        response = self._request("GET", f"/productos/{id_producto}")
        raise_for_api_status(response)
        return response.json()

    def create_product(
        self,
        *,
        nombre: str,
        precio: int,
        id_categoria: int,
        descripcion: Optional[str] = None,
        ruta_imagen: Optional[str] = None,
    ) -> Mapping[str, Any]:
        payload = {
            "nombre": nombre,
            "precio": precio,
            "id_categoria": id_categoria,
            "descripcion": descripcion,
            "ruta_imagen": ruta_imagen,
        }
        response = self._request("POST", "/productos", json=payload)
        raise_for_api_status(response)
        return response.json()

    def update_product(
        self,
        id_producto: int,
        *,
        nombre: str,
        precio: int,
        id_categoria: int,
        descripcion: Optional[str] = None,
        ruta_imagen: Optional[str] = None,
        actualizar_ruta_imagen: bool = False,
    ) -> Mapping[str, Any]:
        payload = {
            "nombre": nombre,
            "precio": precio,
            "id_categoria": id_categoria,
            "descripcion": descripcion,
            "ruta_imagen": ruta_imagen,
            "actualizar_ruta_imagen": actualizar_ruta_imagen,
        }
        response = self._request("PUT", f"/productos/{id_producto}", json=payload)
        raise_for_api_status(response)
        return response.json()

    def activate_product(self, id_producto: int) -> Mapping[str, Any]:
        response = self._request("POST", f"/productos/{id_producto}/activar")
        raise_for_api_status(response)
        return response.json()

    def deactivate_product(self, id_producto: int) -> Mapping[str, Any]:
        response = self._request("POST", f"/productos/{id_producto}/desactivar")
        raise_for_api_status(response)
        return response.json()

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        self.request_count += 1
        return self._client.request(method, path, **kwargs)
