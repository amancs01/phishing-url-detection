"""Tests for the LegitPhish external validation pipeline."""

import inspect
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import LEGITPHISH_SENSITIVITY_METRICS_FILE, LEGITPHISH_VALIDATION_METRICS_FILE
from src.feature_definitions import FEATURE_NAMES
from src.prepare_external_data import TARGET_COLUMN
from src.prepare_legitphish_data import (
    LEGITPHISH_LABEL_MEANINGS,
    build_legitphish_feature_matrix,
    conflicting_duplicate_urls,
    summarize_legitphish_dataset,
)
from src.predict import LEGITIMATE_LABEL, PHISHING_LABEL
from src.run_external_validation import phishing_probability_from_proba
from src.run_legitphish_validation import load_selected_model


def test_legitphish_label_convention_remains_project_convention() -> None:
    """LegitPhish labels should already match 0 phishing and 1 legitimate."""

    assert LEGITPHISH_LABEL_MEANINGS == {
        0: "phishing",
        1: "legitimate",
    }


def test_legitphish_feature_names_exact_order() -> None:
    """LegitPhish matrices should use exact Tier E FEATURE_NAMES order."""

    data = pd.DataFrame(
        {
            "URL": ["https://example.com", "example.org/login"],
            "ClassLabel": [0, 1],
            "url_length": [19, 17],
        }
    )

    matrix = build_legitphish_feature_matrix(data)

    assert list(matrix.columns) == FEATURE_NAMES + [TARGET_COLUMN]
    assert matrix[TARGET_COLUMN].tolist() == [0, 1]


def test_legitphish_supplied_features_are_not_used() -> None:
    """Only the raw URL column should be used for feature generation."""

    data = pd.DataFrame(
        {
            "URL": ["https://example.com", "example.org/login"],
            "ClassLabel": [0, 1],
            "url_length": [999, 999],
            "url_entropy": [9.9, 9.9],
        }
    )
    matrix = build_legitphish_feature_matrix(data)
    summary = summarize_legitphish_dataset(data, matrix)

    assert summary["used_source_columns_for_features"] == ["URL"]
    assert summary["ignored_legitphish_supplied_feature_columns"] == [
        "url_length",
        "url_entropy",
    ]
    assert matrix["url_length"].tolist() != [999, 999]


def test_legitphish_duplicate_conflict_detection() -> None:
    """Identical URLs with different labels should be reported as conflicts."""

    data = pd.DataFrame(
        {
            "URL": ["safe-a", "safe-a", "safe-b"],
            "ClassLabel": [0, 1, 1],
        }
    )

    assert conflicting_duplicate_urls(data) == {"safe-a"}


def test_legitphish_prepare_code_has_no_per_url_network_dependency() -> None:
    """Preparation should parse URL strings locally instead of contacting hosts."""

    import src.prepare_legitphish_data as prepare_legitphish_data

    source = inspect.getsource(prepare_legitphish_data)
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


def test_legitphish_validation_code_does_not_fit_model() -> None:
    """The second external validation must not train or retune the model."""

    import src.run_legitphish_validation as run_legitphish_validation

    source = inspect.getsource(run_legitphish_validation)

    assert ".fit(" not in source
    assert "GridSearchCV" not in source
    assert "RandomizedSearchCV" not in source


def test_phishing_probability_uses_label_zero_column() -> None:
    """Probability extraction should locate phishing label 0 in model.classes_."""

    class ReversedClassModel:
        classes_ = [1, 0]

    probabilities = np.array([[0.1, 0.9], [0.8, 0.2]])

    phishing_probability = phishing_probability_from_proba(
        ReversedClassModel(),
        probabilities,
    )

    assert phishing_probability.tolist() == [0.9, 0.2]


def test_legitphish_validation_loads_frozen_optimized_artifact() -> None:
    """The validation loader should default to the optimized PhiUSIIL artifact."""

    from src.config import OPTIMIZED_MODEL_FILE

    assert load_selected_model.__defaults__ == (OPTIMIZED_MODEL_FILE,)


def test_legitphish_validation_uses_offline_domain_parser() -> None:
    """Domain overlap should use local parsing instead of network lookups."""

    import src.run_legitphish_validation as run_legitphish_validation

    source = inspect.getsource(run_legitphish_validation)
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

    assert "extract_registrable_domain" in source
    for snippet in banned_snippets:
        assert snippet not in source


def test_committed_legitphish_outputs_do_not_contain_raw_urls() -> None:
    """Committed LegitPhish result payloads should contain aggregate data only."""

    url_like_markers = ["http://", "https://", "www.", ".com/", ".net/", ".org/"]
    output_files = [
        LEGITPHISH_VALIDATION_METRICS_FILE,
        LEGITPHISH_SENSITIVITY_METRICS_FILE,
    ]

    for output_file in output_files:
        if not Path(output_file).exists():
            continue

        text = Path(output_file).read_text(encoding="utf-8")
        json.loads(text)
        for marker in url_like_markers:
            assert marker not in text


def test_multi_dataset_origin_sampling_is_deterministic() -> None:
    """LegitPhish origin diagnostics should use fixed sampling."""

    from src.compare_external_shifts import build_origin_dataset

    def frame_for(labels: list[int], offset: int) -> pd.DataFrame:
        rows = []
        for row_index, label in enumerate(labels):
            row = {feature: float(offset + row_index) for feature in FEATURE_NAMES}
            row["label"] = label
            row[TARGET_COLUMN] = label
            rows.append(row)
        return pd.DataFrame(rows)

    labels = [LEGITIMATE_LABEL] * 8 + [PHISHING_LABEL] * 8
    internal = frame_for(labels, 0)
    legitphish = frame_for(labels, 100)

    x_first, y_first, counts_first = build_origin_dataset(
        internal,
        legitphish,
        LEGITIMATE_LABEL,
    )
    x_second, y_second, counts_second = build_origin_dataset(
        internal,
        legitphish,
        LEGITIMATE_LABEL,
    )

    pd.testing.assert_frame_equal(x_first, x_second)
    pd.testing.assert_series_equal(y_first, y_second)
    assert counts_first == counts_second


def test_multi_dataset_shift_code_uses_fixed_origin_tree_settings() -> None:
    """The LegitPhish origin diagnostic should mirror the fixed shallow tree setup."""

    import src.compare_external_shifts as compare_external_shifts

    source = inspect.getsource(compare_external_shifts)

    assert "ORIGIN_RANDOM_STATE = 42" in source
    assert "ORIGIN_TREE_MAX_DEPTH = 5" in source
    assert "max_depth=ORIGIN_TREE_MAX_DEPTH" in source
    assert "random_state=ORIGIN_RANDOM_STATE" in source
