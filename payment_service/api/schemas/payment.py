from pydantic import BaseModel
from typing import List

class Product(BaseModel):
    name: str
    unitPrice: str
    quantity: str

class Buyer(BaseModel):
    email: str
    phone: str
    firstName: str
    lastName: str
    language: str

# class Refund(BaseModel):
#     description: str
#     currencyCode: str

class CreatePaymentRequest(BaseModel):
    description: str
    currencyCode: str
    totalAmount: str
    products: List[Product]
    buyer: Buyer
    customerIp: str
    notifyUrl: str

class CreateRefundRequest(BaseModel):
    description: str
    currencyCode: str