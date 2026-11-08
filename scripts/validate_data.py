"""
YottaPay AI – Data Validation Script
Validates generated data and produces evaluation metrics.

Usage:
    python scripts/validate_data.py
"""
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "generated"
GT_PATH = Path(__file__).resolve().parent.parent / "data" / "ground_truth.csv"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "validation_summary.json"


def main():
    print("="*60)
    print("  YottaPay AI – Data Validation & Evaluation")
    print("="*60)

    vendors = pd.read_csv(DATA_DIR / "vendors.csv")
    pos = pd.read_csv(DATA_DIR / "purchase_orders.csv")
    po_lines = pd.read_csv(DATA_DIR / "purchase_order_lines.csv")
    grns = pd.read_csv(DATA_DIR / "goods_receipts.csv")
    grn_lines = pd.read_csv(DATA_DIR / "goods_receipt_lines.csv")
    invoices = pd.read_csv(DATA_DIR / "invoices.csv")
    inv_lines = pd.read_csv(DATA_DIR / "invoice_lines.csv")
    gt = pd.read_csv(GT_PATH)

    results = {"checks": {}, "metrics": {}}
    errors = []

    # 1. PK Uniqueness
    for name, df, pk in [
        ("vendors", vendors, "id"), ("purchase_orders", pos, "id"),
        ("purchase_order_lines", po_lines, "id"), ("goods_receipts", grns, "id"),
        ("invoices", invoices, "id"), ("invoice_lines", inv_lines, "id")
    ]:
        dups = df[pk].duplicated().sum()
        results["checks"][f"{name}_pk_unique"] = dups == 0
        if dups > 0: errors.append(f"{name}: {dups} duplicate PKs")
    print(f"\n  PK Uniqueness: {'PASS' if not errors else 'FAIL'}")

    # 2. FK Integrity
    vendor_ids = set(vendors["id"])
    po_ids = set(pos["id"])
    po_line_ids = set(po_lines["id"])
    fk_errors = []
    bad_po_vendor = pos[~pos["vendor_id"].isin(vendor_ids)]
    if len(bad_po_vendor): fk_errors.append(f"POs with bad vendor_id: {len(bad_po_vendor)}")
    bad_grn_po = grns[~grns["po_id"].isin(po_ids)]
    if len(bad_grn_po): fk_errors.append(f"GRNs with bad po_id: {len(bad_grn_po)}")
    bad_inv_vendor = invoices[~invoices["vendor_id"].isin(vendor_ids)]
    if len(bad_inv_vendor): fk_errors.append(f"Invoices with bad vendor_id: {len(bad_inv_vendor)}")
    results["checks"]["fk_integrity"] = len(fk_errors) == 0
    results["checks"]["fk_error_count"] = len(fk_errors)
    print(f"  FK Integrity:  {'PASS' if not fk_errors else 'FAIL — ' + '; '.join(fk_errors)}")

    # 3. Invoice Arithmetic
    arith_ok = 0; arith_fail = 0
    for inv_id in invoices["id"]:
        lines = inv_lines[inv_lines["invoice_id"] == inv_id]
        calc_total = lines["line_total"].sum()
        stated = invoices[invoices["id"] == inv_id]["total_amount"].iloc[0]
        if abs(calc_total - stated) <= 0.02:
            arith_ok += 1
        else:
            arith_fail += 1
    results["checks"]["arithmetic_valid_count"] = arith_ok
    results["checks"]["arithmetic_fail_count"] = arith_fail
    print(f"  Arithmetic:    {arith_ok} valid, {arith_fail} failed")

    # 4. Scenario distribution
    scenario_dist = gt["scenario"].value_counts().to_dict()
    results["scenario_distribution"] = scenario_dist
    print(f"\n  Scenario Distribution:")
    for s, c in sorted(scenario_dist.items()):
        print(f"    {s:25s}: {c:>5d} ({c/len(gt)*100:.1f}%)")

    # 5. Matching evaluation (simulated: use ground-truth expected vs scenario)
    # In a real run, the matching engine writes actual results — here we validate GT consistency
    gt_statuses = gt["expected_matching_status"].value_counts()
    results["expected_status_distribution"] = gt_statuses.to_dict()

    # Compute binary classification metrics (MATCHED vs not)
    y_true = (gt["expected_matching_status"] == "MATCHED").astype(int).values
    # Since we haven't run the engine yet, report expected distribution
    n_total = len(gt)
    n_matched = int(y_true.sum())
    n_exception = n_total - n_matched

    results["metrics"]["total_invoices"] = n_total
    results["metrics"]["expected_matched"] = n_matched
    results["metrics"]["expected_exceptions"] = n_exception
    results["metrics"]["expected_match_rate"] = round(n_matched / n_total * 100, 2)

    # Row counts
    results["row_counts"] = {
        "vendors": len(vendors), "purchase_orders": len(pos),
        "purchase_order_lines": len(po_lines), "goods_receipts": len(grns),
        "goods_receipt_lines": len(grn_lines), "invoices": len(invoices),
        "invoice_lines": len(inv_lines), "ground_truth": len(gt),
    }
    print(f"\n  Row Counts:")
    for name, count in results["row_counts"].items():
        print(f"    {name:25s}: {count:>6,}")

    # Save
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(results, indent=2, default=str))
    print(f"\n  Saved: {OUT_PATH}")
    print("="*60)

if __name__ == "__main__":
    main()
