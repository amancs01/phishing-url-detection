"""Compare Decision Tree performance across max_depth values."""

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier

from src.config import FIGURES_DIRECTORY, RANDOM_STATE, create_project_directories
from src.evaluate import evaluate_model
from src.feature_definitions import FEATURE_NAMES
from src.inspect_data import find_target_column
from src.train_baseline import load_split, split_features_and_target
from src.split_data import TRAIN_FILE, VALIDATION_FILE


DEPTH_VALUES = list(range(1, 26))
DEPTH_ACCURACY_FIGURE = FIGURES_DIRECTORY / "tree_depth_accuracy.png"
DEPTH_F1_FIGURE = FIGURES_DIRECTORY / "tree_depth_f1.png"


def compare_tree_depths(depth_values: list[int] | None = None) -> pd.DataFrame:
    """Train Decision Trees across depths and return metric results."""

    if depth_values is None:
        depth_values = DEPTH_VALUES

    train_data = load_split(TRAIN_FILE)
    validation_data = load_split(VALIDATION_FILE)
    target_column = find_target_column(train_data)

    x_train, y_train = split_features_and_target(train_data, target_column)
    x_validation, y_validation = split_features_and_target(
        validation_data,
        target_column,
    )

    results = []

    for max_depth in depth_values:
        model = DecisionTreeClassifier(
            max_depth=max_depth,
            random_state=RANDOM_STATE,
        )
        model.fit(x_train, y_train)

        training_metrics = evaluate_model(model, x_train, y_train)
        validation_metrics = evaluate_model(model, x_validation, y_validation)

        results.append(
            {
                "max_depth": max_depth,
                "training_accuracy": training_metrics["accuracy"],
                "validation_accuracy": validation_metrics["accuracy"],
                "training_f1_phishing": training_metrics["f1_phishing"],
                "validation_f1_phishing": validation_metrics["f1_phishing"],
                "tree_depth": int(model.get_depth()),
                "leaves": int(model.get_n_leaves()),
            }
        )

    return pd.DataFrame(results)


def save_depth_figures(results: pd.DataFrame) -> None:
    """Save accuracy and phishing F1-score comparison plots."""

    create_project_directories()

    plt.figure(figsize=(8, 5))
    plt.plot(results["max_depth"], results["training_accuracy"], marker="o", label="Training")
    plt.plot(
        results["max_depth"],
        results["validation_accuracy"],
        marker="o",
        label="Validation",
    )
    plt.title("Decision Tree depth vs accuracy")
    plt.xlabel("max_depth")
    plt.ylabel("Accuracy")
    plt.xticks(results["max_depth"])
    plt.legend()
    plt.tight_layout()
    plt.savefig(DEPTH_ACCURACY_FIGURE, dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.plot(
        results["max_depth"],
        results["training_f1_phishing"],
        marker="o",
        label="Training",
    )
    plt.plot(
        results["max_depth"],
        results["validation_f1_phishing"],
        marker="o",
        label="Validation",
    )
    plt.title("Decision Tree depth vs phishing F1-score")
    plt.xlabel("max_depth")
    plt.ylabel("F1-score for phishing")
    plt.xticks(results["max_depth"])
    plt.legend()
    plt.tight_layout()
    plt.savefig(DEPTH_F1_FIGURE, dpi=150)
    plt.close()


def main() -> None:
    """Run the depth comparison workflow."""

    results = compare_tree_depths()
    save_depth_figures(results)

    print(results.round(4).to_string(index=False))

    best_row = results.loc[results["validation_f1_phishing"].idxmax()]
    print(
        "Best validation phishing F1 in this range: "
        f"max_depth={int(best_row['max_depth'])}, "
        f"validation_f1={best_row['validation_f1_phishing']:.4f}"
    )
    print(f"Accuracy figure saved to: {DEPTH_ACCURACY_FIGURE}")
    print(f"F1 figure saved to: {DEPTH_F1_FIGURE}")


if __name__ == "__main__":
    main()
