"""
StreamSentinel — Fraud Alerting & Notification Service.

Classifies security risk, creates alert records, automatically triggers OTP
challenges for suspicious transactions, and dispatches external webhooks.
"""
import uuid
from datetime import datetime, timezone
import logging

from src.db import save_alert, get_recent_alerts
from src.otp_service import generate_otp

logger = logging.getLogger("streamsentinel.alerts")


def get_alert_severity(decision, risk_score):
    """Determine alert severity from decision and risk score."""
    if decision == "block" or risk_score > 0.75:
        return "CRITICAL"
    elif decision == "review" or risk_score > 0.50:
        return "HIGH"
    elif decision == "otp" or risk_score > 0.25:
        return "WARNING"
    return None


def evaluate_and_trigger_alert(transaction, decision_result, ml_result, rule_result):
    """
    Evaluate scoring output and trigger alerts + automated OTP challenges if required.

    Returns alert_info dict if an alert was triggered, or None if legitimate (allow).
    """
    decision = decision_result.get("decision", "allow")
    risk_score = float(decision_result.get("risk_score", 0.0))

    if decision == "allow" and risk_score <= 0.25:
        return None  # No alert for normal legitimate transactions

    severity = get_alert_severity(decision, risk_score)
    alert_id = f"ALT_{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    rule_flags = list(decision_result.get("rule_flags", []))
    hr_reason = decision_result.get("human_readable_reason", "")

    if rule_flags:
        reason_str = " • ".join(rule_flags)
    elif hr_reason:
        reason_str = hr_reason
    else:
        reason_str = f"Elevated ML fraud probability ({(risk_score * 100):.1f}%)"

    alert_data = {
        "alert_id": alert_id,
        "transaction_id": transaction.get("transaction_id"),
        "user_id": transaction.get("user_id"),
        "severity": severity,
        "decision": decision,
        "risk_score": risk_score,
        "ml_fraud_score": float(ml_result.get("ml_score", 0.0)),
        "rule_flags": rule_flags,
        "human_readable_reason": hr_reason,
        "reason": reason_str,
        "timestamp": now_iso,
        "acknowledged": False,
        "otp_triggered": False,
        "otp_code": None
    }

    # Automatically trigger OTP for review or otp decisions
    if decision in ["otp", "review"]:
        user_id = transaction.get("user_id")
        txn_id = transaction.get("transaction_id")
        try:
            otp_code = generate_otp(user_id, transaction_id=txn_id)
            alert_data["otp_triggered"] = True
            alert_data["otp_code"] = otp_code
            logger.info(f"Auto-triggered OTP for user {user_id}: {otp_code}")
        except Exception as e:
            logger.error(f"Failed to auto-trigger OTP: {e}")

    # Console Alert Banner
    color = "\033[91m" if severity == "CRITICAL" else ("\033[93m" if severity == "HIGH" else "\033[94m")
    reset = "\033[0m"
    print(f"\n{color}{'='*60}")
    print(f"🚨 FRAUD ALERT DETECTED [{severity}] — ID: {alert_id}")
    print(f"   User: {transaction.get('user_id')} | Txn: {transaction.get('transaction_id')}")
    print(f"   Decision: {decision.upper()} | Risk Score: {risk_score:.4f}")
    print(f"   Reason: {decision_result.get('human_readable_reason')}")
    if alert_data.get("otp_triggered"):
        print(f"   🔐 AUTOMATED OTP CHALLENGE GENERATED: {alert_data['otp_code']}")
    print(f"{'='*60}{reset}\n")

    # Save to MongoDB
    try:
        save_alert(alert_data)
    except Exception as e:
        logger.error(f"Failed to persist alert in MongoDB: {e}")

    # Dispatch to external webhook if configured
    try:
        from src.webhook_service import dispatch_webhook
        dispatch_webhook(alert_data)
    except Exception as e:
        logger.error(f"Failed to dispatch webhook: {e}")

    return alert_data


def get_alerts_feed(limit=50, severity=None):
    """Retrieve security alerts feed."""
    return get_recent_alerts(limit=limit, severity=severity)
