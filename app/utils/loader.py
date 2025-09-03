import json, os
from typing import Dict, Any, List, Type, TypeVar
from app.core.schemas import AccountSummary, Statement, Payment, Transaction

T = TypeVar("T")

def _load_list(path: str) -> list:
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def _validate(items: list, model: Type[T]) -> list:
    out = []
    for i, it in enumerate(items):
        try:
            m = model(**it)  # validate
            out.append(m.model_dump())  # return plain dicts for downstream code
        except Exception as e:
            # Skip invalid rows; you could log e here if needed
            continue
    return out

def load_corpus(data_dir: str) -> Dict[str, Any]:
    acc = _validate(_load_list(os.path.join(data_dir, "account_summary.json")), AccountSummary)
    stm = _validate(_load_list(os.path.join(data_dir, "statements.json")), Statement)
    pay = _validate(_load_list(os.path.join(data_dir, "payments.json")), Payment)
    txs = _validate(_load_list(os.path.join(data_dir, "transactions.json")), Transaction)
    return {
        "account_summary": acc,
        "transactions": txs,
        "payments": pay,
        "statements": stm,
    }
