"""YottaPay AI – Vendors Router (Full Implementation)"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.vendor import Vendor, VendorStatus
from app.audit.audit_service import AuditService
from app.models.audit_event import AuditEntityType
from app.utils.id_generator import vendor_id as make_vid, vendor_code as make_vcode
from app.routers.auth import get_current_user

router = APIRouter(prefix="/vendors")

class VendorCreate(BaseModel):
    name: str; email: str; phone: Optional[str] = None
    address_line1: Optional[str] = None; city: Optional[str] = None
    state: Optional[str] = None; country: str = "India"; pincode: Optional[str] = None
    gstin: Optional[str] = None; pan: Optional[str] = None
    bank_account: Optional[str] = None; bank_ifsc: Optional[str] = None
    payment_terms: int = 30; currency: str = "INR"
    category: Optional[str] = None; contact_person: Optional[str] = None

class VendorUpdate(BaseModel):
    name: Optional[str] = None; email: Optional[str] = None; phone: Optional[str] = None
    address_line1: Optional[str] = None; city: Optional[str] = None
    state: Optional[str] = None; pincode: Optional[str] = None
    bank_account: Optional[str] = None; bank_ifsc: Optional[str] = None
    payment_terms: Optional[int] = None; status: Optional[str] = None
    category: Optional[str] = None; contact_person: Optional[str] = None

def _vd(v):
    return {"id": v.id, "name": v.name, "code": v.code, "email": v.email,
            "phone": v.phone, "address_line1": v.address_line1, "city": v.city,
            "state": v.state, "country": v.country, "pincode": v.pincode,
            "gstin": v.gstin, "pan": v.pan, "bank_account": v.bank_account,
            "bank_ifsc": v.bank_ifsc, "payment_terms": v.payment_terms,
            "currency": v.currency, "status": v.status.value if hasattr(v.status, 'value') else v.status,
            "category": v.category, "contact_person": v.contact_person,
            "created_at": str(v.created_at), "updated_at": str(v.updated_at)}

@router.get("")
def list_vendors(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
                 search: Optional[str] = None, status_filter: Optional[str] = Query(None, alias="status"),
                 db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    q = db.query(Vendor).filter(Vendor.is_deleted == False)
    if search:
        q = q.filter(or_(Vendor.name.ilike(f"%{search}%"), Vendor.code.ilike(f"%{search}%")))
    if status_filter:
        q = q.filter(Vendor.status == status_filter)
    total = q.count()
    items = q.order_by(Vendor.name).offset(skip).limit(limit).all()
    return {"items": [_vd(v) for v in items], "total": total, "skip": skip, "limit": limit, "has_more": (skip+limit)<total}

@router.post("", status_code=201)
def create_vendor(p: VendorCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    seq = db.query(Vendor).count() + 1
    vid = make_vid(seq); vcode = make_vcode(seq)
    while db.query(Vendor).filter(Vendor.id == vid).first():
        seq += 1; vid = make_vid(seq); vcode = make_vcode(seq)
    v = Vendor(id=vid, code=vcode, **p.dict())
    db.add(v); db.flush()
    AuditService(db).log(AuditEntityType.VENDOR, vid, "VENDOR_CREATED", actor=current_user["username"], new_state="ACTIVE")
    return _vd(v)

@router.get("/{vendor_id}")
def get_vendor(vendor_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    v = db.query(Vendor).filter(Vendor.id == vendor_id, Vendor.is_deleted == False).first()
    if not v: raise HTTPException(status_code=404, detail=f"Vendor {vendor_id} not found.")
    return _vd(v)

@router.put("/{vendor_id}")
def update_vendor(vendor_id: str, p: VendorUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    v = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not v: raise HTTPException(status_code=404, detail=f"Vendor {vendor_id} not found.")
    data = p.dict(exclude_none=True)
    for k, val in data.items():
        if k == "status": setattr(v, k, VendorStatus(val))
        else: setattr(v, k, val)
    db.flush()
    return _vd(v)

@router.delete("/{vendor_id}", status_code=204)
def delete_vendor(vendor_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    v = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not v: raise HTTPException(status_code=404, detail=f"Vendor {vendor_id} not found.")
    v.is_deleted = True; v.status = VendorStatus.INACTIVE; db.flush()
