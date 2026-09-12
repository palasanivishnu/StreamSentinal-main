"""
StreamSentinel — Shared Test Fixtures.

Provides mocked services (MongoDB, webhook server) and test clients
so tests run without external infrastructure.
"""
import sys
import os
from unittest.mock import MagicMock, patch
import pytest

# ─── Ensure project root on sys.path ────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ["TESTING"] = "1"


# ─── Mock MongoDB at import time ─────────────────────────────────────────────
_mock_mongo_client = MagicMock()
_mock_db = MagicMock()
_mock_transactions_col = MagicMock()
_mock_alerts_col = MagicMock()
_mock_otps_col = MagicMock()


@pytest.fixture(autouse=True)
def mock_mongo(monkeypatch):
    """Mock all MongoDB collections so tests don't need a running database."""
    monkeypatch.setattr("src.db.client", _mock_mongo_client)
    monkeypatch.setattr("src.db.db", _mock_db)
    monkeypatch.setattr("src.db.transactions_col", _mock_transactions_col)
    monkeypatch.setattr("src.db.alerts_col", _mock_alerts_col)
    monkeypatch.setattr("src.db.otps_col", _mock_otps_col)

    # Reset call counts and side effects between tests
    _mock_transactions_col.reset_mock()
    _mock_alerts_col.reset_mock()
    _mock_otps_col.reset_mock()
    _mock_mongo_client.reset_mock()
    _mock_mongo_client.admin.command.side_effect = None

    yield {
        "client": _mock_mongo_client,
        "db": _mock_db,
        "transactions_col": _mock_transactions_col,
        "alerts_col": _mock_alerts_col,
        "otps_col": _mock_otps_col,
    }


@pytest.fixture
def fastapi_client():
    """TestClient for the FastAPI application."""
    from fastapi.testclient import TestClient
    from src.api import app

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def sample_transaction():
    """A standard test transaction with all required fields."""
    return {
        "transaction_id": "11111111-1111-1111-1111-111111111111",
        "user_id": "user_42",
        "amount": 150.0,
        "amount_vs_avg_ratio": 1.5,
        "txn_count_last_5min": 2,
        "time_since_last_txn_sec": 120.0,
        "distance_from_last_location_km": 5.0,
        "merchant_category_is_new_for_user": 0,
    }


@pytest.fixture
def legit_transaction():
    """A clearly legitimate transaction (low risk)."""
    return {
        "transaction_id": "22222222-2222-2222-2222-222222222222",
        "user_id": "user_safe_01",
        "amount": 25.0,
        "amount_vs_avg_ratio": 0.5,
        "txn_count_last_5min": 1,
        "time_since_last_txn_sec": 3600.0,
        "distance_from_last_location_km": 0.1,
        "merchant_category_is_new_for_user": 0,
    }


@pytest.fixture
def suspicious_transaction():
    """A transaction that should trigger OTP or review."""
    return {
        "transaction_id": "33333333-3333-3333-3333-333333333333",
        "user_id": "user_risky_01",
        "amount": 5000.0,
        "amount_vs_avg_ratio": 15.0,
        "txn_count_last_5min": 8,
        "time_since_last_txn_sec": 10.0,
        "distance_from_last_location_km": 50.0,
        "merchant_category_is_new_for_user": 1,
    }


@pytest.fixture
def fraud_transaction():
    """A clearly fraudulent transaction (high risk)."""
    return {
        "transaction_id": "44444444-4444-4444-4444-444444444444",
        "user_id": "user_fraud_01",
        "amount": 99999.0,
        "amount_vs_avg_ratio": 200.0,
        "txn_count_last_5min": 15,
        "time_since_last_txn_sec": 2.0,
        "distance_from_last_location_km": 500.0,
        "merchant_category_is_new_for_user": 1,
    }
