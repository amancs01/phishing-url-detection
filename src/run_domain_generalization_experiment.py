"""Evaluate Decision Trees under the registrable-domain-disjoint split."""

from __future__ import annotations

import json
import time
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

from src.bootstrap_metrics import bootstrap_metric_ci, dataframe_records, metric_functions
from src.build_domain_disjoint_split import DOMAIN_DISJOINT_SPLIT_SUMMARY_FILE
from src.build_research_tiers import build_research_tiers
from src.config import FIGURES_DIRECTORY, RESULTS_DIRECTORY
from src.run_feature_tier_experiment import (
    FEATURE_TIER_PERFORMANCE_CSV,
    FIXED_TREE_PARAMS,
    evaluate_predictions,
    phishing_probability,
)


DOMAIN_DISJOINT_PERFORMANCE_CSV = RESULTS_DIRECTORY / "domain_disjoint_performance.csv"
DOMAIN_DISJOINT_PERFORMANCE_JSON = RESULTS_DIRECTORY / "domain_disjoint_performance.json"
RANDOM_VS_DOMAIN_F1_FIGURE = FIGURES_DIRECTORY / "random_vs_domain_f1.png"
RANDOM_VS_DOMAIN_RECALL_FIGURE = FIGURES_DIRECTORY / "random_vs_domain_recall.png"
BOOTSTRAP_SEED = 20260821
BOOTSTRAP_ITERATIONS = 1000
EVALUATED_TIERS = ["D-matched", "E"]


def load_domain_split_indices() -> dict[str, list[int]]:
    """Load row indices from the committed domain-disjoint split summary."""

    with DOMAIN_DISJOINT_SPLIT_SUMMARY_FILE.open(encoding="utf-8") as file:
        summary = json.load(file)

    return {
        split_name: [int(index) for index in indices]
        for split_name, indices in summary["row_indices"].items()
    }


def train_fixed_model(x_train: pd.DataFrame, y_train: pd.Series) -> tuple[DecisionTreeClassifier, float]:
    """Train the pre-declared fixed Decision Tree."""

    model = DecisionTreeClassifier(**FIXED_TREE_PARAMS)
    start = time.perf_counter()
    model.fit(x_train, y_train)
    training_time = time.perf_counter() - start
    return model, training_time


def evaluate_tier(
    tier_name: str,
    matrix: pd.DataFrame,
    target: pd.Series,
    split_indices: dict[str, list[int]],
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Train and evaluate one tier on the domain-disjoint split."""

    model, training_time = train_fixed_model(
        matrix.loc[split_indices["train"]],
        target.loc[split_indices["train"]],
    )
    split_metrics = {}
    prediction_times = {}

    for split_name, indices in split_indices.items():
        x_split = matrix.loc[indices]
        y_split = target.loc[indices]
        start = time.perf_counter()
        y_pred = pd.Series(model.predict(x_split), index=indices)
        probabilities = phishing_probability(model, x_split)
        prediction_times[split_name] = time.perf_counter() - start
        split_metrics[split_name] = evaluate_predictions(y_split, y_pred, probabilities)

    test_indices = split_indices["test"]
    x_test = matrix.loc[test_indices]
    y_test = target.loc[test_indices]
    y_test_pred = pd.Series(model.predict(x_test), index=test_indices)
    test_probabilities = phishing_probability(model, x_test)
    test_predictions = pd.DataFrame(
        {
            "tier": tier_name,
            "row_index": test_indices,
            "y_true": y_test.astype(int).tolist(),
            "y_pred": y_test_pred.loc[test_indices].astype(int).tolist(),
            "phishing_probability": test_probabilities,
        }
    )
    bootstrap_intervals = bootstrap_intervals_for_predictions(test_predictions)

    result = {
        "tier": tier_name,
        "split_type": "domain_disjoint",
        "feature_count": int(matrix.shape[1]),
        "training_accuracy": split_metrics["train"]["accuracy"],
        "validation_accuracy": split_metrics["validation"]["accuracy"],
        "test_accuracy": split_metrics["test"]["accuracy"],
        "phishing_precision": split_metrics["test"]["phishing_precision"],
        "phishing_recall": split_metrics["test"]["phishing_recall"],
        "phishing_f1": split_metrics["test"]["phishing_f1"],
        "roc_auc": split_metrics["test"]["roc_auc"],
        "confusion_matrix": split_metrics["test"]["confusion_matrix"],
        "true_phishing_predicted_phishing": split_metrics["test"][
            "true_phishing_predicted_phishing"
        ],
        "true_phishing_predicted_legitimate": split_metrics["test"][
            "true_phishing_predicted_legitimate"
        ],
        "true_legitimate_predicted_phishing": split_metrics["test"][
            "true_legitimate_predicted_phishing"
        ],
        "true_legitimate_predicted_legitimate": split_metrics["test"][
            "true_legitimate_predicted_legitimate"
        ],
        "tree_depth": int(model.get_depth()),
        "number_of_leaves": int(model.get_n_leaves()),
        "training_time_seconds": float(training_time),
        "test_prediction_time_seconds": float(prediction_times["test"]),
        "fixed_tree_params": FIXED_TREE_PARAMS,
        "bootstrap_intervals": bootstrap_intervals,
    }

    return result, test_predictions


def bootstrap_intervals_for_predictions(predictions: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Calculate bootstrap intervals for one tier's test predictions."""

    metrics = metric_functions()
    tier_seed_offsets = {"D-matched": 17, "E": 31}
    tier_name = str(predictions["tier"].iloc[0])
    generator = np.random.default_rng(BOOTSTRAP_SEED + tier_seed_offsets[tier_name])
    intervals = {}
    y_true = predictions["y_true"].to_numpy()
    y_pred = predictions["y_pred"].to_numpy()

    for metric_name, metric_function in metrics.items():
        observed, ci_lower, ci_upper = bootstrap_metric_ci(
            y_true,
            y_pred,
            metric_function,
            generator,
            BOOTSTRAP_ITERATIONS,
        )
        intervals[metric_name] = {
            "observed": observed,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
        }

    return intervals


def build_random_vs_domain_gaps(domain_performance: pd.DataFrame) -> list[dict[str, Any]]:
    """Compare earlier random-split fixed-tree metrics with domain-disjoint metrics."""

    random_performance = pd.read_csv(FEATURE_TIER_PERFORMANCE_CSV)
    random_fixed = random_performance[
        (random_performance["track"] == "fixed_tree")
        & (random_performance["tier"].isin(EVALUATED_TIERS))
    ].set_index("tier")
    domain = domain_performance.set_index("tier")
    records = []

    for tier_name in EVALUATED_TIERS:
        for metric in ["test_accuracy", "phishing_recall", "phishing_f1"]:
            random_value = float(random_fixed.loc[tier_name, metric])
            domain_value = float(domain.loc[tier_name, metric])
            records.append(
                {
                    "tier": tier_name,
                    "metric": metric,
                    "random_split": random_value,
                    "domain_disjoint": domain_value,
                    "domain_minus_random": domain_value - random_value,
                    "domain_minus_random_percentage_points": (
                        domain_value - random_value
                    )
                    * 100,
                }
            )

    return records


def save_random_vs_domain_figures(domain_performance: pd.DataFrame) -> None:
    """Save random-vs-domain F1 and recall figures."""

    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    random_performance = pd.read_csv(FEATURE_TIER_PERFORMANCE_CSV)
    random_fixed = random_performance[
        (random_performance["track"] == "fixed_tree")
        & (random_performance["tier"].isin(EVALUATED_TIERS))
    ][["tier", "phishing_f1", "phishing_recall"]].copy()
    random_fixed["split"] = "random"
    domain = domain_performance[["tier", "phishing_f1", "phishing_recall"]].copy()
    domain["split"] = "domain-disjoint"
    combined = pd.concat([random_fixed, domain], ignore_index=True)

    for metric, output_file, ylabel in [
        ("phishing_f1", RANDOM_VS_DOMAIN_F1_FIGURE, "Phishing F1"),
        ("phishing_recall", RANDOM_VS_DOMAIN_RECALL_FIGURE, "Phishing recall"),
    ]:
        pivot = combined.pivot(index="tier", columns="split", values=metric).loc[
            EVALUATED_TIERS,
            ["random", "domain-disjoint"],
        ]
        ax = pivot.plot(kind="bar", figsize=(8, 5), width=0.72)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Feature tier")
        ax.set_title(f"Random vs domain-disjoint {ylabel}")
        ax.set_ylim(0, 1.05)
        ax.legend(title="Split")
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(output_file, dpi=160)
        plt.close()


def run_domain_generalization_experiment() -> pd.DataFrame:
    """Run fixed-tree domain-disjoint evaluation for D-matched and E."""

    tiers = build_research_tiers()
    split_indices = load_domain_split_indices()
    performance_records = []

    for tier_name in EVALUATED_TIERS:
        print(f"Evaluating Tier {tier_name} on domain-disjoint split...")
        result, predictions = evaluate_tier(
            tier_name,
            tiers.features[tier_name],
            tiers.target,
            split_indices,
        )
        performance_records.append(result)

    performance = pd.DataFrame(performance_records)
    gaps = build_random_vs_domain_gaps(performance)
    save_random_vs_domain_figures(performance)

    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    performance.to_csv(DOMAIN_DISJOINT_PERFORMANCE_CSV, index=False)

    with DOMAIN_DISJOINT_PERFORMANCE_JSON.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "fixed_tree_params": FIXED_TREE_PARAMS,
                "evaluated_tiers": EVALUATED_TIERS,
                "domain_split_summary_file": str(DOMAIN_DISJOINT_SPLIT_SUMMARY_FILE),
                "test_data_used_for_model_selection": False,
                "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
                "bootstrap_seed": BOOTSTRAP_SEED,
                "results": dataframe_records(performance),
                "random_vs_domain_gaps": gaps,
                "safety_statement": (
                    "The experiment used local feature matrices and saved "
                    "domain-disjoint row indices only; no URL was contacted."
                ),
            },
            file,
            indent=2,
        )
        file.write("\n")

    return performance


def main() -> None:
    """Run the domain generalization experiment."""

    performance = run_domain_generalization_experiment()
    print(f"Saved: {DOMAIN_DISJOINT_PERFORMANCE_CSV}")
    print(f"Saved: {DOMAIN_DISJOINT_PERFORMANCE_JSON}")
    print(
        performance[
            [
                "tier",
                "test_accuracy",
                "phishing_recall",
                "phishing_f1",
                "roc_auc",
                "tree_depth",
                "number_of_leaves",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
