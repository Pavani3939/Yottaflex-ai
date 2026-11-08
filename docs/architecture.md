# YottaPay AI – System Architecture

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                            │
│  (Vite + React 18 + Tailwind CSS + Recharts + Lucide Icons)     │
│                                                                  │
│  Pages: Dashboard | Vendors | POs | GRNs | Invoices |           │
│         Matching | Exceptions | Approvals | Payments |          │
│         Analytics | Audit | Settings | Login                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │  Axios REST (HTTP/JSON)
                           │  Base URL: http://localhost:8001/api
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  (Python 3.11 + FastAPI + Uvicorn + SQLAlchemy 2.0)            │
│                                                                  │
│  Routers:                                                        │
│    /api/vendors          /api/purchase-orders                   │
│    /api/goods-receipts   /api/invoices                          │
│    /api/matching         /api/exceptions                        │
│    /api/approvals        /api/payments                          │
│    /api/analytics        /api/audit-events                      │
│                                                                  │
│  Business Logic Services:                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  InvoiceExtractor  │  Three-Way Matching Engine          │   │
│  │  DuplicateDetector │  ExceptionRouter                    │   │
│  │  ApprovalService   │  PaymentService                     │   │
│  │  AuditService      │  AnalyticsService                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │  SQLAlchemy ORM (PyMySQL driver)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MySQL 8.0 Database                           │
│  Schema: yottapay                                                │
│                                                                  │
│  Core Tables:                                                    │
│    vendors               purchase_orders                         │
│    purchase_order_lines  goods_receipts                          │
│    goods_receipt_lines   invoices                                │
│    invoice_lines         approvals                               │
│    payments                                                      │
│                                                                  │
│  Supporting Tables:                                              │
│    invoice_matches       invoice_exceptions                      │
│    audit_events          approval_history                        │
│    invoice_documents                                             │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Component Responsibilities

| Component | Responsibility |
|---|---|
| React Frontend | UI rendering, user interaction, API consumption, state management |
| FastAPI Backend | REST API handling, business logic orchestration, authentication |
| Matching Engine | Three-way PO/GRN/Invoice comparison with configurable tolerances |
| Extraction Service | PDF/OCR/Gemini-assisted invoice field extraction |
| Exception Router | Anomaly detection, exception creation, severity classification |
| Approval Service | Workflow management, eligibility checks, state transitions |
| Payment Service | Readiness evaluation, simulated payment processing |
| Audit Service | Immutable event log, state transition recording |
| Analytics Service | Aggregated metrics, charts data, reporting |
| MySQL Database | Persistent storage of all business entities and events |

## 3. Data Flow: Invoice Processing Pipeline

```
Invoice Upload / Manual Entry
          │
          ▼
  InvoiceExtractor (PDF/OCR/Gemini)
          │ Extracted Fields
          ▼
  Field Validation (Pydantic + Business Rules)
          │ Validated Invoice
          ▼
  Invoice Record Saved  ──► AuditEvent: INVOICE_CREATED
          │
          ▼
  Three-Way Matching Engine
     ├── Vendor Validation
     ├── PO Existence Check
     ├── PO Line Matching (SKU, Qty, Price)
     ├── GRN Quantity Verification
     ├── Tax Code & Amount Validation
     ├── Invoice Arithmetic Check
     └── Duplicate Detection
          │ Match Result
          ▼
  Match Result Persisted ──► AuditEvent: MATCHING_COMPLETED
          │
     ┌────┴────┐
     │         │
  MATCHED   EXCEPTIONS
     │         │
     │    ExceptionRouter
     │         │ Exception Records Created
     │         ▼
     │    Exception Management ──► AuditEvent: EXCEPTION_CREATED
     │         │
     │    [Analyst Resolves]  ──► AuditEvent: EXCEPTION_RESOLVED
     │         │
     └────┬────┘
          │
          ▼
  Approval Eligibility Check
          │ Eligible?
          ▼
  Approval Workflow ──► AuditEvent: APPROVAL_REQUESTED / APPROVED / REJECTED
          │ APPROVED
          ▼
  Payment Readiness Evaluation
          │ READY?
          ▼
  Payment Processing (Simulated) ──► AuditEvent: PAYMENT_PROCESSED
```

## 4. Security Considerations

- API keys stored in `.env` file, never committed to git
- Backend reads credentials via `python-dotenv`
- Frontend never receives raw API keys
- Demo authentication using JWT (HS256, 30-min expiry)
- CORS allows `http://localhost:5174` and `http://localhost:5173` in development

## 5. Technology Decisions

| Decision | Choice | Rationale |
|---|---|---|
| ORM | SQLAlchemy 2.0 declarative | Type-safe, migration-ready |
| DB Driver | PyMySQL | Pure Python, MySQL 8 compatible |
| PDF Processing | PyMuPDF (fitz) | Fast, reliable text extraction |
| OCR | pytesseract + Tesseract | Open-source, local OCR |
| AI Extraction | Google Gemini 1.5 Flash | Optional; falls back gracefully |
| Frontend Build | Vite | Fast HMR, modern ESM bundling |
| State Management | React Context + hooks | Lightweight, no Redux overhead |
| Charts | Recharts | React-native, Tailwind-compatible |
