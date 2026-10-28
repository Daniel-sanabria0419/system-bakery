import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from bakery.app.promotions import (
    compute_cart_line_subtotals,
    is_active_cantidad_por_monto,
    parse_cantidad_por_monto_config,
    use_promociones_table,
)
from bakery.persistence.repositories import (
    get_producto,
    get_promocion,
    insert_sale,
    insert_venta_linea,
    list_active_payment_methods,
)
from bakery.persistence.schema import ESTADO_ACTIVO

CAJA = 1
TENDERO = 1


class SaleValidationError(Exception):
    pass


def register_sale(
    connection: sqlite3.Connection,
    id_medio_pago: int,
    lineas: Sequence[Mapping],
    *,
    fecha_venta: str = None,
) -> Mapping:
    if isinstance(id_medio_pago, bool) or not isinstance(id_medio_pago, int):
        raise SaleValidationError("Debe seleccionar un medio de pago activo.")

    active_ids = {
        method["id_medio_pago"] for method in list_active_payment_methods(connection)
    }
    if id_medio_pago not in active_ids:
        raise SaleValidationError("Debe seleccionar un medio de pago activo.")

    if not isinstance(lineas, (list, tuple)) or len(lineas) < 1:
        raise SaleValidationError("Debe enviar al menos una línea de producto.")

    if use_promociones_table():
        resolved = _resolve_lines_with_promociones(connection, lineas)
    else:
        resolved = [_resolve_line_plain(connection, raw) for raw in lineas]

    valor_total = sum(line["subtotal"] for line in resolved)
    if valor_total <= 0:
        raise SaleValidationError("El valor debe ser un entero mayor que 0.")

    sale = {
        "id_venta": str(uuid.uuid4()),
        "valor_total": valor_total,
        "fecha_venta": fecha_venta or _now(),
        "id_medio_pago": id_medio_pago,
        "caja": CAJA,
        "tendero": TENDERO,
    }
    try:
        insert_sale(connection, **sale)
        for line in resolved:
            insert_venta_linea(
                connection,
                id_venta=sale["id_venta"],
                id_producto=line["id_producto"],
                nombre_producto=line["nombre_producto"],
                precio_aplicado=line["precio_aplicado"],
                cantidad=line["cantidad"],
                subtotal=line["subtotal"],
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return sale


def _resolve_line_plain(connection: sqlite3.Connection, raw: Mapping) -> Mapping:
    """Sin tabla de promociones: solo precio × cantidad (sin montos por categoría)."""
    product, cantidad, _precio_aplicado = _validate_raw_line(connection, raw)
    subtotal = product["precio"] * cantidad
    return {
        "id_producto": product["id_producto"],
        "nombre_producto": product["nombre"],
        "precio_aplicado": product["precio"],
        "cantidad": cantidad,
        "subtotal": subtotal,
    }


def _resolve_lines_with_promociones(
    connection: sqlite3.Connection, lineas: Sequence[Mapping]
) -> List[Mapping]:
    pending: List[Mapping] = []
    promos_by_id: Dict[int, Mapping] = {}
    for raw in lineas:
        product, cantidad, precio_aplicado = _validate_raw_line(connection, raw)
        promo_id = product.get("promocion_id")
        promo: Optional[Mapping] = None
        if isinstance(promo_id, int) and not isinstance(promo_id, bool):
            cached = promos_by_id.get(promo_id)
            if cached is None:
                loaded = get_promocion(connection, promo_id)
                if loaded is not None:
                    promos_by_id[promo_id] = loaded
                    cached = loaded
            promo = cached
            if promo is not None and is_active_cantidad_por_monto(promo):
                try:
                    config = parse_cantidad_por_monto_config(promo["configuracion"])
                except ValueError as error:
                    raise SaleValidationError(str(error)) from error
                if product["precio"] != config["precio_base"]:
                    raise SaleValidationError(
                        "El precio de lista no coincide con precio_base "
                        "de la promoción."
                    )
        pending.append(
            {
                "id_producto": product["id_producto"],
                "nombre_producto": product["nombre"],
                "precio_aplicado": product["precio"],
                "cantidad": cantidad,
                "promocion_id": (
                    promo_id
                    if promo is not None and is_active_cantidad_por_monto(promo)
                    else None
                ),
            }
        )

    subtotals = compute_cart_line_subtotals(pending, promos_by_id=promos_by_id)
    resolved: List[Mapping] = []
    for line, subtotal in zip(pending, subtotals):
        resolved.append(
            {
                "id_producto": line["id_producto"],
                "nombre_producto": line["nombre_producto"],
                "precio_aplicado": line["precio_aplicado"],
                "cantidad": line["cantidad"],
                "subtotal": subtotal,
            }
        )
    return resolved


def _validate_raw_line(
    connection: sqlite3.Connection, raw: Mapping
) -> Tuple[Mapping, int, int]:
    if not isinstance(raw, Mapping):
        raise SaleValidationError("Cada línea debe ser un objeto válido.")

    id_producto = raw.get("id_producto")
    cantidad = raw.get("cantidad")
    precio_aplicado = raw.get("precio_aplicado")

    if isinstance(id_producto, bool) or not isinstance(id_producto, int):
        raise SaleValidationError("Cada línea requiere un producto válido.")
    if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
        raise SaleValidationError("La cantidad debe ser un entero mayor que 0.")
    if (
        isinstance(precio_aplicado, bool)
        or not isinstance(precio_aplicado, int)
        or precio_aplicado <= 0
    ):
        raise SaleValidationError("El precio aplicado debe ser un entero mayor que 0.")

    product = get_producto(connection, id_producto)
    if product is None:
        raise SaleValidationError("El producto no existe.")
    if product["id_estado"] != ESTADO_ACTIVO:
        raise SaleValidationError("El producto debe estar activo.")
    if product["precio"] != precio_aplicado:
        raise SaleValidationError(
            "El precio aplicado no coincide con el precio actual del producto."
        )
    return product, cantidad, precio_aplicado


def _now() -> str:
    return datetime.now().replace(microsecond=0).isoformat(timespec="seconds")
