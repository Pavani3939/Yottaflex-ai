"""
YottaPay AI – Invoice Line ORM Model
Table: invoice_lines
"""
from datetime import datetime

from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer,
    Numeric, String, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class InvoiceLine(Base):
    """
    Individual line item on an Invoice.

    ID format: INVL-{invoice_id}-{line_no:02d}
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        UniqueConstraint("invoice_id", "line_number", name="uq_invline"),
    )

    id = Column(String(50), primary_key=True)
    invoice_id = Column(
        String(35),
        ForeignKey("invoices.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number = Column(Integer, nullable=False)
    po_line_id = Column(
        String(30),
        ForeignKey("purchase_order_lines.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sku = Column(String(50), nullable=True)
    description = Column(String(500), nullable=False)
    uom = Column(String(20), nullable=False, default="EA")
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_code = Column(String(20), nullable=False, default="GST18")
    tax_rate = Column(Numeric(5, 2), nullable=False, default=18.00)
    line_subtotal = Column(Numeric(15, 2), nullable=False, comment="qty × unit_price")
    tax_amount = Column(Numeric(15, 2), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False, comment="subtotal + tax")

    # --- Relationships ---
    invoice = relationship("Invoice", back_populates="lines")
    po_line = relationship("PurchaseOrderLine", back_populates="invoice_lines")

    def __repr__(self) -> str:
        return (
            f"<InvoiceLine id={self.id} sku={self.sku!r} "
            f"qty={self.quantity} total={self.line_total}>"
        )
