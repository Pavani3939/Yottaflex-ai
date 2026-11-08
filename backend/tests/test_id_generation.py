"""
YottaPay AI – ID Generation Tests

Tests all ID format functions in app.utils.id_generator.
"""
import sys
import os
import re
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils.id_generator import (
    vendor_id,
    vendor_code,
    po_id,
    po_line_id,
    grn_id,
    grn_line_id,
    invoice_id,
    invoice_line_id,
    audit_event_id,
)


class TestVendorIdGeneration:
    def test_format(self):
        assert vendor_id(1) == "VND-00001"

    def test_increments(self):
        assert vendor_id(42) == "VND-00042"
        assert vendor_id(100) == "VND-00100"

    def test_padding(self):
        assert vendor_id(99999) == "VND-99999"


class TestVendorCode:
    def test_format(self):
        assert vendor_code(1) == "VND00001"

    def test_increments(self):
        assert vendor_code(42) == "VND00042"


class TestPOIdGeneration:
    def test_format(self):
        assert po_id(2026, 1) == "PO-2026-000001"

    def test_pattern(self):
        result = po_id(2026, 42)
        assert re.match(r"^PO-\d{4}-\d{6}$", result)


class TestPOLineId:
    def test_format(self):
        result = po_line_id("PO-2026-000001", 1)
        assert result == "POLINE-PO-2026-000001-01"


class TestGRNIdGeneration:
    def test_format(self):
        assert grn_id(2026, 1) == "GRN-2026-000001"

    def test_pattern(self):
        result = grn_id(2026, 100)
        assert re.match(r"^GRN-\d{4}-\d{6}$", result)


class TestGRNLineId:
    def test_format(self):
        result = grn_line_id("GRN-2026-000001", 1)
        assert result == "GRNL-GRN-2026-000001-01"


class TestInvoiceIdGeneration:
    def test_format(self):
        result = invoice_id("VND00001", 2026, 1)
        assert result == "INV-VND00001-2026-000001"

    def test_pattern(self):
        result = invoice_id("VND00042", 2026, 999)
        assert re.match(r"^INV-VND\d{5}-\d{4}-\d{6}$", result)


class TestInvoiceLineIdGeneration:
    def test_format(self):
        result = invoice_line_id("INV-VND00001-2026-000001", 1)
        assert result == "INVL-INV-VND00001-2026-000001-01"

    def test_pattern(self):
        result = invoice_line_id("INV-VND00001-2026-000001", 5)
        assert "INVL-" in result


class TestAuditEventIdGeneration:
    def test_format(self):
        eid = audit_event_id()
        assert eid.startswith("EVT-")

    def test_unique(self):
        ids = {audit_event_id() for _ in range(100)}
        assert len(ids) == 100, "Event IDs should be unique"
