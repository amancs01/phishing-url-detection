"""Central configuration values for the phishing URL detection project."""

from pathlib import Path


# Project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIRECTORY = PROJECT_ROOT / "data"
RAW_DATA_DIRECTORY = DATA_DIRECTORY / "raw"
PROCESSED_DATA_DIRECTORY = DATA_DIRECTORY / "processed"
EXTERNAL_DATA_DIRECTORY = DATA_DIRECTORY / "external"
EXTERNAL_RAW_DATA_DIRECTORY = EXTERNAL_DATA_DIRECTORY / "raw"
EXTERNAL_PROCESSED_DATA_DIRECTORY = EXTERNAL_DATA_DIRECTORY / "processed"

MODEL_DIRECTORY = PROJECT_ROOT / "models"
RESULTS_DIRECTORY = PROJECT_ROOT / "results"
REPORTS_DIRECTORY = PROJECT_ROOT / "reports"
FIGURES_DIRECTORY = REPORTS_DIRECTORY / "figures"
NOTEBOOKS_DIRECTORY = PROJECT_ROOT / "notebooks"


# Dataset settings
UCI_DATASET_ID = 967
RAW_DATA_FILE = RAW_DATA_DIRECTORY / "phiusil_raw.csv"
PROCESSED_DATA_FILE = PROCESSED_DATA_DIRECTORY / "phiusil_url_features.csv"
DATASET_SCHEMA_FILE = RESULTS_DIRECTORY / "dataset_schema.json"
DATA_VALIDATION_FILE = RESULTS_DIRECTORY / "data_validation.json"


# External validation settings
URL_PHISH_DATASET_ID = "65z9twcx3r"
URL_PHISH_VERSION = 2
URL_PHISH_DOI = "10.17632/65z9twcx3r.2"
URL_PHISH_DATASET_NAME = (
    "URL-Phish: A Feature-Engineered Dataset for Phishing Detection"
)
URL_PHISH_RAW_FILE = EXTERNAL_RAW_DATA_DIRECTORY / "url_phish_v2_dataset.csv"
URL_PHISH_EXTERNAL_MATRIX_FILE = (
    EXTERNAL_PROCESSED_DATA_DIRECTORY / "url_phish_v2_tier_e_features.csv"
)
EXTERNAL_DATASET_SUMMARY_FILE = RESULTS_DIRECTORY / "external_dataset_summary.json"
LEGITPHISH_RAW_DATA_DIRECTORY = EXTERNAL_DATA_DIRECTORY / "legitphish" / "raw"
LEGITPHISH_PROCESSED_DATA_DIRECTORY = (
    EXTERNAL_DATA_DIRECTORY / "legitphish" / "processed"
)
LEGITPHISH_VERSION = 2
LEGITPHISH_DOI = "10.17632/hx4m73v2sf.2"
LEGITPHISH_RAW_FILE = LEGITPHISH_RAW_DATA_DIRECTORY / "legitphish_v2.csv"
LEGITPHISH_EXTERNAL_MATRIX_FILE = (
    LEGITPHISH_PROCESSED_DATA_DIRECTORY / "legitphish_v2_tier_e_features.csv"
)
LEGITPHISH_DATASET_SUMMARY_FILE = RESULTS_DIRECTORY / "legitphish_dataset_summary.json"
LEGITPHISH_VALIDATION_METRICS_FILE = (
    RESULTS_DIRECTORY / "legitphish_validation_metrics.json"
)
LEGITPHISH_SENSITIVITY_METRICS_FILE = (
    RESULTS_DIRECTORY / "legitphish_sensitivity_metrics.json"
)
LEGITPHISH_CONFUSION_MATRIX_FIGURE = (
    FIGURES_DIRECTORY / "legitphish_confusion_matrix.png"
)
THREE_DATASET_METRIC_COMPARISON_FIGURE = (
    FIGURES_DIRECTORY / "three_dataset_metric_comparison.png"
)
EXTERNAL_VALIDATION_METRICS_FILE = (
    RESULTS_DIRECTORY / "external_validation_metrics.json"
)
EXTERNAL_VALIDATION_PREDICTIONS_FILE = (
    RESULTS_DIRECTORY / "external_validation_predictions.csv"
)
EXTERNAL_CONFUSION_MATRIX_FIGURE = (
    FIGURES_DIRECTORY / "external_confusion_matrix.png"
)
INTERNAL_VS_EXTERNAL_METRICS_FIGURE = (
    FIGURES_DIRECTORY / "internal_vs_external_metrics.png"
)
EXTERNAL_SENSITIVITY_RESULTS_CSV = (
    RESULTS_DIRECTORY / "external_sensitivity_results.csv"
)
EXTERNAL_BOOTSTRAP_CI_FILE = RESULTS_DIRECTORY / "external_bootstrap_ci.json"
EXTERNAL_FULL_VS_BALANCED_FIGURE = (
    FIGURES_DIRECTORY / "external_full_vs_balanced.png"
)
EXTERNAL_FEATURE_SHIFT_FILE = RESULTS_DIRECTORY / "external_feature_shift.csv"
MULTI_DATASET_FEATURE_SHIFT_FILE = RESULTS_DIRECTORY / "multi_dataset_feature_shift.csv"
MULTI_DATASET_ORIGIN_PERFORMANCE_FILE = (
    RESULTS_DIRECTORY / "multi_dataset_origin_performance.json"
)
BENIGN_SHIFT_ACROSS_DATASETS_FIGURE = (
    FIGURES_DIRECTORY / "benign_shift_across_datasets.png"
)
PHISHING_SHIFT_ACROSS_DATASETS_FIGURE = (
    FIGURES_DIRECTORY / "phishing_shift_across_datasets.png"
)


# Model settings
RANDOM_STATE = 42
TEST_SIZE = 0.15
VALIDATION_SIZE = 0.15

MODEL_FILE = MODEL_DIRECTORY / "decision_tree_model.joblib"
MODEL_METADATA_FILE = MODEL_DIRECTORY / "model_metadata.json"
BASELINE_MODEL_FILE = MODEL_DIRECTORY / "baseline_decision_tree.joblib"
OPTIMIZED_MODEL_FILE = MODEL_DIRECTORY / "optimized_decision_tree.joblib"
BASELINE_METRICS_FILE = RESULTS_DIRECTORY / "baseline_model_metrics.json"
BASELINE_CONFUSION_MATRIX_FILE = (
    FIGURES_DIRECTORY / "baseline_validation_confusion_matrix.png"
)
TUNING_RESULTS_FILE = RESULTS_DIRECTORY / "decision_tree_tuning.csv"
BEST_PARAMETERS_FILE = RESULTS_DIRECTORY / "best_parameters.json"
PRUNING_RESULTS_FILE = RESULTS_DIRECTORY / "pruning_analysis.csv"
PRUNING_F1_FIGURE = FIGURES_DIRECTORY / "pruning_f1.png"
PRUNING_COMPLEXITY_FIGURE = FIGURES_DIRECTORY / "pruning_complexity.png"
FINAL_TEST_METRICS_FILE = RESULTS_DIRECTORY / "final_test_metrics.json"
FINAL_TEST_CONFUSION_MATRIX_FILE = (
    FIGURES_DIRECTORY / "final_test_confusion_matrix.png"
)
FEATURE_IMPORTANCE_FILE = RESULTS_DIRECTORY / "feature_importance.csv"
FEATURE_IMPORTANCE_FIGURE = FIGURES_DIRECTORY / "feature_importance.png"
DECISION_TREE_PREVIEW_FIGURE = FIGURES_DIRECTORY / "decision_tree_preview.png"


def create_project_directories() -> None:
    """Create project directories required by scripts."""

    directories = [
        RAW_DATA_DIRECTORY,
        PROCESSED_DATA_DIRECTORY,
        EXTERNAL_RAW_DATA_DIRECTORY,
        EXTERNAL_PROCESSED_DATA_DIRECTORY,
        LEGITPHISH_RAW_DATA_DIRECTORY,
        LEGITPHISH_PROCESSED_DATA_DIRECTORY,
        MODEL_DIRECTORY,
        RESULTS_DIRECTORY,
        REPORTS_DIRECTORY,
        FIGURES_DIRECTORY,
        NOTEBOOKS_DIRECTORY,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
