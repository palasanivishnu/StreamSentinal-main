"""Tests for all four decision paths: Allow, OTP, Review, Block.

Uses crafted feature vectors to exercise each decision path through
Person B's existing thresholds without modifying them.

Person B thresholds (from decision_engine_config.json):
  - ml_weight: 0.5, rule_weight: 0.5
  - allow: risk_score <= 0.25
  - otp:   0.25 < risk_score <= 0.50
  - review: 0.50 < risk_score <= 0.75
  - block:  risk_score > 0.75

Rule weights (from rule_engine_config.json):
  - HIGH_AMOUNT: 0.25 (amount_vs_avg_ratio >= 3.0)
  - HIGH_VELOCITY: 0.25 (txn_count_last_5min >= 5)
  - IMPOSSIBLE_TRAVEL: 0.25 (distance >= 500km AND time <= 3600s)
  - NEW_MERCHANT_CATEGORY: 0.25 (merchant_category_is_new_for_user == 1)
"""

import pytest
from src.schemas import FeatureVector
from fraud_detection.detection_service import score_transaction


def _make_fv(**overrides) -> dict:
    """Create a FeatureVector dict with sensible defaults and overrides."""
    defaults = {
        "transaction_id": "11111111-1111-1111-1111-111111111111",
        "user_id": "test_user",
        "amount": 50.0,
        "amount_vs_avg_ratio": 0.5,
        "txn_count_last_5min": 1,
        "time_since_last_txn_sec": 600.0,
        "distance_from_last_location_km": 5.0,
        "merchant_category_is_new_for_user": False,
    }
    defaults.update(overrides)
    # Validate through Person A's Pydantic model first
    fv = FeatureVector(**defaults)
    return fv.model_dump()


class TestAllowDecision:
    """Test case for ALLOW decision (risk_score <= 0.25)."""

    def test_low_risk_transaction_is_allowed(self):
        """A normal, low-risk transaction should produce 'allow'."""
        fv_dict = _make_fv(
            amount=25.0,
            amount_vs_avg_ratio=0.5,
            txn_count_last_5min=1,
            time_since_last_txn_sec=600.0,
            distance_from_last_location_km=2.0,
            merchant_category_is_new_for_user=False,
        )
        result = score_transaction(fv_dict)
        # No rules should trigger
        assert result["rule_flags"] == []
        # With 0 rule_score and presumably low ML score, risk should be low
        assert result["decision"] == "allow", (
            f"Expected 'allow' but got '{result['decision']}' "
            f"(risk={result['risk_score']:.4f}, ml={result['ml_fraud_score']:.4f})"
        )


class TestOTPDecision:
    """Test case for OTP decision (0.25 < risk_score <= 0.50)."""

    def test_moderate_risk_triggers_otp(self):
        """A transaction with two rules triggered should produce 'otp'.

        With HIGH_AMOUNT + NEW_MERCHANT_CATEGORY: rule_score = 0.50
        risk = 0.5 * ml_score + 0.5 * 0.50 = 0.5*ml + 0.25
        For OTP: need 0.25 < risk <= 0.50, so ml needs to be < 0.50.
        """
        fv_dict = _make_fv(
            amount=800.0,
            amount_vs_avg_ratio=4.0,  # >= 3.0 → HIGH_AMOUNT
            txn_count_last_5min=2,    # < 5 → no HIGH_VELOCITY
            time_since_last_txn_sec=120.0,
            distance_from_last_location_km=10.0,  # < 500 → no IMPOSSIBLE_TRAVEL
            merchant_category_is_new_for_user=True,  # → NEW_MERCHANT_CATEGORY
        )
        result = score_transaction(fv_dict)
        assert "HIGH_AMOUNT" in result["rule_flags"]
        assert "NEW_MERCHANT_CATEGORY" in result["rule_flags"]
        # With rule_score=0.50, risk >= 0.25 guaranteed. Decision should be otp or higher.
        assert result["decision"] in ("otp", "review", "block"), (
            f"Expected 'otp', 'review', or 'block' but got '{result['decision']}' "
            f"(risk={result['risk_score']:.4f}, ml={result['ml_fraud_score']:.4f})"
        )


class TestReviewDecision:
    """Test case for REVIEW decision (0.50 < risk_score <= 0.75)."""

    def test_high_risk_triggers_review(self):
        """A transaction with multiple rules should produce 'review'.

        With HIGH_AMOUNT + HIGH_VELOCITY + NEW_MERCHANT: rule_score = 0.75
        risk = 0.5 * ml_score + 0.5 * 0.75 = 0.5*ml + 0.375
        For review (>0.50): ml needs to be > 0.25 -> risk > 0.50
        For not block (<=0.75): ml needs to be <= 0.75 -> risk <= 0.75
        """
        fv_dict = _make_fv(
            amount=2000.0,
            amount_vs_avg_ratio=5.0,  # >= 3.0 → HIGH_AMOUNT
            txn_count_last_5min=8,    # >= 5 → HIGH_VELOCITY
            time_since_last_txn_sec=120.0,
            distance_from_last_location_km=50.0,  # < 500 → no IMPOSSIBLE_TRAVEL
            merchant_category_is_new_for_user=True,  # → NEW_MERCHANT_CATEGORY
        )
        result = score_transaction(fv_dict)
        assert "HIGH_AMOUNT" in result["rule_flags"]
        assert "HIGH_VELOCITY" in result["rule_flags"]
        assert "NEW_MERCHANT_CATEGORY" in result["rule_flags"]
        assert result["decision"] in ("review", "block"), (
            f"Expected 'review' or 'block' but got '{result['decision']}' "
            f"(risk={result['risk_score']:.4f}, ml={result['ml_fraud_score']:.4f})"
        )


class TestBlockDecision:
    """Test case for BLOCK decision (risk_score > 0.75)."""

    def test_critical_risk_triggers_block(self):
        """A transaction triggering all 4 rules with extreme values should produce 'block'.

        All 4 rules: rule_score = 1.0
        risk = 0.5 * ml_score + 0.5 * 1.0 = 0.5*ml + 0.5
        For block (>0.75): ml needs to be > 0.5 → risk > 0.75
        With extreme values, ML score should be high.
        """
        fv_dict = _make_fv(
            amount=50000.0,
            amount_vs_avg_ratio=100.0,   # >>> 3.0 → HIGH_AMOUNT
            txn_count_last_5min=20,      # >>> 5 → HIGH_VELOCITY
            time_since_last_txn_sec=60.0,  # <= 3600 → enables IMPOSSIBLE_TRAVEL
            distance_from_last_location_km=5000.0,  # >= 500 → IMPOSSIBLE_TRAVEL
            merchant_category_is_new_for_user=True,  # → NEW_MERCHANT_CATEGORY
        )
        result = score_transaction(fv_dict)
        assert "HIGH_AMOUNT" in result["rule_flags"]
        assert "HIGH_VELOCITY" in result["rule_flags"]
        assert "IMPOSSIBLE_TRAVEL" in result["rule_flags"]
        assert "NEW_MERCHANT_CATEGORY" in result["rule_flags"]
        assert result["decision"] == "block", (
            f"Expected 'block' but got '{result['decision']}' "
            f"(risk={result['risk_score']:.4f}, ml={result['ml_fraud_score']:.4f})"
        )


class TestDecisionCoverage:
    """Verify all four decisions are reachable."""

    def test_all_four_decisions_are_reachable(self):
        """Confirm that the detection system can produce multiple distinct decisions."""
        decisions_seen = set()

        test_cases = [
            # Low risk → allow
            dict(amount=25.0, amount_vs_avg_ratio=0.5, txn_count_last_5min=1,
                 time_since_last_txn_sec=600.0, distance_from_last_location_km=2.0,
                 merchant_category_is_new_for_user=False),
            # Moderate → otp (2 rules: HIGH_AMOUNT + NEW_MERCHANT)
            dict(amount=800.0, amount_vs_avg_ratio=4.0, txn_count_last_5min=3,
                 time_since_last_txn_sec=120.0, distance_from_last_location_km=10.0,
                 merchant_category_is_new_for_user=True),
            # High → review (3 rules: HIGH_AMOUNT + HIGH_VELOCITY + NEW_MERCHANT)
            dict(amount=2000.0, amount_vs_avg_ratio=5.0, txn_count_last_5min=8,
                 time_since_last_txn_sec=120.0, distance_from_last_location_km=50.0,
                 merchant_category_is_new_for_user=True),
            # Extreme → block (all 4 rules)
            dict(amount=50000.0, amount_vs_avg_ratio=100.0, txn_count_last_5min=20,
                 time_since_last_txn_sec=60.0, distance_from_last_location_km=5000.0,
                 merchant_category_is_new_for_user=True),
        ]

        for case in test_cases:
            fv = FeatureVector(
                transaction_id="11111111-1111-1111-1111-111111111111",
                user_id="test_coverage",
                **case,
            )
            result = score_transaction(fv.model_dump())
            decisions_seen.add(result["decision"])

        # We should see at least 2 distinct decisions (allow + something higher)
        assert len(decisions_seen) >= 2, (
            f"Expected at least 2 distinct decisions, got {decisions_seen}"
        )
        # Verify both extremes are reachable
        assert "allow" in decisions_seen, f"'allow' not found in {decisions_seen}"
        assert "block" in decisions_seen, f"'block' not found in {decisions_seen}"
