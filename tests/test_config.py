"""
Tests for src.config — environment-based configuration loading.
"""
import os
from unittest.mock import patch


class TestConfigDefaults:
    """Verify all configuration variables have correct defaults."""

    def test_mongodb_uri_default(self):
        with patch.dict(os.environ, {}, clear=True), patch("dotenv.load_dotenv"):
            import importlib
            import src.config
            importlib.reload(src.config)
            assert src.config.MONGODB_URI == "mongodb://127.0.0.1:27017/"

    def test_mongodb_database_default(self):
        with patch.dict(os.environ, {}, clear=True), patch("dotenv.load_dotenv"):
            import importlib
            import src.config
            importlib.reload(src.config)
            assert src.config.MONGODB_DATABASE == "fraud_db"

    def test_fastapi_port_default(self):
        with patch.dict(os.environ, {}, clear=True), patch("dotenv.load_dotenv"):
            import importlib
            import src.config
            importlib.reload(src.config)
            assert src.config.FASTAPI_PORT == 8000

    def test_webhook_url_default_empty(self):
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import src.config
            importlib.reload(src.config)
            assert src.config.WEBHOOK_URL == ""

    def test_otp_expiry_default(self):
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import src.config
            importlib.reload(src.config)
            assert src.config.OTP_EXPIRY_SECONDS == 300

    def test_application_env_default(self):
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import src.config
            importlib.reload(src.config)
            assert src.config.APPLICATION_ENV == "development"


class TestConfigOverrides:
    """Verify environment variables override defaults."""

    def test_mongodb_uri_override(self):
        with patch.dict(os.environ, {"MONGODB_URI": "mongodb://custom:27017/"}):
            import importlib
            import src.config
            importlib.reload(src.config)
            assert src.config.MONGODB_URI == "mongodb://custom:27017/"

    def test_fastapi_port_override(self):
        with patch.dict(os.environ, {"FASTAPI_PORT": "9999"}):
            import importlib
            import src.config
            importlib.reload(src.config)
            assert src.config.FASTAPI_PORT == 9999

    def test_port_env_var_override(self):
        with patch.dict(os.environ, {"PORT": "7000"}):
            import importlib
            import src.config
            importlib.reload(src.config)
            assert src.config.FASTAPI_PORT == 7000

    def test_redis_url_override(self):
        with patch.dict(os.environ, {"REDIS_URL": "rediss://:secret@cloud-redis.com:6379"}):
            import importlib
            import src.config
            importlib.reload(src.config)
            assert src.config.REDIS_URL == "rediss://:secret@cloud-redis.com:6379"

    def test_redis_password_override(self):
        with patch.dict(os.environ, {"REDIS_PASSWORD": "mysecretpassword"}):
            import importlib
            import src.config
            importlib.reload(src.config)
            assert src.config.REDIS_PASSWORD == "mysecretpassword"

    def test_frontend_url_override(self):
        with patch.dict(os.environ, {"FRONTEND_URL": "https://streamsentinel.vercel.app"}):
            import importlib
            import src.config
            importlib.reload(src.config)
            assert src.config.FRONTEND_URL == "https://streamsentinel.vercel.app"

    def test_webhook_url_override(self):
        with patch.dict(
            os.environ, {"WEBHOOK_URL": "https://hooks.example.com/alert"}
        ):
            import importlib
            import src.config
            importlib.reload(src.config)
            assert src.config.WEBHOOK_URL == "https://hooks.example.com/alert"

    def test_application_env_override(self):
        with patch.dict(os.environ, {"APPLICATION_ENV": "production"}):
            import importlib
            import src.config
            importlib.reload(src.config)
            assert src.config.APPLICATION_ENV == "production"
