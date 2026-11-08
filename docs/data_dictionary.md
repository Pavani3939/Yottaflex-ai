# YottaPay AI – Data Dictionary

## Entity: vendors

| Column | Type | Nullable | PK/FK | Description |
|---|---|---|---|---|
| id | VARCHAR(12) | NO | PK | System-generated vendor ID (VND-00001) |
| name | VARCHAR(255) | NO | — | Full legal business name |
| code | VARCHAR(10) | NO | UNIQUE | Short code used in invoice IDs |
| email | VARCHAR(255) | NO | — | Primary contact email |
| phone | VARCHAR(30) | YES | — | Contact phone number |
| address_line1 | VARCHAR(255) | YES | — | Registered address line 1 |
| address_line2 | VARCHAR(255) | YES | — | Address line 2 |
| city | VARCHAR(100) | YES | — | City |
| state | VARCHAR(100) | YES | — | Indian state |
| country | VARCHAR(100) | NO | — | Default: India |
| pincode | VARCHAR(20) | YES | — | 6-digit postal code |
| gstin | VARCHAR(20) | YES | UNIQUE | Indian GST Identification Number |
| pan | VARCHAR(20) | YES | UNIQUE | Permanent Account Number |
| bank_account | VARCHAR(30) | YES | — | Bank account number |
| bank_ifsc | VARCHAR(15) | YES | — | IFSC code for bank transfer |
| payment_terms | INT | NO | — | Net payment days (default 30) |
| currency | VARCHAR(3) | NO | — | ISO 4217 currency code (INR) |
| status | ENUM | NO | — | ACTIVE/INACTIVE/BLACKLISTED/PENDING_REVIEW |
| category | VARCHAR(100) | YES | — | Vendor category (IT, Logistics, etc.) |
| contact_person | VARCHAR(255) | YES | — | Primary contact name |
| created_at | DATETIME | NO | — | Record creation timestamp |
| updated_at | DATETIME | NO | — | Last modification timestamp |
| is_deleted | TINYINT(1) | NO | — | Soft delete flag |

---

## Entity: purchase_orders

| Column | Type | Nullable | PK/FK | Description |
|---|---|---|---|---|
| id | VARCHAR(20) | NO | PK | System PO ID (PO-2026-000001) |
| vendor_id | VARCHAR(12) | NO | FK → vendors | Ordering vendor |
| order_date | DATE | NO | — | Date PO was raised |
| delivery_date | DATE | YES | — | Expected delivery date |
| status | ENUM | NO | — | DRAFT/OPEN/PARTIALLY_RECEIVED/FULLY_RECEIVED/CLOSED/CANCELLED |
| currency | VARCHAR(3) | NO | — | Currency code |
| subtotal | DECIMAL(15,2) | NO | — | Sum of line subtotals |
| tax_amount | DECIMAL(15,2) | NO | — | Sum of line taxes |
| total_amount | DECIMAL(15,2) | NO | — | subtotal + tax_amount |
| department | VARCHAR(100) | YES | — | Requesting department |
| created_by | VARCHAR(100) | NO | — | User who created PO |
| approved_by | VARCHAR(100) | YES | — | User who approved PO |
| notes | TEXT | YES | — | Free-text notes |
| created_at | DATETIME | NO | — | Record creation timestamp |
| updated_at | DATETIME | NO | — | Last modification timestamp |

---

## Entity: purchase_order_lines

| Column | Type | Nullable | PK/FK | Description |
|---|---|---|---|---|
| id | VARCHAR(30) | NO | PK | Line ID (POLINE-PO-2026-000001-01) |
| po_id | VARCHAR(20) | NO | FK → purchase_orders | Parent PO |
| line_number | INT | NO | — | Sequential line number within PO |
| sku | VARCHAR(50) | NO | — | Stock Keeping Unit |
| description | VARCHAR(500) | NO | — | Product description |
| uom | VARCHAR(20) | NO | — | Unit of Measure |
| quantity | DECIMAL(12,3) | NO | — | Ordered quantity |
| unit_price | DECIMAL(12,2) | NO | — | Agreed unit price |
| tax_code | VARCHAR(20) | NO | — | Tax code (GST18, GST5, etc.) |
| tax_rate | DECIMAL(5,2) | NO | — | Tax rate percentage |
| line_subtotal | DECIMAL(15,2) | NO | — | quantity × unit_price |
| tax_amount | DECIMAL(15,2) | NO | — | line_subtotal × tax_rate/100 |
| line_total | DECIMAL(15,2) | NO | — | line_subtotal + tax_amount |
| received_qty | DECIMAL(12,3) | NO | — | Cumulative received quantity |
| status | ENUM | NO | — | OPEN/PARTIALLY_RECEIVED/FULLY_RECEIVED/CLOSED/CANCELLED |
| created_at | DATETIME | NO | — | Record creation timestamp |

---

## Entity: invoices

| Column | Type | Nullable | PK/FK | Description |
|---|---|---|---|---|
| id | VARCHAR(35) | NO | PK | System invoice ID |
| invoice_number | VARCHAR(100) | NO | UNIQUE+vendor | Vendor's own invoice number |
| vendor_id | VARCHAR(12) | NO | FK → vendors | Submitting vendor |
| po_id | VARCHAR(20) | YES | FK → purchase_orders | Linked PO (nullable) |
| invoice_date | DATE | NO | — | Invoice issuance date |
| due_date | DATE | YES | — | Payment due date |
| currency | VARCHAR(3) | NO | — | Currency code |
| subtotal | DECIMAL(15,2) | NO | — | Stated subtotal on invoice |
| tax_amount | DECIMAL(15,2) | NO | — | Stated tax on invoice |
| total_amount | DECIMAL(15,2) | NO | — | Stated grand total |
| calculated_subtotal | DECIMAL(15,2) | YES | — | Computed from lines |
| calculated_tax | DECIMAL(15,2) | YES | — | Computed from lines |
| calculated_total | DECIMAL(15,2) | YES | — | Computed total |
| status | ENUM | NO | — | Full invoice lifecycle state |
| matching_status | ENUM | NO | — | Matching engine result |
| source | ENUM | NO | — | How invoice was submitted |
| extraction_confidence | DECIMAL(5,2) | YES | — | AI extraction confidence % |
| is_duplicate | TINYINT(1) | NO | — | Duplicate flag |
| duplicate_of | VARCHAR(35) | YES | FK → invoices | Original invoice if duplicate |
| notes | TEXT | YES | — | Free-text notes |
| created_by | VARCHAR(100) | NO | — | Submitting user |
| created_at | DATETIME | NO | — | Record creation timestamp |
| updated_at | DATETIME | NO | — | Last modification timestamp |

---

## Entity: invoice_exceptions

| Column | Type | Nullable | PK/FK | Description |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | NO | PK | Auto-increment |
| invoice_id | VARCHAR(35) | NO | FK → invoices | Parent invoice |
| exception_type | ENUM | NO | — | Type of exception |
| severity | ENUM | NO | — | LOW/MEDIUM/HIGH/CRITICAL |
| status | ENUM | NO | — | OPEN/IN_REVIEW/RESOLVED/WAIVED/ESCALATED |
| description | TEXT | NO | — | Human-readable description |
| expected_value | VARCHAR(255) | YES | — | What was expected |
| actual_value | VARCHAR(255) | YES | — | What was found |
| po_line_id | VARCHAR(30) | YES | — | Relevant PO line |
| grn_line_id | VARCHAR(40) | YES | — | Relevant GRN line |
| recommended_action | TEXT | YES | — | Suggested resolution |
| assigned_to | VARCHAR(100) | YES | — | Analyst username |
| resolved_by | VARCHAR(100) | YES | — | Resolver username |
| resolved_at | DATETIME | YES | — | Resolution timestamp |
| resolution_notes | TEXT | YES | — | Resolution explanation |
| created_at | DATETIME | NO | — | Creation timestamp |
| updated_at | DATETIME | NO | — | Last update timestamp |

---

## Entity: audit_events

| Column | Type | Nullable | PK/FK | Description |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | NO | PK | Auto-increment |
| event_id | VARCHAR(50) | NO | UNIQUE | EVT-{UUID4} |
| entity_type | ENUM | NO | — | Type of entity affected |
| entity_id | VARCHAR(50) | NO | — | ID of affected entity |
| event_type | VARCHAR(100) | NO | — | Event name constant |
| previous_state | VARCHAR(100) | YES | — | State before event |
| new_state | VARCHAR(100) | YES | — | State after event |
| actor | VARCHAR(100) | NO | — | Username or 'system' |
| description | TEXT | YES | — | Human-readable description |
| metadata | JSON | YES | — | Extra context |
| ip_address | VARCHAR(45) | YES | — | Client IP if applicable |
| created_at | DATETIME | NO | — | Event timestamp |

---

## Enum Value Reference

### vendors.status
`ACTIVE` | `INACTIVE` | `BLACKLISTED` | `PENDING_REVIEW`

### purchase_orders.status
`DRAFT` | `OPEN` | `PARTIALLY_RECEIVED` | `FULLY_RECEIVED` | `CLOSED` | `CANCELLED`

### invoices.status
`DRAFT` | `PENDING_EXTRACTION` | `EXTRACTED` | `PENDING_MATCH` | `MATCHING` | `MATCHED` | `EXCEPTION` | `APPROVED` | `REJECTED` | `PAYMENT_READY` | `PAYMENT_PROCESSING` | `PAID` | `CANCELLED`

### invoices.matching_status
`NOT_STARTED` | `IN_PROGRESS` | `MATCHED` | `PRICE_VARIANCE` | `QUANTITY_MISMATCH` | `TAX_MISMATCH` | `MISSING_RECEIPT` | `DUPLICATE` | `VENDOR_ERROR` | `TOTAL_MISMATCH` | `DATE_ERROR` | `PARTIALLY_MATCHED` | `FAILED`

### invoice_exceptions.exception_type
`PRICE_VARIANCE` | `QUANTITY_MISMATCH` | `TAX_MISMATCH` | `MISSING_RECEIPT` | `DUPLICATE` | `VENDOR_ERROR` | `TOTAL_MISMATCH` | `DATE_ERROR` | `ARITHMETIC_ERROR` | `SKU_MISMATCH` | `OTHER`

### invoice_exceptions.severity
`LOW` | `MEDIUM` | `HIGH` | `CRITICAL`

### approvals.status
`PENDING` | `APPROVED` | `REJECTED` | `ON_HOLD` | `CANCELLED`

### payments.status
`NOT_READY` | `READY_FOR_PAYMENT` | `PAYMENT_PROCESSING` | `PAID` | `FAILED` | `BLOCKED` | `REVERSED`
