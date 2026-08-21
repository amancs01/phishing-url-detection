"""Post-hoc dataset-origin separability diagnostics."""

from __future__ import annotations

import json
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from src.config import FIGURES_DIRECTORY, PROCESSED_DATA_FILE, RESULTS_DIRECTORY, URL_PHISH_EXTERNAL_MATRIX_FILE
from src.feature_definitions import FEATURE_NAMES
from src.prepare_external_data import TARGET_COLUMN, validate_external_feature_matrix
from src.predict import PHISHING_LABEL, LEGITIMATE_LABEL


DATASET_ORIGIN_PERFORMANCE_FILE = RESULTS_DIRECTORY / "dataset_origin_performance.json"
BENIGN_ORIGIN_IMPORTANCE_FIGURE = FIGURES_DIRECTORY / "dataset_origin_importance_benign.png"
PHISHING_ORIGIN_IMPORTANCE_FIGURE = FIGURES_DIRECTORY / "dataset_origin_importance_phishing.png"
ORIGIN_RANDOM_STATE = 42
ORIGIN_TREE_MAX_DEPTH = 5
INTERNAL_ORIGIN_LABEL = 0
EXTERNAL_ORIGIN_LABEL = 1
TEST_SIZE = 0.30


def load_origin_source_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load internal and external feature matrices."""

    internal = pd.read_csv(PROCESSED_DATA_FILE)
    external = pd.read_csv(URL_PHISH_EXTERNAL_MATRIX_FILE)
    validate_external_feature_matrix(external)

    if list(internal.columns) != FEATURE_NAMES + ["label"]:
        raise ValueError("Internal processed feature matrix has unexpected columns.")

    return internal, external


def build_origin_dataset(
    internal: pd.DataFrame,
    external: pd.DataFrame,
    semantic_label: int,
    random_state: int = ORIGIN_RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.Series, dict[str, int]]:
    """Balance source classes for one semantic label and build origin labels."""

    internal_group = internal[internal["label"] == semantic_label]
    external_group = external[external[TARGET_COLUMN] == semantic_label]
    sample_size = min(len(internal_group), len(external_group))
    internal_sample = internal_group.sample(
        n=sample_size,
        random_state=random_state,
        replace=False,
    )
    external_sample = external_group.sample(
        n=sample_size,
        random_state=random_state,
        replace=False,
    )
    x = pd.concat(
        [internal_sample[FEATURE_NAMES], external_sample[FEATURE_NAMES]],
        ignore_index=True,
    )
    y = pd.Series(
        [INTERNAL_ORIGIN_LABEL] * sample_size + [EXTERNAL_ORIGIN_LABEL] * sample_size,
        name="dataset_origin",
    )
    counts = {
        "internal_available_rows": int(len(internal_group)),
        "external_available_rows": int(len(external_group)),
        "balanced_internal_rows": int(sample_size),
        "balanced_external_rows": int(sample_size),
        "total_balanced_rows": int(sample_size * 2),
    }
    return x, y, counts


def run_one_origin_experiment(
    name: str,
    semantic_label: int,
    internal: pd.DataFrame,
    external: pd.DataFrame,
) -> dict[str, Any]:
    """Run one shallow dataset-origin tree experiment."""

    x, y, counts = build_origin_dataset(internal, external, semantic_label)
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=ORIGIN_RANDOM_STATE,
        stratify=y,
    )
    model = DecisionTreeClassifier(
        max_depth=ORIGIN_TREE_MAX_DEPTH,
        random_state=ORIGIN_RANDOM_STATE,
    )
    model.fit(x_train, y_train)
    y_pred = model.predict(x_test)
    external_probability = model.predict_proba(x_test)[
        :,
        list(model.classes_).index(EXTERNAL_ORIGIN_LABEL),
    ]
    importances = (
        pd.DataFrame(
            {
                "feature": FEATURE_NAMES,
                "importance": model.feature_importances_,
            }
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )

    return {
        "experiment": name,
        "semantic_label": int(semantic_label),
        "origin_label_meaning": {
            "0": "PhiUSIIL source",
            "1": "URL-Phish source",
        },
        "post_hoc_diagnostic": True,
        **counts,
        "origin_accuracy": float(accuracy_score(y_test, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, external_probability)),
        "tree_depth": int(model.get_depth()),
        "leaves": int(model.get_n_leaves()),
        "top_feature_importances": importances.head(10).to_dict(orient="records"),
    }


def save_importance_figure(result: dict[str, Any], output_file) -> None:
    """Save top origin-discriminating feature importances."""

    importance = pd.DataFrame(result["top_feature_importances"]).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(importance["feature"], importance["importance"], color="#5c6f3a")
    ax.set_xlabel("Importance")
    ax.set_title(f"Dataset-origin features: {result['experiment']}")
    fig.tight_layout()
    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=160)
    plt.close(fig)


def run_dataset_origin_experiment() -> dict[str, Any]:
    """Run benign-only and phishing-only origin separability diagnostics."""

    internal, external = load_origin_source_frames()
    benign_result = run_one_origin_experiment(
        "benign_only_origin",
        LEGITIMATE_LABEL,
        internal,
        external,
    )
    phishing_result = run_one_origin_experiment(
        "phishing_only_origin",
        PHISHING_LABEL,
        internal,
        external,
    )
    save_importance_figure(benign_result, BENIGN_ORIGIN_IMPORTANCE_FIGURE)
    save_importance_figure(phishing_result, PHISHING_ORIGIN_IMPORTANCE_FIGURE)
    payload = {
        "analysis_type": "POST-HOC DIAGNOSTIC ANALYSIS",
        "model_purpose": "dataset-origin classification, not phishing detection",
        "origin_label_meaning": {
            "0": "PhiUSIIL source",
            "1": "URL-Phish source",
        },
        "random_state": ORIGIN_RANDOM_STATE,
        "diagnostic_tree_max_depth": ORIGIN_TREE_MAX_DEPTH,
        "test_size": TEST_SIZE,
        "experiments": [benign_result, phishing_result],
        "safety_statement": (
            "Origin diagnostics used local feature matrices only; no URL was "
            "opened, requested, resolved, or contacted."
        ),
    }
    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with DATASET_ORIGIN_PERFORMANCE_FILE.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")
    return payload


def main() -> None:
    """Run post-hoc dataset-origin diagnostics."""

    payload = run_dataset_origin_experiment()
    print(f"Saved: {DATASET_ORIGIN_PERFORMANCE_FILE}")
    print(f"Saved: {BENIGN_ORIGIN_IMPORTANCE_FIGURE}")
    print(f"Saved: {PHISHING_ORIGIN_IMPORTANCE_FIGURE}")
    for result in payload["experiments"]:
        print(
            {
                "experiment": result["experiment"],
                "accuracy": result["origin_accuracy"],
                "balanced_accuracy": result["balanced_accuracy"],
                "roc_auc": result["roc_auc"],
                "depth": result["tree_depth"],
                "leaves": result["leaves"],
                "top_features": result["top_feature_importances"][:5],
            }
        )


if __name__ == "__main__":
    main()
