"""Kafka Producer for StreamSentinel.

Publishes Transaction Events to Kafka topic partitioned by user_id.
"""

import json
import logging
import os
from typing import Any, Callable, Dict, Optional
from confluent_kafka import KafkaError, Producer

from src.schemas import TransactionEvent
from src.config import KAFKA_BOOTSTRAP_SERVERS

logger = logging.getLogger(__name__)


class StreamSentinelProducer:
    """Publishes transaction events partitioned by user_id."""

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        topic: str = "transactions",
        producer_config: Optional[Dict[str, Any]] = None,
        mock_transport: Optional[Callable[[str, str, str], None]] = None,
    ):
        """Initialize the Kafka producer.

        :param bootstrap_servers: Comma-separated Kafka broker addresses.
        :param topic: Kafka topic to publish events to.
        :param producer_config: Additional confluent-kafka configuration options.
        :param mock_transport: Optional callable (topic, key, value) for offline testing/mocking.
        """
        self.topic = topic
        self.mock_transport = mock_transport
        self.last_delivery_info: Dict[str, Any] = {}

        servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS

        if self.mock_transport is None:
            config = {
                "bootstrap.servers": servers,
                "client.id": "streamsentinel-producer",
                "acks": "all",
                "retries": 3,
                "linger.ms": 5,
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

            if producer_config:
                config.update(producer_config)
            self.producer = Producer(config)
        else:
            self.producer = None

    def _delivery_report(self, err: Optional[KafkaError], msg: Any) -> None:
        """Callback invoked once message is delivered or permanently failed."""
        if err is not None:
            logger.error("Message delivery failed: %s", err)
            self.last_delivery_info = {"status": "failed", "error": str(err)}
        else:
            partition = msg.partition()
            offset = msg.offset()
            key = msg.key().decode("utf-8") if msg.key() else None
            self.last_delivery_info = {
                "status": "delivered",
                "topic": msg.topic(),
                "partition": partition,
                "offset": offset,
                "key": key,
            }
            logger.debug(
                "Delivered to topic %s [partition %d] at offset %d with key %s",
                msg.topic(),
                partition,
                offset,
                key,
            )

    def publish_transaction(self, event: TransactionEvent) -> Dict[str, Any]:
        """Publish a single TransactionEvent to Kafka.

        Crucial requirement: message key MUST be user_id to guarantee all transactions
        for the same user route to the same Kafka partition.
        """
        payload = event.model_dump()
        payload_bytes = json.dumps(payload).encode("utf-8")
        key_bytes = event.user_id.encode("utf-8")

        if self.mock_transport is not None:
            self.mock_transport(self.topic, event.user_id, json.dumps(payload))
            return {
                "status": "delivered_mock",
                "topic": self.topic,
                "key": event.user_id,
                "transaction_id": event.transaction_id,
            }

        self.producer.produce(
            topic=self.topic,
            key=key_bytes,
            value=payload_bytes,
            callback=self._delivery_report,
        )
        # Serve delivery report callbacks from previous produce calls
        self.producer.poll(0)
        return {
            "status": "queued",
            "topic": self.topic,
            "key": event.user_id,
            "transaction_id": event.transaction_id,
        }

    def flush(self, timeout: float = 10.0) -> int:
        """Flush any pending messages in buffer."""
        if self.producer is not None:
            return self.producer.flush(timeout)
        return 0
