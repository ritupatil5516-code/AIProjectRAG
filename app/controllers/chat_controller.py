import os, json, re
from typing import List, Dict, Any
from app.services.embedder import embed_texts
from app.core.rag.faiss_store import FaissStore
from app.services.llm_service import LLMService
from app.utils.now import now_utc
from app.services.metrics import detect_total_interest_intent, total_interest_all, total_interest_year, total_interest_month
from app.services.interest_calc import build_daily_balances_tz, monthly_interest_from_daily
from app.core.schemas import Agreement

SYSTEM = (
    "You are a banking co‑pilot. Output JSON only with keys: answer, used_fields, notes, optional calc_request. "
    "Agreement‑first for interest/min-payment; use POSTED transactions for balances and interest. "
    "For 'how much interest for YYYY-MM', include calc_request. "
    "Never invent values; if data is missing, say 'No matching data found.' and list missing fields in notes."
)

def _read(path):
    try: return open(path, "r").read()
    except Exception: return ""

GLOSSARY = _read("./context/glossary.md")
RULES = _read("./context/rules.md")
FORMULAS = _read("./context/formulas.md")

class ChatController:
    def __init__(self, corpus: Dict[str, Any], agreement: Agreement|None):
        self.corpus = corpus
        self.agreement = agreement
        self.history: List[tuple] = []
        self._build_index()

    def add_user(self, msg: str): self.history.append(("user", msg, None))
    def add_assistant(self, msg: str, evidence=None): self.history.append(("assistant", msg, evidence))

    def _build_index(self):
        docs, payloads = [], []
        for i, r in enumerate(self.corpus.get("account_summary", [])):
            docs.append("TYPE:ACCOUNT_SUMMARY RAW:"+json.dumps(r, separators=(",",":"))); payloads.append({"rtype":"account_summary","rid":str(i),"text":docs[-1]})
        for i, r in enumerate(self.corpus.get("statements", [])):
            docs.append("TYPE:STATEMENTS RAW:"+json.dumps(r, separators=(",",":"))); payloads.append({"rtype":"statements","rid":str(i),"text":docs[-1]})
        for i, r in enumerate(self.corpus.get("payments", [])):
            docs.append("TYPE:PAYMENTS RAW:"+json.dumps(r, separators=(",",":"))); payloads.append({"rtype":"payments","rid":str(i),"text":docs[-1]})
        for i, r in enumerate(self.corpus.get("transactions", [])):
            docs.append("TYPE:TRANSACTIONS RAW:"+json.dumps(r, separators=(",",":"))); payloads.append({"rtype":"transactions","rid":str(i),"text":docs[-1]})
        embs = embed_texts(docs)
        self.store = FaissStore(embs.shape[1])
        self.store.add(embs, payloads)

    def _retrieve(self, q: str, k: int=6) -> List[str]:
        qemb = embed_texts([q])
        hits = self.store.search(qemb, k=k)
        return [h[1]["text"][:950] for h in hits]

    def _shortcuts(self, q: str):
        kind = detect_total_interest_intent(q)
        if not kind: return None
        tx = self.corpus.get("transactions", [])
        if kind == "all":
            total, ev = total_interest_all(tx); label = "Total interest"
        elif kind == "year":
            total, ev = total_interest_year(tx, now_utc()); label = "Total interest this year"
        else:
            total, ev = total_interest_month(tx, now_utc()); label = "Total interest this month"
        ans = f"{label} is ${total:.2f}."
        ev_lines = [f"{tid or '(no-id)'} · {dt} · ${amt:.2f}" for (tid, amt, dt) in ev]
        return {"answer": ans, "used_fields":["transactions[POSTED.INTEREST].*"], "notes":"Sum of POSTED INTEREST in window.", "evidence_lines": ev_lines}

    def answer(self, q: str) -> Dict[str, Any]:
        # 1) Deterministic shortcut
        sc = self._shortcuts(q)
        if sc: return sc

        # 2) Build prompt with snippets
        snippets = self._retrieve(q, k=6)
        prelude = f"# Glossary\n{GLOSSARY}\n\n# Rules\n{RULES}\n\n# Formulas\n{FORMULAS}\n\n# Snippets\n" +                   "\n".join(f"- {s}" for s in snippets) + f"\n\nQuestion: {q}"

        # 3) LLM
        result = LLMService().ask(SYSTEM, prelude)

        # 4) Guardrail: force calc_request for interest YYYY-MM
        if ("interest" in q.lower()) and not result.get("calc_request"):
            m = re.search(r"(20\d{2})[-/ ]?(\d{1,2})", q)
            if m:
                ym = f"{m.group(1)}-{int(m.group(2)):02d}"
                result["calc_request"] = {"type":"interest_month","period": ym}

        # 5) Execute calc if asked
        if result.get("calc_request", {}).get("type") == "interest_month":
            ym = result["calc_request"]["period"]
            from zoneinfo import ZoneInfo
            y, m = int(ym[:4]), int(ym[5:7])
            tz = self.agreement.tz if self.agreement else "America/New_York"
            basis = self.agreement.apr_basis if self.agreement else 365
            rounding = self.agreement.rounding if self.agreement else "sum_then_round"
            apr = (self.agreement.purchaseApr if (self.agreement and self.agreement.purchaseApr is not None) 
                   else (self.corpus.get("account_summary",[{}])[0].get("purchaseApr", 20.0)))
            start = datetime(y, m, 1, tzinfo=ZoneInfo(tz))
            end = datetime(y+1,1,1,tzinfo=ZoneInfo(tz)) if m==12 else datetime(y,m+1,1,tzinfo=ZoneInfo(tz))
            daily = build_daily_balances_tz(self.corpus.get("transactions", []), start, end, tz=tz)
            if daily:
                val = monthly_interest_from_daily(daily, apr, basis, rounding=rounding)
                result["answer"] = f"Interest for {ym} (calculated) is ${val:.2f}."
                result.setdefault("used_fields", []).extend(["transactions[month].*","agreement.*"])
                result["notes"] = f"TZ={tz}, basis={basis}, rounding={rounding}, APR={apr}%."
            else:
                result["answer"] = "No matching data found."
                result["notes"] = "No posted transactions to build daily balances."

        result["evidence_lines"] = [s[:140]+("…" if len(s)>140 else "") for s in snippets]
        return result
