"""Evaluate the frozen PhiUSIIL model on LegitPhish without retraining."""

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
    EXTERNAL_VALIDATION_METRICS_FILE,
    LEGITPHISH_CONFUSION_MATRIX_FIGURE,
    LEGITPHISH_DOI,
    LEGITPHISH_EXTERNAL_MATRIX_FILE,
    LEGITPHISH_RAW_FILE,
    LEGITPHISH_SENSITIVITY_METRICS_FILE,
    LEGITPHISH_VALIDATION_METRICS_FILE,
    LEGITPHISH_VERSION,
    MODEL_METADATA_FILE,
    OPTIMIZED_MODEL_FILE,
    RAW_DATA_FILE,
    RESULTS_DIRECTORY,
    THREE_DATASET_METRIC_COMPARISON_FIGURE,
)
from src.domain_utils import extract_registrable_domain
from src.feature_definitions import FEATURE_NAMES
from src.prepare_external_data import TARGET_COLUMN
from src.prepare_legitphish_data import (
    LEGITPHISH_TARGET_COLUMN,
    LEGITPHISH_URL_COLUMN,
    analysis_rows,
    conflicting_duplicate_urls,
    validate_legitphish_feature_matrix,
)
from src.predict import LEGITIMATE_LABEL, PHISHING_LABEL, validate_model
from src.run_external_validation import FIXED_TREE_PARAMS, phishing_probability_from_proba


PHIUSIIL_URL_COLUMN = "URL"
DOMAIN_DISJOINT_PERFORMANCE_FILE = RESULTS_DIRECTORY / "domain_disjoint_performance.json"


def load_legitphish_matrix(matrix_file=LEGITPHISH_EXTERNAL_MATRIX_FILE) -> pd.DataFrame:
    """Load the ignored LegitPhish Tier E matrix."""

    matrix = pd.read_csv(matrix_file)
    validate_legitphish_feature_matrix(matrix)
    return matrix


def load_selected_model(model_file=OPTIMIZED_MODEL_FILE) -> Any:
    """Load the same frozen PhiUSIIL Tier E model used for URL-Phish."""

    return joblib.load(model_file)


def load_model_metadata() -> dict[str, Any]:
    """Load packaged model metadata for feature-contract validation."""

    with MODEL_METADATA_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def validate_legitphish_model(model: Any, metadata: dict[str, Any]) -> None:
    """Validate frozen model artifact, feature order, and class labels."""

    validate_model(model)

    if metadata["feature_names"] != FEATURE_NAMES:
        raise ValueError("Model metadata feature order does not match FEATURE_NAMES.")

    if getattr(model, "n_features_in_", len(FEATURE_NAMES)) != len(FEATURE_NAMES):
        raise ValueError("Frozen model feature count does not match FEATURE_NAMES.")

    params = model.get_params()
    mismatches = {
        key: (params.get(key), expected)
        for key, expected in FIXED_TREE_PARAMS.items()
        if params.get(key) != expected
    }

    if mismatches:
        raise ValueError(f"Frozen model hyperparameters differ: {mismatches}")


def calculate_metrics(
    y_true: pd.Series,
    y_pred: pd.Series,
    phishing_probability: pd.Series,
) -> dict[str, Any]:
    """Calculate metrics with phishing label 0 as positive."""

    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    true_phishing = matrix[0][0] + matrix[0][1]
    true_legitimate = matrix[1][0] + matrix[1][1]
    specificity = matrix[1][1] / true_legitimate if true_legitimate else 0.0
    false_positive_rate = matrix[1][0] / true_legitimate if true_legitimate else 0.0
    false_negative_rate = matrix[0][1] / true_phishing if true_phishing else 0.0
    y_true_binary = (y_true == PHISHING_LABEL).astype(int)

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
        "specificity": float(specificity),
        "false_positive_rate": float(false_positive_rate),
        "false_negative_rate": float(false_negative_rate),
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


def predict_matrix(model: Any, matrix: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Predict LegitPhish rows without modifying the frozen model."""

    x = matrix[FEATURE_NAMES]
    y_true = matrix[TARGET_COLUMN].astype(int)
    y_pred = pd.Series(model.predict(x).astype(int), index=matrix.index)
    phishing_probability = phishing_probability_from_proba(model, model.predict_proba(x))
    predictions = pd.DataFrame(
        {
            "row_index": matrix.index.astype(int),
            "actual_label": y_true.to_numpy(),
            "predicted_label": y_pred.to_numpy(),
            "phishing_probability": phishing_probability.to_numpy(),
        }
    )
    return predictions, calculate_metrics(y_true, y_pred, phishing_probability)


def metrics_from_prediction_rows(rows: pd.DataFrame) -> dict[str, Any]:
    """Calculate metrics from anonymous prediction rows."""

    return calculate_metrics(
        rows["actual_label"].astype(int),
        rows["predicted_label"].astype(int),
        rows["phishing_probability"].astype(float),
    )


def deduplicated_sensitivity(raw_usable: pd.DataFrame, predictions: pd.DataFrame) -> dict[str, Any]:
    """Evaluate exact-URL deduplicated LegitPhish sensitivity."""

    conflicts = conflicting_duplicate_urls(raw_usable)
    non_conflicting = raw_usable[~raw_usable[LEGITPHISH_URL_COLUMN].isin(conflicts)]
    keep_mask = ~non_conflicting.duplicated(subset=[LEGITPHISH_URL_COLUMN], keep="first")
    kept_indices = non_conflicting[keep_mask].index.astype(int).tolist()
    rows = predictions.loc[kept_indices].copy()
    class_counts = rows["actual_label"].value_counts().to_dict()
    return {
        "raw_analysis_rows": int(len(raw_usable)),
        "duplicate_rows": int(raw_usable.duplicated().sum()),
        "duplicate_url_rows": int(raw_usable[LEGITPHISH_URL_COLUMN].duplicated().sum()),
        "conflicting_duplicate_url_values": int(len(conflicts)),
        "rows_with_conflicting_duplicate_url": int(
            raw_usable[LEGITPHISH_URL_COLUMN].isin(conflicts).sum()
        ),
        "deduplicated_rows": int(len(rows)),
        "class_counts": {
            "phishing_label_0": int(class_counts.get(0, 0)),
            "legitimate_label_1": int(class_counts.get(1, 0)),
        },
        "metrics": metrics_from_prediction_rows(rows),
    }


def phiusiil_domain_set() -> set[str]:
    """Extract PhiUSIIL registrable domains offline."""

    raw = pd.read_csv(RAW_DATA_FILE, usecols=[PHIUSIIL_URL_COLUMN])
    return set(raw[PHIUSIIL_URL_COLUMN].astype(str).map(extract_registrable_domain))


def domain_overlap_sensitivity(raw_usable: pd.DataFrame, predictions: pd.DataFrame) -> dict[str, Any]:
    """Evaluate LegitPhish seen/unseen registrable-domain segments."""

    domains = raw_usable[LEGITPHISH_URL_COLUMN].astype(str).map(extract_registrable_domain)
    internal_domains = phiusiil_domain_set()
    seen_mask = domains.isin(internal_domains)
    unseen_mask = ~seen_mask
    domain_count = int(domains.nunique())
    seen_domain_count = int(domains[seen_mask].nunique())
    unseen_domain_count = int(domains[unseen_mask].nunique())

    def segment(mask: pd.Series) -> dict[str, Any]:
        rows = predictions[mask.to_numpy()].copy()
        class_counts = rows["actual_label"].value_counts().to_dict()
        return {
            "row_count": int(len(rows)),
            "class_counts": {
                "phishing_label_0": int(class_counts.get(0, 0)),
                "legitimate_label_1": int(class_counts.get(1, 0)),
            },
            "metrics": metrics_from_prediction_rows(rows),
        }

    return {
        "legitphish_registrable_domains": domain_count,
        "domains_also_present_in_phiusiil": seen_domain_count,
        "domains_unseen_in_phiusiil": unseen_domain_count,
        "overlap_percentage": seen_domain_count / domain_count * 100 if domain_count else 0.0,
        "seen_domain_rows": segment(seen_mask),
        "unseen_domain_rows": segment(unseen_mask),
    }


def save_confusion_matrix_figure(metrics: dict[str, Any]) -> None:
    """Save LegitPhish confusion matrix figure."""

    matrix = metrics["confusion_matrix"]
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    image = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks([0, 1], labels=["Pred phishing", "Pred legitimate"])
    ax.set_yticks([0, 1], labels=["Actual phishing", "Actual legitimate"])
    ax.set_title("LegitPhish external confusion matrix")

    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            ax.text(column_index, row_index, f"{value:,}", ha="center", va="center")

    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    LEGITPHISH_CONFUSION_MATRIX_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(LEGITPHISH_CONFUSION_MATRIX_FIGURE, dpi=160)
    plt.close(fig)


def load_phiusiil_domain_e_metrics() -> dict[str, Any]:
    """Load PhiUSIIL domain-disjoint Tier E metrics."""

    with DOMAIN_DISJOINT_PERFORMANCE_FILE.open(encoding="utf-8") as file:
        results = json.load(file)["results"]

    return next(result for result in results if result["tier"] == "E")


def load_url_phish_metrics() -> dict[str, Any]:
    """Load URL-Phish external metrics."""

    with EXTERNAL_VALIDATION_METRICS_FILE.open(encoding="utf-8") as file:
        return json.load(file)["metrics"]


def save_three_dataset_metric_figure(legitphish_metrics: dict[str, Any]) -> None:
    """Save precision, recall, F1, ROC-AUC, and balanced accuracy comparison."""

    phiusiil = load_phiusiil_domain_e_metrics()
    url_phish = load_url_phish_metrics()
    comparison = pd.DataFrame(
        [
            {
                "dataset": "PhiUSIIL domain-disjoint",
                "phishing_precision": phiusiil["phishing_precision"],
                "phishing_recall": phiusiil["phishing_recall"],
                "phishing_f1": phiusiil["phishing_f1"],
                "roc_auc": phiusiil["roc_auc"],
                "balanced_accuracy": phiusiil["test_accuracy"],
            },
            {
                "dataset": "URL-Phish",
                "phishing_precision": url_phish["phishing_precision"],
                "phishing_recall": url_phish["phishing_recall"],
                "phishing_f1": url_phish["phishing_f1"],
                "roc_auc": url_phish["roc_auc"],
                "balanced_accuracy": url_phish["balanced_accuracy"],
            },
            {
                "dataset": "LegitPhish",
                "phishing_precision": legitphish_metrics["phishing_precision"],
                "phishing_recall": legitphish_metrics["phishing_recall"],
                "phishing_f1": legitphish_metrics["phishing_f1"],
                "roc_auc": legitphish_metrics["roc_auc"],
                "balanced_accuracy": legitphish_metrics["balanced_accuracy"],
            },
        ]
    )
    ax = comparison.set_index("dataset").plot(kind="bar", figsize=(10, 5), width=0.74)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Metric value")
    ax.set_xlabel("")
    ax.set_title("Three-dataset fixed Tier E comparison")
    ax.legend(title="Metric", ncol=2)
    plt.xticks(rotation=12, ha="right")
    plt.tight_layout()
    THREE_DATASET_METRIC_COMPARISON_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(THREE_DATASET_METRIC_COMPARISON_FIGURE, dpi=160)
    plt.close()


def run_legitphish_validation() -> tuple[dict[str, Any], dict[str, Any]]:
    """Run full and sensitivity LegitPhish validation."""

    matrix = load_legitphish_matrix()
    raw_usable = analysis_rows(pd.read_csv(LEGITPHISH_RAW_FILE)).reset_index(drop=True)
    model = load_selected_model()
    metadata = load_model_metadata()
    validate_legitphish_model(model, metadata)
    predictions, metrics = predict_matrix(model, matrix)
    save_confusion_matrix_figure(metrics)
    save_three_dataset_metric_figure(metrics)
    validation_payload = {
        "dataset_name": "LegitPhish Dataset",
        "dataset_version": LEGITPHISH_VERSION,
        "doi": LEGITPHISH_DOI,
        "external_rows": int(len(matrix)),
        "model_file": str(OPTIMIZED_MODEL_FILE),
        "same_frozen_model_as_url_phish": True,
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
        "safety_statement": (
            "LegitPhish evaluation used the ignored local Tier E feature matrix; "
            "no dataset URL was opened, requested, resolved, or contacted."
        ),
    }
    sensitivity_payload = {
        "analysis_type": "SECONDARY SENSITIVITY ANALYSIS",
        "primary_legitphish_result_changed": False,
        "deduplicated_exact_url_sensitivity": deduplicated_sensitivity(
            raw_usable,
            predictions,
        ),
        "cross_dataset_registrable_domain_overlap": domain_overlap_sensitivity(
            raw_usable,
            predictions,
        ),
        "safety_statement": (
            "Deduplication and domain overlap used local strings and offline "
            "registrable-domain parsing only; no URL was contacted."
        ),
    }
    LEGITPHISH_VALIDATION_METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LEGITPHISH_VALIDATION_METRICS_FILE.open("w", encoding="utf-8") as file:
        json.dump(validation_payload, file, indent=2)
        file.write("\n")
    with LEGITPHISH_SENSITIVITY_METRICS_FILE.open("w", encoding="utf-8") as file:
        json.dump(sensitivity_payload, file, indent=2)
        file.write("\n")
    return validation_payload, sensitivity_payload


def main() -> None:
    """Run LegitPhish external validation."""

    validation, sensitivity = run_legitphish_validation()
    metrics = validation["metrics"]
    print(f"Saved: {LEGITPHISH_VALIDATION_METRICS_FILE}")
    print(f"Saved: {LEGITPHISH_SENSITIVITY_METRICS_FILE}")
    print(f"Saved: {LEGITPHISH_CONFUSION_MATRIX_FIGURE}")
    print(f"Saved: {THREE_DATASET_METRIC_COMPARISON_FIGURE}")
    print(
        {
            "accuracy": metrics["accuracy"],
            "phishing_precision": metrics["phishing_precision"],
            "phishing_recall": metrics["phishing_recall"],
            "phishing_f1": metrics["phishing_f1"],
            "roc_auc": metrics["roc_auc"],
            "pr_auc": metrics["pr_auc"],
            "balanced_accuracy": metrics["balanced_accuracy"],
            "specificity": metrics["specificity"],
            "confusion_matrix": metrics["confusion_matrix"],
        }
    )
    print(sensitivity["deduplicated_exact_url_sensitivity"]["metrics"])


if __name__ == "__main__":
    main()
