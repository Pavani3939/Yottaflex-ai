"""
YottaPay AI – Analytics Service

Provides aggregated metrics and time-series data for the dashboard.
All queries run directly against the MySQL database via SQLAlchemy.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.approval import Approval, ApprovalStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_exception import InvoiceException, ExceptionStatus
from app.models.payment import Payment, PaymentStatus
from app.models.purchase_order import PurchaseOrder
from app.models.vendor import Vendor, VendorStatus


class AnalyticsService:
    """
    Aggregation service that powers dashboard charts and KPI cards.
    All methods accept a SQLAlchemy Session and return plain Python dicts/lists.
    """

    # ------------------------------------------------------------------
    # Dashboard summary (KPI cards)
    # ------------------------------------------------------------------

    @staticmethod
    def get_dashboard_summary(db: Session) -> dict:
        """
        Return counts and totals for the main dashboard KPI cards.

        Fields returned:
        - total_vendors, active_vendors
        - total_pos
        - total_invoices, matched_invoices, exception_invoices
        - open_exceptions
        - pending_approvals
        - payment_ready
        - total_paid_amount  (sum of payment amounts with status=PAID)
        """
        # Vendor counts
        total_vendors = db.query(func.count(Vendor.id)).scalar() or 0
        active_vendors = (
            db.query(func.count(Vendor.id))
            .filter(Vendor.status == VendorStatus.ACTIVE)
            .scalar()
            or 0
        )

        # Purchase order count
        total_pos = db.query(func.count(PurchaseOrder.id)).scalar() or 0

        # Invoice counts
        total_invoices = db.query(func.count(Invoice.id)).scalar() or 0
        matched_invoices = (
            db.query(func.count(Invoice.id))
            .filter(Invoice.status == InvoiceStatus.MATCHED)
            .scalar()
            or 0
        )
        exception_invoices = (
            db.query(func.count(Invoice.id))
            .filter(Invoice.status == InvoiceStatus.EXCEPTION)
            .scalar()
            or 0
        )

        # Open exceptions
        open_exceptions = (
            db.query(func.count(InvoiceException.id))
            .filter(InvoiceException.status == ExceptionStatus.OPEN)
            .scalar()
            or 0
        )

        # Pending approvals
        pending_approvals = (
            db.query(func.count(Approval.id))
            .filter(Approval.status == ApprovalStatus.PENDING)
            .scalar()
            or 0
        )

        # Payments ready
        payment_ready = (
            db.query(func.count(Payment.id))
            .filter(Payment.status == PaymentStatus.READY_FOR_PAYMENT)
            .scalar()
            or 0
        )

        # Total paid amount
        total_paid_amount = (
            db.query(func.sum(Payment.amount))
            .filter(Payment.status == PaymentStatus.PAID)
            .scalar()
        )
        total_paid_amount = float(total_paid_amount) if total_paid_amount is not None else 0.0

        return {
            "total_vendors": total_vendors,
            "active_vendors": active_vendors,
            "total_pos": total_pos,
            "total_invoices": total_invoices,
            "matched_invoices": matched_invoices,
            "exception_invoices": exception_invoices,
            "open_exceptions": open_exceptions,
            "pending_approvals": pending_approvals,
            "payment_ready": payment_ready,
            "total_paid_amount": total_paid_amount,
        }

    # ------------------------------------------------------------------
    # Distribution queries (for pie / donut / bar charts)
    # ------------------------------------------------------------------

    @staticmethod
    def get_matching_distribution(db: Session) -> List[dict]:
        """
        Return invoice counts grouped by matching_status.

        Returns a list of:
            [{"matching_status": "<status>", "count": <int>}, ...]
        """
        rows = (
            db.query(Invoice.matching_status, func.count(Invoice.id).label("count"))
            .group_by(Invoice.matching_status)
            .all()
        )
        return [
            {"matching_status": str(row.matching_status), "count": row.count}
            for row in rows
        ]

    @staticmethod
    def get_exception_distribution(db: Session) -> List[dict]:
        """
        Return exception counts grouped by exception_type.

        Returns a list of:
            [{"exception_type": "<type>", "count": <int>}, ...]
        """
        rows = (
            db.query(
                InvoiceException.exception_type,
                func.count(InvoiceException.id).label("count"),
            )
            .group_by(InvoiceException.exception_type)
            .all()
        )
        return [
            {"exception_type": str(row.exception_type), "count": row.count}
            for row in rows
        ]

    @staticmethod
    def get_payment_distribution(db: Session) -> List[dict]:
        """
        Return payment counts grouped by status.

        Returns a list of:
            [{"status": "<status>", "count": <int>}, ...]
        """
        rows = (
            db.query(Payment.status, func.count(Payment.id).label("count"))
            .group_by(Payment.status)
            .all()
        )
        return [
            {"status": str(row.status), "count": row.count}
            for row in rows
        ]

    @staticmethod
    def get_monthly_volume(db: Session, months: int = 12) -> List[dict]:
        """
        Return monthly invoice counts and total amounts for the last N months.

        Groups by YEAR and MONTH of invoice_date, most recent month last.

        Returns a list of:
            [{"month": "YYYY-MM", "invoice_count": <int>, "total_amount": <float>}, ...]
        """
        # Compute cutoff date (first day of the month N months ago)
        now = datetime.utcnow()
        # Go back `months` months from start of current month
        cutoff_month = now.month - months
        cutoff_year = now.year + (cutoff_month - 1) // 12
        cutoff_month = ((cutoff_month - 1) % 12) + 1
        cutoff = datetime(cutoff_year, cutoff_month, 1).date()

        rows = (
            db.query(
                func.year(Invoice.invoice_date).label("year"),
                func.month(Invoice.invoice_date).label("month"),
                func.count(Invoice.id).label("invoice_count"),
                func.sum(Invoice.total_amount).label("total_amount"),
            )
            .filter(Invoice.invoice_date >= cutoff)
            .group_by(
                func.year(Invoice.invoice_date),
                func.month(Invoice.invoice_date),
            )
            .order_by(
                func.year(Invoice.invoice_date).asc(),
                func.month(Invoice.invoice_date).asc(),
            )
            .all()
        )

        return [
            {
                "month": f"{row.year:04d}-{row.month:02d}",
                "invoice_count": row.invoice_count or 0,
                "total_amount": float(row.total_amount) if row.total_amount is not None else 0.0,
            }
            for row in rows
        ]
