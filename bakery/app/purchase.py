from dataclasses import dataclass
from typing import List, Mapping, Optional, Sequence

from bakery.app.calculator import Calculator
from bakery.app.pan_pequeno_pricing import (
    PRECIO_UNITARIO_PAN_PEQUENO,
    is_pan_pequeno,
    quantity_from_value,
    subtotal_for_quantity,
)


@dataclass(frozen=True)
class PurchaseLine:
    """Línea de compra en memoria (producto + cantidad + subtotal)."""

    id_producto: int
    nombre: str
    precio_aplicado: int
    cantidad: int
    subtotal: int


class Purchase:
    """Lista temporal de líneas de producto (solo memoria)."""

    def __init__(self) -> None:
        self._items: List[PurchaseLine] = []

    def add(
        self,
        *,
        id_producto: int,
        nombre: str,
        precio_aplicado: int,
        cantidad: int,
        subtotal: Optional[int] = None,
    ) -> bool:
        if isinstance(id_producto, bool) or not isinstance(id_producto, int):
            return False
        if not isinstance(nombre, str) or not nombre.strip():
            return False
        if (
            isinstance(precio_aplicado, bool)
            or not isinstance(precio_aplicado, int)
            or precio_aplicado <= 0
        ):
            return False
        if (
            isinstance(cantidad, bool)
            or not isinstance(cantidad, int)
            or cantidad <= 0
        ):
            return False
        if subtotal is None:
            computed = precio_aplicado * cantidad
        else:
            if isinstance(subtotal, bool) or not isinstance(subtotal, int) or subtotal <= 0:
                return False
            computed = subtotal
        if computed <= 0:
            return False
        self._items.append(
            PurchaseLine(
                id_producto=id_producto,
                nombre=nombre.strip(),
                precio_aplicado=precio_aplicado,
                cantidad=cantidad,
                subtotal=computed,
            )
        )
        return True

    def clear(self) -> None:
        self._items.clear()

    def items(self) -> List[PurchaseLine]:
        return list(self._items)

    def total(self) -> int:
        return sum(item.subtotal for item in self._items)


def candidates_by_exact_price(
    products: Sequence[Mapping], precio: int
) -> List[Mapping]:
    """Legado / API-only: match por precio exacto.

    El cobro desktop (2.0.2+) usa ``candidates_by_price_prefix``. Se mantiene
    para tests y el espíritu del filtro exacto vía API; no eliminar sin decisión.
    """
    if isinstance(precio, bool) or not isinstance(precio, int) or precio <= 0:
        return []
    matches: List[Mapping] = []
    for product in products:
        product_price = product.get("precio")
        if product_price != precio:
            continue
        estado = product.get("id_estado")
        if estado is not None and estado != 1:
            continue
        matches.append(product)
    return matches


def candidates_by_price_prefix(
    products: Sequence[Mapping], prefix: str
) -> List[Mapping]:
    """Filtra productos activos cuyo precio (string del entero) empieza con prefix.

    Pensado para Calculator.digits() (p. ej. "4", "45"). Prefijo vacío o
    no numérico → lista vacía (la UI no aplica filtro de precio en ese caso).
    No formatea COP; sin floats. El acote por categoría lo hace el llamador.
    """
    if not isinstance(prefix, str) or not prefix or not prefix.isdigit():
        return []
    matches: List[Mapping] = []
    for product in products:
        product_price = product.get("precio")
        if (
            isinstance(product_price, bool)
            or not isinstance(product_price, int)
            or product_price <= 0
        ):
            continue
        if not str(product_price).startswith(prefix):
            continue
        estado = product.get("id_estado")
        if estado is not None and estado != 1:
            continue
        matches.append(product)
    return matches


class SaleDraft:
    """Orquesta entrada, producto seleccionado, cantidad y compra acumulada."""

    def __init__(self) -> None:
        self.entry = Calculator()
        self.purchase = Purchase()
        self._selected_product: Optional[Mapping] = None
        self._quantity = 1

    def select_product(self, product: Mapping) -> bool:
        if not isinstance(product, Mapping):
            return False
        id_producto = product.get("id_producto")
        nombre = product.get("nombre")
        precio = product.get("precio")
        if isinstance(id_producto, bool) or not isinstance(id_producto, int):
            return False
        if not isinstance(nombre, str) or not nombre.strip():
            return False
        if isinstance(precio, bool) or not isinstance(precio, int) or precio <= 0:
            return False
        nombre_categoria = product.get("nombre_categoria")
        if nombre_categoria is not None and not isinstance(nombre_categoria, str):
            return False
        id_categoria = product.get("id_categoria")
        if id_categoria is not None and (
            isinstance(id_categoria, bool) or not isinstance(id_categoria, int)
        ):
            return False
        ruta_imagen = product.get("ruta_imagen")
        if ruta_imagen is not None and not isinstance(ruta_imagen, str):
            return False
        selected = {
            "id_producto": id_producto,
            "nombre": nombre.strip(),
            "precio": precio,
        }
        if id_categoria is not None:
            selected["id_categoria"] = id_categoria
        if isinstance(nombre_categoria, str) and nombre_categoria.strip():
            selected["nombre_categoria"] = nombre_categoria.strip()
        if isinstance(ruta_imagen, str) and ruta_imagen.strip():
            selected["ruta_imagen"] = ruta_imagen.strip()
        self._selected_product = selected
        return True

    def clear_product_selection(self) -> None:
        self._selected_product = None

    def selected_product(self) -> Optional[Mapping]:
        if self._selected_product is None:
            return None
        return dict(self._selected_product)

    def selected_is_pan_pequeno(self) -> bool:
        product = self._selected_product
        if product is None:
            return False
        return is_pan_pequeno(product.get("nombre_categoria"))

    def set_quantity(self, quantity: int) -> bool:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            return False
        self._quantity = quantity
        return True

    def quantity(self) -> int:
        return self._quantity

    def current_subtotal(self) -> Optional[int]:
        """Subtotal de la selección actual (promo Pan pequeño vía módulo)."""
        product = self._selected_product
        if product is None:
            return None
        if is_pan_pequeno(product.get("nombre_categoria")):
            return subtotal_for_quantity(self._quantity)
        return product["precio"] * self._quantity

    def pad_display_amount(self) -> int:
        """Monto del display del pad: entrada, valor tipado PP, o subtotal a agregar."""
        if self._selected_product is None:
            amount = self.entry.current_amount()
            return 0 if amount is None else amount
        if self.selected_is_pan_pequeno():
            typed = self.entry.current_amount()
            if typed is not None:
                return typed
        subtotal = self.current_subtotal()
        return 0 if subtotal is None else subtotal

    def apply_value(self, valor: int) -> bool:
        """Para Pan pequeño: valor → cantidad/subtotal (ceil). Otras: no-op False."""
        if not self.selected_is_pan_pequeno():
            return False
        try:
            cantidad, _subtotal = quantity_from_value(valor)
        except ValueError:
            return False
        self._quantity = cantidad
        return True

    def add_to_purchase(self) -> bool:
        """Agrega línea del producto seleccionado. Rechaza sin producto."""
        product = self._selected_product
        if product is None:
            return False
        if is_pan_pequeno(product.get("nombre_categoria")):
            precio_aplicado = PRECIO_UNITARIO_PAN_PEQUENO
            subtotal = subtotal_for_quantity(self._quantity)
        else:
            precio_aplicado = product["precio"]
            subtotal = precio_aplicado * self._quantity
        if not self.purchase.add(
            id_producto=product["id_producto"],
            nombre=product["nombre"],
            precio_aplicado=precio_aplicado,
            cantidad=self._quantity,
            subtotal=subtotal,
        ):
            return False
        self.entry.clear_entry()
        self.clear_product_selection()
        self._quantity = 1
        return True

    def clear_purchase(self) -> None:
        self.purchase.clear()
        self.entry.clear_entry()
        self.clear_product_selection()
        self._quantity = 1

    def total(self) -> int:
        return self.purchase.total()
