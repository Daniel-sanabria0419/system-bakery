from typing import Any, List, Mapping

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

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        self.request_count += 1
        return self._client.request(method, path, **kwargs)
