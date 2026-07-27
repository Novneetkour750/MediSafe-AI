"""
One-off script: builds the FAISS semantic index from the regulation
CSV's `document` column. Run this whenever the dataset changes.

    cd backend && python scripts/build_index.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))  # allow `import config` etc.

import faiss
from sentence_transformers import SentenceTransformer

from config import get_settings
from database.regulation_repository import get_repository


def main() -> None:
    settings = get_settings()
    df = get_repository().dataframe
    documents = df["document"].tolist()

    print(f"Embedding {len(documents)} documents with {settings.embedding_model_name}...")
    model = SentenceTransformer(settings.embedding_model_name)
    embeddings = model.encode(
        documents, convert_to_numpy=True, normalize_embeddings=True
    ).astype("float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    settings.faiss_index_path.parent.mkdir(exist_ok=True, parents=True)
    faiss.write_index(index, str(settings.faiss_index_path))

    print(f"Indexed {index.ntotal} documents -> {settings.faiss_index_path}")


if __name__ == "__main__":
    main()
