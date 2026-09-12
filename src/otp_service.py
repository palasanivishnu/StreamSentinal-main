"""
StreamSentinel — OTP Generation and Verification Service.

Manages 6-digit OTP challenge tokens with 5-minute TTL.
Integrates with MongoDB storage and updates transaction decision on verification.
"""
import random
import uuid
from datetime import datetime, timedelta, timezone
from src.db import save_otp_record, get_otp_records, update_otp_record_status, update_transaction_decision

# In-memory storage for high-speed fallback & state tracking
otp_store = {}


def generate_otp(user_id, transaction_id=None):
    """
    Generate a 6-digit one-time password for a user.
    Optionally links the OTP to a specific transaction_id.
    Stores record in both memory and MongoDB.
    """
    otp = str(random.randint(100000, 999999))
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=5)
    otp_id = f"OTP_{uuid.uuid4().hex[:8].upper()}"

    record = {
        "otp_id": otp_id,
        "user_id": user_id,
        "transaction_id": transaction_id,
        "otp": otp,
        "status": "PENDING",
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "attempts": 0
    }

    entry = {
        "otp_id": otp_id,
        "user_id": user_id,
        "transaction_id": transaction_id,
        "otp": otp,
        "status": "PENDING",
        "created_at": now,
        "expires_at": expires_at,
        "attempts": 0
    }

    # Store in memory indexed by txn_id and user_id
    if transaction_id:
        otp_store[f"txn:{transaction_id}"] = entry
    otp_store[f"user:{user_id}"] = entry
    otp_store[user_id] = entry

    # Persist in MongoDB
    try:
        save_otp_record(record)
    except Exception as e:
        print(f"[OTP SERVICE WARNING] MongoDB save failed: {e}")

    print(f"[OTP SERVICE] Generated OTP for {user_id}: {otp} (Txn: {transaction_id or 'None'})")

    return otp


def verify_otp(user_id, entered_otp, transaction_id=None):
    """
    Verify an entered OTP for a user and transaction.
    Updates status in memory and MongoDB.
    If valid and linked to a transaction, updates transaction decision to 'allow'.
    Returns tuple: (is_valid: bool, message: str)
    """
    now = datetime.now(timezone.utc)
    entered_str = str(entered_otp).strip()

    # 1. Lookup in-memory record by transaction_id first, then user_id
    mem_record = None
    if transaction_id and f"txn:{transaction_id}" in otp_store:
        mem_record = otp_store[f"txn:{transaction_id}"]
    elif f"user:{user_id}" in otp_store:
        mem_record = otp_store[f"user:{user_id}"]
    elif user_id in otp_store:
        mem_record = otp_store[user_id]

    if mem_record:
        stored_otp = str(mem_record.get("otp", "")).strip()
        expires_at = mem_record.get("expires_at")
        txn_id = transaction_id or mem_record.get("transaction_id")
        status = mem_record.get("status", "PENDING")

        # If expires_at is string, parse it cleanly with UTC fallback
        if isinstance(expires_at, str):
            try:
                exp_clean = expires_at.replace("Z", "+00:00")
                expires_at = datetime.fromisoformat(exp_clean)
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
            except Exception:
                expires_at = now + timedelta(minutes=5)

        if status == "VERIFIED":
            return True, "OTP has already been verified for this transaction."

        if now > expires_at:
            mem_record["status"] = "EXPIRED"
            update_otp_record_status(user_id, stored_otp, "EXPIRED")
            return False, "OTP has expired. Please request a new one."

        if stored_otp == entered_str:
            mem_record["status"] = "VERIFIED"
            update_otp_record_status(user_id, stored_otp, "VERIFIED")

            # Update transaction decision to allow in MongoDB
            if txn_id:
                update_transaction_decision(
                    txn_id,
                    new_decision="allow",
                    additional_fields={
                        "otp_verified": True,
                        "otp_verified_at": now.isoformat(),
                        "otp_status": "VERIFIED"
                    }
                )

            return True, "OTP verified successfully. Transaction approved."
        else:
            if txn_id:
                update_transaction_decision(
                    txn_id,
                    new_decision="block",
                    additional_fields={
                        "otp_verified": False,
                        "otp_verified_at": now.isoformat(),
                        "otp_status": "FAILED",
                        "human_readable_reason": "Blocked due to failed 2FA OTP verification."
                    }
                )
            return False, "Invalid OTP code. Transaction blocked."

    # 2. Fallback to MongoDB lookup if not in memory
    db_records = get_otp_records(user_id=user_id, transaction_id=transaction_id)
    if not db_records and user_id:
        db_records = get_otp_records(user_id=user_id)
    if not db_records:
        return False, "No OTP record found for this user."

    # Filter candidate records for matching transaction_id or user_id
    candidates = []
    if transaction_id:
        candidates = [r for r in db_records if r.get("transaction_id") == transaction_id]
    if not candidates:
        candidates = db_records

    target_record = None
    # 1. First priority: candidate with status=='PENDING', unexpired, and matching entered_str
    for rec in candidates:
        if rec.get("status") == "PENDING":
            exp_str = rec.get("expires_at")
            exp_ok = True
            if exp_str:
                try:
                    exp_clean = str(exp_str).replace("Z", "+00:00")
                    exp_dt = datetime.fromisoformat(exp_clean)
                    if exp_dt.tzinfo is None:
                        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                    if now >= exp_dt:
                        exp_ok = False
                except Exception:
                    pass
            if exp_ok and str(rec.get("otp", "")).strip() == entered_str:
                target_record = rec
                break

    # 2. Second priority: newest candidate with status=='PENDING' and unexpired
    if not target_record:
        for rec in candidates:
            if rec.get("status") == "PENDING":
                exp_str = rec.get("expires_at")
                exp_ok = True
                if exp_str:
                    try:
                        exp_clean = str(exp_str).replace("Z", "+00:00")
                        exp_dt = datetime.fromisoformat(exp_clean)
                        if exp_dt.tzinfo is None:
                            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                        if now >= exp_dt:
                            exp_ok = False
                    except Exception:
                        pass
                if exp_ok:
                    target_record = rec
                    break

    # 3. Fallback to first candidate if all are expired or non-pending
    if not target_record:
        target_record = candidates[0]

    stored_otp = str(target_record.get("otp", "")).strip()
    exp_str = target_record.get("expires_at")
    txn_id = transaction_id or target_record.get("transaction_id")
    rec_status = target_record.get("status", "PENDING")

    if rec_status == "VERIFIED":
        return True, "OTP has already been verified for this transaction."

    if exp_str:
        try:
            exp_clean = str(exp_str).replace("Z", "+00:00")
            exp_dt = datetime.fromisoformat(exp_clean)
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            if now > exp_dt:
                update_otp_record_status(user_id, stored_otp, "EXPIRED")
                return False, "OTP has expired. Please request a new one."
        except Exception:
            pass

    if stored_otp == entered_str:
        update_otp_record_status(user_id, stored_otp, "VERIFIED")
        if txn_id:
            update_transaction_decision(
                txn_id,
                new_decision="allow",
                additional_fields={
                    "otp_verified": True,
                    "otp_verified_at": now.isoformat(),
                    "otp_status": "VERIFIED"
                }
            )
        return True, "OTP verified successfully. Transaction approved."

    if txn_id:
        update_transaction_decision(
            txn_id,
            new_decision="block",
            additional_fields={
                "otp_verified": False,
                "otp_verified_at": now.isoformat(),
                "otp_status": "FAILED",
                "human_readable_reason": "Blocked due to failed 2FA OTP verification."
            }
        )
    return False, "Invalid OTP code. Transaction blocked."


def get_all_otps():
    """Return all active or historical OTP records."""
    db_otps = get_otp_records()
    if db_otps:
        return db_otps
    # Fallback to in-memory store
    memory_list = []
    seen_ids = set()
    for key, data in otp_store.items():
        oid = data.get("otp_id") or key
        if oid in seen_ids:
            continue
        seen_ids.add(oid)
        exp = data["expires_at"]
        exp_iso = exp.isoformat() if isinstance(exp, datetime) else str(exp)
        memory_list.append({
            "user_id": data.get("user_id"),
            "otp": data["otp"],
            "transaction_id": data.get("transaction_id"),
            "status": data.get("status"),
            "expires_at": exp_iso
        })
    return memory_list
