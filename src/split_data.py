"""Create stratified train, validation, and test splits."""

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import PROCESSED_DATA_FILE, PROCESSED_DATA_DIRECTORY, RANDOM_STATE
from src.feature_definitions import FEATURE_NAMES
from src.inspect_data import find_target_column


TRAIN_FILE = PROCESSED_DATA_DIRECTORY / "train.csv"
VALIDATION_FILE = PROCESSED_DATA_DIRECTORY / "validation.csv"
TEST_FILE = PROCESSED_DATA_DIRECTORY / "test.csv"


def target_distribution(dataframe: pd.DataFrame, target_column: str) -> dict:
    """Return target counts sorted by class label."""

    return dataframe[target_column].value_counts().sort_index().to_dict()


def split_processed_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split the processed URL-only dataset into train, validation, and test."""

    dataframe = pd.read_csv(PROCESSED_DATA_FILE)
    target_column = find_target_column(dataframe)

    missing_features = [
        feature_name for feature_name in FEATURE_NAMES if feature_name not in dataframe.columns
    ]

    if missing_features:
        raise ValueError("Missing feature columns: " + ", ".join(missing_features))

    if target_column not in dataframe.columns:
        raise ValueError(f"Target column {target_column} was not found.")

    train_data, temporary_data = train_test_split(
        dataframe,
        test_size=0.30,
        random_state=RANDOM_STATE,
        stratify=dataframe[target_column],
    )

    validation_data, test_data = train_test_split(
        temporary_data,
        test_size=0.50,
        random_state=RANDOM_STATE,
        stratify=temporary_data[target_column],
    )

    validate_splits(train_data, validation_data, test_data, target_column)

    train_data.to_csv(TRAIN_FILE, index=True)
    validation_data.to_csv(VALIDATION_FILE, index=True)
    test_data.to_csv(TEST_FILE, index=True)

    return train_data, validation_data, test_data


def validate_splits(
    train_data: pd.DataFrame,
    validation_data: pd.DataFrame,
    test_data: pd.DataFrame,
    target_column: str,
) -> None:
    """Validate split integrity before saving files."""

    split_indices = [
        set(train_data.index),
        set(validation_data.index),
        set(test_data.index),
    ]

    if split_indices[0] & split_indices[1]:
        raise ValueError("Training and validation splits overlap.")
    if split_indices[0] & split_indices[2]:
        raise ValueError("Training and test splits overlap.")
    if split_indices[1] & split_indices[2]:
        raise ValueError("Validation and test splits overlap.")

    for split_name, split_data in [
        ("training", train_data),
        ("validation", validation_data),
        ("test", test_data),
    ]:
        if target_column not in split_data.columns:
            raise ValueError(f"The {split_name} split is missing the target column.")

        missing_features = [
            feature_name
            for feature_name in FEATURE_NAMES
            if feature_name not in split_data.columns
        ]

        if missing_features:
            raise ValueError(
                f"The {split_name} split is missing features: "
                + ", ".join(missing_features)
            )

        if split_data[target_column].nunique() != 2:
            raise ValueError(f"The {split_name} split does not contain both classes.")


def print_split_summary(
    full_data: pd.DataFrame,
    train_data: pd.DataFrame,
    validation_data: pd.DataFrame,
    test_data: pd.DataFrame,
    target_column: str,
) -> None:
    """Print row counts, percentages, and class distributions."""

    total_rows = len(full_data)

    print(f"Total rows: {total_rows:,}")

    for split_name, split_data in [
        ("Train", train_data),
        ("Validation", validation_data),
        ("Test", test_data),
    ]:
        percentage = len(split_data) / total_rows * 100
        print(f"{split_name} rows: {len(split_data):,} ({percentage:.2f}%)")
        print(
            f"{split_name} target distribution: "
            f"{target_distribution(split_data, target_column)}"
        )


def main() -> None:
    """Run the train, validation, and test split workflow."""

    full_data = pd.read_csv(PROCESSED_DATA_FILE)
    target_column = find_target_column(full_data)
    train_data, validation_data, test_data = split_processed_data()

    print_split_summary(
        full_data,
        train_data,
        validation_data,
        test_data,
        target_column,
    )
    print(f"Training split saved to: {TRAIN_FILE}")
    print(f"Validation split saved to: {VALIDATION_FILE}")
    print(f"Test split saved to: {TEST_FILE}")


if __name__ == "__main__":
    main()
