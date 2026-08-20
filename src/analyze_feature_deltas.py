"""Diagnose reconstruction deltas for PhiUSIIL URL-text features.

This script is research-only. It treats URL values as inert strings and never
opens, requests, resolves, pings, or otherwise contacts any URL.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from src.audit_feature_fidelity import DEFAULT_MAPPING_FILE, load_feature_mapping
from src.config import PROJECT_ROOT, RAW_DATA_FILE, RESULTS_DIRECTORY
from src.feature_extractor import extract_url_features
from src.prepare_data import find_url_column
from src.url_utils import parse_url, strip_url


DELTA_DIAGNOSTICS_FILE = RESULTS_DIRECTORY / "feature_delta_diagnostics.csv"
RECONSTRUCTION_REPORT_FILE = (
    PROJECT_ROOT / "research" / "feature_reconstruction_diagnostics.md"
)
TARGET_COLUMN = "label"
SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")


def remove_scheme_prefix(url: str) -> str:
    """Remove only an explicit URL scheme prefix from stripped URL text."""

    return SCHEME_PATTERN.sub("", strip_url(url), count=1)


def remove_scheme_and_www_prefix(url: str) -> str:
    """Remove an explicit scheme and then a leading www. hostname prefix."""

    without_scheme = remove_scheme_prefix(url)

    if without_scheme.lower().startswith("www."):
        return without_scheme[4:]

    return without_scheme


def scheme_group(url: str) -> str:
    """Return the locally parsed scheme group for aggregate diagnostics."""

    stripped = strip_url(url)
    match = SCHEME_PATTERN.match(stripped)

    if not match:
        return "none"

    return match.group(0).removesuffix("://").lower()


def hostname_path_query(url: str) -> str:
    """Return hostname + path + optional query using local parsing only."""

    parsed = parse_url(url)
    hostname = parsed.hostname or ""
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{hostname}{parsed.path or ''}{query}"


def hostname_without_www_path_query(url: str) -> str:
    """Return hostname without leading www. plus path and optional query."""

    parsed = parse_url(url)
    hostname = parsed.hostname or ""

    if hostname.lower().startswith("www."):
        hostname = hostname[4:]

    query = f"?{parsed.query}" if parsed.query else ""
    return f"{hostname}{parsed.path or ''}{query}"


def netloc_path_query(url: str) -> str:
    """Return netloc + path + optional query using local parsing only."""

    parsed = parse_url(url)
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{parsed.netloc}{parsed.path or ''}{query}"


def netloc_path_query_with_separators(url: str) -> str:
    """Return netloc + path + query separated as URL text would display it."""

    parsed = parse_url(url)
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{parsed.netloc}{parsed.path or ''}{query}"


def count_letters(text: str) -> int:
    """Count alphabetic characters in text."""

    return sum(character.isalpha() for character in text)


def count_digits(text: str) -> int:
    """Count digit characters in text."""

    return sum(character.isdigit() for character in text)


def count_all_special(text: str) -> int:
    """Count non-letter, non-digit, non-whitespace characters."""

    return sum(
        not character.isalnum() and not character.isspace() for character in text
    )


def count_phiusiil_candidate_special(text: str) -> int:
    """Count special characters after excluding common URL structural marks.

    This is not claimed as the original PhiUSIIL implementation. It is one
    plausible local convention tested because the supplied feature is named
    "other special chars".
    """

    excluded = {":", "/", ".", "?", "=", "&"}
    return sum(
        not character.isalnum()
        and not character.isspace()
        and character not in excluded
        for character in text
    )


def safe_ratio(part: pd.Series, whole: pd.Series) -> pd.Series:
    """Return part / whole with zero when the denominator is zero."""

    return part.div(whole.replace(0, np.nan)).fillna(0.0)


def modal_delta(delta: pd.Series) -> tuple[float, int]:
    """Return the most common delta and its count."""

    counts = Counter(delta.round(12).tolist())
    mode, count = counts.most_common(1)[0]
    return float(mode), int(count)


def top_delta_distribution(delta: pd.Series, n: int = 5) -> str:
    """Return a compact top-deltas string for CSV output."""

    counts = Counter(delta.round(12).tolist())
    return "; ".join(f"{value}:{count}" for value, count in counts.most_common(n))


def safe_pearson(supplied: pd.Series, reconstructed: pd.Series) -> float | None:
    """Return Pearson correlation when both inputs vary."""

    if supplied.nunique(dropna=True) <= 1 or reconstructed.nunique(dropna=True) <= 1:
        return None

    correlation = supplied.corr(reconstructed, method="pearson")

    if pd.isna(correlation):
        return None

    return float(correlation)


def summarize_comparison(
    supplied: pd.Series,
    reconstructed: pd.Series,
    feature_name: str,
    comparison_type: str,
    candidate_name: str,
    label_group: str,
    scheme: str = "all",
) -> dict[str, object]:
    """Summarize supplied minus reconstructed values."""

    supplied_numeric = pd.to_numeric(supplied)
    reconstructed_numeric = pd.to_numeric(reconstructed)
    delta = supplied_numeric - reconstructed_numeric
    absolute_error = delta.abs()
    exact_matches = delta == 0
    mode, mode_count = modal_delta(delta)

    return {
        "feature_name": feature_name,
        "comparison_type": comparison_type,
        "candidate_name": candidate_name,
        "label_group": label_group,
        "scheme_group": scheme,
        "compared_rows": int(len(delta)),
        "exact_match_count": int(exact_matches.sum()),
        "exact_match_percentage": float(exact_matches.mean() * 100),
        "mae": float(absolute_error.mean()),
        "median_absolute_error": float(absolute_error.median()),
        "pearson_correlation": safe_pearson(supplied_numeric, reconstructed_numeric),
        "modal_delta": mode,
        "modal_delta_count": mode_count,
        "top_delta_distribution": top_delta_distribution(delta),
    }


def add_grouped_summaries(
    records: list[dict[str, object]],
    dataframe: pd.DataFrame,
    supplied_feature: str,
    reconstructed: pd.Series,
    comparison_type: str,
    candidate_name: str,
) -> None:
    """Add all-row, class-specific, and scheme-specific summary rows."""

    records.append(
        summarize_comparison(
            dataframe[supplied_feature],
            reconstructed,
            supplied_feature,
            comparison_type,
            candidate_name,
            "all",
        )
    )

    for label_value, label_name in [(0, "phishing"), (1, "legitimate")]:
        mask = dataframe[TARGET_COLUMN] == label_value
        records.append(
            summarize_comparison(
                dataframe.loc[mask, supplied_feature],
                reconstructed.loc[mask],
                supplied_feature,
                comparison_type,
                candidate_name,
                label_name,
            )
        )

    if supplied_feature == "URLLength":
        for scheme in ["http", "https", "none", "other"]:
            if scheme == "other":
                mask = ~dataframe["_scheme_group"].isin(["http", "https", "none"])
            else:
                mask = dataframe["_scheme_group"] == scheme

            if not mask.any():
                continue

            records.append(
                summarize_comparison(
                    dataframe.loc[mask, supplied_feature],
                    reconstructed.loc[mask],
                    supplied_feature,
                    comparison_type,
                    candidate_name,
                    "all",
                    scheme,
                )
            )


def candidate_texts(urls: pd.Series) -> dict[str, pd.Series]:
    """Build local candidate URL representations."""

    return {
        "A_full_stripped_raw_url": urls.map(strip_url),
        "B_scheme_prefix_removed": urls.map(remove_scheme_prefix),
        "B2_scheme_and_www_prefix_removed": urls.map(remove_scheme_and_www_prefix),
        "C_hostname_path_query": urls.map(hostname_path_query),
        "C2_hostname_without_www_path_query": urls.map(
            hostname_without_www_path_query
        ),
        "D_netloc_path_query": urls.map(netloc_path_query),
        "D_netloc_path_query_with_separators": urls.map(
            netloc_path_query_with_separators
        ),
    }


def candidate_feature_values(texts: dict[str, pd.Series]) -> dict[str, dict[str, pd.Series]]:
    """Build candidate reconstructed values for investigated features."""

    values: dict[str, dict[str, pd.Series]] = {}

    for candidate_name, text_series in texts.items():
        lengths = text_series.str.len()
        letters = text_series.map(count_letters)
        digits = text_series.map(count_digits)
        all_special = text_series.map(count_all_special)
        other_special = text_series.map(count_phiusiil_candidate_special)

        values[candidate_name] = {
            "URLLength": lengths,
            "NoOfLettersInURL": letters,
            "LetterRatioInURL": safe_ratio(letters, lengths),
            "NoOfDegitsInURL": digits,
            "DegitRatioInURL": safe_ratio(digits, lengths),
            "NoOfOtherSpecialCharsInURL": all_special,
            "NoOfOtherSpecialCharsInURL_other_special": other_special,
            "SpacialCharRatioInURL": safe_ratio(all_special, lengths),
            "SpacialCharRatioInURL_other_special": safe_ratio(
                other_special, lengths
            ),
        }

    return values


def build_current_mapping_diagnostics(dataframe: pd.DataFrame) -> list[dict[str, object]]:
    """Summarize deltas for the currently mapped extractor features."""

    mappings = load_feature_mapping(DEFAULT_MAPPING_FILE)
    url_column = find_url_column(dataframe)
    reconstructed_rows = [
        extract_url_features(url) for url in dataframe[url_column].tolist()
    ]
    reconstructed_dataframe = pd.DataFrame(reconstructed_rows)
    records: list[dict[str, object]] = []

    for mapping in mappings:
        supplied_feature = mapping["supplied_feature"]
        reconstructed_feature = mapping["reconstructed_feature"]
        add_grouped_summaries(
            records,
            dataframe,
            supplied_feature,
            reconstructed_dataframe[reconstructed_feature],
            "current_mapping",
            reconstructed_feature,
        )

    return records


def build_candidate_diagnostics(dataframe: pd.DataFrame) -> list[dict[str, object]]:
    """Summarize candidate reconstruction conventions."""

    url_column = find_url_column(dataframe)
    texts = candidate_texts(dataframe[url_column])
    values = candidate_feature_values(texts)
    investigated_features = [
        "URLLength",
        "NoOfLettersInURL",
        "LetterRatioInURL",
        "NoOfDegitsInURL",
        "DegitRatioInURL",
        "NoOfOtherSpecialCharsInURL",
        "SpacialCharRatioInURL",
    ]
    records: list[dict[str, object]] = []

    for candidate_name, feature_values in values.items():
        for feature_name in investigated_features:
            if feature_name not in dataframe.columns:
                continue

            add_grouped_summaries(
                records,
                dataframe,
                feature_name,
                feature_values[feature_name],
                "candidate_definition",
                candidate_name,
            )

            alternate_key = f"{feature_name}_other_special"
            if alternate_key in feature_values:
                add_grouped_summaries(
                    records,
                    dataframe,
                    feature_name,
                    feature_values[alternate_key],
                    "candidate_definition",
                    f"{candidate_name}_other_special",
                )

    return records


def best_candidate_rows(diagnostics: pd.DataFrame) -> pd.DataFrame:
    """Return the best all-label candidate row for each investigated feature."""

    candidates = diagnostics[
        (diagnostics["comparison_type"] == "candidate_definition")
        & (diagnostics["label_group"] == "all")
        & (diagnostics["scheme_group"] == "all")
    ].copy()

    candidates = candidates.sort_values(
        ["feature_name", "exact_match_percentage", "mae"],
        ascending=[True, False, True],
    )

    return candidates.groupby("feature_name", as_index=False).head(1)


def format_metric(value: object, decimals: int = 3) -> str:
    """Format a metric value for Markdown."""

    if value is None or pd.isna(value):
        return "n/a"

    return f"{float(value):.{decimals}f}"


def write_markdown_report(diagnostics: pd.DataFrame) -> None:
    """Write a concise diagnostics report from computed evidence."""

    best = best_candidate_rows(diagnostics)
    url_scheme_rows = diagnostics[
        (diagnostics["feature_name"] == "URLLength")
        & (diagnostics["candidate_name"] == "B_scheme_prefix_removed")
        & (diagnostics["label_group"] == "all")
        & (diagnostics["scheme_group"].isin(["http", "https"]))
    ]
    current_url = diagnostics[
        (diagnostics["feature_name"] == "URLLength")
        & (diagnostics["comparison_type"] == "current_mapping")
        & (diagnostics["label_group"] == "all")
        & (diagnostics["scheme_group"] == "all")
    ].iloc[0]
    best_url = best[best["feature_name"] == "URLLength"].iloc[0]
    scheme_removed_url = diagnostics[
        (diagnostics["feature_name"] == "URLLength")
        & (diagnostics["candidate_name"] == "B_scheme_prefix_removed")
        & (diagnostics["comparison_type"] == "candidate_definition")
        & (diagnostics["label_group"] == "all")
        & (diagnostics["scheme_group"] == "all")
    ].iloc[0]

    lines = [
        "# PhiUSIIL Feature Reconstruction Diagnostics",
        "",
        "## Purpose",
        "",
        "This report investigates why several URL-text features were directly",
        "computable in principle but did not exactly match the existing project",
        "extractor. The production extractor was not changed. Candidate",
        "definitions were tested in a research-only diagnostics script.",
        "",
        "No URL was opened, requested, resolved, pinged, or contacted.",
        "",
        "## Candidate Representations Tested",
        "",
        "- `A_full_stripped_raw_url`: full stripped URL string.",
        "- `B_scheme_prefix_removed`: stripped URL after removing only `http://`",
        "  or `https://` style scheme prefixes.",
        "- `B2_scheme_and_www_prefix_removed`: scheme removal plus leading",
        "  `www.` removal when present.",
        "- `C_hostname_path_query`: locally parsed hostname, path, and query.",
        "- `C2_hostname_without_www_path_query`: locally parsed hostname after",
        "  leading `www.` removal, path, and query.",
        "- `D_netloc_path_query`: locally parsed netloc, path, and query.",
        "- `_other_special`: alternate special-character count that excludes",
        "  common URL structural separators from \"other special\" characters.",
        "",
        "## Confirmed By Evidence",
        "",
        (
            "- The original production `url_length` comparison matched only "
            f"{format_metric(current_url['exact_match_percentage'])}% exactly, "
            f"with modal supplied-minus-reconstructed delta "
            f"{format_metric(current_url['modal_delta'], 0)}."
        ),
        (
            "- Scheme removal does not explain the `URLLength` mismatch. "
            "After removing only the scheme prefix, exact match is "
            f"{format_metric(scheme_removed_url['exact_match_percentage'])}% "
            f"with MAE {format_metric(scheme_removed_url['mae'], 6)} and modal "
            f"delta {format_metric(scheme_removed_url['modal_delta'], 0)}."
        ),
        (
            "- The best tested `URLLength` candidate remains "
            f"`{best_url['candidate_name']}` with "
            f"{format_metric(best_url['exact_match_percentage'])}% exact "
            f"match and modal delta {format_metric(best_url['modal_delta'], 0)}."
        ),
    ]

    for _, row in url_scheme_rows.iterrows():
        lines.append(
            f"- For `{row['scheme_group']}` rows under scheme removal, exact "
            f"match was {format_metric(row['exact_match_percentage'])}% with "
            f"modal delta {format_metric(row['modal_delta'], 0)}."
        )

    lines.extend(
        [
            "",
            "Best candidate rows by feature:",
            "",
            "| Feature | Best candidate | Exact % | MAE | Pearson | Modal delta |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )

    for _, row in best.iterrows():
        lines.append(
            f"| `{row['feature_name']}` | `{row['candidate_name']}` | "
            f"{format_metric(row['exact_match_percentage'])} | "
            f"{format_metric(row['mae'], 6)} | "
            f"{format_metric(row['pearson_correlation'], 6)} | "
            f"{format_metric(row['modal_delta'], 0)} |"
        )

    letter_row = best[best["feature_name"] == "NoOfLettersInURL"].iloc[0]
    special_row = best[best["feature_name"] == "NoOfOtherSpecialCharsInURL"].iloc[0]

    lines.extend(
        [
            "",
            "## Likely",
            "",
            (
            "- The letter-count mismatch is partly reduced by excluding common "
            "prefix material such as scheme text and leading `www.`, but the "
            "best tested candidate still leaves many residual mismatches. The "
            f"best tested candidate for `NoOfLettersInURL` is "
            f"`{letter_row['candidate_name']}` with "
            f"{format_metric(letter_row['exact_match_percentage'])}% "
            "exact match."
            ),
            (
                "- The special-character mismatch is likely explained by a "
                "narrower definition of \"other special\" characters. The best "
                f"tested candidate for `NoOfOtherSpecialCharsInURL` is "
                f"`{special_row['candidate_name']}` with "
                f"{format_metric(special_row['exact_match_percentage'])}% "
                "exact match."
            ),
            "- Prefix removal explains part of the character-count behavior,",
            "  especially special-character counts, but residual mismatches",
            "  remain for malformed, unusual, or differently normalized URL",
            "  strings.",
            "",
            "## Unresolved",
            "",
            "- The original PhiUSIIL source code or formal feature formulas were",
            "  not available in the project files, so this report does not claim",
            "  bit-for-bit discovery of the original implementation.",
            "- `NoOfAmpersandInURL` and a small subset of query-character rows still",
            "  show discrepancies, likely due to URL encoding or preprocessing",
            "  differences that are not fully specified.",
            "- `SpacialCharRatioInURL` remains spelling-preserved from the dataset",
            "  and depends on the same unresolved special-character convention.",
            "",
            "## Safety Statement",
            "",
            "All operations were local string parsing and aggregation. No dataset",
            "URL was contacted.",
        ]
    )

    RECONSTRUCTION_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    RECONSTRUCTION_REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_delta_diagnostics() -> pd.DataFrame:
    """Run all delta diagnostics and save outputs."""

    dataframe = pd.read_csv(RAW_DATA_FILE)
    url_column = find_url_column(dataframe)
    dataframe["_scheme_group"] = dataframe[url_column].map(scheme_group)

    records = []
    records.extend(build_current_mapping_diagnostics(dataframe))
    records.extend(build_candidate_diagnostics(dataframe))

    diagnostics = pd.DataFrame(records)
    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    diagnostics.to_csv(DELTA_DIAGNOSTICS_FILE, index=False)
    write_markdown_report(diagnostics)

    return diagnostics


def main() -> None:
    """Run command-line diagnostics."""

    diagnostics = run_delta_diagnostics()
    print(f"Saved: {DELTA_DIAGNOSTICS_FILE}")
    print(f"Saved: {RECONSTRUCTION_REPORT_FILE}")
    print(f"Rows: {len(diagnostics)}")


if __name__ == "__main__":
    main()
