import logging

from fastapi import FastAPI

from app.consumer import consumer


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="Adaptador Excel")


@app.on_event("startup")
async def startup() -> None:
    await consumer.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    await consumer.stop()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "adaptador-excel"}
