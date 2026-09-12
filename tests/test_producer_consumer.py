"""Tests for Producer, Consumer, Simulator, and end-to-end Person A pipeline."""

import json
import fakeredis
import pytest
from src.consumer import StreamSentinelConsumer
from src.producer import StreamSentinelProducer
from src.schemas import FeatureVector, TransactionEvent
from src.simulator import (
    DatasetReader,
    TransactionSimulator,
    format_to_uuid,
    parse_csv_row_to_event,
)
from src.state_manager import RedisStateManager


def test_format_to_uuid():
    # 32-hex string
    hex_str = "2da90c7d74bd46a0caf3777415b3ebd3"
    u = format_to_uuid(hex_str)
    assert len(u) == 36
    assert u == "2da90c7d-74bd-46a0-caf3-777415b3ebd3"

    # Arbitrary non-hex string uses uuid5
    u2 = format_to_uuid("txn-12345")
    assert len(u2) == 36


def test_parse_csv_row():
    mock_row = {
        "trans_num": "2da90c7d74bd46a0caf3777415b3ebd3",
        "trans_date_trans_time": "2020-06-21 12:14:25",
        "cc_num": "2291163933867244",
        "merchant": "fraud_Kirlin and Sons",
        "category": "personal_care",
        "amt": "2.86",
        "lat": "33.9659",
        "long": "-80.9355",
        "is_fraud": "0",
    }
    event, is_fraud = parse_csv_row_to_event(mock_row)
    assert is_fraud is False
    assert event.user_id == "2291163933867244"
    assert event.amount == 2.86
    assert event.currency == "USD"
    assert event.merchant_id == "fraud_Kirlin and Sons"
    assert event.merchant_category == "personal_care"
    assert event.location.lat == 33.9659
    assert event.location.lon == -80.9355
    assert "2020-06-21" in event.timestamp


def test_producer_partitions_by_user_id():
    """Verify that Producer publishes with key = user_id."""
    published_records = []

    def mock_transport(topic, key, value):
        published_records.append({"topic": topic, "key": key, "value": value})

    producer = StreamSentinelProducer(mock_transport=mock_transport)

    event = TransactionEvent(
        transaction_id="11111111-1111-1111-1111-111111111111",
        user_id="user_test_partition",
        amount=50.0,
        currency="USD",
        merchant_id="merchant_1",
        merchant_category="grocery",
        location={"lat": 10.0, "lon": 20.0},
        timestamp="2026-09-06T12:00:00Z",
    )

    producer.publish_transaction(event)

    assert len(published_records) == 1
    # Crucial guarantee: message key MUST be user_id
    assert published_records[0]["key"] == "user_test_partition"
    val = json.loads(published_records[0]["value"])
    assert val["user_id"] == "user_test_partition"
    assert val["amount"] == 50.0


def test_end_to_end_simulator_to_feature_vector():
    """End-to-end integration:

    Dataset -> Simulator -> Producer (key=user_id) -> Consumer -> RedisStateManager -> Feature Vector
    """
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    state_mgr = RedisStateManager(redis_client=fake_redis, key_prefix="e2e_test")

    emitted_feature_vectors = []

    consumer = StreamSentinelConsumer(
        state_manager=state_mgr,
        mock_mode=True,
        on_feature_vector=lambda fv: emitted_feature_vectors.append(fv),
    )

    # Route producer directly to consumer's raw message processor
    def pipe_transport(topic, key, value):
        # Assert key is user_id
        parsed = json.loads(value)
        assert key == parsed["user_id"]
        consumer.process_raw_message(value)

    producer = StreamSentinelProducer(mock_transport=pipe_transport)

    # Replay 5 transactions from our extracted sample
    simulator = TransactionSimulator(
        producer=producer,
        dataset_path="data/fraud_sample.csv",
        rate_per_sec=100.0,  # Fast replay for test
    )

    count = simulator.replay(limit=5)
    assert count == 5
    assert len(emitted_feature_vectors) == 5

    # Check the emitted Feature Vector conforms strictly to the contract
    for fv in emitted_feature_vectors:
        assert isinstance(fv, FeatureVector)
        assert fv.transaction_id
        assert fv.user_id
        assert fv.amount > 0
        assert fv.amount_vs_avg_ratio > 0
        assert fv.txn_count_last_5min >= 1
        assert fv.time_since_last_txn_sec >= 0.0
        assert fv.distance_from_last_location_km >= 0.0
        assert isinstance(fv.merchant_category_is_new_for_user, bool)


def test_simulator_trigger_on_demand_fraud():
    """Verify on-demand fraud triggering for live team demos."""
    captured = []

    def capture_transport(topic, key, value):
        captured.append(json.loads(value))

    producer = StreamSentinelProducer(mock_transport=capture_transport)
    simulator = TransactionSimulator(
        producer=producer,
        dataset_path="data/fraud_sample.csv",
    )

    fraud_event = simulator.trigger_on_demand_fraud()
    assert fraud_event is not None
    assert len(captured) == 1
    assert captured[0]["transaction_id"] == fraud_event.transaction_id
