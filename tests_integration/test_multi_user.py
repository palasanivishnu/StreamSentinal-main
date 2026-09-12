"""Multi-user integration tests.

Tests multiple users with sequential transactions and validates that:
1. Each user's state is independent.
2. Multiple users can be scored in sequence.
3. The full A→B pipeline works for diverse user profiles.
"""

import pytest
import json
import fakeredis

from src.schemas import FeatureVector, TransactionEvent, Location
from src.state_manager import RedisStateManager
from src.consumer import StreamSentinelConsumer
from src.producer import StreamSentinelProducer
from fraud_detection.detection_service import score_transaction
from integration.handler import IntegrationHandler


@pytest.fixture
def state_manager():
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    return RedisStateManager(redis_client=fake_redis, key_prefix="multi_user_test")


@pytest.fixture
def handler():
    return IntegrationHandler()


class TestMultiUser:
    """Tests for multiple concurrent users."""

    def test_two_independent_users(self, state_manager, handler):
        """Two different users should have independent state and scoring."""
        # User A: normal transaction
        event_a = TransactionEvent(
            transaction_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            user_id="user_alpha",
            amount=50.0,
            currency="USD",
            merchant_id="m1",
            merchant_category="grocery",
            location=Location(lat=40.7128, lon=-74.0060),
            timestamp="2026-09-06T12:00:00Z",
        )

        # User B: suspicious transaction
        event_b = TransactionEvent(
            transaction_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            user_id="user_beta",
            amount=5000.0,
            currency="USD",
            merchant_id="m2",
            merchant_category="electronics",
            location=Location(lat=35.6762, lon=139.6503),
            timestamp="2026-09-06T12:00:00Z",
        )

        fv_a = state_manager.process_transaction(event_a)
        fv_b = state_manager.process_transaction(event_b)

        result_a = handler.handle_feature_vector(fv_a)
        result_b = handler.handle_feature_vector(fv_b)

        assert result_a is not None
        assert result_b is not None
        assert result_a["user_id"] == "user_alpha"
        assert result_b["user_id"] == "user_beta"
        assert result_a["transaction_id"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        assert result_b["transaction_id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    def test_multiple_users_interleaved(self, state_manager, handler):
        """Multiple users with interleaved transactions."""
        users = ["user_001", "user_002", "user_003"]
        results = {u: [] for u in users}

        for i in range(9):
            user = users[i % 3]
            event = TransactionEvent(
                transaction_id=f"{i+1:08d}-0000-0000-0000-000000000000",
                user_id=user,
                amount=50.0 * (i + 1),
                currency="USD",
                merchant_id=f"merchant_{i}",
                merchant_category=["grocery", "electronics", "restaurant"][i % 3],
                location=Location(lat=40.0 + i * 0.1, lon=-74.0 + i * 0.1),
                timestamp=f"2026-09-06T12:{i:02d}:00Z",
            )

            fv = state_manager.process_transaction(event)
            result = handler.handle_feature_vector(fv)
            assert result is not None
            results[user].append(result)

        # Each user should have 3 results
        for user in users:
            assert len(results[user]) == 3
            for r in results[user]:
                assert r["user_id"] == user
                assert r["decision"] in ("allow", "otp", "review", "block")

    def test_full_mock_pipeline_multi_user(self, state_manager, handler):
        """Full pipeline with mock Kafka transport for multiple users."""
        emitted_fvs = []
        scoring_outputs = []

        def on_fv(fv: FeatureVector):
            emitted_fvs.append(fv)
            result = handler.handle_feature_vector(fv)
            if result:
                scoring_outputs.append(result)

        consumer = StreamSentinelConsumer(
            state_manager=state_manager,
            mock_mode=True,
            on_feature_vector=on_fv,
        )

        def mock_broker(topic, key, value):
            consumer.process_raw_message(value)

        producer = StreamSentinelProducer(mock_transport=mock_broker)

        # Publish events for different users
        events = [
            TransactionEvent(
                transaction_id=f"{i+1:08d}-0000-0000-0000-000000000000",
                user_id=f"mock_user_{i % 3}",
                amount=100.0 * (i + 1),
                currency="USD",
                merchant_id=f"m_{i}",
                merchant_category=["grocery", "electronics", "restaurant"][i % 3],
                location=Location(lat=40.0, lon=-74.0),
                timestamp=f"2026-09-06T12:{i:02d}:00Z",
            )
            for i in range(6)
        ]

        for event in events:
            producer.publish_transaction(event)

        assert len(emitted_fvs) == 6
        assert len(scoring_outputs) == 6

        for output in scoring_outputs:
            assert "risk_score" in output
            assert "decision" in output
            assert output["decision"] in ("allow", "otp", "review", "block")
