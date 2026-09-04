from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.features import build_features


MODEL_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = MODEL_DIR / "recovery_model.joblib"

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

RANDOM_SEED = 42
N_SAMPLES = 5000


FAILURE_REASONS = [
    "Insufficient Funds",
    "Bank Declined",
    "Timeout",
    "Network Error",
    "Expired Card",
    "Invalid Card",
    "Fraud Suspected",
    "Account Blocked",
]

PAYMENT_METHODS = [
    "UPI",
    "CARD",
    "NET_BANKING",
]


def _recovery_probability(
    *,
    amount: float,
    previous_attempts: int,
    failed_attempts: int,
    payment_method: str,
    failure_reason: str,
) -> float:
    """
    Generate the synthetic ground-truth probability.

    IMPORTANT:
        This function is used only to generate the synthetic training
        outcome. It is NOT the ML model and is NOT used by prediction.py.

    The benchmark simulator has a separate outcome mechanism, so the
    evaluation is not circular.
    """

    probability = 0.20

    reason = failure_reason.lower()
    method = payment_method.lower()

    # Failure-type signal.
    if "insufficient" in reason:
        probability += 0.45
    elif "timeout" in reason:
        probability += 0.40
    elif "network" in reason:
        probability += 0.35
    elif "bank declined" in reason:
        probability += 0.12
    elif "expired" in reason:
        probability += 0.02
    elif "invalid card" in reason:
        probability -= 0.05
    elif "fraud" in reason:
        probability -= 0.15
    elif "blocked" in reason:
        probability -= 0.15

    # Payment-method signal.
    if method == "upi":
        probability += 0.05
    elif method == "net_banking":
        probability += 0.02

    # Higher-value payments are slightly harder to recover.
    if amount >= 3000:
        probability -= 0.05
    elif amount < 1000:
        probability += 0.03

    # Repeated failures reduce expected recovery.
    probability -= previous_attempts * 0.10
    probability -= failed_attempts * 0.04

    return float(np.clip(probability, 0.02, 0.95))


def create_training_data(
    n_samples: int = N_SAMPLES,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Create a deterministic synthetic recovery dataset.

    Target:
        1 = recovered
        0 = not recovered

    The target is generated independently from the ML model.
    """

    rng = np.random.default_rng(seed)

    rows: list[dict] = []

    for _ in range(n_samples):
        amount = float(
            np.round(
                rng.uniform(100, 5000),
                2,
            )
        )

        previous_attempts = int(
            rng.choice(
                [0, 1, 2, 3],
                p=[0.50, 0.28, 0.15, 0.07],
            )
        )

        failed_attempts = int(
            min(
                3,
                max(
                    previous_attempts,
                    previous_attempts
                    + int(rng.choice([-1, 0, 1], p=[0.10, 0.75, 0.15])),
                ),
            )
        )

        payment_method = str(
            rng.choice(
                PAYMENT_METHODS,
                p=[0.50, 0.35, 0.15],
            )
        )

        failure_reason = str(
            rng.choice(
                FAILURE_REASONS,
                p=[
                    0.22,  # insufficient funds
                    0.12,  # bank declined
                    0.18,  # timeout
                    0.15,  # network error
                    0.10,  # expired card
                    0.08,  # invalid card
                    0.08,  # fraud
                    0.07,  # blocked
                ],
            )
        )

        probability = _recovery_probability(
            amount=amount,
            previous_attempts=previous_attempts,
            failed_attempts=failed_attempts,
            payment_method=payment_method,
            failure_reason=failure_reason,
        )

        # Independent synthetic outcome.
        recovered = int(
            rng.random() < probability
        )

        payment = {
            "amount": amount,
            "previous_attempts": previous_attempts,
            "failed_attempts": failed_attempts,
            "payment_method": payment_method,
            "failure_reason": failure_reason,
        }

        features = build_features(payment)

        rows.append(
            {
                "amount": features[0],
                "previous_attempts": features[1],
                "failed_attempts": features[2],
                "amount_is_high": features[3],
                "is_upi": features[4],
                "is_card": features[5],
                "is_net_banking": features[6],
                "failure_reason_code": features[7],
                "recovered": recovered,
            }
        )

    return pd.DataFrame(rows)


def build_model() -> Pipeline:
    """Build the recovery probability model."""

    return Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=RANDOM_SEED,
                ),
            ),
        ]
    )


def train_model() -> None:
    """Train, evaluate, and save the recovery model."""

    df = create_training_data()

    X = df[FEATURE_COLUMNS]
    y = df["recovered"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_SEED,
        stratify=y,
    )

    model = build_model()

    model.fit(
        X_train,
        y_train,
    )

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    pr_auc = average_precision_score(
        y_test,
        probabilities,
    )

    brier = brier_score_loss(
        y_test,
        probabilities,
    )

    print("=" * 60)
    print("RecoverAI Recovery Model")
    print("=" * 60)

    print(f"Total samples: {len(df)}")
    print(f"Training samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")

    print(
        f"\nRecovery rate in dataset: "
        f"{y.mean():.2%}"
    )

    print(f"\nAccuracy: {accuracy:.3f}")
    print(f"ROC-AUC: {roc_auc:.3f}")
    print(f"PR-AUC: {pr_auc:.3f}")
    print(f"Brier score: {brier:.3f}")

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )

    print("Confusion matrix:")
    print(
        confusion_matrix(
            y_test,
            predictions,
        )
    )

    # Simple calibration summary.
    fraction_of_positives, mean_predicted_value = calibration_curve(
        y_test,
        probabilities,
        n_bins=5,
        strategy="quantile",
    )

    print("\nCalibration:")
    for predicted, actual in zip(
        mean_predicted_value,
        fraction_of_positives,
    ):
        print(
            f"  predicted={predicted:.3f} "
            f"actual={actual:.3f}"
        )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        model,
        MODEL_PATH,
    )

    print("\nModel saved to:")
    print(MODEL_PATH)

    print("=" * 60)


if __name__ == "__main__":
    train_model()