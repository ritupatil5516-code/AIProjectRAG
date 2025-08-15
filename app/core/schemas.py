
from typing import List, Optional
from pydantic import BaseModel

class AccountSummary(BaseModel):
    accountId: str
    accountNumberLast4: Optional[str] = None
    accountStatus: Optional[str] = None
    subStatuses: Optional[List[str]] = None
    highestPriorityStatus: Optional[str] = None
    creditLimit: Optional[float] = None
    availableCredit: Optional[float] = None
    currentBalance: Optional[float] = None
    statementBalance: Optional[float] = None
    purchaseApr: Optional[float] = None
    minimumDueAmount: Optional[float] = None
    paymentDueDate: Optional[str] = None
    billingCycleOpenDateTime: Optional[str] = None
    billingCycleCloseDateTime: Optional[str] = None

class Statement(BaseModel):
    statementId: str
    openingDateTime: str
    closingDateTime: str
    dueDate: Optional[str] = None
    purchases: Optional[float] = 0.0
    paymentsAndCredits: Optional[float] = 0.0
    interestCharged: Optional[float] = 0.0
    feesCharged: Optional[float] = 0.0
    minimumPaymentDue: Optional[float] = 0.0
    unpaidBalance: Optional[float] = 0.0

class Transaction(BaseModel):
    transactionId: str
    transactionType: str
    transactionStatus: str
    transactionDateTime: str
    amount: float
    endingBalance: Optional[float] = None
    displayTransactionType: Optional[str] = None

class PaymentFunding(BaseModel):
    fundingType: Optional[str] = None
    last4Account: Optional[str] = None

class Payment(BaseModel):
    paymentId: str
    state: str
    paymentDateTime: Optional[str] = None
    effectiveDateTime: Optional[str] = None
    amount: float
    fundingSource: Optional[List[PaymentFunding]] = None

class DataBundle(BaseModel):
    account_summary: List[AccountSummary]
    transactions: List[Transaction]
    statements: List[Statement]
    payments: List[Payment]
