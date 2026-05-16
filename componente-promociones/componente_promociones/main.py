from fastapi import FastAPI

from componente_promociones.routers.campaign_router import router as campaign_router

app = FastAPI(
    title="TeknoShop Campaign Service",
    description="MVP backend service for NBO/NBA campaign management.",
    version="0.1.0",
)

app.include_router(campaign_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
