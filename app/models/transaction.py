from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional, TYPE_CHECKING
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship


if TYPE_CHECKING:
    from app.models.user import User
    from app.models.qrcode import QRCode

MoneyDecimal = Annotated[Decimal, Field(max_digits=18, decimal_places=2)]

IntegerDecimal = Annotated[int, Field(ge=0, le=2**31-1)]

class TransactionType(str, Enum):
    TOPUP = "topup"
    WITHDRAWAL = "withdrawal"
    TRANSFER_SENT = "transfer_sent"
    TRANSFER_RECEIVED = "transfer_received"
    QR_PAYMENT = "qr_payment"

class Transaction(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    amount: MoneyDecimal = Field(nullable=False)
    transaction_type: TransactionType = Field(nullable=False)
    description: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.now, index=True)

    user_id: int = Field(foreign_key="user.id", index=True)
    user: "User" = Relationship(
        back_populates="transactions",
        sa_relationship_kwargs={
            "foreign_keys": "Transaction.user_id",
            "primaryjoin": "Transaction.user_id == User.id"
        }
    )

    # Optional reference to another user for transfers
    reference_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    reference_user: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "Transaction.reference_user_id",
            "primaryjoin": "Transaction.reference_user_id == User.id"
        }
    )

    qr_id: Optional[int] = Field(default=None, foreign_key="qrcode.id", index=True)
    qrcode: Optional["QRCode"] = Relationship(
        back_populates="transactions",
        sa_relationship_kwargs={
            "foreign_keys": "Transaction.qr_id",
            "primaryjoin": "Transaction.qr_id == QRCode.id"
        }
    )

class TransactionPublic(SQLModel):
    id: int
    amount: str
    transaction_type: TransactionType
    description: Optional[str]
    timestamp: datetime
    reference_user_name: Optional[str] = None
