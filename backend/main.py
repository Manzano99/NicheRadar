from fastapi import FastAPI
from routes import perfume_routes

app = FastAPI(
    title="NicheRadar API",
    description="API para comparar precios de perfumes nicho en distintas tiendas online.",
    version="0.1.0"
)

app.include_router(perfume_routes.router)