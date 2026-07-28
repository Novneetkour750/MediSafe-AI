import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent)) 

import faiss
import numpy as np
from fastembed import TextEmbedding

from config import get_settings
from database.regulation_repository import get_repository


def main() -> None:
    settings = get_settings()
    df = get_repository().dataframe
    documents = df["document"].tolist()

    print(f"Embedding {len(documents)} documents with {settings.embedding_model_name}...")
    model = TextEmbedding(model_name=settings.embedding_model_name)
    embeddings = np.array(list(model.embed(documents))).astype("float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    settings.faiss_index_path.parent.mkdir(exist_ok=True, parents=True)
    faiss.write_index(index, str(settings.faiss_index_path))

    print(f"Indexed {index.ntotal} documents -> {settings.faiss_index_path}")


if __name__ == "__main__":
    main()

