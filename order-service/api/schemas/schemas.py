from pydantic import BaseModel

class QRCode(BaseModel):
    code: str  # (for example stolik_1)

class OrderRequest(BaseModel):
    qr_code: str
    item_id: int  # Item's id from the menu
