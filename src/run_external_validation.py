"""Evaluate the packaged PhiUSIIL model on URL-Phish without retraining."""

from __future__ import annotations

import json
from typing import Any

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.config import (
    EXTERNAL_CONFUSION_MATRIX_FIGURE,
    EXTERNAL_VALIDATION_METRICS_FILE,
    EXTERNAL_VALIDATION_PREDICTIONS_FILE,
    INTERNAL_VS_EXTERNAL_METRICS_FIGURE,
    MODEL_METADATA_FILE,
    OPTIMIZED_MODEL_FILE,
    URL_PHISH_DOI,
    URL_PHISH_EXTERNAL_MATRIX_FILE,
    URL_PHISH_VERSION,
)
from src.feature_definitions import FEATURE_NAMES
from src.prepare_external_data import TARGET_COLUMN, validate_external_feature_matrix
from src.predict import PHISHING_LABEL, validate_model


DOMAIN_DISJOINT_PERFORMANCE_FILE = "results/domain_disjoint_performance.json"
FIXED_TREE_PARAMS = {
    "criterion": "entropy",
    "max_depth": 10,
    "min_samples_leaf": 1,
    "min_samples_split": 2,
    "ccp_alpha": 0.0,
    "random_state": 42,
}


def load_external_matrix(matrix_file=URL_PHISH_EXTERNAL_MATRIX_FILE) -> pd.DataFrame:
    """Load the ignored external Tier E matrix created from raw URL text."""

    matrix = pd.read_csv(matrix_file)
    validate_external_feature_matrix(matrix)
    return matrix


def load_selected_model(model_file=OPTIMIZED_MODEL_FILE) -> Any:
    """Load the already-selected PhiUSIIL Tier E model."""

    return joblib.load(model_file)


def load_model_metadata() -> dict[str, Any]:
    """Load packaged model metadata used for feature-contract checks."""

    with MODEL_METADATA_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def validate_external_model(model: Any, metadata: dict[str, Any]) -> None:
    """Validate that the model matches the fixed Tier E external contract."""

    validate_model(model)

    if metadata["feature_names"] != FEATURE_NAMES:
        raise ValueError("Packaged model metadata feature names do not match FEATURE_NAMES.")

    if len(FEATURE_NAMES) != getattr(model, "n_features_in_", len(FEATURE_NAMES)):
        raise ValueError("Packaged model feature count does not match FEATURE_NAMES.")

    model_params = model.get_params()
    mismatches = {
        key: (model_params.get(key), expected_value)
        for key, expected_value in FIXED_TREE_PARAMS.items()
        if model_params.get(key) != expected_value
    }

    if mismatches:
        raise ValueError(f"Packaged model hyperparameters differ: {mismatches}")


def phishing_probability_from_proba(model: Any, probabilities) -> pd.Series:
    """Return class-0 phishing probabilities by inspecting model.classes_."""

    classes = list(model.classes_)

    if PHISHING_LABEL not in classes:
        raise ValueError(f"Model classes do not contain phishing label {PHISHING_LABEL}.")

    phishing_index = classes.index(PHISHING_LABEL)
    return pd.Series(probabilities[:, phishing_index])


def calculate_external_metrics(
    y_true: pd.Series,
    y_pred: pd.Series,
    phishing_probability: pd.Series,
) -> dict[str, Any]:
    """Calculate external metrics with phishing label 0 as the positive class."""

    y_true_binary = (y_true == PHISHING_LABEL).astype(int)
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "phishing_precision": float(
            precision_score(y_true, y_pred, pos_label=PHISHING_LABEL, zero_division=0)
        ),
        "phishing_recall": float(recall_score(y_true, y_pred, pos_label=PHISHING_LABEL)),
        "phishing_f1": float(f1_score(y_true, y_pred, pos_label=PHISHING_LABEL)),
        "roc_auc": float(roc_auc_score(y_true_binary, phishing_probability)),
        "pr_auc": float(average_precision_score(y_true_binary, phishing_probability)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "confusion_matrix": matrix,
        "true_phishing_predicted_phishing": int(matrix[0][0]),
        "true_phishing_predicted_legitimate": int(matrix[0][1]),
        "true_legitimate_predicted_phishing": int(matrix[1][0]),
        "true_legitimate_predicted_legitimate": int(matrix[1][1]),
        "confusion_matrix_order": (
            "[[actual phishing -> predicted phishing, actual phishing -> "
            "predicted legitimate], [actual legitimate -> predicted phishing, "
            "actual legitimate -> predicted legitimate]]"
        ),
    }


def predict_external_matrix(model: Any, matrix: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Predict all external rows without changing the selected model."""

    x_external = matrix[FEATURE_NAMES]
    y_true = matrix[TARGET_COLUMN].astype(int)
    y_pred = pd.Series(model.predict(x_external).astype(int))
    probabilities = model.predict_proba(x_external)
    phishing_probability = phishing_probability_from_proba(model, probabilities)

    predictions = pd.DataFrame(
        {
            "row_index": range(len(matrix)),
            "actual_label": y_true.to_numpy(),
            "predicted_label": y_pred.to_numpy(),
            "phishing_probability": phishing_probability.to_numpy(),
        }
    )
    metrics = calculate_external_metrics(y_true, y_pred, phishing_probability)
    return predictions, metrics


def load_domain_disjoint_tier_e_metrics() -> dict[str, Any]:
    """Load prior PhiUSIIL domain-disjoint Tier E metrics for comparison."""

    with open(DOMAIN_DISJOINT_PERFORMANCE_FILE, encoding="utf-8") as file:
        results = json.load(file)["results"]

    return next(result for result in results if result["tier"] == "E")


def save_external_confusion_matrix(metrics: dict[str, Any]) -> None:
    """Save a compact external confusion-matrix heatmap."""

    EXTERNAL_CONFUSION_MATRIX_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    matrix = metrics["confusion_matrix"]
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    image = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks([0, 1], labels=["Pred phishing", "Pred legitimate"])
    ax.set_yticks([0, 1], labels=["Actual phishing", "Actual legitimate"])
    ax.set_title("URL-Phish external confusion matrix")

    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            ax.text(column_index, row_index, f"{value:,}", ha="center", va="center")

    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(EXTERNAL_CONFUSION_MATRIX_FIGURE, dpi=160)
    plt.close(fig)


def save_internal_vs_external_metrics(metrics: dict[str, Any]) -> None:
    """Save a PhiUSIIL domain-disjoint versus URL-Phish metric comparison."""

    internal = load_domain_disjoint_tier_e_metrics()
    comparison = pd.DataFrame(
        [
            {
                "dataset": "PhiUSIIL domain-disjoint",
                "phishing_recall": internal["phishing_recall"],
                "phishing_f1": internal["phishing_f1"],
                "roc_auc": internal["roc_auc"],
            },
            {
                "dataset": "URL-Phish external",
                "phishing_recall": metrics["phishing_recall"],
                "phishing_f1": metrics["phishing_f1"],
                "roc_auc": metrics["roc_auc"],
            },
        ]
    )
    ax = comparison.set_index("dataset").plot(kind="bar", figsize=(8, 5), width=0.72)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Metric value")
    ax.set_xlabel("")
    ax.set_title("Internal vs external Tier E metrics")
    ax.legend(title="Metric")
    plt.xticks(rotation=12, ha="right")
    plt.tight_layout()
    plt.savefig(INTERNAL_VS_EXTERNAL_METRICS_FIGURE, dpi=160)
    plt.close()


def run_external_validation() -> dict[str, Any]:
    """Run the first external validation using the selected PhiUSIIL model."""

    matrix = load_external_matrix()
    model = load_selected_model()
    metadata = load_model_metadata()
    validate_external_model(model, metadata)
    predictions, metrics = predict_external_matrix(model, matrix)

    save_external_confusion_matrix(metrics)
    save_internal_vs_external_metrics(metrics)
    EXTERNAL_VALIDATION_PREDICTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(EXTERNAL_VALIDATION_PREDICTIONS_FILE, index=False)

    payload = {
        "dataset_name": "URL-Phish: A Feature-Engineered Dataset for Phishing Detection",
        "dataset_version": URL_PHISH_VERSION,
        "doi": URL_PHISH_DOI,
        "external_rows": int(len(matrix)),
        "model_file": str(OPTIMIZED_MODEL_FILE),
        "model_metadata_file": str(MODEL_METADATA_FILE),
        "model_changed": False,
        "external_training_performed": False,
        "external_tuning_performed": False,
        "threshold_changed": False,
        "feature_names": FEATURE_NAMES,
        "fixed_tree_params": FIXED_TREE_PARAMS,
        "phishing_probability": (
            "Probability column selected by locating project phishing label 0 "
            "inside model.classes_."
        ),
        "metrics": metrics,
        "prediction_file_columns": [
            "row_index",
            "actual_label",
            "predicted_label",
            "phishing_probability",
        ],
        "safety_statement": (
            "External evaluation used the ignored local Tier E feature matrix; "
            "no dataset URL was opened, requested, resolved, or contacted."
        ),
    }

    with EXTERNAL_VALIDATION_METRICS_FILE.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")

    return payload


def main() -> None:
    """Run URL-Phish external validation."""

    payload = run_external_validation()
    metrics = payload["metrics"]
    print(f"Saved: {EXTERNAL_VALIDATION_METRICS_FILE}")
    print(f"Saved: {EXTERNAL_VALIDATION_PREDICTIONS_FILE}")
    print(
        {
            "accuracy": metrics["accuracy"],
            "phishing_precision": metrics["phishing_precision"],
            "phishing_recall": metrics["phishing_recall"],
            "phishing_f1": metrics["phishing_f1"],
            "roc_auc": metrics["roc_auc"],
            "pr_auc": metrics["pr_auc"],
            "missed_phishing": metrics["true_phishing_predicted_legitimate"],
        }
    )


if __name__ == "__main__":
    main()
