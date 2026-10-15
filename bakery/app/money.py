def format_cop(amount: int) -> str:
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise TypeError("El valor debe ser un entero.")
    digits = f"{amount:,}".replace(",", ".")
    return f"$ {digits}"
