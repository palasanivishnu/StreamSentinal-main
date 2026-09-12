"""Rule-based fraud detection engine."""

from pathlib import Path
import json

SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
MODELS_DIR = PROJECT_ROOT / "models"

CONFIG_PATH = MODELS_DIR / "rule_engine_config.json"

if not CONFIG_PATH.exists():
    raise FileNotFoundError(
        f"Rule engine configuration not found: {CONFIG_PATH}"
    )

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    RULE_CONFIG = json.load(file)


def amount_threshold_rule(transaction, config):
    return (
        float(transaction["amount_vs_avg_ratio"])
        >= float(
            config["amount_vs_avg_ratio_threshold"]
        )
    )


def velocity_rule(transaction, config):
    return (
        int(transaction["txn_count_last_5min"])
        >= int(
            config["velocity_5min_threshold"]
        )
    )


def impossible_travel_rule(transaction, config):
    return (
        float(
            transaction["distance_from_last_location_km"]
        )
        >= float(
            config["impossible_travel_distance_km"]
        )
        and
        float(
            transaction["time_since_last_txn_sec"]
        )
        <= float(
            config["impossible_travel_time_sec"]
        )
    )


def merchant_mismatch_rule(transaction, config):
    return (
        int(
            transaction[
                "merchant_category_is_new_for_user"
            ]
        )
        == 1
    )


def evaluate_rules(transaction):
    required_fields = [
        "amount",
        "amount_vs_avg_ratio",
        "txn_count_last_5min",
        "time_since_last_txn_sec",
        "distance_from_last_location_km",
        "merchant_category_is_new_for_user"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in transaction
    ]

    if missing_fields:
        raise ValueError(
            f"Missing rule fields: {missing_fields}"
        )

    flags = []

    if amount_threshold_rule(
        transaction,
        RULE_CONFIG
    ):
        flags.append("HIGH_AMOUNT")

    if velocity_rule(
        transaction,
        RULE_CONFIG
    ):
        flags.append("HIGH_VELOCITY")

    if impossible_travel_rule(
        transaction,
        RULE_CONFIG
    ):
        flags.append("IMPOSSIBLE_TRAVEL")

    if merchant_mismatch_rule(
        transaction,
        RULE_CONFIG
    ):
        flags.append("NEW_MERCHANT_CATEGORY")

    if not flags:
        rule_score = 0.0
    else:
        rule_score = sum(
            float(
                RULE_CONFIG["rule_weights"][flag]
            )
            for flag in flags
        )

    rule_score = min(
        max(
            rule_score,
            0.0
        ),
        1.0
    )

    return {
        "rule_flags": flags,
        "rule_score": float(rule_score),
        "rules_triggered": len(flags)
    }
