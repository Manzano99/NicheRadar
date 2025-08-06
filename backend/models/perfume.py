from pydantic import BaseModel

class Perfume(BaseModel):
    name: str
    brand: str
    price: float
    url: str