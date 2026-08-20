"""Tests for feature provenance and fidelity-audit artifacts."""

import json
import re
from pathlib import Path

import pandas as pd
import pytest

from src.audit_feature_fidelity import (
    REQUIRED_AUDIT_COLUMNS,
    compute_feature_fidelity,
    run_feature_fidelity_audit,
    validate_mappings,
)
from src.feature_definitions import FEATURE_NAMES


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROVENANCE_FILE = PROJECT_ROOT / "research" / "phiusiil_feature_provenance.csv"
MAPPING_FILE = PROJECT_ROOT / "research" / "feature_mapping.json"
SCHEMA_FILE = PROJECT_ROOT / "results" / "dataset_schema.json"
FIDELITY_FILE = PROJECT_ROOT / "results" / "feature_fidelity.csv"
FIDELITY_SUMMARY_FILE = PROJECT_ROOT / "results" / "feature_fidelity_summary.json"
FIDELITY_SAMPLE_FILE = PROJECT_ROOT / "results" / "feature_fidelity_mismatch_samples.csv"
FIDELITY_ANALYSIS_FILE = PROJECT_ROOT / "research" / "feature_fidelity_analysis.md"


def load_schema_columns() -> list[str]:
    """Return the committed raw PhiUSIIL schema columns."""

    with SCHEMA_FILE.open(encoding="utf-8") as file:
        schema = json.load(file)

    return schema["column_names"]


def load_mappings() -> list[dict]:
    """Return the committed fidelity mappings."""

    with MAPPING_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def test_every_dataset_column_has_provenance_classification() -> None:
    """Every raw PhiUSIIL column should appear once in the provenance audit."""

    provenance = pd.read_csv(PROVENANCE_FILE)
    schema_columns = load_schema_columns()

    assert provenance["feature_name"].tolist() == schema_columns
    assert provenance["feature_name"].is_unique
    assert provenance["provenance_category"].notna().all()
    assert provenance["confidence"].notna().all()
    assert provenance["evidence_or_reason"].notna().all()


def test_no_deployment_feature_is_webpage_or_network_dependent() -> None:
    """Tier D deployment features should be local URL-text features only."""

    analysis_text = FIDELITY_ANALYSIS_FILE.read_text(encoding="utf-8")
    banned_terms = {
        "dns",
        "whois",
        "ssl",
        "certificate",
        "favicon",
        "html",
        "content",
        "request",
        "response",
        "socket",
    }

    for feature_name in FEATURE_NAMES:
        assert f"`{feature_name}`" in analysis_text
        assert not any(term in feature_name for term in banned_terms)


def test_mappings_reference_valid_dataset_and_extractor_features() -> None:
    """Mappings should connect real PhiUSIIL columns to real extractor names."""

    mappings = load_mappings()

    validate_mappings(mappings, load_schema_columns())


def test_committed_audit_output_has_expected_columns() -> None:
    """The committed audit CSV should expose the documented statistics."""

    audit = pd.read_csv(FIDELITY_FILE)

    assert audit.columns.tolist() == REQUIRED_AUDIT_COLUMNS
    assert len(audit) == len(load_mappings())


def test_exact_match_and_mae_calculations_are_correct() -> None:
    """Metric calculations should be correct on a tiny deterministic example."""

    supplied = pd.DataFrame(
        {
            "SuppliedCount": [1, 2, 4],
            "SuppliedRatio": [0.10, 0.20, 0.35],
        }
    )
    reconstructed = pd.DataFrame(
        {
            "number_of_digits": [1, 3, 4],
            "digit_ratio": [0.10, 0.21, 0.30],
        }
    )
    mappings = [
        {
            "supplied_feature": "SuppliedCount",
            "reconstructed_feature": "number_of_digits",
            "feature_type": "discrete",
            "near_match_tolerance": 0.0,
        },
        {
            "supplied_feature": "SuppliedRatio",
            "reconstructed_feature": "digit_ratio",
            "feature_type": "continuous",
            "near_match_tolerance": 0.02,
        },
    ]

    audit = compute_feature_fidelity(supplied, reconstructed, mappings)
    count_row = audit[audit["supplied_feature"] == "SuppliedCount"].iloc[0]
    ratio_row = audit[audit["supplied_feature"] == "SuppliedRatio"].iloc[0]

    assert count_row["exact_match_count"] == 2
    assert count_row["mismatch_count"] == 1
    assert count_row["exact_match_percentage"] == pytest.approx(2 / 3 * 100)
    assert count_row["mae"] == pytest.approx(1 / 3)
    assert ratio_row["near_match_count"] == 2
    assert ratio_row["mae"] == pytest.approx(0.02)


def test_missing_mapping_column_fails_clearly() -> None:
    """Invalid mappings should fail before any audit output is trusted."""

    mappings = [
        {
            "supplied_feature": "NotAColumn",
            "reconstructed_feature": "url_length",
            "feature_type": "discrete",
            "near_match_tolerance": 0.0,
        }
    ]

    with pytest.raises(ValueError, match="not in dataset columns"):
        validate_mappings(mappings, ["URLLength"])


def test_missing_mapping_key_fails_clearly() -> None:
    """Mappings with missing fields should raise a useful error."""

    with pytest.raises(ValueError, match="missing keys"):
        validate_mappings([{"supplied_feature": "URLLength"}], ["URLLength"])


def test_committed_fidelity_outputs_expose_no_raw_urls() -> None:
    """Committed fidelity outputs should not contain raw dataset URL strings."""

    url_like_pattern = re.compile(r"https?://|www\.", flags=re.IGNORECASE)

    for output_file in [FIDELITY_FILE, FIDELITY_SUMMARY_FILE, FIDELITY_SAMPLE_FILE]:
        output_text = output_file.read_text(encoding="utf-8")
        assert not url_like_pattern.search(output_text)


def test_audit_is_deterministic_on_same_input(tmp_path: Path) -> None:
    """Running the audit twice on the same local text data should match."""

    raw_data_file = tmp_path / "tiny_raw.csv"
    mapping_file = tmp_path / "tiny_mapping.json"
    pd.DataFrame(
        {
            "URL": ["https://example.com", "example.org/login"],
            "URLLength": [19, 17],
            "label": [1, 0],
        }
    ).to_csv(raw_data_file, index=False)
    mapping_file.write_text(
        json.dumps(
            [
                {
                    "supplied_feature": "URLLength",
                    "reconstructed_feature": "url_length",
                    "feature_type": "discrete",
                    "near_match_tolerance": 0.0,
                }
            ]
        ),
        encoding="utf-8",
    )

    first_audit, first_summary, first_samples = run_feature_fidelity_audit(
        raw_data_file=raw_data_file,
        mapping_file=mapping_file,
    )
    second_audit, second_summary, second_samples = run_feature_fidelity_audit(
        raw_data_file=raw_data_file,
        mapping_file=mapping_file,
    )

    pd.testing.assert_frame_equal(first_audit, second_audit)
    pd.testing.assert_frame_equal(first_samples, second_samples)
    assert first_summary == second_summary
