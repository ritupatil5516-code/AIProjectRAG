**Rules**
1. Agreement‑first for interest/min‑payment; fallback to ledger if missing.
2. Use POSTED transactions for balances and interest; ignore pending.
3. For "how much interest YYYY‑MM", request deterministic compute (calc_request).
4. Always include used_fields and notes; never invent values.
