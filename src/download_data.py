"""Download the PhiUSIIL dataset from the UCI repository."""

import pandas as pd
from ucimlrepo import fetch_ucirepo

from src.config import RAW_DATA_FILE, UCI_DATASET_ID, create_project_directories

def download_dataset() -> pd.DataFrame:
    """Download, combine, and return the PhiUSIIL dataset."""

    print(f"Downloading UCI dataset ID {UCI_DATASET_ID}...")

    dataset = fetch_ucirepo(id=UCI_DATASET_ID)

    features = dataset.data.features.copy()
    targets = dataset.data.targets.copy()

    if features is None or targets is None:
        raise ValueError("The UCI repository returned incomplete dataset data.")

    dataframe = pd.concat(
        [
            features.reset_index(drop=True),
            targets.reset_index(drop=True),
        ],
        axis=1,
    )

    return dataframe


def save_dataset(dataframe: pd.DataFrame) -> None:
    """Save the downloaded dataset as a local CSV file."""

    create_project_directories()
    dataframe.to_csv(RAW_DATA_FILE, index=False)

    print(f"Dataset saved to: {RAW_DATA_FILE}")
    print(f"Rows: {dataframe.shape[0]:,}")
    print(f"Columns: {dataframe.shape[1]}")


def main() -> None:
    """Run the dataset download workflow."""

    try:
        dataframe = download_dataset()
        save_dataset(dataframe)
    except Exception as error:
        print(f"Dataset download failed: {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
