"""StreamSentinel - Person A (Data & State) Live Demo Runner.

Demonstrates:
1. Dataset ingestion & replay via Simulator.
2. Kafka producer routing transactions partitioned by user_id.
3. Consumer reading transactions and updating Redis rolling state.
4. Emission of Feature Vectors adhering strictly to the contract.
5. On-demand fraud event injection.
"""

import argparse
import json
import logging
import sys
import time
import fakeredis
import redis

from src.consumer import StreamSentinelConsumer
from src.producer import StreamSentinelProducer
from src.schemas import FeatureVector
from src.simulator import TransactionSimulator
from src.state_manager import RedisStateManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Demo")


import socket

def check_live_services(kafka_servers: str, redis_host: str, redis_port: int) -> bool:
    """Quickly check if Redis socket is open (indicates services are up)."""
    try:
        with socket.create_connection((redis_host, redis_port), timeout=0.3):
            return True
    except (OSError, socket.error):
        return False


def main():
    parser = argparse.ArgumentParser(description="StreamSentinel Person A Demo")
    parser.add_argument("--mode", choices=["auto", "live", "mock"], default="auto",
                        help="Run mode: auto (detect live services, fallback to mock), live, or mock")
    parser.add_argument("--dataset", default="data/fraud_sample.csv",
                        help="Path to dataset CSV (default: data/fraud_sample.csv)")
    parser.add_argument("--rate", type=float, default=2.0,
                        help="Replay rate in transactions/sec (default: 2.0)")
    parser.add_argument("--limit", type=int, default=10,
                        help="Number of transactions to replay (default: 10)")
    parser.add_argument("--trigger-fraud", action="store_true",
                        help="Trigger a flagged fraud transaction on demand")
    parser.add_argument("--kafka", default="localhost:9092", help="Kafka broker address")
    parser.add_argument("--redis-host", default="localhost", help="Redis host")
    parser.add_argument("--redis-port", type=int, default=6379, help="Redis port")

    args = parser.parse_args()

    print("=" * 70)
    print(" STREAM SENTINEL : PERSON A (DATA & STATE) DEMO")
    print("=" * 70)

    use_live = False
    if args.mode == "live":
        use_live = True
    elif args.mode == "auto":
        use_live = check_live_services(args.kafka, args.redis_host, args.redis_port)

    if use_live:
        print(f"[STATUS] Connected to LIVE services (Kafka @ {args.kafka}, Redis @ {args.redis_host}:{args.redis_port})")
        state_mgr = RedisStateManager(host=args.redis_host, port=args.redis_port)
        producer = StreamSentinelProducer(bootstrap_servers=args.kafka, topic="transactions")
        consumer = StreamSentinelConsumer(
            bootstrap_servers=args.kafka,
            topic="transactions",
            state_manager=state_mgr,
        )
    else:
        print("[STATUS] Running in DEMO / MOCK MODE (in-memory partition-verified broker + fakeredis)")
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        state_mgr = RedisStateManager(redis_client=fake_redis, key_prefix="demo")

        def on_vector_received(fv: FeatureVector):
            print("\n" + "-" * 60)
            print(f"--> [FEATURE VECTOR EMITTED FOR PERSON B]")
            print(json.dumps(fv.model_dump(), indent=2))
            print("-" * 60 + "\n")

        consumer = StreamSentinelConsumer(
            state_manager=state_mgr,
            mock_mode=True,
            on_feature_vector=on_vector_received,
        )

        def mock_broker(topic: str, key: str, value: str):
            print(f"\n[KAFKA BROKER] Received msg on topic '{topic}' | Key (user_id)='{key}'")
            consumer.process_raw_message(value)

        producer = StreamSentinelProducer(mock_transport=mock_broker)

    simulator = TransactionSimulator(
        producer=producer,
        dataset_path=args.dataset,
        rate_per_sec=args.rate,
    )

    if args.trigger_fraud:
        print("\n[ACTION] Triggering on-demand fraud transaction for live demo...")
        fraud_event = simulator.trigger_on_demand_fraud()
        if fraud_event:
            print(f"Injected fraud event: {fraud_event.transaction_id} (User: {fraud_event.user_id})")
        return

    print(f"\n[ACTION] Replaying {args.limit} transactions at {args.rate} txns/sec from {args.dataset}...")
    replayed = simulator.replay(limit=args.limit)
    print(f"\n[SUCCESS] Completed replay of {replayed} transactions!")
    print("=" * 70)


if __name__ == "__main__":
    main()
