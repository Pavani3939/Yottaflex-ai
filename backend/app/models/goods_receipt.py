"""
YottaPay AI – Goods Receipt ORM Model
Table: goods_receipts
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Date, DateTime, Enum, ForeignKey,
    String, Text,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class GRNStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    RECEIVED = "RECEIVED"
    PARTIALLY_ACCEPTED = "PARTIALLY_ACCEPTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class GoodsReceipt(Base):
    """
    Records goods received against a Purchase Order.

    ID format: GRN-2026-000001
    """

    __tablename__ = "goods_receipts"

    id = Column(String(20), primary_key=True, comment="GRN-2026-000001")
    po_id = Column(
        String(20),
        ForeignKey("purchase_orders.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    vendor_id = Column(
        String(12),
        ForeignKey("vendors.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    receipt_date = Column(Date, nullable=False)
    warehouse = Column(String(100), nullable=True)
    received_by = Column(String(100), nullable=False, default="warehouse_staff")
    status = Column(Enum(GRNStatus), nullable=False, default=GRNStatus.RECEIVED)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # --- Relationships ---
    purchase_order = relationship("PurchaseOrder", back_populates="goods_receipts")
    vendor = relationship("Vendor", back_populates="goods_receipts")
    lines = relationship(
        "GoodsReceiptLine",
        back_populates="goods_receipt",
        cascade="all, delete-orphan",
    )
    invoice_matches = relationship("InvoiceMatch", back_populates="goods_receipt")

    def __repr__(self) -> str:
        return f"<GoodsReceipt id={self.id} po_id={self.po_id} status={self.status}>"
