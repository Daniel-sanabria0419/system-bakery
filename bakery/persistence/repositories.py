import sqlite3
from typing import List, Mapping

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
