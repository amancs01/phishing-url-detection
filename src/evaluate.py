"""Reusable binary classification evaluation helpers.

PhiUSIIL uses label 0 for phishing and label 1 for legitimate. For security
interpretation, phishing is the important positive class, so these helpers use
`pos_label=0` instead of relying on scikit-learn's default positive label.
"""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
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
CONFUSION_MATRIX_LABELS = [PHISHING_LABEL, LEGITIMATE_LABEL]


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


def calculate_confusion_matrix(y_true, y_pred) -> dict:
    """Return confusion matrix values with phishing listed first.

    Matrix layout:
    - actual phishing, predicted phishing: phishing caught correctly
    - actual phishing, predicted legitimate: phishing missed as legitimate
    - actual legitimate, predicted phishing: legitimate URL flagged as phishing
    - actual legitimate, predicted legitimate: legitimate URL allowed correctly

    The most security-sensitive error is actual phishing predicted legitimate.
    """

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=CONFUSION_MATRIX_LABELS,
    )

    return {
        "labels": ["Phishing", "Legitimate"],
        "matrix": matrix.tolist(),
        "phishing_predicted_phishing": int(matrix[0, 0]),
        "phishing_predicted_legitimate": int(matrix[0, 1]),
        "legitimate_predicted_phishing": int(matrix[1, 0]),
        "legitimate_predicted_legitimate": int(matrix[1, 1]),
        "most_security_sensitive_error": "actual phishing predicted legitimate",
    }


def plot_confusion_matrix(y_true, y_pred, output_path) -> dict:
    """Save a readable confusion matrix plot and return its values."""

    matrix_details = calculate_confusion_matrix(y_true, y_pred)
    matrix = np.asarray(matrix_details["matrix"])
    labels = matrix_details["labels"]

    fig, ax = plt.subplots(figsize=(6, 5))
    image = ax.imshow(matrix, cmap="Blues")
    fig.colorbar(image, ax=ax)

    ax.set_title("Baseline validation confusion matrix")
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("Actual label")
    ax.set_xticks(range(len(labels)), labels)
    ax.set_yticks(range(len(labels)), labels)

    threshold = matrix.max() / 2
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            value = matrix[row_index, column_index]
            text_color = "white" if value > threshold else "black"
            ax.text(
                column_index,
                row_index,
                f"{value:,}",
                ha="center",
                va="center",
                color=text_color,
            )

    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return matrix_details
