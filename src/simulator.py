"""Transaction Simulator for StreamSentinel.

Replays the credit card fraud detection dataset through Kafka at a controlled pace,
with support for on-demand fraud triggering for live demos.
"""

import argparse
import csv
import io
import json
import logging
import os
import sys
import time
import uuid
import zipfile
from datetime import datetime, timezone
from typing import Generator, Iterator, Optional, Tuple

from src.producer import StreamSentinelProducer
from src.schemas import Location, TransactionEvent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("Simulator")


def format_to_uuid(trans_num: str) -> str:
    """Convert transaction string / 32-hex string to standard UUID representation."""
    cleaned = trans_num.strip().replace("-", "")
    if len(cleaned) == 32:
        try:
            return str(uuid.UUID(hex=cleaned))
        except ValueError:
            pass
    # Fallback to deterministic UUID5
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, trans_num))


def parse_csv_row_to_event(row: dict) -> Tuple[TransactionEvent, bool]:
    """Parse a CSV dictionary row into a validated TransactionEvent and is_fraud flag."""
    trans_id = format_to_uuid(row.get("trans_num", str(uuid.uuid4())))
    user_id = str(row.get("cc_num", "")).strip()
    amount = float(row.get("amt", 0.0))
    merchant_id = str(row.get("merchant", "")).strip()
    merchant_category = str(row.get("category", "")).strip()

    lat = float(row.get("lat", 0.0))
    lon = float(row.get("long", 0.0))
    location = Location(lat=lat, lon=lon)

    # Format timestamp to ISO 8601
    raw_time = row.get("trans_date_trans_time", "")
    unix_time = row.get("unix_time")
    if unix_time:
        try:
            iso_time = datetime.fromtimestamp(float(unix_time), tz=timezone.utc).isoformat()
        except (ValueError, TypeError):
            iso_time = datetime.now(timezone.utc).isoformat()
    elif raw_time:
        try:
            dt = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
            iso_time = dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            iso_time = datetime.now(timezone.utc).isoformat()
    else:
        iso_time = datetime.now(timezone.utc).isoformat()

    is_fraud = str(row.get("is_fraud", "0")).strip() == "1"

    event = TransactionEvent(
        transaction_id=trans_id,
        user_id=user_id,
        amount=amount,
        currency="USD",
        merchant_id=merchant_id,
        merchant_category=merchant_category,
        location=location,
        timestamp=iso_time,
    )
    return event, is_fraud


class DatasetReader:
    """Reads transactions from CSV or ZIP file."""

    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path

    def rows(self) -> Generator[dict, None, None]:
        """Yield dictionary rows from dataset file."""
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Dataset not found at {self.dataset_path}")

        if self.dataset_path.endswith(".zip"):
            with zipfile.ZipFile(self.dataset_path, "r") as z:
                # Find the first .csv inside the zip
                csv_files = [f for f in z.namelist() if f.endswith(".csv")]
                if not csv_files:
                    raise ValueError(f"No CSV file found inside zip {self.dataset_path}")
                with z.open(csv_files[0], "r") as f:
                    reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
                    for row in reader:
                        yield row
        else:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    yield row


class TransactionSimulator:
    """Streams dataset transactions to Kafka producer with pacing and demo controls."""

    def __init__(
        self,
        producer: StreamSentinelProducer,
        dataset_path: str = "data/fraud_sample.csv",
        rate_per_sec: float = 2.0,
    ):
        self.producer = producer
        self.dataset_path = dataset_path
        self.rate_per_sec = max(0.1, rate_per_sec)
        self.interval = 1.0 / self.rate_per_sec
        self.reader = DatasetReader(dataset_path)

    def replay(self, limit: Optional[int] = None, loop: bool = False) -> int:
        """Replay transactions at the configured rate.

        :param limit: Maximum number of transactions to replay (None for all).
        :param loop: If True, loops back to beginning upon reaching end of file.
        :return: Total transactions replayed.
        """
        replayed_count = 0
        logger.info(
            "Starting replay from %s at %.2f txns/sec (interval=%.3fs, limit=%s)",
            self.dataset_path,
            self.rate_per_sec,
            self.interval,
            limit,
        )

        while True:
            for row in self.reader.rows():
                event, is_fraud = parse_csv_row_to_event(row)
                res = self.producer.publish_transaction(event)
                replayed_count += 1

                fraud_marker = " [*** FRAUD CASE ***]" if is_fraud else ""
                logger.info(
                    "[%d] Published txn %s | User: %s | $%.2f | Cat: %s%s",
                    replayed_count,
                    event.transaction_id[:8],
                    event.user_id,
                    event.amount,
                    event.merchant_category,
                    fraud_marker,
                )

                if limit is not None and replayed_count >= limit:
                    self.producer.flush()
                    logger.info("Reached replay limit of %d transactions.", limit)
                    return replayed_count

                time.sleep(self.interval)

            if not loop:
                break
            logger.info("Reached EOF; looping back to beginning.")

        self.producer.flush()
        return replayed_count

    def trigger_on_demand_fraud(self) -> Optional[TransactionEvent]:
        """Scan dataset, locate a known fraudulent transaction (is_fraud==1), and inject it immediately.

        Used for live team demos to trigger downstream rule engine & ML alerts on demand.
        """
        logger.info("Scanning for on-demand fraud transaction in %s...", self.dataset_path)
        for row in self.reader.rows():
            event, is_fraud = parse_csv_row_to_event(row)
            if is_fraud:
                logger.warning(
                    "TRIGGERING ON-DEMAND FRAUD TRANSACTION: ID=%s, User=%s, Amt=$%.2f, Cat=%s",
                    event.transaction_id,
                    event.user_id,
                    event.amount,
                    event.merchant_category,
                )
                self.producer.publish_transaction(event)
                self.producer.flush()
                return event

        logger.error("No fraud record found in %s", self.dataset_path)
        return None


def main():
    parser = argparse.ArgumentParser(description="StreamSentinel Transaction Simulator")
    parser.add_argument(
        "--dataset",
        default="data/fraud_sample.csv",
        help="Path to CSV or ZIP dataset file (default: data/fraud_sample.csv)",
    )
    parser.add_argument(
        "--kafka",
        default="localhost:9092",
        help="Kafka bootstrap servers (default: localhost:9092)",
    )
    parser.add_argument(
        "--topic",
        default="transactions",
        help="Kafka topic name (default: transactions)",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=2.0,
        help="Replay rate in transactions per second (default: 2.0)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max number of transactions to replay (default: unlimited)",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop continuously when dataset ends",
    )
    parser.add_argument(
        "--trigger-fraud",
        action="store_true",
        help="Immediately inject a known fraud transaction for live demo",
    )

    args = parser.parse_args()

    # Fallback paths for dataset
    dataset_path = args.dataset
    if not os.path.exists(dataset_path):
        candidate = os.path.expanduser(r"~\Downloads\fraudTest.csv.zip")
        if os.path.exists(candidate):
            dataset_path = candidate
            logger.info("Using dataset from Downloads: %s", dataset_path)

    producer = StreamSentinelProducer(bootstrap_servers=args.kafka, topic=args.topic)
    simulator = TransactionSimulator(
        producer=producer,
        dataset_path=dataset_path,
        rate_per_sec=args.rate,
    )

    if args.trigger_fraud:
        event = simulator.trigger_on_demand_fraud()
        if event:
            print(json.dumps(event.model_dump(), indent=2))
        sys.exit(0)

    simulator.replay(limit=args.limit, loop=args.loop)


if __name__ == "__main__":
    main()
