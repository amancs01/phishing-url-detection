"""External prevalence sensitivity analysis without model retraining."""

from __future__ import annotations

import json
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.config import (
    EXTERNAL_BOOTSTRAP_CI_FILE,
    EXTERNAL_FULL_VS_BALANCED_FIGURE,
    EXTERNAL_SENSITIVITY_RESULTS_CSV,
    EXTERNAL_VALIDATION_PREDICTIONS_FILE,
)
from src.predict import PHISHING_LABEL, LEGITIMATE_LABEL
from src.run_external_validation import calculate_external_metrics


BALANCED_SAMPLE_SEEDS = [42, 43, 44, 45, 46]
BOOTSTRAP_SEED = 20260821
BOOTSTRAP_ITERATIONS = 1000
METRIC_COLUMNS = [
    "accuracy",
    "phishing_precision",
    "phishing_recall",
    "phishing_f1",
    "roc_auc",
    "pr_auc",
]


def load_external_predictions(
    prediction_file=EXTERNAL_VALIDATION_PREDICTIONS_FILE,
) -> pd.DataFrame:
    """Load anonymous external prediction rows."""

    predictions = pd.read_csv(prediction_file)
    expected_columns = [
        "row_index",
        "actual_label",
        "predicted_label",
        "phishing_probability",
    ]

    if list(predictions.columns) != expected_columns:
        raise ValueError("External predictions do not match the anonymous schema.")

    return predictions


def metrics_for_predictions(predictions: pd.DataFrame) -> dict[str, float]:
    """Calculate external metrics from anonymous prediction rows."""

    return calculate_external_metrics(
        predictions["actual_label"].astype(int),
        predictions["predicted_label"].astype(int),
        predictions["phishing_probability"].astype(float),
    )


def build_balanced_sample(predictions: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Retain all phishing rows and sample an equal number of legitimate rows."""

    phishing = predictions[predictions["actual_label"] == PHISHING_LABEL]
    legitimate = predictions[predictions["actual_label"] == LEGITIMATE_LABEL]
    sampled_legitimate = legitimate.sample(
        n=len(phishing),
        replace=False,
        random_state=seed,
    )
    return (
        pd.concat([phishing, sampled_legitimate], ignore_index=True)
        .sort_values("row_index")
        .reset_index(drop=True)
    )


def balanced_sensitivity_records(predictions: pd.DataFrame) -> list[dict[str, float | int | str | None]]:
    """Build full-data and balanced-sampling sensitivity records."""

    full_metrics = metrics_for_predictions(predictions)
    records: list[dict[str, float | int | str | None]] = [
        {
            "analysis": "full_external",
            "seed": None,
            "sample_rows": int(len(predictions)),
            "phishing_rows": int((predictions["actual_label"] == PHISHING_LABEL).sum()),
            "legitimate_rows": int((predictions["actual_label"] == LEGITIMATE_LABEL).sum()),
            **{metric: full_metrics[metric] for metric in METRIC_COLUMNS},
        }
    ]

    full_recall = full_metrics["phishing_recall"]

    for seed in BALANCED_SAMPLE_SEEDS:
        sample = build_balanced_sample(predictions, seed)
        metrics = metrics_for_predictions(sample)

        if not np.isclose(metrics["phishing_recall"], full_recall):
            raise ValueError(
                "Balanced phishing recall changed even though all phishing rows "
                "were retained."
            )

        records.append(
            {
                "analysis": "balanced_sample",
                "seed": seed,
                "sample_rows": int(len(sample)),
                "phishing_rows": int((sample["actual_label"] == PHISHING_LABEL).sum()),
                "legitimate_rows": int((sample["actual_label"] == LEGITIMATE_LABEL).sum()),
                **{metric: metrics[metric] for metric in METRIC_COLUMNS},
            }
        )

    return records


def summarize_balanced_records(records: list[dict[str, float | int | str | None]]) -> list[dict[str, float | str | None]]:
    """Add mean, standard deviation, min, and max rows for balanced samples."""

    frame = pd.DataFrame(records)
    balanced = frame[frame["analysis"] == "balanced_sample"]
    summaries = []

    for statistic in ["mean", "std", "min", "max"]:
        row: dict[str, float | str | None] = {
            "analysis": f"balanced_{statistic}",
            "seed": None,
            "sample_rows": float(balanced["sample_rows"].mean()),
            "phishing_rows": float(balanced["phishing_rows"].mean()),
            "legitimate_rows": float(balanced["legitimate_rows"].mean()),
        }
        for metric in METRIC_COLUMNS:
            row[metric] = float(getattr(balanced[metric], statistic)())
        summaries.append(row)

    return summaries


def _metric_functions() -> dict[str, Callable[[np.ndarray, np.ndarray, np.ndarray], float]]:
    """Return bootstrap metric functions using phishing label 0 as positive."""

    def binary_phishing(y_true: np.ndarray) -> np.ndarray:
        return (y_true == PHISHING_LABEL).astype(int)

    def accuracy(y_true: np.ndarray, y_pred: np.ndarray, probability: np.ndarray) -> float:
        return float(np.mean(y_true == y_pred))

    def precision(y_true: np.ndarray, y_pred: np.ndarray, probability: np.ndarray) -> float:
        predicted_positive = y_pred == PHISHING_LABEL
        true_positive = (y_true == PHISHING_LABEL) & predicted_positive
        denominator = int(predicted_positive.sum())
        return float(true_positive.sum() / denominator) if denominator else 0.0

    def recall(y_true: np.ndarray, y_pred: np.ndarray, probability: np.ndarray) -> float:
        actual_positive = y_true == PHISHING_LABEL
        true_positive = actual_positive & (y_pred == PHISHING_LABEL)
        return float(true_positive.sum() / actual_positive.sum())

    def f1(y_true: np.ndarray, y_pred: np.ndarray, probability: np.ndarray) -> float:
        precision_value = precision(y_true, y_pred, probability)
        recall_value = recall(y_true, y_pred, probability)

        if precision_value + recall_value == 0:
            return 0.0

        return float(2 * precision_value * recall_value / (precision_value + recall_value))

    def roc_auc(y_true: np.ndarray, y_pred: np.ndarray, probability: np.ndarray) -> float:
        return float(roc_auc_score(binary_phishing(y_true), probability))

    return {
        "accuracy": accuracy,
        "phishing_precision": precision,
        "phishing_recall": recall,
        "phishing_f1": f1,
        "roc_auc": roc_auc,
    }


def bootstrap_full_external_ci(
    predictions: pd.DataFrame,
    iterations: int = BOOTSTRAP_ITERATIONS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, dict[str, float]]:
    """Calculate percentile bootstrap intervals over external prediction rows."""

    generator = np.random.default_rng(seed)
    y_true = predictions["actual_label"].astype(int).to_numpy()
    y_pred = predictions["predicted_label"].astype(int).to_numpy()
    probability = predictions["phishing_probability"].astype(float).to_numpy()
    row_count = len(predictions)
    intervals = {}

    for metric_name, metric_function in _metric_functions().items():
        observed = metric_function(y_true, y_pred, probability)
        samples = []

        for _ in range(iterations):
            indices = generator.integers(0, row_count, size=row_count)
            try:
                samples.append(
                    metric_function(y_true[indices], y_pred[indices], probability[indices])
                )
            except ValueError:
                continue

        intervals[metric_name] = {
            "observed": observed,
            "ci_lower": float(np.percentile(samples, 2.5)),
            "ci_upper": float(np.percentile(samples, 97.5)),
        }

    return intervals


def save_full_vs_balanced_figure(records: list[dict[str, float | int | str | None]]) -> None:
    """Save full-external versus balanced-mean sensitivity figure."""

    frame = pd.DataFrame(records)
    full = frame[frame["analysis"] == "full_external"].iloc[0]
    balanced_mean = frame[frame["analysis"] == "balanced_mean"].iloc[0]
    comparison = pd.DataFrame(
        [
            {"analysis": "Full external", **{metric: full[metric] for metric in METRIC_COLUMNS}},
            {
                "analysis": "Balanced mean",
                **{metric: balanced_mean[metric] for metric in METRIC_COLUMNS},
            },
        ]
    )
    ax = comparison.set_index("analysis").plot(kind="bar", figsize=(9, 5), width=0.72)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Metric value")
    ax.set_xlabel("")
    ax.set_title("URL-Phish full external vs balanced sensitivity")
    ax.legend(title="Metric", ncol=2)
    plt.xticks(rotation=0)
    plt.tight_layout()
    EXTERNAL_FULL_VS_BALANCED_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(EXTERNAL_FULL_VS_BALANCED_FIGURE, dpi=160)
    plt.close()


def run_external_sensitivity_analysis() -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    """Run full and balanced external sensitivity analyses."""

    predictions = load_external_predictions()
    records = balanced_sensitivity_records(predictions)
    records.extend(summarize_balanced_records(records))
    results = pd.DataFrame(records)
    intervals = bootstrap_full_external_ci(predictions)

    results.to_csv(EXTERNAL_SENSITIVITY_RESULTS_CSV, index=False)
    with EXTERNAL_BOOTSTRAP_CI_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
                "bootstrap_seed": BOOTSTRAP_SEED,
                "metrics": intervals,
                "safety_statement": (
                    "Bootstrap used anonymous saved prediction rows only; "
                    "no dataset URL was opened, requested, resolved, or contacted."
                ),
            },
            file,
            indent=2,
        )
        file.write("\n")
    save_full_vs_balanced_figure(records)
    return results, intervals


def main() -> None:
    """Run external prevalence sensitivity analysis."""

    results, intervals = run_external_sensitivity_analysis()
    print(f"Saved: {EXTERNAL_SENSITIVITY_RESULTS_CSV}")
    print(f"Saved: {EXTERNAL_BOOTSTRAP_CI_FILE}")
    print(f"Saved: {EXTERNAL_FULL_VS_BALANCED_FIGURE}")
    print(results.to_string(index=False))
    print(intervals)


if __name__ == "__main__":
    main()
