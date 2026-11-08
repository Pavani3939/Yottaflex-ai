"""
YottaPay AI – Pytest Fixtures (conftest.py)

Provides shared fixtures for database sessions, test client, and authentication.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date
from decimal import Decimal

# Ensure the backend root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Mock database session fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_db():
    """Provide a mock SQLAlchemy Session."""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.filter_by.return_value = session
    session.order_by.return_value = session
    session.offset.return_value = session
    session.limit.return_value = session
    session.count.return_value = 0
    session.all.return_value = []
    session.first.return_value = None
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.refresh = MagicMock()
    session.close = MagicMock()
    return session


# ---------------------------------------------------------------------------
# FastAPI TestClient fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def client():
    """Create a FastAPI TestClient with DB dependency overridden."""
    # Patch database connection check to avoid needing a real DB
    with patch("app.database.connection.check_database_connection", return_value=True):
        from app.main import app
        from app.database.connection import get_db
        from fastapi.testclient import TestClient

        mock_session = MagicMock()

        def override_get_db():
            try:
                yield mock_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        test_client = TestClient(app)
        yield test_client
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth token fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def auth_headers(client):
    """
    Return Authorization headers after logging in as admin.
    Uses the built-in demo accounts (admin / password123).
    """
    response = client.post(
        "/api/auth/token",
        data={"username": "admin", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    # If auth fails (no real DB), create a mock JWT
    import jwt
    token = jwt.encode(
        {"sub": "admin", "role": "admin", "exp": datetime(2099, 1, 1).timestamp()},
        "yottapay-secret-key-change-in-production",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_vendor_data():
    """Sample vendor creation payload."""
    return {
        "vendor_name": "Test Vendor Corp",
        "vendor_code": "VND00999",
        "tax_id": "99-9999999",
        "address": "123 Test Street, TestCity, TS 99999",
        "contact_name": "John Test",
        "contact_email": "john@testvendor.com",
        "contact_phone": "+1-555-999-9999",
        "payment_terms": "Net 30",
        "bank_account": "9999999999",
        "bank_routing": "999999999",
        "status": "active",
    }


@pytest.fixture
def sample_po_data():
    """Sample purchase order creation payload."""
    return {
        "vendor_id": "VND-00001",
        "po_date": "2026-10-15",
        "delivery_date": "2026-11-15",
        "status": "OPEN",
        "currency": "USD",
        "lines": [
            {
                "line_number": 1,
                "sku": "SKU-TEST-001",
                "description": "Test Widget",
                "quantity": 100,
                "unit_price": 25.00,
                "unit_of_measure": "EA",
            }
        ],
    }


@pytest.fixture
def sample_invoice_data():
    """Sample invoice creation payload."""
    return {
        "invoice_number": "INV-TEST-001",
        "vendor_id": "VND-00001",
        "po_id": "PO-2026-000001",
        "invoice_date": "2026-10-20",
        "due_date": "2026-11-20",
        "currency": "USD",
        "subtotal": 2500.00,
        "tax_amount": 200.00,
        "discount_amount": 0.00,
        "total_amount": 2700.00,
        "lines": [
            {
                "line_number": 1,
                "sku": "SKU-TEST-001",
                "description": "Test Widget",
                "quantity": 100,
                "unit_price": 25.00,
                "line_total": 2500.00,
            }
        ],
    }
