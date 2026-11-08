"""
YottaPay AI – Payment ORM Model
Table: payments

One payment record per invoice (1:1 relationship).
Simulated payment processing — no real banking integration.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger, Column, Date, DateTime, Enum,
    ForeignKey, Numeric, String, Text,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class PaymentStatus(str, enum.Enum):
    NOT_READY = "NOT_READY"
    READY_FOR_PAYMENT = "READY_FOR_PAYMENT"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    REVERSED = "REVERSED"


class PaymentMethod(str, enum.Enum):
    BANK_TRANSFER = "BANK_TRANSFER"
    CHEQUE = "CHEQUE"
    UPI = "UPI"
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"


class Payment(Base):
    """
    Payment record for an approved invoice.

    Business rules:
    - Only created after invoice reaches APPROVED status.
    - No blocked invoice may be READY_FOR_PAYMENT or beyond.
    - Processing is simulated — no real gateway integration.
    """

    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id = Column(
        String(35),
        ForeignKey("invoices.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        unique=True,                    # 1:1 with invoice
        index=True,
    )
    vendor_id = Column(
        String(12),
        ForeignKey("vendors.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status = Column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.NOT_READY,
        index=True,
    )
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    payment_method = Column(
        Enum(PaymentMethod),
        nullable=True,
        default=PaymentMethod.NEFT,
    )
    payment_reference = Column(String(100), nullable=True, comment="Bank / UPI reference")
    scheduled_date = Column(Date, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(String(100), nullable=True)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # --- Relationships ---
    invoice = relationship("Invoice", back_populates="payment")
    vendor = relationship("Vendor", back_populates="payments")

    def __repr__(self) -> str:
        return (
            f"<Payment id={self.id} invoice_id={self.invoice_id} "
            f"amount={self.amount} status={self.status}>"
        )
