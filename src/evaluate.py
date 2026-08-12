"""Reusable binary classification evaluation helpers.

PhiUSIIL uses label 0 for phishing and label 1 for legitimate. For security
interpretation, phishing is the important positive class, so these helpers use
`pos_label=0` instead of relying on scikit-learn's default positive label.
"""

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


PHISHING_LABEL = 0
LEGITIMATE_LABEL = 1
LABEL_NAMES = {
    PHISHING_LABEL: "Phishing",
    LEGITIMATE_LABEL: "Legitimate",
}


def phishing_probabilities(model: Any, features) -> np.ndarray | None:
    """Return phishing-class probabilities when the model supports them."""

    if not hasattr(model, "predict_proba"):
        return None

    probabilities = model.predict_proba(features)
    class_labels = list(model.classes_)

    if PHISHING_LABEL not in class_labels:
        return None

    phishing_index = class_labels.index(PHISHING_LABEL)
    return probabilities[:, phishing_index]


def calculate_binary_metrics(
    y_true,
    y_pred,
    phishing_scores: np.ndarray | None = None,
) -> dict:
    """Calculate binary metrics with phishing as the positive class."""

    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_phishing": float(
            precision_score(y_true, y_pred, pos_label=PHISHING_LABEL, zero_division=0)
        ),
        "recall_phishing": float(
            recall_score(y_true, y_pred, pos_label=PHISHING_LABEL, zero_division=0)
        ),
        "f1_phishing": float(
            f1_score(y_true, y_pred, pos_label=PHISHING_LABEL, zero_division=0)
        ),
        "classification_report": classification_report(
            y_true,
            y_pred,
            labels=[PHISHING_LABEL, LEGITIMATE_LABEL],
            target_names=["Phishing", "Legitimate"],
            zero_division=0,
            output_dict=True,
        ),
    }

    if phishing_scores is not None:
        phishing_true = np.asarray(y_true) == PHISHING_LABEL
        metrics["roc_auc_phishing"] = float(roc_auc_score(phishing_true, phishing_scores))
    else:
        metrics["roc_auc_phishing"] = None

    return metrics


def evaluate_model(model: Any, features, target) -> dict:
    """Evaluate a fitted model using phishing as the positive class."""

    predictions = model.predict(features)
    probabilities = phishing_probabilities(model, features)

    return calculate_binary_metrics(
        y_true=target,
        y_pred=predictions,
        phishing_scores=probabilities,
    )
