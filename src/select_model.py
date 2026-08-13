"""Select and refit the optimized Decision Tree model."""

import json
from datetime import datetime, timezone

import joblib
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

from src.config import (
    BEST_PARAMETERS_FILE,
    MODEL_METADATA_FILE,
    OPTIMIZED_MODEL_FILE,
    PRUNING_RESULTS_FILE,
    RANDOM_STATE,
    create_project_directories,
)
from src.evaluate import evaluate_model
from src.feature_definitions import FEATURE_NAMES
from src.inspect_data import find_target_column
from src.train_baseline import load_split, split_features_and_target
from src.split_data import TRAIN_FILE, VALIDATION_FILE


DATASET_NAME = "UCI PhiUSIIL Phishing URL Dataset"
LABEL_MEANINGS = {
    "0": "phishing",
    "1": "legitimate",
}


def load_tuning_summary() -> dict:
    """Load the best parameters selected by cross-validation."""

    return json.loads(BEST_PARAMETERS_FILE.read_text(encoding="utf-8"))


def select_ccp_alpha() -> float:
    """Select pruning alpha using validation phishing F1 from pruning analysis."""

    pruning_results = pd.read_csv(PRUNING_RESULTS_FILE)
    best_row = pruning_results.loc[pruning_results["validation_f1_phishing"].idxmax()]
    return float(best_row["ccp_alpha"])


def build_selected_parameters() -> dict:
    """Combine tuned hyperparameters with the selected pruning value."""

    tuning_summary = load_tuning_summary()
    selected_parameters = dict(tuning_summary["best_parameters"])
    selected_parameters["ccp_alpha"] = select_ccp_alpha()
    selected_parameters["random_state"] = RANDOM_STATE
    return selected_parameters


def train_optimized_model() -> tuple[DecisionTreeClassifier, dict]:
    """Refit the selected model on combined training and validation data."""

    train_data = load_split(TRAIN_FILE)
    validation_data = load_split(VALIDATION_FILE)
    development_data = pd.concat([train_data, validation_data], axis=0)
    target_column = find_target_column(development_data)

    features, target = split_features_and_target(development_data, target_column)
    selected_parameters = build_selected_parameters()

    model = DecisionTreeClassifier(**selected_parameters)
    model.fit(features, target)

    development_metrics = evaluate_model(model, features, target)
    tuning_summary = load_tuning_summary()

    metadata = {
        "algorithm": "DecisionTreeClassifier",
        "dataset_name": DATASET_NAME,
        "feature_names": FEATURE_NAMES,
        "feature_count": len(FEATURE_NAMES),
        "selected_hyperparameters": selected_parameters,
        "random_state": RANDOM_STATE,
        "training_rows": int(len(development_data)),
        "development_training_source": "train.csv and validation.csv combined after model selection",
        "test_set_used_for_selection": False,
        "label_meanings": LABEL_MEANINGS,
        "positive_class": "phishing",
        "positive_label": 0,
        "selection_evidence": {
            "best_cross_validation_phishing_f1": tuning_summary[
                "best_mean_cv_phishing_f1"
            ],
            "pruning_selection_rule": (
                "Choose the ccp_alpha with the best validation phishing F1 "
                "from pruning_analysis.csv before final test evaluation."
            ),
        },
        "development_training_metrics": development_metrics,
        "tree_depth": int(model.get_depth()),
        "leaves": int(model.get_n_leaves()),
        "safety_statement": (
            "The model uses only URL-text features generated locally and never "
            "requires opening, requesting, resolving, or contacting a URL."
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    create_project_directories()
    joblib.dump(model, OPTIMIZED_MODEL_FILE)
    MODEL_METADATA_FILE.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    return model, metadata


def main() -> None:
    """Run optimized model selection and refitting."""

    _, metadata = train_optimized_model()

    print("Optimized Decision Tree selected and trained.")
    print(f"Selected hyperparameters: {metadata['selected_hyperparameters']}")
    print(f"Training rows: {metadata['training_rows']:,}")
    print(f"Tree depth: {metadata['tree_depth']}")
    print(f"Leaves: {metadata['leaves']}")
    print(f"Model saved to: {OPTIMIZED_MODEL_FILE}")
    print(f"Metadata saved to: {MODEL_METADATA_FILE}")


if __name__ == "__main__":
    main()
