
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional, List, Dict

def _to_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(timezone.utc)

def _round2(x: float) -> float:
    return round(x + 1e-9, 2)

def dpr(apr_percent: float, basis_days: int) -> float:
    return (apr_percent / 100.0) / float(basis_days)

def average_daily_balance(balances: Iterable[float]) -> float:
    vals = list(balances)
    return (sum(vals) / max(1, len(vals))) if vals else 0.0

def monthly_interest_from_adb(apr_percent: float, basis_days: int, daily_balances: Iterable[float]) -> float:
    vals = list(daily_balances)
    if not vals: return 0.0
    adb = average_daily_balance(vals)
    days = len(vals)
    return _round2(adb * dpr(apr_percent, basis_days) * days)

def build_daily_balances(transactions: List[Dict], start: datetime, end: datetime) -> Optional[list]:
    evts = []
    for t in transactions:
        if (t.get("transactionStatus") or "").upper() != "POSTED":
            continue
        ts = _to_dt(t["transactionDateTime"])
        if ts < start - timedelta(days=31) or ts > end + timedelta(days=1):
            continue
        typ = (t.get("transactionType") or "").upper()
        amt = float(t.get("amount", 0.0))
        if typ in ("PURCHASE","FEE","INTEREST","CASH_ADVANCE","BALANCE_TRANSFER"):
            delta = +amt
        elif typ in ("PAYMENT","REFUND","CREDIT"):
            delta = -amt
        else:
            delta = +amt
        evts.append((ts, delta, float(t.get("endingBalance") or 0.0)))

    if not evts: return None
    evts.sort(key=lambda x: x[0])

    # anchor: latest transaction <= start
    start_balance = None
    for ts, _, endbal in reversed(evts):
        if ts <= start:
            start_balance = endbal
            break
    if start_balance is None:
        return None

    day = start
    balances = []
    idx = 0
    while day <= end:
        day_end = day + timedelta(days=1)
        while idx < len(evts) and day <= evts[idx][0] < day_end:
            start_balance += evts[idx][1]
            idx += 1
        balances.append(start_balance)
        day = day_end
    return balances
