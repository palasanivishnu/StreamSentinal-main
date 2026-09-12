"""Kafka Consumer & Feature Vector Emitter for StreamSentinel.

Consumes Transaction Events from Kafka, updates Redis rolling user state,
and emits the exact Feature Vector contract for Person B (rules + ML).
"""

import argparse
import json
import logging
import os
import signal
import sys
from typing import Any, Callable, Dict, Optional

from confluent_kafka import Consumer, KafkaError, KafkaException

from src.schemas import FeatureVector, TransactionEvent
from src.state_manager import RedisStateManager
from src.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_GROUP_ID, KAFKA_TOPIC

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("Consumer")


class StreamSentinelConsumer:
    """Consumes transaction events, manages state in Redis, and emits feature vectors."""

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        group_id: Optional[str] = None,
        topic: Optional[str] = None,
        state_manager: Optional[RedisStateManager] = None,
        consumer_config: Optional[Dict[str, Any]] = None,
        on_feature_vector: Optional[Callable[[FeatureVector], None]] = None,
        mock_mode: bool = False,
    ):
        self.topic = topic or KAFKA_TOPIC
        self.state_manager = state_manager or RedisStateManager()
        self.on_feature_vector = on_feature_vector
        self.mock_mode = mock_mode
        self.running = False

        servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
        grp = group_id or KAFKA_GROUP_ID

        if not self.mock_mode:
            config = {
                "bootstrap.servers": servers,
                "group.id": grp,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": True,
                "session.timeout.ms": 10000,
            }
            sec_proto = os.getenv("KAFKA_SECURITY_PROTOCOL")
            sasl_mech = os.getenv("KAFKA_SASL_MECHANISM")
            sasl_user = os.getenv("KAFKA_SASL_USERNAME")
            sasl_pass = os.getenv("KAFKA_SASL_PASSWORD")

            if sec_proto:
                config["security.protocol"] = sec_proto
                if sec_proto.upper().endswith("SSL"):
                    config["enable.ssl.certificate.verification"] = False
            if sasl_mech:
                config["sasl.mechanisms"] = sasl_mech
            if sasl_user:
                config["sasl.username"] = sasl_user
            if sasl_pass:
                config["sasl.password"] = sasl_pass

            if consumer_config:
                config.update(consumer_config)
            self.consumer = Consumer(config)
            self.consumer.subscribe([self.topic])
            logger.info("Kafka consumer initialized and subscribed to topic '%s'", self.topic)
        else:
            self.consumer = None

    def process_raw_message(self, raw_value: str) -> FeatureVector:
        """Parse raw transaction event JSON, update Redis state, and emit FeatureVector."""
        event_dict = json.loads(raw_value)
        event = TransactionEvent(**event_dict)
        return self.process_transaction_event(event)

    def process_transaction_event(self, event: TransactionEvent) -> FeatureVector:
        """Process a validated TransactionEvent through Redis state manager."""
        # Update state and compute features
        feature_vector = self.state_manager.process_transaction(event)

        # Output feature vector
        self.emit_feature_vector(feature_vector)
        return feature_vector

    def emit_feature_vector(self, fv: FeatureVector) -> None:
        """Emit FeatureVector according to the contract schema."""
        fv_json = json.dumps(fv.model_dump())
        logger.info("[FEATURE VECTOR EMITTED] %s", fv_json)

        if self.on_feature_vector:
            self.on_feature_vector(fv)

    def start_consuming(self, max_messages: Optional[int] = None) -> int:
        """Start consumption loop."""
        if self.mock_mode:
            logger.warning("Consumer is running in mock mode; no Kafka polling active.")
            return 0

        self.running = True
        consumed_count = 0
        logger.info("Listening for transaction events on topic '%s'...", self.topic)

        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug("Reached end of partition %s [%d]", msg.topic(), msg.partition())
                    else:
                        logger.warning("Kafka consumer poll warning: %s", msg.error())
                        import time
                        time.sleep(1.0)
                    continue

                try:
                    payload = msg.value().decode("utf-8")
                    self.process_raw_message(payload)
                    consumed_count += 1

                    if max_messages and consumed_count >= max_messages:
                        logger.info("Consumed target of %d messages.", max_messages)
                        break

                except Exception as e:
                    logger.error("Error processing message at offset %s: %s", msg.offset(), e, exc_info=True)

        finally:
            self.close()

        return consumed_count

    def stop(self):
        """Signal consumer loop to stop."""
        self.running = False

    def close(self):
        """Close Kafka consumer connection."""
        if self.consumer:
            logger.info("Closing Kafka consumer...")
            self.consumer.close()
            self.consumer = None


def main():
    parser = argparse.ArgumentParser(description="StreamSentinel Kafka Consumer & State Processor")
    parser.add_argument(
        "--kafka",
        default="localhost:9092",
        help="Kafka bootstrap servers (default: localhost:9092)",
    )
    parser.add_argument(
        "--group",
        default="streamsentinel-state-consumer",
        help="Consumer group ID (default: streamsentinel-state-consumer)",
    )
    parser.add_argument(
        "--topic",
        default="transactions",
        help="Kafka topic to consume from (default: transactions)",
    )
    parser.add_argument(
        "--redis-host",
        default="localhost",
        help="Redis host (default: localhost)",
    )
    parser.add_argument(
        "--redis-port",
        type=int,
        default=6379,
        help="Redis port (default: 6379)",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=None,
        help="Max messages to consume before exiting (default: infinite)",
    )

    args = parser.parse_args()

    state_mgr = RedisStateManager(host=args.redis_host, port=args.redis_port)
    consumer = StreamSentinelConsumer(
        bootstrap_servers=args.kafka,
        group_id=args.group,
        topic=args.topic,
        state_manager=state_mgr,
    )

    def handle_sigint(sig, frame):
        logger.info("Shutdown signal received.")
        consumer.stop()

    signal.signal(signal.SIGINT, handle_sigint)
    consumer.start_consuming(max_messages=args.max_messages)


if __name__ == "__main__":
    main()
