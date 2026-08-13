"""Evaluate the selected optimized model on the untouched test set."""

import json

import joblib

from src.config import (
    FINAL_TEST_CONFUSION_MATRIX_FILE,
    FINAL_TEST_METRICS_FILE,
    OPTIMIZED_MODEL_FILE,
    create_project_directories,
)
from src.evaluate import evaluate_model, plot_confusion_matrix
from src.inspect_data import find_target_column
from src.train_baseline import load_split, split_features_and_target
from src.split_data import TEST_FILE


def evaluate_optimized_model_on_test() -> dict:
    """Evaluate the optimized Decision Tree on the final test split once."""

    model = joblib.load(OPTIMIZED_MODEL_FILE)
    test_data = load_split(TEST_FILE)
    target_column = find_target_column(test_data)
    features, target = split_features_and_target(test_data, target_column)

    metrics = evaluate_model(model, features, target)
    predictions = model.predict(features)
    confusion_details = plot_confusion_matrix(
        target,
        predictions,
        FINAL_TEST_CONFUSION_MATRIX_FILE,
    )

    final_results = {
        "evaluation_split": "test",
        "model": "optimized_decision_tree",
        "positive_class": "phishing",
        "positive_label": 0,
        "test_rows": int(len(test_data)),
        "metrics": metrics,
        "confusion_matrix": confusion_details,
        "test_set_used_for_model_selection": False,
        "retuning_after_test_evaluation": False,
    }

    create_project_directories()
    FINAL_TEST_METRICS_FILE.write_text(
        json.dumps(final_results, indent=2),
        encoding="utf-8",
    )

    return final_results


def main() -> None:
    """Run final optimized model evaluation."""

    results = evaluate_optimized_model_on_test()
    metrics = results["metrics"]
    confusion_matrix = results["confusion_matrix"]

    print(f"Test accuracy: {metrics['accuracy']:.4f}")
    print(f"Test phishing precision: {metrics['precision_phishing']:.4f}")
    print(f"Test phishing recall: {metrics['recall_phishing']:.4f}")
    print(f"Test phishing F1-score: {metrics['f1_phishing']:.4f}")
    print(f"Test phishing ROC-AUC: {metrics['roc_auc_phishing']:.4f}")
    print(f"Confusion matrix: {confusion_matrix}")
    print(
        "Most security-sensitive error: "
        "actual phishing predicted legitimate"
    )
    print(f"Metrics saved to: {FINAL_TEST_METRICS_FILE}")
    print(f"Confusion matrix saved to: {FINAL_TEST_CONFUSION_MATRIX_FILE}")


if __name__ == "__main__":
    main()
