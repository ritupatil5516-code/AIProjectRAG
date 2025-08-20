import json
from typing import List, Dict, Any
from app.core.schemas import DataBundle
from app.core.embeddings import EmbeddingsProvider
from app.core.rag.faiss_store import FaissRAG


def _serialize_record(rec: Dict[str, Any], rtype: str) -> str:
    return f"TYPE:{rtype.upper()} RAW:" + json.dumps(rec, separators=(",", ":"))


def _flatten_docs(data: DataBundle) -> List[Dict[str, Any]]:
    docs = []
    for r in data.account_summary:
        docs.append({"rid": r.accountId, "rtype": "account_summary",
                     "text": _serialize_record(r.model_dump(), "account_summary")})
    for t in data.transactions:
        docs.append({"rid": t.transactionId, "rtype": "transactions",
                     "text": _serialize_record(t.model_dump(), "transactions")})
    for s in data.statements:
        docs.append(
            {"rid": s.statementId, "rtype": "statements", "text": _serialize_record(s.model_dump(), "statements")})
    for p in data.payments:
        docs.append({"rid": p.paymentId, "rtype": "payments", "text": _serialize_record(p.model_dump(), "payments")})
    return docs


SYSTEM = """
You are a credit-card banking copilot. Use STRICT context engineering.
- Use the Glossary, Rules, and Interest Formulas verbatim.
- Apply Rules to associate statements, transactions, and payments.
- For interest totals, sum POSTED INTEREST transactions in the requested window.
- If insufficient context, say: "No matching data found."
Return JSON only:
{ "answer": "one or two concise sentences", "used_fields": ["json.path.hints"], "notes": "optional" }
"""


class ChatController:
    def __init__(self, data: DataBundle, glossary: str, rules: str, formulas: str):
        self.data = data
        self.emb = EmbeddingsProvider()
        docs = _flatten_docs(data)
        embs = self.emb.encode([d["text"] for d in docs])
        self.rag = FaissRAG(dim=embs.shape[1])
        self.rag.build(embs, docs)
        self.glossary, self.rules, self.formulas = glossary, rules, formulas

    def retrieve(self, question: str, k: int = 8) -> List[str]:
        q_emb = self.emb.encode([question])
        hits = self.rag.search(q_emb, k=k)
        return [h[1]["text"][:900] for h in hits]

    def prelude(self, question: str, snippets: List[str]) -> str:
        return (
                "# Glossary\n" + self.glossary + "\n\n" +
                "# Association Rules\n" + self.rules + "\n\n" +
                "# Interest Formulas\n" + self.formulas + "\n\n" +
                "## Context snippets (may be partial JSON)\n" +
                "\n".join(f"- {s}" for s in snippets) +
                "\n\nQuestion: " + question
        )
