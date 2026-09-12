"""End-to-end integration tests: Simulator → StateManager → FeatureVector → DetectionService.

Tests the full pipeline without Kafka, using fakeredis for state management.
"""

import pytest
import fakeredis

from src.schemas import FeatureVector, TransactionEvent, Location
from src.state_manager import RedisStateManager
from fraud_detection.detection_service import score_transaction
from integration.handler import IntegrationHandler


SCORING_OUTPUT_FIELDS = {
    "transaction_id", "user_id", "risk_score", "rule_flags",
    "ml_fraud_score", "decision", "human_readable_reason",
    "processed_at", "latency_ms",
}


@pytest.fixture
def state_manager():
    """Create a state manager with fakeredis."""
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    return RedisStateManager(redis_client=fake_redis, key_prefix="e2e_test")


@pytest.fixture
def handler():
    """Create an integration handler."""
    return IntegrationHandler()


class TestEndToEndPipeline:
    """Full pipeline tests: Transaction → Redis → FeatureVector → Detection → ScoringOutput."""

    def test_single_transaction_through_full_pipeline(self, state_manager, handler):
        """A single transaction should flow through the entire pipeline."""
        event = TransactionEvent(
            transaction_id="11111111-1111-1111-1111-111111111111",
            user_id="e2e_user_001",
            amount=100.0,
            currency="USD",
            merchant_id="merchant_test",
            merchant_category="grocery",
            location=Location(lat=40.7128, lon=-74.0060),
            timestamp="2026-09-06T12:00:00Z",
        )

        # Person A: process transaction through state manager
        fv = state_manager.process_transaction(event)
        assert isinstance(fv, FeatureVector)

        # Integration: pass to Person B via handler
        result = handler.handle_feature_vector(fv)

        # Validate scoring output
        assert result is not None
        assert set(result.keys()) == SCORING_OUTPUT_FIELDS
        assert result["transaction_id"] == "11111111-1111-1111-1111-111111111111"
        assert result["user_id"] == "e2e_user_001"
        assert result["decision"] in ("allow", "otp", "review", "block")
        assert result["latency_ms"] > 0

    def test_direct_fv_to_detection_service(self, state_manager):
        """Test bypassing the handler, calling score_transaction directly."""
        event = TransactionEvent(
            transaction_id="22222222-2222-2222-2222-222222222222",
            user_id="direct_test_user",
            amount=75.0,
            currency="USD",
            merchant_id="m1",
            merchant_category="electronics",
            location=Location(lat=35.6762, lon=139.6503),
            timestamp="2026-09-06T12:05:00Z",
        )

        fv = state_manager.process_transaction(event)
        fv_dict = fv.model_dump()

        # Call Person B directly
        result = score_transaction(fv_dict)
        assert result["transaction_id"] == "22222222-2222-2222-2222-222222222222"
        assert result["decision"] in ("allow", "otp", "review", "block")

    def test_sequential_transactions_same_user(self, state_manager, handler):
        """Multiple sequential transactions for the same user build up state correctly."""
        results = []
        base_time = "2026-09-06T12:00:00Z"

        for i in range(5):
            minutes = i * 2
            event = TransactionEvent(
                transaction_id=f"{i+1:08d}-0000-0000-0000-000000000000",
                user_id="sequential_user",
                amount=100.0 * (i + 1),
                currency="USD",
                merchant_id=f"merchant_{i}",
                merchant_category="grocery" if i % 2 == 0 else "electronics",
                location=Location(lat=40.0 + i * 0.01, lon=-74.0),
                timestamp=f"2026-09-06T12:{minutes:02d}:00Z",
            )

            fv = state_manager.process_transaction(event)
            result = handler.handle_feature_vector(fv)
            assert result is not None
            results.append(result)

        # All 5 transactions should have produced valid results
        assert len(results) == 5
        for r in results:
            assert r["decision"] in ("allow", "otp", "review", "block")

    def test_feature_vector_contract_preserved(self, state_manager):
        """Verify the FeatureVector from state manager has all expected fields."""
        event = TransactionEvent(
            transaction_id="33333333-3333-3333-3333-333333333333",
            user_id="contract_test_user",
            amount=42.50,
            currency="USD",
            merchant_id="m1",
            merchant_category="gas_station",
            location=Location(lat=37.7749, lon=-122.4194),
            timestamp="2026-09-06T14:00:00Z",
        )

        fv = state_manager.process_transaction(event)
        fv_dict = fv.model_dump()

        expected_keys = {
            "transaction_id", "user_id", "amount",
            "amount_vs_avg_ratio", "txn_count_last_5min",
            "time_since_last_txn_sec", "distance_from_last_location_km",
            "merchant_category_is_new_for_user",
        }
        assert expected_keys.issubset(set(fv_dict.keys()))

        # Type checks
        assert isinstance(fv_dict["transaction_id"], str)
        assert isinstance(fv_dict["user_id"], str)
        assert isinstance(fv_dict["amount"], float)
        assert isinstance(fv_dict["amount_vs_avg_ratio"], float)
        assert isinstance(fv_dict["txn_count_last_5min"], int)
        assert isinstance(fv_dict["time_since_last_txn_sec"], float)
        assert isinstance(fv_dict["distance_from_last_location_km"], float)
        assert isinstance(fv_dict["merchant_category_is_new_for_user"], bool)
