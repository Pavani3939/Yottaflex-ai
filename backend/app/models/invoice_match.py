"""
YottaPay AI – Invoice Match ORM Model
Table: invoice_matches

Stores the result of each three-way matching run.
A new record is created every time matching is re-run (immutable history).
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum,
    ForeignKey, JSON, Numeric, String, Text,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class MatchOverallStatus(str, enum.Enum):
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


class InvoiceMatch(Base):
    """
    Result record from the Three-Way Matching Engine.

    One new record per matching run — history is never overwritten.
    """

    __tablename__ = "invoice_matches"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id = Column(
        String(35),
        ForeignKey("invoices.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    po_id = Column(
        String(20),
        ForeignKey("purchase_orders.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    grn_id = Column(
        String(20),
        ForeignKey("goods_receipts.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    match_run_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    overall_status = Column(Enum(MatchOverallStatus), nullable=False)

    # --- Detailed check results (JSON blob) ---
    check_results = Column(JSON, nullable=True, comment="Detailed per-check outcome")

    # --- Individual check flags ---
    vendor_valid = Column(Boolean, nullable=False, default=False)
    po_exists = Column(Boolean, nullable=False, default=False)
    sku_matched = Column(Boolean, nullable=False, default=False)
    qty_matched = Column(Boolean, nullable=False, default=False)
    price_matched = Column(Boolean, nullable=False, default=False)
    tax_matched = Column(Boolean, nullable=False, default=False)
    arithmetic_valid = Column(Boolean, nullable=False, default=False)
    receipt_matched = Column(Boolean, nullable=False, default=False)
    is_duplicate = Column(Boolean, nullable=False, default=False)

    # --- Tolerances used during this run ---
    price_tolerance_pct = Column(Numeric(5, 2), default=2.00)
    qty_tolerance_pct = Column(Numeric(5, 2), default=0.00)

    matched_by = Column(String(100), nullable=False, default="system")
    notes = Column(Text, nullable=True)

    # --- Relationships ---
    invoice = relationship("Invoice", back_populates="matches")
    purchase_order = relationship("PurchaseOrder", back_populates="invoice_matches")
    goods_receipt = relationship("GoodsReceipt", back_populates="invoice_matches")

    def __repr__(self) -> str:
        return (
            f"<InvoiceMatch id={self.id} invoice_id={self.invoice_id} "
            f"status={self.overall_status}>"
        )
