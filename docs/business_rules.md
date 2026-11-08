# YottaPay AI – Business Rules

## 1. ID Generation Rules

### Vendor ID
- Format: `VND-{5-digit zero-padded sequence}`
- Example: `VND-00001`, `VND-00300`
- Immutable after creation.

### Vendor Code
- Format: `VND{5-digit}` — used in invoice IDs
- Example: `VND00001`

### Purchase Order ID
- Format: `PO-{YEAR}-{6-digit sequence}`
- Example: `PO-2026-000001`
- Year derived from `order_date`.
- Immutable after creation.

### Purchase Order Line ID
- Format: `POLINE-{po_id}-{2-digit line number}`
- Example: `POLINE-PO-2026-000001-01`

### Goods Receipt ID
- Format: `GRN-{YEAR}-{6-digit sequence}`
- Example: `GRN-2026-000001`

### Goods Receipt Line ID
- Format: `GRNL-{grn_id}-{2-digit line number}`
- Example: `GRNL-GRN-2026-000001-01`

### Invoice ID
- Format: `INV-{vendor_code}-{YEAR}-{6-digit sequence}`
- Example: `INV-VND00001-2026-000001`
- Vendor code is derived from the vendor at time of creation.
- Immutable after creation.

### Invoice Line ID
- Format: `INVL-{invoice_id}-{2-digit line number}`
- Example: `INVL-INV-VND00001-2026-000001-01`

### Audit Event ID
- Format: `EVT-{UUID4}`

---

## 2. Vendor Business Rules

| Rule ID | Rule Description |
|---|---|
| VND-001 | Vendor status must be ACTIVE to submit invoices. |
| VND-002 | BLACKLISTED or INACTIVE vendors result in VENDOR_ERROR exception. |
| VND-003 | GSTIN must follow Indian GST format: `[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}` |
| VND-004 | A vendor's payment_terms define the due date: `invoice_date + payment_terms days`. |
| VND-005 | Currency defaults to INR. Cross-currency invoices require explicit conversion (out of scope for v1). |

---

## 3. Purchase Order Business Rules

| Rule ID | Rule Description |
|---|---|
| PO-001 | PO must exist in the system to perform three-way matching. Missing PO → VENDOR_ERROR. |
| PO-002 | PO must belong to the same vendor as the invoice. |
| PO-003 | PO status must be OPEN or PARTIALLY_RECEIVED to accept new invoices. |
| PO-004 | A PO is FULLY_RECEIVED when all PO lines reach received_qty ≥ quantity. |
| PO-005 | PO total = sum of all PO line totals. |
| PO-006 | A CANCELLED PO cannot accept invoices or GRNs. |
| PO-007 | PO line quantity must be > 0. |
| PO-008 | Invoice date must be ≥ PO order_date. Violation → DATE_ERROR. |

---

## 4. Goods Receipt Business Rules

| Rule ID | Rule Description |
|---|---|
| GRN-001 | GRN must reference an existing PO. |
| GRN-002 | GRN vendor must match PO vendor. |
| GRN-003 | A GRN line accepted_qty cannot exceed PO line quantity minus previously received quantity. |
| GRN-004 | If no GRN exists for a PO line and an invoice references it, raise MISSING_RECEIPT. |
| GRN-005 | Total received across all GRNs for a PO line = sum of GRN line accepted_qty values. |
| GRN-006 | GRN receipt_date must be ≥ PO order_date. |

---

## 5. Invoice Business Rules

| Rule ID | Rule Description |
|---|---|
| INV-001 | Invoice number must be unique per vendor (composite unique key: invoice_number + vendor_id). |
| INV-002 | Invoice date must not be in the future beyond 7 days. |
| INV-003 | Invoice date must be ≥ PO order_date. Violation → DATE_ERROR exception. |
| INV-004 | Invoice subtotal = sum of all invoice line subtotals. Mismatch → TOTAL_MISMATCH. |
| INV-005 | Invoice tax = sum of all invoice line tax amounts. Mismatch → ARITHMETIC_ERROR. |
| INV-006 | Invoice total = subtotal + tax. Mismatch → TOTAL_MISMATCH. |
| INV-007 | Invoice currency must match PO currency. |
| INV-008 | Each invoice line subtotal = quantity × unit_price (rounded to 2 decimal places). |
| INV-009 | Each invoice line tax = subtotal × (tax_rate / 100) (rounded to 2 decimal places). |
| INV-010 | Each invoice line total = subtotal + tax (rounded to 2 decimal places). |

---

## 6. Three-Way Matching Business Rules

### Matching Tolerances (Configurable)
| Parameter | Default Value |
|---|---|
| Price variance tolerance | 2.0% |
| Quantity tolerance | 0.0% (strict) |
| Tax amount tolerance | 0.5% |
| Total amount tolerance | 0.5% |

### Matching Checks (in order)

| Check | Rule | Outcome on Failure |
|---|---|---|
| A. Vendor Validation | Vendor must be ACTIVE | VENDOR_ERROR |
| B. PO Existence | Referenced PO must exist and belong to vendor | VENDOR_ERROR |
| C. PO Status | PO must be OPEN or PARTIALLY_RECEIVED | DATE_ERROR |
| D. Date Check | invoice_date ≥ po.order_date | DATE_ERROR |
| E. Duplicate Check | Same invoice_number+vendor_id already exists | DUPLICATE |
| F. SKU Matching | Invoice line SKU must exist in PO lines | QUANTITY_MISMATCH |
| G. Quantity Check | Invoice qty ≤ PO qty within tolerance | QUANTITY_MISMATCH |
| H. Price Check | |invoice_unit_price - po_unit_price| / po_unit_price ≤ tolerance | PRICE_VARIANCE |
| I. Receipt Check | GRN accepted_qty ≥ invoice qty for each line | MISSING_RECEIPT |
| J. Tax Code Check | Invoice tax_code = PO line tax_code | TAX_MISMATCH |
| K. Tax Amount Check | Invoice tax amount within tolerance of calculated | TAX_MISMATCH |
| L. Arithmetic Check | Invoice totals reconcile (INV-004 to INV-010) | TOTAL_MISMATCH |

### Overall Matching Status Logic
```
if any DUPLICATE exception:          → DUPLICATE
elif VENDOR_ERROR exceptions:         → VENDOR_ERROR
elif DATE_ERROR exceptions:           → DATE_ERROR
elif TOTAL_MISMATCH exceptions:       → TOTAL_MISMATCH
elif all checks pass:                 → MATCHED
elif PRICE_VARIANCE only:             → PRICE_VARIANCE
elif QUANTITY_MISMATCH only:          → QUANTITY_MISMATCH
elif TAX_MISMATCH only:               → TAX_MISMATCH
elif MISSING_RECEIPT only:            → MISSING_RECEIPT
elif multiple exception types:        → PARTIALLY_MATCHED
else:                                 → FAILED
```

---

## 7. Exception Management Rules

### Exception Severity Classification

| Exception Type | Severity | Blocking? |
|---|---|---|
| DUPLICATE | CRITICAL | YES |
| VENDOR_ERROR | CRITICAL | YES |
| DATE_ERROR | HIGH | YES |
| QUANTITY_MISMATCH (>10%) | HIGH | YES |
| QUANTITY_MISMATCH (≤10%) | MEDIUM | NO |
| PRICE_VARIANCE (>5%) | HIGH | YES |
| PRICE_VARIANCE (≤5%) | MEDIUM | NO |
| TOTAL_MISMATCH | CRITICAL | YES |
| MISSING_RECEIPT | HIGH | YES |
| TAX_MISMATCH | MEDIUM | NO |
| ARITHMETIC_ERROR | CRITICAL | YES |
| SKU_MISMATCH | HIGH | YES |

### Exception Resolution Rules
- EXC-001: Only OPEN or IN_REVIEW exceptions can be resolved.
- EXC-002: Resolution requires a resolution_notes entry.
- EXC-003: Resolution creates an audit event: EXCEPTION_RESOLVED.
- EXC-004: Waived exceptions must be approved by a manager role.
- EXC-005: After all blocking exceptions are resolved, re-run matching engine.

---

## 8. Approval Workflow Rules

### Eligibility Criteria (ALL must be true)
- APR-001: Invoice status must be MATCHED or PARTIALLY_MATCHED with no blocking exceptions.
- APR-002: No OPEN exceptions with severity CRITICAL or HIGH that are blocking.
- APR-003: Invoice arithmetic must be valid (checks INV-004 to INV-010).
- APR-004: Vendor must be ACTIVE.
- APR-005: An approval record must not already exist in APPROVED status for this invoice.

### Approval Levels (Simple single-level for v1)
| Invoice Amount | Required Approver Role |
|---|---|
| < ₹10,000 | ops_analyst |
| ₹10,000 – ₹1,00,000 | finance_manager |
| > ₹1,00,000 | vp_finance |

### State Transitions
```
(invoice MATCHED + no blocking exceptions)
         │
         ▼
   PENDING ──► APPROVED ──► (Payment Readiness Evaluated)
         │
         ├──► REJECTED ──► (Invoice status = REJECTED)
         │
         └──► ON_HOLD  ──► (Manual review required)
```

---

## 9. Payment Readiness Rules

### Eligibility Criteria (ALL must be true)
- PAY-001: Invoice status = APPROVED.
- PAY-002: Approval record status = APPROVED.
- PAY-003: Matching status = MATCHED (or PARTIALLY_MATCHED with all exceptions resolved).
- PAY-004: No OPEN exceptions of any severity.
- PAY-005: Vendor status = ACTIVE.
- PAY-006: Vendor has valid bank_account and bank_ifsc.
- PAY-007: Invoice total > 0.

### Payment Status Transitions
```
NOT_READY → READY_FOR_PAYMENT → PAYMENT_PROCESSING → PAID
                                                    └──► FAILED → (retry or BLOCKED)
```

---

## 10. Duplicate Detection Rules

- DUP-001: Exact duplicate: same invoice_number + same vendor_id → DUPLICATE (CRITICAL).
- DUP-002: Near-duplicate: same vendor_id + same total + invoice date within 7 days → flag for review (MEDIUM).
- DUP-003: A duplicate invoice is marked `is_duplicate = TRUE` and `duplicate_of = <original_invoice_id>`.
- DUP-004: A duplicate invoice cannot proceed to approval or payment.

---

## 11. Audit Event Rules

- AUD-001: Every state change must generate an audit_event record.
- AUD-002: Audit events are immutable — never updated or deleted.
- AUD-003: Every event must record: entity_type, entity_id, event_type, previous_state, new_state, actor, timestamp.
- AUD-004: event_id must be globally unique (UUID4 prefixed with EVT-).

### Required Event Types
| Event Type | Triggered When |
|---|---|
| INVOICE_CREATED | Invoice record inserted |
| INVOICE_EXTRACTED | Extraction completes |
| MATCHING_STARTED | Matching engine begins |
| MATCHING_COMPLETED | Matching engine finishes |
| EXCEPTION_CREATED | Exception record inserted |
| EXCEPTION_RESOLVED | Exception status = RESOLVED or WAIVED |
| APPROVAL_REQUESTED | Approval record created |
| INVOICE_APPROVED | Approval status = APPROVED |
| INVOICE_REJECTED | Approval status = REJECTED |
| PAYMENT_READY | Payment status = READY_FOR_PAYMENT |
| PAYMENT_PROCESSING | Payment processing begins |
| PAYMENT_PROCESSED | Payment status = PAID |
| PAYMENT_FAILED | Payment status = FAILED |

---

## 12. Data Validation Rules for Synthetic Generator

| Field | Validation |
|---|---|
| vendor.gstin | 15-char GST format regex |
| po.order_date | Must be in past (before seed date) |
| po_line.quantity | > 0, ≤ 10,000 |
| po_line.unit_price | > 0, ≤ 10,000,000 |
| grn.receipt_date | ≥ po.order_date |
| invoice.invoice_date | ≥ po.order_date |
| invoice_line.quantity | > 0 |
| invoice_line.unit_price | > 0 |
| invoice total | = subtotal + tax (within ₹0.01) |
| Duplicate injection | 5% of invoices flagged via is_duplicate + duplicate_of |
