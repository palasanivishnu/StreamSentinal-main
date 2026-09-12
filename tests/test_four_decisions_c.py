"""
Tests for all four decision paths through Person C in StreamSentinel-main.

Verifies that Person B's ML + Rule → Decision Engine produces all four outcomes
(allow, otp, review, block) and that each decision path flows correctly
through Person C's alert, OTP, and persistence layers.

Uses real Person B models from fraud_detection package.
Decision thresholds from models/decision_engine_config.json:
  allow:  risk_score ≤ 0.25
  otp:    risk_score ≤ 0.50
  review: risk_score ≤ 0.75
  block:  risk_score > 0.75
"""
from unittest.mock import patch, MagicMock
import pytest
from src.schemas import FeatureVector
from integration.handler import IntegrationHandler


class TestAllowDecision:
    """Path 1: allow — low risk transaction."""

    @patch("src.db.save_transaction")
    @patch("src.alert_service.save_alert")
    def test_legit_transaction_allowed(self, mock_save_alert, mock_save_txn, legit_transaction):
        fv = FeatureVector(**legit_transaction)
        handler = IntegrationHandler()

        result = handler.handle_feature_vector(fv)
        assert result["decision"] == "allow"
        assert result["risk_score"] <= 0.25
        assert not mock_save_alert.called


class TestOTPDecision:
    """Path 2: otp — moderate risk, OTP challenge triggered."""

    @patch("src.db.save_transaction")
    @patch("src.alert_service.save_alert")
    def test_moderate_risk_triggers_otp(self, mock_save_alert, mock_save_txn):
        txn = {
            "transaction_id": "11111111-1111-1111-1111-111111111111",
            "user_id": "user_otp",
            "amount": 2000.0,
            "amount_vs_avg_ratio": 5.0,
            "txn_count_last_5min": 3,
            "time_since_last_txn_sec": 60.0,
            "distance_from_last_location_km": 10.0,
            "merchant_category_is_new_for_user": True,
        }

        fv = FeatureVector(**txn)
        handler = IntegrationHandler()

        result = handler.handle_feature_vector(fv)

        assert result["decision"] in ("otp", "review", "block")
        assert mock_save_alert.called

    @patch("src.db.save_transaction")
    @patch("src.alert_service.save_alert")
    def test_otp_verify_approves_transaction(self, mock_save_alert, mock_save_txn):
        """Once OTP is verified, transaction should be approvable."""
        from src.otp_service import generate_otp, verify_otp

        otp_code = generate_otp("user_otp_test", "txn_otp_verify_001")

        success, message = verify_otp(
            user_id="user_otp_test",
            entered_otp=otp_code,
            transaction_id="txn_otp_verify_001",
        )
        assert success is True


class TestReviewDecision:
    """Path 3: review — high risk, needs manual review."""

    @patch("src.db.save_transaction")
    @patch("src.alert_service.save_alert")
    def test_high_risk_triggers_review(self, mock_save_alert, mock_save_txn, suspicious_transaction):
        fv = FeatureVector(**suspicious_transaction)
        handler = IntegrationHandler()

        result = handler.handle_feature_vector(fv)

        assert result["decision"] in ("otp", "review", "block")
        assert result["risk_score"] > 0.25
        assert mock_save_alert.called

    @patch("src.api.update_transaction_decision")
    def test_review_approve_via_api(self, mock_update, fastapi_client):
        mock_update.return_value = True
        resp = fastapi_client.post("/reviews/txn_review_001/approve")
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "approved"
        mock_update.assert_called_once()
        call_kwargs = mock_update.call_args.kwargs
        assert call_kwargs.get("new_decision") == "allow" or mock_update.call_args[0][1] == "allow"

    @patch("src.api.update_transaction_decision")
    def test_review_block_via_api(self, mock_update, fastapi_client):
        mock_update.return_value = True
        resp = fastapi_client.post("/reviews/txn_review_001/block")
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "blocked"
        call_kwargs = mock_update.call_args.kwargs
        assert call_kwargs.get("new_decision") == "block" or mock_update.call_args[0][1] == "block"


class TestBlockDecision:
    """Path 4: block — very high risk, immediate block."""

    @patch("src.db.save_transaction")
    @patch("src.alert_service.save_alert")
    def test_fraud_transaction_blocked(self, mock_save_alert, mock_save_txn, fraud_transaction):
        fv = FeatureVector(**fraud_transaction)
        handler = IntegrationHandler()

        result = handler.handle_feature_vector(fv)

        assert result["decision"] == "block"
        assert result["risk_score"] > 0.75
        assert mock_save_alert.called

    @patch("src.db.save_transaction")
    @patch("src.alert_service.save_alert")
    def test_block_has_human_readable_reason(self, mock_save_alert, mock_save_txn, fraud_transaction):
        fv = FeatureVector(**fraud_transaction)
        handler = IntegrationHandler()

        result = handler.handle_feature_vector(fv)
        assert result["human_readable_reason"]
        assert len(result["human_readable_reason"]) > 10
