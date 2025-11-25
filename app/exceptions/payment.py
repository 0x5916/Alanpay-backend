from typing import Optional
from fastapi import HTTPException, status
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    detail: str
    code: Optional[str] = None

class TransactionException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class TransactionNotFoundException(TransactionException):
    def __init__(self, detail: str = "Transaction not found"):
        super().__init__(detail)

class InsufficientBalanceException(TransactionException):
    def __init__(self, detail: str = "Insufficient balance"):
        super().__init__(detail)

class InvalidAmountException(TransactionException):
    def __init__(self, detail: str = "Invalid amount"):
        super().__init__(detail)

class InvalidQRPaymentException(TransactionException):
    def __init__(self, detail: str = "QR payment must have a valid QR code"):
        super().__init__(detail)
