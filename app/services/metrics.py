from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone
import re

def _parse_iso(dt: str) -> datetime:
    if dt.endswith("Z"):
        return datetime.fromisoformat(dt.replace("Z","+00:00"))
    return datetime.fromisoformat(dt)

def _sum_interest(transactions: List[Dict], start=None, end=None):
    total = 0.0; ev = []
    for t in transactions:
        if (t.get("transactionStatus","").upper()!="POSTED" or 
            t.get("transactionType","").upper()!="INTEREST"):
            continue
        ts = _parse_iso(t["transactionDateTime"]).astimezone(timezone.utc)
        if start is None or (start <= ts < end):
            amt = float(t.get("amount",0.0))
            total += amt
            ev.append((t.get("transactionId",""), amt, t["transactionDateTime"]))
    ev.sort(key=lambda x: x[2])
    return round(total,2), ev

def _year_bounds(now: datetime):
    s = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    e = s.replace(year=s.year+1)
    return s, e

def _month_bounds(now: datetime):
    s = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    e = s.replace(year=s.year+1, month=1) if s.month==12 else s.replace(month=s.month+1)
    return s, e

def total_interest_all(transactions: List[Dict]):
    return _sum_interest(transactions)

def total_interest_year(transactions: List[Dict], now: datetime):
    s,e = _year_bounds(now); return _sum_interest(transactions, s, e)

def total_interest_month(transactions: List[Dict], now: datetime):
    s,e = _month_bounds(now); return _sum_interest(transactions, s, e)

TOTAL_PATTERNS = [
    (re.compile(r"\btotal interest\b(?!.*(year|month))", re.I), "all"),
    (re.compile(r"\btotal interest\b.*\bthis year\b", re.I), "year"),
    (re.compile(r"\btotal interest\b.*\bthis month\b", re.I), "month")
]

def detect_total_interest_intent(q: str):
    for pat, kind in TOTAL_PATTERNS:
        if pat.search(q): return kind
    return None
