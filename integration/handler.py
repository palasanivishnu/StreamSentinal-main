"""Integration handler bridging Person A Feature Vectors to Person B Detection Service & Person C Platform.

This module is the integration point between Person A, Person B, and Person C.
Flow:
  1. Person A FeatureVector → fv_dict
  2. Person B score_transaction(fv_dict) → ScoringOutput (exact 9 keys)
  3. Person C platform processing: Alert evaluation + Auto-OTP + MongoDB save + Prometheus metrics
"""

import logging
from typing import Any, Dict, Optional

from src.schemas import FeatureVector

logger = logging.getLogger(__name__)

# Module-level reference, set on first init
_score_transaction_fn = None


def _load_detection_service():
    """Lazily import Person B's detection_service to control initialization timing."""
    global _score_transaction_fn
    if _score_transaction_fn is None:
        logger.info("Loading Person B detection service (model, rules, SHAP)...")
        from fraud_detection.detection_service import score_transaction
        _score_transaction_fn = score_transaction
        logger.info("Person B detection service loaded successfully.")
    return _score_transaction_fn


class IntegrationHandler:
    """Handles the Person A → Person B → Person C integration boundary.

    Usage:
        handler = IntegrationHandler()
        scoring_output = handler.handle_feature_vector(feature_vector)
    """

    def __init__(self):
        """Initialize handler and eagerly load Person B detection service."""
        self._score_fn = _load_detection_service()

    def handle_feature_vector(self, fv: FeatureVector) -> Optional[Dict[str, Any]]:
        """Process a Person A FeatureVector through Person B's detection pipeline & Person C platform.

        Returns:
            The Person B scoring output dict on success, or None if detection failed.
        """
        try:
            # 1. Convert Pydantic model to plain dict (exact contract fields)
            fv_dict = fv.model_dump()

            # 2. Pass to Person B's detection service (returns exact 9 Person B contract keys)
            scoring_output = self._score_fn(fv_dict)

            # Log the scoring result
            logger.info(
                "\n%s\n"
                "  SCORING OUTPUT\n"
                "  Transaction: %s\n"
                "  User:        %s\n"
                "  Risk Score:  %.4f\n"
                "  ML Score:    %.4f\n"
                "  Rules:       %s\n"
                "  Decision:    %s\n"
                "  Latency:     %.1f ms\n"
                "  Reason:      %s\n"
                "%s",
                "=" * 60,
                scoring_output["transaction_id"],
                scoring_output["user_id"],
                scoring_output["risk_score"],
                scoring_output["ml_fraud_score"],
                scoring_output["rule_flags"],
                scoring_output["decision"].upper(),
                scoring_output["latency_ms"],
                scoring_output["human_readable_reason"],
                "=" * 60,
            )

            # 3. Person C Platform Processing (Alerting, Webhook, Auto-OTP, MongoDB, Prometheus Metrics)
            try:
                from src.alert_service import evaluate_and_trigger_alert
                from src.db import save_transaction
                from src.metrics import (
                    TRANSACTIONS_PROCESSED, DECISIONS_TOTAL, DETECTION_LATENCY, ALERTS_TOTAL
                )

                # Combine input features + scoring output for MongoDB persistence & Alerting
                combined_record = dict(fv_dict)
                combined_record.update(scoring_output)
                if "merchant" in fv_dict and fv_dict["merchant"]:
                    combined_record["merchant"] = fv_dict["merchant"]
                if "merchant_category" in fv_dict and fv_dict["merchant_category"]:
                    combined_record["merchant_category"] = fv_dict["merchant_category"]

                alert_info = evaluate_and_trigger_alert(
                    transaction=combined_record,
                    decision_result={
                        "decision": scoring_output["decision"],
                        "risk_score": scoring_output["risk_score"],
                        "rule_flags": scoring_output["rule_flags"],
                        "human_readable_reason": scoring_output["human_readable_reason"],
                    },
                    ml_result={"ml_score": scoring_output["ml_fraud_score"]},
                    rule_result={"rule_flags": scoring_output["rule_flags"]}
                )

                if alert_info:
                    combined_record["alert_triggered"] = True
                    combined_record["alert_id"] = alert_info["alert_id"]
                    combined_record["alert_severity"] = alert_info["severity"]
                    combined_record["otp_triggered"] = bool(alert_info.get("otp_triggered"))
                    combined_record["otp_status"] = "PENDING" if alert_info.get("otp_triggered") else "NONE"
                    ALERTS_TOTAL.labels(severity=alert_info.get("severity", "UNKNOWN")).inc()
                else:
                    combined_record["alert_triggered"] = False
                    combined_record["otp_status"] = "N/A" if scoring_output["decision"] == "allow" else "NONE"

                # Persist enriched record to MongoDB
                save_transaction(combined_record)

                # Record Prometheus Telemetry Metrics
                TRANSACTIONS_PROCESSED.inc()
                DETECTION_LATENCY.observe(scoring_output["latency_ms"] / 1000.0)
                DECISIONS_TOTAL.labels(decision=scoring_output["decision"]).inc()

            except Exception as pe:
                logger.warning("Person C platform processing warning: %s", pe)

            return scoring_output

        except ValueError as e:
            logger.error("Feature vector validation/detection failed: %s", e)
            return None
        except TypeError as e:
            logger.error("Type error in detection pipeline: %s", e)
            return None
        except Exception as e:
            logger.error("Unexpected detection service error: %s", e, exc_info=True)
            return None
