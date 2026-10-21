from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import ItemCondition, ItemStatus, OrderStatus, UserRole


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
    role: UserRole = UserRole.buyer

    @field_validator("role")
    @classmethod
    def role_must_be_public(cls, value: UserRole) -> UserRole:
        if value == UserRole.admin:
            raise ValueError("cannot register as admin")
        return value


class UserOut(ORMModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    sort: int = 0


class CategoryOut(ORMModel):
    id: int
    name: str
    sort: int


class ItemCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    description: str = ""
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    condition: ItemCondition = ItemCondition.good
    category_id: int
    image_urls: list[str] = Field(default_factory=list)


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    condition: ItemCondition | None = None
    category_id: int | None = None
    image_urls: list[str] | None = None


class ItemOut(ORMModel):
    id: int
    title: str
    description: str
    price: Decimal
    condition: ItemCondition
    status: ItemStatus
    category_id: int
    category_name: str
    seller_id: int
    seller_name: str
    view_count: int
    image_urls: list[str]
    reject_reason: str | None
    created_at: datetime


class ItemPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ItemOut]


class FavoriteOut(ORMModel):
    id: int
    item: ItemOut
    created_at: datetime


class OrderCreate(BaseModel):
    item_id: int


class OrderOut(ORMModel):
    id: int
    item_id: int
    item_title: str
    buyer_id: int
    buyer_name: str
    seller_id: int
    seller_name: str
    status: OrderStatus
    price: Decimal
    created_at: datetime


class OrderPage(BaseModel):
    total: int
    items: list[OrderOut]


class AuditRequest(BaseModel):
    approve: bool
    reason: str | None = None


class Message(BaseModel):
    detail: str
