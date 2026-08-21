"""Build a deterministic registrable-domain-disjoint split.

URLs are treated as inert text. Registrable domains are extracted with the
offline bundled Public Suffix List through `src.domain_utils`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from src.config import RANDOM_STATE, RAW_DATA_FILE, RESULTS_DIRECTORY
from src.domain_utils import UNKNOWN_DOMAIN_GROUP, extract_registrable_domain
from src.prepare_data import find_url_column


DOMAIN_DISJOINT_SPLIT_SUMMARY_FILE = (
    RESULTS_DIRECTORY / "domain_disjoint_split_summary.json"
)
TARGET_COLUMN = "label"
SPLIT_TARGET_FRACTIONS = {
    "train": 0.70,
    "validation": 0.15,
    "test": 0.15,
}
SPLIT_NAMES = ("train", "validation", "test")


@dataclass(frozen=True)
class DomainSplit:
    """Container for row assignments and domain metadata."""

    row_indices: dict[str, list[int]]
    domain_sets: dict[str, set[str]]
    domain_frame: pd.DataFrame
    raw_dataframe: pd.DataFrame


def class_counts(labels: pd.Series) -> dict[str, int]:
    """Return class counts with stable string keys."""

    counts = labels.value_counts().sort_index().to_dict()
    return {str(label): int(counts.get(label, 0)) for label in [0, 1]}


def class_percentages(labels: pd.Series) -> dict[str, float]:
    """Return class percentages with stable string keys."""

    counts = class_counts(labels)
    total = sum(counts.values())

    if total == 0:
        return {"0": 0.0, "1": 0.0}

    return {label: count / total for label, count in counts.items()}


def build_domain_frame(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Build per-row domain keys and per-domain class counts."""

    url_column = find_url_column(raw_dataframe)
    row_frame = pd.DataFrame(
        {
            "row_index": raw_dataframe.index.astype(int),
            "registrable_domain": raw_dataframe[url_column].map(
                extract_registrable_domain
            ),
            "label": raw_dataframe[TARGET_COLUMN].astype(int),
        }
    )
    grouped = (
        row_frame.groupby("registrable_domain")
        .agg(
            row_count=("row_index", "size"),
            phishing_count=("label", lambda values: int((values == 0).sum())),
            legitimate_count=("label", lambda values: int((values == 1).sum())),
            row_indices=("row_index", lambda values: [int(value) for value in values]),
        )
        .reset_index()
    )

    return grouped


def _score_assignment(
    current: dict[str, dict[str, int]],
    split_name: str,
    group: pd.Series,
    targets: dict[str, dict[str, float]],
) -> float:
    """Score how well assigning one group to a split matches target totals."""

    score = 0.0

    for candidate_split in SPLIT_NAMES:
        prospective_rows = current[candidate_split]["rows"]
        prospective_phishing = current[candidate_split]["phishing"]
        prospective_legitimate = current[candidate_split]["legitimate"]

        if candidate_split == split_name:
            prospective_rows += int(group["row_count"])
            prospective_phishing += int(group["phishing_count"])
            prospective_legitimate += int(group["legitimate_count"])

        row_error = (prospective_rows - targets[candidate_split]["rows"]) / targets[
            candidate_split
        ]["rows"]
        phishing_error = (
            prospective_phishing - targets[candidate_split]["phishing"]
        ) / max(targets[candidate_split]["phishing"], 1)
        legitimate_error = (
            prospective_legitimate - targets[candidate_split]["legitimate"]
        ) / max(targets[candidate_split]["legitimate"], 1)

        score += row_error**2 + phishing_error**2 + legitimate_error**2

        if prospective_rows > targets[candidate_split]["rows"] * 1.04:
            score += 1.0

    return score


def allocate_domains(domain_frame: pd.DataFrame) -> dict[str, list[str]]:
    """Allocate whole registrable domains into deterministic split groups."""

    total_rows = int(domain_frame["row_count"].sum())
    total_phishing = int(domain_frame["phishing_count"].sum())
    total_legitimate = int(domain_frame["legitimate_count"].sum())
    targets = {
        split_name: {
            "rows": total_rows * fraction,
            "phishing": total_phishing * fraction,
            "legitimate": total_legitimate * fraction,
        }
        for split_name, fraction in SPLIT_TARGET_FRACTIONS.items()
    }
    rng = np.random.default_rng(RANDOM_STATE)
    shuffled = domain_frame.copy()
    shuffled["_tie_breaker"] = rng.random(len(shuffled))
    shuffled = shuffled.sort_values(
        ["row_count", "_tie_breaker"],
        ascending=[False, True],
    )
    assignments: dict[str, list[str]] = {split_name: [] for split_name in SPLIT_NAMES}
    current = {
        split_name: {"rows": 0, "phishing": 0, "legitimate": 0}
        for split_name in SPLIT_NAMES
    }

    for _, group in shuffled.iterrows():
        best_split = min(
            SPLIT_NAMES,
            key=lambda split_name: (
                _score_assignment(current, split_name, group, targets),
                current[split_name]["rows"],
                split_name,
            ),
        )
        assignments[best_split].append(str(group["registrable_domain"]))
        current[best_split]["rows"] += int(group["row_count"])
        current[best_split]["phishing"] += int(group["phishing_count"])
        current[best_split]["legitimate"] += int(group["legitimate_count"])

    return assignments


def build_domain_split(raw_dataframe: pd.DataFrame | None = None) -> DomainSplit:
    """Build the domain-disjoint split assignment."""

    if raw_dataframe is None:
        raw_dataframe = pd.read_csv(RAW_DATA_FILE)

    domain_frame = build_domain_frame(raw_dataframe)
    assignments = allocate_domains(domain_frame)
    domain_to_rows = domain_frame.set_index("registrable_domain")[
        "row_indices"
    ].to_dict()
    row_indices = {
        split_name: sorted(
            row_index
            for domain in domains
            for row_index in domain_to_rows[domain]
        )
        for split_name, domains in assignments.items()
    }
    domain_sets = {
        split_name: set(domains) for split_name, domains in assignments.items()
    }

    assert_domain_disjoint(domain_sets)

    return DomainSplit(
        row_indices=row_indices,
        domain_sets=domain_sets,
        domain_frame=domain_frame,
        raw_dataframe=raw_dataframe,
    )


def assert_domain_disjoint(domain_sets: dict[str, set[str]]) -> None:
    """Assert that no registrable domain appears in multiple splits."""

    intersections = domain_intersections(domain_sets)

    if any(count != 0 for count in intersections.values()):
        raise ValueError(f"Domain overlap detected: {intersections}")


def domain_intersections(domain_sets: dict[str, set[str]]) -> dict[str, int]:
    """Return pairwise domain-intersection counts."""

    return {
        "train_validation": len(domain_sets["train"] & domain_sets["validation"]),
        "train_test": len(domain_sets["train"] & domain_sets["test"]),
        "validation_test": len(domain_sets["validation"] & domain_sets["test"]),
    }


def duplicate_diagnostics(
    raw_dataframe: pd.DataFrame,
    domain_frame: pd.DataFrame,
) -> dict[str, Any]:
    """Return URL duplicate and domain-group diagnostics without raw strings."""

    url_column = find_url_column(raw_dataframe)
    stripped_lower_urls = raw_dataframe[url_column].astype(str).str.strip().str.lower()
    group_sizes = domain_frame["row_count"].sort_values(ascending=False)
    multi_url_domains = int((domain_frame["row_count"] > 1).sum())
    top_group_sizes = (
        domain_frame.sort_values("row_count", ascending=False)
        .head(10)[["row_count", "phishing_count", "legitimate_count"]]
        .to_dict(orient="records")
    )

    return {
        "exact_duplicate_raw_url_values": int(raw_dataframe[url_column].duplicated().sum()),
        "rows_with_exact_duplicate_raw_url": int(
            raw_dataframe[url_column].duplicated(keep=False).sum()
        ),
        "normalized_duplicate_stripped_lower_url_values": int(
            stripped_lower_urls.duplicated().sum()
        ),
        "rows_with_normalized_duplicate_stripped_lower_url": int(
            stripped_lower_urls.duplicated(keep=False).sum()
        ),
        "domains_with_multiple_urls": multi_url_domains,
        "median_urls_per_domain": float(group_sizes.median()),
        "top_domain_group_sizes_without_domain_names": top_group_sizes,
    }


def split_summary(domain_split: DomainSplit) -> dict[str, Any]:
    """Build compact split metadata."""

    raw_dataframe = domain_split.raw_dataframe
    total_rows = int(len(raw_dataframe))
    all_domains = set().union(*domain_split.domain_sets.values())
    split_details = {}

    for split_name, indices in domain_split.row_indices.items():
        labels = raw_dataframe.loc[indices, TARGET_COLUMN].astype(int)
        split_details[split_name] = {
            "row_count": int(len(indices)),
            "row_percentage": len(indices) / total_rows,
            "unique_registrable_domains": int(len(domain_split.domain_sets[split_name])),
            "class_counts": class_counts(labels),
            "class_percentages": class_percentages(labels),
        }

    unknown_rows = int(
        domain_split.domain_frame.loc[
            domain_split.domain_frame["registrable_domain"] == UNKNOWN_DOMAIN_GROUP,
            "row_count",
        ].sum()
    )

    return {
        "random_state": RANDOM_STATE,
        "split_method": (
            "Deterministic greedy whole-domain allocation toward 70/15/15 "
            "row and class-count targets."
        ),
        "target_fractions": SPLIT_TARGET_FRACTIONS,
        "total_rows": total_rows,
        "total_unique_registrable_domains": int(len(all_domains)),
        "split_details": split_details,
        "domain_intersection_counts": domain_intersections(domain_split.domain_sets),
        "unknown_or_unparseable_group_rows": unknown_rows,
        "row_indices": domain_split.row_indices,
        "duplicate_diagnostics": duplicate_diagnostics(
            raw_dataframe,
            domain_split.domain_frame,
        ),
        "public_suffix_parser": {
            "package": "publicsuffix2",
            "version_constraint": ">=2.20191221,<3.0",
            "runtime_fetch_used": False,
            "limitation": (
                "The bundled Public Suffix List reflects the installed package "
                "version and may differ from future PSL snapshots."
            ),
        },
        "safety_statement": (
            "Registrable domains were extracted from URL strings locally; no "
            "URL was opened, requested, resolved, pinged, or contacted."
        ),
    }


def save_domain_split_summary(summary: dict[str, Any]) -> None:
    """Save the domain-disjoint split summary."""

    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)

    with DOMAIN_DISJOINT_SPLIT_SUMMARY_FILE.open("w", encoding="utf-8") as file:
        json.dump(summary, file)
        file.write("\n")


def main() -> None:
    """Build and save the domain-disjoint split summary."""

    domain_split = build_domain_split()
    summary = split_summary(domain_split)
    save_domain_split_summary(summary)

    print(f"Rows: {summary['total_rows']:,}")
    print(f"Unique registrable domains: {summary['total_unique_registrable_domains']:,}")
    for split_name, details in summary["split_details"].items():
        print(
            f"{split_name}: {details['row_count']:,} rows, "
            f"{details['unique_registrable_domains']:,} domains, "
            f"classes={details['class_counts']}"
        )
    print(f"Intersections: {summary['domain_intersection_counts']}")
    print(f"Saved: {DOMAIN_DISJOINT_SPLIT_SUMMARY_FILE}")


if __name__ == "__main__":
    main()
