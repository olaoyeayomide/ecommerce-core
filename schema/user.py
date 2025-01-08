from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from schema.order import OrderResponse
from enum import Enum


# Shared properties for User
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    is_active: bool = True
    role: str


# Schema for creating a new user (used in POST requests)
class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: Optional[str] = None
    email: EmailStr
    password: str


# Schema for updating user information
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr]
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool]


# Schema for user stored in the database (used in responses)
class UserResponse(UserBase):
    id: int
    created_at: datetime
    orders: Optional[List["OrderResponse"]] = []

    class Config:
        from_attributes = True


class UserRole(str, Enum):
    ADMIN = "admin"
    VENDOR = "vendor"
    CUSTOMER = "customer"
