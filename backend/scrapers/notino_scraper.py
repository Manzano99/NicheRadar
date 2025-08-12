from __future__ import annotations
import re
import time
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

@dataclass
class PerfumeItem:
    source: str
    name: str
    price: float
    currency: str
    url: str
    image: Optional[str] = None

PRICE_RE = re.compile(r"(\d+[.,]?\d*)")
CURRENCY_RE = re.compile(r"(€|EUR|£|GBP|Kč|PLN|RON|lei|Ft|HUF|zł|CZK)")

def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def _parse_price(text: str) -> Tuple[Optional[float], Optional[str]]:
    if not text:
        return None, None
    price_match = PRICE_RE.search(text)
    currency_match = CURRENCY_RE.search(text)
    if not price_match:
        return None, currency_match.group(1) if currency_match else None
    raw = price_match.group(1).replace(".", "").replace(",", ".")
    try:
        value = float(raw)
    except ValueError:
        return None, currency_match.group(1) if currency_match else None
    currency = currency_match.group(1) if currency_match else "€"
    return value, currency

def _candidate_selectors():
    """
    Varios sets de selectores por si Notino cambia nombres de clases.
    Cada entrada es un dict con selectores para card, name, price, url, img.
    """
    return [
        # Variante A (típica en listados de categoría)
        {
            "card": "div.product-item",
            "name": "a.product__title, a.product__title span, h3.product__title",
            "price": ".price .actual, .price b, .price__main, .price span",
            "url": "a.product__title, a.product__link",
            "img": "img",
        },
        # Variante B (grid cards)
        {
            "card": "div.grid__item, li.grid__item, article.product",
            "name": ".product-name, .product__title, h3 a, h3",
            "price": ".product-price, .price, .price__main, .price__value",
            "url": "a[href]",
            "img": "img",
        },
        # Variante C (fallback genérico)
        {
            "card": "article, li, div",
            "name": "[class*='title'], [class*='name']",
            "price": "[class*='price']",
            "url": "a[href]",
            "img": "img",
        },
    ]

def _extract_items(soup: BeautifulSoup, limit: int = 5) -> List[PerfumeItem]:
    for sel in _candidate_selectors():
        cards = soup.select(sel["card"])
        items: List[PerfumeItem] = []
        seen_urls = set()
        for card in cards:
            # Nombre
            name_el = card.select_one(sel["name"])
            name = _clean_text(name_el.get_text()) if name_el else None
            if not name or len(name) < 3:
                continue

            # Precio
            price_el = card.select_one(sel["price"])
            price_text = _clean_text(price_el.get_text()) if price_el else ""
            price, currency = _parse_price(price_text)
            if price is None:
                # A veces el precio va en data-attributes
                for attr in ("data-price", "data-product-price", "data-price-value"):
                    if card.has_attr(attr):
                        price, currency = _parse_price(card.get(attr, ""))
                        break
            if price is None:
                continue

            # URL
            url_el = card.select_one(sel["url"])
            url = url_el["href"] if (url_el and url_el.has_attr("href")) else None
            if url and url.startswith("//"):
                url = "https:" + url
            if not url:
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Imagen (opcional)
            img_el = card.select_one(sel["img"])
            img = None
            if img_el:
                img = img_el.get("data-src") or img_el.get("src")
                if img and img.startswith("//"):
                    img = "https:" + img

            items.append(
                PerfumeItem(
                    source="notino",
                    name=name,
                    price=price,
                    currency=currency or "€",
                    url=url,
                    image=img,
                )
            )
            if len(items) >= limit:
                return items
        if items:
            return items
    return []

def scrape_notino(limit: int = 5, country: str = "es", pause_s: float = 0.0) -> List[dict]:
    """
    Raspa el listado principal de perfumes en Notino para el país dado.
    country: 'es', 'fr', 'de', etc. (controla el dominio y moneda).
    """
    base = f"https://www.notino.{country}"
    # Página de perfumes genérica; puedes cambiar a una subcategoría si lo prefieres
    url = f"{base}/perfumes/"
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    items = _extract_items(soup, limit=limit)

    # Fallback simple: intenta una página de “marcas populares” si no hubo resultados
    if not items:
        alt_url = f"{base}/bestsellers/perfumes/"
        alt = requests.get(alt_url, headers=DEFAULT_HEADERS, timeout=15)
        if alt.ok:
            soup2 = BeautifulSoup(alt.text, "html.parser")
            items = _extract_items(soup2, limit=limit)

    # Pausa opcional para ser amable con el sitio (si añades más páginas)
    if pause_s:
        time.sleep(pause_s)

    return [asdict(i) for i in items]