"""Bootstrap confidence intervals for held-out feature-tier predictions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, recall_score

from src.config import RESULTS_DIRECTORY


FEATURE_TIER_PERFORMANCE_CSV = RESULTS_DIRECTORY / "feature_tier_performance.csv"
FEATURE_TIER_TEST_PREDICTIONS_CSV = (
    RESULTS_DIRECTORY / "feature_tier_test_predictions.csv"
)
PHISHING_LABEL = 0


BOOTSTRAP_METRICS_CSV = RESULTS_DIRECTORY / "feature_tier_bootstrap_metrics.csv"
BOOTSTRAP_METRICS_JSON = RESULTS_DIRECTORY / "feature_tier_bootstrap_metrics.json"
BOOTSTRAP_SEED = 20260821
BOOTSTRAP_ITERATIONS = 1000
PAIRWISE_COMPARISONS = [
    ("A", "C"),
    ("C", "D-matched"),
    ("A", "D-matched"),
    ("D-matched", "E"),
]


def dataframe_records(dataframe: pd.DataFrame) -> list[dict]:
    """Return JSON-safe records with NaN converted to None."""

    return dataframe.astype(object).where(pd.notna(dataframe), None).to_dict(
        orient="records"
    )


def metric_functions() -> dict[str, Callable[[np.ndarray, np.ndarray], float]]:
    """Return metrics used for bootstrap intervals."""

    return {
        "accuracy": lambda y_true, y_pred: float(accuracy_score(y_true, y_pred)),
        "phishing_recall": lambda y_true, y_pred: float(
            recall_score(y_true, y_pred, pos_label=PHISHING_LABEL)
        ),
        "phishing_f1": lambda y_true, y_pred: float(
            f1_score(y_true, y_pred, pos_label=PHISHING_LABEL)
        ),
    }


def bootstrap_metric_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric: Callable[[np.ndarray, np.ndarray], float],
    rng: np.random.Generator,
    iterations: int = BOOTSTRAP_ITERATIONS,
) -> tuple[float, float, float]:
    """Return observed metric and percentile 95% bootstrap CI."""

    observed = metric(y_true, y_pred)
    sample_count = len(y_true)
    bootstrap_values = np.empty(iterations)

    for iteration in range(iterations):
        sample_indices = rng.integers(0, sample_count, sample_count)
        bootstrap_values[iteration] = metric(
            y_true[sample_indices],
            y_pred[sample_indices],
        )

    lower, upper = np.percentile(bootstrap_values, [2.5, 97.5])
    return observed, float(lower), float(upper)


def build_condition_intervals(
    predictions: pd.DataFrame,
    iterations: int = BOOTSTRAP_ITERATIONS,
    seed: int = BOOTSTRAP_SEED,
) -> pd.DataFrame:
    """Build metric intervals for every tier and track."""

    records: list[dict[str, object]] = []
    metrics = metric_functions()
    rng = np.random.default_rng(seed)

    for (tier, track), group in predictions.groupby(["tier", "track"], sort=True):
        y_true = group["y_true"].to_numpy()
        y_pred = group["y_pred"].to_numpy()

        for metric_name, metric_function in metrics.items():
            observed, ci_lower, ci_upper = bootstrap_metric_ci(
                y_true,
                y_pred,
                metric_function,
                rng,
                iterations,
            )
            records.append(
                {
                    "comparison_type": "condition",
                    "track": track,
                    "tier": tier,
                    "metric": metric_name,
                    "observed": observed,
                    "ci_lower": ci_lower,
                    "ci_upper": ci_upper,
                    "difference": None,
                    "difference_percentage_points": None,
                    "baseline_tier": None,
                    "comparison_tier": None,
                    "bootstrap_iterations": iterations,
                    "bootstrap_seed": seed,
                }
            )

    return pd.DataFrame(records)


def _pair_metric_difference(
    left: pd.DataFrame,
    right: pd.DataFrame,
    metric: Callable[[np.ndarray, np.ndarray], float],
    rng: np.random.Generator,
    iterations: int,
) -> tuple[float, float, float]:
    """Bootstrap paired metric difference: left minus right."""

    left = left.sort_values("row_index")
    right = right.sort_values("row_index")

    if left["row_index"].tolist() != right["row_index"].tolist():
        raise ValueError("Pairwise comparison requires identical test row indices.")

    y_true = left["y_true"].to_numpy()
    left_pred = left["y_pred"].to_numpy()
    right_pred = right["y_pred"].to_numpy()
    observed = metric(y_true, left_pred) - metric(y_true, right_pred)
    sample_count = len(y_true)
    bootstrap_values = np.empty(iterations)

    for iteration in range(iterations):
        sample_indices = rng.integers(0, sample_count, sample_count)
        sampled_true = y_true[sample_indices]
        bootstrap_values[iteration] = metric(
            sampled_true,
            left_pred[sample_indices],
        ) - metric(sampled_true, right_pred[sample_indices])

    lower, upper = np.percentile(bootstrap_values, [2.5, 97.5])
    return float(observed), float(lower), float(upper)


def build_pairwise_intervals(
    predictions: pd.DataFrame,
    iterations: int = BOOTSTRAP_ITERATIONS,
    seed: int = BOOTSTRAP_SEED,
) -> pd.DataFrame:
    """Build paired bootstrap intervals for requested tier differences."""

    records: list[dict[str, object]] = []
    metrics = metric_functions()
    rng = np.random.default_rng(seed + 1)

    for track in sorted(predictions["track"].unique()):
        track_predictions = predictions[predictions["track"] == track]

        for baseline_tier, comparison_tier in PAIRWISE_COMPARISONS:
            left = track_predictions[track_predictions["tier"] == baseline_tier]
            right = track_predictions[track_predictions["tier"] == comparison_tier]

            for metric_name, metric_function in metrics.items():
                difference, ci_lower, ci_upper = _pair_metric_difference(
                    left,
                    right,
                    metric_function,
                    rng,
                    iterations,
                )
                records.append(
                    {
                        "comparison_type": "pairwise_difference",
                        "track": track,
                        "tier": None,
                        "metric": metric_name,
                        "observed": None,
                        "ci_lower": ci_lower,
                        "ci_upper": ci_upper,
                        "difference": difference,
                        "difference_percentage_points": difference * 100,
                        "baseline_tier": baseline_tier,
                        "comparison_tier": comparison_tier,
                        "bootstrap_iterations": iterations,
                        "bootstrap_seed": seed,
                    }
                )

    return pd.DataFrame(records)


def run_bootstrap_analysis() -> pd.DataFrame:
    """Run bootstrap intervals and save CSV/JSON artifacts."""

    predictions = pd.read_csv(FEATURE_TIER_TEST_PREDICTIONS_CSV)
    performance = pd.read_csv(FEATURE_TIER_PERFORMANCE_CSV)
    condition_intervals = build_condition_intervals(predictions)
    pairwise_intervals = build_pairwise_intervals(predictions)
    intervals = pd.concat([condition_intervals, pairwise_intervals], ignore_index=True)

    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    intervals.to_csv(BOOTSTRAP_METRICS_CSV, index=False)

    with BOOTSTRAP_METRICS_JSON.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "bootstrap_seed": BOOTSTRAP_SEED,
                "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
                "method": (
                    "Percentile bootstrap over held-out test prediction rows; "
                    "models are not retrained during bootstrap resampling."
                ),
                "metrics": list(metric_functions()),
                "pairwise_comparisons": PAIRWISE_COMPARISONS,
                "performance_rows": dataframe_records(performance),
                "intervals": dataframe_records(intervals),
            },
            file,
            indent=2,
        )
        file.write("\n")

    return intervals


def main() -> None:
    """Run command-line bootstrap analysis."""

    intervals = run_bootstrap_analysis()
    print(f"Saved: {BOOTSTRAP_METRICS_CSV}")
    print(f"Saved: {BOOTSTRAP_METRICS_JSON}")
    print(intervals.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
