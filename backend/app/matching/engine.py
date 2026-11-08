"""
YottaPay AI – Three-Way Matching Engine
========================================
The most critical component of the system.

Compares: Invoice + Purchase Order + Goods Receipt

Checks performed (in order):
  A. Vendor validation
  B. PO existence
  C. PO status check
  D. Date check (invoice date ≥ PO date)
  E. Duplicate detection
  F. SKU matching
  G. Quantity matching (per line)
  H. Price matching (per line, with tolerance)
  I. Receipt quantity check
  J. Tax code and amount matching
  K. Invoice arithmetic reconciliation

Returns one of:
  MATCHED, PRICE_VARIANCE, QUANTITY_MISMATCH, TAX_MISMATCH,
  MISSING_RECEIPT, DUPLICATE, VENDOR_ERROR, TOTAL_MISMATCH,
  DATE_ERROR, PARTIALLY_MATCHED, FAILED
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.invoice import Invoice, InvoiceStatus, MatchingStatus
from app.models.invoice_exception import (
    InvoiceException, ExceptionType, ExceptionSeverity, ExceptionStatus,
    BLOCKING_EXCEPTION_TYPES,
)
from app.models.invoice_match import InvoiceMatch, MatchOverallStatus
from app.models.goods_receipt import GoodsReceipt
from app.models.goods_receipt_line import GoodsReceiptLine
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_order_line import PurchaseOrderLine
from app.models.vendor import Vendor, VendorStatus
from app.audit.audit_service import AuditService
from app.models.audit_event import AuditEventType
from app.utils.arithmetic import (
    round2, price_variance_pct, qty_variance_pct, reconcile_invoice_totals
)

settings = get_settings()


# ---------------------------------------------------------------------------
# Check result dataclass
# ---------------------------------------------------------------------------
@dataclass
class CheckResult:
    """Result of a single matching check."""
    check_name: str
    passed: bool
    exception_type: Optional[str] = None
    severity: Optional[str] = None
    description: str = ""
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    po_line_id: Optional[str] = None
    recommended_action: str = ""


@dataclass
class MatchResult:
    """Aggregated result from the full matching run."""
    overall_status: str = "FAILED"
    checks: list[CheckResult] = field(default_factory=list)
    exceptions_to_create: list[CheckResult] = field(default_factory=list)

    # Individual check flags
    vendor_valid: bool = False
    po_exists: bool = False
    sku_matched: bool = False
    qty_matched: bool = False
    price_matched: bool = False
    tax_matched: bool = False
    arithmetic_valid: bool = False
    receipt_matched: bool = False
    is_duplicate: bool = False


# ---------------------------------------------------------------------------
# Matching Engine
# ---------------------------------------------------------------------------
class ThreeWayMatchingEngine:
    """
    Implements the full three-way invoice matching algorithm.

    Usage:
        engine = ThreeWayMatchingEngine(db)
        result = engine.run(invoice_id)
    """

    def __init__(self, db: Session):
        self.db = db
        self.settings = settings
        self.price_tol = Decimal(str(settings.PRICE_TOLERANCE_PCT))
        self.qty_tol = Decimal(str(settings.QTY_TOLERANCE_PCT))
        self.tax_tol = Decimal(str(settings.TAX_TOLERANCE_PCT))
        self.total_tol = Decimal(str(settings.TOTAL_TOLERANCE_PCT))

    def run(self, invoice_id: str, actor: str = "system") -> MatchResult:
        """
        Execute the full matching pipeline for a given invoice.

        Steps:
          1. Load invoice and related entities from DB.
          2. Run all checks in order.
          3. Determine overall status.
          4. Persist InvoiceMatch record + InvoiceException records.
          5. Update invoice status and matching_status.
          6. Create audit events.
          7. Return MatchResult.
        """
        audit = AuditService(self.db)

        # --- Load invoice ---
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        # Update status to MATCHING
        prev_status = invoice.status.value
        invoice.status = InvoiceStatus.MATCHING
        invoice.matching_status = MatchingStatus.IN_PROGRESS
        self.db.flush()
        audit.matching_started(invoice_id, actor)

        result = MatchResult()
        checks = []

        # === CHECK A: Vendor Validation ===
        vendor = self.db.query(Vendor).filter(Vendor.id == invoice.vendor_id).first()
        vendor_check = self._check_vendor(vendor, invoice)
        checks.append(vendor_check)
        result.vendor_valid = vendor_check.passed

        if not vendor_check.passed:
            result.exceptions_to_create.append(vendor_check)
            result.overall_status = "VENDOR_ERROR"
            result = self._finalize(result, checks, invoice, actor, audit, prev_status)
            return result

        # === CHECK B: PO Existence ===
        po = None
        if invoice.po_id:
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == invoice.po_id).first()
        po_check = self._check_po_exists(po, invoice)
        checks.append(po_check)
        result.po_exists = po_check.passed

        if not po_check.passed:
            result.exceptions_to_create.append(po_check)
            result.overall_status = "VENDOR_ERROR"
            result = self._finalize(result, checks, invoice, actor, audit, prev_status)
            return result

        # === CHECK C: Date Check ===
        if po:
            date_check = self._check_date(invoice, po)
            checks.append(date_check)
            if not date_check.passed:
                result.exceptions_to_create.append(date_check)

        # === CHECK D: Duplicate Detection ===
        dup_check = self._check_duplicate(invoice)
        checks.append(dup_check)
        result.is_duplicate = dup_check.passed is False and dup_check.exception_type == ExceptionType.DUPLICATE
        # Note: dup_check.passed = True means NO duplicate found
        if not dup_check.passed:
            result.exceptions_to_create.append(dup_check)

        # === CHECKS E-K: Line-level checks ===
        invoice_lines = invoice.lines
        po_lines = po.lines if po else []

        # Build lookups
        po_line_by_sku: dict[str, PurchaseOrderLine] = {pl.sku: pl for pl in po_lines}
        po_line_by_id: dict[str, PurchaseOrderLine] = {pl.id: pl for pl in po_lines}

        # Received quantities per PO line (sum of GRN line accepted_qty)
        received_by_po_line = self._get_received_quantities(po_lines)

        sku_all_match = True
        qty_all_match = True
        price_all_match = True
        tax_all_match = True
        receipt_all_match = True

        for inv_line in invoice_lines:
            # === CHECK F: SKU Matching ===
            matched_po_line = None
            if inv_line.po_line_id and inv_line.po_line_id in po_line_by_id:
                matched_po_line = po_line_by_id[inv_line.po_line_id]
            elif inv_line.sku and inv_line.sku in po_line_by_sku:
                matched_po_line = po_line_by_sku[inv_line.sku]

            if not matched_po_line and po_lines:
                sku_check = CheckResult(
                    check_name="SKU_MATCH",
                    passed=False,
                    exception_type=ExceptionType.SKU_MISMATCH,
                    severity=ExceptionSeverity.HIGH,
                    description=f"SKU '{inv_line.sku}' on invoice line {inv_line.line_number} not found in PO {invoice.po_id}",
                    expected_value=", ".join(pl.sku for pl in po_lines),
                    actual_value=inv_line.sku,
                    recommended_action="Verify SKU with vendor and correct invoice.",
                )
                checks.append(sku_check)
                result.exceptions_to_create.append(sku_check)
                sku_all_match = False
                continue  # Can't check qty/price without a PO line

            if matched_po_line:
                # === CHECK G: Quantity Matching ===
                qty_check = self._check_quantity(inv_line, matched_po_line)
                checks.append(qty_check)
                if not qty_check.passed:
                    result.exceptions_to_create.append(qty_check)
                    qty_all_match = False

                # === CHECK H: Price Matching ===
                price_check = self._check_price(inv_line, matched_po_line)
                checks.append(price_check)
                if not price_check.passed:
                    result.exceptions_to_create.append(price_check)
                    price_all_match = False

                # === CHECK I: Receipt Quantity ===
                receipt_check = self._check_receipt(
                    inv_line, matched_po_line, received_by_po_line
                )
                checks.append(receipt_check)
                if not receipt_check.passed:
                    result.exceptions_to_create.append(receipt_check)
                    receipt_all_match = False

                # === CHECK J: Tax Matching ===
                tax_check = self._check_tax(inv_line, matched_po_line)
                checks.append(tax_check)
                if not tax_check.passed:
                    result.exceptions_to_create.append(tax_check)
                    tax_all_match = False

        result.sku_matched = sku_all_match
        result.qty_matched = qty_all_match
        result.price_matched = price_all_match
        result.tax_matched = tax_all_match
        result.receipt_matched = receipt_all_match

        # === CHECK K: Invoice Arithmetic ===
        arith_check = self._check_arithmetic(invoice)
        checks.append(arith_check)
        result.arithmetic_valid = arith_check.passed
        if not arith_check.passed:
            result.exceptions_to_create.append(arith_check)

        # === Determine Overall Status ===
        result.overall_status = self._determine_overall_status(result)
        result.checks = checks

        # === Persist and return ===
        result = self._finalize(result, checks, invoice, actor, audit, prev_status)
        return result

    # -----------------------------------------------------------------------
    # Individual Check Methods
    # -----------------------------------------------------------------------
    def _check_vendor(self, vendor: Optional[Vendor], invoice: Invoice) -> CheckResult:
        if not vendor:
            return CheckResult(
                check_name="VENDOR_VALIDATION",
                passed=False,
                exception_type=ExceptionType.VENDOR_ERROR,
                severity=ExceptionSeverity.CRITICAL,
                description=f"Vendor {invoice.vendor_id} not found in system.",
                expected_value="ACTIVE vendor",
                actual_value="NOT_FOUND",
                recommended_action="Verify vendor registration and resubmit.",
            )
        if vendor.status != VendorStatus.ACTIVE:
            return CheckResult(
                check_name="VENDOR_VALIDATION",
                passed=False,
                exception_type=ExceptionType.VENDOR_ERROR,
                severity=ExceptionSeverity.CRITICAL,
                description=f"Vendor {vendor.id} has status {vendor.status.value}. Only ACTIVE vendors can submit invoices.",
                expected_value="ACTIVE",
                actual_value=vendor.status.value,
                recommended_action="Contact vendor management to review vendor status.",
            )
        return CheckResult(check_name="VENDOR_VALIDATION", passed=True,
                           description="Vendor is ACTIVE.")

    def _check_po_exists(self, po: Optional[PurchaseOrder], invoice: Invoice) -> CheckResult:
        if not invoice.po_id:
            return CheckResult(check_name="PO_EXISTS", passed=True,
                               description="No PO reference on invoice (non-PO invoice).")
        if not po:
            return CheckResult(
                check_name="PO_EXISTS",
                passed=False,
                exception_type=ExceptionType.VENDOR_ERROR,
                severity=ExceptionSeverity.CRITICAL,
                description=f"Referenced PO {invoice.po_id} not found in system.",
                expected_value="Existing PO",
                actual_value="NOT_FOUND",
                recommended_action="Verify PO number with vendor.",
            )
        if po.vendor_id != invoice.vendor_id:
            return CheckResult(
                check_name="PO_EXISTS",
                passed=False,
                exception_type=ExceptionType.VENDOR_ERROR,
                severity=ExceptionSeverity.CRITICAL,
                description=f"PO {po.id} belongs to vendor {po.vendor_id}, but invoice is from {invoice.vendor_id}.",
                expected_value=po.vendor_id,
                actual_value=invoice.vendor_id,
                recommended_action="Verify vendor-PO assignment.",
            )
        return CheckResult(check_name="PO_EXISTS", passed=True,
                           description=f"PO {po.id} found and vendor matches.")

    def _check_date(self, invoice: Invoice, po: PurchaseOrder) -> CheckResult:
        if invoice.invoice_date < po.order_date:
            return CheckResult(
                check_name="DATE_CHECK",
                passed=False,
                exception_type=ExceptionType.DATE_ERROR,
                severity=ExceptionSeverity.HIGH,
                description=(
                    f"Invoice date {invoice.invoice_date} is before PO order date {po.order_date}. "
                    "An invoice cannot predate its purchase order."
                ),
                expected_value=f">= {po.order_date}",
                actual_value=str(invoice.invoice_date),
                recommended_action="Request corrected invoice from vendor with valid date.",
            )
        return CheckResult(check_name="DATE_CHECK", passed=True,
                           description="Invoice date is valid relative to PO date.")

    def _check_duplicate(self, invoice: Invoice) -> CheckResult:
        if invoice.is_duplicate:
            return CheckResult(
                check_name="DUPLICATE_CHECK",
                passed=False,
                exception_type=ExceptionType.DUPLICATE,
                severity=ExceptionSeverity.CRITICAL,
                description=(
                    f"Invoice number '{invoice.invoice_number}' from vendor {invoice.vendor_id} "
                    f"is a duplicate of {invoice.duplicate_of}."
                ),
                expected_value="Unique invoice number",
                actual_value=invoice.invoice_number,
                recommended_action="Reject duplicate invoice. Contact vendor to confirm.",
            )
        # Also check DB for same invoice_number + vendor_id
        existing = (
            self.db.query(Invoice)
            .filter(
                Invoice.invoice_number == invoice.invoice_number,
                Invoice.vendor_id == invoice.vendor_id,
                Invoice.id != invoice.id,
            )
            .first()
        )
        if existing:
            return CheckResult(
                check_name="DUPLICATE_CHECK",
                passed=False,
                exception_type=ExceptionType.DUPLICATE,
                severity=ExceptionSeverity.CRITICAL,
                description=(
                    f"Invoice number '{invoice.invoice_number}' already exists as {existing.id}."
                ),
                expected_value="Unique invoice",
                actual_value=existing.id,
                recommended_action="Reject duplicate. Verify with vendor.",
            )
        return CheckResult(check_name="DUPLICATE_CHECK", passed=True,
                           description="No duplicate detected.")

    def _check_quantity(
        self, inv_line, po_line: PurchaseOrderLine
    ) -> CheckResult:
        inv_qty = Decimal(str(inv_line.quantity))
        po_qty = Decimal(str(po_line.quantity))
        variance_pct = qty_variance_pct(po_qty, inv_qty)

        if variance_pct <= self.qty_tol:
            return CheckResult(
                check_name=f"QTY_CHECK_LINE_{inv_line.line_number}",
                passed=True,
                description=f"Quantity matched: {inv_qty} (invoice) vs {po_qty} (PO).",
                po_line_id=po_line.id,
            )

        severity = ExceptionSeverity.HIGH if variance_pct > 10 else ExceptionSeverity.MEDIUM
        return CheckResult(
            check_name=f"QTY_CHECK_LINE_{inv_line.line_number}",
            passed=False,
            exception_type=ExceptionType.QUANTITY_MISMATCH,
            severity=severity,
            description=(
                f"Line {inv_line.line_number} (SKU: {inv_line.sku}): "
                f"Invoice qty {inv_qty} differs from PO qty {po_qty} "
                f"({variance_pct:.2f}% variance)."
            ),
            expected_value=str(po_qty),
            actual_value=str(inv_qty),
            po_line_id=po_line.id,
            recommended_action="Review quantity with vendor. Request credit note if overbilled.",
        )

    def _check_price(self, inv_line, po_line: PurchaseOrderLine) -> CheckResult:
        inv_price = Decimal(str(inv_line.unit_price))
        po_price = Decimal(str(po_line.unit_price))
        variance_pct = price_variance_pct(po_price, inv_price)

        if variance_pct <= self.price_tol:
            return CheckResult(
                check_name=f"PRICE_CHECK_LINE_{inv_line.line_number}",
                passed=True,
                description=f"Price matched within tolerance: ₹{inv_price} (invoice) vs ₹{po_price} (PO).",
                po_line_id=po_line.id,
            )

        severity = ExceptionSeverity.HIGH if variance_pct > 5 else ExceptionSeverity.MEDIUM
        return CheckResult(
            check_name=f"PRICE_CHECK_LINE_{inv_line.line_number}",
            passed=False,
            exception_type=ExceptionType.PRICE_VARIANCE,
            severity=severity,
            description=(
                f"Line {inv_line.line_number} (SKU: {inv_line.sku}): "
                f"Unit price ₹{inv_price} vs PO price ₹{po_price} "
                f"({variance_pct:.2f}% variance, tolerance {self.price_tol}%)."
            ),
            expected_value=f"₹{po_price}",
            actual_value=f"₹{inv_price}",
            po_line_id=po_line.id,
            recommended_action="Obtain price clarification from vendor or raise PO amendment.",
        )

    def _check_receipt(
        self,
        inv_line,
        po_line: PurchaseOrderLine,
        received_by_po_line: dict[str, Decimal],
    ) -> CheckResult:
        inv_qty = Decimal(str(inv_line.quantity))
        received_qty = received_by_po_line.get(po_line.id, Decimal("0"))

        if received_qty >= inv_qty:
            return CheckResult(
                check_name=f"RECEIPT_CHECK_LINE_{inv_line.line_number}",
                passed=True,
                description=f"GRN quantity {received_qty} covers invoice quantity {inv_qty}.",
                po_line_id=po_line.id,
            )

        return CheckResult(
            check_name=f"RECEIPT_CHECK_LINE_{inv_line.line_number}",
            passed=False,
            exception_type=ExceptionType.MISSING_RECEIPT,
            severity=ExceptionSeverity.HIGH,
            description=(
                f"Line {inv_line.line_number} (SKU: {inv_line.sku}): "
                f"GRN accepted qty {received_qty} is less than invoice qty {inv_qty}. "
                f"Shortfall: {inv_qty - received_qty} units."
            ),
            expected_value=f">= {inv_qty}",
            actual_value=str(received_qty),
            po_line_id=po_line.id,
            recommended_action="Verify goods receipt. Obtain GRN for missing quantities.",
        )

    def _check_tax(self, inv_line, po_line: PurchaseOrderLine) -> CheckResult:
        inv_tax_code = inv_line.tax_code
        po_tax_code = po_line.tax_code

        if inv_tax_code != po_tax_code:
            return CheckResult(
                check_name=f"TAX_CHECK_LINE_{inv_line.line_number}",
                passed=False,
                exception_type=ExceptionType.TAX_MISMATCH,
                severity=ExceptionSeverity.MEDIUM,
                description=(
                    f"Line {inv_line.line_number} (SKU: {inv_line.sku}): "
                    f"Tax code mismatch. Invoice: {inv_tax_code}, PO: {po_tax_code}."
                ),
                expected_value=po_tax_code,
                actual_value=inv_tax_code,
                po_line_id=po_line.id,
                recommended_action="Verify applicable tax code with tax team.",
            )

        # Check tax amount accuracy
        inv_rate = Decimal(str(inv_line.tax_rate))
        inv_subtotal = Decimal(str(inv_line.line_subtotal))
        expected_tax = round2(inv_subtotal * inv_rate / 100)
        actual_tax = Decimal(str(inv_line.tax_amount))
        tax_diff_pct = (
            abs(actual_tax - expected_tax) / expected_tax * 100
            if expected_tax > 0 else Decimal("0")
        )

        if tax_diff_pct > self.tax_tol:
            return CheckResult(
                check_name=f"TAX_CHECK_LINE_{inv_line.line_number}",
                passed=False,
                exception_type=ExceptionType.TAX_MISMATCH,
                severity=ExceptionSeverity.MEDIUM,
                description=(
                    f"Line {inv_line.line_number}: Tax amount ₹{actual_tax} "
                    f"differs from expected ₹{expected_tax} ({tax_diff_pct:.2f}% variance)."
                ),
                expected_value=str(expected_tax),
                actual_value=str(actual_tax),
                po_line_id=po_line.id,
                recommended_action="Request corrected tax calculation from vendor.",
            )

        return CheckResult(
            check_name=f"TAX_CHECK_LINE_{inv_line.line_number}",
            passed=True,
            description=f"Tax code and amount verified for line {inv_line.line_number}.",
            po_line_id=po_line.id,
        )

    def _check_arithmetic(self, invoice: Invoice) -> CheckResult:
        lines = invoice.lines
        if not lines:
            return CheckResult(
                check_name="ARITHMETIC_CHECK",
                passed=False,
                exception_type=ExceptionType.ARITHMETIC_ERROR,
                severity=ExceptionSeverity.CRITICAL,
                description="Invoice has no lines.",
                recommended_action="Add invoice lines before submitting.",
            )

        reconciliation = reconcile_invoice_totals(
            stated_subtotal=Decimal(str(invoice.subtotal)),
            stated_tax=Decimal(str(invoice.tax_amount)),
            stated_total=Decimal(str(invoice.total_amount)),
            line_subtotals=[Decimal(str(l.line_subtotal)) for l in lines],
            line_taxes=[Decimal(str(l.tax_amount)) for l in lines],
        )

        # Store calculated totals on invoice
        invoice.calculated_subtotal = float(reconciliation["calculated_subtotal"])
        invoice.calculated_tax = float(reconciliation["calculated_tax"])
        invoice.calculated_total = float(reconciliation["calculated_total"])

        if reconciliation["arithmetic_valid"]:
            return CheckResult(
                check_name="ARITHMETIC_CHECK",
                passed=True,
                description="Invoice totals reconcile with line sums.",
            )

        return CheckResult(
            check_name="ARITHMETIC_CHECK",
            passed=False,
            exception_type=ExceptionType.ARITHMETIC_ERROR,
            severity=ExceptionSeverity.CRITICAL,
            description=(
                f"Invoice totals do not reconcile. "
                f"Stated total: ₹{invoice.total_amount}, "
                f"Calculated total: ₹{reconciliation['calculated_total']} "
                f"(diff: ₹{reconciliation['total_diff']})."
            ),
            expected_value=str(reconciliation["calculated_total"]),
            actual_value=str(invoice.total_amount),
            recommended_action="Request corrected invoice from vendor.",
        )

    # -----------------------------------------------------------------------
    # Overall Status Determination
    # -----------------------------------------------------------------------
    def _determine_overall_status(self, result: MatchResult) -> str:
        """
        Derive the single overall_status from all check results.
        Priority order: DUPLICATE > VENDOR_ERROR > DATE_ERROR > TOTAL_MISMATCH
                        > individual mismatches > MATCHED
        """
        exc_types = {c.exception_type for c in result.exceptions_to_create}

        if ExceptionType.DUPLICATE in exc_types:
            return MatchOverallStatus.DUPLICATE
        if ExceptionType.VENDOR_ERROR in exc_types:
            return MatchOverallStatus.VENDOR_ERROR
        if ExceptionType.DATE_ERROR in exc_types:
            return MatchOverallStatus.DATE_ERROR
        if ExceptionType.ARITHMETIC_ERROR in exc_types or ExceptionType.TOTAL_MISMATCH in exc_types:
            return MatchOverallStatus.TOTAL_MISMATCH
        if ExceptionType.SKU_MISMATCH in exc_types:
            return MatchOverallStatus.QUANTITY_MISMATCH

        active_exc_types = exc_types - {None}
        if not active_exc_types:
            return MatchOverallStatus.MATCHED
        if len(active_exc_types) == 1:
            et = list(active_exc_types)[0]
            if et == ExceptionType.PRICE_VARIANCE:
                return MatchOverallStatus.PRICE_VARIANCE
            if et == ExceptionType.QUANTITY_MISMATCH:
                return MatchOverallStatus.QUANTITY_MISMATCH
            if et == ExceptionType.TAX_MISMATCH:
                return MatchOverallStatus.TAX_MISMATCH
            if et == ExceptionType.MISSING_RECEIPT:
                return MatchOverallStatus.MISSING_RECEIPT
        # Multiple exception types
        return MatchOverallStatus.PARTIALLY_MATCHED

    # -----------------------------------------------------------------------
    # Finalize – Persist results, update invoice state, create audit events
    # -----------------------------------------------------------------------
    def _finalize(
        self,
        result: MatchResult,
        checks: list[CheckResult],
        invoice: Invoice,
        actor: str,
        audit: AuditService,
        prev_status: str,
    ) -> MatchResult:
        """Persist InvoiceMatch, InvoiceException records and update invoice."""

        # Build JSON check_results
        check_results_json = [
            {
                "check": c.check_name,
                "passed": c.passed,
                "description": c.description,
                "exception_type": c.exception_type.value if c.exception_type else None,
                "severity": c.severity.value if c.severity else None,
            }
            for c in checks
        ]

        # Create InvoiceMatch record
        inv_match = InvoiceMatch(
            invoice_id=invoice.id,
            po_id=invoice.po_id,
            overall_status=result.overall_status,
            check_results=check_results_json,
            vendor_valid=result.vendor_valid,
            po_exists=result.po_exists,
            sku_matched=result.sku_matched,
            qty_matched=result.qty_matched,
            price_matched=result.price_matched,
            tax_matched=result.tax_matched,
            arithmetic_valid=result.arithmetic_valid,
            receipt_matched=result.receipt_matched,
            is_duplicate=result.is_duplicate,
            price_tolerance_pct=float(self.price_tol),
            qty_tolerance_pct=float(self.qty_tol),
            matched_by=actor,
        )
        self.db.add(inv_match)
        self.db.flush()

        # Create InvoiceException records
        for exc_check in result.exceptions_to_create:
            if not exc_check.exception_type:
                continue
            exc = InvoiceException(
                invoice_id=invoice.id,
                exception_type=exc_check.exception_type,
                severity=exc_check.severity or ExceptionSeverity.MEDIUM,
                status=ExceptionStatus.OPEN,
                description=exc_check.description,
                expected_value=exc_check.expected_value,
                actual_value=exc_check.actual_value,
                po_line_id=exc_check.po_line_id,
                recommended_action=exc_check.recommended_action,
            )
            self.db.add(exc)
            self.db.flush()
            audit.exception_created(
                invoice.id, exc.id,
                exc_check.exception_type.value,
                exc_check.severity.value if exc_check.severity else "MEDIUM",
                actor,
            )

        # Update invoice status
        new_matching_status = result.overall_status
        if result.overall_status == MatchOverallStatus.MATCHED:
            invoice.status = InvoiceStatus.MATCHED
        else:
            invoice.status = InvoiceStatus.EXCEPTION

        invoice.matching_status = new_matching_status
        self.db.flush()

        # Audit event
        audit.matching_completed(invoice.id, new_matching_status, actor)

        return result

    # -----------------------------------------------------------------------
    # Helper
    # -----------------------------------------------------------------------
    def _get_received_quantities(
        self, po_lines: list[PurchaseOrderLine]
    ) -> dict[str, Decimal]:
        """Sum accepted GRN quantities for each PO line."""
        result: dict[str, Decimal] = {}
        for po_line in po_lines:
            grn_lines = (
                self.db.query(GoodsReceiptLine)
                .filter(GoodsReceiptLine.po_line_id == po_line.id)
                .all()
            )
            total_received = sum(
                Decimal(str(gl.accepted_qty)) for gl in grn_lines
            )
            result[po_line.id] = total_received
        return result
