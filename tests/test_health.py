"""
Tests for health check endpoints — real dependency connectivity validation.
"""
from unittest.mock import patch, MagicMock
import pytest


class TestHealthBasic:
    """Basic /health endpoint tests."""

    def test_health_always_returns_200(self, fastapi_client):
        resp = fastapi_client.get("/health")
        assert resp.status_code == 200

    def test_health_contains_status(self, fastapi_client):
        data = fastapi_client.get("/health").json()
        assert data["status"] == "healthy"

    def test_health_contains_environment(self, fastapi_client):
        data = fastapi_client.get("/health").json()
        assert "environment" in data

    def test_health_contains_timestamp(self, fastapi_client):
        data = fastapi_client.get("/health").json()
        assert "timestamp" in data


class TestServicesHealth:
    """Dependency health check tests."""

    def test_services_health_lists_multiple_services(self, fastapi_client, mock_mongo):
        mock_mongo["client"].admin.command.return_value = {"ok": 1}
        data = fastapi_client.get("/health/services").json()
        service_names = [s["name"] for s in data["services"]]
        assert "mongodb" in service_names
        assert "fastapi" in service_names
        assert "prometheus_endpoint" in service_names

    def test_services_healthy_when_mongo_up(self, fastapi_client, mock_mongo):
        mock_mongo["client"].admin.command.return_value = {"ok": 1}
        resp = fastapi_client.get("/health/services")
        data = resp.json()
        assert data["overall"] == "healthy", f"Unexpected health response: {data}"

    def test_services_degraded_when_mongo_down(self, fastapi_client, mock_mongo):
        mock_mongo["client"].admin.command.side_effect = Exception("timeout")
        data = fastapi_client.get("/health/services").json()
        assert data["overall"] == "degraded"

    def test_mongo_unhealthy_detail(self, fastapi_client, mock_mongo):
        mock_mongo["client"].admin.command.side_effect = Exception("Connection refused")
        data = fastapi_client.get("/health/services").json()
        mongo_svc = next(s for s in data["services"] if s["name"] == "mongodb")
        assert mongo_svc["status"] == "unhealthy"
        assert "Connection refused" in mongo_svc["detail"]

    @patch("src.db.client", None)
    def test_mongo_unhealthy_when_client_none(self, fastapi_client):
        data = fastapi_client.get("/health/services").json()
        assert data["overall"] == "degraded"
        mongo_svc = next(s for s in data["services"] if s["name"] == "mongodb")
        assert mongo_svc["status"] == "unhealthy"
        assert "not initialized" in mongo_svc["detail"].lower()
