from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence

from bakery.app.promotions import (
    amount_for_quantity,
    compute_cart_line_subtotals,
    is_active_cantidad_por_monto,
    parse_cantidad_por_monto_config,
)
from bakery.persistence.schema import ESTADO_ACTIVO


@dataclass(frozen=True)
class PurchaseLine:
    """Línea de compra en memoria (producto + cantidad + subtotal)."""

    id_producto: int
    nombre: str
    precio_aplicado: int
    cantidad: int
    subtotal: int
    promocion_id: Optional[int] = None


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
        promocion_id: Optional[int] = None,
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
        if promocion_id is not None and (
            isinstance(promocion_id, bool) or not isinstance(promocion_id, int)
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
                promocion_id=promocion_id,
            )
        )
        return True

    def replace_items(self, items: Sequence[PurchaseLine]) -> None:
        self._items = list(items)

    def remove_at(self, index: int) -> bool:
        if isinstance(index, bool) or not isinstance(index, int):
            return False
        if index < 0 or index >= len(self._items):
            return False
        del self._items[index]
        return True

    def clear(self) -> None:
        self._items.clear()

    def items(self) -> List[PurchaseLine]:
        return list(self._items)

    def total(self) -> int:
        return sum(item.subtotal for item in self._items)

    def list_subtotal(self) -> int:
        """Suma a precio de lista: Σ (precio_c/u × cantidad)."""
        return sum(item.precio_aplicado * item.cantidad for item in self._items)

    def discount(self) -> int:
        """Descuento del carrito: list_subtotal − total, clampeado a ≥ 0."""
        delta = self.list_subtotal() - self.total()
        return delta if delta > 0 else 0


def candidates_by_exact_price(
    products: Sequence[Mapping], precio: int
) -> List[Mapping]:
    """Legado / API-only: match por precio exacto.

    El desktop de cobro no filtra la grilla por dígitos. Se mantiene para
    tests y ``GET /productos/activos?precio=``.
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


class SaleDraft:
    """Orquesta producto seleccionado, cantidad y compra acumulada (solo qty)."""

    def __init__(self) -> None:
        self.purchase = Purchase()
        self._selected_product: Optional[Mapping] = None
        self._quantity = 1
        self._promo_by_id: Dict[int, Mapping] = {}

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
        promocion_id = product.get("promocion_id")
        if promocion_id is not None and (
            isinstance(promocion_id, bool) or not isinstance(promocion_id, int)
        ):
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
        if promocion_id is not None:
            selected["promocion_id"] = promocion_id
        promo = _promo_payload_from_product(product)
        if promo is not None:
            selected["promocion_id"] = promo["id"]
            selected["promocion_tipo"] = promo["tipo"]
            selected["promocion_configuracion"] = promo["configuracion"]
            selected["promocion_activo"] = promo["activo"]
            self._promo_by_id[int(promo["id"])] = promo
        self._selected_product = selected
        return True

    def clear_product_selection(self) -> None:
        self._selected_product = None

    def selected_product(self) -> Optional[Mapping]:
        if self._selected_product is None:
            return None
        return dict(self._selected_product)

    def selected_is_pan_pequeno(self) -> bool:
        """True si la selección tiene promo activa cantidad_por_monto por FK."""
        if self._selected_product is None:
            return False
        return self._selected_promo_config() is not None

    def set_quantity(self, quantity: int) -> bool:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            return False
        self._quantity = quantity
        return True

    def quantity(self) -> int:
        return self._quantity

    def current_subtotal(self) -> Optional[int]:
        """Preview pre-Agregar de la selección actual (solo fórmula por cantidad)."""
        product = self._selected_product
        if product is None:
            return None
        config = self._selected_promo_config()
        if config is not None:
            return amount_for_quantity(self._quantity, config)
        return product["precio"] * self._quantity

    def add_to_purchase(self) -> bool:
        """Agrega línea del producto seleccionado. Rechaza sin producto.

        Cantidad solo vía ``quantity()`` (−/+). Tras agregar, cada línea
        conserva el cobro de su propia cantidad.
        """
        product = self._selected_product
        if product is None:
            return False
        config = self._selected_promo_config()
        if config is not None:
            promocion_id = int(product["promocion_id"])
            precio_aplicado = int(config["precio_base"])
            subtotal = amount_for_quantity(self._quantity, config)
        else:
            promocion_id = None
            precio_aplicado = product["precio"]
            subtotal = precio_aplicado * self._quantity
        if not self.purchase.add(
            id_producto=product["id_producto"],
            nombre=product["nombre"],
            precio_aplicado=precio_aplicado,
            cantidad=self._quantity,
            subtotal=subtotal,
            promocion_id=promocion_id,
        ):
            return False
        self._recalculate_purchase_subtotals()
        self.clear_product_selection()
        self._quantity = 1
        return True

    def remove_line(self, index: int) -> bool:
        """Quita una línea por índice y recalcula promos del carrito."""
        if not self.purchase.remove_at(index):
            return False
        self._recalculate_purchase_subtotals()
        return True

    def clear_cart(self) -> None:
        """Vacía solo las líneas del carrito; conserva selección y cantidad."""
        self.purchase.clear()

    def clear_purchase(self) -> None:
        """Reset completo: carrito + selección + cantidad (p. ej. tras venta OK)."""
        self.purchase.clear()
        self.clear_product_selection()
        self._quantity = 1
        self._promo_by_id.clear()

    def list_subtotal(self) -> int:
        return self.purchase.list_subtotal()

    def discount(self) -> int:
        return self.purchase.discount()

    def total(self) -> int:
        return self.purchase.total()

    def _selected_promo_config(self) -> Optional[Mapping]:
        product = self._selected_product
        if product is None:
            return None
        promo_id = product.get("promocion_id")
        if isinstance(promo_id, bool) or not isinstance(promo_id, int):
            return None
        promo = {
            "id": promo_id,
            "tipo": product.get("promocion_tipo"),
            "configuracion": product.get("promocion_configuracion"),
            "activo": product.get("promocion_activo", ESTADO_ACTIVO),
        }
        if not is_active_cantidad_por_monto(promo):
            cached = self._promo_by_id.get(promo_id)
            if cached is None or not is_active_cantidad_por_monto(cached):
                return None
            promo = dict(cached)
        try:
            return parse_cantidad_por_monto_config(promo["configuracion"])
        except ValueError:
            return None

    def _recalculate_purchase_subtotals(self) -> None:
        items = self.purchase.items()
        if not items:
            return
        line_maps = [
            {
                "id_producto": item.id_producto,
                "cantidad": item.cantidad,
                "precio_aplicado": item.precio_aplicado,
                "promocion_id": item.promocion_id,
            }
            for item in items
        ]
        computed = compute_cart_line_subtotals(
            line_maps, promos_by_id=self._promo_by_id
        )
        rebuilt = [
            PurchaseLine(
                id_producto=item.id_producto,
                nombre=item.nombre,
                precio_aplicado=item.precio_aplicado,
                cantidad=item.cantidad,
                subtotal=subtotal,
                promocion_id=item.promocion_id,
            )
            for item, subtotal in zip(items, computed)
        ]
        self.purchase.replace_items(rebuilt)


def _promo_payload_from_product(product: Mapping) -> Optional[Mapping]:
    promo_id = product.get("promocion_id")
    if isinstance(promo_id, bool) or not isinstance(promo_id, int):
        return None
    tipo = product.get("promocion_tipo")
    configuracion = product.get("promocion_configuracion")
    activo = product.get("promocion_activo", ESTADO_ACTIVO)
    if not isinstance(tipo, str) or not isinstance(configuracion, str):
        return None
    if isinstance(activo, bool) or not isinstance(activo, int):
        return None
    promo = {
        "id": promo_id,
        "tipo": tipo,
        "configuracion": configuracion,
        "activo": activo,
    }
    if not is_active_cantidad_por_monto(promo):
        return None
    try:
        parse_cantidad_por_monto_config(configuracion)
    except ValueError:
        return None
    return promo
