"""Tests for registrable-domain-disjoint split construction."""

import json
from pathlib import Path

import pandas as pd

from src.build_domain_disjoint_split import (
    DOMAIN_DISJOINT_SPLIT_SUMMARY_FILE,
    build_domain_split,
    domain_intersections,
    split_summary,
)


def tiny_domain_dataframe() -> pd.DataFrame:
    """Return a small safe URL dataframe with repeated registrable domains."""

    return pd.DataFrame(
        {
            "URL": [
                "https://a.example.com/login",
                "https://b.example.com/reset",
                "https://example.org",
                "https://sub.example.co.uk/path",
                "https://another.example.co.uk/path",
                "http://192.0.2.1/account",
            ],
            "label": [0, 0, 1, 1, 0, 1],
        }
    )


def test_domain_split_has_no_domain_overlap_on_small_data() -> None:
    """A registrable domain should never appear in more than one split."""

    split = build_domain_split(tiny_domain_dataframe())

    assert domain_intersections(split.domain_sets) == {
        "train_validation": 0,
        "train_test": 0,
        "validation_test": 0,
    }


def test_domain_split_is_deterministic_on_small_data() -> None:
    """Repeated split construction should produce identical row indices."""

    first = build_domain_split(tiny_domain_dataframe())
    second = build_domain_split(tiny_domain_dataframe())

    assert first.row_indices == second.row_indices
    assert first.domain_sets == second.domain_sets


def test_split_summary_contains_expected_committed_overlap_counts() -> None:
    """Committed full-data split summary should report zero domain overlap."""

    summary = json.loads(
        Path(DOMAIN_DISJOINT_SPLIT_SUMMARY_FILE).read_text(encoding="utf-8")
    )

    assert summary["total_rows"] == 235795
    assert summary["total_unique_registrable_domains"] == 194036
    assert summary["domain_intersection_counts"] == {
        "train_validation": 0,
        "train_test": 0,
        "validation_test": 0,
    }
    assert summary["public_suffix_parser"]["runtime_fetch_used"] is False


def test_split_summary_has_no_raw_url_or_domain_keys_on_small_data() -> None:
    """Summary output should store row indices and aggregate diagnostics only."""

    summary = split_summary(build_domain_split(tiny_domain_dataframe()))
    summary_text = json.dumps(summary)

    assert "https://" not in summary_text
    assert "example.com" not in summary_text
    assert "example.co.uk" not in summary_text
