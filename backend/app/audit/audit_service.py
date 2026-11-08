"""
YottaPay AI – Audit Service

Creates immutable audit events for every state change.
This service is called by ALL other services — never bypassed.

Rules (from business_rules.md):
- AUD-001: Every state change must generate an audit_event record.
- AUD-002: Audit events are immutable — never updated or deleted.
- AUD-003: Every event must record entity info, event type, states, actor, timestamp.
- AUD-004: event_id must be globally unique (EVT-{UUID4}).
"""
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent, AuditEntityType, AuditEventType
from app.utils.id_generator import audit_event_id


class AuditService:
    """Provides methods to create immutable audit event records."""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        entity_type: AuditEntityType,
        entity_id: str,
        event_type: str,
        actor: str = "system",
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """
        Insert a new audit event.

        This is an INSERT-ONLY operation — existing records are never touched.

        Args:
            entity_type: The type of entity being audited.
            entity_id: The ID of the entity being audited.
            event_type: The event constant (e.g. AuditEventType.INVOICE_CREATED).
            actor: Username or 'system'.
            previous_state: State before the event.
            new_state: State after the event.
            description: Human-readable description.
            metadata: Optional key-value context.
            ip_address: Client IP if available.

        Returns:
            The created AuditEvent instance.
        """
        event = AuditEvent(
            event_id=audit_event_id(),
            entity_type=entity_type,
            entity_id=str(entity_id),
            event_type=event_type,
            previous_state=previous_state,
            new_state=new_state,
            actor=actor,
            description=description,
            metadata_=metadata,
            ip_address=ip_address,
        )
        self.db.add(event)
        self.db.flush()   # get the auto-increment ID without committing
        return event

    # --- Convenience wrappers ---

    def invoice_created(self, invoice_id: str, actor: str = "system") -> AuditEvent:
        return self.log(
            AuditEntityType.INVOICE, invoice_id,
            AuditEventType.INVOICE_CREATED,
            actor=actor, new_state="DRAFT",
            description=f"Invoice {invoice_id} created.",
        )

    def invoice_extracted(self, invoice_id: str, method: str, confidence: float,
                          actor: str = "system") -> AuditEvent:
        return self.log(
            AuditEntityType.INVOICE, invoice_id,
            AuditEventType.INVOICE_EXTRACTED,
            actor=actor,
            previous_state="PENDING_EXTRACTION", new_state="EXTRACTED",
            description=f"Invoice extracted via {method}. Confidence: {confidence:.1f}%",
            metadata={"extraction_method": method, "confidence": confidence},
        )

    def matching_started(self, invoice_id: str, actor: str = "system") -> AuditEvent:
        return self.log(
            AuditEntityType.INVOICE, invoice_id,
            AuditEventType.MATCHING_STARTED,
            actor=actor,
            previous_state="PENDING_MATCH", new_state="MATCHING",
            description=f"Three-way matching started for invoice {invoice_id}.",
        )

    def matching_completed(self, invoice_id: str, result: str,
                           actor: str = "system") -> AuditEvent:
        return self.log(
            AuditEntityType.INVOICE, invoice_id,
            AuditEventType.MATCHING_COMPLETED,
            actor=actor,
            previous_state="MATCHING", new_state=result,
            description=f"Matching completed with result: {result}.",
        )

    def exception_created(self, invoice_id: str, exc_id: int, exc_type: str,
                          severity: str, actor: str = "system") -> AuditEvent:
        return self.log(
            AuditEntityType.INVOICE_EXCEPTION, str(exc_id),
            AuditEventType.EXCEPTION_CREATED,
            actor=actor,
            new_state="OPEN",
            description=f"{severity} {exc_type} exception created for invoice {invoice_id}.",
            metadata={"invoice_id": invoice_id, "exception_type": exc_type},
        )

    def exception_resolved(self, exc_id: int, invoice_id: str, resolution: str,
                           actor: str = "system") -> AuditEvent:
        return self.log(
            AuditEntityType.INVOICE_EXCEPTION, str(exc_id),
            AuditEventType.EXCEPTION_RESOLVED,
            actor=actor,
            previous_state="OPEN", new_state="RESOLVED",
            description=f"Exception {exc_id} resolved: {resolution}",
            metadata={"invoice_id": invoice_id},
        )

    def approval_requested(self, invoice_id: str, approval_id: int,
                           actor: str = "system") -> AuditEvent:
        return self.log(
            AuditEntityType.APPROVAL, str(approval_id),
            AuditEventType.APPROVAL_REQUESTED,
            actor=actor, new_state="PENDING",
            description=f"Approval requested for invoice {invoice_id}.",
            metadata={"invoice_id": invoice_id},
        )

    def invoice_approved(self, invoice_id: str, approval_id: int,
                         approver: str) -> AuditEvent:
        return self.log(
            AuditEntityType.APPROVAL, str(approval_id),
            AuditEventType.INVOICE_APPROVED,
            actor=approver,
            previous_state="PENDING", new_state="APPROVED",
            description=f"Invoice {invoice_id} approved by {approver}.",
            metadata={"invoice_id": invoice_id},
        )

    def invoice_rejected(self, invoice_id: str, approval_id: int,
                         rejector: str, reason: str) -> AuditEvent:
        return self.log(
            AuditEntityType.APPROVAL, str(approval_id),
            AuditEventType.INVOICE_REJECTED,
            actor=rejector,
            previous_state="PENDING", new_state="REJECTED",
            description=f"Invoice {invoice_id} rejected: {reason}",
            metadata={"invoice_id": invoice_id, "reason": reason},
        )

    def payment_ready(self, invoice_id: str, payment_id: int,
                      actor: str = "system") -> AuditEvent:
        return self.log(
            AuditEntityType.PAYMENT, str(payment_id),
            AuditEventType.PAYMENT_READY,
            actor=actor,
            previous_state="NOT_READY", new_state="READY_FOR_PAYMENT",
            description=f"Payment is ready for invoice {invoice_id}.",
            metadata={"invoice_id": invoice_id},
        )

    def payment_processed(self, invoice_id: str, payment_id: int,
                          reference: str, actor: str = "system") -> AuditEvent:
        return self.log(
            AuditEntityType.PAYMENT, str(payment_id),
            AuditEventType.PAYMENT_PROCESSED,
            actor=actor,
            previous_state="PAYMENT_PROCESSING", new_state="PAID",
            description=f"Payment processed for invoice {invoice_id}. Ref: {reference}",
            metadata={"invoice_id": invoice_id, "reference": reference},
        )

    def payment_failed(self, invoice_id: str, payment_id: int,
                       reason: str, actor: str = "system") -> AuditEvent:
        return self.log(
            AuditEntityType.PAYMENT, str(payment_id),
            AuditEventType.PAYMENT_FAILED,
            actor=actor,
            previous_state="PAYMENT_PROCESSING", new_state="FAILED",
            description=f"Payment failed for invoice {invoice_id}: {reason}",
            metadata={"invoice_id": invoice_id, "reason": reason},
        )
