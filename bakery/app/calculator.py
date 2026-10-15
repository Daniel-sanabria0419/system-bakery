from typing import List, Optional

_OPERATORS = "+-"


class Calculator:
    def __init__(self) -> None:
        self._tokens: List[str] = []

    def press_digit(self, digit: str) -> None:
        if len(digit) != 1 or digit not in "0123456789":
            return
        if not self._tokens or self._tokens[-1] in _OPERATORS:
            self._tokens.append(digit)
            return
        if self._tokens[-1] == "0":
            self._tokens[-1] = digit
            return
        self._tokens[-1] += digit

    def press_add(self) -> None:
        self._press_operator("+")

    def press_subtract(self) -> None:
        self._press_operator("-")

    def clear(self) -> None:
        self._tokens.clear()

    def backspace(self) -> None:
        if not self._tokens or self._tokens[-1] in _OPERATORS:
            return
        current = self._tokens[-1]
        if len(current) == 1:
            self._tokens.pop()
            return
        self._tokens[-1] = current[:-1]

    def expression(self) -> str:
        return " ".join(self._tokens)

    def value(self) -> Optional[int]:
        if not self._tokens or self._tokens[-1] in _OPERATORS:
            return None
        total = int(self._tokens[0])
        index = 1
        while index < len(self._tokens):
            operator = self._tokens[index]
            number = int(self._tokens[index + 1])
            if operator == "+":
                total += number
            else:
                total -= number
            index += 2
        if total <= 0:
            return None
        return total

    def _press_operator(self, operator: str) -> None:
        if not self._tokens or self._tokens[-1] in _OPERATORS:
            return
        self._tokens.append(operator)
