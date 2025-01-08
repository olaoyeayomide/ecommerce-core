from fastapi import APIRouter, Depends, HTTPException, status
from schema.order import OrderResponse, OrderUpdate, OrderTotalResponse, OrderCreate
from schema.product import AddProductToOrderRequest
from db.models import User, OrderStatus
from core.rbac import has_role
from crud.order import (
    create_order,
    get_order,
    update_order,
    delete_order,
    add_product_to_order,
    get_total_order_price,
)
from db.session import db_dependency
from core.security import get_current_user
from typing import List
from db.models import Order

router = APIRouter()


# CREATE ORDER
# Endpoint to create a new order for a user.
# Parameters:
# - `user_id`: ID of the user creating the order.
# - `product_ids`: List of product IDs to include in the order.
# - `db`: Database session dependency.
# - `current_user`: The currently authenticated user.
# Functionality:
# - Verifies the user matches the authenticated user.
# - Calls `create_order` to create an order for the user.
# - Returns the created order or raises an exception if validation fails.
@router.post(
    "/orders/", response_model=OrderResponse, dependencies=[Depends(has_role(["user"]))]
)
def create_order_endpoint(
    user_id: int,
    product_ids: List[int],
    db: db_dependency,
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized"
        )
    return create_order(db, user_id, product_ids)


# GET ORDER
# Endpoint to retrieve details of an existing order by ID.
# Parameters:
# - `order_id`: ID of the order to retrieve.
# - `db`: Database session dependency.
# Functionality:
# - Calls `get_order` to fetch the order from the database.
# - Returns the order details or raises an exception if the order is not found.
@router.get("/orders/{order_id}", response_model=OrderResponse)
def read_order(order_id: int, db: db_dependency):
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    return order


# ADD PRODUCT TO ORDER
# Endpoint to add a product to an existing order.
# Parameters:
# - `order_id`: ID of the order to update.
# - `product_data`: Request body containing the product ID to add.
# - `db`: Database session dependency.
# Functionality:
# - Calls `add_product_to_order` to associate a product with the specified order.
# - Returns the updated order or raises an exception if the order or product is not found.
@router.post("/orders/{order_id}/products/")
def add_product(
    order_id: int, product_data: AddProductToOrderRequest, db: db_dependency
):
    order = add_product_to_order(db, order_id, product_data.product_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order or product not found"
        )
    return order


# UPDATE ORDER
# Endpoint to update an existing order.
# Parameters:
# - `order_id`: ID of the order to update.
# - `order`: Request body containing the updated order details.
# - `db`: Database session dependency.
# Functionality:
# - Calls `update_order` to modify the specified order.
# - Returns the updated order or raises an exception if the order is not found.
@router.put("/orders/{order_id}", response_model=OrderResponse)
def update_order_view(order_id: int, order: OrderUpdate, db: db_dependency):
    updated_order = update_order(db, order_id, order)
    if not updated_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    return updated_order


# DELETE ORDER
# Endpoint to delete an existing order.
# Parameters:
# - `order_id`: ID of the order to delete.
# - `db`: Database session dependency.
# Functionality:
# - Calls `delete_order` to remove the specified order.
# - Returns a success message or raises an exception if the order is not found.
@router.delete(
    "/orders/{order_id}",
    response_model=dict,
    dependencies=[Depends(has_role(["admin"]))],
)
def delete_order_view(order_id: int, db: db_dependency):
    if not delete_order(db, order_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    return {"detail": "Order deleted"}


# GET USER ORDERS TOTAL
# Endpoint to calculate the total price of all orders for a user.
# Parameters:
# - `user_id`: ID of the user whose total orders are to be calculated.
# - `db`: Database session dependency.
# Functionality:
# - Calls `get_total_order_price` to calculate the total order value for the user.
# - Returns the total price or raises an exception if no orders are found.
@router.get("/orders/user-orders-total/{user_id}", response_model=OrderTotalResponse)
def get_user_orders_total(user_id: int, db: db_dependency):
    total_price = get_total_order_price(user_id, db)
    if total_price == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No orders found"
        )
    return {"user_id": user_id, "total_price": total_price}


@router.get(
    "/order-status/{order_reference}",
    dependencies=[Depends(has_role(["admin", "user"]))],
)
async def order_status(order_reference: str, db: db_dependency):
    order = db.query(Order).filter(Order.reference == order_reference).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {"order_reference": order.reference, "status": order.status.value}


@router.put("/update-order-status/", dependencies=[Depends(has_role(["admin"]))])
async def update_order_status(
    order_reference: str, status: OrderStatus, db: db_dependency
):
    order = db.query(Order).filter(Order.reference == order_reference).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = status
    db.commit()
    return {"status": "success", "message": "Order status updated successfully"}
