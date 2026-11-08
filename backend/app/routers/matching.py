"""
YottaPay AI – Matching Router

Full implementation of the three-way matching endpoints.
Delegates to ThreeWayMatchingEngine for the matching logic.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.matching.engine import ThreeWayMatchingEngine
from app.models.invoice_match import InvoiceMatch
from app.models.invoice import Invoice
from app.routers.auth import get_current_user

router = APIRouter(prefix="/matching", tags=["Matching"])


# ---------------------------------------------------------------------------
# POST /matching/run/{invoice_id}
# ---------------------------------------------------------------------------
@router.post(
    "/run/{invoice_id}",
    summary="Run three-way matching for an invoice",
    status_code=status.HTTP_200_OK,
)
def run_matching(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger three-way matching for the given invoice.

    Instantiates ThreeWayMatchingEngine and calls engine.run().
    Returns a summary with:
    - overall_status
    - checks summary (passed / failed / warning counts)
    - exceptions_created count
    - invoice_id, match_id
    """
    # Verify invoice exists before spinning up the engine
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice '{invoice_id}' not found.",
        )

    actor = current_user.get("username", "system")
    engine = ThreeWayMatchingEngine(db)

    try:
        result = engine.run(invoice_id=invoice_id, actor=actor)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching engine error: {str(exc)}",
        )

    # Normalise result to a consistent response shape regardless of engine output format
    if isinstance(result, dict):
        overall_status = result.get("overall_status") or result.get("status", "UNKNOWN")
        check_results = result.get("check_results") or result.get("checks", {})
        exceptions_created = result.get("exceptions_created", 0)
        match_id = result.get("match_id") or result.get("id")
    else:
        # result is an InvoiceMatch ORM object
        overall_status = str(result.overall_status)
        check_results = result.check_results or {}
        exceptions_created = 0
        match_id = result.id

    # Build checks summary
    if isinstance(check_results, dict):
        checks_list = list(check_results.values()) if check_results else []
    elif isinstance(check_results, list):
        checks_list = check_results
    else:
        checks_list = []

    passed = sum(
        1 for c in checks_list
        if isinstance(c, dict) and c.get("passed") is True
    )
    failed = sum(
        1 for c in checks_list
        if isinstance(c, dict) and c.get("passed") is False
        and not c.get("warning", False)
    )
    warnings = sum(
        1 for c in checks_list
        if isinstance(c, dict) and c.get("warning") is True
    )

    return {
        "invoice_id": invoice_id,
        "match_id": match_id,
        "overall_status": overall_status,
        "checks_summary": {
            "total": len(checks_list),
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
        },
        "exceptions_created": exceptions_created,
        "actor": actor,
    }


# ---------------------------------------------------------------------------
# GET /matching/results/{invoice_id}
# ---------------------------------------------------------------------------
@router.get(
    "/results/{invoice_id}",
    summary="Get latest matching result for an invoice",
)
def get_matching_result(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Return the most recent InvoiceMatch record for the given invoice.

    Includes all fields (check_results JSON, individual check flags, tolerances, etc.).
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice '{invoice_id}' not found.",
        )

    match = (
        db.query(InvoiceMatch)
        .filter(InvoiceMatch.invoice_id == invoice_id)
        .order_by(InvoiceMatch.match_run_at.desc())
        .first()
    )

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No matching results found for invoice '{invoice_id}'. Run matching first.",
        )

    return {
        "id": match.id,
        "invoice_id": match.invoice_id,
        "po_id": match.po_id,
        "grn_id": match.grn_id,
        "match_run_at": match.match_run_at,
        "overall_status": str(match.overall_status),
        "check_results": match.check_results,
        # Individual check flags
        "vendor_valid": match.vendor_valid,
        "po_exists": match.po_exists,
        "sku_matched": match.sku_matched,
        "qty_matched": match.qty_matched,
        "price_matched": match.price_matched,
        "tax_matched": match.tax_matched,
        "arithmetic_valid": match.arithmetic_valid,
        "receipt_matched": match.receipt_matched,
        "is_duplicate": match.is_duplicate,
        # Tolerances
        "price_tolerance_pct": float(match.price_tolerance_pct) if match.price_tolerance_pct is not None else None,
        "qty_tolerance_pct": float(match.qty_tolerance_pct) if match.qty_tolerance_pct is not None else None,
        "matched_by": match.matched_by,
        "notes": match.notes,
    }


# ---------------------------------------------------------------------------
# GET /matching/history/{invoice_id}
# ---------------------------------------------------------------------------
@router.get(
    "/history/{invoice_id}",
    summary="Get full matching history for an invoice",
)
def get_matching_history(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Return all InvoiceMatch records for the given invoice, most recent first.

    Useful for auditing re-runs and tracking matching progression.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice '{invoice_id}' not found.",
        )

    matches = (
        db.query(InvoiceMatch)
        .filter(InvoiceMatch.invoice_id == invoice_id)
        .order_by(InvoiceMatch.match_run_at.desc())
        .all()
    )

    return [
        {
            "id": m.id,
            "invoice_id": m.invoice_id,
            "po_id": m.po_id,
            "grn_id": m.grn_id,
            "match_run_at": m.match_run_at,
            "overall_status": str(m.overall_status),
            "check_results": m.check_results,
            "vendor_valid": m.vendor_valid,
            "po_exists": m.po_exists,
            "sku_matched": m.sku_matched,
            "qty_matched": m.qty_matched,
            "price_matched": m.price_matched,
            "tax_matched": m.tax_matched,
            "arithmetic_valid": m.arithmetic_valid,
            "receipt_matched": m.receipt_matched,
            "is_duplicate": m.is_duplicate,
            "price_tolerance_pct": float(m.price_tolerance_pct) if m.price_tolerance_pct is not None else None,
            "qty_tolerance_pct": float(m.qty_tolerance_pct) if m.qty_tolerance_pct is not None else None,
            "matched_by": m.matched_by,
            "notes": m.notes,
        }
        for m in matches
    ]
