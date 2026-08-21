"""Tests for final cross-dataset overlap integrity audit helpers."""

import inspect
import json
from pathlib import Path

import pandas as pd

from src.audit_cross_dataset_overlap import (
    add_overlap_keys,
    key_overlap_summary,
    normalized_url_key,
)
from src.config import CROSS_DATASET_OVERLAP_SUMMARY_FILE


def test_exact_overlap_counting_uses_stripped_raw_urls() -> None:
    """Exact URL overlap should trim surrounding whitespace."""

    phiusiil = add_overlap_keys(
        pd.DataFrame(
            {
                "url": [" https://same.test/a ", "https://only-internal.test"],
                "label": [0, 1],
            }
        )
    )
    external = add_overlap_keys(
        pd.DataFrame(
            {
                "url": ["https://same.test/a", "https://only-external.test"],
                "label": [0, 1],
            }
        )
    )

    summary = key_overlap_summary(phiusiil, external, "exact_key")

    assert summary["unique_shared_keys"] == 1
    assert summary["phiusiil_rows_with_shared_key"] == 1
    assert summary["external_rows_with_shared_key"] == 1


def test_normalized_overlap_counting_uses_stripped_lowercase() -> None:
    """Normalized URL overlap should match case-only variants."""

    assert normalized_url_key(" HTTPS://Example.TEST/Login ") == "https://example.test/login"

    phiusiil = add_overlap_keys(
        pd.DataFrame({"url": ["HTTPS://Example.TEST/Login"], "label": [1]})
    )
    external = add_overlap_keys(
        pd.DataFrame({"url": ["https://example.test/login"], "label": [1]})
    )

    exact = key_overlap_summary(phiusiil, external, "exact_key")
    normalized = key_overlap_summary(phiusiil, external, "normalized_key")

    assert exact["unique_shared_keys"] == 0
    assert normalized["unique_shared_keys"] == 1


def test_cross_label_conflict_detection_counts_opposite_labels() -> None:
    """Shared keys with opposite dataset labels must be reported."""

    phiusiil = add_overlap_keys(
        pd.DataFrame(
            {
                "url": ["https://same.test/a", "https://same-label.test"],
                "label": [0, 1],
            }
        )
    )
    external = add_overlap_keys(
        pd.DataFrame(
            {
                "url": ["https://same.test/a", "https://same-label.test"],
                "label": [1, 1],
            }
        )
    )

    summary = key_overlap_summary(phiusiil, external, "exact_key")

    assert summary["cross_label_conflicts"] == {
        "shared_keys_with_any_cross_label_conflict": 1,
        "phiusiil_phishing_external_legitimate_keys": 1,
        "phiusiil_legitimate_external_phishing_keys": 0,
    }


def test_overlap_audit_code_has_no_network_dependency() -> None:
    """Overlap audits should use only local strings and offline parsers."""

    import src.audit_cross_dataset_overlap as audit_cross_dataset_overlap

    source = inspect.getsource(audit_cross_dataset_overlap)
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


def test_committed_overlap_summary_contains_no_raw_urls() -> None:
    """Committed overlap output should be aggregate-only JSON."""

    if not Path(CROSS_DATASET_OVERLAP_SUMMARY_FILE).exists():
        return

    text = Path(CROSS_DATASET_OVERLAP_SUMMARY_FILE).read_text(encoding="utf-8")
    json.loads(text)

    for marker in ["http://", "https://", "www.", ".com/", ".net/", ".org/"]:
        assert marker not in text
