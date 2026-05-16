import logging

from fastapi import FastAPI

from componente_promociones.kafka import publisher
from componente_promociones.routers.campaign_router import router as campaign_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="TeknoShop Campaign Service",
    description="MVP backend service for NBO/NBA campaign management.",
    version="0.1.0",
)

app.include_router(campaign_router)


@app.on_event("shutdown")
async def shutdown() -> None:
    await publisher.stop()


@app.get("/health")
def health_check():
    return {"status": "ok"}
