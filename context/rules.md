# Association & Answering Rules

## Inclusion & Sorting
- Use POSTED transactions only for balances/totals.
- Statement membership: openingDateTime <= transactionDateTime < closingDateTime.
- Sort by transactionDateTime desc; tie-break on highest endingBalance, else max transactionId.

## Balances
- Current balance = latest POSTED endingBalance; fallback account_summary[0].currentBalance.
- Statement balance = account_summary[0].statementBalance else compute from window.
- Ending balance after last payment = payment.endingBalance if present; else next POSTED transaction after payment post.

## Payments
- Upcoming = payments[state="SCHEDULED"], earliest future effectiveDateTime (fallback paymentDateTime).

## Interest (Agreement-first)
- Use agreement.json first for interest/minimum-payment questions; otherwise fall back to these formulas.
- Default posted interest total for a month = sum of POSTED INTEREST transactions in that month.
- For "how much interest for <month>" where ADB math is needed, include calc_request {type: "interest_month", period: "YYYY-MM"}; the app will compute deterministically.
- Explain trailing interest when a balance existed until payment posted.

## FAQ Logic — Interest & Grace Period
1) Why charged interest in March? No grace (prior statement not paid in full by due date) or carried balance → ADB > 0.
2) Paid on the 8th but still got interest — why? Trailing interest until payment posting and/or new purchases without grace.
3) What to pay to avoid more interest? Pay the full statement balance by due date (minimum continues interest).
4) What made up April interest? Report April INTEREST line(s) total; if computing, show DPR, ADB, days.

## Evidence & Errors
- Always return used_fields (JSON paths). If a key field is missing, answer "No matching data found." and list what was missing in notes.