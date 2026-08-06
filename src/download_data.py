"""Download the PhiUSIIL dataset from the UCI repository."""

from pathlib import Path

import pandas as pd
from ucimlrepo import fetch_ucirepo


DATASET_ID = 967
OUTPUT_DIRECTORY = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIRECTORY / "phiusil_raw.csv"


def download_dataset() -> pd.DataFrame:
    """Download, combine, and return the PhiUSIIL dataset."""

    print(f"Downloading UCI dataset ID {DATASET_ID}...")

    dataset = fetch_ucirepo(id=DATASET_ID)

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

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(OUTPUT_FILE, index=False)

    print(f"Dataset saved to: {OUTPUT_FILE}")
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
