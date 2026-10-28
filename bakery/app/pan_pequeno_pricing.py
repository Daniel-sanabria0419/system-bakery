"""Categoría Pan pequeño y precio de lista $300.

El cobro vive en ``bakery.app.promotions``. Este módulo no calcula montos.
"""

from __future__ import annotations

from typing import Mapping, Optional, Union

from bakery.persistence.schema import NOMBRE_CATEGORIA_PAN_PEQUENO

PRECIO_UNITARIO_PAN_PEQUENO = 300


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
