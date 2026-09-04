from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.ml.features import build_features


MODEL_PATH = (
    Path(__file__).resolve().parent
    / "artifacts"
    / "recovery_model.joblib"
)


FEATURE_COLUMNS = [
    "amount",
    "previous_attempts",
    "failed_attempts",
    "amount_is_high",
    "is_upi",
    "is_card",
    "is_net_banking",
    "failure_reason_code",
]


def load_model():
    """Load the trained recovery model from disk."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Recovery model not found at: {MODEL_PATH}. "
            "Run `python -m app.ml.train` first."
        )

    return joblib.load(MODEL_PATH)


def predict_recovery_probability(
    payment: dict[str, Any],
) -> float:
    """
    Predict the probability that a failed payment
    can be successfully recovered.

    Returns:
        Float between 0 and 1.
    """

    model = load_model()

    features = build_features(payment)

    feature_row = pd.DataFrame(
        [features],
        columns=FEATURE_COLUMNS,
    )

    probability = model.predict_proba(
        feature_row
    )[0][1]

    probability = max(
        0.0,
        min(1.0, float(probability)),
    )

    return round(
        probability,
        4,
    )