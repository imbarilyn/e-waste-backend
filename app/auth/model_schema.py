import uuid
from enum import IntEnum
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from enum import Enum




# Enum for representing related constants
class UsedResetToken(IntEnum):
    unused = 1
    used = 0

# Admin
class AdminBase(SQLModel):
    full_name: str = Field(index=True)
    phone_number: str = Field(index=True)
    email: str = Field(index=True)

class Admin(AdminBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field(index=True)
    created_at: datetime = Field(default=datetime.now())
#    relationship
    aggregators: list["Aggregator"] = Relationship(back_populates="admin")


class AdminPublic(AdminBase):
    id: uuid.UUID
    created_at: datetime

class AdminCreate(AdminBase):
    password: str
    confirm_password: str





# Aggregator
class AggregatorBase(SQLModel):
    full_name: str = Field(index=True)
    phone_number: str = Field(index=True)
    email: str = Field(index=True)
    location: str = Field(index=True)

class Aggregator(AggregatorBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field(index=True)
    created_at: datetime = Field(default=datetime.now())
    admin_id: uuid.UUID = Field(foreign_key="admin.id")
    # relationship
    admin: Admin = Relationship(back_populates="aggregators")


class AggregatorPublic(AggregatorBase):
    id: uuid.UUID

class AggregatorCreate(AggregatorBase):
    password: str
    confirm_password: str

# Password Reset
class PasswordReset(SQLModel):
    reset_token: str
    reset_token_expiry: datetime | None = Field(default=None)
    used_reset_token: int = Field(default=0)
    admin_id: uuid.UUID = Field(foreign_key="admin.id")
    admin: Admin = Relationship(back_populates="password_reset")
    aggregator_id: uuid.UUID = Field(foreign_key="aggregator.id")
    aggregator: Aggregator = Relationship(back_populates="password_reset")


