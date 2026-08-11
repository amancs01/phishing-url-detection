"""Build the URL-only modeling dataset from raw URL text."""

import pandas as pd

from src.config import PROCESSED_DATA_FILE, RAW_DATA_FILE, create_project_directories
from src.feature_definitions import FEATURE_NAMES
from src.feature_extractor import extract_url_features
from src.inspect_data import find_target_column


URL_COLUMN_CANDIDATES = ["URL", "url", "Url"]
EXPECTED_TARGET_VALUES = {0, 1}


def find_url_column(dataframe: pd.DataFrame) -> str:
    """Return the raw URL column name found in the dataset."""

    for candidate in URL_COLUMN_CANDIDATES:
        if candidate in dataframe.columns:
            return candidate

    raise ValueError(
        "No URL column was found. Checked: " + ", ".join(URL_COLUMN_CANDIDATES)
    )


def build_feature_dataframe(urls: pd.Series) -> pd.DataFrame:
    """Extract URL-only features for every raw URL string."""

    feature_rows = [extract_url_features(url) for url in urls]
    return pd.DataFrame(feature_rows, columns=FEATURE_NAMES)


def validate_processed_data(dataframe: pd.DataFrame, target_column: str) -> None:
    """Validate the processed modeling dataset before saving."""

    feature_dataframe = dataframe[FEATURE_NAMES]

    if dataframe.empty:
        raise ValueError("Processed dataset is empty.")

    if feature_dataframe.isna().sum().sum() != 0:
        raise ValueError("Processed feature columns contain missing values.")

    non_numeric_columns = [
        column
        for column in FEATURE_NAMES
        if not pd.api.types.is_numeric_dtype(feature_dataframe[column])
    ]

    if non_numeric_columns:
        raise ValueError(
            "Processed feature columns must be numerical. Non-numeric columns: "
            + ", ".join(non_numeric_columns)
        )

    observed_targets = set(dataframe[target_column].dropna().unique().tolist())

    if observed_targets != EXPECTED_TARGET_VALUES:
        raise ValueError(f"Unexpected target values found: {sorted(observed_targets)}")


def prepare_modeling_dataset() -> pd.DataFrame:
    """Create and save the URL-only modeling dataset."""

    raw_dataframe = pd.read_csv(RAW_DATA_FILE)
    url_column = find_url_column(raw_dataframe)
    target_column = find_target_column(raw_dataframe)

    print("Verifying extractor on a small sample...")
    sample_features = build_feature_dataframe(raw_dataframe[url_column].head(3))
    print(sample_features.head().to_string(index=False))

    print("Extracting URL-only features from the full dataset...")
    feature_dataframe = build_feature_dataframe(raw_dataframe[url_column])
    processed_dataframe = feature_dataframe.copy()
    processed_dataframe[target_column] = raw_dataframe[target_column].astype(int)

    validate_processed_data(processed_dataframe, target_column)

    create_project_directories()
    processed_dataframe.to_csv(PROCESSED_DATA_FILE, index=False)

    target_distribution = (
        processed_dataframe[target_column].value_counts().sort_index().to_dict()
    )

    print(f"Raw rows: {raw_dataframe.shape[0]:,}")
    print(f"Processed rows: {processed_dataframe.shape[0]:,}")
    print(f"Number of model features: {len(FEATURE_NAMES)}")
    print(f"Target distribution: {target_distribution}")
    print(f"Output location: {PROCESSED_DATA_FILE}")

    return processed_dataframe


def main() -> None:
    """Run the processed dataset preparation workflow."""

    prepare_modeling_dataset()


if __name__ == "__main__":
    main()
