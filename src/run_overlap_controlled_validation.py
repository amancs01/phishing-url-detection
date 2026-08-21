"""Evaluate overlap-controlled external subsets with the frozen model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
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

from src.audit_cross_dataset_overlap import (
    add_overlap_keys,
    legitphish_rows,
    normalized_url_key,
    phiusiil_rows,
    url_phish_rows,
)
from src.config import (
    EXTERNAL_VALIDATION_METRICS_FILE,
    EXTERNAL_VALIDATION_PREDICTIONS_FILE,
    LEGITPHISH_EXTERNAL_MATRIX_FILE,
    LEGITPHISH_VALIDATION_METRICS_FILE,
    OPTIMIZED_MODEL_FILE,
    OVERLAP_CONTROLLED_VALIDATION_FILE,
    URL_PHISH_EXTERNAL_MATRIX_FILE,
)
from src.feature_definitions import FEATURE_NAMES
from src.prepare_external_data import TARGET_COLUMN
from src.predict import LEGITIMATE_LABEL, PHISHING_LABEL, validate_model


OVERLAP_CONTROLLED_REPORT_FILE = Path("research/overlap_controlled_validation.md")


def phishing_probability_from_model(model: Any, probabilities) -> pd.Series:
    """Return class-0 phishing probabilities by inspecting model.classes_."""

    classes = list(model.classes_)

    if PHISHING_LABEL not in classes:
        raise ValueError(f"Model classes do not contain phishing label {PHISHING_LABEL}.")

    return pd.Series(probabilities[:, classes.index(PHISHING_LABEL)])


def safe_binary_metrics(
    y_true: pd.Series,
    y_pred: pd.Series,
    phishing_probability: pd.Series,
) -> dict[str, Any]:
    """Calculate subset metrics and mark undefined two-class metrics honestly."""

    y_true = y_true.astype(int)
    y_pred = y_pred.astype(int)
    labels_present = set(y_true.unique().tolist())
    has_phishing = PHISHING_LABEL in labels_present
    has_legitimate = LEGITIMATE_LABEL in labels_present
    has_both_classes = has_phishing and has_legitimate
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    true_phishing = matrix[0][0] + matrix[0][1]
    true_legitimate = matrix[1][0] + matrix[1][1]
    y_true_binary = (y_true == PHISHING_LABEL).astype(int)

    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_true, y_pred)) if len(y_true) else None,
        "phishing_precision": float(
            precision_score(y_true, y_pred, pos_label=PHISHING_LABEL, zero_division=0)
        )
        if len(y_true)
        else None,
        "phishing_recall": float(recall_score(y_true, y_pred, pos_label=PHISHING_LABEL))
        if true_phishing
        else None,
        "phishing_f1": float(f1_score(y_true, y_pred, pos_label=PHISHING_LABEL))
        if true_phishing
        else None,
        "specificity": matrix[1][1] / true_legitimate if true_legitimate else None,
        "balanced_accuracy": (
            float(balanced_accuracy_score(y_true, y_pred)) if has_both_classes else None
        ),
        "roc_auc": (
            float(roc_auc_score(y_true_binary, phishing_probability))
            if has_both_classes
            else None
        ),
        "pr_auc": (
            float(average_precision_score(y_true_binary, phishing_probability))
            if has_both_classes
            else None
        ),
        "two_class_metrics_defined": bool(has_both_classes),
        "undefined_metric_reason": None
        if has_both_classes
        else "Subset contains only one observed class.",
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
    return metrics


def subset_class_counts(y_true: pd.Series) -> dict[str, int]:
    """Return stable project class counts."""

    counts = y_true.astype(int).value_counts().to_dict()
    return {
        "phishing_label_0": int(counts.get(PHISHING_LABEL, 0)),
        "legitimate_label_1": int(counts.get(LEGITIMATE_LABEL, 0)),
    }


def prediction_table_for_matrix(model: Any, matrix: pd.DataFrame) -> pd.DataFrame:
    """Predict a matrix without changing the frozen model."""

    x = matrix[FEATURE_NAMES]
    probabilities = model.predict_proba(x)
    return pd.DataFrame(
        {
            "actual_label": matrix[TARGET_COLUMN].astype(int).to_numpy(),
            "predicted_label": model.predict(x).astype(int),
            "phishing_probability": phishing_probability_from_model(
                model,
                probabilities,
            ).to_numpy(),
        }
    )


def evaluate_prediction_subset(
    name: str,
    rows: pd.DataFrame,
    mask: pd.Series,
) -> dict[str, Any]:
    """Evaluate one anonymous prediction subset."""

    subset = rows[mask.to_numpy()].copy()
    y_true = subset["actual_label"].astype(int)
    return {
        "subset": name,
        "rows": int(len(subset)),
        "class_counts": subset_class_counts(y_true),
        "metrics": safe_binary_metrics(
            y_true,
            subset["predicted_label"].astype(int),
            subset["phishing_probability"].astype(float),
        ),
    }


def load_primary_metric_payload(path: Path) -> dict[str, Any]:
    """Load previously committed primary external metrics."""

    with path.open(encoding="utf-8") as file:
        return json.load(file)


def legitphish_overlap_controlled(model: Any, phiusiil: pd.DataFrame) -> dict[str, Any]:
    """Evaluate LegitPhish full and overlap-controlled subsets."""

    legitphish = add_overlap_keys(legitphish_rows())
    matrix = pd.read_csv(LEGITPHISH_EXTERNAL_MATRIX_FILE)
    predictions = prediction_table_for_matrix(model, matrix)
    phi_exact = set(phiusiil["exact_key"])
    phi_normalized = set(phiusiil["normalized_key"])
    phi_domains = set(phiusiil["registrable_domain"])
    keyed_predictions = pd.concat([legitphish.reset_index(drop=True), predictions], axis=1)

    subsets = [
        ("full_primary_reference", pd.Series(True, index=keyed_predictions.index)),
        (
            "remove_exact_urls_present_in_phiusiil",
            ~keyed_predictions["exact_key"].isin(phi_exact),
        ),
        (
            "remove_normalized_urls_present_in_phiusiil",
            ~keyed_predictions["normalized_key"].isin(phi_normalized),
        ),
        (
            "unseen_registrable_domain",
            ~keyed_predictions["registrable_domain"].isin(phi_domains),
        ),
    ]
    return {
        "dataset": "LegitPhish",
        "primary_result_preserved": True,
        "primary_metrics_reference": load_primary_metric_payload(
            LEGITPHISH_VALIDATION_METRICS_FILE
        )["metrics"],
        "subsets": [
            evaluate_prediction_subset(name, keyed_predictions, mask)
            for name, mask in subsets
        ],
    }


def url_phish_overlap_controlled(phiusiil: pd.DataFrame) -> dict[str, Any]:
    """Evaluate URL-Phish exact-overlap-controlled sensitivity."""

    url_phish = add_overlap_keys(url_phish_rows())
    matrix = pd.read_csv(URL_PHISH_EXTERNAL_MATRIX_FILE)
    predictions = pd.read_csv(EXTERNAL_VALIDATION_PREDICTIONS_FILE)
    if len(url_phish) != len(matrix) or len(url_phish) != len(predictions):
        raise ValueError("URL-Phish raw, matrix, and prediction rows are not aligned.")
    keyed_predictions = pd.concat(
        [
            url_phish.reset_index(drop=True),
            predictions[["actual_label", "predicted_label", "phishing_probability"]],
        ],
        axis=1,
    )
    phi_exact = set(phiusiil["exact_key"])
    subsets = [
        ("full_primary_reference", pd.Series(True, index=keyed_predictions.index)),
        (
            "remove_exact_urls_present_in_phiusiil",
            ~keyed_predictions["exact_key"].isin(phi_exact),
        ),
    ]
    return {
        "dataset": "URL-Phish",
        "primary_result_preserved": True,
        "primary_metrics_reference": load_primary_metric_payload(
            EXTERNAL_VALIDATION_METRICS_FILE
        )["metrics"],
        "subsets": [
            evaluate_prediction_subset(name, keyed_predictions, mask)
            for name, mask in subsets
        ],
    }


def metric_value(metrics: dict[str, Any], key: str) -> str:
    """Format a metric value for markdown."""

    value = metrics[key]
    return "undefined" if value is None else f"{value:.6f}"


def write_overlap_controlled_report(payload: dict[str, Any]) -> None:
    """Write overlap-controlled sensitivity report."""

    lines = [
        "# Overlap-Controlled External Validation",
        "",
        "## Scope",
        "",
        "This sensitivity analysis keeps the frozen PhiUSIIL Tier E Decision Tree fixed. It does not retrain, retune, recalibrate, change thresholds, or replace the primary external results.",
        "",
        "## Subset Metrics",
        "",
        "| Dataset | Subset | Rows | Phishing | Legitimate | Accuracy | Precision | Recall | F1 | Specificity | Balanced accuracy | ROC-AUC | PR-AUC |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for dataset in payload["datasets"]:
        for subset in dataset["subsets"]:
            metrics = subset["metrics"]
            counts = subset["class_counts"]
            lines.append(
                f"| {dataset['dataset']} | {subset['subset']} | {subset['rows']:,} | "
                f"{counts['phishing_label_0']:,} | {counts['legitimate_label_1']:,} | "
                f"{metric_value(metrics, 'accuracy')} | "
                f"{metric_value(metrics, 'phishing_precision')} | "
                f"{metric_value(metrics, 'phishing_recall')} | "
                f"{metric_value(metrics, 'phishing_f1')} | "
                f"{metric_value(metrics, 'specificity')} | "
                f"{metric_value(metrics, 'balanced_accuracy')} | "
                f"{metric_value(metrics, 'roc_auc')} | "
                f"{metric_value(metrics, 'pr_auc')} |"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The full rows remain historical primary references. Overlap-controlled subsets test whether external performance persists after removing direct URL overlap with PhiUSIIL.",
            "",
            "For any subset containing only one observed class, two-class metrics are marked undefined instead of assigning a numeric fallback.",
            "",
            "## Safety Statement",
            "",
            payload["safety_statement"],
        ]
    )
    OVERLAP_CONTROLLED_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OVERLAP_CONTROLLED_REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_overlap_controlled_validation() -> dict[str, Any]:
    """Run overlap-controlled external sensitivity analyses."""

    phiusiil = add_overlap_keys(phiusiil_rows())
    model = joblib.load(OPTIMIZED_MODEL_FILE)
    validate_model(model)
    payload = {
        "analysis_type": "OVERLAP-CONTROLLED SENSITIVITY ANALYSIS",
        "model_file": str(OPTIMIZED_MODEL_FILE),
        "model_changed": False,
        "external_training_performed": False,
        "external_tuning_performed": False,
        "threshold_changed": False,
        "feature_names": FEATURE_NAMES,
        "metrics_policy": {
            "single_class_roc_auc": "undefined",
            "single_class_balanced_accuracy": "undefined",
            "single_class_pr_auc": "undefined",
        },
        "datasets": [
            legitphish_overlap_controlled(model, phiusiil),
            url_phish_overlap_controlled(phiusiil),
        ],
        "raw_values_committed": False,
        "safety_statement": (
            "All subset keys were computed from local strings with local parsing "
            "only; no URL was opened, requested, resolved, scraped, or contacted."
        ),
    }
    OVERLAP_CONTROLLED_VALIDATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OVERLAP_CONTROLLED_VALIDATION_FILE.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")
    write_overlap_controlled_report(payload)
    return payload


def main() -> None:
    """Run overlap-controlled validation."""

    payload = run_overlap_controlled_validation()
    print(f"Saved: {OVERLAP_CONTROLLED_VALIDATION_FILE}")
    print(f"Saved: {OVERLAP_CONTROLLED_REPORT_FILE}")
    for dataset in payload["datasets"]:
        print(dataset["dataset"])
        for subset in dataset["subsets"]:
            print(
                {
                    "subset": subset["subset"],
                    "rows": subset["rows"],
                    "class_counts": subset["class_counts"],
                    "phishing_f1": subset["metrics"]["phishing_f1"],
                    "roc_auc": subset["metrics"]["roc_auc"],
                }
            )


if __name__ == "__main__":
    main()
