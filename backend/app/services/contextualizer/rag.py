from __future__ import annotations
from typing import List, Tuple, Optional
import numpy as np

try:
    import faiss  # pip install faiss-cpu
except Exception:  # pragma: no cover
    faiss = None

from app.services.genai_client import get_client

EMBED_MODEL = "gemini-embedding-001"  # can be overridden via env if desired

def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Returns an array of shape (n, d). Uses Gemini embeddings.
    """
    client = get_client()
    # The Google GenAI SDK provides models.embed_content per docs
    res = client.models.embed_content(model=EMBED_MODEL, contents=texts)
    # SDK returns a list of embeddings under res.embeddings
    vecs = [np.array(e.values, dtype="float32") if hasattr(e, "values") else np.array(e, dtype="float32")
            for e in getattr(res, "embeddings", [])]
    return np.vstack(vecs) if vecs else np.zeros((0, 768), dtype="float32")

class SimpleFaissIndex:
    def __init__(self, dim: int, items: List[str], vecs: np.ndarray):
        self.items = items
        self.vecs = vecs.astype("float32")
        if faiss is None:
            self.index = None
        else:
            self.index = faiss.IndexFlatL2(dim)
            self.index.add(self.vecs)

    @classmethod
    def from_texts(cls, texts: List[str]) -> "SimpleFaissIndex":
        vecs = embed_texts(texts)
        dim = vecs.shape[14] if vecs.size else 768
        return cls(dim, texts, vecs)

    def search(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        if self.index is None:
            return []
        q = embed_texts([query])
        if q.size == 0:
            return []
        D, I = self.index.search(q.astype("float32"), k)
        hits = []
        for idx, dist in zip(I, D):
            if 0 <= idx < len(self.items):
                hits.append((self.items[idx], float(dist)))
        return hits
