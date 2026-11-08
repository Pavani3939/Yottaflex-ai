"""
YottaPay AI – Approval History ORM Model
Table: approval_history

Immutable audit trail for every action taken on an approval record.
Records are never updated or deleted.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger, Column, DateTime, Enum,
    ForeignKey, String, Text,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class ApprovalAction(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ON_HOLD = "ON_HOLD"
    ESCALATED = "ESCALATED"
    COMMENT_ADDED = "COMMENT_ADDED"
    CANCELLED = "CANCELLED"


class ApprovalHistory(Base):
    """
    Immutable log of every action taken on an Approval record.
    New rows are only inserted — never updated.
    """

    __tablename__ = "approval_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    approval_id = Column(
        BigInteger,
        ForeignKey("approvals.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_id = Column(
        String(35),
        ForeignKey("invoices.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action = Column(Enum(ApprovalAction), nullable=False)
    actor = Column(String(100), nullable=False)
    comment = Column(Text, nullable=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # --- Relationships ---
    approval = relationship("Approval", back_populates="history")
    invoice = relationship("Invoice")

    def __repr__(self) -> str:
        return (
            f"<ApprovalHistory id={self.id} invoice_id={self.invoice_id} "
            f"action={self.action} actor={self.actor!r}>"
        )
