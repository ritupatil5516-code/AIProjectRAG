
from typing import List, Tuple, Dict, Any
import faiss, numpy as np

def _l2_normalize(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / norms

class FaissRAG:
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)  # cosine via normalized vectors
        self.payloads: List[Dict[str, Any]] = []
        self.vectors = None

    def build(self, embeddings: np.ndarray, payloads: List[Dict[str, Any]]):
        embs = _l2_normalize(embeddings.astype("float32"))
        self.index.reset()
        self.index.add(embs)
        self.payloads = payloads
        self.vectors = embs

    def search(self, query_emb: np.ndarray, k: int = 8) -> List[Tuple[float, Dict[str, Any]]]:
        q = _l2_normalize(query_emb.astype("float32"))
        D, I = self.index.search(q, k)
        out = []
        for i, idx in enumerate(I[0] if I.ndim>1 else I):
            if idx == -1: continue
            score = float(D[0][i] if D.ndim>1 else D[i])
            out.append((score, self.payloads[idx]))
        return out
