"""
YottaPay AI – Arithmetic Utility Tests

Tests for rounding, line calculations, reconciliation, and variance functions.
"""
import sys
import os
import pytest
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils.arithmetic import (
    round_currency,
    calculate_line_subtotal,
    calculate_line_tax,
    calculate_line_total,
    reconcile_invoice_totals,
    price_variance_pct,
    qty_variance_pct,
)


class TestRoundCurrency:
    def test_basic(self):
        assert round_currency(10.555) == Decimal("10.56")
        assert round_currency(10.554) == Decimal("10.55")

    def test_integer(self):
        assert round_currency(100) == Decimal("100.00")

    def test_string_decimal(self):
        assert round_currency(Decimal("99.999")) == Decimal("100.00")

    def test_already_rounded(self):
        assert round_currency(10.50) == Decimal("10.50")


class TestCalculateLineSubtotal:
    def test_basic(self):
        result = calculate_line_subtotal(Decimal("10"), Decimal("25.50"))
        assert result == Decimal("255.00")

    def test_fractional(self):
        result = calculate_line_subtotal(Decimal("3"), Decimal("33.33"))
        assert result == Decimal("99.99")

    def test_zero_qty(self):
        result = calculate_line_subtotal(Decimal("0"), Decimal("100.00"))
        assert result == Decimal("0.00")


class TestCalculateLineTax:
    def test_basic(self):
        result = calculate_line_tax(Decimal("1000.00"), Decimal("8"))
        assert result == Decimal("80.00")

    def test_zero_rate(self):
        result = calculate_line_tax(Decimal("1000.00"), Decimal("0"))
        assert result == Decimal("0.00")


class TestCalculateLineTotal:
    def test_basic(self):
        result = calculate_line_total(Decimal("1000.00"), Decimal("80.00"))
        assert result == Decimal("1080.00")


class TestReconcileInvoiceTotals:
    def test_valid(self):
        result = reconcile_invoice_totals(
            stated_subtotal=Decimal("1000.00"),
            stated_tax=Decimal("80.00"),
            stated_total=Decimal("1080.00"),
            line_subtotals=[Decimal("500.00"), Decimal("500.00")],
            line_taxes=[Decimal("40.00"), Decimal("40.00")],
        )
        assert result["arithmetic_valid"] is True

    def test_invalid_subtotal(self):
        result = reconcile_invoice_totals(
            stated_subtotal=Decimal("999.00"),
            stated_tax=Decimal("80.00"),
            stated_total=Decimal("1079.00"),
            line_subtotals=[Decimal("500.00"), Decimal("500.00")],
            line_taxes=[Decimal("40.00"), Decimal("40.00")],
        )
        assert result["arithmetic_valid"] is False

    def test_within_tolerance(self):
        result = reconcile_invoice_totals(
            stated_subtotal=Decimal("1000.01"),
            stated_tax=Decimal("80.00"),
            stated_total=Decimal("1080.01"),
            line_subtotals=[Decimal("500.00"), Decimal("500.00")],
            line_taxes=[Decimal("40.00"), Decimal("40.00")],
            tolerance=Decimal("0.02"),
        )
        assert result["arithmetic_valid"] is True


class TestPriceVariance:
    def test_zero_variance(self):
        assert price_variance_pct(Decimal("100.00"), Decimal("100.00")) == Decimal("0.00")

    def test_positive_variance(self):
        result = price_variance_pct(Decimal("100.00"), Decimal("105.00"))
        assert result == Decimal("5.00")

    def test_zero_po_price(self):
        result = price_variance_pct(Decimal("0"), Decimal("50.00"))
        assert result == Decimal("100.00")


class TestQtyVariance:
    def test_zero_variance(self):
        assert qty_variance_pct(Decimal("100"), Decimal("100")) == Decimal("0.00")

    def test_over_delivery(self):
        result = qty_variance_pct(Decimal("100"), Decimal("110"))
        assert result == Decimal("10.00")

    def test_under_delivery(self):
        result = qty_variance_pct(Decimal("100"), Decimal("90"))
        assert result == Decimal("10.00")
