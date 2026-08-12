"""Train the baseline Decision Tree classifier."""

import json

import joblib
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

from src.config import (
    BASELINE_METRICS_FILE,
    BASELINE_MODEL_FILE,
    RANDOM_STATE,
    create_project_directories,
)
from src.evaluate import evaluate_model
from src.feature_definitions import FEATURE_NAMES
from src.inspect_data import find_target_column
from src.split_data import TRAIN_FILE, VALIDATION_FILE


def load_split(path) -> pd.DataFrame:
    """Load a saved split while preserving its source index."""

    return pd.read_csv(path, index_col=0)


def split_features_and_target(
    dataframe: pd.DataFrame,
    target_column: str,
) -> tuple[pd.DataFrame, pd.Series]:
    """Return model features and target labels."""

    return dataframe[FEATURE_NAMES], dataframe[target_column]


def train_baseline_model() -> tuple[DecisionTreeClassifier, dict]:
    """Train and evaluate the unrestricted baseline Decision Tree."""

    train_data = load_split(TRAIN_FILE)
    validation_data = load_split(VALIDATION_FILE)
    target_column = find_target_column(train_data)

    x_train, y_train = split_features_and_target(train_data, target_column)
    x_validation, y_validation = split_features_and_target(
        validation_data,
        target_column,
    )

    model = DecisionTreeClassifier(random_state=RANDOM_STATE)
    model.fit(x_train, y_train)

    train_metrics = evaluate_model(model, x_train, y_train)
    validation_metrics = evaluate_model(model, x_validation, y_validation)

    metrics = {
        "algorithm": "DecisionTreeClassifier",
        "parameters": model.get_params(),
        "positive_class": "phishing",
        "positive_label": 0,
        "training_accuracy": train_metrics["accuracy"],
        "validation_accuracy": validation_metrics["accuracy"],
        "training_metrics": train_metrics,
        "validation_metrics": validation_metrics,
        "tree_depth": int(model.get_depth()),
        "leaves": int(model.get_n_leaves()),
        "training_samples": int(len(train_data)),
        "feature_count": int(len(FEATURE_NAMES)),
    }

    create_project_directories()
    joblib.dump(model, BASELINE_MODEL_FILE)
    BASELINE_METRICS_FILE.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )

    return model, metrics


def main() -> None:
    """Run baseline Decision Tree training."""

    _, metrics = train_baseline_model()

    print("Baseline Decision Tree trained.")
    print(f"Training accuracy: {metrics['training_accuracy']:.4f}")
    print(f"Validation accuracy: {metrics['validation_accuracy']:.4f}")
    print(
        "Validation phishing precision: "
        f"{metrics['validation_metrics']['precision_phishing']:.4f}"
    )
    print(
        "Validation phishing recall: "
        f"{metrics['validation_metrics']['recall_phishing']:.4f}"
    )
    print(
        "Validation phishing F1-score: "
        f"{metrics['validation_metrics']['f1_phishing']:.4f}"
    )
    print(
        "Validation phishing ROC-AUC: "
        f"{metrics['validation_metrics']['roc_auc_phishing']:.4f}"
    )
    print(f"Tree depth: {metrics['tree_depth']}")
    print(f"Number of leaves: {metrics['leaves']}")
    print(f"Training samples: {metrics['training_samples']:,}")
    print(f"Number of features: {metrics['feature_count']}")
    print(f"Model saved to: {BASELINE_MODEL_FILE}")
    print(f"Metrics saved to: {BASELINE_METRICS_FILE}")


if __name__ == "__main__":
    main()
