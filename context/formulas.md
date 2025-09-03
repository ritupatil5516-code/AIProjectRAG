**Formulas**
- DPR = APR / apr_basis.
- Monthly interest = sum(daily_balance * DPR) with rounding policy:
  - sum_then_round (default)
  - daily_then_sum (round each day to cent then sum)
