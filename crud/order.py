from sqlalchemy.orm import Session
from db.models import Order, User, Product
from schema.order import OrderResponse, OrderUpdate
from db.session import db_dependency
from sqlalchemy import func


def create_order(db, user_id: int, product_ids: list[int]):
    # Check if the user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    # Initialize the total price
    total_price = 0

    # Create a new order for the user
    new_order = Order(user_id=user_id, total_price=0)
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Add products to the order and calculate the total price
    invalid_products = []
    for product_id in product_ids:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product is None:
            raise ValueError(f"Product with ID {product_id} not found")

        new_order.products.append(product)
        total_price += product.price

    # Update the total_price of the order
    new_order.total_price = total_price
    db.commit()
    db.refresh(new_order)

    # Log or handle invalid products if needed
    if invalid_products:
        print(f"Invalid product IDs: {invalid_products}")  # Log for debugging

    return new_order


# def get_order(db: db_dependency, order_id: int) -> OrderResponse:
def get_order(db: db_dependency, order_id: int):
    return db.query(Order).filter(Order.id == order_id).first()


def get_user_orders(db: Session, user_id: int):
    return db.query(Order).filter(Order.user_id == user_id).all()


def get_orders(
    db: db_dependency, skip: int = 0, limit: int = 10
) -> list[OrderResponse]:
    return db.query(Order).offset(skip).limit(limit).all()


# Add a product to an order
def add_product_to_order(db: db_dependency, order_id: int, product_id: int):
    order = db.query(Order).filter(Order.id == order_id).first()
    product = db.query(Product).filter(Product.id == product_id).first()

    if order and product:
        order.products.append(product)  # Append product to the order
        db.commit()
        db.refresh(order)

    return order


def update_order(db: db_dependency, order_id: int, order: OrderUpdate) -> Order:
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if db_order:
        for key, value in order.dict(exclude_unset=True).items():
            setattr(db_order, key, value)
        db.commit()
        db.refresh(db_order)
    return db_order


def delete_order(db: db_dependency, order_id: int) -> bool:
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if db_order:
        db.delete(db_order)
        db.commit()
        return True
    return False


def get_total_order_price(user_id: int, db: db_dependency) -> float:
    print(f"Looking for orders for user_id: {user_id}")
    total_price = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .with_entities(func.sum(Order.total_price))
        .scalar()
    )

    # If there are no orders, return 0
    return total_price or 0.0
