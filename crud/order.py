from sqlalchemy.orm import Session
from db.models import Order, User, Product
from schema.order import OrderUpdate
from sqlalchemy import func
from typing import List


# ---------------------------
# Order Management Functions
# ---------------------------


# CREATE ORDER
# - Creates a new order for a user with associated products.
# - Parameters:
#   - `db (Session)`: Database session.
#   - `user_id (int)`: ID of the user placing the order.
#   - `product_ids (List[int])`: List of product IDs to be included in the order.
# - Returns:
#   - `Order`: The created order with associated products.
# - Raises:
#   - `ValueError`: If any products are not found or the user is invalid.
def create_order(db: Session, user_id: int, product_ids: List[int]) -> Order:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    if len(products) != len(product_ids):
        raise ValueError("Some products not found")
    total_price = sum(product.price for product in products)
    order = Order(user_id=user_id, total_price=total_price, products=products)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


# GET ORDER BY ID
# - Retrieves an order by its ID.
# - Parameters:
#   - `db (Session)`: Database session.
#   - `order_id (int)`: ID of the order to fetch.
# - Returns:
#   - `Order`: The retrieved order if found; `None` otherwise.
def get_order(db: Session, order_id: int) -> Order:
    return db.query(Order).filter(Order.id == order_id).first()


# ADD PRODUCT TO ORDER
# - Adds a product to an existing order and updates its total price.
# - Parameters:
#   - `db (Session)`: Database session.
#   - `order_id (int)`: ID of the order to update.
#   - `product_id (int)`: ID of the product to add.
# - Returns:
#   - `Order`: The updated order with the added product.
# - Raises:
#   - `ValueError`: If the product or order is not found.
def add_product_to_order(db: Session, order_id: int, product_id: int) -> Order:
    order = get_order(db, order_id)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not order or not product:
        return None
    order.products.append(product)
    order.total_price += product.price
    db.commit()
    db.refresh(order)
    return order


# UPDATE ORDER
# - Updates an existing order based on the provided `OrderUpdate` schema.
# - Parameters:
#   - `db (Session)`: Database session.
#   - `order_id (int)`: ID of the order to update.
#   - `order_data (OrderUpdate)`: Updated data for the order.
# - Returns:
#   - `Order`: The updated order object.
# - Raises:
#   - `ValueError`: If the order is not found or invalid data is provided.
def update_order(db: Session, order_id: int, order_data: OrderUpdate) -> Order:
    order = get_order(db, order_id)
    if not order:
        return None
    for key, value in order_data.dict(exclude_unset=True).items():
        setattr(order, key, value)
    db.commit()
    db.refresh(order)
    return order


# DELETE ORDER
# - Deletes an order by its ID.
# - Parameters:
#   - `db (Session)`: Database session.
#   - `order_id (int)`: ID of the order to delete.
# - Returns:
#   - `bool`: True if the order is deleted successfully; False otherwise.
# - Raises:
#   - `ValueError`: If the order is not found or cannot be deleted.
def delete_order(db: Session, order_id: int) -> bool:
    order = get_order(db, order_id)
    if not order:
        return False
    db.delete(order)
    db.commit()
    return True


def get_total_order_price(user_id: int, db: Session) -> float:
    return (
        db.query(func.sum(Order.total_price)).filter(Order.user_id == user_id).scalar()
        or 0.0
    )
