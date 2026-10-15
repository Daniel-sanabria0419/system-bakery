import sqlite3
import uuid
from datetime import datetime
from typing import Mapping

from bakery.persistence.repositories import insert_sale, list_active_payment_methods

CAJA = 1
TENDERO = 1


class SaleValidationError(Exception):
    pass


def register_sale(
    connection: sqlite3.Connection,
    valor_total: int,
    id_medio_pago: int,
    *,
    fecha_venta: str = None,
) -> Mapping:
    if isinstance(valor_total, bool) or not isinstance(valor_total, int) or valor_total <= 0:
        raise SaleValidationError("El valor debe ser un entero mayor que 0.")
    if isinstance(id_medio_pago, bool) or not isinstance(id_medio_pago, int):
        raise SaleValidationError("Debe seleccionar un medio de pago activo.")

    active_ids = {
        method["id_medio_pago"] for method in list_active_payment_methods(connection)
    }
    if id_medio_pago not in active_ids:
        raise SaleValidationError("Debe seleccionar un medio de pago activo.")

    sale = {
        "id_venta": str(uuid.uuid4()),
        "valor_total": valor_total,
        "fecha_venta": fecha_venta or _now(),
        "id_medio_pago": id_medio_pago,
        "caja": CAJA,
        "tendero": TENDERO,
    }
    insert_sale(connection, **sale)
    connection.commit()
    return sale


def _now() -> str:
    return datetime.now().replace(microsecond=0).isoformat(timespec="seconds")
