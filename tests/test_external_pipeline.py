"""Tests for external URL-Phish preparation and evaluation helpers."""

import inspect

import pandas as pd

from src.feature_definitions import FEATURE_NAMES
from src.external_sensitivity_analysis import (
    balanced_sensitivity_records,
    build_balanced_sample,
    metrics_for_predictions,
)
from src.analyze_class_conditional_shift import class_conditional_shift
from src.run_dataset_origin_experiment import (
    EXTERNAL_ORIGIN_LABEL,
    INTERNAL_ORIGIN_LABEL,
    build_origin_dataset,
)
from src.external_overlap_sensitivity import (
    conflicting_duplicate_urls,
    deduplicated_row_indices,
)
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


def test_balanced_sensitivity_sampling_is_deterministic() -> None:
    """The same seed should produce the same balanced external row set."""

    predictions = pd.DataFrame(
        {
            "row_index": range(8),
            "actual_label": [0, 0, 1, 1, 1, 1, 1, 1],
            "predicted_label": [0, 1, 1, 0, 1, 1, 0, 1],
            "phishing_probability": [0.9, 0.4, 0.1, 0.8, 0.2, 0.3, 0.7, 0.1],
        }
    )

    first = build_balanced_sample(predictions, seed=42)
    second = build_balanced_sample(predictions, seed=42)

    assert first["row_index"].tolist() == second["row_index"].tolist()
    assert len(first[first["actual_label"] == 0]) == 2
    assert len(first[first["actual_label"] == 1]) == 2


def test_balanced_sample_recall_matches_full_when_all_phishing_retained() -> None:
    """Balanced recall should match full recall because all phishing rows remain."""

    predictions = pd.DataFrame(
        {
            "row_index": range(8),
            "actual_label": [0, 0, 1, 1, 1, 1, 1, 1],
            "predicted_label": [0, 1, 1, 0, 1, 1, 0, 1],
            "phishing_probability": [0.9, 0.4, 0.1, 0.8, 0.2, 0.3, 0.7, 0.1],
        }
    )
    balanced = build_balanced_sample(predictions, seed=42)

    assert (
        metrics_for_predictions(predictions)["phishing_recall"]
        == metrics_for_predictions(balanced)["phishing_recall"]
    )


def test_balanced_sensitivity_records_include_summary_safe_schema() -> None:
    """Sensitivity outputs should be aggregate rows with no URL fields."""

    predictions = pd.DataFrame(
        {
            "row_index": range(12),
            "actual_label": [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            "predicted_label": [0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1],
            "phishing_probability": [
                0.9,
                0.4,
                0.8,
                0.1,
                0.7,
                0.3,
                0.2,
                0.6,
                0.1,
                0.2,
                0.8,
                0.1,
            ],
        }
    )

    records = balanced_sensitivity_records(predictions)

    assert records[0]["analysis"] == "full_external"
    assert all("url" not in record for record in records)


def test_class_conditional_shift_uses_correct_project_labels() -> None:
    """Legitimate/benign and phishing groups should use normalized project labels."""

    internal = pd.DataFrame(
        {
            **{feature: [1, 2, 10, 20] for feature in FEATURE_NAMES},
            "label": [1, 1, 0, 0],
        }
    )
    external = pd.DataFrame(
        {
            **{feature: [3, 4, 30, 40] for feature in FEATURE_NAMES},
            "target": [1, 1, 0, 0],
        }
    )

    result = class_conditional_shift(internal, external)
    benign_row = result[
        (result["comparison"] == "legitimate_vs_benign")
        & (result["feature"] == FEATURE_NAMES[0])
    ].iloc[0]
    phishing_row = result[
        (result["comparison"] == "phishing_vs_phishing")
        & (result["feature"] == FEATURE_NAMES[0])
    ].iloc[0]

    assert benign_row["source_mean"] == 1.5
    assert benign_row["external_mean"] == 3.5
    assert phishing_row["source_mean"] == 15.0
    assert phishing_row["external_mean"] == 35.0


def test_dataset_origin_labels_are_not_phishing_labels() -> None:
    """Origin labels should encode source dataset, not phishing semantics."""

    assert INTERNAL_ORIGIN_LABEL == 0
    assert EXTERNAL_ORIGIN_LABEL == 1


def test_origin_experiment_balances_source_classes() -> None:
    """Origin diagnostics should downsample the larger source class."""

    internal = pd.DataFrame(
        {
            **{feature: [1, 2, 3, 4] for feature in FEATURE_NAMES},
            "label": [1, 1, 1, 0],
        }
    )
    external = pd.DataFrame(
        {
            **{feature: [5, 6] for feature in FEATURE_NAMES},
            "target": [1, 1],
        }
    )

    x, y, counts = build_origin_dataset(internal, external, semantic_label=1)

    assert len(x) == 4
    assert y.value_counts().to_dict() == {
        INTERNAL_ORIGIN_LABEL: 2,
        EXTERNAL_ORIGIN_LABEL: 2,
    }
    assert counts["balanced_internal_rows"] == 2
    assert counts["balanced_external_rows"] == 2


def test_duplicate_conflict_handling_excludes_ambiguous_urls() -> None:
    """Deduplication sensitivity should not choose among conflicting labels."""

    raw = pd.DataFrame(
        {
            "url": ["safe-a", "safe-a", "safe-b", "safe-b", "safe-c"],
            "label": [0, 1, 1, 1, 0],
        }
    )

    conflicts = conflicting_duplicate_urls(raw)
    kept_indices, diagnostics = deduplicated_row_indices(raw)

    assert conflicts == {"safe-a"}
    assert kept_indices == [2, 4]
    assert diagnostics["conflicting_duplicate_url_values"] == 1
    assert diagnostics["rows_with_conflicting_duplicate_url"] == 2
