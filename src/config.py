"""Central configuration values for the phishing URL detection project."""

from pathlib import Path


# Project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIRECTORY = PROJECT_ROOT / "data"
RAW_DATA_DIRECTORY = DATA_DIRECTORY / "raw"
PROCESSED_DATA_DIRECTORY = DATA_DIRECTORY / "processed"

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


# Model settings
RANDOM_STATE = 42
TEST_SIZE = 0.15
VALIDATION_SIZE = 0.15

MODEL_FILE = MODEL_DIRECTORY / "decision_tree_model.joblib"
MODEL_METADATA_FILE = MODEL_DIRECTORY / "model_metadata.json"
BASELINE_MODEL_FILE = MODEL_DIRECTORY / "baseline_decision_tree.joblib"
BASELINE_METRICS_FILE = RESULTS_DIRECTORY / "baseline_model_metrics.json"
BASELINE_CONFUSION_MATRIX_FILE = (
    FIGURES_DIRECTORY / "baseline_validation_confusion_matrix.png"
)


def create_project_directories() -> None:
    """Create project directories required by scripts."""

    directories = [
        RAW_DATA_DIRECTORY,
        PROCESSED_DATA_DIRECTORY,
        MODEL_DIRECTORY,
        RESULTS_DIRECTORY,
        REPORTS_DIRECTORY,
        FIGURES_DIRECTORY,
        NOTEBOOKS_DIRECTORY,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
