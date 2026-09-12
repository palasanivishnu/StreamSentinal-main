"""
Tests for B → C Integration in StreamSentinel-main.

Verifies that Person B's scoring output correctly flows through
Person C's platform layer: MongoDB persistence, alert generation,
webhook dispatch, Prometheus metrics, and API retrieval.

Person B's detection logic is NOT mocked — these tests use the real
ML model, rule engine, decision engine, and SHAP explainer.
MongoDB and webhook are mocked (no external infrastructure required).
"""
from unittest.mock import patch, MagicMock, call
import pytest
from src.schemas import FeatureVector
from integration.handler import IntegrationHandler


class TestScoringToMongoDB:
    """Verify handler execution persists transaction output to MongoDB."""

    @patch("src.db.save_transaction")
    @patch("src.alert_service.save_alert")
    def test_handler_calls_save(self, mock_save_alert, mock_save_txn, sample_transaction):
        fv = FeatureVector(**sample_transaction)
        handler = IntegrationHandler()

        result = handler.handle_feature_vector(fv)

        mock_save_txn.assert_called_once()
        saved_data = mock_save_txn.call_args[0][0]
        assert saved_data["transaction_id"] == "11111111-1111-1111-1111-111111111111"
        assert "risk_score" in saved_data
        assert "decision" in saved_data
        assert "ml_fraud_score" in saved_data

    @patch("src.db.save_transaction")
    @patch("src.alert_service.save_alert")
    def test_saved_record_has_all_enriched_fields(self, mock_save_alert, mock_save_txn, sample_transaction):
        fv = FeatureVector(**sample_transaction)
        handler = IntegrationHandler()

        result = handler.handle_feature_vector(fv)
        saved_data = mock_save_txn.call_args[0][0]

        required_fields = [
            "transaction_id", "user_id", "amount",
            "amount_vs_avg_ratio", "txn_count_last_5min",
            "time_since_last_txn_sec", "distance_from_last_location_km",
            "merchant_category_is_new_for_user",
            "risk_score", "rule_flags", "ml_fraud_score",
            "decision", "human_readable_reason",
            "processed_at", "latency_ms",
            "alert_triggered", "otp_status",
        ]
        for field in required_fields:
            assert field in saved_data, f"Missing field in saved record: {field}"


class TestScoringToAlerts:
    """Verify high-risk transactions trigger alert service."""

    @patch("src.db.save_transaction")
    @patch("src.alert_service.save_alert")
    def test_alert_service_called_for_suspicious(self, mock_save_alert, mock_save_txn, suspicious_transaction):
        fv = FeatureVector(**suspicious_transaction)
        handler = IntegrationHandler()

        result = handler.handle_feature_vector(fv)
        assert mock_save_alert.called


class TestScoringMetrics:
    """Verify Prometheus metrics are recorded during scoring."""

    @patch("src.db.save_transaction")
    @patch("src.alert_service.save_alert")
    def test_transactions_processed_incremented(self, mock_save_alert, mock_save_txn, sample_transaction):
        from src.metrics import TRANSACTIONS_PROCESSED

        before = TRANSACTIONS_PROCESSED._value.get()
        fv = FeatureVector(**sample_transaction)
        handler = IntegrationHandler()

        handler.handle_feature_vector(fv)
        assert TRANSACTIONS_PROCESSED._value.get() == before + 1

    @patch("src.db.save_transaction")
    @patch("src.alert_service.save_alert")
    def test_detection_latency_recorded(self, mock_save_alert, mock_save_txn, sample_transaction):
        from src.metrics import DETECTION_LATENCY

        before = DETECTION_LATENCY._sum.get()
        fv = FeatureVector(**sample_transaction)
        handler = IntegrationHandler()

        handler.handle_feature_vector(fv)
        assert DETECTION_LATENCY._sum.get() > before

    @patch("src.db.save_transaction")
    @patch("src.alert_service.save_alert")
    def test_decision_counter_incremented(self, mock_save_alert, mock_save_txn, sample_transaction):
        from src.metrics import DECISIONS_TOTAL

        fv = FeatureVector(**sample_transaction)
        handler = IntegrationHandler()

        result = handler.handle_feature_vector(fv)
        decision = result["decision"]
        count = DECISIONS_TOTAL.labels(decision=decision)._value.get()
        assert count > 0


class TestScoringToWebhook:
    """Verify webhook is dispatched through the alert service chain."""

    @patch("src.webhook_service.WEBHOOK_URL", "https://test.example.com/hook")
    @patch("src.webhook_service.httpx.post")
    @patch("src.db.save_transaction")
    def test_webhook_dispatched_on_alert(self, mock_save_txn, mock_post, suspicious_transaction):
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        fv = FeatureVector(**suspicious_transaction)
        handler = IntegrationHandler()

        result = handler.handle_feature_vector(fv)
        assert mock_post.called


class TestAPIRetrieval:
    """Verify scored transactions can be retrieved via API."""

    @patch("src.api.get_recent_transactions")
    def test_scored_transaction_retrievable(self, mock_get, fastapi_client):
        mock_get.return_value = [
            {
                "transaction_id": "txn_test_001",
                "decision": "allow",
                "risk_score": 0.15,
            }
        ]
        resp = fastapi_client.get("/transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["transactions"][0]["transaction_id"] == "txn_test_001"
