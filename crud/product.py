from sqlalchemy.orm import Session
from db.models import Product, ProductImage
from schema.product import ProductCreate
import os
from fastapi import UploadFile, HTTPException
from typing import List
import shutil
from db.session import db_dependency
from PIL import Image
import aiofiles


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
BASE_URL = "http://127.0.0.1:8000"  # Base URL of your server
UPLOAD_DIR = "static/product_images"  # Directory to store uploaded images
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Create if it doesn't exist


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# def upload_image(file: UploadFile):
#     # Ensure the file type is allowed
#     if not allowed_file(file.filename):
#         raise HTTPException(
#             status_code=400, detail="Invalid file type. Only images are allowed."
#         )

#     # Save the file to the designated location
#     file_location = os.path.join(UPLOAD_DIR, file.filename)

#     try:
#         with open(file_location, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

#     # Return the full URL path to the uploaded image
#     return f"{BASE_URL}/static/product_images/{file.filename}"


def upload_image(file: UploadFile, product_id: int) -> str:
    product_dir = os.path.join(UPLOAD_DIR)
    os.makedirs(product_dir, exist_ok=True)
    file_location = os.path.join(product_dir, file.filename)

    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Return a URL pointing to the image
        image_url = f"http://127.0.0.1:8000/{file_location}"
        return image_url
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")


def create_product_image(db, product_id: int, image_url: str):
    """Create and save a new image record for a product."""
    new_image = ProductImage(product_id=product_id, image_url=image_url)
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    return new_image


def delete_product_image(db, product_id: int, image_id: int):
    """Delete an image record for a product from the database and filesystem."""
    image = (
        db.query(ProductImage)
        .filter(ProductImage.id == image_id, ProductImage.product_id == product_id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Delete image file from the filesystem
    try:
        os.remove(image.image_url)
    except Exception:
        pass  # Handle file deletion error

    db.delete(image)
    db.commit()
    return image


# NEW
# Validate File Size: Reject overly large images.
# Validate Dimensions: Use libraries like Pillow to enforce specific width and height constraints.


def validate_image(file: UploadFile):
    try:
        img = Image.open(file.file)
        if img.width > 2000 or img.height > 2000:
            raise HTTPException(
                status_code=400, detail="Image dimensions exceed the limit"
            )
        file.file.seek(0)  # Reset file pointer after reading
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")


#  Add Asynchronous File Uploads
# For improved scalability and performance, make the file upload process asynchronous if your setup supports it:
async def async_upload_image(file: UploadFile, product_id: int):
    product_dir = os.path.join(UPLOAD_DIR, str(product_id))
    os.makedirs(product_dir, exist_ok=True)
    file_location = os.path.join(product_dir, file.filename)

    try:
        async with aiofiles.open(file_location, "wb") as buffer:
            while chunk := await file.read(1024):  # Read in chunks
                await buffer.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    return f"{BASE_URL}/static/product_images/{product_id}/{file.filename}"


def create_product(
    db: db_dependency,
    product: ProductCreate,
):

    db_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
    )

    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def get_all_products(
    db: db_dependency, skip: int = 0, limit: int = 10
) -> List[Product]:
    products = db.query(Product).offset(skip).limit(limit).all()
    return products


# GET PRODUCT BY ID
def get_product_by_id(db: db_dependency, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()


# UPDATE PRODUCT
def update_product_by_id(
    db: db_dependency, product_id: int, product_data: ProductCreate
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    # Update the product fields
    product.name = product_data.name
    product.price = product_data.price
    product.description = product_data.description
    product.stock = product_data.stock

    db.commit()
    db.refresh(product)
    return product


# DELETE PRODUCT
def delete_product_by_id(db: db_dependency, product_id: int):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    db.delete(product)
    db.commit()
    return product


# UPLOAD IMAGES
def upload_product_image(db: db_dependency, product_id: int, file: UploadFile):
    # File type validation
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only images are allowed."
        )

    # Retrieve the product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Handle file upload
    upload_directory = "images/"
    os.makedirs(upload_directory, exist_ok=True)
    file_location = os.path.join(upload_directory, file.filename)

    try:
        with open(file_location, "wb") as image:
            shutil.copyfileobj(file.file, image)
        # Associate image with product
        product.image_url = f"http://127.0.0.1:8000/{file_location}"
        db.add(product)
        db.commit()
        db.refresh(product)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    return product
