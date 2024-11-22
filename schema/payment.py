from pydantic import BaseModel, EmailStr


class InitializePaymentRequest(BaseModel):
    amount: int
    email: EmailStr


# Define a schema for payment verification, especially if the client needs to pass additional information, like the transaction_reference.
class PaymentVerificationSchema(BaseModel):
    reference: str  # unique transaction reference ID from Paystack


# Create a schema for the response after payment initiation or verification to standardize the structure of the data returned.
class PaymentResponseSchema(BaseModel):
    authorization_url: str
    access_code: str
    reference: str


class PaystackWebhookRequest(BaseModel):
    event: str
    data: dict


class PaymentInitializationError(Exception):
    """Exception raised when payment initialization fails."""

    pass
