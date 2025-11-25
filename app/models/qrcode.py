from datetime import datetime
from enum import Enum
import json
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.models.transaction import MoneyDecimal, IntegerDecimal

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.user import User

class QRType(Enum):
    REQUEST_PAYMENT = "request_payment"  # You request money from others
    SEND_PAYMENT = "send_payment"        # You send money to others

class QRCode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    qr_id: str = Field(index=True, unique=True, nullable=False)
    qr_type: QRType = Field(nullable=False)
    max_use_count: IntegerDecimal = Field(default=None, nullable=True)
    amount: Optional[MoneyDecimal] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    expire: Optional[datetime] = Field(default=None, nullable=True)

    user_id: int = Field(foreign_key="user.id", index=True)
    user: "User" = Relationship(
        back_populates="qrcodes",
        sa_relationship_kwargs={
            "foreign_keys": "QRCode.user_id",
            "primaryjoin": "QRCode.user_id == User.id"
        }
    )

    # Relationship to transactions
    transactions: list["Transaction"] = Relationship(
        back_populates="qrcode",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "Transaction.qr_id",
            "primaryjoin": "QRCode.id == Transaction.qr_id"
        }
    )

    @classmethod
    async def get_by_qr_id(cls, session: AsyncSession, qr_id: str) -> Optional["QRCode"]:
        stmt = select(cls).options(selectinload(cls.user)).where(cls.qr_id == qr_id).limit(1) # type: ignore
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def current_use_count(self, session: AsyncSession) -> int:
        stmt = text("SELECT COUNT(*) FROM transaction WHERE qr_id = :id AND user_id = (SELECT user_id FROM qrcode WHERE id = :id LIMIT 1)")\
            .bindparams(id=self.id)
        result = await session.execute(stmt)
        cnt = result.scalar()
        return cnt or 0
    
    async def is_exceed_limit(self, session: AsyncSession) -> bool:
        current_count = await self.current_use_count(session)
        return current_count >= self.max_use_count

    def to_qrcode_dict(self) -> dict:
        return {
            "qr_id": self.qr_id,
            "qr_type": self.qr_type.value,
            "amount": str(self.amount),
            "expire": self.expire.isoformat() if self.expire else None
        }
    
    def to_qrcode_json(self) -> str:
        return json.dumps(self.to_qrcode_dict(), separators=(',', ':'), ensure_ascii=False)

    @property
    def is_expired(self) -> bool:
        return self.expire is not None and datetime.now() > self.expire

    def can_be_used(self) -> bool:
        return not self.is_expired
    
    @classmethod
    async def clean_unused_send_qrcodes(cls, session: AsyncSession) -> int:
        stmt = delete(cls).where(
            cls.qr_type == QRType.SEND_PAYMENT, # type: ignore
            text("id NOT IN (SELECT qr_id FROM transaction)")
        )
        
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount