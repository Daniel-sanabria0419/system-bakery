"""Motor de promociones tipadas (packs greedy + carrito por promocion_id).

Cutover 2.0.4: ``USE_PROMOCIONES_TABLE`` default True; cobro por FK.
Cobro: ``(qty // G) * M + (qty % G) * P`` (packs greedy; p. ej. 17 → 4900).
En carrito se suman cantidades del mismo ``promocion_id`` (tras agregar por
``id_producto``) y se aplica la misma fórmula. Sin ``todo_o_nada`` ni
``ajuste_manual``. Desactivar solo con ``BAKERY_USE_PROMOCIONES_TABLE=0``.
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
    """Valida y normaliza config JSON de tipo cantidad_por_monto.

    Claves: ``precio_base``, ``grupo_cantidad``, ``grupo_monto``, ``modo``
    (``ceil`` para valor→qty). Sin ``politica_resto`` ni ``ajuste_manual``.
    """
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

    if "politica_resto" in raw:
        raise ValueError(
            "politica_resto ya no se usa; el cobro es greedy "
            "(packs = qty // grupo_cantidad)."
        )
    if "ajuste_manual" in raw:
        raise ValueError("ajuste_manual no está soportado.")

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
    return {
        "precio_base": precio_base,
        "grupo_cantidad": grupo_cantidad,
        "grupo_monto": grupo_monto,
        "modo": "ceil",
    }


def amount_for_quantity(cantidad: int, config: Mapping) -> int:
    """Monto greedy: ``(qty // G) * M + (qty % G) * P``.

    Ej.: G=7, M=2000, P=300 → 7=2000, 8=2300, 14=4000, 17=4900.
    """
    cantidad_ok = _require_positive_int(
        cantidad, "La cantidad debe ser un entero mayor que 0."
    )
    cfg = parse_cantidad_por_monto_config(config)
    grupo_cantidad = cfg["grupo_cantidad"]
    packs = cantidad_ok // grupo_cantidad
    resto = cantidad_ok % grupo_cantidad
    return packs * cfg["grupo_monto"] + resto * cfg["precio_base"]


def quantity_from_value(valor: int, config: Mapping) -> Tuple[int, int]:
    """Pad valor→cantidad: ``ceil(valor / precio_base)``.

    El segundo valor es el cobro greedy de esa qty (puede diferir del tipado).
    """
    valor_ok = _require_positive_int(valor, "El valor debe ser un entero mayor que 0.")
    cfg = parse_cantidad_por_monto_config(config)
    precio_base = cfg["precio_base"]
    cantidad = (valor_ok + precio_base - 1) // precio_base
    return cantidad, amount_for_quantity(cantidad, cfg)


def amount_for_cart_group(lines: Sequence[Mapping], config: Mapping) -> int:
    """Monto del grupo: suma qty (por ``id_producto``) y fórmula greedy.

    Equivale a packs greedy sobre el total del ``promocion_id`` (4+3 → 2000;
    7+5 → 3500; 8 → 2300; 17 → 4900).
    """
    if not lines:
        raise ValueError("El grupo de carrito no puede estar vacío.")
    cfg = parse_cantidad_por_monto_config(config)
    qty_by_sku: Dict[int, int] = {}
    for line in lines:
        id_producto = line.get("id_producto")
        if isinstance(id_producto, bool) or not isinstance(id_producto, int):
            raise ValueError("id_producto debe ser un entero.")
        cantidad = _require_positive_int(
            line.get("cantidad"), "La cantidad debe ser un entero mayor que 0."
        )
        qty_by_sku[id_producto] = qty_by_sku.get(id_producto, 0) + cantidad
    total_qty = sum(qty_by_sku.values())
    return amount_for_quantity(total_qty, cfg)


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
    """Subtotales por línea: greedy por ``promocion_id`` + reparto B.

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
