"""Compare internal PhiUSIIL and external URL-Phish Tier E feature distributions."""

from __future__ import annotations

import pandas as pd
from scipy.stats import ks_2samp

from src.config import (
    EXTERNAL_FEATURE_SHIFT_FILE,
    PROCESSED_DATA_FILE,
    URL_PHISH_EXTERNAL_MATRIX_FILE,
)
from src.feature_definitions import FEATURE_NAMES
from src.prepare_external_data import TARGET_COLUMN, validate_external_feature_matrix


QUANTILES = [0.05, 0.25, 0.75, 0.95]


def load_internal_features() -> pd.DataFrame:
    """Load internal PhiUSIIL Tier E features from ignored processed storage."""

    data = pd.read_csv(PROCESSED_DATA_FILE)
    return data[FEATURE_NAMES]


def load_external_features() -> pd.DataFrame:
    """Load external URL-Phish Tier E features from ignored processed storage."""

    data = pd.read_csv(URL_PHISH_EXTERNAL_MATRIX_FILE)
    validate_external_feature_matrix(data)
    return data[FEATURE_NAMES + [TARGET_COLUMN]]


def feature_distribution_record(
    feature_name: str,
    internal: pd.Series,
    external: pd.Series,
) -> dict[str, float | str]:
    """Calculate descriptive and two-sample KS statistics for one feature."""

    ks_result = ks_2samp(internal, external)
    record: dict[str, float | str] = {
        "feature": feature_name,
        "internal_mean": float(internal.mean()),
        "external_mean": float(external.mean()),
        "mean_difference_external_minus_internal": float(
            external.mean() - internal.mean()
        ),
        "internal_median": float(internal.median()),
        "external_median": float(external.median()),
        "internal_std": float(internal.std()),
        "external_std": float(external.std()),
        "ks_statistic": float(ks_result.statistic),
        "ks_p_value": float(ks_result.pvalue),
    }

    for quantile in QUANTILES:
        suffix = str(int(quantile * 100)).zfill(2)
        record[f"internal_q{suffix}"] = float(internal.quantile(quantile))
        record[f"external_q{suffix}"] = float(external.quantile(quantile))

    return record


def analyze_external_feature_shift() -> pd.DataFrame:
    """Create feature-shift diagnostics without raw URL values."""

    internal = load_internal_features()
    external = load_external_features()
    records = [
        feature_distribution_record(feature_name, internal[feature_name], external[feature_name])
        for feature_name in FEATURE_NAMES
    ]
    results = (
        pd.DataFrame(records)
        .sort_values("ks_statistic", ascending=False)
        .reset_index(drop=True)
    )
    results.to_csv(EXTERNAL_FEATURE_SHIFT_FILE, index=False)
    return results


def main() -> None:
    """Run feature distribution shift diagnostics."""

    results = analyze_external_feature_shift()
    print(f"Saved: {EXTERNAL_FEATURE_SHIFT_FILE}")
    print(results.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
