import os, numpy as np
from typing import List
from sentence_transformers import SentenceTransformer

_model = None

def embed_texts(texts: List[str]) -> np.ndarray:
    global _model
    if _model is None:
        name = os.getenv("LOCAL_EMBED_MODEL", "all-MiniLM-L6-v2")
        _model = SentenceTransformer(name)
    embs = _model.encode(texts, normalize_embeddings=False, convert_to_numpy=True, show_progress_bar=False)
    return embs.astype("float32")
