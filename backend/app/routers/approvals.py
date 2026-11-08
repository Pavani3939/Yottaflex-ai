"""YottaPay AI – Approvals Router (Full)"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.approval import Approval
from app.models.approval_history import ApprovalHistory
from app.approvals.approval_service import ApprovalService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/approvals")

class DecisionRequest(BaseModel):
    notes: str = ""

def _ad(a):
    return {"id": a.id, "invoice_id": a.invoice_id,
            "status": a.status.value if hasattr(a.status, 'value') else a.status,
            "requested_at": str(a.requested_at), "requested_by": a.requested_by,
            "reviewed_at": str(a.reviewed_at) if a.reviewed_at else None,
            "reviewed_by": a.reviewed_by, "decision_notes": a.decision_notes,
            "approval_level": a.approval_level, "next_approver": a.next_approver}

def _hd(h):
    return {"id": h.id, "action": h.action.value if hasattr(h.action, 'value') else h.action,
            "actor": h.actor, "comment": h.comment,
            "previous_status": h.previous_status, "new_status": h.new_status,
            "created_at": str(h.created_at)}

@router.get("")
def list_approvals(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
                   status_filter: Optional[str] = Query(None, alias="status"),
                   db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    q = db.query(Approval)
    if status_filter: q = q.filter(Approval.status == status_filter)
    total = q.count()
    items = q.order_by(Approval.requested_at.desc()).offset(skip).limit(limit).all()
    return {"items": [_ad(a) for a in items], "total": total, "skip": skip, "limit": limit}

@router.get("/{approval_id}")
def get_approval(approval_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    a = db.query(Approval).filter(Approval.id == approval_id).first()
    if not a: raise HTTPException(status_code=404, detail="Approval not found.")
    r = _ad(a)
    r["history"] = [_hd(h) for h in db.query(ApprovalHistory).filter(ApprovalHistory.approval_id == approval_id).order_by(ApprovalHistory.created_at.desc()).all()]
    return r

@router.post("/request/{invoice_id}", status_code=201)
def request_approval(invoice_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    svc = ApprovalService(db)
    a = svc.request_approval(invoice_id, current_user["username"])
    return _ad(a)

@router.post("/{approval_id}/approve")
def approve(approval_id: int, body: DecisionRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    svc = ApprovalService(db)
    a = svc.approve(approval_id, current_user["username"], body.notes)
    return _ad(a)

@router.post("/{approval_id}/reject")
def reject(approval_id: int, body: DecisionRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    svc = ApprovalService(db)
    a = svc.reject(approval_id, current_user["username"], body.notes)
    return _ad(a)

@router.post("/{approval_id}/hold")
def hold(approval_id: int, body: DecisionRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    svc = ApprovalService(db)
    a = svc.hold(approval_id, current_user["username"], body.notes)
    return _ad(a)
