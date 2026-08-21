"""Post-hoc external deduplication and domain-overlap sensitivity analysis."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from src.config import (
    EXTERNAL_VALIDATION_METRICS_FILE,
    EXTERNAL_VALIDATION_PREDICTIONS_FILE,
    RAW_DATA_FILE,
    RESULTS_DIRECTORY,
    URL_PHISH_RAW_FILE,
)
from src.domain_utils import extract_registrable_domain
from src.prepare_external_data import LABEL_COLUMN, URL_COLUMN, normalize_url_phish_labels
from src.run_external_validation import calculate_external_metrics


EXTERNAL_OVERLAP_SENSITIVITY_FILE = RESULTS_DIRECTORY / "external_overlap_sensitivity.json"
PHIUSIIL_URL_COLUMN = "URL"


def load_external_raw_predictions() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load local raw URL-Phish data and anonymous external predictions."""

    raw = pd.read_csv(URL_PHISH_RAW_FILE)
    predictions = pd.read_csv(EXTERNAL_VALIDATION_PREDICTIONS_FILE)

    if len(raw) != len(predictions):
        raise ValueError("External raw rows and prediction rows are not aligned.")

    return raw, predictions


def load_primary_external_metrics() -> dict[str, Any]:
    """Load the registered primary external metrics."""

    with EXTERNAL_VALIDATION_METRICS_FILE.open(encoding="utf-8") as file:
        return json.load(file)["metrics"]


def metrics_from_prediction_rows(rows: pd.DataFrame) -> dict[str, Any]:
    """Evaluate metrics from anonymous prediction rows."""

    return calculate_external_metrics(
        rows["actual_label"].astype(int),
        rows["predicted_label"].astype(int),
        rows["phishing_probability"].astype(float),
    )


def conflicting_duplicate_urls(raw: pd.DataFrame) -> set[str]:
    """Return exact URL strings that appear with conflicting labels."""

    label_counts = raw.groupby(URL_COLUMN)[LABEL_COLUMN].nunique(dropna=False)
    return set(label_counts[label_counts > 1].index.tolist())


def deduplicated_row_indices(raw: pd.DataFrame) -> tuple[list[int], dict[str, int]]:
    """Return first non-conflicting exact-URL row indices for dedup sensitivity."""

    conflicts = conflicting_duplicate_urls(raw)
    non_conflicting = raw[~raw[URL_COLUMN].isin(conflicts)]
    keep_mask = ~non_conflicting.duplicated(subset=[URL_COLUMN], keep="first")
    kept_indices = non_conflicting[keep_mask].index.astype(int).tolist()
    diagnostics = {
        "raw_rows": int(len(raw)),
        "duplicate_rows": int(raw.duplicated().sum()),
        "duplicate_url_rows": int(raw[URL_COLUMN].duplicated().sum()),
        "conflicting_duplicate_url_values": int(len(conflicts)),
        "rows_with_conflicting_duplicate_url": int(raw[URL_COLUMN].isin(conflicts).sum()),
        "deduplicated_rows": int(len(kept_indices)),
    }
    return kept_indices, diagnostics


def deduplicated_external_sensitivity(raw: pd.DataFrame, predictions: pd.DataFrame) -> dict[str, Any]:
    """Evaluate the frozen model on exact-URL deduplicated external rows."""

    kept_indices, diagnostics = deduplicated_row_indices(raw)
    dedup_predictions = predictions.loc[kept_indices].copy()
    metrics = metrics_from_prediction_rows(dedup_predictions)
    class_counts = dedup_predictions["actual_label"].value_counts().to_dict()
    primary_metrics = load_primary_external_metrics()
    return {
        **diagnostics,
        "project_class_counts": {
            "phishing_label_0": int(class_counts.get(0, 0)),
            "legitimate_label_1": int(class_counts.get(1, 0)),
        },
        "metrics": metrics,
        "primary_external_metrics_for_reference": primary_metrics,
        "metric_differences_deduplicated_minus_primary": {
            metric_name: metrics[metric_name] - primary_metrics[metric_name]
            for metric_name in [
                "accuracy",
                "phishing_precision",
                "phishing_recall",
                "phishing_f1",
                "roc_auc",
                "balanced_accuracy",
            ]
        },
    }


def external_domain_groups(raw: pd.DataFrame) -> pd.Series:
    """Extract URL-Phish registrable domains offline."""

    return raw[URL_COLUMN].astype(str).map(extract_registrable_domain)


def phiusiil_domain_set() -> set[str]:
    """Extract the set of PhiUSIIL registrable domains offline."""

    raw = pd.read_csv(RAW_DATA_FILE, usecols=[PHIUSIIL_URL_COLUMN])
    return set(raw[PHIUSIIL_URL_COLUMN].astype(str).map(extract_registrable_domain))


def metrics_by_domain_overlap(raw: pd.DataFrame, predictions: pd.DataFrame) -> dict[str, Any]:
    """Evaluate external rows whose registrable domains are seen or unseen."""

    external_domains = external_domain_groups(raw)
    internal_domains = phiusiil_domain_set()
    seen_mask = external_domains.isin(internal_domains)
    unseen_mask = ~seen_mask
    domain_count = int(external_domains.nunique())
    seen_domain_count = int(external_domains[seen_mask].nunique())
    unseen_domain_count = int(external_domains[unseen_mask].nunique())

    def segment(mask: pd.Series) -> dict[str, Any]:
        rows = predictions[mask.to_numpy()].copy()
        class_counts = rows["actual_label"].value_counts().to_dict()
        return {
            "row_count": int(len(rows)),
            "project_class_counts": {
                "phishing_label_0": int(class_counts.get(0, 0)),
                "legitimate_label_1": int(class_counts.get(1, 0)),
            },
            "metrics": metrics_from_prediction_rows(rows),
        }

    return {
        "url_phish_registrable_domains": domain_count,
        "domains_also_present_in_phiusiil": seen_domain_count,
        "domains_unseen_in_phiusiil": unseen_domain_count,
        "overlap_percentage": seen_domain_count / domain_count * 100 if domain_count else 0.0,
        "seen_domain_rows": segment(seen_mask),
        "unseen_domain_rows": segment(unseen_mask),
    }


def run_external_overlap_sensitivity() -> dict[str, Any]:
    """Run deduplication and offline domain-overlap sensitivity analyses."""

    raw, predictions = load_external_raw_predictions()
    payload = {
        "analysis_type": "POST-HOC DIAGNOSTIC ANALYSIS",
        "primary_external_result_changed": False,
        "deduplicated_exact_url_sensitivity": deduplicated_external_sensitivity(
            raw,
            predictions,
        ),
        "cross_dataset_registrable_domain_overlap": metrics_by_domain_overlap(
            raw,
            predictions,
        ),
        "source_category_diagnostics": {
            "available": False,
            "reason": (
                "URL-Phish Version 2 contains url, dom, tld, numerical features, "
                "and label columns, but no reliable source/category metadata."
            ),
        },
        "safety_statement": (
            "Exact URL and registrable-domain grouping used local strings and "
            "offline publicsuffix2 parsing only; no URL was opened, requested, "
            "resolved, or contacted."
        ),
    }
    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with EXTERNAL_OVERLAP_SENSITIVITY_FILE.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")
    return payload


def main() -> None:
    """Run post-hoc external overlap sensitivity."""

    payload = run_external_overlap_sensitivity()
    print(f"Saved: {EXTERNAL_OVERLAP_SENSITIVITY_FILE}")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
