from pydantic import BaseModel
from typing import Optional, List

class Agreement(BaseModel):
    purchaseApr: Optional[float] = None
    cashAdvanceApr: Optional[float] = None
    balanceTransferApr: Optional[float] = None
    penaltyApr: Optional[float] = None
    apr_basis: int = 365
    interest_method: str = "ADB_including_new"
    hasGracePeriod: bool = True
    graceCondition: str = "prior statement paid in full by due date"
    compounding: str = "daily"
    postingDay: str = "statement_close"
    minFixedFloor: float = 25.0
    minPercentOfBalance: float = 0.01
    rounding: str = "sum_then_round"
    tz: str = "America/New_York"

class AccountSummary(BaseModel):
    accountId: str
    creditLimit: float
    availableCredit: Optional[float] = None
    currentBalance: Optional[float] = None
    statementBalance: Optional[float] = None
    purchaseApr: Optional[float] = None
    highestPriorityStatus: Optional[str] = None
    billingCycleOpenDateTime: Optional[str] = None
    billingCycleCloseDateTime: Optional[str] = None

class Statement(BaseModel):
    statementId: str
    openingDateTime: str
    closingDateTime: str
    dueDate: str
    purchases: Optional[float] = 0.0
    paymentsAndCredits: Optional[float] = 0.0
    interestCharged: Optional[float] = 0.0
    feesCharged: Optional[float] = 0.0
    minimumPaymentDue: Optional[float] = 0.0
    unpaidBalance: Optional[float] = 0.0

class Payment(BaseModel):
    paymentId: str
    state: str
    paymentDateTime: str
    effectiveDateTime: Optional[str] = None
    amount: float
    fundingSource: Optional[list] = None

class Transaction(BaseModel):
    transactionId: str
    transactionType: str
    transactionStatus: str
    transactionDateTime: str
    amount: float
    endingBalance: Optional[float] = None
