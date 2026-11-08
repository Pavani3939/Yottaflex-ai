"""YottaPay AI – Audit Events Router (Full)"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.audit_event import AuditEvent
from app.routers.auth import get_current_user

router = APIRouter(prefix="/audit-events")

def _ed(e):
    return {"id": e.id, "event_id": e.event_id,
            "entity_type": e.entity_type.value if hasattr(e.entity_type, 'value') else e.entity_type,
            "entity_id": e.entity_id, "event_type": e.event_type,
            "previous_state": e.previous_state, "new_state": e.new_state,
            "actor": e.actor, "description": e.description, "metadata": e.metadata_,
            "created_at": str(e.created_at)}

@router.get("")
def list_events(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                entity_type: Optional[str] = None, entity_id: Optional[str] = None,
                event_type: Optional[str] = None, db: Session = Depends(get_db),
                current_user: dict = Depends(get_current_user)):
    q = db.query(AuditEvent)
    if entity_type: q = q.filter(AuditEvent.entity_type == entity_type)
    if entity_id: q = q.filter(AuditEvent.entity_id == entity_id)
    if event_type: q = q.filter(AuditEvent.event_type == event_type)
    total = q.count()
    items = q.order_by(AuditEvent.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": [_ed(e) for e in items], "total": total, "skip": skip, "limit": limit}

@router.get("/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    e = db.query(AuditEvent).filter(AuditEvent.event_id == event_id).first()
    if not e: raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")
    return _ed(e)
