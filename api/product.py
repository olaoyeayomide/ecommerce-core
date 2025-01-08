from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from typing import List
from schema.product import ProductCreate, ProductResponse
from crud.product import (
    create_product,
    upload_image,
    get_all_products,
    get_product_by_id,
    update_product_by_id,
    delete_product_by_id,
    upload_product_image,
    create_product_image,
    # delete_product_image,
)
from db.session import db_dependency
from db.models import ProductImage
from core.rbac import has_role

router = APIRouter()


# CREATE PRODUCT
# Endpoint: Create a new product
# Description:
#   Adds a new product to the database with details like name, price, description, and stock.
# Request Body:
#   - name (str): The name of the product.
#   - price (float): The price of the product.
#   - description (str): A brief description of the product.
#   - stock (int): The available stock for the product.
# Dependencies:
#   - Requires the current user to have "admin" or "vendor" roles.
# Response:
#   - The created product details.
@router.post(
    "/products/",
    response_model=ProductResponse,
    dependencies=[Depends(has_role(["admin", "vendor"]))],
)
def create_new_product(
    db: db_dependency,
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    stock: int = Form(...),
):
    product_data = ProductCreate(
        name=name, price=price, description=description, stock=stock
    )
    new_product = create_product(db=db, product=product_data)
    return new_product


# GET PRODUCT
# Endpoint: Retrieve a list of products
# Description:
#   Fetches a paginated list of all products in the database.
# Query Parameters:
#   - skip (int): The number of products to skip (default: 0).
#   - limit (int): The maximum number of products to return (default: 10).
# Response:
#   - A list of products.
@router.get("/products/", response_model=List[ProductResponse])
def get_products(db: db_dependency, skip: int = 0, limit: int = 10):
    products = get_all_products(db=db, skip=skip, limit=limit)
    return products


# GET PRODUCT BY ID
# Endpoint: Retrieve a product by ID
# Description:
#   Fetches the details of a specific product by its ID.
# Path Parameters:
#   - product_id (int): The ID of the product to retrieve.
# Response:
#   - The product details or a 404 error if the product is not found.
@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: db_dependency):
    product = get_product_by_id(db=db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# UPDATE PRODUCT
# Endpoint: Update a product by ID
# Description:
#   Updates the details of a specific product.
# Path Parameters:
#   - product_id (int): The ID of the product to update.
# Request Body:
#   - ProductCreate schema: The updated product details.
# Response:
#   - The updated product details or a 404 error if the product is not found.
@router.put(
    "/products/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(has_role(["admin", "vendor"]))],
)
def update_product(
    product_id: int,
    product_update: ProductCreate,
    db: db_dependency,
):
    updated_product = update_product_by_id(
        db=db, product_id=product_id, product_data=product_update
    )
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product


# DELETE PRODUCT
# Endpoint: Delete a product by ID
# Description:
#   Deletes a specific product from the database.
# Path Parameters:
#   - product_id (int): The ID of the product to delete.
# Dependencies:
#   - Requires the current user to have "admin" or "vendor" roles.
# Response:
#   - The details of the deleted product or a 404 error if the product is not found.
@router.delete(
    "/products/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(has_role(["admin", "vendor"]))],
)
def delete_product(
    product_id: int,
    db: db_dependency,
):
    deleted_product = delete_product_by_id(db=db, product_id=product_id)
    if not deleted_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return deleted_product


# === IMAGE MANAGEMENT ENDPOINTS ===

# Endpoint: Upload an image for a product
# Description:
#   Uploads a single image for a specific product.
# Path Parameters:
#   - product_id (int): The ID of the product to upload the image for.
# Request Body:
#   - file (UploadFile): The image file to upload.
# Response:
#   - The updated product details with the uploaded image or a 404 error if the product is not found.


# UPLOAD IMAGES
@router.post(
    "/products/{product_id}/upload-image",
    response_model=ProductResponse,
    dependencies=[Depends(has_role(["admin", "vendor"]))],
)
def upload_product_img(
    db: db_dependency,
    product_id: int,
    file: UploadFile = File(...),
):
    product = get_product_by_id(db=db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # Call upload_image function or similar for adding the image
    updated_product = upload_product_image(db=db, product_id=product_id, file=file)
    return updated_product


# UPLOAD MULTIPLE IMAGES
# Endpoint: Upload multiple images for a product
# Description:
#   Uploads multiple images for a specific product and saves their URLs in the database.
# Path Parameters:
#   - product_id (int): The ID of the product to upload images for.
# Request Body:
#   - files (List[UploadFile]): A list of image files to upload.
# Response:
#   - A list of URLs of the uploaded images or a 404 error if the product is not found.
@router.post(
    "/products/{product_id}/upload-images",
    response_model=List[str],
    dependencies=[Depends(has_role(["admin", "vendor"]))],
)
def upload_multiple_images(product_id: int, files: List[UploadFile], db: db_dependency):
    product = get_product_by_id(db=db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    uploaded_urls = []
    for file in files:
        # Upload image to filesystem and get the URL
        image_url = upload_image(file, product_id)

        # Create image record in the database
        create_product_image(db, product_id, image_url)

        uploaded_urls.append(image_url)

    return uploaded_urls


# DELETE PRODUCT IMAGE
# Endpoint: Delete an image for a product
# Description:
#   Deletes a specific image of a product from the database and file system.
# Path Parameters:
#   - product_id (int): The ID of the product the image belongs to.
#   - image_id (int): The ID of the image to delete.
# Response:
#   - A success message or a 404 error if the product or image is not found.
@router.delete(
    "/products/{product_id}/images/{image_id}",
    dependencies=[Depends(has_role(["admin", "vendor"]))],
)
def delete_product_image(product_id: int, image_id: int, db: db_dependency):
    product = get_product_by_id(db=db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    image = (
        db.query(ProductImage)
        .filter(ProductImage.id == image_id, ProductImage.product_id == product_id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        os.remove(image.image_url)  # Delete the file from the filesystem
    except Exception:
        pass  # Handle file deletion error

    db.delete(image)
    db.commit()
    return {"detail": "Image deleted successfully"}
