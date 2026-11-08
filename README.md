# YottaPay AI

**Intelligent Invoice Processing & Payment Automation Platform**

> Built for the YottaFlex AI 72-Hour Coding Challenge — Associate AI Forward Deployed Engineer

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
[![MySQL 8.0](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://mysql.com)

---

## 📋 Overview

YottaPay AI automates the full invoice-to-payment lifecycle for enterprise procurement. It ingests vendor invoices (PDF/image/manual), extracts structured data via OCR and AI, performs three-way matching against Purchase Orders and Goods Receipt Notes, routes exceptions for human review, manages multi-level approval workflows, and evaluates payment readiness — all with a complete audit trail.

### Key Capabilities

| Module | Description |
|--------|-------------|
| **Invoice Intake** | Upload PDF/image invoices or enter data manually |
| **Data Extraction** | PyMuPDF text extraction + Tesseract OCR + optional Gemini AI |
| **3-Way Matching** | 11 automated checks against POs and GRNs with configurable tolerances |
| **Duplicate Detection** | Identifies duplicate invoice_number + vendor_id combinations |
| **Exception Management** | Auto-creates exceptions for mismatches; assign, resolve, or waive |
| **Approval Workflow** | Multi-level approval with approve/reject/hold actions |
| **Payment Readiness** | 7-rule evaluation engine determining if invoices are ready to pay |
| **Analytics Dashboard** | Real-time metrics via Recharts — matching rates, exception distributions, volumes |
| **Audit Trail** | Immutable event log for every system action |
| **Reporting** | Monthly volume trends, vendor performance, payment pipeline |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  Tailwind CSS  •  Recharts  •  React Router  •  Axios   │
├─────────────────────────────────────────────────────────┤
│                    FastAPI Backend                        │
│  SQLAlchemy ORM  •  Pydantic  •  JWT Auth  •  Loguru    │
├─────────────────────────────────────────────────────────┤
│                     MySQL 8.0                            │
│  14 tables  •  FK constraints  •  indexes  •  enums     │
└─────────────────────────────────────────────────────────┘
```

### Tech Stack

- **Frontend:** React 18, Tailwind CSS, Recharts, React Router v6, Axios
- **Backend:** FastAPI, SQLAlchemy 2.0, Pydantic v2, PyJWT, Loguru
- **Database:** MySQL 8.0 (required — not PostgreSQL/MongoDB/SQLite)
- **Extraction:** PyMuPDF (fitz), Tesseract OCR (pytesseract), Google Gemini API (optional)
- **Data Generation:** Faker, Pandas, NumPy (seed: `20261022`)
- **Testing:** Pytest, HTTPX, FastAPI TestClient

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ and pnpm (or npm)
- MySQL 8.0 running locally
- Tesseract OCR installed (optional, for image invoices)

### 1. Clone & Navigate

```bash
cd YottaPay-AI
```

### 2. MySQL Database Setup

```sql
-- Connect to MySQL as root
mysql -u root -p

-- Create database and user
CREATE DATABASE IF NOT EXISTS yottapay_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'yottapay'@'localhost' IDENTIFIED BY 'yottapay_pass';
GRANT ALL PRIVILEGES ON yottapay_ai.* TO 'yottapay'@'localhost';
FLUSH PRIVILEGES;
```

Or run the provided script:

```bash
mysql -u root -p < backend/create_database.sql
```

### 3. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your MySQL credentials:
#   DB_HOST=localhost
#   DB_PORT=3306
#   DB_USER=yottapay
#   DB_PASSWORD=yottapay_pass
#   DB_NAME=yottapay_ai
#   JWT_SECRET_KEY=your-secret-key-change-in-production
```

### 4. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 5. Initialize Database Tables

```bash
# From backend/
python -c "from app.database.init_db import init_db; init_db()"
```

### 6. Generate Synthetic Data

```bash
cd ../scripts

# Generate all CSV files (seed: 20261022)
python generate_data.py

# Validate data quality
python validate_data.py

# Verify reproducibility (runs twice, compares MD5)
python reproduce_data.py
```

### 7. Seed Database

```bash
python seed_database.py
```

### 8. Start Backend Server

```bash
cd ../backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

The API is now available at `http://localhost:8001`:
- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc
- **Health Check:** http://localhost:8001/health

### 9. Frontend Setup

```bash
cd ../frontend
pnpm install    # or: npm install
pnpm run dev    # or: npm run dev
```

Frontend runs at `http://localhost:5174` and proxies `/api` to the backend.

---

## 🔐 Demo Accounts

| Username | Password | Role | Access |
|----------|----------|------|--------|
| `admin` | `password123` | Admin | Full system access |
| `analyst` | `password123` | Analyst | Read-only + matching + reports |
| `finance` | `password123` | Finance | Approvals + payments + exceptions |

---

## 📊 Data Generation

The synthetic data generator creates a realistic enterprise dataset:

| Entity | Count | Description |
|--------|-------|-------------|
| Vendors | 300 | With addresses, bank details, payment terms |
| Purchase Orders | 1,500 | With 1-5 line items each |
| Goods Receipts | 1,800 | Linked to POs with receipt quantities |
| Invoices | 2,000 | With embedded anomalies (see below) |

### Anomaly Distribution (Fixed Seed: 20261022)

| Scenario | Percentage | Description |
|----------|-----------|-------------|
| Clean Match | 70% | All checks pass |
| Price Mismatch | 10% | Unit price deviates > 2% from PO |
| Quantity Mismatch | 8% | Quantity deviates > 5% from PO/GRN |
| Missing PO | 5% | References non-existent PO |
| Duplicate | 4% | Same invoice_number + vendor_id |
| Arithmetic Error | 3% | Line totals or invoice total incorrect |

### Ground Truth

`data/generated/ground_truth.csv` contains the expected anomaly label for each invoice. These labels are **never used as input features** by the matching engine — they exist solely for evaluation.

---

## 🎯 Three-Way Matching Engine

The matching engine runs 11 independent checks:

| Code | Check | Tolerance |
|------|-------|-----------|
| VND-001 | Vendor exists and is active | — |
| PO-001 | PO exists and matches vendor | — |
| DT-001 | Invoice date within PO window | 365 days |
| DUP-001 | No duplicate invoice_number + vendor_id | — |
| SKU-001 | All invoice SKUs exist in PO | — |
| QTY-001 | Quantity within tolerance | ±5% |
| PRC-001 | Unit price within tolerance | ±2% |
| GRN-001 | Goods receipt exists and matches | — |
| TAX-001 | Tax amount consistent | ±1% |
| ARI-001 | Line arithmetic (qty × price = total) | ±0.01 |
| TOT-001 | Total reconciliation (sub + tax - disc = total) | ±0.01 |

### Match Outcomes

- **FULL_MATCH** — All checks pass
- **PARTIAL_MATCH** — Minor warnings only
- **MISMATCH** — One or more checks fail → exceptions created
- **NO_MATCH** — Critical failure (missing vendor/PO)

---

## 🔄 Approval & Payment Rules

### Approval Eligibility
- Invoice must have been matched (status ≠ RECEIVED)
- No unresolved blocking exceptions
- No existing PENDING approval for the same invoice

### Payment Readiness (7 Rules)

| Rule | Condition |
|------|-----------|
| PAY-001 | Invoice status must be APPROVED |
| PAY-002 | No unresolved exceptions with severity HIGH or CRITICAL |
| PAY-003 | Matching status must be FULL_MATCH or PARTIAL_MATCH |
| PAY-004 | Vendor must be active |
| PAY-005 | Invoice not past maximum age (365 days) |
| PAY-006 | No duplicate flag |
| PAY-007 | Total amount > 0 |

---

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest -v

# Run specific test modules
pytest tests/test_id_generation.py -v
pytest tests/test_arithmetic.py -v
pytest tests/test_models.py -v
pytest tests/test_matching.py -v
pytest tests/test_api.py -v

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Modules

| Module | Tests | Description |
|--------|-------|-------------|
| `test_id_generation.py` | 14 | All ID format functions (VND, PO, GRN, INV, EVT) |
| `test_arithmetic.py` | 13 | Rounding, line totals, reconciliation, variance |
| `test_models.py` | 14 | ORM model instantiation for all 14 tables |
| `test_matching.py` | 17 | Matching engine checks for each anomaly scenario |
| `test_api.py` | 12 | Health, auth, vendor, invoice, audit API endpoints |

---

## 📁 Project Structure

```
YottaPay-AI/
├── backend/
│   ├── app/
│   │   ├── analytics/         # Analytics service
│   │   ├── approvals/         # Approval workflow service
│   │   ├── audit/             # Immutable audit trail service
│   │   ├── database/          # SQLAlchemy connection & init
│   │   ├── exceptions/        # Exception management service
│   │   ├── extraction/        # PDF/OCR/AI extraction
│   │   ├── matching/          # Three-way matching engine
│   │   ├── models/            # 14 SQLAlchemy ORM models
│   │   ├── payments/          # Payment readiness service
│   │   ├── routers/           # 11 FastAPI routers
│   │   ├── schemas/           # Pydantic response schemas
│   │   ├── utils/             # ID generation, arithmetic
│   │   ├── config.py          # Pydantic Settings
│   │   └── main.py            # FastAPI application entry
│   ├── tests/                 # Pytest test suite
│   ├── create_database.sql    # MySQL schema script
│   ├── requirements.txt       # Python dependencies
│   └── pytest.ini             # Pytest configuration
├── frontend/
│   ├── src/
│   │   ├── components/        # 8 reusable UI components
│   │   ├── context/           # Auth context provider
│   │   ├── layouts/           # MainLayout with sidebar
│   │   ├── pages/             # 15 page components
│   │   ├── services/          # API service layer (Axios)
│   │   ├── utils/             # Formatters, constants
│   │   ├── App.jsx            # Route definitions
│   │   └── main.jsx           # React entry point
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── scripts/
│   ├── generate_data.py       # Synthetic data generator
│   ├── validate_data.py       # Data quality validator
│   ├── reproduce_data.py      # Reproducibility verifier
│   └── seed_database.py       # Database seeder
├── data/
│   └── generated/             # CSV output directory
├── docs/
│   ├── architecture.md        # System architecture
│   ├── business_rules.md      # Business rules reference
│   ├── database_schema.md     # Full database schema
│   ├── data_dictionary.md     # Field definitions
│   └── evaluation.md          # Evaluation methodology
├── prompt-history/
│   └── gemini-prompts.md      # AI prompt history
├── .env.example               # Environment template
├── .gitignore
└── README.md                  # This file
```

---

## 📐 Database Schema

14 tables with full referential integrity:

```
vendors ──┬── purchase_orders ──┬── purchase_order_lines
          │                     └── goods_receipts ── goods_receipt_lines
          └── invoices ──┬── invoice_lines
                         ├── invoice_documents
                         ├── invoice_matches
                         ├── invoice_exceptions
                         ├── approvals ── approval_history
                         └── payments
                         
audit_events (standalone — immutable log)
```

See [docs/database_schema.md](docs/database_schema.md) for complete DDL and field definitions.

---

## 📈 Evaluation Metrics

The system evaluates matching accuracy against ground truth labels:

| Metric | Formula | Target |
|--------|---------|--------|
| **Precision** | TP / (TP + FP) | > 0.90 |
| **Recall** | TP / (TP + FN) | > 0.85 |
| **F1 Score** | 2 × P × R / (P + R) | > 0.87 |

Where:
- **TP** = Anomaly correctly detected
- **FP** = Clean invoice falsely flagged
- **FN** = Anomaly missed by engine

See [docs/evaluation.md](docs/evaluation.md) for methodology details.

---

## 🤖 AI Transparency

All AI prompts used during development are documented in [prompt-history/gemini-prompts.md](prompt-history/gemini-prompts.md), as required by the challenge guidelines.

---

## 📄 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/token` | Login (OAuth2 password flow) |
| `GET` | `/api/auth/me` | Current user info |
| `GET/POST` | `/api/vendors` | List / Create vendors |
| `GET/PUT` | `/api/vendors/{id}` | Get / Update vendor |
| `GET/POST` | `/api/purchase-orders` | List / Create POs |
| `GET` | `/api/purchase-orders/{id}` | Get PO with lines |
| `GET` | `/api/goods-receipts` | List GRNs |
| `GET` | `/api/goods-receipts/{id}` | Get GRN with lines |
| `GET/POST` | `/api/invoices` | List / Create invoices |
| `POST` | `/api/invoices/upload` | Upload invoice file |
| `GET` | `/api/invoices/{id}` | Get invoice detail |
| `POST` | `/api/matching/run/{id}` | Run matching for invoice |
| `GET` | `/api/matching/results/{id}` | Get latest match result |
| `GET` | `/api/matching/history/{id}` | Get match history |
| `GET` | `/api/exceptions` | List exceptions |
| `POST` | `/api/exceptions/{id}/resolve` | Resolve exception |
| `POST` | `/api/exceptions/{id}/assign` | Assign exception |
| `GET` | `/api/approvals` | List approvals |
| `POST` | `/api/approvals/{id}/approve` | Approve |
| `POST` | `/api/approvals/{id}/reject` | Reject |
| `POST` | `/api/approvals/{id}/hold` | Put on hold |
| `GET` | `/api/payments` | List payments |
| `POST` | `/api/payments/process/{id}` | Process payment |
| `GET` | `/api/analytics/*` | Dashboard, matching, exceptions, payments, volume |
| `GET` | `/api/audit-events` | List audit events |
| `GET` | `/api/audit-events/{id}` | Get audit event |

Full interactive docs at `/docs` (Swagger) and `/redoc` (ReDoc).

---

## 📝 License

Built for the YottaFlex AI Recruitment Challenge. All rights reserved.

---

*YottaPay AI — From invoice to insight, automated.*
