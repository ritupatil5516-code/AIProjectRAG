import numpy as np, faiss
from typing import List, Dict, Any, Tuple

def _l2_normalize(x: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / n

class FaissStore:
    def __init__(self, dim: int):
        self.index = faiss.IndexFlatIP(dim)
        self.dim = dim
        self.payloads: List[Dict[str, Any]] = []

    def add(self, vecs: np.ndarray, payloads: List[Dict[str, Any]]):
        vecs = _l2_normalize(vecs.astype("float32"))
        self.index.add(vecs)
        self.payloads.extend(payloads)

    def search(self, qvec: np.ndarray, k: int=8) -> List[Tuple[float, Dict[str, Any]]]:
        q = _l2_normalize(qvec.astype("float32"))
        D, I = self.index.search(q, k)
        out = []
        idxs = I[0] if I.ndim>1 else I
        ds = D[0] if D.ndim>1 else D
        for rank, idx in enumerate(idxs):
            if idx == -1: continue
            out.append((float(ds[rank]), self.payloads[idx]))
        # stable secondary sort (rtype, rid) to break ties
        return sorted(out, key=lambda x: (-x[0], x[1].get("rtype",""), x[1].get("rid","")))
