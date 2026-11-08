"""
YottaPay AI – Invoice Arithmetic Utilities

All financial calculations use Python's Decimal for precision.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List


TWO_PLACES = Decimal("0.01")


def round_currency(value: float | Decimal) -> Decimal:
    """Round to 2 decimal places using banker's rounding."""
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def round2(value: float | Decimal) -> Decimal:
    """Compatibility helper used by invoice and purchase order routers."""
    return round_currency(value)


def calculate_line_subtotal(quantity: Decimal, unit_price: Decimal) -> Decimal:
    """Calculate line subtotal: qty × unit_price."""
    return round_currency(quantity * unit_price)


def calculate_line_tax(subtotal: Decimal, tax_rate: Decimal) -> Decimal:
    """Calculate line tax: subtotal × tax_rate / 100."""
    return round_currency(subtotal * tax_rate / Decimal("100"))


def calculate_line_total(subtotal: Decimal, tax: Decimal) -> Decimal:
    """Calculate line total: subtotal + tax."""
    return round_currency(subtotal + tax)


def reconcile_invoice_totals(
    stated_subtotal: Decimal,
    stated_tax: Decimal,
    stated_total: Decimal,
    line_subtotals: List[Decimal],
    line_taxes: List[Decimal],
    tolerance: Decimal = Decimal("0.01"),
) -> dict:
    """
    Verify that invoice header totals match the sum of line totals.

    Returns:
        dict with keys: arithmetic_valid, subtotal_diff, tax_diff, total_diff
    """
    calc_subtotal = sum(line_subtotals, Decimal("0"))
    calc_tax = sum(line_taxes, Decimal("0"))
    calc_total = calc_subtotal + calc_tax

    subtotal_diff = abs(stated_subtotal - calc_subtotal)
    tax_diff = abs(stated_tax - calc_tax)
    total_diff = abs(stated_total - calc_total)

    return {
        "arithmetic_valid": (
            subtotal_diff <= tolerance
            and tax_diff <= tolerance
            and total_diff <= tolerance
        ),
        "calculated_subtotal": calc_subtotal,
        "calculated_tax": calc_tax,
        "calculated_total": calc_total,
        "subtotal_diff": subtotal_diff,
        "tax_diff": tax_diff,
        "total_diff": total_diff,
    }


def price_variance_pct(po_price: Decimal, invoice_price: Decimal) -> Decimal:
    """Calculate absolute percentage variance between PO price and invoice price."""
    if po_price == 0:
        return Decimal("100.00")
    return round_currency(abs(invoice_price - po_price) / po_price * Decimal("100"))


def qty_variance_pct(po_qty: Decimal, invoice_qty: Decimal) -> Decimal:
    """Calculate absolute percentage variance between PO qty and invoice qty."""
    if po_qty == 0:
        return Decimal("100.00")
    return round_currency(abs(invoice_qty - po_qty) / po_qty * Decimal("100"))
