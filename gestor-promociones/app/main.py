import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

from app.db import promociones_collection
from app.kafka import publisher


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gestor de promociones")


class Promocion(BaseModel):
    id: str = Field(default_factory=lambda: f"promo-{uuid4().hex[:8]}")
    name: str = Field(..., min_length=1)
    description: str = ""
    segment: str = "general"
    channel: str = "web"
    priority: int = 0
    active: bool = True
    starts_at: datetime | None = None
    ends_at: datetime | None = None


@app.on_event("startup")
async def startup() -> None:
    await publisher.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    await publisher.stop()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "gestor-promociones"}


@app.get("/promociones")
async def listar_promociones() -> list[dict[str, Any]]:
    try:
        items = list(promociones_collection().find({}, {"_id": 0}))
        return items
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/promociones", status_code=status.HTTP_201_CREATED)
async def crear_promocion(payload: Promocion) -> dict[str, Any]:
    document = payload.model_dump(mode="json")
    try:
        promociones_collection().insert_one(document)
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    event = {
        "event_type": "promotion_created",
        "event_id": str(uuid4()),
        "source": "gestor-promociones",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "payload": document,
    }
    try:
        await publisher.publish_promotion_created(event)
    except Exception as exc:
        logger.error(
            "promotion_created_event_publish_failed",
            extra={"promotion_id": document["id"], "error": str(exc)},
        )
        raise HTTPException(status_code=502, detail="Promotion saved but event publish failed") from exc

    logger.info("promotion_created", extra={"promotion_id": document["id"]})
    return document
