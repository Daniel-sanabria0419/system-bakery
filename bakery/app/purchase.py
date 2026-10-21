from dataclasses import dataclass
from typing import List, Mapping, Optional, Sequence

from bakery.app.calculator import Calculator


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
        subtotal = precio_aplicado * cantidad
        if subtotal <= 0:
            return False
        self._items.append(
            PurchaseLine(
                id_producto=id_producto,
                nombre=nombre.strip(),
                precio_aplicado=precio_aplicado,
                cantidad=cantidad,
                subtotal=subtotal,
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
    """Filtra productos activos (o ya filtrados) con precio exacto entero."""
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
        self._selected_product = {
            "id_producto": id_producto,
            "nombre": nombre.strip(),
            "precio": precio,
        }
        return True

    def clear_product_selection(self) -> None:
        self._selected_product = None

    def selected_product(self) -> Optional[Mapping]:
        if self._selected_product is None:
            return None
        return dict(self._selected_product)

    def set_quantity(self, quantity: int) -> bool:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            return False
        self._quantity = quantity
        return True

    def quantity(self) -> int:
        return self._quantity

    def add_to_purchase(self) -> bool:
        """Agrega línea del producto seleccionado. Rechaza sin producto."""
        product = self._selected_product
        if product is None:
            return False
        if not self.purchase.add(
            id_producto=product["id_producto"],
            nombre=product["nombre"],
            precio_aplicado=product["precio"],
            cantidad=self._quantity,
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
