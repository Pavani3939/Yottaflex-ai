# YottaPay AI – Complete Database Schema

## Database: `yottapay`
## Charset: utf8mb4 | Collation: utf8mb4_unicode_ci

---

## Entity Relationship Summary

```
vendors ──< purchase_orders ──< purchase_order_lines
                                        │
                                        ├──< goods_receipt_lines >── goods_receipts
                                        │
                                        └──< invoice_lines >── invoices >── vendors
                                                     │
                                                     ├──< invoice_matches
                                                     ├──< invoice_exceptions
                                                     ├──< approvals ──< approval_history
                                                     ├──< payments
                                                     └──< invoice_documents

audit_events (polymorphic – references any entity)
```

---

## TABLE 1: vendors

```sql
CREATE TABLE vendors (
    id              VARCHAR(12)     NOT NULL,           -- VND-00001
    name            VARCHAR(255)    NOT NULL,
    code            VARCHAR(10)     NOT NULL UNIQUE,    -- VND01, VND02 …
    email           VARCHAR(255)    NOT NULL,
    phone           VARCHAR(30),
    address_line1   VARCHAR(255),
    address_line2   VARCHAR(255),
    city            VARCHAR(100),
    state           VARCHAR(100),
    country         VARCHAR(100)    NOT NULL DEFAULT 'India',
    pincode         VARCHAR(20),
    gstin           VARCHAR(20)     UNIQUE,             -- Indian GST number
    pan             VARCHAR(20)     UNIQUE,
    bank_account    VARCHAR(30),
    bank_ifsc       VARCHAR(15),
    payment_terms   INT             NOT NULL DEFAULT 30, -- days
    currency        VARCHAR(3)      NOT NULL DEFAULT 'INR',
    status          ENUM('ACTIVE','INACTIVE','BLACKLISTED','PENDING_REVIEW')
                    NOT NULL DEFAULT 'ACTIVE',
    category        VARCHAR(100),
    contact_person  VARCHAR(255),
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
    is_deleted      TINYINT(1)      NOT NULL DEFAULT 0,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Lifecycle States:** ACTIVE → INACTIVE | BLACKLISTED | PENDING_REVIEW

---

## TABLE 2: purchase_orders

```sql
CREATE TABLE purchase_orders (
    id              VARCHAR(20)     NOT NULL,           -- PO-2026-000001
    vendor_id       VARCHAR(12)     NOT NULL,
    order_date      DATE            NOT NULL,
    delivery_date   DATE,
    status          ENUM('DRAFT','OPEN','PARTIALLY_RECEIVED','FULLY_RECEIVED',
                         'CLOSED','CANCELLED')
                    NOT NULL DEFAULT 'OPEN',
    currency        VARCHAR(3)      NOT NULL DEFAULT 'INR',
    subtotal        DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    tax_amount      DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    total_amount    DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    department      VARCHAR(100),
    created_by      VARCHAR(100)    NOT NULL DEFAULT 'system',
    approved_by     VARCHAR(100),
    notes           TEXT,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_po_vendor FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## TABLE 3: purchase_order_lines

```sql
CREATE TABLE purchase_order_lines (
    id              VARCHAR(30)     NOT NULL,           -- POLINE-PO-2026-000001-01
    po_id           VARCHAR(20)     NOT NULL,
    line_number     INT             NOT NULL,
    sku             VARCHAR(50)     NOT NULL,
    description     VARCHAR(500)    NOT NULL,
    uom             VARCHAR(20)     NOT NULL DEFAULT 'EA',  -- Each, Kg, Litre …
    quantity        DECIMAL(12,3)   NOT NULL,
    unit_price      DECIMAL(12,2)   NOT NULL,
    tax_code        VARCHAR(20)     NOT NULL DEFAULT 'GST18',
    tax_rate        DECIMAL(5,2)    NOT NULL DEFAULT 18.00, -- percentage
    line_subtotal   DECIMAL(15,2)   NOT NULL,
    tax_amount      DECIMAL(15,2)   NOT NULL,
    line_total      DECIMAL(15,2)   NOT NULL,
    received_qty    DECIMAL(12,3)   NOT NULL DEFAULT 0.000,
    status          ENUM('OPEN','PARTIALLY_RECEIVED','FULLY_RECEIVED','CLOSED','CANCELLED')
                    NOT NULL DEFAULT 'OPEN',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_po_line (po_id, line_number),
    CONSTRAINT fk_poline_po FOREIGN KEY (po_id) REFERENCES purchase_orders(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## TABLE 4: goods_receipts

```sql
CREATE TABLE goods_receipts (
    id              VARCHAR(20)     NOT NULL,           -- GRN-2026-000001
    po_id           VARCHAR(20)     NOT NULL,
    vendor_id       VARCHAR(12)     NOT NULL,
    receipt_date    DATE            NOT NULL,
    warehouse       VARCHAR(100),
    received_by     VARCHAR(100)    NOT NULL DEFAULT 'warehouse_staff',
    status          ENUM('DRAFT','RECEIVED','PARTIALLY_ACCEPTED','ACCEPTED',
                         'REJECTED','CLOSED')
                    NOT NULL DEFAULT 'RECEIVED',
    notes           TEXT,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_grn_po     FOREIGN KEY (po_id)     REFERENCES purchase_orders(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_grn_vendor FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## TABLE 5: goods_receipt_lines

```sql
CREATE TABLE goods_receipt_lines (
    id              VARCHAR(40)     NOT NULL,           -- GRNL-GRN-2026-000001-01
    grn_id          VARCHAR(20)     NOT NULL,
    po_line_id      VARCHAR(30)     NOT NULL,
    line_number     INT             NOT NULL,
    sku             VARCHAR(50)     NOT NULL,
    description     VARCHAR(500),
    uom             VARCHAR(20)     NOT NULL DEFAULT 'EA',
    received_qty    DECIMAL(12,3)   NOT NULL,
    accepted_qty    DECIMAL(12,3)   NOT NULL,
    rejected_qty    DECIMAL(12,3)   NOT NULL DEFAULT 0.000,
    unit_price      DECIMAL(12,2)   NOT NULL,
    batch_number    VARCHAR(100),
    expiry_date     DATE,
    status          ENUM('PENDING','ACCEPTED','PARTIALLY_ACCEPTED','REJECTED')
                    NOT NULL DEFAULT 'ACCEPTED',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_grn_line (grn_id, line_number),
    CONSTRAINT fk_grnl_grn    FOREIGN KEY (grn_id)     REFERENCES goods_receipts(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_grnl_poline FOREIGN KEY (po_line_id) REFERENCES purchase_order_lines(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## TABLE 6: invoices

```sql
CREATE TABLE invoices (
    id                  VARCHAR(35)     NOT NULL,       -- INV-VND00001-2026-000001
    invoice_number      VARCHAR(100)    NOT NULL,       -- Vendor's own invoice number
    vendor_id           VARCHAR(12)     NOT NULL,
    po_id               VARCHAR(20),                    -- nullable (non-PO invoices)
    invoice_date        DATE            NOT NULL,
    due_date            DATE,
    currency            VARCHAR(3)      NOT NULL DEFAULT 'INR',
    subtotal            DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    tax_amount          DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    total_amount        DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    calculated_subtotal DECIMAL(15,2),                  -- derived from lines
    calculated_tax      DECIMAL(15,2),
    calculated_total    DECIMAL(15,2),
    status              ENUM('DRAFT','PENDING_EXTRACTION','EXTRACTED','PENDING_MATCH',
                             'MATCHING','MATCHED','EXCEPTION','APPROVED','REJECTED',
                             'PAYMENT_READY','PAYMENT_PROCESSING','PAID','CANCELLED')
                        NOT NULL DEFAULT 'DRAFT',
    matching_status     ENUM('NOT_STARTED','IN_PROGRESS','MATCHED','PRICE_VARIANCE',
                             'QUANTITY_MISMATCH','TAX_MISMATCH','MISSING_RECEIPT',
                             'DUPLICATE','VENDOR_ERROR','TOTAL_MISMATCH','DATE_ERROR',
                             'PARTIALLY_MATCHED','FAILED')
                        NOT NULL DEFAULT 'NOT_STARTED',
    source              ENUM('UPLOAD_PDF','UPLOAD_IMAGE','MANUAL','API')
                        NOT NULL DEFAULT 'MANUAL',
    extraction_confidence DECIMAL(5,2),                 -- 0.00 to 100.00
    is_duplicate        TINYINT(1)      NOT NULL DEFAULT 0,
    duplicate_of        VARCHAR(35),                    -- self-referential FK
    notes               TEXT,
    created_by          VARCHAR(100)    NOT NULL DEFAULT 'system',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_invoice_number_vendor (invoice_number, vendor_id),
    CONSTRAINT fk_inv_vendor   FOREIGN KEY (vendor_id)   REFERENCES vendors(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_inv_po       FOREIGN KEY (po_id)       REFERENCES purchase_orders(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_inv_dup      FOREIGN KEY (duplicate_of) REFERENCES invoices(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Lifecycle States:** DRAFT → PENDING_EXTRACTION → EXTRACTED → PENDING_MATCH → MATCHING → MATCHED | EXCEPTION → APPROVED | REJECTED → PAYMENT_READY → PAYMENT_PROCESSING → PAID

---

## TABLE 7: invoice_lines

```sql
CREATE TABLE invoice_lines (
    id              VARCHAR(50)     NOT NULL,           -- INVL-<invoice_id>-01
    invoice_id      VARCHAR(35)     NOT NULL,
    line_number     INT             NOT NULL,
    po_line_id      VARCHAR(30),                        -- nullable
    sku             VARCHAR(50),
    description     VARCHAR(500)    NOT NULL,
    uom             VARCHAR(20)     NOT NULL DEFAULT 'EA',
    quantity        DECIMAL(12,3)   NOT NULL,
    unit_price      DECIMAL(12,2)   NOT NULL,
    tax_code        VARCHAR(20)     NOT NULL DEFAULT 'GST18',
    tax_rate        DECIMAL(5,2)    NOT NULL DEFAULT 18.00,
    line_subtotal   DECIMAL(15,2)   NOT NULL,
    tax_amount      DECIMAL(15,2)   NOT NULL,
    line_total      DECIMAL(15,2)   NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_invline (invoice_id, line_number),
    CONSTRAINT fk_invl_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_invl_poline  FOREIGN KEY (po_line_id) REFERENCES purchase_order_lines(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## TABLE 8: invoice_matches

```sql
CREATE TABLE invoice_matches (
    id              BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
    invoice_id      VARCHAR(35)      NOT NULL,
    po_id           VARCHAR(20),
    grn_id          VARCHAR(20),
    match_run_at    DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    overall_status  ENUM('MATCHED','PRICE_VARIANCE','QUANTITY_MISMATCH','TAX_MISMATCH',
                         'MISSING_RECEIPT','DUPLICATE','VENDOR_ERROR','TOTAL_MISMATCH',
                         'DATE_ERROR','PARTIALLY_MATCHED','FAILED')
                    NOT NULL,
    -- Checks performed (JSON blob for detailed check results)
    check_results   JSON,
    -- Individual check flags
    vendor_valid        TINYINT(1) NOT NULL DEFAULT 0,
    po_exists           TINYINT(1) NOT NULL DEFAULT 0,
    sku_matched         TINYINT(1) NOT NULL DEFAULT 0,
    qty_matched         TINYINT(1) NOT NULL DEFAULT 0,
    price_matched       TINYINT(1) NOT NULL DEFAULT 0,
    tax_matched         TINYINT(1) NOT NULL DEFAULT 0,
    arithmetic_valid    TINYINT(1) NOT NULL DEFAULT 0,
    receipt_matched     TINYINT(1) NOT NULL DEFAULT 0,
    is_duplicate        TINYINT(1) NOT NULL DEFAULT 0,
    -- Tolerances applied
    price_tolerance_pct DECIMAL(5,2) DEFAULT 2.00,
    qty_tolerance_pct   DECIMAL(5,2) DEFAULT 0.00,
    matched_by      VARCHAR(100) NOT NULL DEFAULT 'system',
    notes           TEXT,
    PRIMARY KEY (id),
    CONSTRAINT fk_match_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_match_po      FOREIGN KEY (po_id)      REFERENCES purchase_orders(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_match_grn     FOREIGN KEY (grn_id)     REFERENCES goods_receipts(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## TABLE 9: invoice_exceptions

```sql
CREATE TABLE invoice_exceptions (
    id              BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
    invoice_id      VARCHAR(35)      NOT NULL,
    exception_type  ENUM('PRICE_VARIANCE','QUANTITY_MISMATCH','TAX_MISMATCH',
                         'MISSING_RECEIPT','DUPLICATE','VENDOR_ERROR','TOTAL_MISMATCH',
                         'DATE_ERROR','ARITHMETIC_ERROR','SKU_MISMATCH','OTHER')
                    NOT NULL,
    severity        ENUM('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL DEFAULT 'MEDIUM',
    status          ENUM('OPEN','IN_REVIEW','RESOLVED','WAIVED','ESCALATED')
                    NOT NULL DEFAULT 'OPEN',
    description     TEXT            NOT NULL,
    expected_value  VARCHAR(255),
    actual_value    VARCHAR(255),
    po_line_id      VARCHAR(30),
    grn_line_id     VARCHAR(40),
    recommended_action TEXT,
    assigned_to     VARCHAR(100),
    resolved_by     VARCHAR(100),
    resolved_at     DATETIME,
    resolution_notes TEXT,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_exc_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## TABLE 10: approvals

```sql
CREATE TABLE approvals (
    id              BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
    invoice_id      VARCHAR(35)      NOT NULL UNIQUE,  -- one approval record per invoice
    status          ENUM('PENDING','APPROVED','REJECTED','ON_HOLD','CANCELLED')
                    NOT NULL DEFAULT 'PENDING',
    requested_at    DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    requested_by    VARCHAR(100)     NOT NULL DEFAULT 'system',
    reviewed_at     DATETIME,
    reviewed_by     VARCHAR(100),
    decision_notes  TEXT,
    approval_level  INT              NOT NULL DEFAULT 1,
    next_approver   VARCHAR(100),
    PRIMARY KEY (id),
    CONSTRAINT fk_appr_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## TABLE 11: approval_history

```sql
CREATE TABLE approval_history (
    id              BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
    approval_id     BIGINT UNSIGNED  NOT NULL,
    invoice_id      VARCHAR(35)      NOT NULL,
    action          ENUM('SUBMITTED','APPROVED','REJECTED','ON_HOLD','ESCALATED',
                         'COMMENT_ADDED','CANCELLED') NOT NULL,
    actor           VARCHAR(100)     NOT NULL,
    comment         TEXT,
    previous_status VARCHAR(50),
    new_status      VARCHAR(50),
    created_at      DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_apphist_appr    FOREIGN KEY (approval_id) REFERENCES approvals(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_apphist_invoice FOREIGN KEY (invoice_id)  REFERENCES invoices(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## TABLE 12: payments

```sql
CREATE TABLE payments (
    id              BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
    invoice_id      VARCHAR(35)      NOT NULL UNIQUE,
    vendor_id       VARCHAR(12)      NOT NULL,
    status          ENUM('NOT_READY','READY_FOR_PAYMENT','PAYMENT_PROCESSING',
                         'PAID','FAILED','BLOCKED','REVERSED')
                    NOT NULL DEFAULT 'NOT_READY',
    amount          DECIMAL(15,2)    NOT NULL,
    currency        VARCHAR(3)       NOT NULL DEFAULT 'INR',
    payment_method  ENUM('BANK_TRANSFER','CHEQUE','UPI','NEFT','RTGS','IMPS')
                    DEFAULT 'NEFT',
    payment_reference VARCHAR(100),
    scheduled_date  DATE,
    processed_at    DATETIME,
    processed_by    VARCHAR(100),
    failure_reason  TEXT,
    created_at      DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_pay_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_pay_vendor  FOREIGN KEY (vendor_id)  REFERENCES vendors(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## TABLE 13: audit_events

```sql
CREATE TABLE audit_events (
    id              BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
    event_id        VARCHAR(50)      NOT NULL UNIQUE,  -- EVT-<uuid>
    entity_type     ENUM('VENDOR','PURCHASE_ORDER','GOODS_RECEIPT','INVOICE',
                         'INVOICE_LINE','INVOICE_MATCH','INVOICE_EXCEPTION',
                         'APPROVAL','PAYMENT') NOT NULL,
    entity_id       VARCHAR(50)      NOT NULL,
    event_type      VARCHAR(100)     NOT NULL,         -- INVOICE_CREATED, etc.
    previous_state  VARCHAR(100),
    new_state       VARCHAR(100),
    actor           VARCHAR(100)     NOT NULL DEFAULT 'system',
    description     TEXT,
    metadata        JSON,                              -- extra key-value context
    ip_address      VARCHAR(45),
    created_at      DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_audit_entity (entity_type, entity_id),
    INDEX idx_audit_event_type (event_type),
    INDEX idx_audit_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## TABLE 14: invoice_documents

```sql
CREATE TABLE invoice_documents (
    id              BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
    invoice_id      VARCHAR(35)      NOT NULL,
    file_name       VARCHAR(255)     NOT NULL,
    file_path       VARCHAR(500)     NOT NULL,
    file_type       ENUM('PDF','JPEG','PNG','TIFF','OTHER') NOT NULL DEFAULT 'PDF',
    file_size_bytes BIGINT,
    extraction_method ENUM('PYMUPDF','TESSERACT_OCR','GEMINI_AI','MANUAL') NOT NULL,
    extraction_status ENUM('PENDING','SUCCESS','FAILED','PARTIAL') NOT NULL DEFAULT 'PENDING',
    raw_text        LONGTEXT,
    extracted_json  JSON,
    upload_at       DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_doc_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## Cardinality Summary

| Relationship | Type | Notes |
|---|---|---|
| Vendor → PurchaseOrder | 1 : Many | A vendor can have many POs |
| Vendor → Invoice | 1 : Many | A vendor can submit many invoices |
| PurchaseOrder → PurchaseOrderLine | 1 : Many | 1–8 lines per PO |
| PurchaseOrder → GoodsReceipt | 1 : Many | PO can have multiple partial GRNs |
| GoodsReceipt → GoodsReceiptLine | 1 : Many | One line per PO line received |
| PurchaseOrderLine → GoodsReceiptLine | 1 : Many | A PO line can appear in multiple GRNs |
| Invoice → InvoiceLine | 1 : Many | At least one line per invoice |
| Invoice → InvoiceMatch | 1 : Many | Matching can be re-run |
| Invoice → InvoiceException | 1 : Many | Multiple exceptions per invoice |
| Invoice → Approval | 1 : 1 | One active approval record |
| Approval → ApprovalHistory | 1 : Many | Full audit trail |
| Invoice → Payment | 1 : 1 | One payment record per invoice |
| Invoice → InvoiceDocument | 1 : Many | Multiple supporting files |
