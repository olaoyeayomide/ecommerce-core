from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from typing import List

# from sqlalchemy.orm import Session
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

from typing import List

from db.models import ProductImage
from core.rbac import has_role

router = APIRouter()


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


# +Get products
@router.get("/products/", response_model=List[ProductResponse])
def get_products(db: db_dependency, skip: int = 0, limit: int = 10):
    products = get_all_products(db=db, skip=skip, limit=limit)
    return products


# GET PRODUCT BY ID
@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: db_dependency):
    product = get_product_by_id(db=db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# UPDATE PRODUCT
# @router.put("/products/{product_id}", response_model=ProductResponse)
# def update_product(
#     product_id: int,
#     product_update: ProductCreate,  # Assuming it shares the same schema
#     db: db_dependency,
#     # current_user: User = Depends(get_current_user),
# ):
#     updated_product = update_product_by_id(
#         db=db, product_id=product_id, product_data=product_update
#     )
#     if not updated_product:
#         raise HTTPException(status_code=404, detail="Product not found")
#     return updated_product


# DELETE PRODUCT
@router.delete(
    "/products/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(has_role(["admin", "vendor"]))],
)
def delete_product(
    product_id: int,
    db: db_dependency,
    # current_user: User = Depends(get_current_user)
):
    deleted_product = delete_product_by_id(db=db, product_id=product_id)
    if not deleted_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return deleted_product


# IMAGES


# UPLOAD IMAGES
@router.post("/products/{product_id}/upload-image", response_model=ProductResponse)
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


@router.post("/products/{product_id}/upload-images", response_model=List[str])
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


@router.delete("/products/{product_id}/images/{image_id}")
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
