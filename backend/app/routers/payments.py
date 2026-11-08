"""YottaPay AI – Payments Router (Full)"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.payment import Payment
from app.payments.payment_service import PaymentService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/payments")

def _pd(p):
    return {"id": p.id, "invoice_id": p.invoice_id, "vendor_id": p.vendor_id,
            "status": p.status.value if hasattr(p.status, 'value') else p.status,
            "amount": float(p.amount), "currency": p.currency,
            "payment_method": p.payment_method.value if p.payment_method and hasattr(p.payment_method, 'value') else p.payment_method,
            "payment_reference": p.payment_reference,
            "scheduled_date": str(p.scheduled_date) if p.scheduled_date else None,
            "processed_at": str(p.processed_at) if p.processed_at else None,
            "processed_by": p.processed_by, "failure_reason": p.failure_reason,
            "created_at": str(p.created_at)}

@router.get("")
def list_payments(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
                  status_filter: Optional[str] = Query(None, alias="status"),
                  vendor_id: Optional[str] = None, db: Session = Depends(get_db),
                  current_user: dict = Depends(get_current_user)):
    q = db.query(Payment)
    if status_filter: q = q.filter(Payment.status == status_filter)
    if vendor_id: q = q.filter(Payment.vendor_id == vendor_id)
    total = q.count()
    items = q.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": [_pd(p) for p in items], "total": total, "skip": skip, "limit": limit}

@router.get("/{payment_id}")
def get_payment(payment_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p: raise HTTPException(status_code=404, detail="Payment not found.")
    return _pd(p)

@router.post("/evaluate/{invoice_id}")
def evaluate_readiness(invoice_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    svc = PaymentService(db)
    p = svc.evaluate_readiness(invoice_id, current_user["username"])
    return _pd(p)

@router.post("/process/{invoice_id}")
def process_payment(invoice_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    svc = PaymentService(db)
    p = svc.process_payment(invoice_id, current_user["username"])
    return _pd(p)
