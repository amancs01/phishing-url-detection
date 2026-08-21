"""Tests for the LegitPhish external validation pipeline."""

import inspect

import pandas as pd

from src.feature_definitions import FEATURE_NAMES
from src.prepare_external_data import TARGET_COLUMN
from src.prepare_legitphish_data import (
    LEGITPHISH_LABEL_MEANINGS,
    build_legitphish_feature_matrix,
    conflicting_duplicate_urls,
    summarize_legitphish_dataset,
)


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
