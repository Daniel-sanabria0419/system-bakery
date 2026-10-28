"""Motor de promociones tipadas (cantidad_por_monto + carrito por promocion_id).

Cutover 2.0.4: ``USE_PROMOCIONES_TABLE`` default True; cobro por FK.
JSON de DB slim: ``{"precio_base": N, "modo": "ceil"}``.
Cobro: menor múltiplo de 1000 con ``ceil(monto / precio_base) >= cantidad``
(p. ej. 17 → 5000). ``modo: ceil`` también define valor→qty.
Desactivar con ``BAKERY_USE_PROMOCIONES_TABLE=0``.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    PROMO_GRUPO_CANTIDAD_DEFAULT,
    PROMO_GRUPO_MONTO_DEFAULT,
    PROMO_POLITICA_RESTO_DEFAULT,
    TIPO_PROMOCION_CANTIDAD_POR_MONTO,
)

# Flag de cobro. Default True tras cutover (Etapa 5).
USE_PROMOCIONES_TABLE = True

# Pasos de la tabla valor→cantidad (1000→4, 2000→7, …). El cobro es el menor
# múltiplo de esta escala con ceil(monto / precio_base) >= cantidad del grupo.
PROMO_MONTO_ESCALA = 1000

# DB seed: solo precio_base + modo. El motor acepta grupo_*/politica opcionales
# (p. ej. re-parse del dict normalizado) y rellena defaults si faltan.
_ALLOWED_CONFIG_KEYS = frozenset(
    {
        "precio_base",
        "modo",
        "grupo_cantidad",
        "grupo_monto",
        "politica_resto",
    }
)


def use_promociones_table() -> bool:
    env = os.environ.get("BAKERY_USE_PROMOCIONES_TABLE")
    if env is not None and env.strip() != "":
        return env.strip().lower() in ("1", "true", "yes", "on")
    return bool(USE_PROMOCIONES_TABLE)


def parse_cantidad_por_monto_config(configuracion: object) -> Dict[str, Any]:
    """Valida config; DB canónica es ``precio_base`` + ``modo``.

    Si faltan ``grupo_cantidad`` / ``grupo_monto`` / ``politica_resto``, usa
    defaults de código (7 / 2000 / greedy). Rechaza ``ajuste_manual``.
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

    if "ajuste_manual" in raw:
        raise ValueError("ajuste_manual no está soportado.")
    extra = set(raw) - _ALLOWED_CONFIG_KEYS
    if extra:
        raise ValueError(
            "configuracion tiene claves no permitidas: "
            f"{sorted(extra)}"
        )

    precio_base = _require_positive_int(
        raw.get("precio_base"), "precio_base debe ser un entero mayor que 0."
    )
    modo = raw.get("modo")
    if modo != "ceil":
        raise ValueError("modo debe ser 'ceil'.")

    if "grupo_cantidad" in raw:
        grupo_cantidad = _require_positive_int(
            raw.get("grupo_cantidad"),
            "grupo_cantidad debe ser un entero mayor que 0.",
        )
    else:
        grupo_cantidad = PROMO_GRUPO_CANTIDAD_DEFAULT
    if "grupo_monto" in raw:
        grupo_monto = _require_positive_int(
            raw.get("grupo_monto"),
            "grupo_monto debe ser un entero mayor que 0.",
        )
    else:
        grupo_monto = PROMO_GRUPO_MONTO_DEFAULT
    if "politica_resto" in raw:
        politica = raw.get("politica_resto")
        if politica != PROMO_POLITICA_RESTO_DEFAULT:
            raise ValueError(
                f"politica_resto debe ser '{PROMO_POLITICA_RESTO_DEFAULT}'."
            )
    else:
        politica = PROMO_POLITICA_RESTO_DEFAULT

    return {
        "precio_base": precio_base,
        "grupo_cantidad": grupo_cantidad,
        "grupo_monto": grupo_monto,
        "modo": "ceil",
        "politica_resto": politica,
    }


def amount_for_quantity(cantidad: int, config: Mapping) -> int:
    """Menor múltiplo de ``PROMO_MONTO_ESCALA`` con ``ceil(monto / precio_base) >= cantidad``.

    Inversa de la tabla valor→cantidad. Con precio_base 300 y escala 1000:
    4→1000, 7→2000, 10→3000, 14→4000, 17→5000, 20→6000, 24→7000,
    27→8000, 30→9000, 34→10000. Entre nudos sube al siguiente múltiplo
    (8→3000, 12→4000).
    """
    cantidad_ok = _require_positive_int(
        cantidad, "La cantidad debe ser un entero mayor que 0."
    )
    cfg = parse_cantidad_por_monto_config(config)
    precio_base = cfg["precio_base"]
    # Menor entero con ceil(m / precio_base) >= cantidad, luego al múltiplo
    # de la escala (la tabla valor→cantidad va de mil en mil).
    minimo = precio_base * (cantidad_ok - 1) + 1
    pasos = (minimo + PROMO_MONTO_ESCALA - 1) // PROMO_MONTO_ESCALA
    return pasos * PROMO_MONTO_ESCALA


def quantity_from_value(valor: int, config: Mapping) -> Tuple[int, int]:
    """Pad valor→cantidad: ``ceil(valor / precio_base)`` (sin cambio).

    El segundo valor es el cobro de esa qty en la escala de miles
    (puede diferir del valor tipado).
    """
    valor_ok = _require_positive_int(valor, "El valor debe ser un entero mayor que 0.")
    cfg = parse_cantidad_por_monto_config(config)
    precio_base = cfg["precio_base"]
    cantidad = (valor_ok + precio_base - 1) // precio_base
    return cantidad, amount_for_quantity(cantidad, cfg)


def amount_for_cart_group(lines: Sequence[Mapping], config: Mapping) -> int:
    """Monto del grupo: suma la qty y luego ``amount_for_quantity``.

    El agrupamiento es anterior a la fórmula.
    Ej.: 4+3 → 2000; 7+5 → 4000; 8 → 3000; 17 → 5000.
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
    """Subtotales por línea: escala ceil por ``promocion_id`` + reparto B.

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
