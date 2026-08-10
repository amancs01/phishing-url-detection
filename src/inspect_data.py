"""Inspect the raw PhiUSIIL dataset schema."""

import json
from collections import Counter

import pandas as pd

from src.config import DATASET_SCHEMA_FILE, RAW_DATA_FILE, create_project_directories


TARGET_CANDIDATES = ["label", "Label", "CLASS_LABEL", "class", "target", "Target"]


def find_target_column(dataframe: pd.DataFrame) -> str:
    """Return the dataset target column found from known target names."""

    for candidate in TARGET_CANDIDATES:
        if candidate in dataframe.columns:
            return candidate

    raise ValueError(
        "No target column was found. Checked: " + ", ".join(TARGET_CANDIDATES)
    )


def find_duplicate_columns(columns: pd.Index) -> list[str]:
    """Return repeated column names in their first-seen order."""

    counts = Counter(columns)
    return [column for column, count in counts.items() if count > 1]


def build_schema_summary(dataframe: pd.DataFrame) -> dict:
    """Build a JSON-friendly summary of the dataset schema."""

    target_column = find_target_column(dataframe)
    target_counts = dataframe[target_column].value_counts(dropna=False).sort_index()

    return {
        "source_file": str(RAW_DATA_FILE),
        "rows": int(dataframe.shape[0]),
        "columns": int(dataframe.shape[1]),
        "column_names": list(dataframe.columns),
        "data_types": {
            column: str(dtype) for column, dtype in dataframe.dtypes.items()
        },
        "duplicate_column_names": find_duplicate_columns(dataframe.columns),
        "target_column": target_column,
        "target_value_counts": {
            str(label): int(count) for label, count in target_counts.items()
        },
    }


def save_schema_summary(summary: dict) -> None:
    """Save the schema summary as formatted JSON."""

    create_project_directories()
    DATASET_SCHEMA_FILE.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    """Run the dataset schema inspection workflow."""

    dataframe = pd.read_csv(RAW_DATA_FILE)
    summary = build_schema_summary(dataframe)
    save_schema_summary(summary)

    print(f"Rows: {summary['rows']:,}")
    print(f"Columns: {summary['columns']}")
    print("Column names:")
    for column in summary["column_names"]:
        print(f"- {column}")
    print("Data types:")
    for column, dtype in summary["data_types"].items():
        print(f"- {column}: {dtype}")
    print(f"Duplicate column names: {summary['duplicate_column_names']}")
    print(f"Target column: {summary['target_column']}")
    print(f"Target counts: {summary['target_value_counts']}")
    print(f"Schema summary saved to: {DATASET_SCHEMA_FILE}")


if __name__ == "__main__":
    main()
