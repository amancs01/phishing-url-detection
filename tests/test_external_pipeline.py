"""Tests for external URL-Phish preparation and evaluation helpers."""

import inspect

import pandas as pd

from src.feature_definitions import FEATURE_NAMES
from src.prepare_external_data import (
    TARGET_COLUMN,
    build_external_feature_matrix,
    normalize_url_phish_labels,
    summarize_external_dataset,
)
from src.run_external_validation import (
    calculate_external_metrics,
    phishing_probability_from_proba,
)


def test_url_phish_label_1_becomes_project_phishing_label_0() -> None:
    """URL-Phish phishing labels should invert into the project convention."""

    labels = pd.Series([1])

    assert normalize_url_phish_labels(labels).tolist() == [0]


def test_url_phish_label_0_becomes_project_legitimate_label_1() -> None:
    """URL-Phish benign labels should invert into the project convention."""

    labels = pd.Series([0])

    assert normalize_url_phish_labels(labels).tolist() == [1]


def test_external_feature_names_exact_order() -> None:
    """External matrices should use the exact Tier E feature order."""

    data = pd.DataFrame(
        {
            "url": ["https://example.com", "example.org/login"],
            "label": [0, 1],
        }
    )

    matrix = build_external_feature_matrix(data)

    assert list(matrix.columns) == FEATURE_NAMES + [TARGET_COLUMN]


def test_external_summary_contains_no_raw_urls() -> None:
    """Committed external summaries should not expose raw URL strings."""

    data = pd.DataFrame(
        {
            "url": ["https://example.com", "example.org/login"],
            "label": [0, 1],
            "url_len": [19, 17],
        }
    )
    matrix = build_external_feature_matrix(data)
    summary = summarize_external_dataset(data, matrix)
    summary_text = str(summary)

    assert "example.com" not in summary_text
    assert "example.org" not in summary_text
    assert summary["used_source_columns_for_features"] == ["url"]
    assert summary["ignored_url_phish_supplied_feature_columns"] == ["url_len"]


def test_external_prepare_code_has_no_per_url_network_dependency() -> None:
    """Preparation should parse URL strings locally instead of contacting hosts."""

    import src.prepare_external_data as prepare_external_data

    source = inspect.getsource(prepare_external_data)
    banned_snippets = [
        "requests",
        "urllib.request",
        "selenium",
        "playwright",
        "socket",
        "whois",
        "urlopen",
        ".resolve(",
        "gethostby",
    ]

    for snippet in banned_snippets:
        assert snippet not in source


def test_prediction_workflow_does_not_call_fit() -> None:
    """External evaluation should never update the selected model."""

    import src.run_external_validation as run_external_validation

    source = inspect.getsource(run_external_validation)

    assert ".fit(" not in source


def test_phishing_probability_uses_class_0_column() -> None:
    """Class probability lookup should inspect classes_ instead of assuming order."""

    class FakeModel:
        classes_ = pd.Series([1, 0]).to_numpy()

    probabilities = pd.DataFrame([[0.2, 0.8], [0.7, 0.3]]).to_numpy()

    assert phishing_probability_from_proba(FakeModel(), probabilities).tolist() == [
        0.8,
        0.3,
    ]


def test_external_metrics_interpret_phishing_as_positive_class() -> None:
    """Precision, recall, and F1 should use project phishing label 0."""

    y_true = pd.Series([0, 0, 1, 1])
    y_pred = pd.Series([0, 1, 0, 1])
    phishing_probability = pd.Series([0.9, 0.4, 0.8, 0.1])

    metrics = calculate_external_metrics(y_true, y_pred, phishing_probability)

    assert metrics["phishing_precision"] == 0.5
    assert metrics["phishing_recall"] == 0.5
    assert metrics["phishing_f1"] == 0.5
    assert metrics["confusion_matrix"] == [[1, 1], [1, 1]]


def test_committed_external_metrics_have_no_raw_urls() -> None:
    """Committed external metrics should contain aggregates, not raw URL strings."""

    from src.config import EXTERNAL_VALIDATION_METRICS_FILE

    if not EXTERNAL_VALIDATION_METRICS_FILE.exists():
        return

    text = EXTERNAL_VALIDATION_METRICS_FILE.read_text(encoding="utf-8")

    assert "http://" not in text
    assert "https://" not in text
    assert "www." not in text
