"""StreamSentinel - Integrated Demo (Person A + Person B).

Demonstrates the full end-to-end fraud detection pipeline:
1. Dataset replay via Simulator → Kafka Producer
2. Consumer reads transactions → Redis rolling state → Feature Vector
3. Integration handler passes Feature Vector → Person B Detection Service
4. Person B: Rule Engine + XGBoost ML + Decision Engine + SHAP
5. Scoring Output displayed with risk score, decision, and explanation

Supports both live (Kafka + Redis) and mock (in-memory) modes.
"""

import argparse
import json
import logging
import os
import socket
import sys

import fakeredis

from src.consumer import StreamSentinelConsumer
from src.producer import StreamSentinelProducer
from src.schemas import FeatureVector
from src.simulator import TransactionSimulator
from src.state_manager import RedisStateManager
from integration.handler import IntegrationHandler
from integration.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    KAFKA_GROUP_ID,
    REDIS_HOST,
    REDIS_PORT,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("IntegratedDemo")


def check_live_services(redis_host: str, redis_port: int) -> bool:
    """Check if Redis is reachable (indicates infrastructure is up)."""
    try:
        with socket.create_connection((redis_host, redis_port), timeout=0.3):
            return True
    except (OSError, socket.error):
        return False


def main():
    parser = argparse.ArgumentParser(description="StreamSentinel Integrated Demo (Person A + Person B)")
    parser.add_argument("--mode", choices=["auto", "live", "mock"], default="auto",
                        help="Run mode: auto (detect services), live, or mock (default: auto)")
    parser.add_argument("--dataset", default="data/fraud_sample.csv",
                        help="Path to dataset CSV (default: data/fraud_sample.csv)")
    parser.add_argument("--rate", type=float, default=2.0,
                        help="Replay rate in transactions/sec (default: 2.0)")
    parser.add_argument("--limit", type=int, default=10,
                        help="Number of transactions to replay (default: 10)")
    parser.add_argument("--trigger-fraud", action="store_true",
                        help="Inject a known fraud transaction for demo")
    parser.add_argument("--kafka", default=KAFKA_BOOTSTRAP_SERVERS, help="Kafka broker address")
    parser.add_argument("--redis-host", default=REDIS_HOST, help="Redis host")
    parser.add_argument("--redis-port", type=int, default=REDIS_PORT, help="Redis port")

    args = parser.parse_args()

    print("=" * 70)
    print(" STREAM SENTINEL : INTEGRATED DEMO (PERSON A + PERSON B)")
    print("=" * 70)

    # Initialize Person B detection service (loads model, rules, SHAP)
    print("\n[INIT] Loading Person B Detection Service...")
    handler = IntegrationHandler()
    print("[INIT] Person B Detection Service ready.\n")

    # Determine run mode
    use_live = False
    if args.mode == "live":
        use_live = True
    elif args.mode == "auto":
        use_live = check_live_services(args.redis_host, args.redis_port)

    # Create the integrated callback
    def integrated_callback(fv: FeatureVector):
        """Person A emits FeatureVector → Person B scores it."""
        print("\n" + "-" * 60)
        print(f"  [PERSON A] FEATURE VECTOR EMITTED")
        print(f"  Transaction: {fv.transaction_id}")
        print(f"  User:        {fv.user_id}")
        print(f"  Amount:      ${fv.amount:.2f}")
        print(f"  Avg Ratio:   {fv.amount_vs_avg_ratio:.2f}")
        print(f"  Velocity:    {fv.txn_count_last_5min} txns in 5min")
        print(f"  Time Gap:    {fv.time_since_last_txn_sec:.1f}s")
        print(f"  Distance:    {fv.distance_from_last_location_km:.1f}km")
        print(f"  New Merchant: {fv.merchant_category_is_new_for_user}")
        print("-" * 60)

        # Hand off to Person B
        result = handler.handle_feature_vector(fv)

        if result:
            print(f"\n  [PERSON B] SCORING OUTPUT")
            print(f"  Risk Score:   {result['risk_score']:.4f}")
            print(f"  ML Score:     {result['ml_fraud_score']:.4f}")
            print(f"  Rules:        {result['rule_flags']}")
            print(f"  Decision:     {result['decision'].upper()}")
            print(f"  Latency:      {result['latency_ms']:.1f} ms")
            print(f"  Reason:       {result['human_readable_reason']}")
            print(f"  Processed At: {result['processed_at']}")
        else:
            print("  [PERSON B] Detection failed for this transaction.")

        print("-" * 60 + "\n")

    if use_live:
        print(f"[STATUS] LIVE MODE (Kafka @ {args.kafka}, Redis @ {args.redis_host}:{args.redis_port})")
        state_mgr = RedisStateManager(host=args.redis_host, port=args.redis_port)
        producer = StreamSentinelProducer(bootstrap_servers=args.kafka, topic=KAFKA_TOPIC)
        consumer = StreamSentinelConsumer(
            bootstrap_servers=args.kafka,
            topic=KAFKA_TOPIC,
            state_manager=state_mgr,
            on_feature_vector=integrated_callback,
        )
    else:
        print("[STATUS] MOCK MODE (in-memory broker + fakeredis)")
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        state_mgr = RedisStateManager(redis_client=fake_redis, key_prefix="demo")

        consumer = StreamSentinelConsumer(
            state_manager=state_mgr,
            mock_mode=True,
            on_feature_vector=integrated_callback,
        )

        def mock_broker(topic: str, key: str, value: str):
            consumer.process_raw_message(value)

        producer = StreamSentinelProducer(mock_transport=mock_broker)

    simulator = TransactionSimulator(
        producer=producer,
        dataset_path=args.dataset,
        rate_per_sec=args.rate,
    )

    if args.trigger_fraud:
        print("\n[ACTION] Triggering on-demand fraud transaction...")
        fraud_event = simulator.trigger_on_demand_fraud()
        if fraud_event:
            print(f"Injected fraud event: {fraud_event.transaction_id}")
        return

    print(f"\n[ACTION] Replaying {args.limit} transactions at {args.rate} txns/sec...\n")
    replayed = simulator.replay(limit=args.limit)
    print(f"\n[SUCCESS] Completed replay of {replayed} transactions through full A->B pipeline!")
    print("=" * 70)


if __name__ == "__main__":
    main()
