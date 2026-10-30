import json
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union

from bakery.app.promotions import (
    compute_cart_line_subtotals,
    is_active_cantidad_por_monto,
    parse_cantidad_por_monto_config,
)
from bakery.persistence.repositories import (
    ORIGEN_OBSERVACION_DURANTE_VENTA,
    ORIGEN_OBSERVACION_POSTERIOR,
    TIPO_CAMBIO_CREACION,
    TIPO_CAMBIO_EDICION,
    TIPO_CAMBIO_OBSERVACION_POSTERIOR,
    delete_venta_lineas,
    get_producto,
    get_promocion,
    get_sale,
    get_sale_detail as load_sale_detail,
    insert_sale,
    insert_venta_cambio,
    insert_venta_linea,
    insert_venta_observacion,
    list_active_payment_methods,
    list_venta_cambios,
    list_venta_lineas,
    list_venta_observaciones,
    list_ventas,
    sale_is_editable,
    update_sale_header,
)
from bakery.persistence.schema import ESTADO_ACTIVO

CAJA = 1
TENDERO = 1


class SaleValidationError(Exception):
    pass


class SaleNotFoundError(Exception):
    pass


class SaleNotEditableError(Exception):
    """Venta fuera de la ventana de 1 h (reloj del servidor)."""

    pass


def list_sales(
    connection: sqlite3.Connection,
    *,
    now: Optional[Union[datetime, str]] = None,
) -> List[Mapping]:
    """Listado de ventas (más recientes primero) con flag ``editable`` del servidor."""
    rows: List[Mapping] = []
    for row in list_ventas(connection):
        item = dict(row)
        item["editable"] = sale_is_editable(item["fecha_venta"], now=now)
        item["es_legado"] = int(item["cantidad_lineas"]) == 0
        rows.append(item)
    return rows


def get_sale_detail(
    connection: sqlite3.Connection,
    id_venta: str,
    *,
    now: Optional[Union[datetime, str]] = None,
) -> Optional[Mapping]:
    """Detalle de venta (cabecera, líneas, observaciones) + ``editable``."""
    detail = load_sale_detail(connection, id_venta)
    if detail is None:
        return None
    result = dict(detail)
    result["editable"] = sale_is_editable(result["fecha_venta"], now=now)
    result["es_legado"] = len(result["lineas"]) == 0
    return result


def list_sale_cambios(
    connection: sqlite3.Connection, id_venta: str
) -> List[Mapping]:
    """Auditoría consultable de una venta (creación, ediciones, obs).

    Devuelve filas ordenadas; ``antes`` / ``despues`` parseados desde JSON.
    No borra ni muta ``venta_cambios``.
    """
    sale = get_sale(connection, id_venta)
    if sale is None:
        raise SaleNotFoundError("Venta no encontrada.")

    rows: List[Mapping] = []
    for row in list_venta_cambios(connection, id_venta):
        item = dict(row)
        antes_raw = item.pop("antes_json")
        despues_raw = item.pop("despues_json")
        item["antes"] = json.loads(antes_raw) if antes_raw is not None else None
        item["despues"] = json.loads(despues_raw)
        rows.append(item)
    return rows


def register_sale(
    connection: sqlite3.Connection,
    id_medio_pago: int,
    lineas: Sequence[Mapping],
    *,
    id_venta: str,
    fecha_venta: str = None,
    observacion: Optional[str] = None,
) -> Mapping:
    sale_id = _validate_id_venta(id_venta)
    existing = get_sale(connection, sale_id)
    if existing is not None:
        return existing

    if isinstance(id_medio_pago, bool) or not isinstance(id_medio_pago, int):
        raise SaleValidationError("Debe seleccionar un medio de pago activo.")

    active_methods = list_active_payment_methods(connection)
    active_by_id = {method["id_medio_pago"]: method for method in active_methods}
    if id_medio_pago not in active_by_id:
        raise SaleValidationError("Debe seleccionar un medio de pago activo.")

    if not isinstance(lineas, (list, tuple)) or len(lineas) < 1:
        raise SaleValidationError("Debe enviar al menos una línea de producto.")

    texto_obs = _normalize_optional_observacion(observacion)

    resolved = _resolve_lines_with_promociones(connection, lineas)

    valor_total = sum(line["total"] for line in resolved)
    if valor_total <= 0:
        raise SaleValidationError("El valor debe ser un entero mayor que 0.")

    sale = {
        "id_venta": sale_id,
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
                total=line["total"],
                id_promocion=line.get("id_promocion"),
                nombre_promocion=line.get("nombre_promocion"),
            )
        observaciones_audit: List[Mapping] = []
        if texto_obs is not None:
            observaciones_audit.append(
                {
                    "texto": texto_obs,
                    "origen": ORIGEN_OBSERVACION_DURANTE_VENTA,
                }
            )
        despues_payload = _audit_state_payload(
            id_medio_pago=id_medio_pago,
            nombre_medio=active_by_id[id_medio_pago]["nombre"],
            valor_total=valor_total,
            lineas=resolved,
            observaciones=observaciones_audit,
        )
        despues_json = json.dumps(
            despues_payload, ensure_ascii=False, separators=(",", ":")
        )
        id_cambio = insert_venta_cambio(
            connection,
            id_venta=sale["id_venta"],
            fecha_cambio=sale["fecha_venta"],
            tipo=TIPO_CAMBIO_CREACION,
            despues_json=despues_json,
        )
        if texto_obs is not None:
            insert_venta_observacion(
                connection,
                id_venta=sale["id_venta"],
                texto=texto_obs,
                origen=ORIGEN_OBSERVACION_DURANTE_VENTA,
                fecha_creacion=sale["fecha_venta"],
                id_cambio=id_cambio,
            )
        connection.commit()
    except sqlite3.IntegrityError:
        # Carrera: otro POST con el mismo id ya hizo commit.
        connection.rollback()
        raced = get_sale(connection, sale_id)
        if raced is not None:
            return raced
        raise
    except Exception:
        connection.rollback()
        raise
    return sale


def update_sale(
    connection: sqlite3.Connection,
    id_venta: str,
    id_medio_pago: int,
    lineas: Sequence[Mapping],
    *,
    observacion_venta: Optional[str] = None,
    now: Optional[Union[datetime, str]] = None,
) -> Mapping:
    """Edita una venta dentro de la ventana de 1 h; recalcula con promo vigente.

    No muta ``fecha_venta``, ``caja``, ``tendero`` ni ``id_venta``.
    Escribe auditoría ``tipo=edicion`` con antes/después completos.
    No borra filas previas de ``venta_cambios`` (el original se conserva).
    """
    sale = get_sale(connection, id_venta)
    if sale is None:
        raise SaleNotFoundError("Venta no encontrada.")

    if not sale_is_editable(sale["fecha_venta"], now=now):
        raise SaleNotEditableError(
            "La venta solo se puede editar dentro de la primera hora."
        )

    if isinstance(id_medio_pago, bool) or not isinstance(id_medio_pago, int):
        raise SaleValidationError("Debe seleccionar un medio de pago activo.")

    active_methods = list_active_payment_methods(connection)
    active_by_id = {method["id_medio_pago"]: method for method in active_methods}
    if id_medio_pago not in active_by_id:
        raise SaleValidationError("Debe seleccionar un medio de pago activo.")

    if not isinstance(lineas, (list, tuple)):
        raise SaleValidationError("Debe enviar lineas de producto.")

    existing_lines = list_venta_lineas(connection, id_venta)
    is_legado = len(existing_lines) == 0
    if is_legado and len(lineas) > 0:
        raise SaleValidationError(
            "Venta legado sin líneas: no se pueden inventar productos."
        )
    if not is_legado and len(lineas) < 1:
        raise SaleValidationError("Debe enviar al menos una línea de producto.")

    texto_obs = _normalize_optional_observacion(observacion_venta)
    existing_obs = list_venta_observaciones(connection, id_venta)
    last_durante = _last_durante_venta_texto(existing_obs)
    append_obs = texto_obs is not None and texto_obs != last_durante

    if is_legado:
        resolved: List[Mapping] = []
        valor_total = int(sale["valor_total"])
    else:
        resolved = _resolve_lines_with_promociones(connection, lineas)
        valor_total = sum(line["total"] for line in resolved)
        if valor_total <= 0:
            raise SaleValidationError("El valor debe ser un entero mayor que 0.")

    when = _now_value(now)
    antes_payload = _audit_state_payload(
        id_medio_pago=int(sale["id_medio_pago"]),
        nombre_medio=_medio_nombre(connection, int(sale["id_medio_pago"])),
        valor_total=int(sale["valor_total"]),
        lineas=existing_lines,
        observaciones=existing_obs,
    )
    despues_obs_audit = [
        {"texto": obs["texto"], "origen": obs["origen"]} for obs in existing_obs
    ]
    if append_obs:
        despues_obs_audit.append(
            {"texto": texto_obs, "origen": ORIGEN_OBSERVACION_DURANTE_VENTA}
        )
    despues_payload = _audit_state_payload(
        id_medio_pago=id_medio_pago,
        nombre_medio=active_by_id[id_medio_pago]["nombre"],
        valor_total=valor_total,
        lineas=resolved if not is_legado else [],
        observaciones=despues_obs_audit,
    )
    antes_json = json.dumps(
        antes_payload, ensure_ascii=False, separators=(",", ":")
    )
    despues_json = json.dumps(
        despues_payload, ensure_ascii=False, separators=(",", ":")
    )

    try:
        id_cambio = insert_venta_cambio(
            connection,
            id_venta=id_venta,
            fecha_cambio=when,
            tipo=TIPO_CAMBIO_EDICION,
            antes_json=antes_json,
            despues_json=despues_json,
        )
        update_sale_header(
            connection,
            id_venta,
            valor_total=valor_total,
            id_medio_pago=id_medio_pago,
        )
        if not is_legado:
            delete_venta_lineas(connection, id_venta)
            for line in resolved:
                insert_venta_linea(
                    connection,
                    id_venta=id_venta,
                    id_producto=line["id_producto"],
                    nombre_producto=line["nombre_producto"],
                    precio_aplicado=line["precio_aplicado"],
                    cantidad=line["cantidad"],
                    subtotal=line["subtotal"],
                    total=line["total"],
                    id_promocion=line.get("id_promocion"),
                    nombre_promocion=line.get("nombre_promocion"),
                )
        if append_obs:
            insert_venta_observacion(
                connection,
                id_venta=id_venta,
                texto=texto_obs,
                origen=ORIGEN_OBSERVACION_DURANTE_VENTA,
                fecha_creacion=when,
                id_cambio=id_cambio,
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise

    updated = get_sale(connection, id_venta)
    assert updated is not None
    return updated


def add_sale_observacion(
    connection: sqlite3.Connection,
    id_venta: str,
    texto: str,
    *,
    fecha_creacion: Optional[str] = None,
) -> Mapping:
    """Agrega observación posterior (siempre permitida). Append-only + auditoría mínima."""
    sale = get_sale(connection, id_venta)
    if sale is None:
        raise SaleNotFoundError("Venta no encontrada.")

    if not isinstance(texto, str):
        raise SaleValidationError("La observación no puede estar vacía.")
    texto_limpio = texto.strip()
    if not texto_limpio:
        raise SaleValidationError("La observación no puede estar vacía.")

    when = fecha_creacion or _now()
    despues_json = json.dumps(
        {
            "texto": texto_limpio,
            "origen": ORIGEN_OBSERVACION_POSTERIOR,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    try:
        id_cambio = insert_venta_cambio(
            connection,
            id_venta=id_venta,
            fecha_cambio=when,
            tipo=TIPO_CAMBIO_OBSERVACION_POSTERIOR,
            despues_json=despues_json,
        )
        id_observacion = insert_venta_observacion(
            connection,
            id_venta=id_venta,
            texto=texto_limpio,
            origen=ORIGEN_OBSERVACION_POSTERIOR,
            fecha_creacion=when,
            id_cambio=id_cambio,
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return {
        "id_observacion": id_observacion,
        "id_venta": id_venta,
        "texto": texto_limpio,
        "origen": ORIGEN_OBSERVACION_POSTERIOR,
        "fecha_creacion": when,
        "id_cambio": id_cambio,
    }


def _normalize_optional_observacion(observacion: object) -> Optional[str]:
    if observacion is None:
        return None
    if not isinstance(observacion, str):
        raise SaleValidationError("La observación debe ser texto.")
    texto = observacion.strip()
    if not texto:
        return None
    return texto


def _now_value(now: Optional[Union[datetime, str]]) -> str:
    if now is None:
        return _now()
    if isinstance(now, datetime):
        return now.replace(microsecond=0).isoformat(timespec="seconds")
    return str(now)


def _last_durante_venta_texto(observaciones: Sequence[Mapping]) -> Optional[str]:
    last: Optional[str] = None
    for obs in observaciones:
        if obs.get("origen") == ORIGEN_OBSERVACION_DURANTE_VENTA:
            last = str(obs["texto"])
    return last


def _medio_nombre(connection: sqlite3.Connection, id_medio_pago: int) -> str:
    row = connection.execute(
        "SELECT nombre FROM medios_pago WHERE id_medio_pago = ?",
        (id_medio_pago,),
    ).fetchone()
    return str(row["nombre"]) if row is not None else ""


def _audit_line_dicts(lineas: Sequence[Mapping]) -> List[dict]:
    result: List[dict] = []
    for line in lineas:
        result.append(
            {
                "id_producto": line["id_producto"],
                "nombre_producto": line["nombre_producto"],
                "cantidad": line["cantidad"],
                "precio_aplicado": line["precio_aplicado"],
                "subtotal": line["subtotal"],
                "total": line["total"],
                "id_promocion": line.get("id_promocion"),
                "nombre_promocion": line.get("nombre_promocion"),
            }
        )
    return result


def _audit_state_payload(
    *,
    id_medio_pago: int,
    nombre_medio: str,
    valor_total: int,
    lineas: Sequence[Mapping],
    observaciones: Sequence[Mapping],
) -> dict:
    obs_list: List[dict] = []
    for obs in observaciones:
        if "origen" in obs and "texto" in obs:
            obs_list.append({"texto": obs["texto"], "origen": obs["origen"]})
        else:
            obs_list.append(dict(obs))
    return {
        "id_medio_pago": id_medio_pago,
        "nombre_medio": nombre_medio,
        "valor_total": valor_total,
        "lineas": _audit_line_dicts(lineas),
        "observaciones": obs_list,
    }


def _validate_id_venta(id_venta: object) -> str:
    if not isinstance(id_venta, str) or not id_venta.strip():
        raise SaleValidationError("Debe enviar un id_venta UUID válido.")
    try:
        return str(uuid.UUID(id_venta.strip()))
    except ValueError as error:
        raise SaleValidationError("Debe enviar un id_venta UUID válido.") from error


def _resolve_lines_with_promociones(
    connection: sqlite3.Connection, lineas: Sequence[Mapping]
) -> List[Mapping]:
    pending: List[Mapping] = []
    promos_by_id: Dict[int, Mapping] = {}
    for raw in lineas:
        product, cantidad, _precio_aplicado = _validate_raw_line(connection, raw)
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
        active_promo = (
            promo if promo is not None and is_active_cantidad_por_monto(promo) else None
        )
        pending.append(
            {
                "id_producto": product["id_producto"],
                "nombre_producto": product["nombre"],
                "precio_aplicado": product["precio"],
                "cantidad": cantidad,
                "promocion_id": (
                    int(active_promo["id"]) if active_promo is not None else None
                ),
                "nombre_promocion": (
                    str(active_promo["nombre"]) if active_promo is not None else None
                ),
            }
        )

    line_maps = [
        {
            "id_producto": line["id_producto"],
            "cantidad": line["cantidad"],
            "precio_aplicado": line["precio_aplicado"],
            "promocion_id": line["promocion_id"],
        }
        for line in pending
    ]
    charged_amounts = compute_cart_line_subtotals(
        line_maps, promos_by_id=promos_by_id
    )

    resolved: List[Mapping] = []
    for line, charged in zip(pending, charged_amounts):
        list_subtotal = line["cantidad"] * line["precio_aplicado"]
        # Snapshot solo si la promo bajó el cobro. Si total == subtotal, nulos.
        hubo_descuento = charged < list_subtotal
        resolved.append(
            {
                "id_producto": line["id_producto"],
                "nombre_producto": line["nombre_producto"],
                "precio_aplicado": line["precio_aplicado"],
                "cantidad": line["cantidad"],
                "subtotal": list_subtotal,
                "total": charged,
                "id_promocion": line["promocion_id"] if hubo_descuento else None,
                "nombre_promocion": (
                    line["nombre_promocion"] if hubo_descuento else None
                ),
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
