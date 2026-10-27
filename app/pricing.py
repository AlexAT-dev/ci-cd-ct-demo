"""Чиста бізнес-логіка розрахунку вартості замовлення (без HTTP, без БД).

Саме цей модуль покривається unit-тестами.
"""

from decimal import ROUND_HALF_UP, Decimal

BULK_THRESHOLD = 10  # від 10 шт. однієї позиції — знижка 5% на рядок
BULK_DISCOUNT = Decimal("0.05")

PROMO_CODES: dict[str, dict] = {
    "SAVE10": {"type": "percent", "value": Decimal("10")},
    "MINUS50": {"type": "fixed", "value": Decimal("50"), "min_subtotal": Decimal("200")},
}


class PricingError(ValueError):
    """Помилка бізнес-правил (некоректна кількість, невідомий промокод тощо)."""


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def line_total(unit_price: Decimal, quantity: int) -> Decimal:
    if quantity <= 0:
        raise PricingError("Quantity must be positive")
    if unit_price < 0:
        raise PricingError("Price cannot be negative")
    total = unit_price * quantity
    if quantity >= BULK_THRESHOLD:
        total -= total * BULK_DISCOUNT
    return money(total)


def promo_discount(subtotal: Decimal, code: str | None) -> Decimal:
    if not code:
        return Decimal("0.00")
    promo = PROMO_CODES.get(code.strip().upper())
    if promo is None:
        raise PricingError(f"Unknown promo code: {code}")
    if subtotal < promo.get("min_subtotal", Decimal("0")):
        raise PricingError(f"Promo code {code} requires subtotal >= {promo['min_subtotal']}")
    if promo["type"] == "percent":
        return money(subtotal * promo["value"] / 100)
    return money(min(promo["value"], subtotal))


def quote(lines: list[tuple[Decimal, int]], promo_code: str | None = None) -> dict[str, Decimal]:
    """lines — список (ціна за одиницю, кількість)."""
    if not lines:
        raise PricingError("Order must contain at least one item")
    subtotal = money(sum((line_total(price, qty) for price, qty in lines), Decimal("0")))
    discount = promo_discount(subtotal, promo_code)
    return {"subtotal": subtotal, "discount": discount, "total": money(subtotal - discount)}
