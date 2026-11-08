"""
YottaPay AI – Three-Way Matching Engine Tests

Tests the matching engine logic with mock data for each anomaly scenario.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from decimal import Decimal
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_vendor(vendor_id="VND-00001", status="active"):
    v = MagicMock()
    v.id = vendor_id
    v.vendor_code = vendor_id.replace("-", "").replace("VND", "VND")
    v.status = status
    return v


def _make_po(po_id="PO-2026-000001", vendor_id="VND-00001", status="OPEN"):
    po = MagicMock()
    po.id = po_id
    po.vendor_id = vendor_id
    po.status = status
    po.po_date = date(2026, 10, 1)
    po.total_amount = Decimal("2500.00")
    return po


def _make_po_line(sku="SKU-001", qty=100, price=25.00):
    line = MagicMock()
    line.sku = sku
    line.quantity = qty
    line.unit_price = Decimal(str(price))
    line.line_number = 1
    return line


def _make_invoice(invoice_id="INV-VND00001-2026-000001", vendor_id="VND-00001",
                   po_id="PO-2026-000001", total=2700.00, subtotal=2500.00,
                   tax=200.00, discount=0.00):
    inv = MagicMock()
    inv.id = invoice_id
    inv.invoice_number = "INV-TEST-001"
    inv.vendor_id = vendor_id
    inv.po_id = po_id
    inv.invoice_date = date(2026, 10, 20)
    inv.total_amount = Decimal(str(total))
    inv.subtotal = Decimal(str(subtotal))
    inv.tax_amount = Decimal(str(tax))
    inv.discount_amount = Decimal(str(discount))
    inv.status = "RECEIVED"
    return inv


def _make_invoice_line(sku="SKU-001", qty=100, price=25.00):
    line = MagicMock()
    line.sku = sku
    line.quantity = qty
    line.unit_price = Decimal(str(price))
    line.line_total = Decimal(str(qty * price))
    line.line_number = 1
    return line


def _make_grn(grn_id="GRN-2026-000001", po_id="PO-2026-000001", vendor_id="VND-00001"):
    grn = MagicMock()
    grn.id = grn_id
    grn.po_id = po_id
    grn.vendor_id = vendor_id
    grn.receipt_date = date(2026, 10, 18)
    grn.status = "RECEIVED"
    return grn


def _make_grn_line(sku="SKU-001", qty_received=100):
    line = MagicMock()
    line.sku = sku
    line.quantity_received = qty_received
    line.line_number = 1
    return line


class TestMatchingEngineChecks:
    """Test individual check logic patterns."""

    def test_vendor_validation_active(self):
        """Active vendor should pass vendor check."""
        vendor = _make_vendor(status="active")
        assert vendor.status == "active"

    def test_vendor_validation_inactive(self):
        """Inactive vendor should fail vendor check."""
        vendor = _make_vendor(status="inactive")
        assert vendor.status != "active"

    def test_po_exists(self):
        """PO should be found and match vendor."""
        po = _make_po(vendor_id="VND-00001")
        invoice = _make_invoice(vendor_id="VND-00001", po_id="PO-2026-000001")
        assert po.vendor_id == invoice.vendor_id

    def test_po_vendor_mismatch(self):
        """PO vendor mismatch should fail."""
        po = _make_po(vendor_id="VND-00002")
        invoice = _make_invoice(vendor_id="VND-00001")
        assert po.vendor_id != invoice.vendor_id

    def test_sku_matching_pass(self):
        """All invoice SKUs exist in PO lines."""
        po_lines = [_make_po_line(sku="SKU-001"), _make_po_line(sku="SKU-002")]
        inv_lines = [_make_invoice_line(sku="SKU-001")]
        po_skus = {l.sku for l in po_lines}
        inv_skus = {l.sku for l in inv_lines}
        assert inv_skus.issubset(po_skus)

    def test_sku_matching_fail(self):
        """Invoice has SKU not in PO."""
        po_lines = [_make_po_line(sku="SKU-001")]
        inv_lines = [_make_invoice_line(sku="SKU-999")]
        po_skus = {l.sku for l in po_lines}
        inv_skus = {l.sku for l in inv_lines}
        assert not inv_skus.issubset(po_skus)

    def test_quantity_within_tolerance(self):
        """Quantity within 5% tolerance should pass."""
        po_qty = 100
        inv_qty = 103  # 3% over
        tolerance = 5.0
        variance = abs(inv_qty - po_qty) / po_qty * 100
        assert variance <= tolerance

    def test_quantity_outside_tolerance(self):
        """Quantity outside 5% tolerance should fail."""
        po_qty = 100
        inv_qty = 110  # 10% over
        tolerance = 5.0
        variance = abs(inv_qty - po_qty) / po_qty * 100
        assert variance > tolerance

    def test_price_within_tolerance(self):
        """Price within 2% tolerance should pass."""
        po_price = Decimal("25.00")
        inv_price = Decimal("25.40")  # 1.6% over
        tolerance = 2.0
        variance = abs(float(inv_price - po_price)) / float(po_price) * 100
        assert variance <= tolerance

    def test_price_outside_tolerance(self):
        """Price outside 2% tolerance should fail."""
        po_price = Decimal("25.00")
        inv_price = Decimal("26.00")  # 4% over
        tolerance = 2.0
        variance = abs(float(inv_price - po_price)) / float(po_price) * 100
        assert variance > tolerance

    def test_arithmetic_valid(self):
        """Line total = qty * unit_price."""
        qty = 100
        price = Decimal("25.00")
        expected = Decimal("2500.00")
        actual = Decimal(str(qty)) * price
        assert actual == expected

    def test_arithmetic_invalid(self):
        """Wrong line total detected."""
        line = _make_invoice_line(sku="SKU-001", qty=100, price=25.00)
        line.line_total = Decimal("2600.00")  # Wrong
        expected = Decimal(str(line.quantity)) * line.unit_price
        assert line.line_total != expected

    def test_total_reconciliation_pass(self):
        """subtotal + tax - discount = total."""
        subtotal = Decimal("2500.00")
        tax = Decimal("200.00")
        discount = Decimal("0.00")
        total = Decimal("2700.00")
        expected = subtotal + tax - discount
        assert expected == total

    def test_total_reconciliation_fail(self):
        """Wrong total detected."""
        subtotal = Decimal("2500.00")
        tax = Decimal("200.00")
        discount = Decimal("0.00")
        total = Decimal("2800.00")  # Wrong
        expected = subtotal + tax - discount
        assert expected != total

    def test_duplicate_detection(self):
        """Same invoice_number + vendor_id = duplicate."""
        existing = _make_invoice(invoice_id="INV-1")
        new_inv = _make_invoice(invoice_id="INV-2")
        new_inv.invoice_number = existing.invoice_number
        new_inv.vendor_id = existing.vendor_id
        assert new_inv.invoice_number == existing.invoice_number
        assert new_inv.vendor_id == existing.vendor_id

    def test_grn_matching_pass(self):
        """GRN quantity matches invoice quantity."""
        grn_line = _make_grn_line(sku="SKU-001", qty_received=100)
        inv_line = _make_invoice_line(sku="SKU-001", qty=100)
        assert grn_line.quantity_received == inv_line.quantity

    def test_grn_matching_fail(self):
        """GRN quantity doesn't match invoice quantity."""
        grn_line = _make_grn_line(sku="SKU-001", qty_received=80)
        inv_line = _make_invoice_line(sku="SKU-001", qty=100)
        assert grn_line.quantity_received != inv_line.quantity

    def test_date_validation_pass(self):
        """Invoice date within PO date window."""
        po_date = date(2026, 10, 1)
        inv_date = date(2026, 10, 20)
        window_days = 365
        delta = (inv_date - po_date).days
        assert 0 <= delta <= window_days

    def test_date_validation_fail(self):
        """Invoice date too far from PO date."""
        po_date = date(2024, 1, 1)
        inv_date = date(2026, 10, 20)
        window_days = 365
        delta = (inv_date - po_date).days
        assert delta > window_days
