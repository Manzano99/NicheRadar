from __future__ import annotations
import re
import time
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter

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

try:
    # urllib3 v2+
    from urllib3.util.retry import Retry
    RETRY_KW = {"allowed_methods": {"GET"}}
except Exception:
    # compatibilidad con urllib3<2
    from urllib3.util import Retry
    RETRY_KW = {"method_whitelist": frozenset({"GET"})}

def _build_session() -> requests.Session:
    """
    Crea una sesión requests con retries/backoff y headers de navegador.
    """
    s = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.7,
        status_forcelist=[429, 500, 502, 503, 504],
        **RETRY_KW,
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.headers.update(DEFAULT_HEADERS)
    return s

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

def _is_notino_url(url: str, country: str | None = None) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        if not host.endswith("notino.es") and not host.endswith("notino.fr") and not host.endswith("notino.de") and not host.endswith("notino.it"):
            return False
        if country:
            return host.endswith(f"notino.{country}")
        return True
    except Exception:
        return False

def scrape_notino_product(url: str, country: str | None = None) -> dict:
    """
    Raspa una página de producto concreta en Notino y devuelve {source,name,price,currency,url,image}.
    """
    if not _is_notino_url(url, country):
        raise ValueError("URL no válida para Notino o país no coincide")

    s = _build_session()
    # pre-hit home para cookies si tenemos country deducible
    if country:
        base = f"https://www.notino.{country}/"
        resp_home = s.get(base, timeout=15)
        resp_home.raise_for_status()

    # obtener la página de producto
    resp = s.get(url, headers={"Referer": url}, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # NAME (título H1 o variantes)
    name = None
    for sel in ["h1.product__title", "h1", ".pd-header__title", ".product-name", "meta[property='og:title']"]:
        el = soup.select_one(sel)
        if el:
            name = _clean_text(el.get("content") or el.get_text())
            if name:
                break

    # PRICE (busca en bloques de precio y metas)
    price_text = ""
    for sel in [".price .actual", ".price__main", ".price b", ".product-price", "meta[itemprop='price']"]:
        el = soup.select_one(sel)
        if el:
            price_text = el.get("content") or el.get_text()
            if price_text:
                break
    price, currency = _parse_price(price_text)

    # IMAGE (og:image o img principal)
    image = None
    for sel in ["meta[property='og:image']", ".product__img img", ".pd-gallery__image img", "img"]:
        el = soup.select_one(sel)
        if el:
            image = el.get("content") or el.get("src") or el.get("data-src")
            if image:
                if image.startswith("//"): image = "https:" + image
                break

    if not name or price is None:
        # intenta leer data-json embebido (simplificado)
        for script in soup.find_all("script"):
            t = script.string or ""
            if t and "price" in t and "name" in t:
                m_name = re.search(r'"name"\s*:\s*"([^"]+)"', t)
                m_price = re.search(r'"price"\s*:\s*"?(?P<p>\d+[.,]?\d*)"?', t)
                m_curr  = re.search(r'"priceCurrency"\s*:\s*"([^"]+)"', t)
                if not name and m_name: name = _clean_text(m_name.group(1))
                if price is None and m_price:
                    price = float(m_price.group("p").replace(".", "").replace(",", "."))
                if not currency and m_curr: currency = m_curr.group(1)
                if name and price is not None:
                    break

    if not name or price is None:
        raise RuntimeError("No se pudo extraer name/price en la página de producto.")

    return {
        "source": "notino",
        "name": name,
        "price": float(price),
        "currency": currency or "€",
        "url": url,
        "image": image,
    }