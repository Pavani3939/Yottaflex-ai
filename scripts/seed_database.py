"""
YottaPay AI – Database Seeder
Loads generated CSV data into MySQL tables.

Usage:
    cd backend
    python -m scripts.seed_database
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pandas as pd
from sqlalchemy.orm import Session
from app.database.connection import engine, SessionLocal, Base
from app.database.init_db import create_database_if_not_exists, init_db
from app.models import *
from loguru import logger

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "generated"

def load_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        logger.error(f"File not found: {path}")
        logger.info("Run 'python scripts/generate_data.py' first.")
        sys.exit(1)
    return pd.read_csv(path, keep_default_na=False)

def seed():
    create_database_if_not_exists()
    init_db()
    db = SessionLocal()
    try:
        # Clear existing data (reverse FK order)
        for tbl in reversed(Base.metadata.sorted_tables):
            db.execute(tbl.delete())
        db.commit()
        logger.info("Cleared existing data.")

        # 1. Vendors
        df = load_csv("vendors")
        for _, r in df.iterrows():
            db.add(Vendor(id=r["id"], name=r["name"], code=r["code"], email=r["email"],
                          phone=r.get("phone",""), address_line1=r.get("address_line1",""),
                          city=r.get("city",""), state=r.get("state",""), country=r.get("country","India"),
                          pincode=r.get("pincode",""), gstin=r.get("gstin",""), pan=r.get("pan",""),
                          bank_account=r.get("bank_account",""), bank_ifsc=r.get("bank_ifsc",""),
                          payment_terms=int(r.get("payment_terms",30)), currency=r.get("currency","INR"),
                          status=VendorStatus(r["status"]), category=r.get("category",""),
                          contact_person=r.get("contact_person","")))
        db.commit()
        logger.info(f"Seeded {len(df)} vendors.")

        # 2. Purchase Orders
        df = load_csv("purchase_orders")
        for _, r in df.iterrows():
            db.add(PurchaseOrder(id=r["id"], vendor_id=r["vendor_id"], order_date=r["order_date"],
                                 delivery_date=r.get("delivery_date") or None,
                                 status=POStatus(r["status"]), currency=r.get("currency","INR"),
                                 subtotal=float(r["subtotal"]), tax_amount=float(r["tax_amount"]),
                                 total_amount=float(r["total_amount"]),
                                 department=r.get("department",""), created_by=r.get("created_by","system"),
                                 approved_by=r.get("approved_by",""), notes=r.get("notes","")))
        db.commit()
        logger.info(f"Seeded {len(df)} purchase orders.")

        # 3. PO Lines
        df = load_csv("purchase_order_lines")
        for _, r in df.iterrows():
            db.add(PurchaseOrderLine(id=r["id"], po_id=r["po_id"], line_number=int(r["line_number"]),
                                     sku=r["sku"], description=r["description"], uom=r.get("uom","EA"),
                                     quantity=float(r["quantity"]), unit_price=float(r["unit_price"]),
                                     tax_code=r.get("tax_code","GST18"), tax_rate=float(r.get("tax_rate",18)),
                                     line_subtotal=float(r["line_subtotal"]), tax_amount=float(r["tax_amount"]),
                                     line_total=float(r["line_total"]),
                                     received_qty=float(r.get("received_qty",0)),
                                     status=POLineStatus(r.get("status","OPEN"))))
        db.commit()
        logger.info(f"Seeded {len(df)} PO lines.")

        # 4. Goods Receipts
        df = load_csv("goods_receipts")
        for _, r in df.iterrows():
            db.add(GoodsReceipt(id=r["id"], po_id=r["po_id"], vendor_id=r["vendor_id"],
                                receipt_date=r["receipt_date"], warehouse=r.get("warehouse",""),
                                received_by=r.get("received_by","warehouse_staff"),
                                status=GRNStatus(r.get("status","ACCEPTED")), notes=r.get("notes","")))
        db.commit()
        logger.info(f"Seeded {len(df)} goods receipts.")

        # 5. GRN Lines
        df = load_csv("goods_receipt_lines")
        for _, r in df.iterrows():
            db.add(GoodsReceiptLine(id=r["id"], grn_id=r["grn_id"], po_line_id=r["po_line_id"],
                                    line_number=int(r["line_number"]), sku=r["sku"],
                                    description=r.get("description",""), uom=r.get("uom","EA"),
                                    received_qty=float(r["received_qty"]),
                                    accepted_qty=float(r["accepted_qty"]),
                                    rejected_qty=float(r.get("rejected_qty",0)),
                                    unit_price=float(r["unit_price"]),
                                    batch_number=r.get("batch_number",""),
                                    status=GRNLineStatus(r.get("status","ACCEPTED"))))
        db.commit()
        logger.info(f"Seeded {len(df)} GRN lines.")

        # 6. Invoices
        df = load_csv("invoices")
        for _, r in df.iterrows():
            db.add(Invoice(id=r["id"], invoice_number=r["invoice_number"], vendor_id=r["vendor_id"],
                           po_id=r.get("po_id") if r.get("po_id") else None,
                           invoice_date=r["invoice_date"], due_date=r.get("due_date") or None,
                           currency=r.get("currency","INR"),
                           subtotal=float(r["subtotal"]), tax_amount=float(r["tax_amount"]),
                           total_amount=float(r["total_amount"]),
                           calculated_subtotal=float(r.get("calculated_subtotal",0)),
                           calculated_tax=float(r.get("calculated_tax",0)),
                           calculated_total=float(r.get("calculated_total",0)),
                           status=InvoiceStatus(r.get("status","PENDING_MATCH")),
                           matching_status=MatchingStatus(r.get("matching_status","NOT_STARTED")),
                           source=InvoiceSource(r.get("source","MANUAL")),
                           is_duplicate=bool(r.get("is_duplicate",False)),
                           duplicate_of=r.get("duplicate_of") if r.get("duplicate_of") else None,
                           notes=r.get("notes",""), created_by=r.get("created_by","data_generator")))
        db.commit()
        logger.info(f"Seeded {len(df)} invoices.")

        # 7. Invoice Lines
        df = load_csv("invoice_lines")
        for _, r in df.iterrows():
            db.add(InvoiceLine(id=r["id"], invoice_id=r["invoice_id"],
                               line_number=int(r["line_number"]),
                               po_line_id=r.get("po_line_id") if r.get("po_line_id") else None,
                               sku=r.get("sku",""), description=r["description"], uom=r.get("uom","EA"),
                               quantity=float(r["quantity"]), unit_price=float(r["unit_price"]),
                               tax_code=r.get("tax_code","GST18"), tax_rate=float(r.get("tax_rate",18)),
                               line_subtotal=float(r["line_subtotal"]), tax_amount=float(r["tax_amount"]),
                               line_total=float(r["line_total"])))
        db.commit()
        logger.info(f"Seeded {len(df)} invoice lines.")

        logger.success("Database seeding complete!")
    except Exception as e:
        db.rollback()
        logger.error(f"Seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
