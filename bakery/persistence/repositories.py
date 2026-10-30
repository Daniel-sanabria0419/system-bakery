import sqlite3
from datetime import datetime
from typing import List, Mapping, Optional, Union

from bakery.persistence.schema import ESTADO_ACTIVO

# Beta 2.1: ventana de edición (solo reloj del servidor / inyectable en tests).
EDITABLE_WINDOW_SECONDS = 3600

ORIGEN_OBSERVACION_DURANTE_VENTA = "durante_venta"
ORIGEN_OBSERVACION_POSTERIOR = "posterior"

TIPO_CAMBIO_CREACION = "creacion"
TIPO_CAMBIO_EDICION = "edicion"
TIPO_CAMBIO_OBSERVACION_POSTERIOR = "observacion_posterior"
TIPO_CAMBIO_OBSERVACION_CORRECCION = "observacion_correccion"


def sale_is_editable(
    fecha_venta: str,
    now: Optional[Union[datetime, str]] = None,
) -> bool:
    """True si elapsed desde fecha_venta es estrictamente menor a 1 hora.

    ``now`` es inyectable para tests (datetime o ISO str). Si se omite, usa
    ``datetime.now()`` del proceso (reloj del servidor embebido).
    """
    fecha_dt = datetime.fromisoformat(fecha_venta)
    if now is None:
        now_dt = datetime.now()
    elif isinstance(now, datetime):
        now_dt = now
    else:
        now_dt = datetime.fromisoformat(now)
    elapsed = (now_dt - fecha_dt).total_seconds()
    return elapsed < EDITABLE_WINDOW_SECONDS


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


def get_sale(
    connection: sqlite3.Connection, id_venta: str
) -> Optional[Mapping]:
    row = connection.execute(
        """
        SELECT id_venta, valor_total, fecha_venta, id_medio_pago, caja, tendero
        FROM ventas
        WHERE id_venta = ?
        """,
        (id_venta,),
    ).fetchone()
    return dict(row) if row is not None else None


def list_ventas(connection: sqlite3.Connection) -> List[Mapping]:
    """Lista ventas más recientes primero; incluye nombre de medio y conteo de líneas."""
    rows = connection.execute(
        """
        SELECT
            v.id_venta,
            v.valor_total,
            v.fecha_venta,
            v.id_medio_pago,
            v.caja,
            v.tendero,
            m.nombre AS nombre_medio,
            (
                SELECT COUNT(*)
                FROM venta_lineas vl
                WHERE vl.id_venta = v.id_venta
            ) AS cantidad_lineas
        FROM ventas v
        JOIN medios_pago m ON m.id_medio_pago = v.id_medio_pago
        ORDER BY v.fecha_venta DESC, v.id_venta DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_sale_detail(
    connection: sqlite3.Connection, id_venta: str
) -> Optional[Mapping]:
    """Cabecera + nombre de medio + líneas + observaciones. None si no existe."""
    row = connection.execute(
        """
        SELECT
            v.id_venta,
            v.valor_total,
            v.fecha_venta,
            v.id_medio_pago,
            v.caja,
            v.tendero,
            m.nombre AS nombre_medio
        FROM ventas v
        JOIN medios_pago m ON m.id_medio_pago = v.id_medio_pago
        WHERE v.id_venta = ?
        """,
        (id_venta,),
    ).fetchone()
    if row is None:
        return None
    detail = dict(row)
    detail["lineas"] = list_venta_lineas(connection, id_venta)
    detail["observaciones"] = list_venta_observaciones(connection, id_venta)
    return detail


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
    total: int,
    id_promocion: Optional[int] = None,
    nombre_promocion: Optional[str] = None,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO venta_lineas (
            id_venta, id_producto, nombre_producto,
            precio_aplicado, cantidad, subtotal, total,
            id_promocion, nombre_promocion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            id_venta,
            id_producto,
            nombre_producto,
            precio_aplicado,
            cantidad,
            subtotal,
            total,
            id_promocion,
            nombre_promocion,
        ),
    )
    return int(cursor.lastrowid)


def list_venta_lineas(
    connection: sqlite3.Connection, id_venta: str
) -> List[Mapping]:
    rows = connection.execute(
        """
        SELECT id_linea, id_venta, id_producto, nombre_producto,
               precio_aplicado, cantidad, subtotal, total,
               id_promocion, nombre_promocion
        FROM venta_lineas
        WHERE id_venta = ?
        ORDER BY id_linea
        """,
        (id_venta,),
    ).fetchall()
    return [dict(row) for row in rows]


def insert_venta_cambio(
    connection: sqlite3.Connection,
    *,
    id_venta: str,
    fecha_cambio: str,
    tipo: str,
    despues_json: str,
    antes_json: Optional[str] = None,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO venta_cambios (
            id_venta, fecha_cambio, tipo, antes_json, despues_json
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (id_venta, fecha_cambio, tipo, antes_json, despues_json),
    )
    return int(cursor.lastrowid)


def list_venta_cambios(
    connection: sqlite3.Connection, id_venta: str
) -> List[Mapping]:
    rows = connection.execute(
        """
        SELECT id_cambio, id_venta, fecha_cambio, tipo, antes_json, despues_json
        FROM venta_cambios
        WHERE id_venta = ?
        ORDER BY fecha_cambio ASC, id_cambio ASC
        """,
        (id_venta,),
    ).fetchall()
    return [dict(row) for row in rows]


def insert_venta_observacion(
    connection: sqlite3.Connection,
    *,
    id_venta: str,
    texto: str,
    origen: str,
    fecha_creacion: str,
    id_cambio: Optional[int] = None,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO venta_observaciones (
            id_venta, texto, origen, fecha_creacion, id_cambio
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (id_venta, texto, origen, fecha_creacion, id_cambio),
    )
    return int(cursor.lastrowid)


def list_venta_observaciones(
    connection: sqlite3.Connection, id_venta: str
) -> List[Mapping]:
    rows = connection.execute(
        """
        SELECT id_observacion, id_venta, texto, origen, fecha_creacion, id_cambio
        FROM venta_observaciones
        WHERE id_venta = ?
        ORDER BY fecha_creacion ASC, id_observacion ASC
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


def get_categoria_by_nombre(
    connection: sqlite3.Connection, nombre: str
) -> Optional[Mapping]:
    row = connection.execute(
        """
        SELECT id_categoria, nombre
        FROM categorias
        WHERE nombre = ?
        """,
        (nombre,),
    ).fetchone()
    return dict(row) if row else None


_PRODUCTO_COLUMNS = (
    "id_producto, nombre, precio, id_categoria, descripcion, id_estado, "
    "ruta_imagen, promocion_id"
)

_PROMOCION_COLUMNS = "id, nombre, tipo, configuracion, activo"


def insert_producto(
    connection: sqlite3.Connection,
    *,
    nombre: str,
    precio: int,
    id_categoria: int,
    descripcion: Optional[str],
    id_estado: int,
    ruta_imagen: Optional[str] = None,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO productos (
            nombre, precio, id_categoria, descripcion, id_estado, ruta_imagen
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (nombre, precio, id_categoria, descripcion, id_estado, ruta_imagen),
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


def set_producto_ruta_imagen(
    connection: sqlite3.Connection,
    id_producto: int,
    ruta_imagen: Optional[str],
) -> None:
    connection.execute(
        """
        UPDATE productos
        SET ruta_imagen = ?
        WHERE id_producto = ?
        """,
        (ruta_imagen, id_producto),
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


def set_producto_promocion_id(
    connection: sqlite3.Connection,
    id_producto: int,
    promocion_id: Optional[int],
) -> None:
    connection.execute(
        """
        UPDATE productos
        SET promocion_id = ?
        WHERE id_producto = ?
        """,
        (promocion_id, id_producto),
    )


def insert_promocion(
    connection: sqlite3.Connection,
    *,
    nombre: str,
    tipo: str,
    configuracion: str,
    activo: int,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO promociones (nombre, tipo, configuracion, activo)
        VALUES (?, ?, ?, ?)
        """,
        (nombre, tipo, configuracion, activo),
    )
    return int(cursor.lastrowid)


def get_promocion(
    connection: sqlite3.Connection, id_promocion: int
) -> Optional[Mapping]:
    row = connection.execute(
        f"""
        SELECT {_PROMOCION_COLUMNS}
        FROM promociones
        WHERE id = ?
        """,
        (id_promocion,),
    ).fetchone()
    return dict(row) if row else None


def list_promociones(connection: sqlite3.Connection) -> List[Mapping]:
    rows = connection.execute(
        f"""
        SELECT {_PROMOCION_COLUMNS}
        FROM promociones
        ORDER BY id
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_producto(
    connection: sqlite3.Connection, id_producto: int
) -> Optional[Mapping]:
    row = connection.execute(
        f"""
        SELECT {_PRODUCTO_COLUMNS}
        FROM productos
        WHERE id_producto = ?
        """,
        (id_producto,),
    ).fetchone()
    return dict(row) if row else None


def list_productos(connection: sqlite3.Connection) -> List[Mapping]:
    rows = connection.execute(
        f"""
        SELECT {_PRODUCTO_COLUMNS}
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
    query = f"""
        SELECT {_PRODUCTO_COLUMNS}
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
