from fastapi import APIRouter, Query
from models.perfume import Perfume
from scrapers.notino_scraper import scrape_notino

router = APIRouter(prefix="/api", tags=["Perfumes"])

@router.get("/ping")
def ping():
    return {"message": "pong - NicheRadar está vivo"}

@router.get("/perfumes", response_model=list[Perfume])
def get_perfumes():
    return [
        Perfume(
            name="Oud for Greatness",
            brand="Initio",
            price=245.00,
            url="https://example.com/oud-for-greatness"
        ),
        Perfume(
            name="Herod",
            brand="Parfums de Marly",
            price=180.00,
            url="https://example.com/herod"
        )
    ]
    
@router.get("/scrape/notino")
def get_perfumes_from_notino(
    limit: int = Query(5, ge=1, le=50),
    country: str = Query("es", min_length=2, max_length=3),
):
    return scrape_notino(limit=limit, country=country)