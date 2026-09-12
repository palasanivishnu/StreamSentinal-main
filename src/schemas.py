"""Data contracts for StreamSentinel Person A pipeline.

Schemas strictly match the contracts defined in AGENTS.md.
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class Location(BaseModel):
    lat: float
    lon: float


class TransactionEvent(BaseModel):
    """Transaction Event published to Kafka, partitioned by user_id."""

    transaction_id: str = Field(description="UUID string identifying transaction")
    user_id: str = Field(description="User identifier (maps to cc_num)")
    amount: float = Field(description="Transaction amount in specified currency")
    currency: str = Field(default="USD", description="ISO 4217 currency code")
    merchant_id: str = Field(description="Merchant identifier")
    merchant_category: str = Field(description="Category of the merchant")
    location: Location = Field(description="Location of transaction (lat, lon)")
    timestamp: str = Field(description="ISO 8601 formatted timestamp")

    @field_validator("transaction_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        # Validate that string is a valid UUID format
        try:
            val = UUID(v)
            return str(val)
        except ValueError:
            raise ValueError(f"transaction_id '{v}' is not a valid UUID")


class FeatureVector(BaseModel):
    """Feature Vector emitted from consumer/Redis state.

    Consumed downstream by Person B's rule engine and ML model.
    """

    transaction_id: str = Field(description="UUID string matching the transaction")
    user_id: str = Field(description="User identifier")
    amount: float = Field(description="Transaction amount")
    amount_vs_avg_ratio: float = Field(description="Ratio of current amount to historical average")
    txn_count_last_5min: int = Field(description="Transaction count in the last 5 minutes")
    time_since_last_txn_sec: float = Field(description="Seconds since user's previous transaction")
    distance_from_last_location_km: float = Field(description="Distance in km from user's last known location")
    merchant_category_is_new_for_user: bool = Field(description="Whether merchant category is new for this user")
    merchant: Optional[str] = Field(default=None, description="Clean merchant name")
    merchant_category: Optional[str] = Field(default=None, description="Merchant category name")

    @field_validator("transaction_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            val = UUID(v)
            return str(val)
        except ValueError:
            raise ValueError(f"transaction_id '{v}' is not a valid UUID")
