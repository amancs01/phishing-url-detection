"""Compare class-conditional feature shift across external datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from src.config import (
    BENIGN_SHIFT_ACROSS_DATASETS_FIGURE,
    LEGITPHISH_EXTERNAL_MATRIX_FILE,
    MULTI_DATASET_FEATURE_SHIFT_FILE,
    MULTI_DATASET_ORIGIN_PERFORMANCE_FILE,
    PHISHING_SHIFT_ACROSS_DATASETS_FIGURE,
    PROCESSED_DATA_FILE,
    URL_PHISH_EXTERNAL_MATRIX_FILE,
)
from src.feature_definitions import FEATURE_NAMES
from src.prepare_external_data import TARGET_COLUMN, validate_external_feature_matrix
from src.prepare_legitphish_data import validate_legitphish_feature_matrix
from src.predict import LEGITIMATE_LABEL, PHISHING_LABEL


SHIFT_REPORT_FILE = Path("research/multi_dataset_shift_analysis.md")
INTERNAL_LABEL_COLUMN = "label"
ORIGIN_RANDOM_STATE = 42
ORIGIN_TREE_MAX_DEPTH = 5
ORIGIN_TEST_SIZE = 0.30
INTERNAL_ORIGIN_LABEL = 0
EXTERNAL_ORIGIN_LABEL = 1
BINARY_FEATURES = {
    "domain_is_ip",
    "uses_https_text",
    "has_port",
    "has_suspicious_keyword",
    "known_shortener_domain",
}


def load_feature_matrices() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load local feature matrices without accessing original URL targets."""

    internal = pd.read_csv(PROCESSED_DATA_FILE)
    url_phish = pd.read_csv(URL_PHISH_EXTERNAL_MATRIX_FILE)
    legitphish = pd.read_csv(LEGITPHISH_EXTERNAL_MATRIX_FILE)
    validate_external_feature_matrix(url_phish)
    validate_legitphish_feature_matrix(legitphish)

    if list(internal.columns) != FEATURE_NAMES + [INTERNAL_LABEL_COLUMN]:
        raise ValueError("Internal processed feature matrix has unexpected columns.")

    return internal, url_phish, legitphish


def series_stats(values: pd.Series, prefix: str) -> dict[str, float]:
    """Return descriptive statistics for one feature distribution."""

    return {
        f"{prefix}_mean": float(values.mean()),
        f"{prefix}_median": float(values.median()),
        f"{prefix}_p10": float(values.quantile(0.10)),
        f"{prefix}_p25": float(values.quantile(0.25)),
        f"{prefix}_p75": float(values.quantile(0.75)),
        f"{prefix}_p90": float(values.quantile(0.90)),
    }


def feature_shift_record(
    comparison_id: str,
    semantic_class: str,
    external_dataset: str,
    feature_name: str,
    internal_values: pd.Series,
    external_values: pd.Series,
) -> dict[str, Any]:
    """Calculate one class-conditional feature-shift row."""

    ks = ks_2samp(internal_values, external_values)
    internal_mean = float(internal_values.mean())
    external_mean = float(external_values.mean())
    internal_median = float(internal_values.median())
    external_median = float(external_values.median())
    record: dict[str, Any] = {
        "comparison_id": comparison_id,
        "semantic_class": semantic_class,
        "external_dataset": external_dataset,
        "feature": feature_name,
        "internal_rows": int(internal_values.shape[0]),
        "external_rows": int(external_values.shape[0]),
        **series_stats(internal_values, "internal"),
        **series_stats(external_values, "external"),
        "ks_statistic": float(ks.statistic),
        "ks_p_value": float(ks.pvalue),
        "mean_difference_external_minus_internal": external_mean - internal_mean,
        "median_difference_external_minus_internal": external_median - internal_median,
        "is_binary_feature": feature_name in BINARY_FEATURES,
        "internal_proportion_1": None,
        "external_proportion_1": None,
        "absolute_percentage_point_difference_1": None,
    }

    if feature_name in BINARY_FEATURES:
        record["internal_proportion_1"] = internal_mean
        record["external_proportion_1"] = external_mean
        record["absolute_percentage_point_difference_1"] = (
            abs(external_mean - internal_mean) * 100
        )

    return record


def build_shift_table(
    internal: pd.DataFrame,
    url_phish: pd.DataFrame,
    legitphish: pd.DataFrame,
) -> pd.DataFrame:
    """Build all preregistered class-conditional comparisons."""

    comparisons = [
        (
            "A_phiusiil_legitimate_vs_url_phish_benign",
            "legitimate",
            "URL-Phish",
            internal[internal[INTERNAL_LABEL_COLUMN] == LEGITIMATE_LABEL],
            url_phish[url_phish[TARGET_COLUMN] == LEGITIMATE_LABEL],
        ),
        (
            "B_phiusiil_legitimate_vs_legitphish_legitimate",
            "legitimate",
            "LegitPhish",
            internal[internal[INTERNAL_LABEL_COLUMN] == LEGITIMATE_LABEL],
            legitphish[legitphish[TARGET_COLUMN] == LEGITIMATE_LABEL],
        ),
        (
            "C_phiusiil_phishing_vs_url_phish_phishing",
            "phishing",
            "URL-Phish",
            internal[internal[INTERNAL_LABEL_COLUMN] == PHISHING_LABEL],
            url_phish[url_phish[TARGET_COLUMN] == PHISHING_LABEL],
        ),
        (
            "D_phiusiil_phishing_vs_legitphish_phishing",
            "phishing",
            "LegitPhish",
            internal[internal[INTERNAL_LABEL_COLUMN] == PHISHING_LABEL],
            legitphish[legitphish[TARGET_COLUMN] == PHISHING_LABEL],
        ),
    ]
    records = []

    for comparison_id, semantic_class, external_dataset, internal_group, external_group in comparisons:
        for feature_name in FEATURE_NAMES:
            records.append(
                feature_shift_record(
                    comparison_id,
                    semantic_class,
                    external_dataset,
                    feature_name,
                    internal_group[feature_name],
                    external_group[feature_name],
                )
            )

    return (
        pd.DataFrame(records)
        .sort_values(["semantic_class", "external_dataset", "ks_statistic"], ascending=[True, True, False])
        .reset_index(drop=True)
    )


def shift_similarity_summary(shift: pd.DataFrame) -> pd.DataFrame:
    """Summarize which external dataset is closest to PhiUSIIL by class."""

    summary = (
        shift.groupby(["semantic_class", "external_dataset"], as_index=False)
        .agg(
            mean_ks_statistic=("ks_statistic", "mean"),
            median_ks_statistic=("ks_statistic", "median"),
            max_ks_statistic=("ks_statistic", "max"),
        )
        .sort_values(["semantic_class", "mean_ks_statistic", "median_ks_statistic"])
        .reset_index(drop=True)
    )
    summary["similarity_rank_within_class"] = (
        summary.groupby("semantic_class")["mean_ks_statistic"].rank(method="first")
    ).astype(int)
    return summary


def save_shift_figures(shift: pd.DataFrame) -> None:
    """Save grouped KS plots for legitimate/benign and phishing comparisons."""

    figure_specs = [
        ("legitimate", BENIGN_SHIFT_ACROSS_DATASETS_FIGURE, "Legitimate-class feature shift"),
        ("phishing", PHISHING_SHIFT_ACROSS_DATASETS_FIGURE, "Phishing-class feature shift"),
    ]

    for semantic_class, output_file, title in figure_specs:
        class_rows = shift[shift["semantic_class"] == semantic_class]
        top_features = (
            class_rows.groupby("feature")["ks_statistic"]
            .max()
            .sort_values(ascending=False)
            .head(10)
            .index.tolist()
        )
        plot_data = (
            class_rows[class_rows["feature"].isin(top_features)]
            .pivot(index="feature", columns="external_dataset", values="ks_statistic")
            .loc[top_features]
            .iloc[::-1]
        )
        ax = plot_data.plot(
            kind="barh",
            figsize=(8.5, 5.2),
            width=0.72,
            color=["#4e79a7", "#f28e2b"],
        )
        ax.set_xlabel("KS statistic")
        ax.set_ylabel("")
        ax.set_title(title)
        ax.set_xlim(0, max(0.05, float(plot_data.max().max()) * 1.12))
        ax.legend(title="External dataset")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        plt.tight_layout()
        plt.savefig(output_file, dpi=160)
        plt.close()


def build_origin_dataset(
    internal: pd.DataFrame,
    legitphish: pd.DataFrame,
    semantic_label: int,
) -> tuple[pd.DataFrame, pd.Series, dict[str, int]]:
    """Balance PhiUSIIL and LegitPhish rows for one class."""

    internal_group = internal[internal[INTERNAL_LABEL_COLUMN] == semantic_label]
    legitphish_group = legitphish[legitphish[TARGET_COLUMN] == semantic_label]
    sample_size = min(len(internal_group), len(legitphish_group))
    internal_sample = internal_group.sample(n=sample_size, random_state=ORIGIN_RANDOM_STATE)
    legitphish_sample = legitphish_group.sample(n=sample_size, random_state=ORIGIN_RANDOM_STATE)
    x = pd.concat(
        [internal_sample[FEATURE_NAMES], legitphish_sample[FEATURE_NAMES]],
        ignore_index=True,
    )
    y = pd.Series(
        [INTERNAL_ORIGIN_LABEL] * sample_size + [EXTERNAL_ORIGIN_LABEL] * sample_size,
        name="dataset_origin",
    )
    counts = {
        "internal_available_rows": int(len(internal_group)),
        "external_available_rows": int(len(legitphish_group)),
        "balanced_internal_rows": int(sample_size),
        "balanced_external_rows": int(sample_size),
        "total_balanced_rows": int(sample_size * 2),
    }
    return x, y, counts


def run_one_origin_experiment(
    experiment: str,
    semantic_label: int,
    internal: pd.DataFrame,
    legitphish: pd.DataFrame,
) -> dict[str, Any]:
    """Run a shallow dataset-origin tree for PhiUSIIL vs LegitPhish."""

    x, y, counts = build_origin_dataset(internal, legitphish, semantic_label)
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=ORIGIN_TEST_SIZE,
        random_state=ORIGIN_RANDOM_STATE,
        stratify=y,
    )
    model = DecisionTreeClassifier(
        max_depth=ORIGIN_TREE_MAX_DEPTH,
        random_state=ORIGIN_RANDOM_STATE,
    )
    model.fit(x_train, y_train)
    y_pred = model.predict(x_test)
    legitphish_probability = model.predict_proba(x_test)[
        :,
        list(model.classes_).index(EXTERNAL_ORIGIN_LABEL),
    ]
    importances = (
        pd.DataFrame(
            {
                "feature": FEATURE_NAMES,
                "importance": model.feature_importances_,
            }
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
    return {
        "experiment": experiment,
        "semantic_label": int(semantic_label),
        "origin_label_meaning": {
            "0": "PhiUSIIL source",
            "1": "LegitPhish source",
        },
        "post_hoc_diagnostic": True,
        **counts,
        "origin_accuracy": float(accuracy_score(y_test, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, legitphish_probability)),
        "tree_depth": int(model.get_depth()),
        "leaves": int(model.get_n_leaves()),
        "top_feature_importances": importances.head(10).to_dict(orient="records"),
    }


def run_legitphish_origin_diagnostics(
    internal: pd.DataFrame,
    legitphish: pd.DataFrame,
) -> dict[str, Any]:
    """Run legitimate-only and phishing-only origin diagnostics."""

    payload = {
        "analysis_type": "POST-HOC DIAGNOSTIC ANALYSIS",
        "model_purpose": "dataset-origin classification, not phishing detection",
        "origin_label_meaning": {
            "0": "PhiUSIIL source",
            "1": "LegitPhish source",
        },
        "random_state": ORIGIN_RANDOM_STATE,
        "diagnostic_tree_max_depth": ORIGIN_TREE_MAX_DEPTH,
        "test_size": ORIGIN_TEST_SIZE,
        "experiments": [
            run_one_origin_experiment(
                "legitimate_only_phiusiil_vs_legitphish_origin",
                LEGITIMATE_LABEL,
                internal,
                legitphish,
            ),
            run_one_origin_experiment(
                "phishing_only_phiusiil_vs_legitphish_origin",
                PHISHING_LABEL,
                internal,
                legitphish,
            ),
        ],
        "safety_statement": (
            "Origin diagnostics used local feature matrices only; no URL was "
            "opened, requested, resolved, or contacted."
        ),
    }
    MULTI_DATASET_ORIGIN_PERFORMANCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MULTI_DATASET_ORIGIN_PERFORMANCE_FILE.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")
    return payload


def top_shift_lines(shift: pd.DataFrame, comparison_id: str, count: int = 5) -> list[str]:
    """Format top shifted features for the markdown report."""

    rows = shift[shift["comparison_id"] == comparison_id].head(count)
    return [
        (
            f"- {row.feature}: KS={row.ks_statistic:.3f}, "
            f"internal_mean={row.internal_mean:.3f}, external_mean={row.external_mean:.3f}"
        )
        for row in rows.itertuples()
    ]


def origin_line(result: dict[str, Any]) -> str:
    """Format one origin diagnostic result."""

    top_features = ", ".join(
        feature["feature"] for feature in result["top_feature_importances"][:5]
    )
    return (
        f"- {result['experiment']}: accuracy={result['origin_accuracy']:.6f}, "
        f"AUC={result['roc_auc']:.6f}, top features={top_features}"
    )


def write_shift_report(
    shift: pd.DataFrame,
    similarity: pd.DataFrame,
    origin_payload: dict[str, Any],
) -> None:
    """Write an aggregate-only research note for the multi-dataset shifts."""

    legitimate_similarity = similarity[similarity["semantic_class"] == "legitimate"]
    phishing_similarity = similarity[similarity["semantic_class"] == "phishing"]
    closest_legitimate = legitimate_similarity.iloc[0]
    closest_phishing = phishing_similarity.iloc[0]
    report = [
        "# Multi-Dataset Class-Conditional Shift Analysis",
        "",
        "## Scope",
        "",
        "This post-hoc diagnostic compares the fixed Tier E lexical feature space across PhiUSIIL, URL-Phish, and LegitPhish. It uses only local feature matrices derived from URL strings; no URL was opened, requested, resolved, or contacted.",
        "",
        "## Similarity Summary",
        "",
        "| Semantic class | External dataset | Mean KS | Median KS | Max KS | Rank |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]

    for row in similarity.itertuples():
        report.append(
            f"| {row.semantic_class} | {row.external_dataset} | "
            f"{row.mean_ks_statistic:.6f} | {row.median_ks_statistic:.6f} | "
            f"{row.max_ks_statistic:.6f} | {row.similarity_rank_within_class} |"
        )

    report.extend(
        [
            "",
            "Lower average KS indicates greater lexical similarity to the matching PhiUSIIL class. By that criterion, "
            f"{closest_legitimate.external_dataset} is more similar to PhiUSIIL legitimate URLs, while "
            f"{closest_phishing.external_dataset} is more similar to PhiUSIIL phishing URLs.",
            "",
            "## Top Legitimate-Class Shifts",
            "",
            "PhiUSIIL legitimate vs URL-Phish benign:",
            *top_shift_lines(shift, "A_phiusiil_legitimate_vs_url_phish_benign"),
            "",
            "PhiUSIIL legitimate vs LegitPhish legitimate:",
            *top_shift_lines(shift, "B_phiusiil_legitimate_vs_legitphish_legitimate"),
            "",
            "## Top Phishing-Class Shifts",
            "",
            "PhiUSIIL phishing vs URL-Phish phishing:",
            *top_shift_lines(shift, "C_phiusiil_phishing_vs_url_phish_phishing"),
            "",
            "PhiUSIIL phishing vs LegitPhish phishing:",
            *top_shift_lines(shift, "D_phiusiil_phishing_vs_legitphish_phishing"),
            "",
            "## PhiUSIIL vs LegitPhish Origin Diagnostics",
            "",
            *[origin_line(result) for result in origin_payload["experiments"]],
            "",
            "These origin trees are diagnostic only. They estimate whether a shallow classifier can separate dataset source within a fixed semantic class, and they are not phishing-detection models.",
        ]
    )
    SHIFT_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    SHIFT_REPORT_FILE.write_text("\n".join(report) + "\n", encoding="utf-8")


def run_multi_dataset_shift_analysis() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Run multi-dataset shift and origin diagnostics."""

    internal, url_phish, legitphish = load_feature_matrices()
    shift = build_shift_table(internal, url_phish, legitphish)
    similarity = shift_similarity_summary(shift)
    origin_payload = run_legitphish_origin_diagnostics(internal, legitphish)
    MULTI_DATASET_FEATURE_SHIFT_FILE.parent.mkdir(parents=True, exist_ok=True)
    shift.to_csv(MULTI_DATASET_FEATURE_SHIFT_FILE, index=False)
    save_shift_figures(shift)
    write_shift_report(shift, similarity, origin_payload)
    return shift, similarity, origin_payload


def main() -> None:
    """Run multi-dataset shift analysis."""

    shift, similarity, origin_payload = run_multi_dataset_shift_analysis()
    print(f"Saved: {MULTI_DATASET_FEATURE_SHIFT_FILE}")
    print(f"Saved: {MULTI_DATASET_ORIGIN_PERFORMANCE_FILE}")
    print(f"Saved: {BENIGN_SHIFT_ACROSS_DATASETS_FIGURE}")
    print(f"Saved: {PHISHING_SHIFT_ACROSS_DATASETS_FIGURE}")
    print(f"Saved: {SHIFT_REPORT_FILE}")
    print(similarity.to_string(index=False))
    for result in origin_payload["experiments"]:
        print(
            {
                "experiment": result["experiment"],
                "origin_accuracy": result["origin_accuracy"],
                "roc_auc": result["roc_auc"],
                "top_features": result["top_feature_importances"][:5],
            }
        )
    print(shift.groupby(["semantic_class", "external_dataset"]).size().to_dict())


if __name__ == "__main__":
    main()
