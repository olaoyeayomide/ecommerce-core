from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.user import router as user_router
from api.product import router as product_router
from api.order import router as order_router
from api.mfa import router as mfa_router
from api.email import router as email_router
from api.auth import router as auth_router
from payment.paystack_routers import router as payment_router
from db.session import Base, engine

app = FastAPI()

# Mount the directory as a static route to serve images
app.mount(
    "/static/product_images",
    StaticFiles(directory="static/product_images"),
    name="product_images",
)

app.include_router(user_router)
app.include_router(product_router, prefix="/product", tags=["product"])
app.include_router(order_router, prefix="/order", tags=["order"])
app.include_router(mfa_router, prefix="/mfa", tags=["mfa"])
app.include_router(email_router, prefix="/email", tags=["email"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(payment_router, prefix="/payments", tags=["payments"])

# Create database tables
Base.metadata.create_all(bind=engine)
