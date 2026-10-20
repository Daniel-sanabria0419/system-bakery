import sqlite3
from typing import List, Mapping, Optional

from bakery.persistence.repositories import (
    get_categoria,
    get_producto,
    insert_producto,
    list_active_productos,
    list_categorias,
    list_productos,
    set_producto_estado,
    update_producto,
)
from bakery.persistence.schema import ESTADO_ACTIVO, ESTADO_INACTIVO


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
) -> Mapping:
    nombre_ok = _normalize_nombre(nombre)
    precio_ok = _require_positive_int(precio, "El precio debe ser un entero mayor que 0.")
    id_categoria_ok = _require_existing_categoria(connection, id_categoria)
    descripcion_ok = _normalize_descripcion(descripcion)

    id_producto = insert_producto(
        connection,
        nombre=nombre_ok,
        precio=precio_ok,
        id_categoria=id_categoria_ok,
        descripcion=descripcion_ok,
        id_estado=ESTADO_ACTIVO,
    )
    connection.commit()
    product = get_producto(connection, id_producto)
    assert product is not None
    return product


def update_product(
    connection: sqlite3.Connection,
    id_producto: int,
    *,
    nombre: str,
    precio: int,
    id_categoria: int,
    descripcion: Optional[str] = None,
) -> Mapping:
    product = _require_product(connection, id_producto)
    nombre_ok = _normalize_nombre(nombre)
    precio_ok = _require_positive_int(precio, "El precio debe ser un entero mayor que 0.")
    id_categoria_ok = _require_existing_categoria(connection, id_categoria)
    descripcion_ok = _normalize_descripcion(descripcion)

    update_producto(
        connection,
        product["id_producto"],
        nombre=nombre_ok,
        precio=precio_ok,
        id_categoria=id_categoria_ok,
        descripcion=descripcion_ok,
    )
    connection.commit()
    updated = get_producto(connection, product["id_producto"])
    assert updated is not None
    return updated


def list_all_products(connection: sqlite3.Connection) -> List[Mapping]:
    return list_productos(connection)


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
    return list_active_productos(
        connection, id_categoria=id_categoria, precio=precio_ok
    )


def find_active_products_by_price(
    connection: sqlite3.Connection, precio: int
) -> List[Mapping]:
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
    return updated


def _require_product(connection: sqlite3.Connection, id_producto: int) -> Mapping:
    if isinstance(id_producto, bool) or not isinstance(id_producto, int):
        raise ProductValidationError("El producto no existe.")
    product = get_producto(connection, id_producto)
    if product is None:
        raise ProductValidationError("El producto no existe.")
    return product


def _require_existing_categoria(
    connection: sqlite3.Connection, id_categoria: int
) -> int:
    if isinstance(id_categoria, bool) or not isinstance(id_categoria, int):
        raise ProductValidationError("Debe seleccionar una categoría válida.")
    if get_categoria(connection, id_categoria) is None:
        raise ProductValidationError("Debe seleccionar una categoría válida.")
    return id_categoria


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
