"""Integration tests: Person A FeatureVector → Person B Detection Service.

Tests the core integration boundary: FeatureVector.model_dump() → score_transaction().
Validates that Person B's detection service accepts Person A's output and produces
a valid Scoring Output conforming to the B→C contract.
"""

import pytest
from src.schemas import FeatureVector
from fraud_detection.detection_service import score_transaction


# Required fields in the Scoring Output (Person B → Person C contract)
SCORING_OUTPUT_FIELDS = {
    "transaction_id",
    "user_id",
    "risk_score",
    "rule_flags",
    "ml_fraud_score",
    "decision",
    "human_readable_reason",
    "processed_at",
    "latency_ms",
}

VALID_DECISIONS = {"allow", "otp", "review", "block"}


def _make_feature_vector(**overrides) -> FeatureVector:
    """Helper to create a FeatureVector with sensible defaults."""
    defaults = {
        "transaction_id": "11111111-1111-1111-1111-111111111111",
        "user_id": "test_user_001",
        "amount": 50.0,
        "amount_vs_avg_ratio": 1.0,
        "txn_count_last_5min": 1,
        "time_since_last_txn_sec": 300.0,
        "distance_from_last_location_km": 5.0,
        "merchant_category_is_new_for_user": False,
    }
    defaults.update(overrides)
    return FeatureVector(**defaults)


class TestAToB:
    """Tests for the A→B integration boundary."""

    def test_basic_feature_vector_to_scoring_output(self):
        """FeatureVector.model_dump() produces a valid input for score_transaction()."""
        fv = _make_feature_vector()
        fv_dict = fv.model_dump()

        result = score_transaction(fv_dict)

        # Validate all required output fields exist
        assert set(result.keys()) == SCORING_OUTPUT_FIELDS

        # Validate field types
        assert isinstance(result["transaction_id"], str)
        assert isinstance(result["user_id"], str)
        assert isinstance(result["risk_score"], float)
        assert isinstance(result["rule_flags"], list)
        assert isinstance(result["ml_fraud_score"], float)
        assert isinstance(result["decision"], str)
        assert isinstance(result["human_readable_reason"], str)
        assert isinstance(result["processed_at"], str)
        assert isinstance(result["latency_ms"], float)

    def test_scoring_output_decision_is_valid(self):
        """Decision must be one of allow/otp/review/block."""
        fv = _make_feature_vector()
        result = score_transaction(fv.model_dump())
        assert result["decision"] in VALID_DECISIONS

    def test_transaction_id_preserved(self):
        """transaction_id must pass through unchanged."""
        test_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        fv = _make_feature_vector(transaction_id=test_id)
        result = score_transaction(fv.model_dump())
        assert result["transaction_id"] == test_id

    def test_user_id_preserved(self):
        """user_id must pass through unchanged."""
        fv = _make_feature_vector(user_id="my_special_user")
        result = score_transaction(fv.model_dump())
        assert result["user_id"] == "my_special_user"

    def test_risk_score_in_valid_range(self):
        """Risk score must be between 0 and 1."""
        fv = _make_feature_vector()
        result = score_transaction(fv.model_dump())
        assert 0.0 <= result["risk_score"] <= 1.0

    def test_ml_fraud_score_in_valid_range(self):
        """ML fraud score must be between 0 and 1."""
        fv = _make_feature_vector()
        result = score_transaction(fv.model_dump())
        assert 0.0 <= result["ml_fraud_score"] <= 1.0

    def test_latency_is_positive(self):
        """Latency must be a positive number."""
        fv = _make_feature_vector()
        result = score_transaction(fv.model_dump())
        assert result["latency_ms"] > 0

    def test_human_readable_reason_not_empty(self):
        """Human-readable reason must not be empty."""
        fv = _make_feature_vector()
        result = score_transaction(fv.model_dump())
        assert len(result["human_readable_reason"]) > 0

    def test_processed_at_is_iso8601(self):
        """processed_at must be a valid ISO 8601 string."""
        from datetime import datetime
        fv = _make_feature_vector()
        result = score_transaction(fv.model_dump())
        # Should parse without error
        dt = datetime.fromisoformat(result["processed_at"])
        assert dt is not None

    def test_rule_flags_are_strings(self):
        """All rule flags must be strings."""
        fv = _make_feature_vector(
            amount_vs_avg_ratio=10.0,
            merchant_category_is_new_for_user=True,
        )
        result = score_transaction(fv.model_dump())
        for flag in result["rule_flags"]:
            assert isinstance(flag, str)

    def test_boolean_field_handled_correctly(self):
        """Person A emits bool; Person B must handle it (int(True)==1)."""
        fv_true = _make_feature_vector(merchant_category_is_new_for_user=True)
        result = score_transaction(fv_true.model_dump())
        assert "NEW_MERCHANT_CATEGORY" in result["rule_flags"]

        fv_false = _make_feature_vector(merchant_category_is_new_for_user=False)
        result2 = score_transaction(fv_false.model_dump())
        assert "NEW_MERCHANT_CATEGORY" not in result2["rule_flags"]
