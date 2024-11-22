from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from schema.product import ProductResponse


# Shared properties for Order
class OrderBase(BaseModel):
    user_id: int
    total_price: float
    order_status: Optional[str] = "pending"


# Schema for creating a new order (used in POST requests)
class OrderCreate(BaseModel):
    # user_id: int,
    product_ids: List[int]


# Schema for updating an order
class OrderUpdate(OrderBase):
    order_status: Optional[str] = None


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

    # class OrderResponse(BaseModel):
    #     id: int
    #     user_id: int
    #     total_price: float
    #     reference: str
    #     created_at: datetime
    #     products: List[ProductResponse]

    class Config:
        from_attributes = True


# Initialize this later


# from enum import Enum

# class OrderStatus(str, Enum):
#     pending = "pending"
#     completed = "completed"
#     canceled = "canceled"
#     refunded = "refunded"

# class Order(Base):
#     __tablename__ = "orders"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     total_price = Column(Float, nullable=False)
#     order_status = Column(String, default=OrderStatus.pending.value)
#     created_at = Column(DateTime, default=datetime.utcnow)

#     user = relationship("User", back_populates="orders")
