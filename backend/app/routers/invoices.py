"""
YottaPay AI – Invoices Router (Full Implementation)
"""
import os
from datetime import date, timedelta
from typing import Optional

from fastapi import (
    APIRouter, Depends, File, Form, HTTPException,
    Query, UploadFile, status,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.invoice import Invoice, InvoiceStatus, MatchingStatus, InvoiceSource
from app.models.invoice_line import InvoiceLine
from app.models.invoice_document import InvoiceDocument, DocumentFileType, ExtractionMethod, ExtractionStatus
from app.models.vendor import Vendor
from app.audit.audit_service import AuditService
from app.extraction.extractor import extract_invoice
from app.utils.id_generator import invoice_id as make_invoice_id, invoice_line_id
from app.utils.arithmetic import round2
from app.config import get_settings
from app.routers.auth import get_current_user

router = APIRouter(prefix="/invoices")
settings = get_settings()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class InvoiceLineCreate(BaseModel):
    sku: Optional[str] = None
    description: str
    uom: str = "EA"
    quantity: float
    unit_price: float
    tax_code: str = "GST18"
    tax_rate: float = 18.0
    po_line_id: Optional[str] = None


class InvoiceCreate(BaseModel):
    invoice_number: str
    vendor_id: str
    po_id: Optional[str] = None
    invoice_date: date
    currency: str = "INR"
    lines: list[InvoiceLineCreate]
    notes: Optional[str] = None


class InvoiceLineOut(BaseModel):
    id: str
    line_number: int
    sku: Optional[str]
    description: str
    quantity: float
    unit_price: float
    tax_code: str
    tax_rate: float
    line_subtotal: float
    tax_amount: float
    line_total: float

    class Config:
        from_attributes = True


class InvoiceOut(BaseModel):
    id: str
    invoice_number: str
    vendor_id: str
    po_id: Optional[str]
    invoice_date: date
    due_date: Optional[date]
    currency: str
    subtotal: float
    tax_amount: float
    total_amount: float
    status: str
    matching_status: str
    source: str
    is_duplicate: bool
    created_at: str
    lines: list[InvoiceLineOut] = []

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# GET /invoices
# ---------------------------------------------------------------------------
@router.get("")
def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    matching_status: Optional[str] = Query(None),
    vendor_id: Optional[str] = Query(None),
    is_duplicate: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    q = db.query(Invoice)
    if status:
        q = q.filter(Invoice.status == status)
    if matching_status:
        q = q.filter(Invoice.matching_status == matching_status)
    if vendor_id:
        q = q.filter(Invoice.vendor_id == vendor_id)
    if is_duplicate is not None:
        q = q.filter(Invoice.is_duplicate == is_duplicate)

    total = q.count()
    invoices = q.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": [_invoice_to_dict(inv) for inv in invoices],
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": (skip + limit) < total,
    }


# ---------------------------------------------------------------------------
# POST /invoices  (manual entry)
# ---------------------------------------------------------------------------
@router.post("", status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Validate vendor
    vendor = db.query(Vendor).filter(Vendor.id == payload.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor {payload.vendor_id} not found.")

    # Check duplicate invoice_number per vendor
    existing = db.query(Invoice).filter(
        Invoice.invoice_number == payload.invoice_number,
        Invoice.vendor_id == payload.vendor_id,
    ).first()
    is_dup = existing is not None
    dup_of = existing.id if is_dup else None

    # Generate invoice ID
    count = db.query(Invoice).filter(Invoice.vendor_id == payload.vendor_id).count()
    year = payload.invoice_date.year
    inv_id = make_invoice_id(vendor.code, year, count + 1)

    # Calculate totals from lines
    subtotal_sum = round2(sum(l.quantity * l.unit_price for l in payload.lines))
    tax_sum = round2(sum(
        round2(l.quantity * l.unit_price) * round2(l.tax_rate) / 100
        for l in payload.lines
    ))
    total_sum = round2(subtotal_sum + tax_sum)

    # Due date
    due_date = payload.invoice_date + timedelta(days=vendor.payment_terms)

    inv = Invoice(
        id=inv_id,
        invoice_number=payload.invoice_number,
        vendor_id=payload.vendor_id,
        po_id=payload.po_id,
        invoice_date=payload.invoice_date,
        due_date=due_date,
        currency=payload.currency,
        subtotal=float(subtotal_sum),
        tax_amount=float(tax_sum),
        total_amount=float(total_sum),
        calculated_subtotal=float(subtotal_sum),
        calculated_tax=float(tax_sum),
        calculated_total=float(total_sum),
        status=InvoiceStatus.PENDING_MATCH,
        matching_status=MatchingStatus.NOT_STARTED,
        source=InvoiceSource.MANUAL,
        is_duplicate=is_dup,
        duplicate_of=dup_of,
        notes=payload.notes,
        created_by=current_user["username"],
    )
    db.add(inv)
    db.flush()

    # Create invoice lines
    for ln, line_data in enumerate(payload.lines, start=1):
        sub = round2(line_data.quantity * line_data.unit_price)
        tax = round2(sub * round2(line_data.tax_rate) / 100)
        total_line = round2(sub + tax)

        inv_line = InvoiceLine(
            id=invoice_line_id(inv_id, ln),
            invoice_id=inv_id,
            line_number=ln,
            po_line_id=line_data.po_line_id,
            sku=line_data.sku,
            description=line_data.description,
            uom=line_data.uom,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            tax_code=line_data.tax_code,
            tax_rate=line_data.tax_rate,
            line_subtotal=float(sub),
            tax_amount=float(tax),
            line_total=float(total_line),
        )
        db.add(inv_line)

    db.flush()

    # Audit
    audit = AuditService(db)
    audit.invoice_created(inv_id, actor=current_user["username"])

    return _invoice_to_dict(inv)


# ---------------------------------------------------------------------------
# POST /invoices/upload  (file upload + extraction)
# ---------------------------------------------------------------------------
@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    file: UploadFile = File(...),
    vendor_id: str = Form(...),
    po_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Validate file type
    fname = file.filename.lower()
    if fname.endswith(".pdf"):
        file_type = DocumentFileType.PDF
    elif fname.endswith((".jpg", ".jpeg")):
        file_type = DocumentFileType.JPEG
    elif fname.endswith(".png"):
        file_type = DocumentFileType.PNG
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, JPEG or PNG.")

    # Check file size
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit.")

    # Validate vendor
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor {vendor_id} not found.")

    # Save file to disk
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    import uuid
    safe_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # Extract fields
    extracted = extract_invoice(content, file_type.value, use_gemini=True)

    # Create a draft invoice from extracted data
    inv_date = date.today()
    if extracted.get("invoice_date"):
        try:
            from datetime import datetime
            inv_date = datetime.strptime(extracted["invoice_date"], "%Y-%m-%d").date()
        except Exception:
            pass

    count = db.query(Invoice).filter(Invoice.vendor_id == vendor_id).count()
    inv_id = make_invoice_id(vendor.code, inv_date.year, count + 1)
    inv_number = extracted.get("invoice_number") or f"EXTRACTED-{inv_id}"
    due_date = inv_date + timedelta(days=vendor.payment_terms)

    inv = Invoice(
        id=inv_id,
        invoice_number=inv_number,
        vendor_id=vendor_id,
        po_id=po_id,
        invoice_date=inv_date,
        due_date=due_date,
        currency=extracted.get("currency", "INR"),
        subtotal=extracted.get("subtotal") or 0,
        tax_amount=extracted.get("tax_amount") or 0,
        total_amount=extracted.get("total_amount") or 0,
        status=InvoiceStatus.EXTRACTED,
        matching_status=MatchingStatus.NOT_STARTED,
        source=InvoiceSource.UPLOAD_PDF if file_type == DocumentFileType.PDF else InvoiceSource.UPLOAD_IMAGE,
        extraction_confidence=extracted.get("confidence", 0),
        created_by=current_user["username"],
    )
    db.add(inv)
    db.flush()

    # Save document record
    doc = InvoiceDocument(
        invoice_id=inv_id,
        file_name=file.filename,
        file_path=file_path,
        file_type=file_type,
        file_size_bytes=len(content),
        extraction_method=ExtractionMethod(extracted.get("extraction_method", "PYMUPDF")),
        extraction_status=ExtractionStatus.SUCCESS if extracted.get("invoice_number") else ExtractionStatus.PARTIAL,
        raw_text=extracted.get("raw_text", "")[:65535],
        extracted_json=extracted,
    )
    db.add(doc)
    db.flush()

    # Audit
    audit = AuditService(db)
    audit.invoice_created(inv_id, actor=current_user["username"])
    audit.invoice_extracted(
        inv_id,
        extracted.get("extraction_method", "PYMUPDF"),
        extracted.get("confidence", 0),
        actor=current_user["username"],
    )

    return {
        "invoice_id": inv_id,
        "extracted_fields": extracted,
        "message": "Invoice uploaded and extracted. Please review and confirm the extracted fields.",
    }


# ---------------------------------------------------------------------------
# GET /invoices/{id}
# ---------------------------------------------------------------------------
@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found.")

    result = _invoice_to_dict(inv)
    result["lines"] = [
        {
            "id": l.id, "line_number": l.line_number, "sku": l.sku,
            "description": l.description, "quantity": float(l.quantity),
            "unit_price": float(l.unit_price), "tax_code": l.tax_code,
            "tax_rate": float(l.tax_rate), "line_subtotal": float(l.line_subtotal),
            "tax_amount": float(l.tax_amount), "line_total": float(l.line_total),
        }
        for l in inv.lines
    ]
    result["exceptions"] = [
        {
            "id": e.id, "exception_type": e.exception_type.value,
            "severity": e.severity.value, "status": e.status.value,
            "description": e.description,
            "expected_value": e.expected_value, "actual_value": e.actual_value,
            "recommended_action": e.recommended_action,
            "assigned_to": e.assigned_to, "resolved_by": e.resolved_by,
        }
        for e in inv.exceptions
    ]
    if inv.approval:
        result["approval"] = {
            "id": inv.approval.id,
            "status": inv.approval.status.value,
            "requested_by": inv.approval.requested_by,
            "reviewed_by": inv.approval.reviewed_by,
            "decision_notes": inv.approval.decision_notes,
        }
    if inv.payment:
        result["payment"] = {
            "id": inv.payment.id,
            "status": inv.payment.status.value,
            "amount": float(inv.payment.amount),
            "payment_reference": inv.payment.payment_reference,
        }
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _invoice_to_dict(inv: Invoice) -> dict:
    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "vendor_id": inv.vendor_id,
        "po_id": inv.po_id,
        "invoice_date": str(inv.invoice_date),
        "due_date": str(inv.due_date) if inv.due_date else None,
        "currency": inv.currency,
        "subtotal": float(inv.subtotal),
        "tax_amount": float(inv.tax_amount),
        "total_amount": float(inv.total_amount),
        "status": inv.status.value,
        "matching_status": inv.matching_status.value,
        "source": inv.source.value,
        "is_duplicate": inv.is_duplicate,
        "duplicate_of": inv.duplicate_of,
        "extraction_confidence": float(inv.extraction_confidence) if inv.extraction_confidence else None,
        "created_by": inv.created_by,
        "created_at": str(inv.created_at),
    }
