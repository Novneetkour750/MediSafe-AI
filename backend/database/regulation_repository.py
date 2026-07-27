"""
RegulationRepository — the ONLY place in the codebase that touches the
regulation dataset on disk.

Responsibilities:
    - Load the CSV once and cache it in memory.
    - Expose small, honest read methods (distinct medicines, distinct
      countries, raw dataframe access for the search service).

Explicitly NOT responsible for:
    - Ranking, scoring, or filtering results by relevance (SearchService).
    - Formatting data for the API or the UI (RegulationService).
    - Anything involving embeddings, FAISS, or the LLM.

If the data source ever moves from CSV to Postgres, this is the only
file that should need to change.
"""
from pathlib import Path

import pandas as pd

from config import get_settings
from utils.logger import get_logger

log = get_logger("database.regulation_repository")


class RegulationRepository:
    def __init__(self, csv_path: Path | None = None):
        self._csv_path = csv_path or get_settings().dataset_path
        self._df: pd.DataFrame = self._load()

    def _load(self) -> pd.DataFrame:
        log.info("Loading regulation dataset from %s", self._csv_path)
        df = pd.read_csv(self._csv_path)
        log.info("Loaded %d regulation records", len(df))
        return df

    @property
    def dataframe(self) -> pd.DataFrame:
        """Read-only access to the full dataset, for the search service."""
        return self._df

    def list_countries(self) -> list[str]:
        return sorted(self._df["country"].dropna().unique().tolist())

    def list_medicines(self) -> list[str]:
        return sorted(self._df["medicine_name"].dropna().unique().tolist())

    def summary_stats(self) -> dict:
        status = self._df["status"].str.lower()
        return {
            "total_records": len(self._df),
            "total_medicines": int(self._df["medicine_name"].nunique()),
            "total_countries": int(self._df["country"].nunique()),
            "allowed": int((status == "allowed").sum()),
            "restricted": int((status == "restricted").sum()),
            "banned": int((status == "banned").sum()),
            "authorities": int(self._df["authority"].nunique()),
        }


# Module-level singleton, created once at import time and reused by every
# service — mirrors how the dataframe was shared in the original app,
# but now behind one explicit accessor instead of a scattered `df = get_dataframe()`.
_repository: RegulationRepository | None = None


def get_repository() -> RegulationRepository:
    global _repository
    if _repository is None:
        _repository = RegulationRepository()
    return _repository
