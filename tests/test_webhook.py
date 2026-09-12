"""
Tests for src.webhook_service — external webhook dispatch.
"""
from unittest.mock import patch, MagicMock
import pytest

from src.webhook_service import dispatch_webhook
from src.metrics import WEBHOOK_TOTAL


@pytest.fixture
def sample_alert():
    """A standard alert payload for webhook testing."""
    return {
        "alert_id": "alert_test_001",
        "transaction_id": "txn_test_001",
        "user_id": "user_42",
        "risk_score": 0.85,
        "decision": "block",
        "rule_flags": ["high_amount", "velocity_spike"],
        "severity": "CRITICAL",
        "timestamp": "2025-01-01T00:00:00Z",
        "human_readable_reason": "Blocked: high amount and velocity spike",
    }


class TestWebhookDisabled:
    """Tests when WEBHOOK_URL is empty (disabled)."""

    @patch("src.webhook_service.WEBHOOK_URL", "")
    def test_returns_none_when_disabled(self, sample_alert):
        result = dispatch_webhook(sample_alert)
        assert result is None

    @patch("src.webhook_service.WEBHOOK_URL", "")
    def test_increments_disabled_counter(self, sample_alert):
        before = WEBHOOK_TOTAL.labels(status="disabled")._value.get()
        dispatch_webhook(sample_alert)
        assert WEBHOOK_TOTAL.labels(status="disabled")._value.get() == before + 1


class TestWebhookSuccess:
    """Tests when webhook dispatch succeeds."""

    @patch("src.webhook_service.WEBHOOK_URL", "https://hooks.example.com/alert")
    @patch("src.webhook_service.httpx.post")
    def test_successful_dispatch(self, mock_post, sample_alert):
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = dispatch_webhook(sample_alert)
        assert result["status"] == "success"
        assert result["status_code"] == 200
        mock_post.assert_called_once()

    @patch("src.webhook_service.WEBHOOK_URL", "https://hooks.example.com/alert")
    @patch("src.webhook_service.httpx.post")
    def test_payload_contains_required_fields(self, mock_post, sample_alert):
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        dispatch_webhook(sample_alert)

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["event"] == "fraud_alert"
        assert payload["alert_id"] == "alert_test_001"
        assert payload["decision"] == "block"
        assert payload["severity"] == "CRITICAL"


class TestWebhookHMAC:
    """Tests for HMAC signature authentication."""

    @patch("src.webhook_service.WEBHOOK_URL", "https://hooks.example.com/alert")
    @patch("src.webhook_service.WEBHOOK_SECRET", "test_secret_key")
    @patch("src.webhook_service.httpx.post")
    def test_includes_signature_header(self, mock_post, sample_alert):
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        dispatch_webhook(sample_alert)

        call_kwargs = mock_post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert "X-StreamSentinel-Signature" in headers


class TestWebhookFailure:
    """Tests when webhook dispatch fails."""

    @patch("src.webhook_service.WEBHOOK_URL", "https://hooks.example.com/alert")
    @patch("src.webhook_service.httpx.post")
    def test_non_2xx_response(self, mock_post, sample_alert):
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        result = dispatch_webhook(sample_alert)
        assert result["status"] == "failure"
        assert result["status_code"] == 500
        assert mock_post.call_count == 2

    @patch("src.webhook_service.WEBHOOK_URL", "https://hooks.example.com/alert")
    @patch("src.webhook_service.httpx.post")
    def test_timeout(self, mock_post, sample_alert):
        import httpx
        mock_post.side_effect = httpx.TimeoutException("Connection timed out")

        result = dispatch_webhook(sample_alert)
        assert result["status"] == "timeout"
        assert mock_post.call_count == 2

    @patch("src.webhook_service.WEBHOOK_URL", "https://hooks.example.com/alert")
    @patch("src.webhook_service.httpx.post")
    def test_connection_error(self, mock_post, sample_alert):
        mock_post.side_effect = ConnectionError("Connection refused")

        result = dispatch_webhook(sample_alert)
        assert result["status"] == "error"
        assert "Connection refused" in result["error"]
