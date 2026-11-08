"""
YottaPay AI – Goods Receipt Line ORM Model
Table: goods_receipt_lines
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Date, DateTime, Enum, ForeignKey,
    Integer, Numeric, String, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class GRNLineStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_ACCEPTED = "PARTIALLY_ACCEPTED"
    REJECTED = "REJECTED"


class GoodsReceiptLine(Base):
    """
    Individual item line within a Goods Receipt.

    ID format: GRNL-GRN-2026-000001-01
    """

    __tablename__ = "goods_receipt_lines"
    __table_args__ = (
        UniqueConstraint("grn_id", "line_number", name="uq_grn_line"),
    )

    id = Column(String(40), primary_key=True, comment="GRNL-{grn_id}-{line_no:02d}")
    grn_id = Column(
        String(20),
        ForeignKey("goods_receipts.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    po_line_id = Column(
        String(30),
        ForeignKey("purchase_order_lines.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    line_number = Column(Integer, nullable=False)
    sku = Column(String(50), nullable=False)
    description = Column(String(500), nullable=True)
    uom = Column(String(20), nullable=False, default="EA")
    received_qty = Column(Numeric(12, 3), nullable=False)
    accepted_qty = Column(Numeric(12, 3), nullable=False)
    rejected_qty = Column(Numeric(12, 3), nullable=False, default=0)
    unit_price = Column(Numeric(12, 2), nullable=False)
    batch_number = Column(String(100), nullable=True)
    expiry_date = Column(Date, nullable=True)
    status = Column(Enum(GRNLineStatus), nullable=False, default=GRNLineStatus.ACCEPTED)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # --- Relationships ---
    goods_receipt = relationship("GoodsReceipt", back_populates="lines")
    po_line = relationship("PurchaseOrderLine", back_populates="goods_receipt_lines")

    def __repr__(self) -> str:
        return (
            f"<GRNLine id={self.id} sku={self.sku!r} "
            f"accepted_qty={self.accepted_qty}>"
        )
