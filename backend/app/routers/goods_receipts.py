"""YottaPay AI – Goods Receipts Router (Full)"""
from typing import Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.goods_receipt import GoodsReceipt, GRNStatus
from app.models.goods_receipt_line import GoodsReceiptLine, GRNLineStatus
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_order_line import PurchaseOrderLine
from app.utils.id_generator import grn_id as make_grn_id, grn_line_id as make_grnl_id
from app.routers.auth import get_current_user

router = APIRouter(prefix="/goods-receipts")

class GRNLineCreate(BaseModel):
    po_line_id: str; received_qty: float; accepted_qty: float; rejected_qty: float = 0
    batch_number: Optional[str] = None

class GRNCreate(BaseModel):
    po_id: str; receipt_date: date; warehouse: Optional[str] = None
    notes: Optional[str] = None; lines: list[GRNLineCreate]

def _gd(g):
    return {"id": g.id, "po_id": g.po_id, "vendor_id": g.vendor_id,
            "receipt_date": str(g.receipt_date), "warehouse": g.warehouse,
            "received_by": g.received_by,
            "status": g.status.value if hasattr(g.status, 'value') else g.status,
            "notes": g.notes, "created_at": str(g.created_at),
            "lines_count": len(g.lines) if g.lines else 0}

def _gld(l):
    return {"id": l.id, "grn_id": l.grn_id, "po_line_id": l.po_line_id,
            "line_number": l.line_number, "sku": l.sku, "description": l.description,
            "received_qty": float(l.received_qty), "accepted_qty": float(l.accepted_qty),
            "rejected_qty": float(l.rejected_qty), "unit_price": float(l.unit_price),
            "batch_number": l.batch_number,
            "status": l.status.value if hasattr(l.status, 'value') else l.status}

@router.get("")
def list_grns(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
              po_id: Optional[str] = None, vendor_id: Optional[str] = None,
              db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    q = db.query(GoodsReceipt)
    if po_id: q = q.filter(GoodsReceipt.po_id == po_id)
    if vendor_id: q = q.filter(GoodsReceipt.vendor_id == vendor_id)
    total = q.count()
    items = q.order_by(GoodsReceipt.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": [_gd(g) for g in items], "total": total, "skip": skip, "limit": limit}

@router.post("", status_code=201)
def create_grn(p: GRNCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == p.po_id).first()
    if not po: raise HTTPException(status_code=404, detail="PO not found.")
    seq = db.query(GoodsReceipt).count() + 1
    gid = make_grn_id(p.receipt_date.year, seq)
    while db.query(GoodsReceipt).filter(GoodsReceipt.id == gid).first():
        seq += 1; gid = make_grn_id(p.receipt_date.year, seq)
    grn = GoodsReceipt(id=gid, po_id=p.po_id, vendor_id=po.vendor_id,
                       receipt_date=p.receipt_date, warehouse=p.warehouse,
                       received_by=current_user["username"], status=GRNStatus.ACCEPTED, notes=p.notes)
    db.add(grn); db.flush()
    for ln, ld in enumerate(p.lines, 1):
        pol = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.id == ld.po_line_id).first()
        if not pol: raise HTTPException(status_code=404, detail=f"PO line {ld.po_line_id} not found.")
        lid = make_grnl_id(gid, ln)
        gl = GoodsReceiptLine(id=lid, grn_id=gid, po_line_id=ld.po_line_id, line_number=ln,
                              sku=pol.sku, description=pol.description, uom=pol.uom,
                              received_qty=ld.received_qty, accepted_qty=ld.accepted_qty,
                              rejected_qty=ld.rejected_qty, unit_price=float(pol.unit_price),
                              batch_number=ld.batch_number, status=GRNLineStatus.ACCEPTED)
        db.add(gl)
    db.flush()
    return _gd(grn)

@router.get("/{grn_id}")
def get_grn(grn_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    grn = db.query(GoodsReceipt).filter(GoodsReceipt.id == grn_id).first()
    if not grn: raise HTTPException(status_code=404, detail="GRN not found.")
    r = _gd(grn); r["lines"] = [_gld(l) for l in grn.lines]; return r
