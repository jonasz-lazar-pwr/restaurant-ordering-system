from pydantic import BaseModel

class MenuItem(BaseModel):
    id: int
    name: str
    description: str
    price: float