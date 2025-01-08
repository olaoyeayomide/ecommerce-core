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

# ---------------------------
# Product Image Management Functions
# ---------------------------


# ALLOWED FILE CHECK
# - Checks if a file has an allowed extension (png, jpg, jpeg, gif).
# - Parameters:
#   - `filename (str)`: The file name to check.
# - Returns:
#   - `bool`: True if the file has an allowed extension; False otherwise.
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# IMAGE UPLOAD
# - Handles the uploading of a product image and stores it in the specified directory.
# - Parameters:
#   - `file (UploadFile)`: The uploaded file object.
#   - `product_id (int)`: The ID of the product to associate with the image.
# - Returns:
#   - `str`: The URL pointing to the uploaded image.
# - Raises:
#   - `HTTPException`: If there's an error saving the file.
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


# CREATE PRODUCT IMAGE
# - Creates and saves a new image record for a product in the database.
# - Parameters:
#   - `db`: Database session.
#   - `product_id (int)`: The ID of the product to associate with the image.
#   - `image_url (str)`: The URL of the uploaded image.
# - Returns:
#   - `ProductImage`: The created image record.
def create_product_image(db, product_id: int, image_url: str):
    """Create and save a new image record for a product."""
    new_image = ProductImage(product_id=product_id, image_url=image_url)
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    return new_image


# DELETE PRODUCT IMAGE
# - Deletes an image record for a product from the database and the filesystem.
# - Parameters:
#   - `db`: Database session.
#   - `product_id (int)`: The ID of the product associated with the image.
#   - `image_id (int)`: The ID of the image to delete.
# - Returns:
#   - `ProductImage`: The deleted image record.
# - Raises:
#   - `HTTPException`: If the image is not found.
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


# VALIDATE IMAGE
# - Validates the dimensions of the uploaded image to ensure it meets the constraints.
# - Parameters:
#   - `file (UploadFile)`: The uploaded file object.
# - Returns:
#   - None
# - Raises:
#   - `HTTPException`: If the image dimensions exceed the allowed limits.
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


# ASYNCHRONOUS IMAGE UPLOAD
# - Handles the asynchronous uploading of a product image.
# - Parameters:
#   - `file (UploadFile)`: The uploaded file object.
#   - `product_id (int)`: The ID of the product to associate with the image.
# - Returns:
#   - `str`: The URL pointing to the uploaded image.
# - Raises:
#   - `HTTPException`: If there's an error saving the file.
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


# CREATE PRODUCT
# - Creates a new product and saves it to the database.
# - Parameters:
#   - `db (db_dependency)`: Database session.
#   - `product (ProductCreate)`: Product data to be saved.
# - Returns:
#   - `Product`: The created product.
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


# GET ALL PRODUCTS
# - Retrieves all products from the database, with optional pagination.
# - Parameters:
#   - `db (db_dependency)`: Database session.
#   - `skip (int)`: Number of products to skip (default: 0).
#   - `limit (int)`: Maximum number of products to return (default: 10).
# - Returns:
#   - `List[Product]`: List of products.
def get_all_products(
    db: db_dependency, skip: int = 0, limit: int = 10
) -> List[Product]:
    products = db.query(Product).offset(skip).limit(limit).all()
    return products


# GET PRODUCT BY ID
# - Retrieves a product by its ID from the database.
# - Parameters:
#   - `db (db_dependency)`: Database session.
#   - `product_id (int)`: The ID of the product to retrieve.
# - Returns:
#   - `Product`: The product with the specified ID, or None if not found.
def get_product_by_id(db: db_dependency, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()


# UPDATE PRODUCT
# - Updates an existing product based on the provided data.
# - Parameters:
#   - `db (db_dependency)`: Database session.
#   - `product_id (int)`: The ID of the product to update.
#   - `product_data (ProductCreate)`: New data for the product.
# - Returns:
#   - `Product`: The updated product, or None if the product was not found.
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
# - Deletes a product by its ID from the database.
# - Parameters:
#   - `db (db_dependency)`: Database session.
#   - `product_id (int)`: The ID of the product to delete.
# - Returns:
#   - `Product`: The deleted product, or None if the product was not found.
def delete_product_by_id(db: db_dependency, product_id: int):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    db.delete(product)
    db.commit()
    return product


# UPLOAD PRODUCT IMAGES
# - Uploads an image for a specific product and associates it with the product in the database.
# - Parameters:
#   - `db (db_dependency)`: Database session.
#   - `product_id (int)`: The ID of the product to associate with the image.
#   - `file (UploadFile)`: The uploaded image file.
# - Returns:
#   - `Product`: The updated product with the associated
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
