"""
YottaPay AI – Approval Service

Manages the approval workflow for invoices that have passed three-way matching.

Business Rules (from business_rules.md):
- APR-001: Only invoices with status MATCHED or PARTIALLY_MATCHED may enter approval.
- APR-002: No invoice with an open BLOCKING exception may be approved.
- APR-003: Vendor must be ACTIVE before approval can be requested.
- APR-004: Every approval action creates an ApprovalHistory entry and an AuditEvent.
- APR-005: An approved invoice triggers PaymentService.evaluate_readiness().
"""
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit.audit_service import AuditService
from app.models.approval import Approval, ApprovalStatus
from app.models.approval_history import ApprovalHistory, ApprovalAction
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_exception import (
    InvoiceException,
    ExceptionStatus,
    ExceptionSeverity,
    BLOCKING_EXCEPTION_TYPES,
    BLOCKING_SEVERITIES,
)
from app.models.vendor import Vendor, VendorStatus


class ApprovalService:
    """
    Handles the full approval lifecycle for an invoice:
    request → approve / reject / hold.
    """

    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_invoice_or_404(self, invoice_id: str) -> Invoice:
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice '{invoice_id}' not found.",
            )
        return invoice

    def _get_approval_or_404(self, approval_id: int) -> Approval:
        approval = self.db.query(Approval).filter(Approval.id == approval_id).first()
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval record {approval_id} not found.",
            )
        return approval

    def _check_blocking_exceptions(self, invoice_id: str) -> None:
        """
        Raise HTTPException 422 if the invoice has any open/in-review exceptions
        that are either a BLOCKING type or have CRITICAL/HIGH severity.
        """
        blocking = (
            self.db.query(InvoiceException)
            .filter(
                InvoiceException.invoice_id == invoice_id,
                InvoiceException.status.in_(
                    [ExceptionStatus.OPEN, ExceptionStatus.IN_REVIEW]
                ),
            )
            .all()
        )

        blocking_found = [
            exc
            for exc in blocking
            if exc.exception_type in BLOCKING_EXCEPTION_TYPES
            or exc.severity in BLOCKING_SEVERITIES
        ]

        if blocking_found:
            types_str = ", ".join(str(e.exception_type) for e in blocking_found)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Invoice '{invoice_id}' has {len(blocking_found)} blocking "
                    f"open exception(s): {types_str}. "
                    "Resolve or waive all blocking exceptions before requesting approval."
                ),
            )

    def _add_history(
        self,
        approval: Approval,
        action: ApprovalAction,
        actor: str,
        previous_status: Optional[str],
        new_status: str,
        notes: Optional[str] = None,
    ) -> ApprovalHistory:
        entry = ApprovalHistory(
            approval_id=approval.id,
            invoice_id=approval.invoice_id,
            action=action,
            actor=actor,
            comment=notes,
            previous_status=previous_status,
            new_status=new_status,
        )
        self.db.add(entry)
        return entry

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def request_approval(self, invoice_id: str, actor: str = "system") -> Approval:
        """
        Create an Approval record for an invoice.

        Eligibility checks (raises HTTPException if any fail):
        1. Invoice exists.
        2. Invoice status is MATCHED or PARTIALLY_MATCHED.
        3. Vendor is ACTIVE.
        4. No open blocking exceptions.

        Returns the newly created Approval.
        """
        invoice = self._get_invoice_or_404(invoice_id)

        # --- Rule APR-001: invoice status check ---
        eligible_statuses = {InvoiceStatus.MATCHED, InvoiceStatus.PARTIALLY_MATCHED}
        # Also allow EXCEPTION status invoices where exceptions have been waived
        if invoice.status not in eligible_statuses and invoice.status != InvoiceStatus.EXCEPTION:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Invoice '{invoice_id}' cannot enter approval from status "
                    f"'{invoice.status}'. "
                    "Required: MATCHED or PARTIALLY_MATCHED."
                ),
            )

        # --- Rule APR-003: vendor must be ACTIVE ---
        vendor = self.db.query(Vendor).filter(Vendor.id == invoice.vendor_id).first()
        if not vendor or vendor.status != VendorStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Vendor '{invoice.vendor_id}' is not ACTIVE "
                    f"(current status: {vendor.status if vendor else 'NOT FOUND'}). "
                    "Cannot request approval for an invoice from an inactive vendor."
                ),
            )

        # --- Rule APR-002: no blocking exceptions ---
        self._check_blocking_exceptions(invoice_id)

        # --- Check for existing pending approval (idempotent) ---
        existing = (
            self.db.query(Approval)
            .filter(Approval.invoice_id == invoice_id)
            .first()
        )
        if existing:
            if existing.status == ApprovalStatus.PENDING:
                # Idempotent: return the already-pending approval
                return existing
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"An approval record already exists for invoice '{invoice_id}' "
                    f"with status '{existing.status}'. "
                    "Cannot create a duplicate approval."
                ),
            )

        # --- Create the Approval record ---
        approval = Approval(
            invoice_id=invoice_id,
            status=ApprovalStatus.PENDING,
            requested_by=actor,
            requested_at=datetime.utcnow(),
        )
        self.db.add(approval)
        self.db.flush()  # populate approval.id

        # --- Create initial history entry ---
        self._add_history(
            approval=approval,
            action=ApprovalAction.SUBMITTED,
            actor=actor,
            previous_status=str(invoice.status),
            new_status=str(ApprovalStatus.PENDING),
            notes="Approval requested.",
        )

        # --- Audit event ---
        self.audit.approval_requested(
            invoice_id=invoice_id,
            approval_id=approval.id,
            actor=actor,
        )

        self.db.commit()
        self.db.refresh(approval)
        return approval

    def approve(
        self,
        approval_id: int,
        reviewer: str,
        notes: Optional[str] = None,
    ) -> Approval:
        """
        Approve an invoice.

        1. Sets approval.status = APPROVED.
        2. Sets invoice.status = APPROVED.
        3. Creates ApprovalHistory entry.
        4. Logs AuditEvent.
        5. Triggers PaymentService.evaluate_readiness().

        Returns the updated Approval.
        """
        approval = self._get_approval_or_404(approval_id)

        if approval.status != ApprovalStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Approval {approval_id} cannot be approved from status "
                    f"'{approval.status}'. Only PENDING approvals can be approved."
                ),
            )

        previous_approval_status = str(approval.status)

        # --- Update Approval ---
        approval.status = ApprovalStatus.APPROVED
        approval.reviewed_at = datetime.utcnow()
        approval.reviewed_by = reviewer
        approval.decision_notes = notes

        # --- Update Invoice ---
        invoice = self._get_invoice_or_404(approval.invoice_id)
        previous_invoice_status = str(invoice.status)
        invoice.status = InvoiceStatus.APPROVED
        invoice.updated_at = datetime.utcnow()

        self.db.flush()

        # --- History entry ---
        self._add_history(
            approval=approval,
            action=ApprovalAction.APPROVED,
            actor=reviewer,
            previous_status=previous_approval_status,
            new_status=str(ApprovalStatus.APPROVED),
            notes=notes,
        )

        # --- Audit event ---
        self.audit.invoice_approved(
            invoice_id=approval.invoice_id,
            approval_id=approval.id,
            approver=reviewer,
        )

        self.db.commit()
        self.db.refresh(approval)

        # --- Trigger payment readiness evaluation ---
        try:
            from app.payments.payment_service import PaymentService
            payment_svc = PaymentService(self.db)
            payment_svc.evaluate_readiness(invoice_id=approval.invoice_id, actor=reviewer)
        except Exception:
            # Payment evaluation is non-blocking; log but do not fail approval
            pass

        return approval

    def reject(
        self,
        approval_id: int,
        reviewer: str,
        notes: Optional[str] = None,
    ) -> Approval:
        """
        Reject an invoice approval.

        1. Sets approval.status = REJECTED.
        2. Sets invoice.status = REJECTED.
        3. Creates ApprovalHistory entry.
        4. Logs AuditEvent.

        Returns the updated Approval.
        """
        approval = self._get_approval_or_404(approval_id)

        if approval.status not in (ApprovalStatus.PENDING, ApprovalStatus.ON_HOLD):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Approval {approval_id} cannot be rejected from status "
                    f"'{approval.status}'."
                ),
            )

        previous_status = str(approval.status)

        # --- Update Approval ---
        approval.status = ApprovalStatus.REJECTED
        approval.reviewed_at = datetime.utcnow()
        approval.reviewed_by = reviewer
        approval.decision_notes = notes

        # --- Update Invoice ---
        invoice = self._get_invoice_or_404(approval.invoice_id)
        invoice.status = InvoiceStatus.REJECTED
        invoice.updated_at = datetime.utcnow()

        self.db.flush()

        # --- History entry ---
        self._add_history(
            approval=approval,
            action=ApprovalAction.REJECTED,
            actor=reviewer,
            previous_status=previous_status,
            new_status=str(ApprovalStatus.REJECTED),
            notes=notes,
        )

        # --- Audit event ---
        self.audit.invoice_rejected(
            invoice_id=approval.invoice_id,
            approval_id=approval.id,
            rejector=reviewer,
            reason=notes or "No reason provided.",
        )

        self.db.commit()
        self.db.refresh(approval)
        return approval

    def hold(
        self,
        approval_id: int,
        reviewer: str,
        notes: Optional[str] = None,
    ) -> Approval:
        """
        Place an invoice approval on hold for further review.

        1. Sets approval.status = ON_HOLD.
        2. Creates ApprovalHistory entry.

        Returns the updated Approval.
        """
        approval = self._get_approval_or_404(approval_id)

        if approval.status != ApprovalStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Approval {approval_id} cannot be placed on hold from status "
                    f"'{approval.status}'. Only PENDING approvals can be held."
                ),
            )

        previous_status = str(approval.status)

        # --- Update Approval ---
        approval.status = ApprovalStatus.ON_HOLD
        approval.reviewed_by = reviewer
        approval.decision_notes = notes

        self.db.flush()

        # --- History entry ---
        self._add_history(
            approval=approval,
            action=ApprovalAction.ON_HOLD,
            actor=reviewer,
            previous_status=previous_status,
            new_status=str(ApprovalStatus.ON_HOLD),
            notes=notes,
        )

        self.db.commit()
        self.db.refresh(approval)
        return approval
