"""
YottaPay AI – Synthetic Data Generator
======================================
Fixed seed: 20261022
Generates: vendors, purchase_orders, purchase_order_lines,
           goods_receipts, goods_receipt_lines, invoices, invoice_lines,
           ground_truth.csv, validation_summary.json

Usage:
    python scripts/generate_data.py                     # default sizes
    python scripts/generate_data.py --vendors 300       # custom size
    python scripts/generate_data.py --verify-seed       # reproducibility check
"""
import argparse
import hashlib
import json
import os
import random
import sys
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SEED = 20261022
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "generated"
GROUND_TRUTH_PATH = Path(__file__).resolve().parent.parent / "data" / "ground_truth.csv"
VALIDATION_SUMMARY_PATH = Path(__file__).resolve().parent.parent / "data" / "validation_summary.json"

BASE_DATE = date(2025, 1, 1)   # earliest PO date
LATEST_DATE = date(2026, 10, 1)  # latest invoice date

# Tax codes and rates
TAX_CODES = {
    "GST5":  5.0,
    "GST12": 12.0,
    "GST18": 18.0,
    "GST28": 28.0,
    "EXEMPT": 0.0,
}
TAX_CODE_WEIGHTS = [0.10, 0.20, 0.50, 0.15, 0.05]

# UoM options
UOM_OPTIONS = ["EA", "KG", "LTR", "MTR", "BOX", "PACK", "SET", "PCS"]

# Indian states
INDIAN_STATES = [
    "Andhra Pradesh", "Bihar", "Delhi", "Gujarat", "Haryana",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
    "Punjab", "Rajasthan", "Tamil Nadu", "Telangana",
    "Uttar Pradesh", "West Bengal",
]

# Vendor categories
VENDOR_CATEGORIES = [
    "IT Services", "Logistics", "Manufacturing", "Consulting",
    "Raw Materials", "Office Supplies", "Maintenance", "Facility Management",
    "Healthcare", "Telecoms",
]

# Product SKUs and descriptions
PRODUCT_CATALOG = [
    ("SKU-LAPTOP-001",  "Laptop 15-inch Core i7",          "EA",  45000, "GST18"),
    ("SKU-MONITOR-002", "27-inch 4K Monitor",               "EA",  28000, "GST18"),
    ("SKU-CHAIR-003",   "Ergonomic Office Chair",            "EA",   8500, "GST18"),
    ("SKU-PAPER-004",   "A4 Printing Paper 500 Sheets",      "BOX",   350, "GST12"),
    ("SKU-CABLE-005",   "USB-C Cable 2m",                    "EA",    250, "GST18"),
    ("SKU-STEEL-006",   "Stainless Steel Sheet 1mm",         "KG",    120, "GST18"),
    ("SKU-PAINT-007",   "Industrial Paint 20L",              "LTR",   180, "GST18"),
    ("SKU-PUMP-008",    "Submersible Pump 1HP",              "EA",  12000, "GST18"),
    ("SKU-PIPE-009",    "GI Pipe 25mm x 6m",                 "MTR",   280, "GST18"),
    ("SKU-BOLT-010",    "M12 Hex Bolt Set",                  "PACK",   95, "GST18"),
    ("SKU-GLOVE-011",   "Safety Gloves (Pair)",              "PACK",  120, "GST5"),
    ("SKU-MASK-012",    "N95 Safety Mask",                   "PACK",  350, "GST5"),
    ("SKU-SERVER-013",  "Dell PowerEdge Server R740",        "EA", 350000, "GST18"),
    ("SKU-SWITCH-014",  "Cisco 24-Port Network Switch",      "EA",  25000, "GST18"),
    ("SKU-DESK-015",    "Height-Adjustable Desk",            "EA",  18000, "GST18"),
    ("SKU-CONF-016",    "Conference Phone Unit",             "EA",  22000, "GST18"),
    ("SKU-CHEM-017",    "Industrial Solvent 5L",             "LTR",  450, "GST12"),
    ("SKU-BEARING-018", "Ball Bearing 6205",                 "EA",    85, "GST18"),
    ("SKU-MOTOR-019",   "AC Motor 5HP",                      "EA",  18000, "GST18"),
    ("SKU-TABLET-020",  "Android Tablet 10-inch",            "EA",  15000, "GST18"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
TWO = Decimal("0.01")

def round2(v) -> Decimal:
    return Decimal(str(v)).quantize(TWO, rounding=ROUND_HALF_UP)

def random_date(start: date, end: date, rng: random.Random) -> date:
    delta = (end - start).days
    return start + timedelta(days=rng.randint(0, delta))

def gstin(state_code: int, pan: str, rng: random.Random) -> str:
    """Generate a plausible GSTIN."""
    entity = rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    check = rng.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return f"{state_code:02d}{pan}1{entity}1Z{check}"


# ---------------------------------------------------------------------------
# Generator Class
# ---------------------------------------------------------------------------
class YottaPayDataGenerator:
    """Reproducible synthetic data generator with fixed seed."""

    def __init__(
        self,
        n_vendors: int = 300,
        n_pos: int = 1500,
        n_grns: int = 1800,
        n_invoices: int = 2000,
        seed: int = SEED,
        output_dir: Path = OUTPUT_DIR,
    ):
        self.n_vendors = n_vendors
        self.n_pos = n_pos
        self.n_grns = n_grns
        self.n_invoices = n_invoices
        self.seed = seed
        self.output_dir = output_dir

        # Seed all RNGs
        random.seed(seed)
        np.random.seed(seed)
        self.rng = random.Random(seed)
        self.fake = Faker("en_IN")
        Faker.seed(seed)

        # Storage
        self.vendors: list[dict] = []
        self.purchase_orders: list[dict] = []
        self.po_lines: list[dict] = []
        self.goods_receipts: list[dict] = []
        self.grn_lines: list[dict] = []
        self.invoices: list[dict] = []
        self.invoice_lines: list[dict] = []
        self.ground_truth: list[dict] = []

    # -----------------------------------------------------------------------
    # STEP 1 – Vendors
    # -----------------------------------------------------------------------
    def generate_vendors(self) -> None:
        print(f"  Generating {self.n_vendors} vendors …")
        statuses = ["ACTIVE"] * 88 + ["INACTIVE"] * 8 + ["BLACKLISTED"] * 2 + ["PENDING_REVIEW"] * 2
        payment_terms_options = [15, 30, 45, 60, 90]

        for i in range(1, self.n_vendors + 1):
            vid = f"VND-{i:05d}"
            vcode = f"VND{i:05d}"
            state = self.rng.choice(INDIAN_STATES)
            state_code = INDIAN_STATES.index(state) + 1
            pan = (
                "".join(self.rng.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5))
                + f"{i:04d}"
                + self.rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            )
            self.vendors.append({
                "id": vid,
                "name": self.fake.company(),
                "code": vcode,
                "email": self.fake.company_email(),
                "phone": self.fake.phone_number()[:20],
                "address_line1": self.fake.street_address()[:100],
                "city": self.fake.city()[:50],
                "state": state,
                "country": "India",
                "pincode": self.fake.postcode()[:6],
                "gstin": gstin(state_code, pan, self.rng),
                "pan": pan,
                "bank_account": str(self.rng.randint(10**11, 10**15 - 1)),
                "bank_ifsc": f"HDFC{self.rng.randint(10000, 99999):07d}",
                "payment_terms": self.rng.choice(payment_terms_options),
                "currency": "INR",
                "status": self.rng.choice(statuses),
                "category": self.rng.choice(VENDOR_CATEGORIES),
                "contact_person": self.fake.name(),
            })

    # -----------------------------------------------------------------------
    # STEP 2 – Purchase Orders
    # -----------------------------------------------------------------------
    def generate_purchase_orders(self) -> None:
        print(f"  Generating {self.n_pos} purchase orders …")
        active_vendor_ids = [v["id"] for v in self.vendors if v["status"] == "ACTIVE"]
        departments = ["IT", "Finance", "Operations", "HR", "Procurement", "Maintenance"]

        for i in range(1, self.n_pos + 1):
            order_date = random_date(BASE_DATE, date(2026, 6, 30), self.rng)
            delivery_date = order_date + timedelta(days=self.rng.randint(7, 60))
            self.purchase_orders.append({
                "id": f"PO-{order_date.year}-{i:06d}",
                "vendor_id": self.rng.choice(active_vendor_ids),
                "order_date": order_date.isoformat(),
                "delivery_date": delivery_date.isoformat(),
                "status": "OPEN",
                "currency": "INR",
                "subtotal": 0,
                "tax_amount": 0,
                "total_amount": 0,
                "department": self.rng.choice(departments),
                "created_by": "procurement_system",
                "approved_by": self.fake.first_name().lower() + "_mgr",
                "notes": "",
            })

    # -----------------------------------------------------------------------
    # STEP 3 – PO Lines
    # -----------------------------------------------------------------------
    def generate_po_lines(self) -> None:
        print("  Generating PO lines …")
        for po in self.purchase_orders:
            n_lines = self.rng.randint(1, 8)
            po_subtotal = Decimal("0")
            po_tax = Decimal("0")
            products_used = self.rng.sample(PRODUCT_CATALOG, min(n_lines, len(PRODUCT_CATALOG)))

            for ln, product in enumerate(products_used, start=1):
                sku, desc, uom, base_price, tax_code = product
                quantity = round2(self.rng.uniform(1, 100))
                # Vary price ±20%
                unit_price = round2(base_price * self.rng.uniform(0.80, 1.20))
                tax_rate = Decimal(str(TAX_CODES[tax_code]))
                subtotal = round2(quantity * unit_price)
                tax_amt = round2(subtotal * tax_rate / 100)
                line_total = round2(subtotal + tax_amt)

                po_subtotal += subtotal
                po_tax += tax_amt

                self.po_lines.append({
                    "id": f"POLINE-{po['id']}-{ln:02d}",
                    "po_id": po["id"],
                    "line_number": ln,
                    "sku": sku,
                    "description": desc,
                    "uom": uom,
                    "quantity": float(quantity),
                    "unit_price": float(unit_price),
                    "tax_code": tax_code,
                    "tax_rate": float(tax_rate),
                    "line_subtotal": float(subtotal),
                    "tax_amount": float(tax_amt),
                    "line_total": float(line_total),
                    "received_qty": 0.0,
                    "status": "OPEN",
                })

            # Update PO totals
            po["subtotal"] = float(po_subtotal)
            po["tax_amount"] = float(po_tax)
            po["total_amount"] = float(round2(po_subtotal + po_tax))

    # -----------------------------------------------------------------------
    # STEP 4 – Goods Receipts
    # -----------------------------------------------------------------------
    def generate_goods_receipts(self) -> None:
        print(f"  Generating {self.n_grns} goods receipts …")
        warehouses = ["WH-MUMBAI-01", "WH-DELHI-02", "WH-BENGALURU-03",
                      "WH-HYDERABAD-04", "WH-CHENNAI-05"]

        # Build a lookup of valid PO IDs with their order dates
        po_lookup = {po["id"]: po for po in self.purchase_orders}
        po_ids = list(po_lookup.keys())

        for i in range(1, self.n_grns + 1):
            po = po_lookup[self.rng.choice(po_ids)]
            po_date = date.fromisoformat(po["order_date"])
            receipt_date = random_date(
                po_date + timedelta(days=1),
                min(po_date + timedelta(days=90), LATEST_DATE),
                self.rng,
            )
            grn_id = f"GRN-{receipt_date.year}-{i:06d}"
            self.goods_receipts.append({
                "id": grn_id,
                "po_id": po["id"],
                "vendor_id": po["vendor_id"],
                "receipt_date": receipt_date.isoformat(),
                "warehouse": self.rng.choice(warehouses),
                "received_by": "warehouse_staff",
                "status": "ACCEPTED",
                "notes": "",
            })

    # -----------------------------------------------------------------------
    # STEP 5 – GRN Lines (map to PO lines)
    # -----------------------------------------------------------------------
    def generate_grn_lines(self) -> None:
        print("  Generating GRN lines …")
        # Build lookup: po_id → list of po_line dicts
        po_line_lookup: dict[str, list[dict]] = {}
        for poline in self.po_lines:
            po_line_lookup.setdefault(poline["po_id"], []).append(poline)

        # Track received quantities per PO line
        received_tracker: dict[str, float] = {}

        for grn in self.goods_receipts:
            po_lines_for_grn = po_line_lookup.get(grn["po_id"], [])
            if not po_lines_for_grn:
                continue
            # Receive a random subset of PO lines
            n_lines = self.rng.randint(1, len(po_lines_for_grn))
            selected_lines = self.rng.sample(po_lines_for_grn, n_lines)

            for ln, poline in enumerate(selected_lines, start=1):
                already_received = received_tracker.get(poline["id"], 0.0)
                remaining = max(0, poline["quantity"] - already_received)
                if remaining <= 0:
                    continue
                recv_qty = round(self.rng.uniform(0.1, remaining), 3)
                accepted_qty = recv_qty   # simplification: all accepted
                rejected_qty = 0.0

                grn_line_id = f"GRNL-{grn['id']}-{ln:02d}"
                self.grn_lines.append({
                    "id": grn_line_id,
                    "grn_id": grn["id"],
                    "po_line_id": poline["id"],
                    "line_number": ln,
                    "sku": poline["sku"],
                    "description": poline["description"],
                    "uom": poline["uom"],
                    "received_qty": recv_qty,
                    "accepted_qty": accepted_qty,
                    "rejected_qty": rejected_qty,
                    "unit_price": poline["unit_price"],
                    "batch_number": f"BATCH-{self.rng.randint(10000, 99999)}",
                    "status": "ACCEPTED",
                })
                received_tracker[poline["id"]] = already_received + accepted_qty

        # Back-fill received_qty on PO lines
        for poline in self.po_lines:
            poline["received_qty"] = round(received_tracker.get(poline["id"], 0.0), 3)
            if poline["received_qty"] >= poline["quantity"]:
                poline["status"] = "FULLY_RECEIVED"
            elif poline["received_qty"] > 0:
                poline["status"] = "PARTIALLY_RECEIVED"

    # -----------------------------------------------------------------------
    # STEP 6 & 7 – Invoices and Invoice Lines (clean baseline first)
    # -----------------------------------------------------------------------
    def generate_invoices(self) -> None:
        print(f"  Generating {self.n_invoices} invoices (baseline + anomaly injection) …")

        # Build lookups
        active_vendors = {v["id"]: v for v in self.vendors if v["status"] == "ACTIVE"}
        all_vendors = {v["id"]: v for v in self.vendors}
        po_lookup = {po["id"]: po for po in self.purchase_orders}
        po_line_lookup: dict[str, list[dict]] = {}
        for poline in self.po_lines:
            po_line_lookup.setdefault(poline["po_id"], []).append(poline)
        grn_line_lookup: dict[str, list[dict]] = {}
        for gline in self.grn_lines:
            grn_line_lookup.setdefault(gline["po_line_id"], []).append(gline)

        active_vendor_ids = list(active_vendors.keys())
        pos_with_grns = list({g["po_id"] for g in self.goods_receipts})

        # ---- Anomaly distribution (of n_invoices) ----
        n_clean      = int(self.n_invoices * 0.70)
        n_price      = int(self.n_invoices * 0.10)
        n_qty        = int(self.n_invoices * 0.08)
        n_dup        = int(self.n_invoices * 0.05)
        n_missing    = int(self.n_invoices * 0.04)
        n_tax_vendor = self.n_invoices - n_clean - n_price - n_qty - n_dup - n_missing

        scenarios = (
            ["CLEAN"]          * n_clean   +
            ["PRICE_VARIANCE"] * n_price   +
            ["QUANTITY_MISMATCH"] * n_qty  +
            ["DUPLICATE"]      * n_dup     +
            ["MISSING_RECEIPT"] * n_missing +
            ["TAX_VENDOR_ERROR"] * n_tax_vendor
        )
        self.rng.shuffle(scenarios)

        inv_seq = 1
        vendor_inv_seq: dict[str, int] = {}  # vendor_id → seq counter
        # Track invoice_number+vendor for duplicate injection
        existing_inv_numbers: list[tuple[str, str]] = []  # (invoice_number, vendor_id)

        for scenario in scenarios:
            # --- Pick vendor ---
            if scenario == "TAX_VENDOR_ERROR" and self.rng.random() < 0.4:
                # 40% of TAX_VENDOR_ERROR = VENDOR_ERROR (inactive/blacklisted vendor)
                bad_vendors = [v["id"] for v in self.vendors if v["status"] in ("INACTIVE", "BLACKLISTED")]
                vendor_id = self.rng.choice(bad_vendors) if bad_vendors else self.rng.choice(active_vendor_ids)
                anomaly_subtype = "VENDOR_ERROR"
            else:
                vendor_id = self.rng.choice(active_vendor_ids)
                anomaly_subtype = scenario

            vendor = all_vendors[vendor_id]
            vcode = vendor["code"]

            # --- Pick a PO ---
            vendor_pos = [po for po in self.purchase_orders if po["vendor_id"] == vendor_id]
            po = None
            if vendor_pos and scenario != "MISSING_RECEIPT":
                po_candidates = [p for p in vendor_pos if p["id"] in pos_with_grns]
                if po_candidates:
                    po = self.rng.choice(po_candidates)
                elif vendor_pos:
                    po = self.rng.choice(vendor_pos)

            # For MISSING_RECEIPT: pick a PO without GRN lines
            if scenario == "MISSING_RECEIPT" and vendor_pos:
                no_grn_pos = [p for p in vendor_pos if p["id"] not in pos_with_grns]
                if no_grn_pos:
                    po = self.rng.choice(no_grn_pos)
                else:
                    po = self.rng.choice(vendor_pos)

            # --- Dates ---
            if po:
                po_date = date.fromisoformat(po["order_date"])
            else:
                po_date = BASE_DATE

            if scenario == "CLEAN" or scenario == "PRICE_VARIANCE" or scenario == "QUANTITY_MISMATCH":
                invoice_date = random_date(po_date, LATEST_DATE, self.rng)
            elif anomaly_subtype == "DATE_ERROR":
                # Invoice date BEFORE PO date
                invoice_date = po_date - timedelta(days=self.rng.randint(1, 30))
            else:
                invoice_date = random_date(po_date, LATEST_DATE, self.rng)

            # --- Invoice ID ---
            seq = vendor_inv_seq.get(vendor_id, 0) + 1
            vendor_inv_seq[vendor_id] = seq
            inv_id = f"INV-{vcode}-{invoice_date.year}-{seq:06d}"
            inv_number = f"INV/{vcode}/{invoice_date.year}/{seq:06d}"

            # --- Duplicate injection ---
            is_duplicate = False
            duplicate_of = None
            if scenario == "DUPLICATE" and existing_inv_numbers:
                # Reuse an existing invoice number from same vendor
                same_vendor_invs = [(n, v) for n, v in existing_inv_numbers if v == vendor_id]
                if same_vendor_invs:
                    inv_number, _ = self.rng.choice(same_vendor_invs)
                    is_duplicate = True
                    # Find the original invoice ID
                    duplicate_of = next(
                        (inv["id"] for inv in self.invoices
                         if inv["invoice_number"] == inv_number and inv["vendor_id"] == vendor_id),
                        None,
                    )

            # --- Build invoice lines from PO lines ---
            if po:
                po_lines_for_inv = po_line_lookup.get(po["id"], [])
                selected_po_lines = self.rng.sample(
                    po_lines_for_inv, min(self.rng.randint(1, 5), len(po_lines_for_inv))
                ) if po_lines_for_inv else []
            else:
                selected_po_lines = []

            # Fallback if no PO lines: create standalone line
            if not selected_po_lines:
                product = self.rng.choice(PRODUCT_CATALOG)
                sku, desc, uom, base_price, tax_code = product
                qty = round2(self.rng.uniform(1, 20))
                price = round2(base_price * self.rng.uniform(0.9, 1.1))
                selected_po_lines = [{
                    "id": None, "sku": sku, "description": desc, "uom": uom,
                    "quantity": float(qty), "unit_price": float(price),
                    "tax_code": tax_code, "tax_rate": TAX_CODES[tax_code],
                }]

            # --- Build invoice lines with anomaly injection ---
            inv_lines = []
            inv_subtotal = Decimal("0")
            inv_tax = Decimal("0")

            for ln, poline in enumerate(selected_po_lines, start=1):
                inv_line_id = f"INVL-{inv_id}-{ln:02d}"
                sku = poline["sku"]
                desc = poline["description"]
                uom = poline.get("uom", "EA")
                po_qty = Decimal(str(poline["quantity"]))
                po_price = Decimal(str(poline["unit_price"]))
                tax_code = poline["tax_code"]
                tax_rate = Decimal(str(poline["tax_rate"]))

                inv_qty = po_qty
                inv_price = po_price

                # Inject anomalies
                if scenario == "PRICE_VARIANCE":
                    # ±5–25% price variance
                    factor = self.rng.uniform(1.05, 1.25)
                    if self.rng.random() < 0.5:
                        factor = 1 / factor
                    inv_price = round2(po_price * Decimal(str(factor)))

                elif scenario == "QUANTITY_MISMATCH":
                    # Invoice qty > PO qty (overbilling)
                    inv_qty = round2(po_qty * Decimal(str(self.rng.uniform(1.05, 1.5))))

                elif anomaly_subtype == "TAX_VENDOR_ERROR" or scenario == "TAX_VENDOR_ERROR":
                    # Incorrect tax rate
                    all_rates = [Decimal(str(r)) for r in TAX_CODES.values() if r != float(tax_rate)]
                    if all_rates:
                        tax_rate = self.rng.choice(all_rates)
                        tax_code = self.rng.choice([k for k, v in TAX_CODES.items() if Decimal(str(v)) == tax_rate])

                # Calculate line amounts
                subtotal = round2(inv_qty * inv_price)
                tax_amt = round2(subtotal * tax_rate / 100)
                line_total = round2(subtotal + tax_amt)

                inv_subtotal += subtotal
                inv_tax += tax_amt

                inv_lines.append({
                    "id": inv_line_id,
                    "invoice_id": inv_id,
                    "line_number": ln,
                    "po_line_id": poline.get("id"),
                    "sku": sku,
                    "description": desc,
                    "uom": uom,
                    "quantity": float(inv_qty),
                    "unit_price": float(inv_price),
                    "tax_code": tax_code,
                    "tax_rate": float(tax_rate),
                    "line_subtotal": float(subtotal),
                    "tax_amount": float(tax_amt),
                    "line_total": float(line_total),
                })

            inv_total = round2(inv_subtotal + inv_tax)

            # Inject TOTAL_MISMATCH: corrupt the stated total
            stated_subtotal = float(inv_subtotal)
            stated_tax = float(inv_tax)
            stated_total = float(inv_total)

            if scenario == "CLEAN":
                # Correctly calculated
                pass
            # For other scenarios, totals remain mathematically consistent
            # (the anomaly is in line-level quantities/prices vs PO)

            # --- Determine expected matching status (ground truth) ---
            gt_status = self._determine_ground_truth(
                scenario, anomaly_subtype, vendor, po, is_duplicate
            )

            # --- Payment due date ---
            payment_terms = vendor.get("payment_terms", 30)
            due_date = (invoice_date + timedelta(days=payment_terms)).isoformat()

            inv_record = {
                "id": inv_id,
                "invoice_number": inv_number,
                "vendor_id": vendor_id,
                "po_id": po["id"] if po else None,
                "invoice_date": invoice_date.isoformat(),
                "due_date": due_date,
                "currency": "INR",
                "subtotal": stated_subtotal,
                "tax_amount": stated_tax,
                "total_amount": stated_total,
                "calculated_subtotal": stated_subtotal,
                "calculated_tax": stated_tax,
                "calculated_total": stated_total,
                "status": "PENDING_MATCH",
                "matching_status": "NOT_STARTED",
                "source": "MANUAL",
                "extraction_confidence": None,
                "is_duplicate": is_duplicate,
                "duplicate_of": duplicate_of,
                "notes": f"Synthetic data – scenario: {scenario}",
                "created_by": "data_generator",
            }

            self.invoices.append(inv_record)
            self.invoice_lines.extend(inv_lines)

            # Ground truth record (kept SEPARATE from invoice data)
            self.ground_truth.append({
                "invoice_id": inv_id,
                "scenario": scenario,
                "anomaly_subtype": anomaly_subtype,
                "expected_matching_status": gt_status,
                "is_duplicate": is_duplicate,
                "duplicate_of": duplicate_of,
            })

            if not is_duplicate:
                existing_inv_numbers.append((inv_number, vendor_id))

            inv_seq += 1

    def _determine_ground_truth(
        self, scenario: str, subtype: str, vendor: dict, po: Optional[dict], is_dup: bool
    ) -> str:
        """Calculate the EXPECTED matching status based on the scenario."""
        if is_dup or scenario == "DUPLICATE":
            return "DUPLICATE"
        if subtype == "VENDOR_ERROR":
            return "VENDOR_ERROR"
        if subtype == "DATE_ERROR":
            return "DATE_ERROR"
        if scenario == "PRICE_VARIANCE":
            return "PRICE_VARIANCE"
        if scenario == "QUANTITY_MISMATCH":
            return "QUANTITY_MISMATCH"
        if scenario == "MISSING_RECEIPT":
            return "MISSING_RECEIPT"
        if scenario in ("TAX_VENDOR_ERROR", "TAX_MISMATCH"):
            return "TAX_MISMATCH"
        if scenario == "CLEAN":
            return "MATCHED"
        return "MATCHED"

    # -----------------------------------------------------------------------
    # STEP 8 – Save CSVs
    # -----------------------------------------------------------------------
    def save_all(self) -> dict:
        """Save all generated data to CSV files and return checksums."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        datasets = {
            "vendors": self.vendors,
            "purchase_orders": self.purchase_orders,
            "purchase_order_lines": self.po_lines,
            "goods_receipts": self.goods_receipts,
            "goods_receipt_lines": self.grn_lines,
            "invoices": self.invoices,
            "invoice_lines": self.invoice_lines,
        }

        checksums = {}
        for name, records in datasets.items():
            path = self.output_dir / f"{name}.csv"
            df = pd.DataFrame(records)
            df.to_csv(path, index=False)
            md5 = hashlib.md5(path.read_bytes()).hexdigest()
            checksums[name] = {"rows": len(records), "checksum_md5": md5}
            print(f"    Saved {len(records):>6,} rows → {path.name}  [MD5: {md5[:8]}…]")

        # Ground truth (separate from business data)
        gt_path = GROUND_TRUTH_PATH
        gt_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(self.ground_truth).to_csv(gt_path, index=False)
        gt_md5 = hashlib.md5(gt_path.read_bytes()).hexdigest()
        checksums["ground_truth"] = {"rows": len(self.ground_truth), "checksum_md5": gt_md5}
        print(f"    Saved {len(self.ground_truth):>6,} rows → ground_truth.csv  [MD5: {gt_md5[:8]}…]")

        return checksums

    # -----------------------------------------------------------------------
    # STEP 9 – Validation Summary
    # -----------------------------------------------------------------------
    def build_validation_summary(self, checksums: dict) -> None:
        """Build and save validation_summary.json."""
        vendor_ids = {v["id"] for v in self.vendors}
        po_ids = {p["id"] for p in self.purchase_orders}
        po_line_ids = {pl["id"] for pl in self.po_lines}
        grn_ids = {g["id"] for g in self.goods_receipts}
        invoice_ids = {inv["id"] for inv in self.invoices}

        # FK checks
        fk_errors = []
        for po in self.purchase_orders:
            if po["vendor_id"] not in vendor_ids:
                fk_errors.append(f"PO {po['id']}: vendor_id {po['vendor_id']} not found")
        for grn in self.goods_receipts:
            if grn["po_id"] not in po_ids:
                fk_errors.append(f"GRN {grn['id']}: po_id {grn['po_id']} not found")
        for inv in self.invoices:
            if inv["vendor_id"] not in vendor_ids:
                fk_errors.append(f"INV {inv['id']}: vendor_id {inv['vendor_id']} not found")

        # Duplicate invoice_id check
        all_inv_ids = [inv["id"] for inv in self.invoices]
        dup_ids = len(all_inv_ids) - len(set(all_inv_ids))

        # Arithmetic check on invoice lines
        arith_errors = 0
        for inv in self.invoices:
            inv_id = inv["id"]
            lines = [l for l in self.invoice_lines if l["invoice_id"] == inv_id]
            calc_total = sum(Decimal(str(l["line_total"])) for l in lines)
            stated_total = Decimal(str(inv["total_amount"]))
            if abs(calc_total - stated_total) > Decimal("0.02"):
                arith_errors += 1

        # Scenario distribution
        scenario_counts = {}
        for gt in self.ground_truth:
            s = gt["scenario"]
            scenario_counts[s] = scenario_counts.get(s, 0) + 1

        summary = {
            "seed": self.seed,
            "generated_at": str(pd.Timestamp.now()),
            "totals": {
                "vendors": len(self.vendors),
                "purchase_orders": len(self.purchase_orders),
                "purchase_order_lines": len(self.po_lines),
                "goods_receipts": len(self.goods_receipts),
                "goods_receipt_lines": len(self.grn_lines),
                "invoices": len(self.invoices),
                "invoice_lines": len(self.invoice_lines),
            },
            "validation": {
                "fk_failures": len(fk_errors),
                "fk_error_details": fk_errors[:10],
                "duplicate_invoice_ids": dup_ids,
                "arithmetic_failures": arith_errors,
                "pk_uniqueness_ok": dup_ids == 0,
            },
            "scenario_distribution": scenario_counts,
            "checksums": checksums,
        }

        VALIDATION_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
        VALIDATION_SUMMARY_PATH.write_text(json.dumps(summary, indent=2, default=str))
        print(f"    Saved validation_summary.json")
        print(f"\n  Validation: FK errors={len(fk_errors)}, Arith errors={arith_errors}, Dup IDs={dup_ids}")

    # -----------------------------------------------------------------------
    # Main Run
    # -----------------------------------------------------------------------
    def run(self) -> None:
        print(f"\n{'='*60}")
        print(f"  YottaPay AI – Synthetic Data Generator")
        print(f"  Seed: {self.seed}")
        print(f"{'='*60}")

        self.generate_vendors()
        self.generate_purchase_orders()
        self.generate_po_lines()
        self.generate_goods_receipts()
        self.generate_grn_lines()
        self.generate_invoices()

        print(f"\n  Saving files …")
        checksums = self.save_all()
        self.build_validation_summary(checksums)

        print(f"\n{'='*60}")
        print(f"  Generation complete!")
        print(f"  PO Lines generated : {len(self.po_lines):,}")
        print(f"  GRN Lines generated: {len(self.grn_lines):,}")
        print(f"  Invoice Lines      : {len(self.invoice_lines):,}")
        print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="YottaPay AI – Synthetic Data Generator")
    parser.add_argument("--vendors",   type=int, default=300,  help="Number of vendors")
    parser.add_argument("--pos",       type=int, default=1500, help="Number of purchase orders")
    parser.add_argument("--grns",      type=int, default=1800, help="Number of goods receipts")
    parser.add_argument("--invoices",  type=int, default=2000, help="Number of invoices")
    parser.add_argument("--seed",      type=int, default=SEED, help="Random seed")
    parser.add_argument("--verify-seed", action="store_true",  help="Run twice and verify reproducibility")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.verify_seed:
        # Run reproduce_data.py instead
        import subprocess
        subprocess.run([sys.executable, str(Path(__file__).parent / "reproduce_data.py")], check=True)
    else:
        gen = YottaPayDataGenerator(
            n_vendors=args.vendors,
            n_pos=args.pos,
            n_grns=args.grns,
            n_invoices=args.invoices,
            seed=args.seed,
        )
        gen.run()
