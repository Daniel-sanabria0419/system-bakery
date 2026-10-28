"""Shim de compatibilidad (Beta 2.0.4 cutover).

La lógica de montos vive en ``bakery.app.promotions`` con la config canónica.
``is_pan_pequeno`` permanece solo para catálogo / validación de lista, no para cobro.
"""

from __future__ import annotations

from typing import Mapping, Optional, Tuple, Union

from bakery.app.promotions import (
    amount_for_quantity,
    quantity_from_value as promo_quantity_from_value,
)
from bakery.persistence.schema import (
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    PROMOCION_PAN_PEQUENO_CONFIG,
)

PRECIO_UNITARIO_PAN_PEQUENO = 300
PROMO_CANTIDAD = 7
PROMO_VALOR = 2000


def is_pan_pequeno(categoria: Union[str, Mapping, None]) -> bool:
    """True si la categoría es Pan pequeño (por nombre exacto)."""
    if isinstance(categoria, str):
        return categoria == NOMBRE_CATEGORIA_PAN_PEQUENO
    if isinstance(categoria, Mapping):
        nombre = categoria.get("nombre")
        return isinstance(nombre, str) and nombre == NOMBRE_CATEGORIA_PAN_PEQUENO
    return False


def is_pan_pequeno_nombre(nombre: Optional[str]) -> bool:
    return isinstance(nombre, str) and nombre == NOMBRE_CATEGORIA_PAN_PEQUENO


def subtotal_for_quantity(cantidad: int) -> int:
    """Delegado al motor ``promotions`` (config canónica)."""
    return amount_for_quantity(cantidad, PROMOCION_PAN_PEQUENO_CONFIG)


def quantity_from_value(valor: int) -> Tuple[int, int]:
    """Delegado al motor ``promotions`` (config canónica)."""
    return promo_quantity_from_value(valor, PROMOCION_PAN_PEQUENO_CONFIG)
