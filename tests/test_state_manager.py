"""Unit tests for RedisStateManager and feature vector emission."""

import pytest
import fakeredis
from src.schemas import TransactionEvent, Location, FeatureVector
from src.state_manager import RedisStateManager, haversine_distance_km


@pytest.fixture
def fake_redis_client():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def state_manager(fake_redis_client):
    return RedisStateManager(redis_client=fake_redis_client, key_prefix="test_sentinel")


def test_haversine_distance():
    # NYC (40.7128, -74.0060) to LA (34.0522, -118.2437) ~ 3935 km
    dist = haversine_distance_km(40.7128, -74.0060, 34.0522, -118.2437)
    assert 3900 < dist < 4000

    # Same location
    dist_same = haversine_distance_km(40.7128, -74.0060, 40.7128, -74.0060)
    assert dist_same == 0.0


def test_first_transaction_features(state_manager):
    event = TransactionEvent(
        transaction_id="11111111-1111-1111-1111-111111111111",
        user_id="user_123",
        amount=100.0,
        currency="USD",
        merchant_id="merchant_abc",
        merchant_category="grocery",
        location=Location(lat=40.7128, lon=-74.0060),
        timestamp="2026-09-06T12:00:00Z",
    )

    fv = state_manager.process_transaction(event)

    assert isinstance(fv, FeatureVector)
    assert fv.transaction_id == "11111111-1111-1111-1111-111111111111"
    assert fv.user_id == "user_123"
    assert fv.amount == 100.0
    assert fv.amount_vs_avg_ratio == 1.0  # First transaction ratio is 1.0
    assert fv.txn_count_last_5min == 1
    assert fv.time_since_last_txn_sec == 0.0
    assert fv.distance_from_last_location_km == 0.0
    assert fv.merchant_category_is_new_for_user is True


def test_subsequent_transactions_rolling_updates(state_manager):
    # Txn 1: 100.0 at 12:00:00 at lat 40.0, lon -74.0, category grocery
    t1 = TransactionEvent(
        transaction_id="11111111-1111-1111-1111-111111111111",
        user_id="user_test",
        amount=100.0,
        currency="USD",
        merchant_id="m1",
        merchant_category="grocery",
        location=Location(lat=40.0, lon=-74.0),
        timestamp="2026-09-06T12:00:00Z",
    )
    fv1 = state_manager.process_transaction(t1)
    assert fv1.amount_vs_avg_ratio == 1.0
    assert fv1.merchant_category_is_new_for_user is True

    # Txn 2: 200.0 at 12:02:00 (120s later) in category grocery (not new)
    t2 = TransactionEvent(
        transaction_id="22222222-2222-2222-2222-222222222222",
        user_id="user_test",
        amount=200.0,
        currency="USD",
        merchant_id="m2",
        merchant_category="grocery",
        location=Location(lat=40.1, lon=-74.0),
        timestamp="2026-09-06T12:02:00Z",
    )
    fv2 = state_manager.process_transaction(t2)
    # Previous avg was 100.0. Current amount is 200.0 -> ratio is 2.0!
    assert fv2.amount_vs_avg_ratio == 2.0
    assert fv2.time_since_last_txn_sec == 120.0
    assert fv2.txn_count_last_5min == 2
    assert fv2.distance_from_last_location_km > 0.0
    assert fv2.merchant_category_is_new_for_user is False  # Grocery seen before!

    # Txn 3: 150.0 at 12:04:00 (120s later) in category electronics (new category)
    t3 = TransactionEvent(
        transaction_id="33333333-3333-3333-3333-333333333333",
        user_id="user_test",
        amount=150.0,
        currency="USD",
        merchant_id="m3",
        merchant_category="electronics",
        location=Location(lat=40.1, lon=-74.0),
        timestamp="2026-09-06T12:04:00Z",
    )
    fv3 = state_manager.process_transaction(t3)
    # Prior average: (100 + 200) / 2 = 150.0. Current is 150.0 -> ratio is 1.0!
    assert fv3.amount_vs_avg_ratio == 1.0
    assert fv3.txn_count_last_5min == 3
    assert fv3.merchant_category_is_new_for_user is True  # electronics is new!

    # Txn 4: at 12:06:00 (360 seconds after Txn 1).
    # Txn 1 at 12:00:00 should have dropped out of the 5-minute (300s) window!
    # Txn 2 (12:02:00) is 240s ago (< 300s), Txn 3 (12:04:00) is 120s ago (< 300s).
    # Txn 4 is now. Total in 5m window = 3 (Txn 2, Txn 3, Txn 4).
    t4 = TransactionEvent(
        transaction_id="44444444-4444-4444-4444-444444444444",
        user_id="user_test",
        amount=50.0,
        currency="USD",
        merchant_id="m4",
        merchant_category="electronics",
        location=Location(lat=40.1, lon=-74.0),
        timestamp="2026-09-06T12:06:00Z",
    )
    fv4 = state_manager.process_transaction(t4)
    assert fv4.txn_count_last_5min == 3  # Txn 1 aged out
    assert fv4.time_since_last_txn_sec == 120.0
    assert fv4.merchant_category_is_new_for_user is False
