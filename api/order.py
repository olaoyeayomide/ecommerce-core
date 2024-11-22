from fastapi import APIRouter, Depends, HTTPException, status
from schema.order import OrderResponse, OrderUpdate, OrderTotalResponse, OrderCreate
from schema.product import AddProductToOrderRequest
from db.models import User
from core.rbac import has_role

# from crud import order as crud_order
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

router = APIRouter()


@router.post(
    "/orders/", response_model=OrderResponse, dependencies=[Depends(has_role(["user"]))]
)
def create_order_endpoint(
    user_id: int,
    product_ids: List[int],
    db: db_dependency,
    current_user: User = Depends(get_current_user),
):
    # Check if the user exists and matches the current user
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create orders for this user",
        )

    order = create_order(db=db, user_id=user_id, product_ids=product_ids)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User or product not found"
        )

    return order


# @router.post(
#     "/orders/", response_model=dict, dependencies=[Depends(has_role(["user"]))]
# )
# async def create_order_endpoint(
#     order_data: OrderCreate,
#     db: db_dependency,
#     current_user: User = Depends(get_current_user),
# ):
#     new_order = await create_order(db=db, user_id=user_id, product_ids=product_ids)
#     return {"message": "Order created successfully", "order": new_order}


@router.get("/orders/{order_id}", response_model=OrderResponse)
def read_get_order(order_id: int, db: db_dependency):
    db_order = get_order(db=db, order_id=order_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order


# Endpoint to add a product to an order
@router.post("/orders/{order_id}/products/")
def add_product(
    order_id: int, product_data: AddProductToOrderRequest, db: db_dependency
):
    order = add_product_to_order(db, order_id, product_id=product_data.product_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order or product not found")
    return order


@router.put("/orders/{order_id}", response_model=OrderResponse)
def update_order_view(order_id: int, order: OrderUpdate, db: db_dependency):
    db_order = update_order(db=db, order_id=order_id, order=order)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order


@router.delete(
    "/orders/{order_id}",
    response_model=dict,
    dependencies=[Depends(has_role(["admin"]))],
)
def delete_order_view(order_id: int, db: db_dependency):
    success = delete_order(db=db, order_id=order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"detail": "Order deleted"}


# NOTE: Work on this later

# @router.get("/orders/me", response_model=list[OrderResponse])
# def get_orders_for_user(
#     db: db_dependency, current_user: User = Depends(get_current_user)
# ):
#     orders = get_user_orders(db, user_id=current_user.id)
#     return orders


@router.get("/orders/user-orders-total/{user_id}", response_model=OrderTotalResponse)
def get_user_orders_total(user_id: int, db: db_dependency):
    """
    API endpoint to get the total price of a user's orders.
    """
    total_price = get_total_order_price(user_id=user_id, db=db)
    print(f"Total price: {total_price}")

    if total_price == 0:
        raise HTTPException(status_code=404, detail="No orders found for this user")

    return {"user_id": user_id, "total_price": total_price}
