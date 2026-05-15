import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


GESTOR_PROMOCIONES_URL = os.getenv(
    "GESTOR_PROMOCIONES_URL", "http://gestor-promociones:8000"
)

app = FastAPI(title="Motor NBA/NBO")


class EvaluacionRequest(BaseModel):
    cliente_id: str = Field(..., min_length=1)
    segmento: str = "general"
    canal: str = "web"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "motor-nba-nbo"}


@app.post("/evaluate")
async def evaluate(payload: EvaluacionRequest) -> dict[str, Any]:
    promociones = await _obtener_promociones()
    elegibles = [
        promocion
        for promocion in promociones
        if promocion.get("active", True)
        and promocion.get("segment", "general") in {payload.segmento, "general"}
        and promocion.get("channel", payload.canal) in {payload.canal, "todos"}
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
            response = await client.get(f"{GESTOR_PROMOCIONES_URL}/promociones")
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return data
            return data.get("items", [])
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
