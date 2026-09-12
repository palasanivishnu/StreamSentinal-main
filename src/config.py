"""
StreamSentinel — Centralized Configuration Management.

All operational configuration is loaded from environment variables
with safe local development defaults. Production values should be
set through .env or container environment variables.
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; env vars can be set directly

# ─── MongoDB ────────────────────────────────────────────────────────────────
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "fraud_db")

# ─── Kafka ──────────────────────────────────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_SECURITY_PROTOCOL = os.getenv("KAFKA_SECURITY_PROTOCOL", "")
KAFKA_SASL_MECHANISM = os.getenv("KAFKA_SASL_MECHANISM", "")
KAFKA_SASL_USERNAME = os.getenv("KAFKA_SASL_USERNAME", "")
KAFKA_SASL_PASSWORD = os.getenv("KAFKA_SASL_PASSWORD", "")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "streamsentinel-app")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "transactions")

# ─── Redis ──────────────────────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# ─── FastAPI ────────────────────────────────────────────────────────────────
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("PORT") or os.getenv("FASTAPI_PORT") or "8000")

# ─── CORS ───────────────────────────────────────────────────────────────────
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

# ─── Prometheus ─────────────────────────────────────────────────────────────
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9090"))

# ─── Grafana ────────────────────────────────────────────────────────────────
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")

# ─── Webhook ────────────────────────────────────────────────────────────────
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
WEBHOOK_TIMEOUT_SECONDS = int(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "5"))

# ─── OTP ────────────────────────────────────────────────────────────────────
OTP_EXPIRY_SECONDS = int(os.getenv("OTP_EXPIRY_SECONDS", "300"))

# ─── Application ────────────────────────────────────────────────────────────
APPLICATION_ENV = os.getenv("APPLICATION_ENV", "development")
