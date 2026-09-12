"""Centralized configuration for the integrated StreamSentinel system.

All values can be overridden via environment variables.
"""

import os

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "transactions")
KAFKA_GROUP_ID = os.environ.get("KAFKA_GROUP_ID", "streamsentinel-state-consumer")
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
