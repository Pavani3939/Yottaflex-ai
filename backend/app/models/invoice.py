"""
YottaPay AI – Invoice ORM Model
Table: invoices

This is the central entity of the system.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, ForeignKey,
    Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_EXTRACTION = "PENDING_EXTRACTION"
    EXTRACTED = "EXTRACTED"
    PENDING_MATCH = "PENDING_MATCH"
    MATCHING = "MATCHING"
    MATCHED = "MATCHED"
    EXCEPTION = "EXCEPTION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAYMENT_READY = "PAYMENT_READY"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class MatchingStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    MATCHED = "MATCHED"
    PRICE_VARIANCE = "PRICE_VARIANCE"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    TAX_MISMATCH = "TAX_MISMATCH"
    MISSING_RECEIPT = "MISSING_RECEIPT"
    DUPLICATE = "DUPLICATE"
    VENDOR_ERROR = "VENDOR_ERROR"
    TOTAL_MISMATCH = "TOTAL_MISMATCH"
    DATE_ERROR = "DATE_ERROR"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    FAILED = "FAILED"


class InvoiceSource(str, enum.Enum):
    UPLOAD_PDF = "UPLOAD_PDF"
    UPLOAD_IMAGE = "UPLOAD_IMAGE"
    MANUAL = "MANUAL"
    API = "API"


class Invoice(Base):
    """
    Central entity representing a vendor invoice.

    ID format: INV-{vendor_code}-{YEAR}-{6-digit seq}
    Example  : INV-VND00001-2026-000001
    """

    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", "vendor_id", name="uq_invoice_number_vendor"),
    )

    id = Column(String(35), primary_key=True)
    invoice_number = Column(
        String(100),
        nullable=False,
        comment="Vendor's own invoice reference number",
    )
    vendor_id = Column(
        String(12),
        ForeignKey("vendors.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    po_id = Column(
        String(20),
        ForeignKey("purchase_orders.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # --- Dates ---
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)

    # --- Financials (as stated on invoice) ---
    currency = Column(String(3), nullable=False, default="INR")
    subtotal = Column(Numeric(15, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=0)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)

    # --- Financials (calculated from invoice lines for verification) ---
    calculated_subtotal = Column(Numeric(15, 2), nullable=True)
    calculated_tax = Column(Numeric(15, 2), nullable=True)
    calculated_total = Column(Numeric(15, 2), nullable=True)

    # --- Lifecycle State ---
    status = Column(
        Enum(InvoiceStatus),
        nullable=False,
        default=InvoiceStatus.DRAFT,
        index=True,
    )
    matching_status = Column(
        Enum(MatchingStatus),
        nullable=False,
        default=MatchingStatus.NOT_STARTED,
        index=True,
    )

    # --- Source & Extraction ---
    source = Column(Enum(InvoiceSource), nullable=False, default=InvoiceSource.MANUAL)
    extraction_confidence = Column(
        Numeric(5, 2),
        nullable=True,
        comment="AI extraction confidence 0–100",
    )

    # --- Duplicate Detection ---
    is_duplicate = Column(Boolean, nullable=False, default=False)
    duplicate_of = Column(
        String(35),
        ForeignKey("invoices.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )

    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=False, default="system")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # --- Relationships ---
    vendor = relationship("Vendor", back_populates="invoices")
    purchase_order = relationship("PurchaseOrder", back_populates="invoices")
    lines = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    matches = relationship(
        "InvoiceMatch",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    exceptions = relationship(
        "InvoiceException",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    approval = relationship(
        "Approval",
        back_populates="invoice",
        uselist=False,
        cascade="all, delete-orphan",
    )
    payment = relationship(
        "Payment",
        back_populates="invoice",
        uselist=False,
        cascade="all, delete-orphan",
    )
    documents = relationship(
        "InvoiceDocument",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    # Self-referential: invoices that are duplicates of this invoice
    duplicate_invoices = relationship(
        "Invoice",
        foreign_keys=[duplicate_of],
        backref="original_invoice",
        remote_side="Invoice.id",
    )

    def __repr__(self) -> str:
        return (
            f"<Invoice id={self.id} vendor_id={self.vendor_id} "
            f"status={self.status} matching={self.matching_status}>"
        )
