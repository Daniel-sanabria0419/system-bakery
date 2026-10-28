"""Motor de promociones tipadas (cantidad_por_monto por línea).

JSON de DB: ``{"precio_base": N, "modo": "ceil"}``.
Cada línea usa su propia cantidad. Promo solo si esa cantidad es un nudo
de la tabla ceil en miles (17 → 5000); si no, ``cantidad × precio_base``.
Otra línea no cambia el cobro de las demás.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Sequence

from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    TIPO_PROMOCION_CANTIDAD_POR_MONTO,
)

# Tabla de nudos en miles, de 1000 a 10000. Promo solo si la cantidad
# de la línea es exactamente ceil(monto / precio_base) para uno de esos montos.
PROMO_MONTO_ESCALA = 1000
PROMO_TABLA_MILES = 10

_ALLOWED_CONFIG_KEYS = frozenset({"precio_base", "modo"})


def parse_cantidad_por_monto_config(configuracion: object) -> Dict[str, Any]:
    """Valida config canónica: ``precio_base`` + ``modo`` ``ceil``.

    Rechaza ``ajuste_manual`` y claves que no entran al cobro.
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

    return {
        "precio_base": precio_base,
        "modo": "ceil",
    }


def amount_for_quantity(cantidad: int, config: Mapping) -> int:
    """Promo solo en los nudos exactos de la tabla ceil (miles, hasta 10000).

    Con precio_base 300: 4→1000, 7→2000, 10→3000, 14→4000, 17→5000,
    20→6000, 24→7000, 27→8000, 30→9000, 34→10000.
    Cualquier otra cantidad: ``cantidad × precio_base``
    (1→300, 8→2400, 12→3600).
    """
    cantidad_ok = _require_positive_int(
        cantidad, "La cantidad debe ser un entero mayor que 0."
    )
    cfg = parse_cantidad_por_monto_config(config)
    precio_base = cfg["precio_base"]
    monto = PROMO_MONTO_ESCALA
    tope = PROMO_TABLA_MILES * PROMO_MONTO_ESCALA
    while monto <= tope:
        if (monto + precio_base - 1) // precio_base == cantidad_ok:
            return monto
        monto += PROMO_MONTO_ESCALA
    return cantidad_ok * precio_base


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
    """Subtotal de cada línea con su propia cantidad. Sin pool de carrito.

    Cada línea: ``id_producto``, ``cantidad``, ``precio_aplicado``,
    ``promocion_id`` (opcional). Promo ``cantidad_por_monto`` activa →
    ``amount_for_quantity`` de esa línea. Si no, ``precio_aplicado × cantidad``.
    """
    if not lines:
        return []
    result: List[int] = []
    for line in lines:
        promo_id = line.get("promocion_id")
        promo = None
        if (
            not isinstance(promo_id, bool)
            and isinstance(promo_id, int)
            and promo_id in promos_by_id
        ):
            candidate = promos_by_id[promo_id]
            if is_active_cantidad_por_monto(candidate):
                promo = candidate
        if promo is None:
            precio = _require_positive_int(
                line.get("precio_aplicado"),
                "El precio aplicado debe ser un entero mayor que 0.",
            )
            cantidad = _require_positive_int(
                line.get("cantidad"),
                "La cantidad debe ser un entero mayor que 0.",
            )
            result.append(precio * cantidad)
            continue
        config = parse_cantidad_por_monto_config(promo["configuracion"])
        cantidad = _require_positive_int(
            line.get("cantidad"),
            "La cantidad debe ser un entero mayor que 0.",
        )
        result.append(amount_for_quantity(cantidad, config))
    return result


def _require_positive_int(value: object, message: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(message)
    return value
