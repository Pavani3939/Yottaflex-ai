"""
YottaPay AI – API Endpoint Tests

Tests health check, authentication, and core API patterns.
"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "app" in data
        assert data["app"] == "YottaPay AI"
        assert data["version"] == "1.0.0"

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data


class TestAuthEndpoints:
    def test_login_success(self, client):
        response = client.post(
            "/api/auth/token",
            data={"username": "admin", "password": "password123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        response = client.post(
            "/api/auth/token",
            data={"username": "admin", "password": "wrongpass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 401

    def test_login_unknown_user(self, client):
        response = client.post(
            "/api/auth/token",
            data={"username": "nobody", "password": "password123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 401

    def test_me_endpoint(self, client, auth_headers):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"

    def test_protected_route_no_token(self, client):
        response = client.get("/api/vendors")
        assert response.status_code == 401


class TestVendorEndpoints:
    def test_list_vendors(self, client, auth_headers):
        response = client.get("/api/vendors", headers=auth_headers)
        assert response.status_code == 200

    def test_get_vendor_not_found(self, client, auth_headers):
        response = client.get("/api/vendors/VND-99999", headers=auth_headers)
        assert response.status_code == 404


class TestInvoiceEndpoints:
    def test_list_invoices(self, client, auth_headers):
        response = client.get("/api/invoices", headers=auth_headers)
        assert response.status_code == 200


class TestMatchingEndpoints:
    def test_matching_result_not_found(self, client, auth_headers):
        response = client.get("/api/matching/results/FAKE-INV", headers=auth_headers)
        assert response.status_code == 404


class TestAuditEndpoints:
    def test_list_audit_events(self, client, auth_headers):
        response = client.get("/api/audit-events", headers=auth_headers)
        assert response.status_code == 200

    def test_get_audit_event_not_found(self, client, auth_headers):
        response = client.get("/api/audit-events/EVT-nonexistent", headers=auth_headers)
        assert response.status_code == 404


class TestOpenAPISchema:
    def test_openapi_json(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "YottaPay AI"
        assert "/api/auth/token" in str(data["paths"].keys())
