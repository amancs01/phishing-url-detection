"""Compare Decision Tree performance across controlled feature tiers."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    make_scorer,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.tree import DecisionTreeClassifier

from src.build_research_tiers import (
    RESEARCH_SPLIT_INDICES_FILE,
    RESEARCH_TIER_SUMMARY_FILE,
    ResearchTiers,
    build_research_tiers,
    save_research_tier_artifacts,
)
from src.config import FIGURES_DIRECTORY, RANDOM_STATE, RESULTS_DIRECTORY


FEATURE_TIER_PERFORMANCE_CSV = RESULTS_DIRECTORY / "feature_tier_performance.csv"
FEATURE_TIER_PERFORMANCE_JSON = RESULTS_DIRECTORY / "feature_tier_performance.json"
FEATURE_TIER_TEST_PREDICTIONS_CSV = (
    RESULTS_DIRECTORY / "feature_tier_test_predictions.csv"
)
FEATURE_TIER_F1_FIGURE = FIGURES_DIRECTORY / "feature_tier_f1.png"
FEATURE_TIER_RECALL_FIGURE = FIGURES_DIRECTORY / "feature_tier_recall.png"
FEATURE_TIER_COMPLEXITY_FIGURE = FIGURES_DIRECTORY / "feature_tier_complexity.png"
PHISHING_LABEL = 0
LEGITIMATE_LABEL = 1

FIXED_TREE_PARAMS = {
    "criterion": "entropy",
    "max_depth": 10,
    "min_samples_leaf": 1,
    "min_samples_split": 2,
    "ccp_alpha": 0.0,
    "random_state": RANDOM_STATE,
}

TUNING_PARAM_GRID = {
    "criterion": ["gini", "entropy"],
    "max_depth": [6, 10, 14, None],
    "min_samples_leaf": [1, 5],
    "min_samples_split": [2],
    "ccp_alpha": [0.0],
}


def phishing_probability(model: DecisionTreeClassifier, features: pd.DataFrame):
    """Return predicted probability for class 0 using model.classes_."""

    probabilities = model.predict_proba(features)
    class_to_index = {label: index for index, label in enumerate(model.classes_)}
    phishing_index = class_to_index[PHISHING_LABEL]
    return probabilities[:, phishing_index]


def evaluate_predictions(
    y_true: pd.Series,
    y_pred: pd.Series,
    phishing_probability_values,
) -> dict[str, Any]:
    """Calculate classification metrics with phishing as positive class."""

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=[PHISHING_LABEL, LEGITIMATE_LABEL],
    )

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "phishing_precision": float(
            precision_score(y_true, y_pred, pos_label=PHISHING_LABEL)
        ),
        "phishing_recall": float(
            recall_score(y_true, y_pred, pos_label=PHISHING_LABEL)
        ),
        "phishing_f1": float(f1_score(y_true, y_pred, pos_label=PHISHING_LABEL)),
        "roc_auc": float(roc_auc_score(y_true == PHISHING_LABEL, phishing_probability_values)),
        "confusion_matrix": cm.tolist(),
        "true_phishing_predicted_phishing": int(cm[0, 0]),
        "true_phishing_predicted_legitimate": int(cm[0, 1]),
        "true_legitimate_predicted_phishing": int(cm[1, 0]),
        "true_legitimate_predicted_legitimate": int(cm[1, 1]),
    }


def train_fixed_tree(x_train: pd.DataFrame, y_train: pd.Series) -> tuple[DecisionTreeClassifier, dict[str, Any], float]:
    """Fit the pre-declared fixed Decision Tree."""

    model = DecisionTreeClassifier(**FIXED_TREE_PARAMS)
    start = time.perf_counter()
    model.fit(x_train, y_train)
    training_time = time.perf_counter() - start
    return model, FIXED_TREE_PARAMS.copy(), training_time


def train_tuned_tree(x_train: pd.DataFrame, y_train: pd.Series) -> tuple[DecisionTreeClassifier, dict[str, Any], float, float]:
    """Fit a Decision Tree using the same modest CV search protocol."""

    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    scorer = make_scorer(f1_score, pos_label=PHISHING_LABEL)
    search = GridSearchCV(
        DecisionTreeClassifier(random_state=RANDOM_STATE),
        param_grid=TUNING_PARAM_GRID,
        scoring=scorer,
        cv=cv,
        n_jobs=1,
    )
    start = time.perf_counter()
    search.fit(x_train, y_train)
    training_time = time.perf_counter() - start
    best_model = search.best_estimator_

    return (
        best_model,
        search.best_params_,
        training_time,
        float(search.best_score_),
    )


def evaluate_model_on_splits(
    model: DecisionTreeClassifier,
    tiers: ResearchTiers,
    tier_name: str,
    track: str,
    params: dict[str, Any],
    training_time: float,
    cv_best_score: float | None = None,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Evaluate one fitted model on train, validation, and test splits."""

    matrix = tiers.features[tier_name]
    split_indices = tiers.split_indices
    y = tiers.target
    predictions_by_split: dict[str, pd.Series] = {}
    probabilities_by_split = {}
    split_metrics = {}
    prediction_times = {}

    for split_name, indices in split_indices.items():
        x_split = matrix.loc[indices]
        y_split = y.loc[indices]
        start = time.perf_counter()
        y_pred = pd.Series(model.predict(x_split), index=indices)
        phishing_probs = phishing_probability(model, x_split)
        prediction_times[split_name] = time.perf_counter() - start
        predictions_by_split[split_name] = y_pred
        probabilities_by_split[split_name] = phishing_probs
        split_metrics[split_name] = evaluate_predictions(
            y_split,
            y_pred,
            phishing_probs,
        )

    test_indices = split_indices["test"]
    test_predictions = pd.DataFrame(
        {
            "tier": tier_name,
            "track": track,
            "row_index": test_indices,
            "y_true": y.loc[test_indices].astype(int).tolist(),
            "y_pred": predictions_by_split["test"].loc[test_indices].astype(int).tolist(),
            "phishing_probability": probabilities_by_split["test"],
        }
    )

    result = {
        "tier": tier_name,
        "track": track,
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
        "params": params,
        "cv_best_score": cv_best_score,
    }

    return result, test_predictions


def run_track_for_tier(
    tiers: ResearchTiers,
    tier_name: str,
    track: str,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Train and evaluate one track for one tier."""

    matrix = tiers.features[tier_name]
    train_indices = tiers.split_indices["train"]
    x_train = matrix.loc[train_indices]
    y_train = tiers.target.loc[train_indices]

    if track == "fixed_tree":
        model, params, training_time = train_fixed_tree(x_train, y_train)
        cv_best_score = None
    elif track == "equal_tuning":
        model, params, training_time, cv_best_score = train_tuned_tree(x_train, y_train)
    else:
        raise ValueError(f"Unknown experiment track: {track}")

    return evaluate_model_on_splits(
        model,
        tiers,
        tier_name,
        track,
        params,
        training_time,
        cv_best_score,
    )


def save_performance_figures(performance: pd.DataFrame) -> None:
    """Create comparison figures with matplotlib."""

    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    tier_order = ["A", "B", "C", "D-matched", "E"]
    track_order = ["fixed_tree", "equal_tuning"]

    for metric, output_file, ylabel in [
        ("phishing_f1", FEATURE_TIER_F1_FIGURE, "Phishing F1"),
        ("phishing_recall", FEATURE_TIER_RECALL_FIGURE, "Phishing recall"),
    ]:
        pivot = performance.pivot(index="tier", columns="track", values=metric).loc[
            tier_order,
            track_order,
        ]
        ax = pivot.plot(kind="bar", figsize=(9, 5), width=0.75)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Feature tier")
        ax.set_title(f"{ylabel} by feature tier")
        ax.set_ylim(0, 1.05)
        ax.legend(title="Track")
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(output_file, dpi=160)
        plt.close()

    fixed = performance[performance["track"] == "fixed_tree"].set_index("tier").loc[
        tier_order
    ]
    ax = fixed[["tree_depth", "number_of_leaves"]].plot(
        kind="bar",
        figsize=(9, 5),
        width=0.75,
    )
    ax.set_ylabel("Count")
    ax.set_xlabel("Feature tier")
    ax.set_title("Fixed-tree complexity by feature tier")
    ax.legend(title="Complexity")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(FEATURE_TIER_COMPLEXITY_FIGURE, dpi=160)
    plt.close()


def run_feature_tier_experiment() -> pd.DataFrame:
    """Run fixed and equal-tuning Decision Tree experiments."""

    tiers = build_research_tiers()
    save_research_tier_artifacts(tiers)
    performance_records: list[dict[str, Any]] = []
    prediction_frames: list[pd.DataFrame] = []

    for tier_name in ["A", "B", "C", "D-matched", "E"]:
        for track in ["fixed_tree", "equal_tuning"]:
            print(f"Running {track} for Tier {tier_name}...")
            result, test_predictions = run_track_for_tier(tiers, tier_name, track)
            performance_records.append(result)
            prediction_frames.append(test_predictions)

    performance = pd.DataFrame(performance_records)
    predictions = pd.concat(prediction_frames, ignore_index=True)

    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    performance.to_csv(FEATURE_TIER_PERFORMANCE_CSV, index=False)
    predictions.to_csv(FEATURE_TIER_TEST_PREDICTIONS_CSV, index=False)

    with FEATURE_TIER_PERFORMANCE_JSON.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "fixed_tree_params": FIXED_TREE_PARAMS,
                "tuning_param_grid": TUNING_PARAM_GRID,
                "tuning_scoring": "phishing_f1_pos_label_0",
                "tuning_cv": "StratifiedKFold(n_splits=3, shuffle=True, random_state=42)",
                "test_data_used_for_model_selection": False,
                "split_indices_file": str(RESEARCH_SPLIT_INDICES_FILE),
                "tier_summary_file": str(RESEARCH_TIER_SUMMARY_FILE),
                "results": performance_records,
                "safety_statement": (
                    "The experiment used local feature matrices only and did "
                    "not contact any URL."
                ),
            },
            file,
            indent=2,
        )
        file.write("\n")

    save_performance_figures(performance)

    return performance


def main() -> None:
    """Run the feature-tier Decision Tree experiment."""

    performance = run_feature_tier_experiment()
    print(f"Saved: {FEATURE_TIER_PERFORMANCE_CSV}")
    print(f"Saved: {FEATURE_TIER_PERFORMANCE_JSON}")
    print(f"Saved: {FEATURE_TIER_TEST_PREDICTIONS_CSV}")
    print(
        performance[
            [
                "tier",
                "track",
                "test_accuracy",
                "phishing_recall",
                "phishing_f1",
                "tree_depth",
                "number_of_leaves",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
