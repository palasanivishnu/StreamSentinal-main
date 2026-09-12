"""ML inference engine using XGBoost for fraud detection."""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import xgboost as xgb

from .feature_contract import (
    FEATURE_COLUMNS,
    FEATURE_COUNT,
    MODEL_NAME,
    MODEL_VERSION
)

SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
MODELS_DIR = PROJECT_ROOT / "models"

MODEL_PATH = MODELS_DIR / "xgboost_fraud_detector.json"
CONFIG_PATH = MODELS_DIR / "deployment_config.json"
FEATURE_PATH = MODELS_DIR / "feature_columns.json"

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model file not found: {MODEL_PATH}"
    )

if not CONFIG_PATH.exists():
    raise FileNotFoundError(
        f"Deployment config not found: {CONFIG_PATH}"
    )

if not FEATURE_PATH.exists():
    raise FileNotFoundError(
        f"Feature contract file not found: {FEATURE_PATH}"
    )

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    CONFIG = json.load(file)

with open(FEATURE_PATH, "r", encoding="utf-8") as file:
    SAVED_FEATURE_CONTRACT = json.load(file)

saved_features = SAVED_FEATURE_CONTRACT["features"]

if saved_features != FEATURE_COLUMNS:
    raise ValueError(
        "Saved feature order does not match feature_contract.py"
    )

if len(saved_features) != FEATURE_COUNT:
    raise ValueError(
        "Saved feature count does not match feature_contract.py"
    )

CLASSIFICATION_THRESHOLD = float(
    CONFIG["classification_threshold"]
)

MODEL = xgb.XGBClassifier()
MODEL.load_model(MODEL_PATH)

def predict_transaction(transaction):
    if not isinstance(transaction, dict):
        raise TypeError(
            "Transaction must be a dictionary."
        )

    missing_features = [
        feature
        for feature in FEATURE_COLUMNS
        if feature not in transaction
    ]

    if missing_features:
        raise ValueError(
            f"Missing required ML features: {missing_features}"
        )

    values = {
        feature: transaction[feature]
        for feature in FEATURE_COLUMNS
    }

    input_df = pd.DataFrame(
        [values],
        columns=FEATURE_COLUMNS
    )

    for feature in FEATURE_COLUMNS:
        input_df[feature] = pd.to_numeric(
            input_df[feature],
            errors="coerce"
        )

    if input_df.isnull().any().any():
        raise ValueError(
            "Transaction contains missing or invalid feature values."
        )

    input_array = input_df.to_numpy(
        dtype=float
    )

    if not np.isfinite(input_array).all():
        raise ValueError(
            "Transaction contains non-finite feature values."
        )

    fraud_probability = float(
        MODEL.predict_proba(input_df)[0, 1]
    )

    prediction = int(
        fraud_probability >= CLASSIFICATION_THRESHOLD
    )

    prediction_label = (
        "Fraud"
        if prediction == 1
        else "Legitimate"
    )

    return {
        "ml_score": fraud_probability,
        "ml_prediction": prediction,
        "ml_label": prediction_label,
        "model": MODEL_NAME,
        "model_version": MODEL_VERSION
    }
