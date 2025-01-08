from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from schema.product import ProductResponse


# Shared properties for Order
class OrderBase(BaseModel):
    user_id: int
    total_price: float
    status: Optional[str] = "pending"


# Schema for creating a new order (used in POST requests)
class OrderCreate(BaseModel):
    # user_id: int,
    product_ids: List[int]


# Schema for updating an order
class OrderUpdate(OrderBase):
    status: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    user_id: int  # ForeignKey reference to the User model
    created_at: datetime
    total_price: float
    reference: str
    products: List[ProductResponse]


class OrderTotalResponse(BaseModel):
    user_id: int
    total_price: float

    class Config:
        from_attributes = True
