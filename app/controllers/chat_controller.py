
import json
from typing import List, Dict, Any
from app.core.schemas import DataBundle
from app.core.embeddings import EmbeddingsProvider
from app.core.rag.faiss_store import FaissRAG

def _serialize_record(rec: Dict[str, Any], rtype: str) -> str:
    return f"TYPE:{rtype.upper()} RAW:" + json.dumps(rec, separators=(",",":"))

def _flatten_docs(data: DataBundle) -> List[Dict[str, Any]]:
    docs = []
    for r in data.account_summary:
        docs.append({"rid": r.accountId, "rtype":"account_summary", "text": _serialize_record(r.model_dump(), "account_summary")})
    for t in data.transactions:
        docs.append({"rid": t.transactionId, "rtype":"transactions", "text": _serialize_record(t.model_dump(), "transactions")})
    for s in data.statements:
        docs.append({"rid": s.statementId, "rtype":"statements", "text": _serialize_record(s.model_dump(), "statements")})
    for p in data.payments:
        docs.append({"rid": p.paymentId, "rtype":"payments", "text": _serialize_record(p.model_dump(), "payments")})
    return docs

SYSTEM = """You are a credit-card banking copilot. Use STRICT context engineering and JSON output only.

Agreement precedence and compute handoff:
- If an agreement.json (from agreement.pdf) is available, ALWAYS prefer it for interest/minimum-payment/fee questions.
- When a deterministic calculation is needed, include a JSON field "calc_request" with a minimal object, e.g.:
  { "calc_request": { "type": "interest_month", "period": "YYYY-MM" } }
- If agreement values needed for the calc are missing, do NOT guess; omit calc_request and answer from rules/formulas or say "No matching data found." with notes.

General policy:
- Use POSTED transactions for balances/totals. Current balance = latest POSTED endingBalance; fallback account_summary.currentBalance.
- Upcoming payment = earliest future payments[state='SCHEDULED'] by effectiveDateTime (fallback paymentDateTime).
- Sum of interest for a month = sum of POSTED INTEREST transactions in that month when asked for posted interest, or request an interest_month calc for ADB math when asked "how much interest for <month>".

Return JSON only:
{ "answer": "concise sentence(s)", "used_fields": ["path.hints"], "notes": "optional", "calc_request": { "type": "..." } }"""

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
        return [h[1]["text"][:950] for h in hits]

    def prelude(self, question: str, snippets: List[str]) -> str:
        return (
            "# Glossary\n" + self.glossary + "\n\n" +
            "# Association Rules\n" + self.rules + "\n\n" +
            "# Interest Formulas\n" + self.formulas + "\n\n" +
            "## Context snippets (may be partial JSON)\n" +
            "\n".join(f"- {s}" for s in snippets) +
            "\n\nQuestion: " + question
        )
