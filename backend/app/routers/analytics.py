"""
YottaPay AI – Analytics Router

Full implementation that calls AnalyticsService and returns real data from MySQL.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.analytics.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", summary="Dashboard summary cards")
def dashboard_summary(db: Session = Depends(get_db)):
    """
    Return high-level KPI cards for the main dashboard.

    Includes:
    - Vendor counts (total, active)
    - PO count
    - Invoice counts (total, matched, exception)
    - Open exception count
    - Pending approval count
    - Payment ready count
    - Total paid amount
    """
    return AnalyticsService.get_dashboard_summary(db)


@router.get("/matching", summary="Matching distribution for pie chart")
def matching_distribution(db: Session = Depends(get_db)):
    """
    Return counts of invoices grouped by matching_status.

    Use for a pie or donut chart showing matching outcomes.
    """
    return AnalyticsService.get_matching_distribution(db)


@router.get("/exceptions", summary="Exception distribution by type")
def exception_distribution(db: Session = Depends(get_db)):
    """
    Return counts of invoice exceptions grouped by exception_type.

    Use for a bar or donut chart showing exception breakdown.
    """
    return AnalyticsService.get_exception_distribution(db)


@router.get("/payments", summary="Payment status distribution")
def payment_distribution(db: Session = Depends(get_db)):
    """
    Return counts of payment records grouped by status.

    Use for a bar or pie chart showing the payment pipeline status.
    """
    return AnalyticsService.get_payment_distribution(db)


@router.get("/monthly-volume", summary="Monthly invoice volume for bar chart")
def monthly_volume(
    months: int = Query(12, ge=1, le=24, description="Number of months to include"),
    db: Session = Depends(get_db),
):
    """
    Return monthly invoice counts and total amounts for the last N months.

    Use for a bar or line chart showing invoice volume over time.
    Each entry has: month (YYYY-MM), invoice_count, total_amount.
    """
    return AnalyticsService.get_monthly_volume(db, months=months)
