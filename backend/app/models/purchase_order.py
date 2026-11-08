"""
YottaPay AI – Purchase Order ORM Model
Table: purchase_orders
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Date, DateTime, Enum, ForeignKey,
    Numeric, String, Text,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class POStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    FULLY_RECEIVED = "FULLY_RECEIVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class PurchaseOrder(Base):
    """
    Represents a Purchase Order raised against a Vendor.

    ID format: PO-2026-000001
    """

    __tablename__ = "purchase_orders"

    id = Column(String(20), primary_key=True, comment="PO-2026-000001")
    vendor_id = Column(
        String(12),
        ForeignKey("vendors.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_date = Column(Date, nullable=False)
    delivery_date = Column(Date, nullable=True)
    status = Column(Enum(POStatus), nullable=False, default=POStatus.OPEN)
    currency = Column(String(3), nullable=False, default="INR")
    subtotal = Column(Numeric(15, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=0)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)
    department = Column(String(100), nullable=True)
    created_by = Column(String(100), nullable=False, default="system")
    approved_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # --- Relationships ---
    vendor = relationship("Vendor", back_populates="purchase_orders")
    lines = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    goods_receipts = relationship("GoodsReceipt", back_populates="purchase_order")
    invoices = relationship("Invoice", back_populates="purchase_order")
    invoice_matches = relationship("InvoiceMatch", back_populates="purchase_order")

    def __repr__(self) -> str:
        return f"<PurchaseOrder id={self.id} vendor_id={self.vendor_id} status={self.status}>"
