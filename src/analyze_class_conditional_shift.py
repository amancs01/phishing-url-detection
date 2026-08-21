"""Post-hoc class-conditional feature shift diagnostics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import ks_2samp

from src.config import (
    FIGURES_DIRECTORY,
    PROCESSED_DATA_FILE,
    RESULTS_DIRECTORY,
    URL_PHISH_EXTERNAL_MATRIX_FILE,
)
from src.feature_definitions import FEATURE_NAMES
from src.prepare_external_data import TARGET_COLUMN, validate_external_feature_matrix


CLASS_CONDITIONAL_SHIFT_FILE = RESULTS_DIRECTORY / "class_conditional_feature_shift.csv"
BENIGN_SHIFT_FIGURE = FIGURES_DIRECTORY / "benign_feature_shift.png"
PHISHING_SHIFT_FIGURE = FIGURES_DIRECTORY / "phishing_feature_shift.png"
INTERNAL_LABEL_COLUMN = "label"
PHISHING_LABEL = 0
LEGITIMATE_LABEL = 1
BINARY_FEATURES = {
    "domain_is_ip",
    "uses_https_text",
    "has_port",
    "has_suspicious_keyword",
    "known_shortener_domain",
}


def load_internal_external_features(
    internal_file: Path = PROCESSED_DATA_FILE,
    external_file: Path = URL_PHISH_EXTERNAL_MATRIX_FILE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load ignored internal and external feature matrices."""

    internal = pd.read_csv(internal_file)
    external = pd.read_csv(external_file)
    validate_external_feature_matrix(external)

    expected_internal_columns = FEATURE_NAMES + [INTERNAL_LABEL_COLUMN]

    if list(internal.columns) != expected_internal_columns:
        raise ValueError("Internal processed feature matrix has unexpected columns.")

    return internal, external


def _series_stats(values: pd.Series, prefix: str) -> dict[str, float]:
    """Return descriptive statistics for one feature series."""

    return {
        f"{prefix}_mean": float(values.mean()),
        f"{prefix}_median": float(values.median()),
        f"{prefix}_std": float(values.std()),
        f"{prefix}_p10": float(values.quantile(0.10)),
        f"{prefix}_p25": float(values.quantile(0.25)),
        f"{prefix}_p75": float(values.quantile(0.75)),
        f"{prefix}_p90": float(values.quantile(0.90)),
    }


def feature_shift_record(
    comparison: str,
    feature_name: str,
    source_values: pd.Series,
    external_values: pd.Series,
) -> dict[str, Any]:
    """Calculate class-conditional shift statistics for one feature."""

    ks_result = ks_2samp(source_values, external_values)
    source_median = float(source_values.median())
    external_median = float(external_values.median())
    source_mean = float(source_values.mean())
    external_mean = float(external_values.mean())
    record: dict[str, Any] = {
        "comparison": comparison,
        "feature": feature_name,
        "source_rows": int(source_values.shape[0]),
        "external_rows": int(external_values.shape[0]),
        **_series_stats(source_values, "source"),
        **_series_stats(external_values, "external"),
        "ks_statistic": float(ks_result.statistic),
        "ks_p_value": float(ks_result.pvalue),
        "mean_difference_external_minus_source": external_mean - source_mean,
        "median_difference_external_minus_source": external_median - source_median,
        "is_binary_feature": feature_name in BINARY_FEATURES,
        "source_proportion_1": None,
        "external_proportion_1": None,
        "absolute_percentage_point_difference_1": None,
    }

    if feature_name in BINARY_FEATURES:
        source_proportion = source_mean
        external_proportion = external_mean
        record["source_proportion_1"] = source_proportion
        record["external_proportion_1"] = external_proportion
        record["absolute_percentage_point_difference_1"] = abs(
            external_proportion - source_proportion
        ) * 100

    return record


def class_conditional_shift(internal: pd.DataFrame, external: pd.DataFrame) -> pd.DataFrame:
    """Compare matching semantic classes across PhiUSIIL and URL-Phish."""

    groups = {
        "legitimate_vs_benign": (
            internal[internal[INTERNAL_LABEL_COLUMN] == LEGITIMATE_LABEL],
            external[external[TARGET_COLUMN] == LEGITIMATE_LABEL],
        ),
        "phishing_vs_phishing": (
            internal[internal[INTERNAL_LABEL_COLUMN] == PHISHING_LABEL],
            external[external[TARGET_COLUMN] == PHISHING_LABEL],
        ),
    }
    records = []

    for comparison_name, (source_group, external_group) in groups.items():
        for feature_name in FEATURE_NAMES:
            records.append(
                feature_shift_record(
                    comparison_name,
                    feature_name,
                    source_group[feature_name],
                    external_group[feature_name],
                )
            )

    return (
        pd.DataFrame(records)
        .sort_values(["comparison", "ks_statistic"], ascending=[True, False])
        .reset_index(drop=True)
    )


def save_shift_figures(results: pd.DataFrame) -> None:
    """Save separate class-conditional KS ranking figures."""

    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    figure_map = {
        "legitimate_vs_benign": (BENIGN_SHIFT_FIGURE, "Legitimate/benign feature shift"),
        "phishing_vs_phishing": (PHISHING_SHIFT_FIGURE, "Phishing feature shift"),
    }

    for comparison_name, (figure_file, title) in figure_map.items():
        top = (
            results[results["comparison"] == comparison_name]
            .sort_values("ks_statistic", ascending=False)
            .head(10)
            .iloc[::-1]
        )
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(top["feature"], top["ks_statistic"], color="#2f6f8f")
        ax.set_xlabel("KS statistic")
        ax.set_title(title)
        ax.set_xlim(0, max(0.05, float(top["ks_statistic"].max()) * 1.1))
        fig.tight_layout()
        fig.savefig(figure_file, dpi=160)
        plt.close(fig)


def run_class_conditional_shift() -> pd.DataFrame:
    """Run and save class-conditional feature-shift diagnostics."""

    internal, external = load_internal_external_features()
    results = class_conditional_shift(internal, external)
    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    results.to_csv(CLASS_CONDITIONAL_SHIFT_FILE, index=False)
    save_shift_figures(results)
    return results


def main() -> None:
    """Run class-conditional diagnostics."""

    results = run_class_conditional_shift()
    print(f"Saved: {CLASS_CONDITIONAL_SHIFT_FILE}")
    print(f"Saved: {BENIGN_SHIFT_FIGURE}")
    print(f"Saved: {PHISHING_SHIFT_FIGURE}")
    for comparison_name in ["legitimate_vs_benign", "phishing_vs_phishing"]:
        print()
        print(comparison_name)
        print(
            results[results["comparison"] == comparison_name]
            .head(10)[
                [
                    "feature",
                    "ks_statistic",
                    "source_mean",
                    "external_mean",
                    "mean_difference_external_minus_source",
                ]
            ]
            .to_string(index=False)
        )


if __name__ == "__main__":
    main()
