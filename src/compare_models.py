"""Compare baseline and optimized Decision Tree models after selection."""

import json

import joblib
import pandas as pd

from src.config import (
    BASELINE_METRICS_FILE,
    BASELINE_MODEL_FILE,
    FINAL_TEST_METRICS_FILE,
    MODEL_METADATA_FILE,
    OPTIMIZED_MODEL_FILE,
    RESULTS_DIRECTORY,
    create_project_directories,
)
from src.evaluate import evaluate_model
from src.inspect_data import find_target_column
from src.train_baseline import load_split, split_features_and_target
from src.split_data import TEST_FILE, TRAIN_FILE, VALIDATION_FILE


MODEL_COMPARISON_FILE = RESULTS_DIRECTORY / "model_comparison.csv"


def summarize_model(
    model_name: str,
    model,
    train_data: pd.DataFrame,
    validation_data: pd.DataFrame,
    test_data: pd.DataFrame,
) -> dict:
    """Return train, validation, and test metrics for one fitted model."""

    target_column = find_target_column(train_data)
    x_train, y_train = split_features_and_target(train_data, target_column)
    x_validation, y_validation = split_features_and_target(
        validation_data,
        target_column,
    )
    x_test, y_test = split_features_and_target(test_data, target_column)

    training_metrics = evaluate_model(model, x_train, y_train)
    validation_metrics = evaluate_model(model, x_validation, y_validation)
    test_metrics = evaluate_model(model, x_test, y_test)

    return {
        "model": model_name,
        "training_accuracy": training_metrics["accuracy"],
        "validation_accuracy": validation_metrics["accuracy"],
        "final_test_accuracy": test_metrics["accuracy"],
        "final_test_precision_phishing": test_metrics["precision_phishing"],
        "final_test_recall_phishing": test_metrics["recall_phishing"],
        "final_test_f1_phishing": test_metrics["f1_phishing"],
        "final_test_roc_auc_phishing": test_metrics["roc_auc_phishing"],
        "tree_depth": int(model.get_depth()),
        "leaves": int(model.get_n_leaves()),
    }


def compare_models() -> pd.DataFrame:
    """Compare baseline and optimized models after model selection."""

    baseline_model = joblib.load(BASELINE_MODEL_FILE)
    optimized_model = joblib.load(OPTIMIZED_MODEL_FILE)

    train_data = load_split(TRAIN_FILE)
    validation_data = load_split(VALIDATION_FILE)
    test_data = load_split(TEST_FILE)

    comparison = pd.DataFrame(
        [
            summarize_model(
                "baseline_unrestricted_decision_tree",
                baseline_model,
                train_data,
                validation_data,
                test_data,
            ),
            summarize_model(
                "optimized_decision_tree",
                optimized_model,
                train_data,
                validation_data,
                test_data,
            ),
        ]
    )

    create_project_directories()
    comparison.to_csv(MODEL_COMPARISON_FILE, index=False)

    return comparison


def main() -> None:
    """Run the model comparison workflow."""

    comparison = compare_models()

    print(comparison.round(4).to_string(index=False))
    print(
        "Comparison was performed after model selection; test results were not "
        "used to change the optimized model."
    )
    print(f"Model comparison saved to: {MODEL_COMPARISON_FILE}")
    print(f"Baseline metrics source: {BASELINE_METRICS_FILE}")
    print(f"Optimized metadata source: {MODEL_METADATA_FILE}")
    print(f"Final test metrics source: {FINAL_TEST_METRICS_FILE}")


if __name__ == "__main__":
    main()
