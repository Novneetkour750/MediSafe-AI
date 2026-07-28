from pathlib import Path
from functools import lru_cache
import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent  


class Settings:
    # External services 
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Data locations
    dataset_path: Path = BASE_DIR / "dataset" / "medicine_travel_regulations.csv"
    faiss_index_path: Path = BASE_DIR / "models" / "medisafe.index"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Search tuning
    min_match_score: float = 0.45
    default_top_k: int = 20  

    # API
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — import this, don't instantiate Settings() directly."""
    return Settings()

