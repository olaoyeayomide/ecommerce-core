from fastapi import APIRouter, HTTPException, Depends
from db.session import db_dependency
from db.models import Product, Order, User
from core.rbac import has_role

router = APIRouter()


# Endpoint for fetching all products (admin access)
@router.get("/admin/products/", dependencies=[Depends(has_role(["admin"]))])
async def list_products(db: db_dependency):
    try:
        products = db.query(Product).all()
        return {"products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint for fetching all orders (admin access)
@router.get("/admin/orders/", dependencies=[Depends(has_role(["admin"]))])
async def list_orders(db: db_dependency):
    try:
        orders = db.query(Order).all()
        return {"orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint for fetching all users (admin access)
@router.get("/admin/users/", dependencies=[Depends(has_role(["admin"]))])
async def list_users(db: db_dependency):
    try:
        users = db.query(User).all()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
