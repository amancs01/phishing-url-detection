"""Validate basic quality of the raw PhiUSIIL dataset."""

import json

import pandas as pd

from src.config import DATA_VALIDATION_FILE, RAW_DATA_FILE, create_project_directories
from src.inspect_data import find_target_column


EXPECTED_TARGET_VALUES = {0, 1}
URL_COLUMN_CANDIDATES = ["URL", "url", "Url"]


def find_url_column(dataframe: pd.DataFrame) -> str | None:
    """Return the URL column name if it exists."""

    for candidate in URL_COLUMN_CANDIDATES:
        if candidate in dataframe.columns:
            return candidate

    return None


def count_duplicate_url_values(dataframe: pd.DataFrame, url_column: str | None) -> dict:
    """Count duplicate URL values when a URL column is available."""

    if url_column is None:
        return {
            "url_column": None,
            "duplicate_url_values": None,
            "rows_with_duplicate_url": None,
        }

    duplicated_mask = dataframe[url_column].duplicated(keep=False)
    duplicate_value_count = int(
        dataframe.loc[duplicated_mask, url_column].nunique(dropna=False)
    )

    return {
        "url_column": url_column,
        "duplicate_url_values": duplicate_value_count,
        "rows_with_duplicate_url": int(duplicated_mask.sum()),
    }


def build_validation_report(dataframe: pd.DataFrame) -> dict:
    """Build a JSON-friendly dataset quality validation report."""

    target_column = find_target_column(dataframe)
    target_series = dataframe[target_column]
    target_counts = target_series.value_counts(dropna=False).sort_index()
    observed_targets = set(target_series.dropna().unique().tolist())
    unexpected_targets = sorted(observed_targets - EXPECTED_TARGET_VALUES)
    url_column = find_url_column(dataframe)

    missing_values = dataframe.isna().sum().sort_values(ascending=False)
    constant_columns = [
        column
        for column in dataframe.columns
        if dataframe[column].nunique(dropna=False) <= 1
    ]

    report = {
        "source_file": str(RAW_DATA_FILE),
        "shape": {
            "rows": int(dataframe.shape[0]),
            "columns": int(dataframe.shape[1]),
        },
        "missing_values_by_column": {
            column: int(count) for column, count in missing_values.items()
        },
        "total_missing_values": int(missing_values.sum()),
        "duplicate_rows": int(dataframe.duplicated().sum()),
        "duplicate_url_summary": count_duplicate_url_values(dataframe, url_column),
        "target_column": target_column,
        "target_class_distribution": {
            str(label): int(count) for label, count in target_counts.items()
        },
        "expected_target_values": sorted(EXPECTED_TARGET_VALUES),
        "unexpected_target_values": [str(value) for value in unexpected_targets],
        "target_missing_values": int(target_series.isna().sum()),
        "target_unique_value_count": int(target_series.nunique(dropna=True)),
        "target_is_valid": bool(
            target_series.notna().all()
            and len(observed_targets) == len(EXPECTED_TARGET_VALUES)
            and observed_targets == EXPECTED_TARGET_VALUES
        ),
        "constant_columns": constant_columns,
    }

    return report


def save_validation_report(report: dict) -> None:
    """Save the validation report as formatted JSON."""

    create_project_directories()
    DATA_VALIDATION_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    """Run the dataset validation workflow."""

    dataframe = pd.read_csv(RAW_DATA_FILE)
    report = build_validation_report(dataframe)
    save_validation_report(report)

    print(f"Rows: {report['shape']['rows']:,}")
    print(f"Columns: {report['shape']['columns']}")
    print(f"Total missing values: {report['total_missing_values']:,}")
    print(f"Duplicate rows: {report['duplicate_rows']:,}")
    print(f"Duplicate URL summary: {report['duplicate_url_summary']}")
    print(f"Target column: {report['target_column']}")
    print(f"Target distribution: {report['target_class_distribution']}")
    print(f"Unexpected target values: {report['unexpected_target_values']}")
    print(f"Target is valid: {report['target_is_valid']}")
    print(f"Constant columns: {report['constant_columns']}")
    print(f"Validation report saved to: {DATA_VALIDATION_FILE}")


if __name__ == "__main__":
    main()
