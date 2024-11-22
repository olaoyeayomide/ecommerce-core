from pydantic import BaseModel, Field
from typing import Optional
from fastapi import UploadFile, File


class ProductCreate(BaseModel):
    name: str
    price: float
    description: str
    stock: int
    image_url: Optional[str] = None

    # print(f"{image_url}")


class ProductResponse(ProductCreate):
    id: int


class AddProductToOrderRequest(BaseModel):
    product_id: int

    class Config:
        from_attributes = True
