"""Motor de promociones tipadas (Beta 2.0.5 híbrido).

Cutover 2.0.4: ``USE_PROMOCIONES_TABLE`` default True; cobro por FK.
Beta 2.0.5: múltiplos exactos por ``id_producto`` + pool ``todo_o_nada``
del mismo ``promocion_id``. Sin montos por nombre de categoría.
Desactivar solo con ``BAKERY_USE_PROMOCIONES_TABLE=0`` (precio × cantidad plano).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    TIPO_PROMOCION_CANTIDAD_POR_MONTO,
)

# Flag de cobro. Default True tras cutover (Etapa 5).
USE_PROMOCIONES_TABLE = True


def use_promociones_table() -> bool:
    env = os.environ.get("BAKERY_USE_PROMOCIONES_TABLE")
    if env is not None and env.strip() != "":
        return env.strip().lower() in ("1", "true", "yes", "on")
    return bool(USE_PROMOCIONES_TABLE)


def parse_cantidad_por_monto_config(configuracion: object) -> Dict[str, Any]:
    """Valida y normaliza config JSON de tipo cantidad_por_monto."""
    if isinstance(configuracion, Mapping):
        raw = dict(configuracion)
    elif isinstance(configuracion, str):
        try:
            loaded = json.loads(configuracion)
        except json.JSONDecodeError as error:
            raise ValueError("La configuración de promoción no es JSON válido.") from error
        if not isinstance(loaded, dict):
            raise ValueError("La configuración de promoción debe ser un objeto.")
        raw = loaded
    else:
        raise ValueError("La configuración de promoción es inválida.")

    precio_base = _require_positive_int(
        raw.get("precio_base"), "precio_base debe ser un entero mayor que 0."
    )
    grupo_cantidad = _require_positive_int(
        raw.get("grupo_cantidad"), "grupo_cantidad debe ser un entero mayor que 0."
    )
    grupo_monto = _require_positive_int(
        raw.get("grupo_monto"), "grupo_monto debe ser un entero mayor que 0."
    )
    modo = raw.get("modo")
    if modo != "ceil":
        raise ValueError("modo debe ser 'ceil'.")
    politica = raw.get("politica_resto")
    if politica != "todo_o_nada":
        raise ValueError("politica_resto debe ser 'todo_o_nada'.")
    return {
        "precio_base": precio_base,
        "grupo_cantidad": grupo_cantidad,
        "grupo_monto": grupo_monto,
        "modo": "ceil",
        "politica_resto": "todo_o_nada",
    }


def amount_for_quantity(cantidad: int, config: Mapping) -> int:
    """Monto para una qty con política todo_o_nada (§4.1)."""
    cantidad_ok = _require_positive_int(
        cantidad, "La cantidad debe ser un entero mayor que 0."
    )
    cfg = parse_cantidad_por_monto_config(config)
    grupo_cantidad = cfg["grupo_cantidad"]
    if cantidad_ok % grupo_cantidad == 0:
        return (cantidad_ok // grupo_cantidad) * cfg["grupo_monto"]
    return cantidad_ok * cfg["precio_base"]


def quantity_from_value(valor: int, config: Mapping) -> Tuple[int, int]:
    """Menor cantidad cuyo subtotal (misma fórmula) es ≥ valor (modo ceil)."""
    valor_ok = _require_positive_int(valor, "El valor debe ser un entero mayor que 0.")
    cfg = parse_cantidad_por_monto_config(config)
    precio_base = cfg["precio_base"]
    grupo_cantidad = cfg["grupo_cantidad"]
    q_max = max(valor_ok // precio_base + grupo_cantidad + 1, grupo_cantidad + 1)
    best_q: Optional[int] = None
    best_sub: Optional[int] = None
    for cantidad in range(1, q_max + 1):
        subtotal = amount_for_quantity(cantidad, cfg)
        if subtotal < valor_ok:
            continue
        if (
            best_sub is None
            or subtotal < best_sub
            or (subtotal == best_sub and cantidad < best_q)  # type: ignore[operator]
        ):
            best_q = cantidad
            best_sub = subtotal
    if best_q is None or best_sub is None:
        cantidad = q_max + 1
        while True:
            subtotal = amount_for_quantity(cantidad, cfg)
            if subtotal >= valor_ok:
                return cantidad, subtotal
            cantidad += 1
    return best_q, best_sub


def amount_for_cart_group(lines: Sequence[Mapping], config: Mapping) -> int:
    """Monto híbrido 2.0.5: exactos por ``id_producto`` + pool ``todo_o_nada``.

    Cada línea debe traer ``id_producto`` y ``cantidad``. Se suman cantidades
    del mismo SKU; si ``qty_sku % G == 0`` → combos; si no, entra al pool del
    grupo y se aplica la misma política ``todo_o_nada`` al pool.
    """
    if not lines:
        raise ValueError("El grupo de carrito no puede estar vacío.")
    cfg = parse_cantidad_por_monto_config(config)
    grupo_cantidad = cfg["grupo_cantidad"]
    grupo_monto = cfg["grupo_monto"]
    precio_base = cfg["precio_base"]
    qty_by_sku: Dict[int, int] = {}
    for line in lines:
        id_producto = line.get("id_producto")
        if isinstance(id_producto, bool) or not isinstance(id_producto, int):
            raise ValueError("id_producto debe ser un entero.")
        cantidad = _require_positive_int(
            line.get("cantidad"), "La cantidad debe ser un entero mayor que 0."
        )
        qty_by_sku[id_producto] = qty_by_sku.get(id_producto, 0) + cantidad
    monto = 0
    pool = 0
    for qty_sku in qty_by_sku.values():
        if qty_sku % grupo_cantidad == 0:
            monto += (qty_sku // grupo_cantidad) * grupo_monto
        else:
            pool += qty_sku
    if pool > 0:
        if pool % grupo_cantidad == 0:
            monto += (pool // grupo_cantidad) * grupo_monto
        else:
            monto += pool * precio_base
    return monto


def allocate_group_subtotals(
    lines: Sequence[Mapping], monto_grupo: int
) -> List[int]:
    """Reparto B: proporcional por cantidad en enteros; residuo en la última."""
    if not lines:
        return []
    monto = _require_positive_int(
        monto_grupo, "El monto de grupo debe ser un entero mayor que 0."
    )
    cantidades = [
        _require_positive_int(
            line.get("cantidad"), "La cantidad debe ser un entero mayor que 0."
        )
        for line in lines
    ]
    qty_total = sum(cantidades)
    subtotals: List[int] = []
    assigned = 0
    for index, cantidad in enumerate(cantidades):
        if index == len(cantidades) - 1:
            subtotals.append(monto - assigned)
        else:
            part = (monto * cantidad) // qty_total
            subtotals.append(part)
            assigned += part
    return subtotals


def is_active_cantidad_por_monto(promo: Mapping) -> bool:
    if not isinstance(promo, Mapping):
        return False
    if promo.get("activo") != ESTADO_ACTIVO:
        return False
    return promo.get("tipo") == TIPO_PROMOCION_CANTIDAD_POR_MONTO


def compute_cart_line_subtotals(
    lines: Sequence[Mapping],
    *,
    promos_by_id: Mapping[int, Mapping],
) -> List[int]:
    """Subtotales por línea con motor híbrido 2.0.5 por promocion_id activo.

    Cada línea: ``id_producto``, ``cantidad``, ``precio_aplicado``,
    ``promocion_id`` (opcional). Líneas sin promo válida →
    ``precio_aplicado × cantidad``.
    """
    if not lines:
        return []
    n = len(lines)
    result: List[Optional[int]] = [None] * n
    groups: Dict[int, List[int]] = {}
    for index, line in enumerate(lines):
        promo_id = line.get("promocion_id")
        if (
            isinstance(promo_id, bool)
            or not isinstance(promo_id, int)
            or promo_id not in promos_by_id
        ):
            precio = _require_positive_int(
                line.get("precio_aplicado"),
                "El precio aplicado debe ser un entero mayor que 0.",
            )
            cantidad = _require_positive_int(
                line.get("cantidad"),
                "La cantidad debe ser un entero mayor que 0.",
            )
            result[index] = precio * cantidad
            continue
        promo = promos_by_id[promo_id]
        if not is_active_cantidad_por_monto(promo):
            precio = _require_positive_int(
                line.get("precio_aplicado"),
                "El precio aplicado debe ser un entero mayor que 0.",
            )
            cantidad = _require_positive_int(
                line.get("cantidad"),
                "La cantidad debe ser un entero mayor que 0.",
            )
            result[index] = precio * cantidad
            continue
        groups.setdefault(promo_id, []).append(index)

    for promo_id, indices in groups.items():
        promo = promos_by_id[promo_id]
        config = parse_cantidad_por_monto_config(promo["configuracion"])
        group_lines = [lines[i] for i in indices]
        monto = amount_for_cart_group(group_lines, config)
        parts = allocate_group_subtotals(group_lines, monto)
        for index, subtotal in zip(indices, parts):
            result[index] = subtotal

    filled: List[int] = []
    for value in result:
        if value is None:
            raise ValueError("No se pudo calcular el subtotal de una línea.")
        filled.append(value)
    return filled


def _require_positive_int(value: object, message: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(message)
    return value
