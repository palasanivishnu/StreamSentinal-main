"""
Tests for src.metrics — Prometheus instrumentation verification.
"""
from prometheus_client import REGISTRY

from src.metrics import (
    TRANSACTIONS_PROCESSED,
    TRANSACTIONS_ERRORS,
    TRANSACTIONS_IN_PROGRESS,
    DECISIONS_TOTAL,
    DETECTION_LATENCY,
    ALERTS_TOTAL,
    OTP_VERIFICATION_TOTAL,
    WEBHOOK_TOTAL,
    API_REQUESTS_TOTAL,
    API_REQUEST_DURATION,
    API_ERRORS_TOTAL,
    REVIEW_ACTIONS_TOTAL,
    DB_ERRORS_TOTAL,
)


class TestMetricRegistration:
    """Verify all metrics are properly registered in the Prometheus registry."""

    def test_transactions_processed_registered(self):
        assert "streamsentinel_transactions_processed" in TRANSACTIONS_PROCESSED._name

    def test_transactions_errors_registered(self):
        assert "streamsentinel_transactions_errors" in TRANSACTIONS_ERRORS._name

    def test_transactions_in_progress_registered(self):
        assert TRANSACTIONS_IN_PROGRESS._name == "streamsentinel_transactions_in_progress"

    def test_decisions_total_registered(self):
        assert "streamsentinel_decisions" in DECISIONS_TOTAL._name

    def test_detection_latency_registered(self):
        assert DETECTION_LATENCY._name == "streamsentinel_detection_latency_seconds"

    def test_alerts_total_registered(self):
        assert "streamsentinel_alerts" in ALERTS_TOTAL._name

    def test_otp_verification_total_registered(self):
        assert "streamsentinel_otp_verification" in OTP_VERIFICATION_TOTAL._name

    def test_webhook_total_registered(self):
        assert "streamsentinel_webhook" in WEBHOOK_TOTAL._name

    def test_api_requests_total_registered(self):
        assert "streamsentinel_api_requests" in API_REQUESTS_TOTAL._name

    def test_api_request_duration_registered(self):
        assert API_REQUEST_DURATION._name == "streamsentinel_api_request_duration_seconds"

    def test_api_errors_total_registered(self):
        assert "streamsentinel_api_errors" in API_ERRORS_TOTAL._name

    def test_review_actions_total_registered(self):
        assert "streamsentinel_review_actions" in REVIEW_ACTIONS_TOTAL._name

    def test_db_errors_total_registered(self):
        assert "streamsentinel_db_errors" in DB_ERRORS_TOTAL._name


class TestMetricLabels:
    """Verify labeled metrics have correct label names."""

    def test_decisions_total_labels(self):
        assert DECISIONS_TOTAL._labelnames == ("decision",)

    def test_alerts_total_labels(self):
        assert ALERTS_TOTAL._labelnames == ("severity",)

    def test_otp_verification_labels(self):
        assert OTP_VERIFICATION_TOTAL._labelnames == ("result",)

    def test_webhook_labels(self):
        assert WEBHOOK_TOTAL._labelnames == ("status",)

    def test_api_requests_labels(self):
        assert set(API_REQUESTS_TOTAL._labelnames) == {"method", "endpoint", "status_code"}

    def test_api_duration_labels(self):
        assert set(API_REQUEST_DURATION._labelnames) == {"method", "endpoint"}

    def test_review_actions_labels(self):
        assert REVIEW_ACTIONS_TOTAL._labelnames == ("action",)


class TestMetricOperations:
    """Verify metrics can be incremented/observed without errors."""

    def test_counter_increment(self):
        before = TRANSACTIONS_PROCESSED._value.get()
        TRANSACTIONS_PROCESSED.inc()
        assert TRANSACTIONS_PROCESSED._value.get() == before + 1

    def test_labeled_counter_increment(self):
        DECISIONS_TOTAL.labels(decision="allow").inc()
        # No exception = pass

    def test_histogram_observe(self):
        DETECTION_LATENCY.observe(0.042)
        # No exception = pass

    def test_gauge_inc_dec(self):
        initial = TRANSACTIONS_IN_PROGRESS._value.get()
        TRANSACTIONS_IN_PROGRESS.inc()
        assert TRANSACTIONS_IN_PROGRESS._value.get() == initial + 1
        TRANSACTIONS_IN_PROGRESS.dec()
        assert TRANSACTIONS_IN_PROGRESS._value.get() == initial
