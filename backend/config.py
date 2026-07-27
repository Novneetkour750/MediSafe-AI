"""
Application configuration.

Single source of truth for paths, environment variables, and tunable
constants. Nothing in this file talks to pandas, FAISS, or Gemini —
it only describes *where things are* and *what the defaults are*.
"""
from pathlib import Path
from functools import lru_cache
import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent  # project root, one level above backend/


class Settings:
    # --- External services -------------------------------------------------
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # --- Data locations ------------------------------------------------------
    dataset_path: Path = BASE_DIR / "dataset" / "medicine_travel_regulations.csv"
    faiss_index_path: Path = BASE_DIR / "models" / "medisafe.index"
    embedding_model_name: str = "all-MiniLM-L6-v2"

    # --- Search tuning ---------------------------------------------------------
    min_match_score: float = 0.45
    default_top_k: int = 20  # generous headroom above the current 10-country dataset

    # --- API ---------------------------------------------------------------
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — import this, don't instantiate Settings() directly."""
    return Settings()
