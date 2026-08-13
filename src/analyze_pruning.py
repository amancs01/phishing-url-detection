"""Analyze Decision Tree cost-complexity pruning."""

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

from src.config import (
    BEST_PARAMETERS_FILE,
    PRUNING_COMPLEXITY_FIGURE,
    PRUNING_F1_FIGURE,
    PRUNING_RESULTS_FILE,
    RANDOM_STATE,
    create_project_directories,
)
from src.evaluate import evaluate_model
from src.inspect_data import find_target_column
from src.train_baseline import load_split, split_features_and_target
from src.split_data import TRAIN_FILE, VALIDATION_FILE


MAX_ALPHA_VALUES = 25


def load_best_parameters() -> dict:
    """Load tuned Decision Tree parameters from the tuning summary."""

    summary = json.loads(BEST_PARAMETERS_FILE.read_text(encoding="utf-8"))
    return summary["best_parameters"]


def select_representative_alphas(alphas: np.ndarray) -> np.ndarray:
    """Return a manageable sorted subset of pruning alpha values."""

    unique_alphas = np.unique(alphas)

    if len(unique_alphas) <= MAX_ALPHA_VALUES:
        return unique_alphas

    positions = np.linspace(0, len(unique_alphas) - 1, MAX_ALPHA_VALUES, dtype=int)
    return unique_alphas[positions]


def analyze_pruning() -> pd.DataFrame:
    """Evaluate pruned Decision Trees across representative ccp_alpha values."""

    train_data = load_split(TRAIN_FILE)
    validation_data = load_split(VALIDATION_FILE)
    target_column = find_target_column(train_data)

    x_train, y_train = split_features_and_target(train_data, target_column)
    x_validation, y_validation = split_features_and_target(
        validation_data,
        target_column,
    )

    best_parameters = load_best_parameters()
    base_model = DecisionTreeClassifier(
        **best_parameters,
        random_state=RANDOM_STATE,
    )
    pruning_path = base_model.cost_complexity_pruning_path(x_train, y_train)
    alphas = select_representative_alphas(pruning_path.ccp_alphas)

    results = []

    for ccp_alpha in alphas:
        model = DecisionTreeClassifier(
            **best_parameters,
            ccp_alpha=float(ccp_alpha),
            random_state=RANDOM_STATE,
        )
        model.fit(x_train, y_train)

        training_metrics = evaluate_model(model, x_train, y_train)
        validation_metrics = evaluate_model(model, x_validation, y_validation)

        results.append(
            {
                "ccp_alpha": float(ccp_alpha),
                "training_accuracy": training_metrics["accuracy"],
                "validation_accuracy": validation_metrics["accuracy"],
                "training_f1_phishing": training_metrics["f1_phishing"],
                "validation_f1_phishing": validation_metrics["f1_phishing"],
                "tree_depth": int(model.get_depth()),
                "leaves": int(model.get_n_leaves()),
            }
        )

    results_dataframe = pd.DataFrame(results)
    create_project_directories()
    results_dataframe.to_csv(PRUNING_RESULTS_FILE, index=False)

    return results_dataframe


def save_pruning_figures(results: pd.DataFrame) -> None:
    """Save pruning F1 and complexity figures."""

    plt.figure(figsize=(8, 5))
    plt.plot(
        results["ccp_alpha"],
        results["training_f1_phishing"],
        marker="o",
        label="Training",
    )
    plt.plot(
        results["ccp_alpha"],
        results["validation_f1_phishing"],
        marker="o",
        label="Validation",
    )
    plt.title("Cost-complexity pruning vs phishing F1-score")
    plt.xlabel("ccp_alpha")
    plt.ylabel("F1-score for phishing")
    plt.xscale("symlog", linthresh=1e-8)
    plt.legend()
    plt.tight_layout()
    plt.savefig(PRUNING_F1_FIGURE, dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.plot(results["ccp_alpha"], results["tree_depth"], marker="o", label="Depth")
    plt.plot(results["ccp_alpha"], results["leaves"], marker="o", label="Leaves")
    plt.title("Cost-complexity pruning vs tree complexity")
    plt.xlabel("ccp_alpha")
    plt.ylabel("Complexity")
    plt.xscale("symlog", linthresh=1e-8)
    plt.legend()
    plt.tight_layout()
    plt.savefig(PRUNING_COMPLEXITY_FIGURE, dpi=150)
    plt.close()


def main() -> None:
    """Run pruning analysis."""

    results = analyze_pruning()
    save_pruning_figures(results)

    print(results.round(6).to_string(index=False))
    best_row = results.loc[results["validation_f1_phishing"].idxmax()]
    print(
        "Best validation phishing F1 in pruning analysis: "
        f"ccp_alpha={best_row['ccp_alpha']:.10f}, "
        f"validation_f1={best_row['validation_f1_phishing']:.4f}"
    )
    print(f"Pruning results saved to: {PRUNING_RESULTS_FILE}")
    print(f"F1 figure saved to: {PRUNING_F1_FIGURE}")
    print(f"Complexity figure saved to: {PRUNING_COMPLEXITY_FIGURE}")


if __name__ == "__main__":
    main()
