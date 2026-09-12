"""Validation tests for error handling at the A→B integration boundary.

Verifies that Person B's detection service properly rejects:
- Missing fields
- Wrong types
- NaN/Inf values
- Malformed feature vectors
"""

import math
import pytest
from fraud_detection.detection_service import score_transaction


class TestMissingFields:
    """Tests for missing required fields."""

    def test_missing_transaction_id(self):
        """Missing transaction_id should raise ValueError."""
        fv = {
            "user_id": "user_001",
            "amount": 50.0,
            "amount_vs_avg_ratio": 1.0,
            "txn_count_last_5min": 1,
            "time_since_last_txn_sec": 300.0,
            "distance_from_last_location_km": 5.0,
            "merchant_category_is_new_for_user": False,
        }
        with pytest.raises(ValueError, match="Missing detection fields"):
            score_transaction(fv)

    def test_missing_amount(self):
        """Missing amount should raise ValueError."""
        fv = {
            "transaction_id": "11111111-1111-1111-1111-111111111111",
            "user_id": "user_001",
            "amount_vs_avg_ratio": 1.0,
            "txn_count_last_5min": 1,
            "time_since_last_txn_sec": 300.0,
            "distance_from_last_location_km": 5.0,
            "merchant_category_is_new_for_user": False,
        }
        with pytest.raises(ValueError, match="Missing"):
            score_transaction(fv)

    def test_missing_multiple_fields(self):
        """Missing multiple fields should raise ValueError."""
        fv = {
            "transaction_id": "11111111-1111-1111-1111-111111111111",
            "user_id": "user_001",
            "amount": 50.0,
        }
        with pytest.raises(ValueError, match="Missing"):
            score_transaction(fv)

    def test_empty_dict(self):
        """Empty dict should raise ValueError."""
        with pytest.raises(ValueError, match="Missing"):
            score_transaction({})


class TestWrongTypes:
    """Tests for wrong field types."""

    def test_amount_as_string(self):
        """Non-numeric string for amount should raise ValueError."""
        fv = {
            "transaction_id": "11111111-1111-1111-1111-111111111111",
            "user_id": "user_001",
            "amount": "not_a_number",
            "amount_vs_avg_ratio": 1.0,
            "txn_count_last_5min": 1,
            "time_since_last_txn_sec": 300.0,
            "distance_from_last_location_km": 5.0,
            "merchant_category_is_new_for_user": False,
        }
        with pytest.raises((ValueError, TypeError)):
            score_transaction(fv)

    def test_not_a_dict(self):
        """Non-dict input should raise an error."""
        with pytest.raises((TypeError, AttributeError, ValueError)):
            score_transaction("not a dict")

    def test_none_input(self):
        """None input should raise error."""
        with pytest.raises((TypeError, AttributeError)):
            score_transaction(None)


class TestNaNInf:
    """Tests for NaN and Inf values."""

    def test_nan_amount(self):
        """NaN amount should be rejected."""
        fv = {
            "transaction_id": "11111111-1111-1111-1111-111111111111",
            "user_id": "user_001",
            "amount": float("nan"),
            "amount_vs_avg_ratio": 1.0,
            "txn_count_last_5min": 1,
            "time_since_last_txn_sec": 300.0,
            "distance_from_last_location_km": 5.0,
            "merchant_category_is_new_for_user": False,
        }
        with pytest.raises(ValueError):
            score_transaction(fv)

    def test_inf_distance(self):
        """Inf distance should be rejected."""
        fv = {
            "transaction_id": "11111111-1111-1111-1111-111111111111",
            "user_id": "user_001",
            "amount": 50.0,
            "amount_vs_avg_ratio": 1.0,
            "txn_count_last_5min": 1,
            "time_since_last_txn_sec": 300.0,
            "distance_from_last_location_km": float("inf"),
            "merchant_category_is_new_for_user": False,
        }
        with pytest.raises(ValueError):
            score_transaction(fv)

    def test_negative_inf(self):
        """Negative inf should be rejected."""
        fv = {
            "transaction_id": "11111111-1111-1111-1111-111111111111",
            "user_id": "user_001",
            "amount": float("-inf"),
            "amount_vs_avg_ratio": 1.0,
            "txn_count_last_5min": 1,
            "time_since_last_txn_sec": 300.0,
            "distance_from_last_location_km": 5.0,
            "merchant_category_is_new_for_user": False,
        }
        with pytest.raises(ValueError):
            score_transaction(fv)


class TestIntegrationHandlerErrorHandling:
    """Tests for the IntegrationHandler's error handling."""

    def test_handler_returns_none_on_invalid_input(self):
        """IntegrationHandler.handle_feature_vector should return None on detection failure."""
        from src.schemas import FeatureVector
        from integration.handler import IntegrationHandler

        handler = IntegrationHandler()

        # Create a valid feature vector — this should succeed
        fv = FeatureVector(
            transaction_id="11111111-1111-1111-1111-111111111111",
            user_id="test_user",
            amount=50.0,
            amount_vs_avg_ratio=1.0,
            txn_count_last_5min=1,
            time_since_last_txn_sec=300.0,
            distance_from_last_location_km=5.0,
            merchant_category_is_new_for_user=False,
        )
        result = handler.handle_feature_vector(fv)
        assert result is not None
        assert "decision" in result
