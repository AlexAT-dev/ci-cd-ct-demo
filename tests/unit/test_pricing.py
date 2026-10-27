"""Unit-тести: перевіряють чисту логіку pricing.py ізольовано, без HTTP."""

from decimal import Decimal

import pytest

from app import pricing

D = Decimal


class TestLineTotal:
    def test_regular_quantity(self):
        assert pricing.line_total(D("19.99"), 3) == D("59.97")

    def test_bulk_discount_applied_from_threshold(self):
        # 10 * 10.00 = 100.00, мінус 5% = 95.00
        assert pricing.line_total(D("10.00"), 10) == D("95.00")

    def test_no_bulk_discount_below_threshold(self):
        assert pricing.line_total(D("10.00"), 9) == D("90.00")

    @pytest.mark.parametrize("qty", [0, -1])
    def test_non_positive_quantity_rejected(self, qty):
        with pytest.raises(pricing.PricingError):
            pricing.line_total(D("1.00"), qty)

    def test_negative_price_rejected(self):
        with pytest.raises(pricing.PricingError):
            pricing.line_total(D("-1.00"), 1)


class TestPromoDiscount:
    def test_no_code_means_no_discount(self):
        assert pricing.promo_discount(D("100.00"), None) == D("0.00")

    def test_percent_code(self):
        assert pricing.promo_discount(D("123.45"), "SAVE10") == D("12.35")

    def test_code_is_case_insensitive(self):
        assert pricing.promo_discount(D("100.00"), " save10 ") == D("10.00")

    def test_fixed_code_above_minimum(self):
        assert pricing.promo_discount(D("250.00"), "MINUS50") == D("50.00")

    def test_fixed_code_below_minimum_rejected(self):
        with pytest.raises(pricing.PricingError, match="requires subtotal"):
            pricing.promo_discount(D("199.99"), "MINUS50")

    def test_unknown_code_rejected(self):
        with pytest.raises(pricing.PricingError, match="Unknown promo code"):
            pricing.promo_discount(D("100.00"), "FREE")


class TestQuote:
    def test_full_quote(self):
        result = pricing.quote([(D("45.00"), 2), (D("10.00"), 10)], "SAVE10")
        assert result == {"subtotal": D("185.00"), "discount": D("18.50"), "total": D("166.50")}

    def test_empty_order_rejected(self):
        with pytest.raises(pricing.PricingError):
            pricing.quote([])
