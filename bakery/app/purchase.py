from typing import List

from bakery.app.calculator import Calculator


class Purchase:
    """Lista temporal de montos de una compra (solo memoria)."""

    def __init__(self) -> None:
        self._items: List[int] = []

    def add(self, amount: int) -> bool:
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            return False
        self._items.append(amount)
        return True

    def clear(self) -> None:
        self._items.clear()

    def items(self) -> List[int]:
        return list(self._items)

    def total(self) -> int:
        return sum(self._items)


class SaleDraft:
    """Orquesta la entrada actual y la compra acumulada."""

    def __init__(self) -> None:
        self.entry = Calculator()
        self.purchase = Purchase()

    def add_to_purchase(self) -> bool:
        amount = self.entry.current_amount()
        if amount is None or amount <= 0:
            return False
        if not self.purchase.add(amount):
            return False
        self.entry.clear_entry()
        return True

    def clear_purchase(self) -> None:
        self.purchase.clear()
        self.entry.clear_entry()

    def total(self) -> int:
        return self.purchase.total()
