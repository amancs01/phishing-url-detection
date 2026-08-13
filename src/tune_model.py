"""Tune Decision Tree hyperparameters using training data only."""

import json

import pandas as pd
from sklearn.metrics import f1_score, make_scorer
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.tree import DecisionTreeClassifier

from src.config import (
    BEST_PARAMETERS_FILE,
    RANDOM_STATE,
    TUNING_RESULTS_FILE,
    create_project_directories,
)
from src.evaluate import PHISHING_LABEL
from src.train_baseline import load_split, split_features_and_target
from src.split_data import TRAIN_FILE
from src.inspect_data import find_target_column


CV_FOLDS = 3
PARAMETER_GRID = {
    "criterion": ["gini", "entropy"],
    "max_depth": [4, 6, 8, 10, 12, 18],
    "min_samples_split": [2, 10, 20],
    "min_samples_leaf": [1, 5, 10],
}


def count_candidate_configurations(parameter_grid: dict) -> int:
    """Count the number of parameter combinations in a grid."""

    total = 1
    for values in parameter_grid.values():
        total *= len(values)
    return total


def tune_decision_tree() -> tuple[GridSearchCV, pd.DataFrame, dict]:
    """Run a phishing-F1-focused grid search on the training split."""

    train_data = load_split(TRAIN_FILE)
    target_column = find_target_column(train_data)
    features, target = split_features_and_target(train_data, target_column)

    phishing_f1_scorer = make_scorer(f1_score, pos_label=PHISHING_LABEL)
    cross_validator = StratifiedKFold(
        n_splits=CV_FOLDS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    search = GridSearchCV(
        estimator=DecisionTreeClassifier(random_state=RANDOM_STATE),
        param_grid=PARAMETER_GRID,
        scoring=phishing_f1_scorer,
        cv=cross_validator,
        n_jobs=-1,
        return_train_score=True,
    )
    search.fit(features, target)

    results = pd.DataFrame(search.cv_results_).sort_values(
        "rank_test_score",
        ascending=True,
    )

    best_summary = {
        "algorithm": "DecisionTreeClassifier",
        "scoring": "f1_score with phishing as the positive class",
        "positive_label": PHISHING_LABEL,
        "cross_validation_folds": CV_FOLDS,
        "candidate_configurations": count_candidate_configurations(PARAMETER_GRID),
        "best_parameters": search.best_params_,
        "best_mean_cv_phishing_f1": float(search.best_score_),
    }

    create_project_directories()
    results.to_csv(TUNING_RESULTS_FILE, index=False)
    BEST_PARAMETERS_FILE.write_text(
        json.dumps(best_summary, indent=2),
        encoding="utf-8",
    )

    return search, results, best_summary


def main() -> None:
    """Run Decision Tree hyperparameter tuning."""

    _, _, best_summary = tune_decision_tree()

    print(
        "Candidate configurations: "
        f"{best_summary['candidate_configurations']}"
    )
    print(f"Cross-validation folds: {best_summary['cross_validation_folds']}")
    print(f"Best parameters: {best_summary['best_parameters']}")
    print(
        "Best mean CV phishing F1: "
        f"{best_summary['best_mean_cv_phishing_f1']:.4f}"
    )
    print(f"Tuning results saved to: {TUNING_RESULTS_FILE}")
    print(f"Best parameter summary saved to: {BEST_PARAMETERS_FILE}")


if __name__ == "__main__":
    main()
