import os
from dotenv import load_dotenv
from paystackapi.paystack import Paystack
from fastapi import HTTPException
from paystackapi.transaction import Transaction
import uuid
import logging
import requests
from db.session import db_dependency
from db.models import Order, Payment
from core.email import send_email
from sqlalchemy.orm import Session
from schema.payment import PaymentInitializationError


load_dotenv()

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
paystackapi = Paystack(secret_key=PAYSTACK_SECRET_KEY)
CALLBACK_URL = os.getenv("PAYSTACK_CALLBACK_URL")


def get_order_by_reference(db: Session, reference: str):
    """
    Fetch an order by its reference ID.
    """
    return db.query(Order).filter(Order.reference == reference).first()


def initialize_payment(order, db: Session):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "email": order.user.email,
        "amount": int(order.total_price * 100),  # Convert to kobo
        "reference": order.reference,
    }

    # Make the request to Paystack
    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()

    if response.status_code != 200 or not response_data.get("status"):
        raise ValueError(f"Paystack API error: {response_data}")

    # Save the payment to the database
    payment = Payment(
        reference=order.reference,
        order_id=order.id,
        amount=order.total_price,
        status="initialized",
    )
    db.add(payment)
    db.commit()

    return response_data["data"]["authorization_url"]


def verify_payment(reference: str, db: Session):
    response = Transaction.verify(reference=reference)

    if not response["status"] or response["data"]["status"] != "success":
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # Update the payment record
    payment = db.query(Payment).filter(Payment.reference == reference).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment.status = "success"
    payment.paid_at = response["data"].get("paid_at")
    payment.amount = response["data"]["amount"] / 100  # Convert to major currency unit
    db.commit()

    return response["data"]


def get_payment_status(reference):
    response = Transaction.verify(reference=reference)
    return response["data"]["status"]


def get_payment_history():
    response = Transaction.list(perPage=10, page=1)
    if response["status"] and response["data"]:
        return response["data"]
    else:
        raise Exception("Failed to fetch payment history")


def redirect_to_payment_page(payment_url):
    return {"payment_url": payment_url}


def handle_successful_payment(db: db_dependency, payment_data: dict):
    # Extract data from payment_data
    transaction_reference = payment_data.get("reference")
    user_email = payment_data.get("customer", {}).get("email")
    amount = payment_data.get("amount")
    status = payment_data.get("status")

    # 1. Update Order in Database
    try:
        order = db.query(Order).filter(Order.reference == transaction_reference).first()
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")

        # Update order status based on successful payment
        order.status = "completed"
        order.paid_at = payment_data.get("paid_at")  # Set to payment timestamp
        order.amount_paid = amount / 100  # Convert from kobo to naira, for example

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating order: {str(e)}")

    # 2. Send Confirmation Email to Customer
    try:
        email_subject = "Payment Successful - Thank you for your purchase!"
        email_body = f"Dear customer,\n\nYour payment of NGN{amount / 100} was successful. Your order will be processed shortly.\n\nThank you for shopping with us!"

        send_email(to_address=user_email, subject=email_subject, body=email_body)
    except Exception as e:
        # Log or handle email sending failure (optional)
        print(f"Error sending confirmation email: {str(e)}")

    return {"status": "success", "payment_data": payment_data}
