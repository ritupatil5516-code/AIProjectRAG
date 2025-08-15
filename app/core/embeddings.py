
from typing import List, Optional
import os, numpy as np

class EmbeddingsProvider:
    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("OPENAI_EMBED_MODEL","text-embedding-3-small")
        self.use_openai = bool(os.getenv("OPENAI_API_KEY"))
        self.client = None
        if self.use_openai:
            try:
                from openai import OpenAI  # type: ignore
                self.client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL"))
            except Exception:
                self.use_openai = False
                self.client = None
        if not self.use_openai:
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore
                self.st_model = SentenceTransformer(os.getenv("LOCAL_EMBED_MODEL","all-MiniLM-L6-v2"))
            except Exception as e:
                raise RuntimeError("No embeddings backend available. Set OPENAI_API_KEY or install sentence-transformers.") from e

    def encode(self, texts: List[str]) -> np.ndarray:
        if self.use_openai and self.client:
            res = self.client.embeddings.create(model=self.model, input=texts)
            vecs = [np.array(d.embedding, dtype=np.float32) for d in res.data]
            return np.vstack(vecs)
        vecs = self.st_model.encode(texts, convert_to_numpy=True, normalize_embeddings=False)
        return vecs.astype("float32")
