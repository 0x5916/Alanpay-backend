from datetime import datetime
from decimal import Decimal
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Relationship, SQLModel, Field, table

from typing import TYPE_CHECKING, Optional, Self, Sequence

if TYPE_CHECKING:
    from app.models.qrcode import QRCode
    from app.models.transaction import Transaction

class UserBase(SQLModel):
    pass

class User(UserBase, table=True):
    class Meta:
        tablename = "users"
    id: int = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    password: str = Field(nullable=False)
    transactions: list["Transaction"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "lazy": "selectin", 
            "foreign_keys": "Transaction.user_id",
            "primaryjoin": "User.id == Transaction.user_id"
        }
    )
    qrcodes: list["QRCode"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "lazy": "selectin", 
            "foreign_keys": "QRCode.user_id",
            "primaryjoin": "User.id == QRCode.user_id"
        }
    )

    async def total_balance(self, session: AsyncSession) -> Decimal:
        stmt = text("""
            SELECT COALESCE(SUM(amount), 0.00) as total
            FROM transaction
            WHERE user_id = :user_id
        """).bindparams(user_id=self.id)
        result = await session.execute(stmt)
        return result.scalar() or Decimal('0.00')

    @classmethod
    async def get_all_users(cls, session: AsyncSession) -> Sequence[Self]:
        stmt = select(cls)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    @classmethod
    async def get_by_username(cls, session: AsyncSession, name: str) -> Optional[Self]:
        stmt = select(cls).where(
            text("username = :name").bindparams(name=name)
        ).limit(1)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user

    @classmethod
    async def add(cls, session: AsyncSession, user: Self) -> Self:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @classmethod
    async def update(cls, session: AsyncSession, user: Self) -> Self:
        await session.merge(user)
        await session.commit()
        await session.refresh(user)
        return user

    @classmethod
    async def get_transactions_by_date(
        cls,
        session: AsyncSession, 
        user_id: int, 
        from_date: datetime
    ) -> Sequence["Transaction"]:
        from app.models.transaction import Transaction 

        stmt = select(Transaction).where(
            text("user_id = :user_id").bindparams(user_id=user_id),
            text("timestamp >= :from_date").bindparams(from_date=from_date)
        ).order_by(text("timestamp DESC"))
        result = await session.execute(stmt)
        return result.scalars().all()
    
    @classmethod
    async def get_transactions_by_date_paginated(
        cls, 
        session: AsyncSession, 
        user_id: int, 
        from_date: datetime,
        limit: int = 20,
        offset: int = 0
    ) -> Sequence["Transaction"]:

        stmt = select(text("transaction")).where(
            text("user_id = :user_id").bindparams(user_id=user_id),
            text("timestamp >= :from_date").bindparams(from_date=from_date)
        ).order_by(text("timestamp DESC")).limit(limit).offset(offset)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    @classmethod
    async def count_transactions_by_date(
        cls, 
        session: AsyncSession, 
        user_id: int, 
        from_date: datetime
    ) -> int:
        stmt = text("""
            SELECT COUNT(*) FROM transaction
            WHERE user_id = :user_id AND timestamp >= :from_date
        """).bindparams(
            user_id=user_id,
            from_date=from_date
        )
        result = await session.execute(stmt)
        count = result.scalar()
        return count or 0

class UserPublic(UserBase):
    id: int
    username: str
    balance: str

class UserCreate(UserBase):
    username: str
    password: str

class UserLogin(UserCreate):
    ...

class UserUpdate(UserBase):
    username: Optional[str] = None
    password: Optional[str] = None
