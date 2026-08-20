"""Tests for controlled research tier and bootstrap artifacts."""

import json
from pathlib import Path

import pandas as pd

from src.bootstrap_metrics import dataframe_records
from src.build_research_tiers import TIER_FEATURES


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPLIT_FILE = PROJECT_ROOT / "results" / "research_split_indices.json"
TIER_SUMMARY_FILE = PROJECT_ROOT / "results" / "research_tier_summary.json"
PERFORMANCE_FILE = PROJECT_ROOT / "results" / "feature_tier_performance.csv"
BOOTSTRAP_JSON_FILE = PROJECT_ROOT / "results" / "feature_tier_bootstrap_metrics.json"
BOOTSTRAP_CSV_FILE = PROJECT_ROOT / "results" / "feature_tier_bootstrap_metrics.csv"


def test_research_split_indices_cover_same_rows_once() -> None:
    """The shared research split should be complete and non-overlapping."""

    split_indices = json.loads(SPLIT_FILE.read_text(encoding="utf-8"))
    all_indices = (
        split_indices["train"]
        + split_indices["validation"]
        + split_indices["test"]
    )

    assert len(all_indices) == 235795
    assert len(set(all_indices)) == 235795
    assert len(split_indices["train"]) == 165056
    assert len(split_indices["validation"]) == 35369
    assert len(split_indices["test"]) == 35370


def test_research_tier_summary_matches_locked_feature_lists() -> None:
    """Committed tier summary should match the code-level locked tier lists."""

    summary = json.loads(TIER_SUMMARY_FILE.read_text(encoding="utf-8"))

    for tier_name, feature_names in TIER_FEATURES.items():
        tier_summary = summary["tiers"][tier_name]
        assert tier_summary["feature_count"] == len(feature_names)
        assert tier_summary["feature_names"] == feature_names
        assert tier_summary["row_count"] == 235795
        assert tier_summary["has_missing_values"] is False
        assert tier_summary["all_numeric"] is True

    assert summary["controls"]["same_split_assignment_all_tiers"] is True
    assert summary["controls"]["raw_url_not_used_as_model_feature"] is True


def test_feature_tier_performance_contains_expected_tracks_and_tiers() -> None:
    """Performance output should contain both Decision Tree tracks for all tiers."""

    performance = pd.read_csv(PERFORMANCE_FILE)

    assert set(performance["tier"]) == {"A", "B", "C", "D-matched", "E"}
    assert set(performance["track"]) == {"fixed_tree", "equal_tuning"}
    assert len(performance) == 10
    assert (performance["phishing_f1"].between(0, 1)).all()
    assert (performance["phishing_recall"].between(0, 1)).all()
    assert (performance["test_accuracy"].between(0, 1)).all()


def test_bootstrap_artifacts_are_json_valid_and_expected_shape() -> None:
    """Bootstrap outputs should be reproducible, JSON-valid metric summaries."""

    bootstrap_json = json.loads(BOOTSTRAP_JSON_FILE.read_text(encoding="utf-8"))
    bootstrap_csv = pd.read_csv(BOOTSTRAP_CSV_FILE)

    assert bootstrap_json["bootstrap_seed"] == 20260821
    assert bootstrap_json["bootstrap_iterations"] == 1000
    assert len(bootstrap_csv) == 54
    assert set(bootstrap_csv["metric"]) == {
        "accuracy",
        "phishing_recall",
        "phishing_f1",
    }


def test_dataframe_records_converts_nan_to_none() -> None:
    """Bootstrap JSON helper should avoid non-standard NaN values."""

    records = dataframe_records(pd.DataFrame({"value": [1.0, float("nan")]}))

    assert records == [{"value": 1.0}, {"value": None}]
