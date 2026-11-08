"""
YottaPay AI – Approval ORM Model
Table: approvals

One approval record per invoice (1:1 relationship).
History of all approval actions is kept in approval_history.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger, Column, DateTime, Enum,
    ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ON_HOLD = "ON_HOLD"
    CANCELLED = "CANCELLED"


class Approval(Base):
    """
    Approval workflow record for an invoice.

    Business rules:
    - Only created for invoices with no blocking open exceptions.
    - Approval amount levels determine the required approver role.
    - A blocked invoice must never enter this table.
    """

    __tablename__ = "approvals"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id = Column(
        String(35),
        ForeignKey("invoices.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        unique=True,                    # 1:1 with invoice
        index=True,
    )
    status = Column(
        Enum(ApprovalStatus),
        nullable=False,
        default=ApprovalStatus.PENDING,
        index=True,
    )
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    requested_by = Column(String(100), nullable=False, default="system")
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    decision_notes = Column(Text, nullable=True)
    approval_level = Column(Integer, nullable=False, default=1)
    next_approver = Column(String(100), nullable=True)

    # --- Relationships ---
    invoice = relationship("Invoice", back_populates="approval")
    history = relationship(
        "ApprovalHistory",
        back_populates="approval",
        cascade="all, delete-orphan",
        order_by="ApprovalHistory.created_at",
    )

    def __repr__(self) -> str:
        return (
            f"<Approval id={self.id} invoice_id={self.invoice_id} "
            f"status={self.status}>"
        )
