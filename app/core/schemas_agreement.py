
from pydantic import BaseModel
from typing import Optional

class Agreement(BaseModel):
    purchaseApr: Optional[float] = None
    cashAdvanceApr: Optional[float] = None
    balanceTransferApr: Optional[float] = None
    penaltyApr: Optional[float] = None
    apr_basis: int = 365
    interest_method: str = "ADB_including_new"
    hasGracePeriod: bool = True
    graceCondition: Optional[str] = "prior statement paid in full by due date"
    compounding: str = "daily"
    postingDay: str = "statement_close"
    minFixedFloor: float = 25.0
    minPercentOfBalance: float = 0.01
    lateFee: Optional[float] = None
    returnedPaymentFee: Optional[float] = None
    cashAdvanceFeePct: Optional[float] = None
    btFeePct: Optional[float] = None
    foreignTxnPct: Optional[float] = None
    rounding: str = "to_cent"
    trailingInterest: bool = True
