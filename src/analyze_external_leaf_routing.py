"""Post-hoc leaf-routing diagnostics for external false positives."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import (
    FIGURES_DIRECTORY,
    OPTIMIZED_MODEL_FILE,
    PROCESSED_DATA_DIRECTORY,
    PROCESSED_DATA_FILE,
    RESULTS_DIRECTORY,
    URL_PHISH_EXTERNAL_MATRIX_FILE,
)
from src.feature_definitions import FEATURE_NAMES
from src.prepare_external_data import TARGET_COLUMN, validate_external_feature_matrix
from src.predict import PHISHING_LABEL, LEGITIMATE_LABEL, validate_model
from src.run_external_validation import phishing_probability_from_proba


EXTERNAL_LEAF_ROUTING_FILE = RESULTS_DIRECTORY / "external_leaf_routing.csv"
EXTERNAL_LEAF_ROUTING_SUMMARY_FILE = RESULTS_DIRECTORY / "external_leaf_routing_summary.json"
EXTERNAL_PROBABILITY_DISTRIBUTION_FIGURE = (
    FIGURES_DIRECTORY / "external_probability_distribution.png"
)
TRAIN_SPLIT_FILE = PROCESSED_DATA_DIRECTORY / "train.csv"
VALIDATION_SPLIT_FILE = PROCESSED_DATA_DIRECTORY / "validation.csv"
TOP_FALSE_POSITIVE_LEAVES = 8


def load_model():
    """Load and validate the frozen Tier E model."""

    model = joblib.load(OPTIMIZED_MODEL_FILE)
    validate_model(model)
    return model


def load_internal_training_frame() -> pd.DataFrame:
    """Load the PhiUSIIL train+validation rows used to fit the packaged model."""

    frames = [pd.read_csv(TRAIN_SPLIT_FILE), pd.read_csv(VALIDATION_SPLIT_FILE)]
    training = pd.concat(frames, ignore_index=True)
    required_columns = FEATURE_NAMES + ["label"]

    if any(column not in training.columns for column in required_columns):
        raise ValueError("Internal train/validation files do not match FEATURE_NAMES.")

    return training[required_columns]


def load_internal_all_frame() -> pd.DataFrame:
    """Load all internal PhiUSIIL feature rows for probability diagnostics."""

    data = pd.read_csv(PROCESSED_DATA_FILE)

    if list(data.columns) != FEATURE_NAMES + ["label"]:
        raise ValueError("Internal processed file does not match FEATURE_NAMES.")

    return data


def load_external_frame() -> pd.DataFrame:
    """Load ignored external URL-Phish feature matrix."""

    external = pd.read_csv(URL_PHISH_EXTERNAL_MATRIX_FILE)
    validate_external_feature_matrix(external)
    return external


def leaf_path(model, leaf_id: int) -> str:
    """Return a complete human-readable path to a Decision Tree leaf."""

    tree = model.tree_
    paths: list[str] = []

    def visit(node_id: int, conditions: list[str]) -> bool:
        if node_id == leaf_id:
            paths.extend(conditions)
            return True

        left_child = tree.children_left[node_id]
        right_child = tree.children_right[node_id]

        if left_child == right_child:
            return False

        feature_name = FEATURE_NAMES[tree.feature[node_id]]
        threshold = tree.threshold[node_id]

        if visit(left_child, conditions + [f"{feature_name} <= {threshold:.6f}"]):
            return True

        return visit(right_child, conditions + [f"{feature_name} > {threshold:.6f}"])

    visit(0, [])
    return " AND ".join(paths)


def probability_summary(name: str, labels: pd.Series, probabilities: pd.Series) -> dict[str, Any]:
    """Summarize phishing-probability distributions for one group."""

    values = probabilities.astype(float)
    return {
        "group": name,
        "rows": int(values.shape[0]),
        "mean": float(values.mean()),
        "median": float(values.median()),
        "q01": float(values.quantile(0.01)),
        "q05": float(values.quantile(0.05)),
        "q10": float(values.quantile(0.10)),
        "q25": float(values.quantile(0.25)),
        "q75": float(values.quantile(0.75)),
        "q90": float(values.quantile(0.90)),
        "q95": float(values.quantile(0.95)),
        "q99": float(values.quantile(0.99)),
        "proportion_probability_ge_0_5": float((values >= 0.5).mean()),
        "proportion_probability_exactly_0": float((values == 0).mean()),
        "proportion_probability_exactly_1": float((values == 1).mean()),
    }


def build_leaf_routing_table(model, training: pd.DataFrame, external: pd.DataFrame) -> pd.DataFrame:
    """Aggregate internal training and external routing counts by leaf."""

    train_leaves = pd.Series(model.apply(training[FEATURE_NAMES]), name="leaf_node_id")
    external_leaves = pd.Series(model.apply(external[FEATURE_NAMES]), name="leaf_node_id")
    external_pred = pd.Series(model.predict(external[FEATURE_NAMES]), name="predicted_label")
    leaf_ids = sorted(set(train_leaves.unique()) | set(external_leaves.unique()))
    records = []

    for leaf_id in leaf_ids:
        train_mask = train_leaves == leaf_id
        external_mask = external_leaves == leaf_id
        train_labels = training.loc[train_mask, "label"]
        external_labels = external.loc[external_mask, TARGET_COLUMN]
        external_predictions = external_pred.loc[external_mask]
        phishing_count = int((train_labels == PHISHING_LABEL).sum())
        legitimate_count = int((train_labels == LEGITIMATE_LABEL).sum())
        train_count = int(train_mask.sum())
        external_benign_count = int((external_labels == LEGITIMATE_LABEL).sum())
        external_phishing_count = int((external_labels == PHISHING_LABEL).sum())
        external_benign_false_positive_count = int(
            (
                (external_labels == LEGITIMATE_LABEL)
                & (external_predictions == PHISHING_LABEL)
            ).sum()
        )
        predicted_class = int(model.classes_[np.argmax(model.tree_.value[leaf_id][0])])
        records.append(
            {
                "leaf_node_id": int(leaf_id),
                "phiusiil_training_sample_count": train_count,
                "phiusiil_training_phishing_count": phishing_count,
                "phiusiil_training_legitimate_count": legitimate_count,
                "training_phishing_proportion": (
                    phishing_count / train_count if train_count else None
                ),
                "predicted_class": predicted_class,
                "external_benign_count": external_benign_count,
                "external_phishing_count": external_phishing_count,
                "external_benign_false_positive_count": external_benign_false_positive_count,
                "decision_path": leaf_path(model, int(leaf_id)),
            }
        )

    return (
        pd.DataFrame(records)
        .sort_values("external_benign_false_positive_count", ascending=False)
        .reset_index(drop=True)
    )


def build_probability_summaries(model, internal_all: pd.DataFrame, external: pd.DataFrame) -> list[dict[str, Any]]:
    """Summarize phishing probabilities for internal and external classes."""

    internal_probabilities = phishing_probability_from_proba(
        model,
        model.predict_proba(internal_all[FEATURE_NAMES]),
    )
    external_probabilities = phishing_probability_from_proba(
        model,
        model.predict_proba(external[FEATURE_NAMES]),
    )
    groups = [
        (
            "PhiUSIIL legitimate",
            internal_all["label"] == LEGITIMATE_LABEL,
            internal_all["label"],
            internal_probabilities,
        ),
        (
            "PhiUSIIL phishing",
            internal_all["label"] == PHISHING_LABEL,
            internal_all["label"],
            internal_probabilities,
        ),
        (
            "URL-Phish benign",
            external[TARGET_COLUMN] == LEGITIMATE_LABEL,
            external[TARGET_COLUMN],
            external_probabilities,
        ),
        (
            "URL-Phish phishing",
            external[TARGET_COLUMN] == PHISHING_LABEL,
            external[TARGET_COLUMN],
            external_probabilities,
        ),
    ]
    return [
        probability_summary(name, labels[mask], probabilities[mask])
        for name, mask, labels, probabilities in groups
    ]


def save_probability_figure(model, internal_all: pd.DataFrame, external: pd.DataFrame) -> None:
    """Save phishing-probability ECDF-style distribution plot."""

    internal_probabilities = phishing_probability_from_proba(
        model,
        model.predict_proba(internal_all[FEATURE_NAMES]),
    )
    external_probabilities = phishing_probability_from_proba(
        model,
        model.predict_proba(external[FEATURE_NAMES]),
    )
    series_map = {
        "PhiUSIIL legitimate": internal_probabilities[
            internal_all["label"] == LEGITIMATE_LABEL
        ],
        "PhiUSIIL phishing": internal_probabilities[
            internal_all["label"] == PHISHING_LABEL
        ],
        "URL-Phish benign": external_probabilities[
            external[TARGET_COLUMN] == LEGITIMATE_LABEL
        ],
        "URL-Phish phishing": external_probabilities[
            external[TARGET_COLUMN] == PHISHING_LABEL
        ],
    }
    fig, ax = plt.subplots(figsize=(8, 5))

    for label, values in series_map.items():
        sorted_values = np.sort(values.astype(float).to_numpy())
        y_values = np.arange(1, len(sorted_values) + 1) / len(sorted_values)
        ax.step(sorted_values, y_values, where="post", label=label)

    ax.axvline(0.5, color="#555555", linestyle="--", linewidth=1)
    ax.set_xlabel("Phishing probability")
    ax.set_ylabel("Cumulative proportion")
    ax.set_title("Post-hoc phishing-probability distributions")
    ax.legend()
    fig.tight_layout()
    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    fig.savefig(EXTERNAL_PROBABILITY_DISTRIBUTION_FIGURE, dpi=160)
    plt.close(fig)


def run_external_leaf_routing_analysis() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run leaf routing and probability diagnostics."""

    model = load_model()
    training = load_internal_training_frame()
    internal_all = load_internal_all_frame()
    external = load_external_frame()
    leaf_table = build_leaf_routing_table(model, training, external)
    probability_summaries = build_probability_summaries(model, internal_all, external)
    save_probability_figure(model, internal_all, external)
    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    leaf_table.to_csv(EXTERNAL_LEAF_ROUTING_FILE, index=False)
    summary = {
        "analysis_type": "POST-HOC DIAGNOSTIC ANALYSIS",
        "top_false_positive_leaves": leaf_table.head(TOP_FALSE_POSITIVE_LEAVES).to_dict(
            orient="records"
        ),
        "probability_summaries": probability_summaries,
        "external_predicted_phishing_percentage": float(
            (model.predict(external[FEATURE_NAMES]) == PHISHING_LABEL).mean() * 100
        ),
        "external_benign_specificity": float(
            (
                model.predict(external[external[TARGET_COLUMN] == LEGITIMATE_LABEL][FEATURE_NAMES])
                == LEGITIMATE_LABEL
            ).mean()
        ),
        "safety_statement": (
            "Leaf routing used local feature matrices and the frozen model; no URL "
            "was opened, requested, resolved, or contacted."
        ),
    }

    with EXTERNAL_LEAF_ROUTING_SUMMARY_FILE.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)
        file.write("\n")

    return leaf_table, summary


def main() -> None:
    """Run post-hoc external leaf-routing diagnostics."""

    leaf_table, summary = run_external_leaf_routing_analysis()
    print(f"Saved: {EXTERNAL_LEAF_ROUTING_FILE}")
    print(f"Saved: {EXTERNAL_LEAF_ROUTING_SUMMARY_FILE}")
    print(f"Saved: {EXTERNAL_PROBABILITY_DISTRIBUTION_FIGURE}")
    print(
        leaf_table.head(TOP_FALSE_POSITIVE_LEAVES)[
            [
                "leaf_node_id",
                "phiusiil_training_sample_count",
                "training_phishing_proportion",
                "external_benign_false_positive_count",
                "external_phishing_count",
                "decision_path",
            ]
        ].to_string(index=False)
    )
    print(summary["probability_summaries"])


if __name__ == "__main__":
    main()
