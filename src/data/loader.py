from pathlib import Path

import pandas as pd


class DataLoader:
    """Responsible for loading datasets."""

    @staticmethod
    def load_csv(file_path: str) -> pd.DataFrame:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {file_path}")

        return pd.read_csv(path)
