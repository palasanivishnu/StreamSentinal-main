"""Redis stateful profile manager for StreamSentinel.

Maintains live per-user profiles and computes Feature Vectors.
"""

import math
import os
from datetime import datetime
from typing import Optional, Tuple, Union
import dateutil.parser
import redis

from src.schemas import FeatureVector, TransactionEvent


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on Earth in kilometers."""
    r = 6371.0  # Earth radius in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 4)


def parse_timestamp_to_epoch(ts_str: str) -> float:
    """Parse ISO 8601 or common timestamp string to Unix epoch seconds."""
    dt = dateutil.parser.parse(ts_str)
    return dt.timestamp()


class RedisStateManager:
    """Manages per-user state in Redis and produces Feature Vectors."""

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        key_prefix: str = "stream_sentinel",
        use_event_time_for_window: bool = True,
        redis_url: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize RedisStateManager.

        :param redis_client: Optional existing redis.Redis or fakeredis instance.
        :param host: Redis host (default: localhost).
        :param port: Redis port (default: 6379).
        :param db: Redis database index (default: 0).
        :param key_prefix: Namespace prefix for Redis keys.
        :param use_event_time_for_window: If True, uses transaction timestamp for 5m window.
                                         If False, uses wall-clock time.
        :param redis_url: Optional Redis URL (e.g. rediss://... for cloud Redis with TLS).
        :param password: Optional Redis password for authenticated instances.
        """
        if redis_client is not None:
            self.redis = redis_client
        else:
            effective_url = redis_url or os.getenv("REDIS_URL")
            if effective_url:
                self.redis = redis.from_url(
                    effective_url,
                    decode_responses=True,
                )
            else:
                effective_password = password or os.getenv("REDIS_PASSWORD") or None
                self.redis = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=effective_password,
                    decode_responses=True,
                )
        self.prefix = key_prefix
        self.use_event_time = use_event_time_for_window

    def _user_profile_key(self, user_id: str) -> str:
        return f"{self.prefix}:user:{user_id}:profile"

    def _user_txns_key(self, user_id: str) -> str:
        return f"{self.prefix}:user:{user_id}:txns_5m"

    def _user_categories_key(self, user_id: str) -> str:
        return f"{self.prefix}:user:{user_id}:categories"

    def process_transaction(self, event: TransactionEvent) -> FeatureVector:
        """Look up user state in Redis, compute features, update state, and emit FeatureVector.

        This maintains:
        1. Rolling average transaction amount.
        2. Last known location and timestamp (with distance & elapsed time).
        3. Transaction count in the last 5 minutes.
        4. Category history (detecting if category is new for user).
        """
        user_id = str(event.user_id)
        current_amount = float(event.amount)
        current_lat = float(event.location.lat)
        current_lon = float(event.location.lon)
        current_category = str(event.merchant_category)
        epoch_time = parse_timestamp_to_epoch(event.timestamp)

        profile_key = self._user_profile_key(user_id)
        txns_key = self._user_txns_key(user_id)
        categories_key = self._user_categories_key(user_id)

        # 1. Fetch current profile state
        profile_data = self.redis.hgetall(profile_key)

        # 2. Compute Amount vs Average Ratio
        total_amount = float(profile_data.get("total_amount", 0.0))
        txn_count = int(profile_data.get("txn_count", 0))

        if txn_count > 0 and total_amount > 0.0:
            historical_avg = total_amount / txn_count
            amount_vs_avg_ratio = round(current_amount / historical_avg, 4)
        else:
            # First transaction for this user: ratio is baseline 1.0
            amount_vs_avg_ratio = 1.0

        # 3. Compute Distance and Time Since Last Transaction
        has_last_location = "last_lat" in profile_data and "last_lon" in profile_data
        has_last_time = "last_epoch" in profile_data

        if has_last_location and has_last_time:
            last_lat = float(profile_data["last_lat"])
            last_lon = float(profile_data["last_lon"])
            last_epoch = float(profile_data["last_epoch"])

            distance_km = haversine_distance_km(last_lat, last_lon, current_lat, current_lon)
            time_since_sec = max(0.0, round(epoch_time - last_epoch, 2))
        else:
            # First transaction or no prior location
            distance_km = 0.0
            time_since_sec = 0.0

        # 4. Check if merchant category is new for user
        is_existing_cat = self.redis.sismember(categories_key, current_category)
        merchant_category_is_new = not bool(is_existing_cat)

        # 5. Compute Transaction Count in Last 5 Minutes (300 seconds)
        window_now = epoch_time if self.use_event_time else datetime.utcnow().timestamp()
        cutoff_epoch = window_now - 300.0

        # Prune transactions older than 300 seconds
        self.redis.zremrangebyscore(txns_key, "-inf", f"({cutoff_epoch}")

        # Add current transaction to the sorted set
        # Score = window_now, member = event.transaction_id
        self.redis.zadd(txns_key, {event.transaction_id: window_now})

        # Count total in window (including current transaction)
        txn_count_5m = int(self.redis.zcard(txns_key))

        # 6. Atomic profile update
        new_total_amount = total_amount + current_amount
        new_txn_count = txn_count + 1

        pipeline = self.redis.pipeline()
        pipeline.hset(
            profile_key,
            mapping={
                "total_amount": str(new_total_amount),
                "txn_count": str(new_txn_count),
                "last_lat": str(current_lat),
                "last_lon": str(current_lon),
                "last_epoch": str(epoch_time),
                "last_timestamp": event.timestamp,
            },
        )
        # Add category to user set
        pipeline.sadd(categories_key, current_category)

        # Set 24h TTL on rolling keys to prevent unbounded memory growth
        pipeline.expire(profile_key, 86400 * 30)
        pipeline.expire(txns_key, 86400)
        pipeline.expire(categories_key, 86400 * 30)
        pipeline.execute()

        # Format clean merchant name
        merchant_raw = getattr(event, "merchant_id", "") or ""
        merchant_clean = merchant_raw.replace("fraud_", "").replace("_", " ").strip() if merchant_raw.startswith("fraud_") else merchant_raw.replace("_", " ").strip()

        # 7. Construct and return validated Feature Vector
        return FeatureVector(
            transaction_id=event.transaction_id,
            user_id=event.user_id,
            amount=current_amount,
            amount_vs_avg_ratio=amount_vs_avg_ratio,
            txn_count_last_5min=txn_count_5m,
            time_since_last_txn_sec=time_since_sec,
            distance_from_last_location_km=distance_km,
            merchant_category_is_new_for_user=merchant_category_is_new,
            merchant=merchant_clean or "Retail Merchant",
            merchant_category=current_category or "retail",
        )

    def reset_user_state(self, user_id: str):
        """Helper to clear state for a specific user."""
        self.redis.delete(
            self._user_profile_key(user_id),
            self._user_txns_key(user_id),
            self._user_categories_key(user_id),
        )

    def flush_all_state(self):
        """Helper to clear all keys matching stream_sentinel namespace."""
        cursor = 0
        while True:
            cursor, keys = self.redis.scan(cursor=cursor, match=f"{self.prefix}:*", count=500)
            if keys:
                self.redis.delete(*keys)
            if cursor == 0:
                break
