from pathlib import Path

import faiss
import numpy as np
from fastembed import TextEmbedding

from config import get_settings
from database.regulation_repository import get_repository
from utils.logger import get_logger

log = get_logger("services.search")


class SearchService:
    def __init__(self, index_path: Path | None = None, model_name: str | None = None):
        settings = get_settings()
        self._repo = get_repository()
        self._model = TextEmbedding(model_name=model_name or settings.embedding_model_name)
        self._index = faiss.read_index(str(index_path or settings.faiss_index_path))
        log.info("FAISS index loaded (%d vectors)", self._index.ntotal)

    def search(self, query: str, destination_country: str | None = None, k: int = 5) -> list[dict]:
        search_text = f"{query} in {destination_country}" if destination_country else query


        embedding = np.array(list(self._model.embed([search_text]))).astype("float32")

        scores, indices = self._index.search(embedding, k)

        df = self._repo.dataframe
        results = [
            {"score": float(score), "data": df.iloc[idx].to_dict()}
            for score, idx in zip(scores[0], indices[0])
            if idx != -1
        ]

        if destination_country:
            destination_lower = destination_country.strip().lower()
            results.sort(
                key=lambda r: (
                    r["data"].get("country", "").strip().lower() != destination_lower,
                    -r["score"],
                )
            )

        return results


_search_service: SearchService | None = None


def get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service

