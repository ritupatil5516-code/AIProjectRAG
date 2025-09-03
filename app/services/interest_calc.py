from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict
import zoneinfo

def _to_local(dt_str: str, tz: str):
    tzinfo = zoneinfo.ZoneInfo(tz)
    return datetime.fromisoformat(dt_str.replace("Z","+00:00")).astimezone(tzinfo)

def build_daily_balances_tz(transactions: List[Dict], start_local: datetime, end_local: datetime, tz="America/New_York"):
    tzinfo = zoneinfo.ZoneInfo(tz)
    evts = []
    for t in transactions:
        if (t.get("transactionStatus") or "").upper() != "POSTED":
            continue
        ts_local = _to_local(t["transactionDateTime"], tz)
        typ = (t.get("transactionType") or "").upper()
        amt = float(t.get("amount", 0.0))
        delta = +amt if typ in {"PURCHASE","FEE","INTEREST","CASH_ADVANCE","BALANCE_TRANSFER"} else -amt
        evts.append((ts_local, delta, float(t.get("endingBalance") or 0.0)))
    if not evts:
        return None
    evts.sort(key=lambda x: x[0])

    # Anchor
    anchor = None
    for ts, d, endbal in reversed(evts):
        if ts.date() <= start_local.date():
            anchor = endbal; break
    if anchor is None:
        ts0, d0, end0 = evts[0]
        anchor = end0 - d0

    day = datetime(start_local.year, start_local.month, start_local.day, tzinfo=tzinfo)
    end_day = datetime(end_local.year, end_local.month, end_local.day, tzinfo=tzinfo)
    i = 0
    balances = []
    while day <= end_day:
        next_day = day + timedelta(days=1)
        while i < len(evts) and day <= evts[i][0] < next_day:
            anchor += evts[i][1]
            i += 1
        balances.append(round(anchor + 1e-9, 2))
        day = next_day
    return balances

def monthly_interest_from_daily(daily_balances: List[float], apr_percent: float, basis_days: int, rounding="sum_then_round"):
    dpr = (apr_percent/100.0)/float(basis_days)
    if rounding == "daily_then_sum":
        cents = [round(round(b*dpr, 6), 2) for b in daily_balances]
        return round(sum(cents), 2)
    return round(sum(b*dpr for b in daily_balances), 2)
