"""
Tests for src.api — FastAPI platform API routes.
"""
from unittest.mock import patch, MagicMock
import pytest


class TestHealthEndpoints:
    """Health check endpoint tests."""

    def test_health_returns_200(self, fastapi_client):
        resp = fastapi_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_health_services_returns_200(self, fastapi_client, mock_mongo):
        mock_mongo["client"].admin.command.return_value = {"ok": 1}
        resp = fastapi_client.get("/health/services")
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall"] in ("healthy", "degraded")
        assert len(data["services"]) >= 2

    def test_health_services_degraded_when_mongo_down(self, fastapi_client, mock_mongo):
        mock_mongo["client"].admin.command.side_effect = Exception("Connection refused")
        resp = fastapi_client.get("/health/services")
        data = resp.json()
        assert data["overall"] == "degraded"
        mongo_svc = next(s for s in data["services"] if s["name"] == "mongodb")
        assert mongo_svc["status"] == "unhealthy"


class TestTransactionEndpoints:
    """Transaction CRUD endpoint tests."""

    @patch("src.api.get_recent_transactions")
    def test_list_transactions(self, mock_get, fastapi_client):
        mock_get.return_value = [{"transaction_id": "txn_001", "decision": "allow"}]
        resp = fastapi_client.get("/transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["transactions"][0]["transaction_id"] == "txn_001"

    @patch("src.api.get_recent_transactions")
    def test_list_transactions_with_decision_filter(self, mock_get, fastapi_client):
        mock_get.return_value = []
        resp = fastapi_client.get("/transactions?decision=block")
        assert resp.status_code == 200
        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs.get("filter_query", {}).get("decision") == "block"

    @patch("src.api.get_recent_transactions")
    def test_list_transactions_invalid_decision(self, mock_get, fastapi_client):
        resp = fastapi_client.get("/transactions?decision=invalid")
        assert resp.status_code == 422  # Validation error

    def test_get_transaction_found(self, fastapi_client, mock_mongo):
        mock_mongo["transactions_col"].find_one.return_value = {
            "_id": MagicMock(__str__=lambda s: "abc"),
            "transaction_id": "txn_001",
            "decision": "allow",
        }
        resp = fastapi_client.get("/transactions/txn_001")
        assert resp.status_code == 200

    def test_get_transaction_not_found(self, fastapi_client, mock_mongo):
        mock_mongo["transactions_col"].find_one.return_value = None
        resp = fastapi_client.get("/transactions/txn_missing")
        assert resp.status_code == 404


class TestUserEndpoints:
    """User transaction endpoint tests."""

    @patch("src.api.get_recent_transactions")
    def test_get_user_transactions(self, mock_get, fastapi_client):
        mock_get.return_value = [
            {"transaction_id": "txn_001", "user_id": "user_42"}
        ]
        resp = fastapi_client.get("/users/user_42/transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "user_42"
        assert data["count"] == 1


class TestAlertEndpoints:
    """Alert endpoint tests."""

    @patch("src.api.get_alerts_feed")
    def test_list_alerts(self, mock_get, fastapi_client):
        mock_get.return_value = [{"alert_id": "alert_001", "severity": "HIGH"}]
        resp = fastapi_client.get("/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1

    def test_get_alert_found(self, fastapi_client, mock_mongo):
        mock_mongo["alerts_col"].find_one.return_value = {
            "_id": MagicMock(__str__=lambda s: "xyz"),
            "alert_id": "alert_001",
            "severity": "CRITICAL",
        }
        resp = fastapi_client.get("/alerts/alert_001")
        assert resp.status_code == 200

    def test_get_alert_not_found(self, fastapi_client, mock_mongo):
        mock_mongo["alerts_col"].find_one.return_value = None
        resp = fastapi_client.get("/alerts/alert_missing")
        assert resp.status_code == 404

    @patch("src.api.acknowledge_alert")
    def test_acknowledge_alert_success(self, mock_ack, fastapi_client):
        mock_ack.return_value = True
        resp = fastapi_client.post("/alerts/alert_001/acknowledge")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    @patch("src.api.acknowledge_alert")
    def test_acknowledge_alert_not_found(self, mock_ack, fastapi_client):
        mock_ack.return_value = False
        resp = fastapi_client.post("/alerts/alert_missing/acknowledge")
        assert resp.status_code == 404


class TestReviewEndpoints:
    """Review workflow endpoint tests."""

    @patch("src.api.get_recent_transactions")
    def test_list_reviews(self, mock_get, fastapi_client):
        mock_get.return_value = [
            {"transaction_id": "txn_001", "decision": "review"},
        ]
        resp = fastapi_client.get("/reviews")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1

    @patch("src.api.update_transaction_decision")
    def test_approve_review(self, mock_update, fastapi_client):
        mock_update.return_value = True
        resp = fastapi_client.post("/reviews/txn_001/approve")
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "approved"

    @patch("src.api.update_transaction_decision")
    def test_block_review(self, mock_update, fastapi_client):
        mock_update.return_value = True
        resp = fastapi_client.post("/reviews/txn_001/block")
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "blocked"

    @patch("src.api.update_transaction_decision")
    def test_approve_review_not_found(self, mock_update, fastapi_client):
        mock_update.return_value = False
        resp = fastapi_client.post("/reviews/txn_missing/approve")
        assert resp.status_code == 404


class TestOTPEndpoint:
    """OTP verification endpoint tests."""

    @patch("src.api.verify_otp")
    def test_otp_verify_success(self, mock_verify, fastapi_client):
        mock_verify.return_value = (True, "OTP verified successfully")
        resp = fastapi_client.post(
            "/otp/verify",
            json={"user_id": "user_42", "otp_code": "123456"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "verified" in data["message"].lower()

    @patch("src.api.verify_otp")
    def test_otp_verify_failure(self, mock_verify, fastapi_client):
        mock_verify.return_value = (False, "Invalid OTP code")
        resp = fastapi_client.post(
            "/otp/verify",
            json={"user_id": "user_42", "otp_code": "000000"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False


class TestAnalyticsEndpoints:
    """Analytics endpoint tests."""

    @patch("src.api.get_dashboard_metrics")
    def test_analytics_summary(self, mock_metrics, fastapi_client):
        mock_metrics.return_value = {
            "total_transactions": 100,
            "allow_count": 70,
            "otp_count": 15,
            "review_count": 10,
            "block_count": 5,
        }
        resp = fastapi_client.get("/analytics/summary")
        assert resp.status_code == 200

    @patch("src.api.get_dashboard_metrics")
    def test_analytics_decisions(self, mock_metrics, fastapi_client):
        mock_metrics.return_value = {
            "total_transactions": 100,
            "allow_count": 70,
            "otp_count": 15,
            "review_count": 10,
            "block_count": 5,
        }
        resp = fastapi_client.get("/analytics/decisions")
        assert resp.status_code == 200
        data = resp.json()
        assert "decisions" in data
        assert "allow" in data["decisions"]
        assert data["decisions"]["allow"]["count"] == 70
        assert data["decisions"]["allow"]["percentage"] == 70.0

    def test_analytics_latency(self, fastapi_client, mock_mongo):
        mock_mongo["transactions_col"].aggregate.return_value = iter(
            [
                {
                    "_id": None,
                    "avg_latency_ms": 42.5,
                    "min_latency_ms": 10.0,
                    "max_latency_ms": 150.0,
                    "count": 50,
                }
            ]
        )
        resp = fastapi_client.get("/analytics/latency")
        assert resp.status_code == 200
        data = resp.json()
        assert data["avg_latency_ms"] == 42.5


class TestMetricsEndpoint:
    """Prometheus metrics endpoint tests."""

    def test_metrics_returns_prometheus_format(self, fastapi_client):
        resp = fastapi_client.get("/metrics")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers.get("content-type", "")
        assert "streamsentinel_" in resp.text
