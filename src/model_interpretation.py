"""Generate interpretation artifacts for the optimized Decision Tree."""

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.tree import plot_tree

from src.config import (
    DECISION_TREE_PREVIEW_FIGURE,
    FEATURE_IMPORTANCE_FIGURE,
    FEATURE_IMPORTANCE_FILE,
    OPTIMIZED_MODEL_FILE,
    create_project_directories,
)
from src.feature_definitions import FEATURE_NAMES


CLASS_NAMES = ["Phishing", "Legitimate"]


def load_optimized_model():
    """Load the optimized Decision Tree model artifact."""

    return joblib.load(OPTIMIZED_MODEL_FILE)


def build_feature_importance_table(model) -> pd.DataFrame:
    """Return a sorted feature importance table."""

    table = pd.DataFrame(
        {
            "feature": FEATURE_NAMES,
            "importance": model.feature_importances_,
        }
    )

    return table.sort_values("importance", ascending=False).reset_index(drop=True)


def save_feature_importance_figure(importance_table: pd.DataFrame) -> None:
    """Save a readable bar chart of the most important features."""

    top_features = importance_table.head(15).iloc[::-1]

    plt.figure(figsize=(9, 6))
    plt.barh(top_features["feature"], top_features["importance"], color="#4c72b0")
    plt.title("Top Decision Tree feature importances")
    plt.xlabel("Importance")
    plt.tight_layout()
    plt.savefig(FEATURE_IMPORTANCE_FIGURE, dpi=150)
    plt.close()


def save_tree_preview(model) -> None:
    """Save a simplified top-level Decision Tree visualization."""

    plt.figure(figsize=(18, 10))
    plot_tree(
        model,
        feature_names=FEATURE_NAMES,
        class_names=CLASS_NAMES,
        max_depth=3,
        filled=True,
        rounded=True,
        fontsize=8,
    )
    plt.title("Optimized Decision Tree preview, first 3 levels")
    plt.tight_layout()
    plt.savefig(DECISION_TREE_PREVIEW_FIGURE, dpi=150)
    plt.close()


def generate_interpretation_artifacts() -> pd.DataFrame:
    """Generate feature importance and tree preview artifacts."""

    model = load_optimized_model()
    importance_table = build_feature_importance_table(model)

    create_project_directories()
    importance_table.to_csv(FEATURE_IMPORTANCE_FILE, index=False)
    save_feature_importance_figure(importance_table)
    save_tree_preview(model)

    return importance_table


def main() -> None:
    """Run model interpretation artifact generation."""

    importance_table = generate_interpretation_artifacts()

    print("Top 10 feature importances:")
    print(importance_table.head(10).to_string(index=False))
    print(f"Feature importance saved to: {FEATURE_IMPORTANCE_FILE}")
    print(f"Feature importance figure saved to: {FEATURE_IMPORTANCE_FIGURE}")
    print(f"Decision Tree preview saved to: {DECISION_TREE_PREVIEW_FIGURE}")


if __name__ == "__main__":
    main()
