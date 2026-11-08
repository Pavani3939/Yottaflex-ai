"""
YottaPay AI – Exception Management Service
Routes, tracks and resolves invoice exceptions.
"""
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit.audit_service import AuditService
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_exception import (
    InvoiceException, ExceptionStatus, ExceptionSeverity,
    BLOCKING_EXCEPTION_TYPES,
)
from app.models.audit_event import AuditEventType, AuditEntityType


class ExceptionService:
    """Manages the lifecycle of invoice exceptions."""

    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def resolve(
        self,
        exception_id: int,
        resolution_notes: str,
        resolved_by: str,
        waive: bool = False,
    ) -> InvoiceException:
        """
        Resolve or waive an open exception.

        Rules:
        - EXC-001: Only OPEN or IN_REVIEW exceptions can be resolved.
        - EXC-002: resolution_notes is mandatory.
        - EXC-003: Creates an audit event.
        """
        exc = self.db.query(InvoiceException).filter(
            InvoiceException.id == exception_id
        ).first()
        if not exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exception {exception_id} not found.",
            )
        if exc.status not in (ExceptionStatus.OPEN, ExceptionStatus.IN_REVIEW):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Exception {exception_id} has status {exc.status.value} and cannot be resolved.",
            )
        if not resolution_notes or not resolution_notes.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="resolution_notes is required to resolve an exception.",
            )

        new_status = ExceptionStatus.WAIVED if waive else ExceptionStatus.RESOLVED
        prev_status = exc.status.value

        exc.status = new_status
        exc.resolved_by = resolved_by
        exc.resolved_at = datetime.utcnow()
        exc.resolution_notes = resolution_notes
        self.db.flush()

        # Audit event
        self.audit.exception_resolved(
            exc.invoice_id, exception_id, resolution_notes, resolved_by
        )

        # Check if invoice can now proceed to approval
        self._check_invoice_unblocked(exc.invoice_id)

        return exc

    def assign(
        self,
        exception_id: int,
        assigned_to: str,
        actor: str,
    ) -> InvoiceException:
        """Assign an exception to an analyst."""
        exc = self.db.query(InvoiceException).filter(
            InvoiceException.id == exception_id
        ).first()
        if not exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exception {exception_id} not found.",
            )
        exc.assigned_to = assigned_to
        if exc.status == ExceptionStatus.OPEN:
            exc.status = ExceptionStatus.IN_REVIEW
        self.db.flush()

        self.audit.log(
            AuditEntityType.INVOICE_EXCEPTION,
            str(exception_id),
            AuditEventType.EXCEPTION_ASSIGNED,
            actor=actor,
            description=f"Exception {exception_id} assigned to {assigned_to}.",
        )
        return exc

    def _check_invoice_unblocked(self, invoice_id: str) -> None:
        """
        After resolving an exception, check if the invoice still has
        blocking open exceptions. Update invoice status accordingly.
        """
        blocking_open = (
            self.db.query(InvoiceException)
            .filter(
                InvoiceException.invoice_id == invoice_id,
                InvoiceException.status.in_([
                    ExceptionStatus.OPEN, ExceptionStatus.IN_REVIEW
                ]),
            )
            .all()
        )

        # Apply is_blocking property
        still_blocked = any(e.is_blocking for e in blocking_open)

        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if invoice and not still_blocked and invoice.status == InvoiceStatus.EXCEPTION:
            # All blocking exceptions resolved — invoice can proceed
            invoice.status = InvoiceStatus.MATCHED
            self.db.flush()
            self.audit.log(
                AuditEntityType.INVOICE,
                invoice_id,
                "INVOICE_UNBLOCKED",
                description="All blocking exceptions resolved. Invoice ready for approval.",
            )
