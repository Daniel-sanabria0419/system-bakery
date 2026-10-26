"""Precio y promoción fijos de la categoría Pan pequeño.

Fuente única de verdad para subtotales y conversión valor→cantidad.
Sin floats. Sin motor genérico de promociones.
"""

from __future__ import annotations

from typing import Mapping, Optional, Tuple, Union

from bakery.persistence.schema import NOMBRE_CATEGORIA_PAN_PEQUENO

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
    """Subtotal entero para una cantidad de Pan pequeño.

    Promo solo si cantidad es múltiplo de 7: (cantidad // 7) * 2000.
    Si no: cantidad * 300.
    """
    cantidad_ok = _require_positive_int(cantidad, "La cantidad debe ser un entero mayor que 0.")
    if cantidad_ok % PROMO_CANTIDAD == 0:
        return (cantidad_ok // PROMO_CANTIDAD) * PROMO_VALOR
    return cantidad_ok * PRECIO_UNITARIO_PAN_PEQUENO


def quantity_from_value(valor: int) -> Tuple[int, int]:
    """Convierte un valor deseado en (cantidad, subtotal) válidos.

    Si el valor coincide exactamente con algún subtotal, usa esa cantidad
    (la menor si hay empate).
    Si no, redondea hacia arriba al menor subtotal alcanzable ≥ valor
    (nunca hacia abajo).
    """
    valor_ok = _require_positive_int(valor, "El valor debe ser un entero mayor que 0.")
    q_max = max(
        valor_ok // PRECIO_UNITARIO_PAN_PEQUENO + PROMO_CANTIDAD + 1,
        PROMO_CANTIDAD + 1,
    )
    best_q: Optional[int] = None
    best_sub: Optional[int] = None
    for cantidad in range(1, q_max + 1):
        subtotal = subtotal_for_quantity(cantidad)
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
        # Ampliación defensiva (no debería ocurrir con el bound anterior).
        cantidad = q_max + 1
        while True:
            subtotal = subtotal_for_quantity(cantidad)
            if subtotal >= valor_ok:
                return cantidad, subtotal
            cantidad += 1
    return best_q, best_sub


def _require_positive_int(value: object, message: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(message)
    return value
