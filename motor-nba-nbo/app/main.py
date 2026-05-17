import os
from typing import Any
import asyncio

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


COMPONENTE_PROMOCIONES_URL = os.getenv(
    "COMPONENTE_PROMOCIONES_URL", "http://componente-promociones:8000"
)

app = FastAPI(title="Motor NBA/NBO")
FORCE_DIFFERENT_RESPONSE_NEXT_EVALUATE = False
FORCE_RESPONSE_LOCK = asyncio.Lock()


class EvaluacionRequest(BaseModel):
    cliente_id: str = Field(..., min_length=1)
    segmento: str = "general"
    canal: str = "web"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "motor-nba-nbo"}


@app.post("/force-different-response")
async def force_different_response() -> dict[str, Any]:
    global FORCE_DIFFERENT_RESPONSE_NEXT_EVALUATE
    async with FORCE_RESPONSE_LOCK:
        FORCE_DIFFERENT_RESPONSE_NEXT_EVALUATE = True

    return {
        "forced_next_evaluate": True,
        "message": "Different response will be forced",
    }


@app.post("/evaluate")
async def evaluate(payload: EvaluacionRequest) -> dict[str, Any]:
    forced_response = await _consume_forced_response_flag()
    if forced_response:
        return {
            "cliente_id": payload.cliente_id,
            "decision": "oferta_diferente",
            "promocion": {
                "id": "forced-different-response",
                "message": "Intentionally different response",
            },
        }

    promociones = await _obtener_promociones()
    canal = payload.canal.upper()
    elegibles = [
        promocion
        for promocion in promociones
        if promocion.get("status") == "ACTIVE"
        and promocion.get("channel", canal) in {canal, "ALL"}
    ]
    elegibles.sort(key=lambda item: item.get("priority", 0), reverse=True)
    recomendacion = elegibles[0] if elegibles else None

    return {
        "cliente_id": payload.cliente_id,
        "decision": "oferta_disponible" if recomendacion else "sin_oferta",
        "promocion": recomendacion,
    }


async def _obtener_promociones() -> list[dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{COMPONENTE_PROMOCIONES_URL}/campaigns")
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return data
            return data.get("items", [])
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


async def _consume_forced_response_flag() -> bool:
    global FORCE_DIFFERENT_RESPONSE_NEXT_EVALUATE
    async with FORCE_RESPONSE_LOCK:
        should_force = FORCE_DIFFERENT_RESPONSE_NEXT_EVALUATE
        FORCE_DIFFERENT_RESPONSE_NEXT_EVALUATE = False
        return should_force
