"""
YottaPay AI – Payment Service

Evaluates payment readiness and simulates payment processing for approved invoices.

Business Rules (PAY-001 through PAY-007):
- PAY-001: Invoice must have status APPROVED.
- PAY-002: No OPEN or IN_REVIEW blocking exceptions on the invoice.
- PAY-003: Approval record must exist with status APPROVED.
- PAY-004: Vendor must be ACTIVE.
- PAY-005: Vendor must have bank account details (bank_account + bank_ifsc).
- PAY-006: Invoice must not be a duplicate (is_duplicate = False).
- PAY-007: Invoice total_amount must be > 0.
"""
import uuid
from datetime import datetime
from typing import Optional, Tuple

from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from app.audit.audit_service import AuditService
from app.models.approval import Approval, ApprovalStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_exception import (
    InvoiceException,
    ExceptionStatus,
    ExceptionSeverity,
    BLOCKING_EXCEPTION_TYPES,
    BLOCKING_SEVERITIES,
)
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.vendor import Vendor


class PaymentService:
    """
    Handles payment readiness evaluation and simulated payment processing.
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
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Invoice '{invoice_id}' not found.",
            )
        return invoice

    def _get_or_create_payment(self, invoice: Invoice) -> Payment:
        """Return existing Payment record or create a new one."""
        payment = (
            self.db.query(Payment)
            .filter(Payment.invoice_id == invoice.id)
            .first()
        )
        if not payment:
            payment = Payment(
                invoice_id=invoice.id,
                vendor_id=invoice.vendor_id,
                amount=invoice.total_amount,
                currency=invoice.currency or "INR",
                status=PaymentStatus.NOT_READY,
                payment_method=PaymentMethod.NEFT,
            )
            self.db.add(payment)
            self.db.flush()
        return payment

    # ------------------------------------------------------------------
    # PAY-001 through PAY-007 eligibility checks
    # ------------------------------------------------------------------

    def _check_eligibility(self, invoice_id: str) -> Tuple[bool, str]:
        """
        Run all 7 payment eligibility rules.

        Returns:
            (True, "") if all checks pass.
            (False, "<reason>") at the first failing check.
        """
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return False, f"Invoice '{invoice_id}' not found."

        # PAY-001: Invoice status must be APPROVED
        if invoice.status != InvoiceStatus.APPROVED:
            return (
                False,
                f"PAY-001: Invoice status is '{invoice.status}', expected APPROVED.",
            )

        # PAY-002: No open/in-review blocking exceptions
        open_exceptions = (
            self.db.query(InvoiceException)
            .filter(
                InvoiceException.invoice_id == invoice_id,
                InvoiceException.status.in_(
                    [ExceptionStatus.OPEN, ExceptionStatus.IN_REVIEW]
                ),
            )
            .all()
        )
        blocking = [
            exc
            for exc in open_exceptions
            if exc.exception_type in BLOCKING_EXCEPTION_TYPES
            or exc.severity in BLOCKING_SEVERITIES
        ]
        if blocking:
            return (
                False,
                f"PAY-002: {len(blocking)} blocking open exception(s) found "
                f"({', '.join(str(e.exception_type) for e in blocking)}).",
            )

        # PAY-003: Approval record must exist and be APPROVED
        approval = (
            self.db.query(Approval)
            .filter(Approval.invoice_id == invoice_id)
            .first()
        )
        if not approval:
            return False, "PAY-003: No approval record found for this invoice."
        if approval.status != ApprovalStatus.APPROVED:
            return (
                False,
                f"PAY-003: Approval status is '{approval.status}', expected APPROVED.",
            )

        # PAY-004: Vendor must be ACTIVE
        vendor = self.db.query(Vendor).filter(Vendor.id == invoice.vendor_id).first()
        if not vendor:
            return False, f"PAY-004: Vendor '{invoice.vendor_id}' not found."
        from app.models.vendor import VendorStatus
        if vendor.status != VendorStatus.ACTIVE:
            return (
                False,
                f"PAY-004: Vendor '{vendor.id}' is not ACTIVE (status: {vendor.status}).",
            )

        # PAY-005: Vendor must have bank account details
        if not vendor.bank_account or not vendor.bank_ifsc:
            return (
                False,
                f"PAY-005: Vendor '{vendor.id}' is missing bank account details "
                "(bank_account and/or bank_ifsc are empty).",
            )

        # PAY-006: Invoice must not be a duplicate
        if invoice.is_duplicate:
            return (
                False,
                f"PAY-006: Invoice '{invoice_id}' is flagged as a duplicate "
                f"of '{invoice.duplicate_of}'.",
            )

        # PAY-007: Invoice total must be > 0
        try:
            total = float(invoice.total_amount)
        except (TypeError, ValueError):
            total = 0.0
        if total <= 0:
            return (
                False,
                f"PAY-007: Invoice total_amount ({invoice.total_amount}) must be > 0.",
            )

        return True, ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate_readiness(
        self, invoice_id: str, actor: str = "system"
    ) -> Payment:
        """
        Run all PAY-001..PAY-007 checks and set the Payment record status to
        READY_FOR_PAYMENT (all pass) or BLOCKED (any fail).

        Creates a Payment record if one does not yet exist.
        Calls AuditService.payment_ready() when the invoice is ready.

        Returns the Payment record.
        """
        invoice = self._get_invoice_or_404(invoice_id)
        payment = self._get_or_create_payment(invoice)

        is_eligible, reason = self._check_eligibility(invoice_id)

        if is_eligible:
            payment.status = PaymentStatus.READY_FOR_PAYMENT
            payment.failure_reason = None
            payment.updated_at = datetime.utcnow()
            # Reflect on invoice
            invoice.status = InvoiceStatus.PAYMENT_READY
            invoice.updated_at = datetime.utcnow()
            self.db.flush()
            self.audit.payment_ready(
                invoice_id=invoice_id,
                payment_id=payment.id,
                actor=actor,
            )
        else:
            payment.status = PaymentStatus.BLOCKED
            payment.failure_reason = reason
            payment.updated_at = datetime.utcnow()
            self.db.flush()

        self.db.commit()
        self.db.refresh(payment)
        return payment

    def process_payment(
        self, invoice_id: str, actor: str = "system"
    ) -> Payment:
        """
        Simulate processing a payment for a READY_FOR_PAYMENT invoice.

        Steps:
        1. Verify payment exists and is READY_FOR_PAYMENT.
        2. Set status = PAYMENT_PROCESSING.
        3. Generate a payment reference (PAY-REF-{UUID8}).
        4. Set status = PAID.
        5. Update invoice.status = PAID.
        6. Call AuditService.payment_processed().

        Returns the updated Payment record.
        """
        invoice = self._get_invoice_or_404(invoice_id)

        payment = (
            self.db.query(Payment)
            .filter(Payment.invoice_id == invoice_id)
            .first()
        )
        if not payment:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=(
                    f"No payment record found for invoice '{invoice_id}'. "
                    "Call evaluate_readiness first."
                ),
            )

        if payment.status != PaymentStatus.READY_FOR_PAYMENT:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Payment for invoice '{invoice_id}' is in status "
                    f"'{payment.status}'. Only READY_FOR_PAYMENT invoices can be processed."
                ),
            )

        # --- Step 1: Mark as processing ---
        payment.status = PaymentStatus.PAYMENT_PROCESSING
        payment.updated_at = datetime.utcnow()
        invoice.status = InvoiceStatus.PAYMENT_PROCESSING
        invoice.updated_at = datetime.utcnow()
        self.db.flush()

        # --- Step 2: Simulate processing (generate reference) ---
        payment_reference = f"PAY-REF-{str(uuid.uuid4())[:8].upper()}"

        # --- Step 3: Mark as PAID ---
        payment.status = PaymentStatus.PAID
        payment.payment_reference = payment_reference
        payment.processed_at = datetime.utcnow()
        payment.processed_by = actor
        payment.updated_at = datetime.utcnow()

        invoice.status = InvoiceStatus.PAID
        invoice.updated_at = datetime.utcnow()

        self.db.flush()

        # --- Audit event ---
        self.audit.payment_processed(
            invoice_id=invoice_id,
            payment_id=payment.id,
            reference=payment_reference,
            actor=actor,
        )

        self.db.commit()
        self.db.refresh(payment)
        return payment
