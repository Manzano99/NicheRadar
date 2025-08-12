from pydantic import BaseModel, HttpUrl

class Perfume(BaseModel):
    name: str
    brand: str | None = None
    price: float
    url: HttpUrl