import sqlite3
from typing import List, Mapping, Optional

from bakery.persistence.schema import ESTADO_ACTIVO


def list_active_payment_methods(connection: sqlite3.Connection) -> List[Mapping]:
    rows = connection.execute(
        """
        SELECT id_medio_pago, nombre, id_estado
        FROM medios_pago
        WHERE id_estado = ?
        ORDER BY id_medio_pago
        """,
        (ESTADO_ACTIVO,),
    ).fetchall()
    return [dict(row) for row in rows]


def insert_sale(
    connection: sqlite3.Connection,
    *,
    id_venta: str,
    valor_total: int,
    fecha_venta: str,
    id_medio_pago: int,
    caja: int = 1,
    tendero: int = 1,
) -> None:
    connection.execute(
        """
        INSERT INTO ventas (
            id_venta, valor_total, fecha_venta, id_medio_pago, caja, tendero
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (id_venta, valor_total, fecha_venta, id_medio_pago, caja, tendero),
    )


def insert_venta_linea(
    connection: sqlite3.Connection,
    *,
    id_venta: str,
    id_producto: int,
    nombre_producto: str,
    precio_aplicado: int,
    cantidad: int,
    subtotal: int,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO venta_lineas (
            id_venta, id_producto, nombre_producto,
            precio_aplicado, cantidad, subtotal
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            id_venta,
            id_producto,
            nombre_producto,
            precio_aplicado,
            cantidad,
            subtotal,
        ),
    )
    return int(cursor.lastrowid)


def list_venta_lineas(
    connection: sqlite3.Connection, id_venta: str
) -> List[Mapping]:
    rows = connection.execute(
        """
        SELECT id_linea, id_venta, id_producto, nombre_producto,
               precio_aplicado, cantidad, subtotal
        FROM venta_lineas
        WHERE id_venta = ?
        ORDER BY id_linea
        """,
        (id_venta,),
    ).fetchall()
    return [dict(row) for row in rows]


def list_categorias(connection: sqlite3.Connection) -> List[Mapping]:
    rows = connection.execute(
        """
        SELECT id_categoria, nombre
        FROM categorias
        ORDER BY id_categoria
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_categoria(
    connection: sqlite3.Connection, id_categoria: int
) -> Optional[Mapping]:
    row = connection.execute(
        """
        SELECT id_categoria, nombre
        FROM categorias
        WHERE id_categoria = ?
        """,
        (id_categoria,),
    ).fetchone()
    return dict(row) if row else None


def insert_producto(
    connection: sqlite3.Connection,
    *,
    nombre: str,
    precio: int,
    id_categoria: int,
    descripcion: Optional[str],
    id_estado: int,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO productos (
            nombre, precio, id_categoria, descripcion, id_estado
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (nombre, precio, id_categoria, descripcion, id_estado),
    )
    return int(cursor.lastrowid)


def update_producto(
    connection: sqlite3.Connection,
    id_producto: int,
    *,
    nombre: str,
    precio: int,
    id_categoria: int,
    descripcion: Optional[str],
) -> None:
    connection.execute(
        """
        UPDATE productos
        SET nombre = ?, precio = ?, id_categoria = ?, descripcion = ?
        WHERE id_producto = ?
        """,
        (nombre, precio, id_categoria, descripcion, id_producto),
    )


def set_producto_estado(
    connection: sqlite3.Connection, id_producto: int, id_estado: int
) -> None:
    connection.execute(
        """
        UPDATE productos
        SET id_estado = ?
        WHERE id_producto = ?
        """,
        (id_estado, id_producto),
    )


def get_producto(
    connection: sqlite3.Connection, id_producto: int
) -> Optional[Mapping]:
    row = connection.execute(
        """
        SELECT id_producto, nombre, precio, id_categoria, descripcion, id_estado
        FROM productos
        WHERE id_producto = ?
        """,
        (id_producto,),
    ).fetchone()
    return dict(row) if row else None


def list_productos(connection: sqlite3.Connection) -> List[Mapping]:
    rows = connection.execute(
        """
        SELECT id_producto, nombre, precio, id_categoria, descripcion, id_estado
        FROM productos
        ORDER BY id_producto
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_active_productos(
    connection: sqlite3.Connection,
    *,
    id_categoria: Optional[int] = None,
    precio: Optional[int] = None,
) -> List[Mapping]:
    query = """
        SELECT id_producto, nombre, precio, id_categoria, descripcion, id_estado
        FROM productos
        WHERE id_estado = ?
    """
    params: list = [ESTADO_ACTIVO]
    if id_categoria is not None:
        query += " AND id_categoria = ?"
        params.append(id_categoria)
    if precio is not None:
        query += " AND precio = ?"
        params.append(precio)
    query += " ORDER BY id_producto"
    rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]
