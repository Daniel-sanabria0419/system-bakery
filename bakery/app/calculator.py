from typing import Optional

from bakery.app.money import format_cop


class Calculator:
    """Buffer de entrada numérica actual (local, sin HTTP)."""

    def __init__(self) -> None:
        self._digits = ""

    def press_digit(self, digit: str) -> None:
        if len(digit) != 1 or digit not in "0123456789":
            return
        if not self._digits or self._digits == "0":
            self._digits = digit
            return
        self._digits += digit

    def press_zeros(self) -> None:
        """Append two zeros (button 00), preserving leading-zero rules."""
        if not self._digits or self._digits == "0":
            self._digits = "0"
            return
        self._digits += "00"

    def backspace(self) -> None:
        if not self._digits:
            return
        self._digits = self._digits[:-1]

    def clear_entry(self) -> None:
        self._digits = ""

    def clear(self) -> None:
        self.clear_entry()

    def digits(self) -> str:
        return self._digits

    def current_amount(self) -> Optional[int]:
        if not self._digits:
            return None
        return int(self._digits)

    def display_text(self) -> str:
        """Presentación monetaria de la entrada. Placeholder si no hay dígitos."""
        amount = self.current_amount()
        if amount is None:
            return format_cop(0)
        return format_cop(amount)
