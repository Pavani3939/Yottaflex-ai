"""
YottaPay AI – Purchase Order Line ORM Model
Table: purchase_order_lines
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Enum, ForeignKey,
    Integer, Numeric, String, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class POLineStatus(str, enum.Enum):
    OPEN = "OPEN"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    FULLY_RECEIVED = "FULLY_RECEIVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class PurchaseOrderLine(Base):
    """
    Individual line item within a Purchase Order.

    ID format: POLINE-PO-2026-000001-01
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        UniqueConstraint("po_id", "line_number", name="uq_po_line"),
    )

    id = Column(String(30), primary_key=True, comment="POLINE-{po_id}-{line_no:02d}")
    po_id = Column(
        String(20),
        ForeignKey("purchase_orders.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    line_number = Column(Integer, nullable=False, comment="Sequence within PO")
    sku = Column(String(50), nullable=False, comment="Stock Keeping Unit")
    description = Column(String(500), nullable=False)
    uom = Column(String(20), nullable=False, default="EA", comment="Unit of Measure")
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_code = Column(String(20), nullable=False, default="GST18")
    tax_rate = Column(Numeric(5, 2), nullable=False, default=18.00)
    line_subtotal = Column(Numeric(15, 2), nullable=False, comment="qty × unit_price")
    tax_amount = Column(Numeric(15, 2), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False, comment="subtotal + tax")
    received_qty = Column(Numeric(12, 3), nullable=False, default=0, comment="Cumulative received")
    status = Column(Enum(POLineStatus), nullable=False, default=POLineStatus.OPEN)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # --- Relationships ---
    purchase_order = relationship("PurchaseOrder", back_populates="lines")
    goods_receipt_lines = relationship("GoodsReceiptLine", back_populates="po_line")
    invoice_lines = relationship("InvoiceLine", back_populates="po_line")

    def __repr__(self) -> str:
        return f"<POLine id={self.id} sku={self.sku!r} qty={self.quantity}>"
