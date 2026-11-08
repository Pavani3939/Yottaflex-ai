"""
YottaPay AI – Audit Event ORM Model
Table: audit_events

Immutable event log for every state change across all entities.
Events are INSERT-ONLY — never updated or deleted.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger, Column, DateTime, Enum,
    Index, JSON, String, Text,
)

from app.database.connection import Base


class AuditEntityType(str, enum.Enum):
    VENDOR = "VENDOR"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    GOODS_RECEIPT = "GOODS_RECEIPT"
    INVOICE = "INVOICE"
    INVOICE_LINE = "INVOICE_LINE"
    INVOICE_MATCH = "INVOICE_MATCH"
    INVOICE_EXCEPTION = "INVOICE_EXCEPTION"
    APPROVAL = "APPROVAL"
    PAYMENT = "PAYMENT"


# --- Canonical Event Type constants ---
class AuditEventType:
    # Invoice lifecycle
    INVOICE_CREATED = "INVOICE_CREATED"
    INVOICE_EXTRACTED = "INVOICE_EXTRACTED"
    INVOICE_UPDATED = "INVOICE_UPDATED"
    INVOICE_CANCELLED = "INVOICE_CANCELLED"

    # Matching
    MATCHING_STARTED = "MATCHING_STARTED"
    MATCHING_COMPLETED = "MATCHING_COMPLETED"

    # Exceptions
    EXCEPTION_CREATED = "EXCEPTION_CREATED"
    EXCEPTION_ASSIGNED = "EXCEPTION_ASSIGNED"
    EXCEPTION_RESOLVED = "EXCEPTION_RESOLVED"
    EXCEPTION_WAIVED = "EXCEPTION_WAIVED"
    EXCEPTION_ESCALATED = "EXCEPTION_ESCALATED"

    # Approval
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    INVOICE_APPROVED = "INVOICE_APPROVED"
    INVOICE_REJECTED = "INVOICE_REJECTED"
    INVOICE_ON_HOLD = "INVOICE_ON_HOLD"

    # Payment
    PAYMENT_READY = "PAYMENT_READY"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    PAYMENT_PROCESSED = "PAYMENT_PROCESSED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PAYMENT_REVERSED = "PAYMENT_REVERSED"

    # Vendor
    VENDOR_CREATED = "VENDOR_CREATED"
    VENDOR_UPDATED = "VENDOR_UPDATED"
    VENDOR_STATUS_CHANGED = "VENDOR_STATUS_CHANGED"


class AuditEvent(Base):
    """
    Immutable event record capturing every state transition.

    Rules:
    - Never update or delete a row in this table.
    - event_id must be globally unique (EVT-{UUID4}).
    - actor is 'system' for automated events, username for human actions.
    """

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_event_type", "event_type"),
        Index("idx_audit_created", "created_at"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id = Column(
        String(50),
        nullable=False,
        unique=True,
        comment="EVT-{UUID4}",
    )
    entity_type = Column(Enum(AuditEntityType), nullable=False)
    entity_id = Column(String(50), nullable=False)
    event_type = Column(String(100), nullable=False, comment="e.g. INVOICE_CREATED")
    previous_state = Column(String(100), nullable=True)
    new_state = Column(String(100), nullable=True)
    actor = Column(String(100), nullable=False, default="system")
    description = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True, comment="Extra context key-value")
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<AuditEvent id={self.id} event_id={self.event_id!r} "
            f"event_type={self.event_type!r} entity_id={self.entity_id!r}>"
        )
