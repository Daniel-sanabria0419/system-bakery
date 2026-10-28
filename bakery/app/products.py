import sqlite3
from typing import Dict, List, Mapping, Optional

from bakery.app.pan_pequeno_pricing import (
    PRECIO_UNITARIO_PAN_PEQUENO,
    is_pan_pequeno,
)
from bakery.app.product_images import normalize_ruta_imagen
from bakery.app.promotions import use_promociones_table
from bakery.persistence.repositories import (
    get_categoria,
    get_producto,
    get_promocion,
    insert_producto,
    list_active_productos,
    list_categorias,
    list_productos,
    set_producto_estado,
    set_producto_promocion_id,
    set_producto_ruta_imagen,
    update_producto,
)
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    ESTADO_INACTIVO,
    ensure_promocion_pan_pequeno,
)


class ProductValidationError(Exception):
    pass


def list_categories(connection: sqlite3.Connection) -> List[Mapping]:
    return list_categorias(connection)


def create_product(
    connection: sqlite3.Connection,
    *,
    nombre: str,
    precio: int,
    id_categoria: int,
    descripcion: Optional[str] = None,
    ruta_imagen: Optional[str] = None,
) -> Mapping:
    nombre_ok = _normalize_nombre(nombre)
    precio_ok = _require_positive_int(precio, "El precio debe ser un entero mayor que 0.")
    id_categoria_ok = _require_existing_categoria(connection, id_categoria)
    _require_pan_pequeno_precio(connection, id_categoria_ok, precio_ok)
    descripcion_ok = _normalize_descripcion(descripcion)
    try:
        ruta_ok = normalize_ruta_imagen(ruta_imagen)
    except ValueError as error:
        raise ProductValidationError(str(error)) from error

    id_producto = insert_producto(
        connection,
        nombre=nombre_ok,
        precio=precio_ok,
        id_categoria=id_categoria_ok,
        descripcion=descripcion_ok,
        id_estado=ESTADO_ACTIVO,
        ruta_imagen=ruta_ok,
    )
    _sync_promocion_for_categoria(connection, id_producto, id_categoria_ok)
    connection.commit()
    product = get_producto(connection, id_producto)
    assert product is not None
    return _enrich_product_promocion(connection, product)


def update_product(
    connection: sqlite3.Connection,
    id_producto: int,
    *,
    nombre: str,
    precio: int,
    id_categoria: int,
    descripcion: Optional[str] = None,
    ruta_imagen: Optional[str] = None,
    actualizar_ruta_imagen: bool = False,
) -> Mapping:
    product = _require_product(connection, id_producto)
    nombre_ok = _normalize_nombre(nombre)
    precio_ok = _require_positive_int(precio, "El precio debe ser un entero mayor que 0.")
    id_categoria_ok = _require_existing_categoria(connection, id_categoria)
    _require_pan_pequeno_precio(connection, id_categoria_ok, precio_ok)
    descripcion_ok = _normalize_descripcion(descripcion)

    update_producto(
        connection,
        product["id_producto"],
        nombre=nombre_ok,
        precio=precio_ok,
        id_categoria=id_categoria_ok,
        descripcion=descripcion_ok,
    )
    if actualizar_ruta_imagen:
        try:
            ruta_ok = normalize_ruta_imagen(ruta_imagen)
        except ValueError as error:
            raise ProductValidationError(str(error)) from error
        set_producto_ruta_imagen(connection, product["id_producto"], ruta_ok)
    _sync_promocion_for_categoria(
        connection, product["id_producto"], id_categoria_ok
    )
    connection.commit()
    updated = get_producto(connection, product["id_producto"])
    assert updated is not None
    return _enrich_product_promocion(connection, updated)


def set_product_image(
    connection: sqlite3.Connection,
    id_producto: int,
    ruta_imagen: Optional[str],
) -> Mapping:
    product = _require_product(connection, id_producto)
    try:
        ruta_ok = normalize_ruta_imagen(ruta_imagen)
    except ValueError as error:
        raise ProductValidationError(str(error)) from error
    set_producto_ruta_imagen(connection, product["id_producto"], ruta_ok)
    connection.commit()
    updated = get_producto(connection, product["id_producto"])
    assert updated is not None
    return _enrich_product_promocion(connection, updated)


def list_all_products(connection: sqlite3.Connection) -> List[Mapping]:
    return _enrich_products(connection, list_productos(connection))


def list_active_products(
    connection: sqlite3.Connection,
    *,
    id_categoria: Optional[int] = None,
    precio: Optional[int] = None,
) -> List[Mapping]:
    if id_categoria is not None:
        _require_existing_categoria(connection, id_categoria)
    precio_ok = None
    if precio is not None:
        precio_ok = _require_positive_int(
            precio, "El precio debe ser un entero mayor que 0."
        )
    return _enrich_products(
        connection,
        list_active_productos(
            connection, id_categoria=id_categoria, precio=precio_ok
        ),
    )


def find_active_products_by_price(
    connection: sqlite3.Connection, precio: int
) -> List[Mapping]:
    """Legado / API-only: activos con precio exacto. Desktop de cobro usa prefijo."""
    return list_active_products(connection, precio=precio)


def activate_product(connection: sqlite3.Connection, id_producto: int) -> Mapping:
    return _set_product_estado(connection, id_producto, ESTADO_ACTIVO)


def deactivate_product(connection: sqlite3.Connection, id_producto: int) -> Mapping:
    return _set_product_estado(connection, id_producto, ESTADO_INACTIVO)


def get_product(connection: sqlite3.Connection, id_producto: int) -> Mapping:
    return _require_product(connection, id_producto)


def _set_product_estado(
    connection: sqlite3.Connection, id_producto: int, id_estado: int
) -> Mapping:
    product = _require_product(connection, id_producto)
    set_producto_estado(connection, product["id_producto"], id_estado)
    connection.commit()
    updated = get_producto(connection, product["id_producto"])
    assert updated is not None
    return _enrich_product_promocion(connection, updated)


def _require_product(connection: sqlite3.Connection, id_producto: int) -> Mapping:
    if isinstance(id_producto, bool) or not isinstance(id_producto, int):
        raise ProductValidationError("El producto no existe.")
    product = get_producto(connection, id_producto)
    if product is None:
        raise ProductValidationError("El producto no existe.")
    return _enrich_product_promocion(connection, product)


def _enrich_products(
    connection: sqlite3.Connection, products: List[Mapping]
) -> List[Mapping]:
    if not use_promociones_table():
        return list(products)
    cache: Dict[int, Optional[Mapping]] = {}
    return [
        _enrich_product_promocion(connection, product, cache=cache)
        for product in products
    ]


def _enrich_product_promocion(
    connection: sqlite3.Connection,
    product: Mapping,
    *,
    cache: Optional[Dict[int, Optional[Mapping]]] = None,
) -> Mapping:
    """Adjunta tipo/config/activo de promo cuando el flag dual-path está on."""
    enriched = dict(product)
    if not use_promociones_table():
        return enriched
    promo_id = product.get("promocion_id")
    if isinstance(promo_id, bool) or not isinstance(promo_id, int):
        return enriched
    promo: Optional[Mapping]
    if cache is not None and promo_id in cache:
        promo = cache[promo_id]
    else:
        promo = get_promocion(connection, promo_id)
        if cache is not None:
            cache[promo_id] = promo
    if promo is None:
        return enriched
    enriched["promocion_tipo"] = promo["tipo"]
    enriched["promocion_configuracion"] = promo["configuracion"]
    enriched["promocion_activo"] = promo["activo"]
    return enriched


def _require_existing_categoria(
    connection: sqlite3.Connection, id_categoria: int
) -> int:
    if isinstance(id_categoria, bool) or not isinstance(id_categoria, int):
        raise ProductValidationError("Debe seleccionar una categoría válida.")
    if get_categoria(connection, id_categoria) is None:
        raise ProductValidationError("Debe seleccionar una categoría válida.")
    return id_categoria


def _require_pan_pequeno_precio(
    connection: sqlite3.Connection, id_categoria: int, precio: int
) -> None:
    categoria = get_categoria(connection, id_categoria)
    if categoria is None:
        return
    if is_pan_pequeno(categoria) and precio != PRECIO_UNITARIO_PAN_PEQUENO:
        raise ProductValidationError(
            "Los productos de Pan pequeño deben tener precio "
            f"{PRECIO_UNITARIO_PAN_PEQUENO}."
        )


def _sync_promocion_for_categoria(
    connection: sqlite3.Connection, id_producto: int, id_categoria: int
) -> None:
    """Asigna/limpia FK de promo según categoría (no calcula montos de cobro)."""
    categoria = get_categoria(connection, id_categoria)
    if categoria is not None and is_pan_pequeno(categoria):
        promo_id = ensure_promocion_pan_pequeno(connection)
        set_producto_promocion_id(connection, id_producto, promo_id)
    else:
        set_producto_promocion_id(connection, id_producto, None)


def _require_positive_int(value: object, message: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ProductValidationError(message)
    return value


def _normalize_nombre(nombre: object) -> str:
    if not isinstance(nombre, str):
        raise ProductValidationError("El nombre es obligatorio.")
    normalized = nombre.strip()
    if not normalized:
        raise ProductValidationError("El nombre es obligatorio.")
    return normalized


def _normalize_descripcion(descripcion: object) -> Optional[str]:
    if descripcion is None:
        return None
    if not isinstance(descripcion, str):
        raise ProductValidationError("La descripción debe ser texto.")
    normalized = descripcion.strip()
    return normalized or None
