"""
StreamSentinel — MongoDB Database Persistence Layer.

Handles storage and retrieval for transactions, security alerts,
and OTP lifecycle state.
"""
from pymongo import MongoClient, DESCENDING
from datetime import datetime, timezone
import logging

from src.config import MONGODB_URI, MONGODB_DATABASE

logger = logging.getLogger("streamsentinel.db")

MONGO_URI = MONGODB_URI
DB_NAME = MONGODB_DATABASE

import json
import uuid
from pathlib import Path

DB_FILE = Path("data/local_db.json")


class FileCollection:
    """Thread-safe persistent JSON collection fallback when standalone MongoDB is unavailable."""

    def __init__(self, name, db_path=DB_FILE):
        self.name = name
        self.db_path = db_path

    def _read_data(self):
        if not self.db_path.exists():
            return []
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(self.name, [])
        except Exception:
            return []

    def _write_data(self, items):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        all_data = {}
        if self.db_path.exists():
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
            except Exception:
                all_data = {}
        all_data[self.name] = items
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2)

    def insert_one(self, doc):
        items = self._read_data()
        doc = dict(doc)
        if "_id" not in doc:
            doc["_id"] = str(uuid.uuid4())
        items.insert(0, doc)
        self._write_data(items)
        return doc

    def find(self, query=None):
        items = self._read_data()
        query = query or {}
        filtered = []

        import re

        def matches_subquery(item, subq):
            for k, v in subq.items():
                if isinstance(v, dict):
                    val = item.get(k)
                    if "$in" in v and val not in v["$in"]:
                        return False
                    if "$gte" in v and (val is None or val < v["$gte"]):
                        return False
                    if "$regex" in v:
                        opts = re.IGNORECASE if v.get("$options") == "i" else 0
                        if not re.search(v["$regex"], str(val or ""), opts):
                            return False
                else:
                    if item.get(k) != v:
                        return False
            return True

        for item in items:
            match = True
            for k, v in query.items():
                if k == "$or" and isinstance(v, list):
                    if not any(matches_subquery(item, subq) for subq in v):
                        match = False
                        break
                elif isinstance(v, dict):
                    val = item.get(k)
                    if "$in" in v and val not in v["$in"]:
                        match = False
                        break
                    if "$gte" in v and (val is None or val < v["$gte"]):
                        match = False
                        break
                    if "$regex" in v:
                        opts = re.IGNORECASE if v.get("$options") == "i" else 0
                        if not re.search(v["$regex"], str(val or ""), opts):
                            match = False
                            break
                elif item.get(k) != v:
                    match = False
                    break
            if match:
                filtered.append(dict(item))

        class SimpleCursor(list):
            def sort(self, key, direction=None):
                return self
            def limit(self, n):
                return SimpleCursor(self[:n])

        return SimpleCursor(filtered)

    def find_one(self, query=None):
        results = self.find(query)
        return results[0] if results else None

    def count_documents(self, query=None):
        return len(self.find(query))

    def update_one(self, filter_q, update_q):
        items = self._read_data()
        modified = 0
        set_fields = update_q.get("$set", {})
        for item in items:
            match = all(item.get(k) == v for k, v in filter_q.items())
            if match:
                item.update(set_fields)
                modified += 1
                break
        if modified:
            self._write_data(items)
        class UpdateRes:
            modified_count = modified
        return UpdateRes()

    def update_many(self, filter_q, update_q):
        items = self._read_data()
        modified = 0
        set_fields = update_q.get("$set", {})
        for item in items:
            match = all(item.get(k) == v for k, v in filter_q.items())
            if match:
                item.update(set_fields)
                modified += 1
        if modified:
            self._write_data(items)
        class UpdateRes:
            modified_count = modified
        return UpdateRes()

    def aggregate(self, pipeline):
        items = self._read_data()
        if not items:
            return []
        risks = [item.get("risk_score", 0.0) for item in items if "risk_score" in item]
        avg = sum(risks) / len(risks) if risks else 0.0
        return [{"_id": None, "avg_risk": avg}]


try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client[DB_NAME]
    transactions_col = db["transactions"]
    alerts_col = db["alerts"]
    otps_col = db["otps"]
except Exception as e:
    logger.info("Standalone MongoDB unavailable. Using persistent FileCollection database for seamless multi-process sharing.")
    client = None
    db = None
    transactions_col = FileCollection("transactions")
    alerts_col = FileCollection("alerts")
    otps_col = FileCollection("otps")


def save_transaction(transaction_result):
    """Persist scoring result to MongoDB."""
    if transactions_col is None:
        return False
    try:
        doc = dict(transaction_result)
        if "_id" in doc:
            del doc["_id"]
        doc["saved_at"] = datetime.now(timezone.utc).isoformat()
        transactions_col.insert_one(doc)
        return True
    except Exception as e:
        logger.error(f"Failed to save transaction: {e}")
        return False


def get_recent_transactions(limit=50, filter_query=None):
    """Retrieve recent transactions from MongoDB."""
    if transactions_col is None:
        return []
    try:
        query = filter_query or {}
        cursor = transactions_col.find(query).sort("_id", DESCENDING).limit(limit)
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        return []


def update_transaction_decision(transaction_id, new_decision, additional_fields=None):
    """Update decision/status for a transaction (e.g., after OTP verification)."""
    if transactions_col is None:
        return False
    try:
        update_data = {"$set": {"decision": new_decision}}
        if additional_fields:
            for k, v in additional_fields.items():
                update_data["$set"][k] = v
        update_data["$set"]["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = transactions_col.update_many({"transaction_id": transaction_id}, update_data)
        return res.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating transaction decision: {e}")
        return False


def save_alert(alert_data):
    """Persist a security alert record."""
    if alerts_col is None:
        return False
    try:
        doc = dict(alert_data)
        if "_id" in doc:
            del doc["_id"]
        alerts_col.insert_one(doc)
        return True
    except Exception as e:
        logger.error(f"Failed to save alert: {e}")
        return False


def get_recent_alerts(limit=50, severity=None):
    """Retrieve recent fraud alerts."""
    if alerts_col is None:
        return []
    try:
        query = {}
        if severity:
            query["severity"] = severity
        cursor = alerts_col.find(query).sort("_id", DESCENDING).limit(limit)
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return []


def acknowledge_alert(alert_id):
    """Mark an alert as acknowledged."""
    if alerts_col is None:
        return False
    try:
        res = alerts_col.update_one(
            {"alert_id": alert_id},
            {"$set": {"acknowledged": True, "acknowledged_at": datetime.now(timezone.utc).isoformat()}}
        )
        return res.modified_count > 0
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}")
        return False


def save_otp_record(otp_record):
    """Persist OTP record to MongoDB."""
    if otps_col is None:
        return False
    try:
        doc = dict(otp_record)
        if "_id" in doc:
            del doc["_id"]
        otps_col.insert_one(doc)
        return True
    except Exception as e:
        logger.error(f"Failed to save OTP record: {e}")
        return False


def get_otp_records(user_id=None, transaction_id=None):
    """Fetch OTP records for a user or transaction."""
    if otps_col is None:
        return []
    try:
        query = {}
        if user_id:
            query["user_id"] = user_id
        if transaction_id:
            query["transaction_id"] = transaction_id
        cursor = otps_col.find(query).sort("_id", DESCENDING)
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
    except Exception as e:
        logger.error(f"Error fetching OTP records: {e}")
        return []


def update_otp_record_status(user_id, otp_code, new_status):
    """Update status of an OTP record."""
    if otps_col is None:
        return False
    try:
        res = otps_col.update_many(
            {"user_id": user_id, "otp": otp_code},
            {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        return res.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating OTP record status: {e}")
        return False


def get_dashboard_metrics():
    """Aggregate high-level metrics for dashboard presentation."""
    if transactions_col is None:
        return {
            "total_transactions": 0,
            "allow_count": 0,
            "otp_count": 0,
            "review_count": 0,
            "block_count": 0,
            "avg_risk_score": 0.0,
            "alerts_count": 0
        }
    try:
        total = transactions_col.count_documents({})
        allow_c = transactions_col.count_documents({"decision": "allow"})
        otp_c = transactions_col.count_documents({"decision": "otp"})
        review_c = transactions_col.count_documents({"decision": "review"})
        block_c = transactions_col.count_documents({"decision": "block"})
        
        alerts_c = alerts_col.count_documents({}) if alerts_col is not None else 0

        pipeline = [{"$group": {"_id": None, "avg_risk": {"$avg": "$risk_score"}}}]
        agg = list(transactions_col.aggregate(pipeline))
        avg_risk = agg[0]["avg_risk"] if agg and "avg_risk" in agg[0] else 0.0

        return {
            "total_transactions": total,
            "allow_count": allow_c,
            "otp_count": otp_c,
            "review_count": review_c,
            "block_count": block_c,
            "avg_risk_score": round(float(avg_risk or 0.0), 4),
            "alerts_count": alerts_c
        }
    except Exception as e:
        logger.error(f"Error calculating dashboard metrics: {e}")
        return {
            "total_transactions": 0,
            "allow_count": 0,
            "otp_count": 0,
            "review_count": 0,
            "block_count": 0,
            "avg_risk_score": 0.0,
            "alerts_count": 0
        }
