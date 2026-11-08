"""YottaPay AI – Purchase Orders Router (Full)"""
from typing import Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.purchase_order import PurchaseOrder, POStatus
from app.models.purchase_order_line import PurchaseOrderLine
from app.models.vendor import Vendor
from app.utils.id_generator import po_id as make_po_id, po_line_id as make_pol_id
from app.utils.arithmetic import round2
from app.routers.auth import get_current_user

router = APIRouter(prefix="/purchase-orders")

class POLineCreate(BaseModel):
    sku: str; description: str; uom: str = "EA"; quantity: float; unit_price: float
    tax_code: str = "GST18"; tax_rate: float = 18.0

class POCreate(BaseModel):
    vendor_id: str; order_date: date; delivery_date: Optional[date] = None
    department: Optional[str] = None; notes: Optional[str] = None; lines: list[POLineCreate]

def _pod(po):
    return {"id": po.id, "vendor_id": po.vendor_id, "order_date": str(po.order_date),
            "delivery_date": str(po.delivery_date) if po.delivery_date else None,
            "status": po.status.value if hasattr(po.status, 'value') else po.status,
            "currency": po.currency, "subtotal": float(po.subtotal),
            "tax_amount": float(po.tax_amount), "total_amount": float(po.total_amount),
            "department": po.department, "created_by": po.created_by,
            "created_at": str(po.created_at), "lines_count": len(po.lines) if po.lines else 0}

def _pold(l):
    return {"id": l.id, "line_number": l.line_number, "sku": l.sku, "description": l.description,
            "uom": l.uom, "quantity": float(l.quantity), "unit_price": float(l.unit_price),
            "tax_code": l.tax_code, "tax_rate": float(l.tax_rate),
            "line_subtotal": float(l.line_subtotal), "tax_amount": float(l.tax_amount),
            "line_total": float(l.line_total), "received_qty": float(l.received_qty),
            "status": l.status.value if hasattr(l.status, 'value') else l.status}

@router.get("")
def list_pos(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
             status_filter: Optional[str] = Query(None, alias="status"),
             vendor_id: Optional[str] = None, db: Session = Depends(get_db),
             current_user: dict = Depends(get_current_user)):
    q = db.query(PurchaseOrder)
    if status_filter: q = q.filter(PurchaseOrder.status == status_filter)
    if vendor_id: q = q.filter(PurchaseOrder.vendor_id == vendor_id)
    total = q.count()
    items = q.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": [_pod(po) for po in items], "total": total, "skip": skip, "limit": limit}

@router.post("", status_code=201)
def create_po(p: POCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    v = db.query(Vendor).filter(Vendor.id == p.vendor_id).first()
    if not v: raise HTTPException(status_code=404, detail="Vendor not found.")
    seq = db.query(PurchaseOrder).count() + 1
    pid = make_po_id(p.order_date.year, seq)
    while db.query(PurchaseOrder).filter(PurchaseOrder.id == pid).first():
        seq += 1; pid = make_po_id(p.order_date.year, seq)
    po = PurchaseOrder(id=pid, vendor_id=p.vendor_id, order_date=p.order_date,
                       delivery_date=p.delivery_date, status=POStatus.OPEN,
                       department=p.department, notes=p.notes, created_by=current_user["username"])
    db.add(po); db.flush()
    sub = Decimal("0"); tax_sum = Decimal("0")
    for ln, ld in enumerate(p.lines, 1):
        lid = make_pol_id(pid, ln)
        s = round2(ld.quantity * ld.unit_price)
        t = round2(s * Decimal(str(ld.tax_rate)) / 100)
        lt = round2(s + t); sub += s; tax_sum += t
        line = PurchaseOrderLine(id=lid, po_id=pid, line_number=ln, sku=ld.sku,
                                 description=ld.description, uom=ld.uom, quantity=ld.quantity,
                                 unit_price=ld.unit_price, tax_code=ld.tax_code, tax_rate=ld.tax_rate,
                                 line_subtotal=float(s), tax_amount=float(t), line_total=float(lt))
        db.add(line)
    po.subtotal = float(sub); po.tax_amount = float(tax_sum); po.total_amount = float(round2(sub + tax_sum))
    db.flush()
    return _pod(po)

@router.get("/{po_id}")
def get_po(po_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po: raise HTTPException(status_code=404, detail="PO not found.")
    r = _pod(po); r["lines"] = [_pold(l) for l in po.lines]; return r

@router.get("/{po_id}/lines")
def get_po_lines(po_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.po_id == po_id).all()
    return [_pold(l) for l in lines]
