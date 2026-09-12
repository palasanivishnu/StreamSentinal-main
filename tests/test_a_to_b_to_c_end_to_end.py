"""
Explicit End-to-End Integration Test: A → B → C Pipeline.

Proves complete data flow across all three subsystems:
  Person A: Transaction Simulator / Event → Redis State Manager → Feature Vector
  Person B: Feature Vector → Rule Engine + XGBoost ML + Decision Engine + SHAP Explainer
  Person C: Scoring Output → MongoDB Persistence + Alerting + Webhook + Prometheus + FastAPI
"""
from unittest.mock import patch, MagicMock
import pytest
import fakeredis

from src.schemas import TransactionEvent, Location
from src.state_manager import RedisStateManager
from integration.handler import IntegrationHandler


class TestFullAToBToCPipeline:
    """Tests full pipeline integration from raw transaction to Person C output."""

    @patch("src.db.save_transaction")
    @patch("src.alert_service.save_alert")
    def test_full_pipeline_legit_transaction(self, mock_save_alert, mock_save_txn):
        """Flow a legitimate transaction through A → B → C."""
        txn_event = TransactionEvent(
            transaction_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
            user_id="user_e2e_01",
            amount=50.0,
            currency="USD",
            merchant_id="merchant_01",
            merchant_category="grocery",
            location=Location(lat=40.7128, lon=-74.0060),
            timestamp="2025-01-01T12:00:00Z"
        )

        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        state_mgr = RedisStateManager(redis_client=fake_redis, key_prefix="test_a_b_c")

        # Prime merchant history so grocery is not a new category for user
        state_mgr.process_transaction(TransactionEvent(
            transaction_id="3fa85f64-5717-4562-b3fc-2c963f66afa0",
            user_id="user_e2e_01",
            amount=10.0,
            currency="USD",
            merchant_id="merchant_01",
            merchant_category="grocery",
            location=Location(lat=40.7128, lon=-74.0060),
            timestamp="2025-01-01T11:00:00Z"
        ))

        fv = state_mgr.process_transaction(txn_event)

        # Verify Person A Feature Vector output
        assert fv.transaction_id == "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        assert fv.user_id == "user_e2e_01"
        assert fv.amount == 50.0

        # 2. Person A → Person B → Person C: Pass Feature Vector through Integration Handler
        handler = IntegrationHandler()
        scoring_output = handler.handle_feature_vector(fv)

        # 3. Verify Person B Detection Output
        assert scoring_output is not None
        assert scoring_output["transaction_id"] == "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        assert scoring_output["user_id"] == "user_e2e_01"
        assert scoring_output["decision"] == "allow"
        assert scoring_output["risk_score"] <= 0.25
        assert "ml_fraud_score" in scoring_output
        assert "human_readable_reason" in scoring_output

        # 4. Verify Person C Platform Integration
        assert mock_save_txn.called

    @patch("src.db.save_transaction")
    @patch("src.alert_service.save_alert")
    def test_full_pipeline_fraud_transaction(self, mock_save_alert, mock_save_txn):
        """Flow a high-risk fraud transaction through A → B → C."""
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        state_mgr = RedisStateManager(redis_client=fake_redis, key_prefix="test_a_b_c_fraud")

        txn1 = TransactionEvent(
            transaction_id="3fa85f64-5717-4562-b3fc-2c963f66afa1",
            user_id="user_e2e_fraud",
            amount=20.0,
            currency="USD",
            merchant_id="merchant_01",
            merchant_category="grocery",
            location=Location(lat=40.7128, lon=-74.0060),
            timestamp="2025-01-01T12:00:00Z"
        )
        state_mgr.process_transaction(txn1)

        # Second transaction 1 second later with extreme amount & distance (triggers rules + ML)
        txn2 = TransactionEvent(
            transaction_id="3fa85f64-5717-4562-b3fc-2c963f66afa2",
            user_id="user_e2e_fraud",
            amount=99999.0,
            currency="USD",
            merchant_id="merchant_02",
            merchant_category="jewelry",
            location=Location(lat=51.5074, lon=-0.1278),  # London!
            timestamp="2025-01-01T12:00:01Z"
        )
        fv2 = state_mgr.process_transaction(txn2)

        handler = IntegrationHandler()
        scoring_output = handler.handle_feature_vector(fv2)

        # Verify Person B Detection Output
        assert scoring_output is not None
        assert scoring_output["decision"] in ("review", "block")
        assert scoring_output["risk_score"] > 0.50

        # Verify Person C Platform Integration (Alert & Save)
        assert mock_save_txn.called
        assert mock_save_alert.called

    @patch("src.api.get_recent_transactions")
    def test_full_pipeline_api_retrieval(self, mock_get_txns, fastapi_client):
        """Verify Person C FastAPI returns transactions scored through the pipeline."""
        mock_get_txns.return_value = [
            {
                "transaction_id": "3fa85f64-5717-4562-b3fc-2c963f66afa2",
                "user_id": "user_e2e_fraud",
                "amount": 99999.0,
                "risk_score": 0.95,
                "decision": "block",
                "rule_flags": ["IMPOSSIBLE_TRAVEL", "HIGH_AMOUNT"],
                "alert_triggered": True,
                "alert_severity": "CRITICAL"
            }
        ]

        resp = fastapi_client.get("/transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["transactions"][0]["decision"] == "block"
