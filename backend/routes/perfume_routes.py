from fastapi import APIRouter, Query, HTTPException
import requests
from models.scraped_item import ScrapedItem
from scrapers.notino_scraper import scrape_notino, scrape_notino_product

router = APIRouter(prefix="/api", tags=["Perfumes"])

@router.get("/scrape/notino", response_model=list[ScrapedItem])
def scrape_notino_list(
    limit: int = Query(5, ge=1, le=50),
    country: str = Query("es", min_length=2, max_length=3),
):
    try:
        items = scrape_notino(limit=limit, country=country, pause_s=0.4)
        if not items:
            raise HTTPException(status_code=204, detail="Sin resultados (posible bloqueo o cambios de markup).")
        return items
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else 502
        raise HTTPException(status_code=status, detail=f"Notino respondió {status}. Prueba otro país o más tarde.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scrape/notino/product", response_model=ScrapedItem)
def scrape_notino_product_route(
    url: str = Query(..., description="URL completa del producto en Notino"),
    country: str | None = Query(None, description="Opcional: es, fr, de, it"),
):
    try:
        item = scrape_notino_product(url=url, country=country)
        return item
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else 502
        raise HTTPException(status_code=status, detail=f"Notino respondió {status} al consultar el producto.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))