"""Mensajes legibles desde FastAPI detail en ApiClient."""

import httpx

from bakery.desktop.client import raise_for_api_status


def test_raise_for_api_status_uses_string_detail() -> None:
    request = httpx.Request("POST", "http://test/productos")
    response = httpx.Response(
        400,
        json={"detail": "El precio de Pan pequeño debe ser 300."},
        request=request,
    )
    try:
        raise_for_api_status(response)
        assert False, "expected HTTPStatusError"
    except httpx.HTTPStatusError as exc:
        assert "Pan pequeño" in str(exc)
        assert exc.response.status_code == 400


def test_raise_for_api_status_uses_validation_list() -> None:
    request = httpx.Request("POST", "http://test/productos")
    response = httpx.Response(
        422,
        json={
            "detail": [
                {"loc": ["body", "precio"], "msg": "Input should be a valid integer"},
            ]
        },
        request=request,
    )
    try:
        raise_for_api_status(response)
        assert False, "expected HTTPStatusError"
    except httpx.HTTPStatusError as exc:
        assert "valid integer" in str(exc)


def test_raise_for_api_status_success_noop() -> None:
    request = httpx.Request("GET", "http://test/categorias")
    response = httpx.Response(200, json=[], request=request)
    raise_for_api_status(response)
