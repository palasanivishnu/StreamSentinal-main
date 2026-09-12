"""Decision engine combining ML scores and rule results."""

from pathlib import Path
import json
import numpy as np

SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
MODELS_DIR = PROJECT_ROOT / "models"

CONFIG_PATH = MODELS_DIR / "decision_engine_config.json"

if not CONFIG_PATH.exists():
    raise FileNotFoundError(
        f"Decision engine configuration not found: {CONFIG_PATH}"
    )

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    DECISION_CONFIG = json.load(file)


def calculate_risk_score(
    ml_fraud_score,
    rule_score
):
    ml_fraud_score = float(ml_fraud_score)
    rule_score = float(rule_score)

    if not 0 <= ml_fraud_score <= 1:
        raise ValueError(
            "ML fraud score must be between 0 and 1."
        )

    if not 0 <= rule_score <= 1:
        raise ValueError(
            "Rule score must be between 0 and 1."
        )

    risk_score = (
        DECISION_CONFIG["ml_weight"]
        * ml_fraud_score
        +
        DECISION_CONFIG["rule_weight"]
        * rule_score
    )

    return float(
        np.clip(
            risk_score,
            0.0,
            1.0
        )
    )


def classify_risk(risk_score):
    risk_score = float(risk_score)

    if not 0 <= risk_score <= 1:
        raise ValueError(
            "Risk score must be between 0 and 1."
        )

    if risk_score <= DECISION_CONFIG["allow_max_risk"]:
        return "allow"

    if risk_score <= DECISION_CONFIG["otp_max_risk"]:
        return "otp"

    if risk_score <= DECISION_CONFIG["review_max_risk"]:
        return "review"

    return "block"


def generate_decision_reason(
    ml_fraud_score,
    rule_flags,
    risk_score,
    decision
):
    if not isinstance(
        rule_flags,
        list
    ):
        raise TypeError(
            "rule_flags must be a list."
        )

    if rule_flags:
        rule_text = ", ".join(
            rule_flags
        )
        rule_reason = (
            f"Triggered rules: {rule_text}"
        )
    else:
        rule_reason = (
            "No deterministic rules triggered"
        )

    return (
        f"{rule_reason}. "
        f"ML fraud score: "
        f"{float(ml_fraud_score):.4f}. "
        f"Combined risk score: "
        f"{float(risk_score):.4f}. "
        f"Decision: {decision.upper()}."
    )


def make_decision(
    ml_fraud_score,
    rule_result
):
    if not isinstance(
        rule_result,
        dict
    ):
        raise TypeError(
            "rule_result must be a dictionary."
        )

    if "rule_flags" not in rule_result:
        raise ValueError(
            "rule_result is missing rule_flags."
        )

    if "rule_score" not in rule_result:
        raise ValueError(
            "rule_result is missing rule_score."
        )

    rule_flags = rule_result["rule_flags"]
    rule_score = float(
        rule_result["rule_score"]
    )

    risk_score = calculate_risk_score(
        ml_fraud_score,
        rule_score
    )

    decision = classify_risk(
        risk_score
    )

    human_readable_reason = (
        generate_decision_reason(
            ml_fraud_score,
            rule_flags,
            risk_score,
            decision
        )
    )

    return {
        "risk_score": risk_score,
        "rule_flags": rule_flags,
        "ml_fraud_score": float(
            ml_fraud_score
        ),
        "decision": decision,
        "human_readable_reason": human_readable_reason
    }
