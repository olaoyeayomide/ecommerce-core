from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from payment.paystack_crud import (
    initialize_payment,
    verify_payment,
    get_payment_status,
    get_payment_history,
    handle_successful_payment,
    get_order_by_reference,
)
from db.session import db_dependency
import os
from schema.payment import InitializePaymentRequest, PaystackWebhookRequest
from db.models import Order
import logging
import hmac
import hashlib
import json
from core.rbac import has_role


router = APIRouter()
logger = logging.getLogger(__name__)


PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYLOAD = '{"event": "charge.success", "data": {"reference": "test_reference", "amount": 500000, "status": "success"}}'


# -----------------------------
# API Endpoints for Payment
# -----------------------------


# INITIALIZE PAYMENT ENDPOINT
# - This endpoint initializes a payment for an order by calling the Paystack API.
# - Parameters:
#   - `order_reference (str)`: The reference ID of the order.
#   - `db (db_dependency)`: The database session.
# - Returns:
#   - A dictionary with a "status" key and the Paystack payment URL for the user to complete the payment.
# - Raises:
#   - HTTPException with a 404 status code if the order is not found.
#   - HTTPException with a 400 status code if the order's total price is invalid.
#   - HTTPException with a 500 status code if payment initialization fails.
@router.post(
    "/initialize-payment/",
    dependencies=[Depends(has_role(["admin", "user", "vendor"]))],
)
async def initialize_payment_endpoint(order_reference: str, db: db_dependency):
    # Retrieve the order using the order reference
    order = db.query(Order).filter(Order.reference == order_reference).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order.total_price or order.total_price <= 0:
        raise HTTPException(status_code=400, detail="Invalid order total price")

    try:
        # Initialize payment and save to the database
        payment_url = initialize_payment(order, db)
        return {"status": "success", "payment_url": payment_url}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Payment initialization failed: {str(e)}"
        )


# VERIFY PAYMENT ENDPOINT
# - This endpoint verifies the payment status for a given reference.
# - Parameters:
#   - `reference (str)`: The reference ID of the payment.
#   - `db (db_dependency)`: The database session to verify payment details.
# - Returns:
#   - A dictionary with a "status" key and the payment data if successful.
# - Raises:
#   - HTTPException with a 400 status code if an error occurs during payment verification.
@router.get("/verify-payment/", dependencies=[Depends(has_role(["admin"]))])
async def verify_payment_endpoint(reference: str, db: db_dependency):
    try:
        result = verify_payment(reference, db)
        return {"status": "success", "payment_data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error occurred: {str(e)}")


# PAYMENT STATUS ENDPOINT
# - This endpoint retrieves the status of a payment by referencing the transaction.
# - Parameters:
#   - `reference (str)`: The reference ID of the payment.
# - Returns:
#   - A dictionary containing the payment status.
# - Raises:
#   - HTTPException with a 400 status code if any error occurs.
@router.get("/payment-status/", dependencies=[Depends(has_role(["admin", "user"]))])
async def payment_status_endpoint(reference: str):
    try:
        status = get_payment_status(reference)
        return {"status": status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# PAYMENT HISTORY ENDPOINT
# - This endpoint fetches a list of recent payment transactions from Paystack.
# - Returns:
#   - A dictionary containing the transaction history.
# - Raises:
#   - HTTPException with a 400 status code if fetching the transaction history fails.
@router.get("/payment-history/", dependencies=[Depends(has_role(["admin"]))])
async def payment_history_endpoint():
    try:
        history = get_payment_history()
        return {"transactions": history}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# PAYSTACK WEBHOOK ENDPOINT
# - This endpoint processes incoming webhook events from Paystack.
# - Parameters:
#   - `request (Request)`: The HTTP request object containing the webhook data.
# - Returns:
#   - A message confirming receipt of the webhook event.
# - Raises:
#   - HTTPException with a 400 status code if the signature is invalid or the payload is malformed.
@router.post("/webhook/")
async def paystack_webhook(request: Request):
    headers = request.headers
    raw_body = await request.body()
    signature = headers.get("x-paystack-signature")

    # Validate Paystack webhook signature (this is just an example, adjust as needed)
    expected_signature = hmac.new(
        PAYSTACK_SECRET_KEY.encode("utf-8"), raw_body, hashlib.sha512
    ).hexdigest()

    if signature != expected_signature:
        raise HTTPException(status_code=400, detail="Invalid Paystack signature")

    try:
        parsed_body = json.loads(raw_body)
        logger.info(f"Paystack Webhook received: {parsed_body}")
        # Handle the event here
        return {"message": "Webhook received"}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")
