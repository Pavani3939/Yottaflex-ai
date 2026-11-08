"""
YottaPay AI – Model Instantiation Tests

Verifies all 14 ORM models can be instantiated without errors.
"""
import sys
import os
import pytest
from datetime import datetime, date
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.vendor import Vendor
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_order_line import PurchaseOrderLine
from app.models.goods_receipt import GoodsReceipt
from app.models.goods_receipt_line import GoodsReceiptLine
from app.models.invoice import Invoice
from app.models.invoice_line import InvoiceLine
from app.models.invoice_match import InvoiceMatch
from app.models.invoice_exception import InvoiceException
from app.models.invoice_document import InvoiceDocument
from app.models.approval import Approval
from app.models.approval_history import ApprovalHistory
from app.models.payment import Payment
from app.models.audit_event import AuditEvent


class TestVendorModel:
    def test_instantiate(self):
        v = Vendor(
            id="VND-00001",
            code="VND00001",
            name="Test Vendor",
            email="test@vendor.com",
            status="ACTIVE",
        )
        assert v.id == "VND-00001"
        assert v.name == "Test Vendor"
        assert v.status == "ACTIVE"


class TestPurchaseOrderModel:
    def test_instantiate(self):
        po = PurchaseOrder(
            id="PO-2026-000001",
            vendor_id="VND-00001",
            order_date=date(2026, 10, 15),
            status="OPEN",
            currency="USD",
            total_amount=Decimal("2500.00"),
        )
        assert po.id == "PO-2026-000001"
        assert po.currency == "USD"


class TestPurchaseOrderLineModel:
    def test_instantiate(self):
        line = PurchaseOrderLine(
            id="POL-2026-000001-01",
            po_id="PO-2026-000001",
            line_number=1,
            sku="SKU-001",
            quantity=100,
            unit_price=Decimal("25.00"),
        )
        assert line.sku == "SKU-001"
        assert line.quantity == 100


class TestGoodsReceiptModel:
    def test_instantiate(self):
        gr = GoodsReceipt(
            id="GRN-2026-000001",
            po_id="PO-2026-000001",
            vendor_id="VND-00001",
            receipt_date=date(2026, 10, 20),
            status="RECEIVED",
        )
        assert gr.status == "RECEIVED"


class TestGoodsReceiptLineModel:
    def test_instantiate(self):
        grl = GoodsReceiptLine(
            id="GRNL-2026-000001-01",
            grn_id="GRN-2026-000001",
            po_line_id="POL-2026-000001-01",
            line_number=1,
            sku="SKU-001",
            received_qty=Decimal("100"),
            accepted_qty=Decimal("100"),
            unit_price=Decimal("25.00"),
        )
        assert grl.received_qty == Decimal("100")


class TestInvoiceModel:
    def test_instantiate(self):
        inv = Invoice(
            id="INV-VND00001-2026-000001",
            invoice_number="INV-TEST-001",
            vendor_id="VND-00001",
            po_id="PO-2026-000001",
            invoice_date=date(2026, 10, 20),
            total_amount=Decimal("2700.00"),
            status="RECEIVED",
        )
        assert inv.total_amount == Decimal("2700.00")


class TestInvoiceLineModel:
    def test_instantiate(self):
        il = InvoiceLine(
            id="INVL-VND00001-2026-000001-01",
            invoice_id="INV-VND00001-2026-000001",
            line_number=1,
            sku="SKU-001",
            quantity=100,
            unit_price=Decimal("25.00"),
            line_total=Decimal("2500.00"),
        )
        assert il.line_total == Decimal("2500.00")


class TestInvoiceMatchModel:
    def test_instantiate(self):
        m = InvoiceMatch(
            id=1,
            invoice_id="INV-VND00001-2026-000001",
            po_id="PO-2026-000001",
            overall_status="FULL_MATCH",
            vendor_valid=True,
            po_exists=True,
        )
        assert m.overall_status == "FULL_MATCH"
        assert m.vendor_valid is True


class TestInvoiceExceptionModel:
    def test_instantiate(self):
        ex = InvoiceException(
            id=1,
            invoice_id="INV-VND00001-2026-000001",
            exception_type="PRICE_MISMATCH",
            severity="HIGH",
            status="OPEN",
        )
        assert ex.exception_type == "PRICE_MISMATCH"


class TestInvoiceDocumentModel:
    def test_instantiate(self):
        doc = InvoiceDocument(
            id=1,
            invoice_id="INV-VND00001-2026-000001",
            file_name="invoice.pdf",
            file_path="/uploads/invoice.pdf",
            file_type="PDF",
            file_size_bytes=1024,
            extraction_method="PYMUPDF",
        )
        assert doc.file_name == "invoice.pdf"


class TestApprovalModel:
    def test_instantiate(self):
        a = Approval(
            id=1,
            invoice_id="INV-VND00001-2026-000001",
            status="PENDING",
            approval_level=1,
            requested_by="admin",
        )
        assert a.status == "PENDING"


class TestApprovalHistoryModel:
    def test_instantiate(self):
        ah = ApprovalHistory(
            id=1,
            approval_id=1,
            action="APPROVED",
            actor="admin",
        )
        assert ah.action == "APPROVED"


class TestPaymentModel:
    def test_instantiate(self):
        p = Payment(
            id=1,
            invoice_id="INV-VND00001-2026-000001",
            vendor_id="VND-00001",
            amount=Decimal("2700.00"),
            status="NOT_READY",
        )
        assert p.status == "NOT_READY"


class TestAuditEventModel:
    def test_instantiate(self):
        ae = AuditEvent(
            id=1,
            event_id="EVT-abc123",
            entity_type="INVOICE",
            entity_id="INV-VND00001-2026-000001",
            event_type="CREATED",
            actor="admin",
        )
        assert ae.entity_type == "INVOICE"
        assert ae.event_type == "CREATED"
