from fastapi import FastAPI
from routes import auth, order, payment

app = FastAPI(
    title="API Gateway",
    description="Gateway for routing requests to microservices"
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(order.router, prefix="/order", tags=["order"])
app.include_router(payment.router, prefix="/payment", tags=["payment"])

@app.get("/", tags=["Health"])
def root():
    return {"status": "API Gateway is up"}
