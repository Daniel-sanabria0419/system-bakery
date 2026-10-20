from typing import Any, List, Mapping, Optional

import httpx

from bakery.api.app import API_HOST, API_PORT


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
        response.raise_for_status()
        return response.json()

    def create_sale(self, valor_total: int, id_medio_pago: int) -> Mapping[str, Any]:
        response = self._request(
            "POST",
            "/ventas",
            json={"valor_total": valor_total, "id_medio_pago": id_medio_pago},
        )
        response.raise_for_status()
        return response.json()

    def list_categories(self) -> List[Mapping[str, Any]]:
        response = self._request("GET", "/categorias")
        response.raise_for_status()
        return response.json()

    def list_products(self) -> List[Mapping[str, Any]]:
        response = self._request("GET", "/productos")
        response.raise_for_status()
        return response.json()

    def list_active_products(
        self,
        *,
        id_categoria: Optional[int] = None,
        precio: Optional[int] = None,
    ) -> List[Mapping[str, Any]]:
        params = {}
        if id_categoria is not None:
            params["id_categoria"] = id_categoria
        if precio is not None:
            params["precio"] = precio
        response = self._request("GET", "/productos/activos", params=params or None)
        response.raise_for_status()
        return response.json()

    def get_product(self, id_producto: int) -> Mapping[str, Any]:
        response = self._request("GET", f"/productos/{id_producto}")
        response.raise_for_status()
        return response.json()

    def create_product(
        self,
        *,
        nombre: str,
        precio: int,
        id_categoria: int,
        descripcion: Optional[str] = None,
    ) -> Mapping[str, Any]:
        payload = {
            "nombre": nombre,
            "precio": precio,
            "id_categoria": id_categoria,
            "descripcion": descripcion,
        }
        response = self._request("POST", "/productos", json=payload)
        response.raise_for_status()
        return response.json()

    def update_product(
        self,
        id_producto: int,
        *,
        nombre: str,
        precio: int,
        id_categoria: int,
        descripcion: Optional[str] = None,
    ) -> Mapping[str, Any]:
        payload = {
            "nombre": nombre,
            "precio": precio,
            "id_categoria": id_categoria,
            "descripcion": descripcion,
        }
        response = self._request("PUT", f"/productos/{id_producto}", json=payload)
        response.raise_for_status()
        return response.json()

    def activate_product(self, id_producto: int) -> Mapping[str, Any]:
        response = self._request("POST", f"/productos/{id_producto}/activar")
        response.raise_for_status()
        return response.json()

    def deactivate_product(self, id_producto: int) -> Mapping[str, Any]:
        response = self._request("POST", f"/productos/{id_producto}/desactivar")
        response.raise_for_status()
        return response.json()

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        self.request_count += 1
        return self._client.request(method, path, **kwargs)
