"""Beta 2.0.2 Etapa 1: filtro por prefijo de precio (capa app)."""

from bakery.app.purchase import candidates_by_price_prefix


def _product(
    id_producto: int,
    nombre: str,
    precio: int,
    *,
    id_estado: int = 1,
) -> dict:
    return {
        "id_producto": id_producto,
        "nombre": nombre,
        "precio": precio,
        "id_estado": id_estado,
    }


def test_prefix_4_matches_prices_starting_with_4() -> None:
    products = [
        _product(1, "A", 4500),
        _product(2, "B", 400),
        _product(3, "C", 45),
        _product(4, "D", 4),
        _product(5, "E", 5000),
        _product(6, "F", 14500),
    ]
    matches = candidates_by_price_prefix(products, "4")
    assert [item["nombre"] for item in matches] == ["A", "B", "C", "D"]


def test_prefix_45_narrows_matches() -> None:
    products = [
        _product(1, "A", 4500),
        _product(2, "B", 45),
        _product(3, "C", 400),
        _product(4, "D", 450),
    ]
    matches = candidates_by_price_prefix(products, "45")
    assert [item["nombre"] for item in matches] == ["A", "B", "D"]


def test_prefix_4500_exact_string_match() -> None:
    products = [
        _product(1, "A", 4500),
        _product(2, "B", 45000),
        _product(3, "C", 450),
    ]
    matches = candidates_by_price_prefix(products, "4500")
    assert [item["nombre"] for item in matches] == ["A", "B"]


def test_empty_prefix_returns_empty() -> None:
    products = [_product(1, "A", 4500)]
    assert candidates_by_price_prefix(products, "") == []


def test_non_digit_prefix_returns_empty() -> None:
    products = [_product(1, "A", 4500)]
    assert candidates_by_price_prefix(products, "4a") == []
    assert candidates_by_price_prefix(products, "$4") == []


def test_no_match_returns_empty() -> None:
    products = [
        _product(1, "A", 2500),
        _product(2, "B", 300),
    ]
    assert candidates_by_price_prefix(products, "9") == []


def test_inactive_products_excluded() -> None:
    products = [
        _product(1, "Activo", 4500, id_estado=1),
        _product(2, "Inactivo", 4500, id_estado=0),
        _product(3, "Otro", 400, id_estado=1),
    ]
    matches = candidates_by_price_prefix(products, "4")
    assert [item["nombre"] for item in matches] == ["Activo", "Otro"]


def test_missing_estado_treated_as_active() -> None:
    product = {"id_producto": 1, "nombre": "Sin estado", "precio": 4500}
    matches = candidates_by_price_prefix([product], "45")
    assert [item["nombre"] for item in matches] == ["Sin estado"]


def test_prefix_zero_only_matches_prices_starting_with_zero() -> None:
    """Buffer '0' del pad: solo precios cuyo str empieza con '0' (ninguno típico)."""
    products = [
        _product(1, "A", 4500),
        _product(2, "B", 300),
    ]
    assert candidates_by_price_prefix(products, "0") == []


def test_rejects_invalid_precio_values() -> None:
    products = [
        {"id_producto": 1, "nombre": "Float", "precio": 45.0, "id_estado": 1},
        {"id_producto": 2, "nombre": "Neg", "precio": -45, "id_estado": 1},
        {"id_producto": 3, "nombre": "Ok", "precio": 45, "id_estado": 1},
        {"id_producto": 4, "nombre": "Bool", "precio": True, "id_estado": 1},
    ]
    matches = candidates_by_price_prefix(products, "45")
    assert [item["nombre"] for item in matches] == ["Ok"]
