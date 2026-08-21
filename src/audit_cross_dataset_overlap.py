"""Audit cross-dataset URL and domain overlap using local strings only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import (
    CROSS_DATASET_OVERLAP_SUMMARY_FILE,
    LEGITPHISH_RAW_FILE,
    RAW_DATA_FILE,
    URL_PHISH_RAW_FILE,
)
from src.domain_utils import extract_registrable_domain
from src.inspect_data import find_target_column
from src.prepare_data import find_url_column
from src.prepare_external_data import LABEL_COLUMN, URL_COLUMN, normalize_url_phish_labels
from src.prepare_legitphish_data import (
    LEGITPHISH_TARGET_COLUMN,
    LEGITPHISH_URL_COLUMN,
    analysis_rows,
)
from src.predict import LEGITIMATE_LABEL, PHISHING_LABEL
from src.url_utils import strip_url


OVERLAP_AUDIT_REPORT_FILE = Path("research/cross_dataset_overlap_audit.md")


def normalized_url_key(url: str) -> str:
    """Return the project's existing stripped-lower normalized URL key."""

    return strip_url(url).lower()


def phiusiil_rows(raw_file: Path = RAW_DATA_FILE) -> pd.DataFrame:
    """Load PhiUSIIL raw URL strings and project labels."""

    raw = pd.read_csv(raw_file)
    url_column = find_url_column(raw)
    target_column = find_target_column(raw)
    return pd.DataFrame(
        {
            "url": raw[url_column].astype(str),
            "label": raw[target_column].astype(int),
        }
    )


def url_phish_rows(raw_file: Path = URL_PHISH_RAW_FILE) -> pd.DataFrame:
    """Load URL-Phish raw URL strings with labels in project convention."""

    raw = pd.read_csv(raw_file)
    return pd.DataFrame(
        {
            "url": raw[URL_COLUMN].astype(str),
            "label": normalize_url_phish_labels(raw[LABEL_COLUMN]),
        }
    )


def legitphish_rows(raw_file: Path = LEGITPHISH_RAW_FILE) -> pd.DataFrame:
    """Load usable LegitPhish raw URL strings with project labels."""

    raw = analysis_rows(pd.read_csv(raw_file))
    return pd.DataFrame(
        {
            "url": raw[LEGITPHISH_URL_COLUMN].astype(str),
            "label": raw[LEGITPHISH_TARGET_COLUMN].astype(int),
        }
    ).reset_index(drop=True)


def add_overlap_keys(rows: pd.DataFrame) -> pd.DataFrame:
    """Add exact, normalized, and registrable-domain keys."""

    keyed = rows.copy()
    unique_urls = pd.Series(keyed["url"].unique())
    exact_key_map = {url: strip_url(url) for url in unique_urls}
    normalized_key_map = {url: normalized_url_key(url) for url in unique_urls}
    domain_key_map = {url: extract_registrable_domain(url) for url in unique_urls}
    keyed["exact_key"] = keyed["url"].map(exact_key_map)
    keyed["normalized_key"] = keyed["url"].map(normalized_key_map)
    keyed["registrable_domain"] = keyed["url"].map(domain_key_map)
    return keyed


def conflict_counts(
    internal: pd.DataFrame,
    external: pd.DataFrame,
    key_column: str,
) -> dict[str, int]:
    """Count shared keys whose labels conflict across datasets."""

    internal_phishing = set(internal.loc[internal["label"] == PHISHING_LABEL, key_column])
    internal_legitimate = set(internal.loc[internal["label"] == LEGITIMATE_LABEL, key_column])
    external_phishing = set(external.loc[external["label"] == PHISHING_LABEL, key_column])
    external_legitimate = set(external.loc[external["label"] == LEGITIMATE_LABEL, key_column])
    phishing_to_legitimate = internal_phishing & external_legitimate
    legitimate_to_phishing = internal_legitimate & external_phishing
    conflict_keys = set(phishing_to_legitimate) | set(legitimate_to_phishing)
    return {
        "shared_keys_with_any_cross_label_conflict": int(len(set(conflict_keys))),
        "phiusiil_phishing_external_legitimate_keys": int(len(phishing_to_legitimate)),
        "phiusiil_legitimate_external_phishing_keys": int(len(legitimate_to_phishing)),
    }


def same_label_overlap_counts(
    internal: pd.DataFrame,
    external: pd.DataFrame,
    key_column: str,
) -> dict[str, Any]:
    """Count class-conditional same-label overlap for one key type."""

    records = {}
    for label, label_name in [
        (PHISHING_LABEL, "phishing"),
        (LEGITIMATE_LABEL, "legitimate"),
    ]:
        internal_label = internal[internal["label"] == label]
        external_label = external[external["label"] == label]
        shared = set(internal_label[key_column]) & set(external_label[key_column])
        records[f"phiusiil_{label_name}_external_{label_name}"] = {
            "unique_shared_keys": int(len(shared)),
            "phiusiil_rows_with_shared_key": int(internal_label[key_column].isin(shared).sum()),
            "external_rows_with_shared_key": int(external_label[key_column].isin(shared).sum()),
        }
    return records


def key_overlap_summary(
    internal: pd.DataFrame,
    external: pd.DataFrame,
    key_column: str,
) -> dict[str, Any]:
    """Summarize overlap for exact URL, normalized URL, or domain keys."""

    internal_keys = set(internal[key_column])
    external_keys = set(external[key_column])
    shared_keys = internal_keys & external_keys
    return {
        "unique_phiusiil_keys": int(len(internal_keys)),
        "unique_external_keys": int(len(external_keys)),
        "unique_shared_keys": int(len(shared_keys)),
        "phiusiil_rows_with_shared_key": int(internal[key_column].isin(shared_keys).sum()),
        "external_rows_with_shared_key": int(external[key_column].isin(shared_keys).sum()),
        "overlap_percentage_of_phiusiil_keys": (
            len(shared_keys) / len(internal_keys) * 100 if internal_keys else 0.0
        ),
        "overlap_percentage_of_external_keys": (
            len(shared_keys) / len(external_keys) * 100 if external_keys else 0.0
        ),
        "class_conditional_same_label_overlap": same_label_overlap_counts(
            internal,
            external,
            key_column,
        ),
        "cross_label_conflicts": conflict_counts(internal, external, key_column),
    }


def class_composition(rows: pd.DataFrame) -> dict[str, Any]:
    """Return class counts and proportions."""

    counts = rows["label"].value_counts().to_dict()
    total = int(len(rows))
    phishing = int(counts.get(PHISHING_LABEL, 0))
    legitimate = int(counts.get(LEGITIMATE_LABEL, 0))
    return {
        "total": total,
        "phishing": phishing,
        "legitimate": legitimate,
        "phishing_proportion": phishing / total if total else 0.0,
        "legitimate_proportion": legitimate / total if total else 0.0,
    }


def predictions_by_class(rows: pd.DataFrame) -> dict[str, int]:
    """Return predicted-label counts for a row subset."""

    counts = rows["predicted_label"].value_counts().to_dict()
    return {
        "predicted_phishing": int(counts.get(PHISHING_LABEL, 0)),
        "predicted_legitimate": int(counts.get(LEGITIMATE_LABEL, 0)),
    }


def legitphish_seen_unseen_composition(
    phiusiil: pd.DataFrame,
    legitphish: pd.DataFrame,
) -> dict[str, Any]:
    """Summarize LegitPhish seen/unseen-domain class and prediction composition."""

    import joblib

    from src.config import LEGITPHISH_EXTERNAL_MATRIX_FILE, OPTIMIZED_MODEL_FILE
    from src.feature_definitions import FEATURE_NAMES

    legitphish_domains = legitphish["registrable_domain"]
    phiusiil_domains = set(phiusiil["registrable_domain"])
    seen_mask = legitphish_domains.isin(phiusiil_domains)
    matrix = pd.read_csv(LEGITPHISH_EXTERNAL_MATRIX_FILE)
    model = joblib.load(OPTIMIZED_MODEL_FILE)
    row_predictions = legitphish[["label"]].copy()
    row_predictions["predicted_label"] = model.predict(matrix[FEATURE_NAMES]).astype(int)

    def segment(mask: pd.Series) -> dict[str, Any]:
        subset = row_predictions[mask.to_numpy()]
        return {
            "class_composition": class_composition(subset.rename(columns={"label": "label"})),
            "predictions_by_class": predictions_by_class(subset),
        }

    return {
        "seen_domain_subset": segment(seen_mask),
        "unseen_domain_subset": segment(~seen_mask),
        "unseen_domain_metric_note": (
            "The prior unseen-domain ROC-AUC of 0.5 was a valid two-class "
            "calculation, not a single-class fallback: the subset contained "
            "both phishing and legitimate rows, but the frozen model assigned "
            "all unseen-domain rows to the phishing class."
        ),
    }


def pair_overlap_audit(
    external_name: str,
    phiusiil: pd.DataFrame,
    external: pd.DataFrame,
) -> dict[str, Any]:
    """Audit one PhiUSIIL/external dataset pair."""

    return {
        "external_dataset": external_name,
        "row_counts": {
            "phiusiil": int(len(phiusiil)),
            "external": int(len(external)),
        },
        "class_counts": {
            "phiusiil": class_composition(phiusiil),
            "external": class_composition(external),
        },
        "exact_url_overlap": key_overlap_summary(phiusiil, external, "exact_key"),
        "normalized_url_overlap": key_overlap_summary(
            phiusiil,
            external,
            "normalized_key",
        ),
        "registrable_domain_overlap": key_overlap_summary(
            phiusiil,
            external,
            "registrable_domain",
        ),
    }


def write_overlap_report(payload: dict[str, Any]) -> None:
    """Write the markdown overlap audit without raw URLs or domains."""

    lines = [
        "# Cross-Dataset Overlap Audit",
        "",
        "## Scope",
        "",
        "This audit compares PhiUSIIL against URL-Phish and LegitPhish using local URL strings only. It reports aggregate overlap counts for exact stripped URLs, stripped-lower normalized URLs, and offline registrable-domain keys. It does not list overlapping URLs or domains.",
        "",
        "## Pairwise Overlap",
        "",
        "| External dataset | Exact shared URLs | Normalized shared URLs | Shared registrable domains | Exact cross-label conflicts | Normalized cross-label conflicts | Domain cross-label conflicts |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for pair in payload["pairwise_overlap"]:
        lines.append(
            f"| {pair['external_dataset']} | "
            f"{pair['exact_url_overlap']['unique_shared_keys']:,} | "
            f"{pair['normalized_url_overlap']['unique_shared_keys']:,} | "
            f"{pair['registrable_domain_overlap']['unique_shared_keys']:,} | "
            f"{pair['exact_url_overlap']['cross_label_conflicts']['shared_keys_with_any_cross_label_conflict']:,} | "
            f"{pair['normalized_url_overlap']['cross_label_conflicts']['shared_keys_with_any_cross_label_conflict']:,} | "
            f"{pair['registrable_domain_overlap']['cross_label_conflicts']['shared_keys_with_any_cross_label_conflict']:,} |"
        )

    legit = payload["legitphish_seen_unseen_composition"]
    seen = legit["seen_domain_subset"]["class_composition"]
    unseen = legit["unseen_domain_subset"]["class_composition"]
    seen_pred = legit["seen_domain_subset"]["predictions_by_class"]
    unseen_pred = legit["unseen_domain_subset"]["predictions_by_class"]
    lines.extend(
        [
            "",
            "## LegitPhish Seen/Unseen-Domain Composition",
            "",
            "| Segment | Total | Phishing | Legitimate | Phishing proportion | Legitimate proportion | Predicted phishing | Predicted legitimate |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            (
                f"| Seen in PhiUSIIL | {seen['total']:,} | {seen['phishing']:,} | "
                f"{seen['legitimate']:,} | {seen['phishing_proportion']:.6f} | "
                f"{seen['legitimate_proportion']:.6f} | {seen_pred['predicted_phishing']:,} | "
                f"{seen_pred['predicted_legitimate']:,} |"
            ),
            (
                f"| Unseen in PhiUSIIL | {unseen['total']:,} | {unseen['phishing']:,} | "
                f"{unseen['legitimate']:,} | {unseen['phishing_proportion']:.6f} | "
                f"{unseen['legitimate_proportion']:.6f} | {unseen_pred['predicted_phishing']:,} | "
                f"{unseen_pred['predicted_legitimate']:,} |"
            ),
            "",
            "## Unseen-Domain Metric Note",
            "",
            legit["unseen_domain_metric_note"],
            "",
            "The unseen-domain subset is extremely class-skewed toward phishing. Its high phishing F1 coexists with ROC-AUC and balanced accuracy of 0.5 because the model predicts every row as phishing, yielding phishing recall of 1.0 and legitimate specificity of 0.0.",
            "",
            "## Safety Statement",
            "",
            payload["safety_statement"],
        ]
    )
    OVERLAP_AUDIT_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OVERLAP_AUDIT_REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_cross_dataset_overlap_audit() -> dict[str, Any]:
    """Run and save the cross-dataset overlap audit."""

    phiusiil = add_overlap_keys(phiusiil_rows())
    url_phish = add_overlap_keys(url_phish_rows())
    legitphish = add_overlap_keys(legitphish_rows())
    payload = {
        "analysis_type": "FINAL DATA-INTEGRITY AUDIT",
        "normalization": {
            "exact_url_key": "strip_url(url)",
            "normalized_url_key": "strip_url(url).lower()",
            "registrable_domain_key": (
                "extract_registrable_domain(url) using local publicsuffix2 parsing"
            ),
        },
        "pairwise_overlap": [
            pair_overlap_audit("URL-Phish", phiusiil, url_phish),
            pair_overlap_audit("LegitPhish", phiusiil, legitphish),
        ],
        "legitphish_seen_unseen_composition": legitphish_seen_unseen_composition(
            phiusiil,
            legitphish,
        ),
        "raw_values_committed": False,
        "safety_statement": (
            "All overlap keys were computed from local strings with local parsing "
            "only; no URL was opened, requested, resolved, scraped, or contacted."
        ),
    }
    CROSS_DATASET_OVERLAP_SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CROSS_DATASET_OVERLAP_SUMMARY_FILE.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")
    write_overlap_report(payload)
    return payload


def main() -> None:
    """Run the final cross-dataset overlap audit."""

    payload = run_cross_dataset_overlap_audit()
    print(f"Saved: {CROSS_DATASET_OVERLAP_SUMMARY_FILE}")
    print(f"Saved: {OVERLAP_AUDIT_REPORT_FILE}")
    for pair in payload["pairwise_overlap"]:
        print(
            {
                "external_dataset": pair["external_dataset"],
                "exact_shared_urls": pair["exact_url_overlap"]["unique_shared_keys"],
                "normalized_shared_urls": pair["normalized_url_overlap"][
                    "unique_shared_keys"
                ],
                "shared_registrable_domains": pair["registrable_domain_overlap"][
                    "unique_shared_keys"
                ],
            }
        )


if __name__ == "__main__":
    main()
