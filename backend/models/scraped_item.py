from pydantic import BaseModel, HttpUrl
class ScrapedItem(BaseModel):
    source: str
    name: str
    price: float
    currency: str
    url: HttpUrl
    image: HttpUrl | None = None