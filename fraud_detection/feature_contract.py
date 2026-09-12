"""Feature contract for Person A → Person B integration."""

FEATURE_COLUMNS = [
    "amount",
    "amount_vs_avg_ratio",
    "txn_count_last_5min",
    "time_since_last_txn_sec",
    "distance_from_last_location_km",
    "merchant_category_is_new_for_user"
]

FEATURE_COUNT = len(FEATURE_COLUMNS)
MODEL_VERSION = "2.0"
MODEL_NAME = "XGBoost"
