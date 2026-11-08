"""
YottaPay AI – Invoice Exception ORM Model
Table: invoice_exceptions
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger, Column, DateTime, Enum,
    ForeignKey, String, Text,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class ExceptionType(str, enum.Enum):
    PRICE_VARIANCE = "PRICE_VARIANCE"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    TAX_MISMATCH = "TAX_MISMATCH"
    MISSING_RECEIPT = "MISSING_RECEIPT"
    DUPLICATE = "DUPLICATE"
    VENDOR_ERROR = "VENDOR_ERROR"
    TOTAL_MISMATCH = "TOTAL_MISMATCH"
    DATE_ERROR = "DATE_ERROR"
    ARITHMETIC_ERROR = "ARITHMETIC_ERROR"
    SKU_MISMATCH = "SKU_MISMATCH"
    OTHER = "OTHER"


class ExceptionSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExceptionStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    WAIVED = "WAIVED"
    ESCALATED = "ESCALATED"


# Exceptions that BLOCK approval and payment when OPEN
BLOCKING_EXCEPTION_TYPES = {
    ExceptionType.DUPLICATE,
    ExceptionType.VENDOR_ERROR,
    ExceptionType.DATE_ERROR,
    ExceptionType.TOTAL_MISMATCH,
    ExceptionType.ARITHMETIC_ERROR,
    ExceptionType.SKU_MISMATCH,
    ExceptionType.MISSING_RECEIPT,
}

# HIGH+ severity variance exceptions also block
BLOCKING_SEVERITIES = {ExceptionSeverity.HIGH, ExceptionSeverity.CRITICAL}


class InvoiceException(Base):
    """
    An anomaly or discrepancy detected during invoice matching.

    Multiple exceptions can exist per invoice.
    Blocking exceptions prevent approval and payment.
    """

    __tablename__ = "invoice_exceptions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id = Column(
        String(35),
        ForeignKey("invoices.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exception_type = Column(Enum(ExceptionType), nullable=False, index=True)
    severity = Column(
        Enum(ExceptionSeverity),
        nullable=False,
        default=ExceptionSeverity.MEDIUM,
        index=True,
    )
    status = Column(
        Enum(ExceptionStatus),
        nullable=False,
        default=ExceptionStatus.OPEN,
        index=True,
    )
    description = Column(Text, nullable=False)
    expected_value = Column(String(255), nullable=True, comment="What was expected")
    actual_value = Column(String(255), nullable=True, comment="What was found")
    po_line_id = Column(String(30), nullable=True, comment="Relevant PO line ID")
    grn_line_id = Column(String(40), nullable=True, comment="Relevant GRN line ID")
    recommended_action = Column(Text, nullable=True)
    assigned_to = Column(String(100), nullable=True, comment="Analyst username")
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # --- Relationships ---
    invoice = relationship("Invoice", back_populates="exceptions")

    @property
    def is_blocking(self) -> bool:
        """Return True if this open exception blocks approval/payment."""
        if self.status not in (ExceptionStatus.OPEN, ExceptionStatus.IN_REVIEW):
            return False
        if self.exception_type in BLOCKING_EXCEPTION_TYPES:
            return True
        if self.severity in BLOCKING_SEVERITIES:
            return True
        return False

    def __repr__(self) -> str:
        return (
            f"<InvoiceException id={self.id} invoice_id={self.invoice_id} "
            f"type={self.exception_type} severity={self.severity} status={self.status}>"
        )
