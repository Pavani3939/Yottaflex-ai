"""YottaPay AI – Exceptions Router (Full)"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.invoice_exception import InvoiceException
from app.exceptions.exception_service import ExceptionService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/exceptions")

class ResolveRequest(BaseModel):
    resolution_notes: str
    waive: bool = False

class AssignRequest(BaseModel):
    assigned_to: str

def _ed(e):
    return {"id": e.id, "invoice_id": e.invoice_id,
            "exception_type": e.exception_type.value if hasattr(e.exception_type, 'value') else e.exception_type,
            "severity": e.severity.value if hasattr(e.severity, 'value') else e.severity,
            "status": e.status.value if hasattr(e.status, 'value') else e.status,
            "description": e.description, "expected_value": e.expected_value,
            "actual_value": e.actual_value, "po_line_id": e.po_line_id,
            "recommended_action": e.recommended_action, "assigned_to": e.assigned_to,
            "resolved_by": e.resolved_by, "resolved_at": str(e.resolved_at) if e.resolved_at else None,
            "resolution_notes": e.resolution_notes, "created_at": str(e.created_at)}

@router.get("")
def list_exceptions(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
                    invoice_id: Optional[str] = None, exception_type: Optional[str] = None,
                    severity: Optional[str] = None, status_filter: Optional[str] = Query(None, alias="status"),
                    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    q = db.query(InvoiceException)
    if invoice_id: q = q.filter(InvoiceException.invoice_id == invoice_id)
    if exception_type: q = q.filter(InvoiceException.exception_type == exception_type)
    if severity: q = q.filter(InvoiceException.severity == severity)
    if status_filter: q = q.filter(InvoiceException.status == status_filter)
    total = q.count()
    items = q.order_by(InvoiceException.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": [_ed(e) for e in items], "total": total, "skip": skip, "limit": limit}

@router.get("/{exc_id}")
def get_exception(exc_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    e = db.query(InvoiceException).filter(InvoiceException.id == exc_id).first()
    if not e: raise HTTPException(status_code=404, detail="Exception not found.")
    return _ed(e)

@router.put("/{exc_id}/resolve")
def resolve_exception(exc_id: int, body: ResolveRequest, db: Session = Depends(get_db),
                      current_user: dict = Depends(get_current_user)):
    svc = ExceptionService(db)
    e = svc.resolve(exc_id, body.resolution_notes, current_user["username"], body.waive)
    return _ed(e)

@router.put("/{exc_id}/assign")
def assign_exception(exc_id: int, body: AssignRequest, db: Session = Depends(get_db),
                     current_user: dict = Depends(get_current_user)):
    svc = ExceptionService(db)
    e = svc.assign(exc_id, body.assigned_to, current_user["username"])
    return _ed(e)
