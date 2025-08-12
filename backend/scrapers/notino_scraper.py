import requests
from bs4 import BeautifulSoup

def scrape_notino():
    url = "https://www.notino.es/perfumes/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": "No se pudo acceder a la página"}

    soup = BeautifulSoup(response.text, 'html.parser')

    perfumes = []

    product_cards = soup.select('.product-item__text')[:5]  # Limita a 5 para pruebas

    for card in product_cards:
        name_tag = card.select_one('.product-item__name')
        price_tag = card.select_one('.price__value')

        if name_tag and price_tag:
            perfume = {
                "name": name_tag.get_text(strip=True),
                "price": price_tag.get_text(strip=True)
            }
            perfumes.append(perfume)

    return perfumes