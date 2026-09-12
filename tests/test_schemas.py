"""Unit tests for TransactionEvent and FeatureVector schemas."""

import json
import pytest
from pydantic import ValidationError

from src.schemas import FeatureVector, Location, TransactionEvent


def test_valid_transaction_event():
    event = TransactionEvent(
        transaction_id="12345678-1234-5678-1234-567812345678",
        user_id="user_test_99",
        amount=42.50,
        currency="USD",
        merchant_id="merchant_99",
        merchant_category="grocery_pos",
        location=Location(lat=37.7749, lon=-122.4194),
        timestamp="2026-09-06T12:30:00Z",
    )
    assert event.user_id == "user_test_99"
    assert event.amount == 42.50
    assert event.currency == "USD"
    assert event.location.lat == 37.7749
    assert event.location.lon == -122.4194

    # Verify JSON serializability
    dumped = json.loads(event.model_dump_json())
    assert dumped["transaction_id"] == "12345678-1234-5678-1234-567812345678"
    assert dumped["location"] == {"lat": 37.7749, "lon": -122.4194}


def test_invalid_uuid_in_transaction_event():
    with pytest.raises(ValidationError):
        TransactionEvent(
            transaction_id="not-a-valid-uuid",
            user_id="user_test_99",
            amount=42.50,
            currency="USD",
            merchant_id="merchant_99",
            merchant_category="grocery_pos",
            location=Location(lat=37.7749, lon=-122.4194),
            timestamp="2026-09-06T12:30:00Z",
        )


def test_feature_vector_schema():
    fv = FeatureVector(
        transaction_id="12345678-1234-5678-1234-567812345678",
        user_id="user_test_99",
        amount=42.50,
        amount_vs_avg_ratio=1.25,
        txn_count_last_5min=3,
        time_since_last_txn_sec=45.2,
        distance_from_last_location_km=0.35,
        merchant_category_is_new_for_user=False,
    )
    data = json.loads(fv.model_dump_json())
    # Confirm exact contract keys
    expected_keys = {
        "transaction_id",
        "user_id",
        "amount",
        "amount_vs_avg_ratio",
        "txn_count_last_5min",
        "time_since_last_txn_sec",
        "distance_from_last_location_km",
        "merchant_category_is_new_for_user",
    }
    assert expected_keys.issubset(set(data.keys()))
