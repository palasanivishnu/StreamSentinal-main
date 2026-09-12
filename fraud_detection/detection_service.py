"""Integrated fraud detection service."""

from datetime import datetime, timezone
import time

from .ml_service import get_ml_score
from .rule_engine import evaluate_rules
from .shap_explainer import explain_transaction
from .decision_engine import make_decision


FEATURE_COLUMNS = [
    "amount",
    "amount_vs_avg_ratio",
    "txn_count_last_5min",
    "time_since_last_txn_sec",
    "distance_from_last_location_km",
    "merchant_category_is_new_for_user"
]


def feature_reason_text(
    feature,
    value,
    shap_value
):
    direction = (
        "increased"
        if float(shap_value) > 0
        else "decreased"
    )

    if feature == "amount":
        value_text = f"amount={float(value):.2f}"
    elif feature == "amount_vs_avg_ratio":
        value_text = (
            f"amount_vs_avg_ratio={float(value):.2f}"
        )
    elif feature == "txn_count_last_5min":
        value_text = (
            f"txn_count_last_5min={int(value)}"
        )
    elif feature == "time_since_last_txn_sec":
        value_text = (
            f"time_since_last_txn_sec={float(value):.2f}"
        )
    elif feature == "distance_from_last_location_km":
        value_text = (
            f"distance_from_last_location_km={float(value):.2f}"
        )
    elif feature == "merchant_category_is_new_for_user":
        value_text = (
            f"merchant_category_is_new_for_user={int(value)}"
        )
    else:
        value_text = f"{feature}={value}"

    return (
        f"{value_text} {direction} fraud risk"
    )


def generate_reason(
    rule_flags,
    ml_score,
    shap_result,
    decision
):
    parts = []

    if rule_flags:
        parts.append(
            "Triggered rules: "
            + ", ".join(rule_flags)
        )
    else:
        parts.append(
            "No deterministic rules triggered"
        )

    parts.append(
        f"ML fraud score: {float(ml_score):.4f}"
    )

    for item in shap_result["top_features"]:
        parts.append(
            feature_reason_text(
                item["feature"],
                item["feature_value"],
                item["shap_value"]
            )
        )

    parts.append(
        f"Decision: {decision.upper()}"
    )

    return ". ".join(parts) + "."


def score_transaction(transaction):
    start_time = time.perf_counter()

    required_fields = [
        "transaction_id",
        "user_id",
        *FEATURE_COLUMNS
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in transaction
    ]

    if missing_fields:
        raise ValueError(
            f"Missing detection fields: {missing_fields}"
        )

    features = {
        feature: transaction[feature]
        for feature in FEATURE_COLUMNS
    }

    ml_result = get_ml_score(
        features
    )

    rule_result = evaluate_rules(
        features
    )

    decision_result = make_decision(
        ml_result["ml_score"],
        rule_result
    )

    shap_result = explain_transaction(
        features,
        top_n=3
    )

    reason = generate_reason(
        decision_result["rule_flags"],
        ml_result["ml_score"],
        shap_result,
        decision_result["decision"]
    )

    latency_ms = (
        time.perf_counter()
        - start_time
    ) * 1000

    return {
        "transaction_id": transaction["transaction_id"],
        "user_id": transaction["user_id"],
        "risk_score": float(
            decision_result["risk_score"]
        ),
        "rule_flags": list(
            decision_result["rule_flags"]
        ),
        "ml_fraud_score": float(
            ml_result["ml_score"]
        ),
        "decision": decision_result["decision"],
        "human_readable_reason": reason,
        "processed_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "latency_ms": float(
            latency_ms
        )
    }
