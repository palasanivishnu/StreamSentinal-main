"""SHAP-based explainability for fraud detection."""

from pathlib import Path
import numpy as np
import pandas as pd
import shap
import xgboost as xgb

SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
MODELS_DIR = PROJECT_ROOT / "models"

MODEL_PATH = MODELS_DIR / "xgboost_fraud_detector.json"
FEATURE_PATH = MODELS_DIR / "feature_columns.json"

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model file not found: {MODEL_PATH}"
    )

if not FEATURE_PATH.exists():
    raise FileNotFoundError(
        f"Feature contract file not found: {FEATURE_PATH}"
    )

with open(FEATURE_PATH, "r", encoding="utf-8") as file:
    FEATURE_CONFIG = __import__("json").load(file)

FEATURE_COLUMNS = FEATURE_CONFIG["features"]

MODEL = xgb.XGBClassifier()
MODEL.load_model(MODEL_PATH)

EXPLAINER = shap.TreeExplainer(MODEL)


def explain_transaction(transaction, top_n=3):
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
            f"Missing SHAP features: {missing_features}"
        )

    input_df = pd.DataFrame(
        [
            {
                feature: transaction[feature]
                for feature in FEATURE_COLUMNS
            }
        ],
        columns=FEATURE_COLUMNS
    )

    for feature in FEATURE_COLUMNS:
        input_df[feature] = pd.to_numeric(
            input_df[feature],
            errors="coerce"
        )

    if input_df.isnull().any().any():
        raise ValueError(
            "Invalid SHAP input values."
        )

    input_array = input_df.to_numpy(dtype=float)

    if not np.isfinite(input_array).all():
        raise ValueError(
            "Non-finite SHAP input values."
        )

    values = np.asarray(
        EXPLAINER.shap_values(input_df)
    )

    if values.ndim == 2:
        values = values[0]

    if len(values) != len(FEATURE_COLUMNS):
        raise ValueError(
            "SHAP output size does not match feature count."
        )

    explanation_df = pd.DataFrame({
        "feature": FEATURE_COLUMNS,
        "feature_value": input_df.iloc[0].to_numpy(),
        "shap_value": values
    })

    explanation_df["absolute_shap"] = (
        explanation_df["shap_value"].abs()
    )

    explanation_df = (
        explanation_df
        .sort_values(
            "absolute_shap",
            ascending=False
        )
        .reset_index(drop=True)
    )

    top_features = explanation_df.head(
        max(1, int(top_n))
    )

    return {
        "top_features": top_features[
            [
                "feature",
                "feature_value",
                "shap_value"
            ]
        ].to_dict(orient="records")
    }
