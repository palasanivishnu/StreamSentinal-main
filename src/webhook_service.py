"""
StreamSentinel — External Webhook Dispatcher.

Sends fraud alert notifications to a configurable HTTP endpoint.
Fails gracefully when no webhook URL is configured.
"""
import hashlib
import hmac
import json
import logging

import httpx

from src.config import WEBHOOK_URL, WEBHOOK_SECRET, WEBHOOK_TIMEOUT_SECONDS
from src.metrics import WEBHOOK_TOTAL

logger = logging.getLogger("streamsentinel.webhook")


def dispatch_webhook(alert_data):
    """
    Send alert data to the configured webhook URL via HTTP POST.

    Returns dict with dispatch result, or None if webhooks are disabled.
    Retries once on failure. Never raises — all errors are logged and counted.
    """
    if not WEBHOOK_URL:
        WEBHOOK_TOTAL.labels(status="disabled").inc()
        return None

    # Build payload with non-sensitive alert information only
    payload = {
        "event": "fraud_alert",
        "alert_id": alert_data.get("alert_id"),
        "transaction_id": alert_data.get("transaction_id"),
        "user_id": alert_data.get("user_id"),
        "risk_score": alert_data.get("risk_score"),
        "decision": alert_data.get("decision"),
        "rule_flags": alert_data.get("rule_flags", []),
        "severity": alert_data.get("severity"),
        "timestamp": alert_data.get("timestamp"),
        "human_readable_reason": alert_data.get("human_readable_reason", ""),
    }

    headers = {"Content-Type": "application/json"}

    # HMAC signature for webhook authentication
    if WEBHOOK_SECRET:
        body_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        signature = hmac.new(
            WEBHOOK_SECRET.encode("utf-8"),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()
        headers["X-StreamSentinel-Signature"] = signature

    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        try:
            response = httpx.post(
                WEBHOOK_URL,
                json=payload,
                headers=headers,
                timeout=WEBHOOK_TIMEOUT_SECONDS,
            )

            if response.is_success:
                WEBHOOK_TOTAL.labels(status="success").inc()
                logger.info(
                    "Webhook dispatched: %s → %s (HTTP %d)",
                    alert_data.get("alert_id"),
                    WEBHOOK_URL,
                    response.status_code,
                )
                return {"status": "success", "status_code": response.status_code}

            logger.warning(
                "Webhook non-2xx: HTTP %d (attempt %d/%d)",
                response.status_code,
                attempt,
                max_attempts,
            )
            if attempt == max_attempts:
                WEBHOOK_TOTAL.labels(status="failure").inc()
                return {"status": "failure", "status_code": response.status_code}

        except httpx.TimeoutException:
            logger.warning(
                "Webhook timeout after %ds (attempt %d/%d)",
                WEBHOOK_TIMEOUT_SECONDS,
                attempt,
                max_attempts,
            )
            if attempt == max_attempts:
                WEBHOOK_TOTAL.labels(status="timeout").inc()
                return {"status": "timeout"}

        except Exception as e:
            logger.error(
                "Webhook dispatch error: %s (attempt %d/%d)",
                e,
                attempt,
                max_attempts,
            )
            if attempt == max_attempts:
                WEBHOOK_TOTAL.labels(status="failure").inc()
                return {"status": "error", "error": str(e)}

    return None
