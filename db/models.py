from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Float,
    DateTime,
    Boolean,
    Table,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from db.session import Base
from enum import Enum
import uuid
from sqlalchemy.sql import func
from sqlalchemy import JSON

order_product_association = Table(
    "order_product",
    Base.metadata,
    Column("order_id", Integer, ForeignKey("orders.id"), primary_key=True),
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
)


# ROLE MODEL
class Role(Enum):
    ADMIN = "admin"
    VENDOR = "vendor"
    USER = "user"


# USER MODEL
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True)
    phone_number = Column(String)
    hashed_password = Column(String)
    otp_secret = Column(String, nullable=True)
    role = Column(String, default=Role.USER.value)
    permissions = Column(JSON, nullable=True)  # Additional fine-grained permissions
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Relationship to orders
    orders = relationship("Order", back_populates="user")


# USER MODEL
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_price = Column(Float, nullable=False)
    reference = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    order_status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )  # Last update time

    # Relationships
    # Many-to-many relationship with Product
    products = relationship(
        "Product", secondary=order_product_association, back_populates="orders"
    )
    payments = relationship(
        "Payment", back_populates="order"
    )  # Link payments to orders
    user = relationship(
        "User", back_populates="orders"
    )  # Link orders to users (if applicable)


# PRODUCT MODEL
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    description = Column(String)
    stock = Column(Integer)
    image_url = Column(String)
    # Relationships
    orders = relationship(
        "Order", secondary=order_product_association, back_populates="products"
    )


# PRODUCT IMAGE MODEL
class ProductImage(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    image_url = Column(String, nullable=False)


# PAYMENT MODEL
class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    reference = Column(String, unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="initialized")
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    order = relationship(
        "Order", back_populates="payments"
    )  # Establish relationship with the Order model
