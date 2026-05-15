import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException


GESTOR_PROMOCIONES_URL = os.getenv(
    "GESTOR_PROMOCIONES_URL", "http://gestor-promociones:8000"
)
MOTOR_NBA_NBO_URL = os.getenv("MOTOR_NBA_NBO_URL", "http://motor-nba-nbo:8000")

app = FastAPI(title="API Gateway")


async def _proxy(method: str, url: str, json: dict[str, Any] | None = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(method, url, json=json)
            response.raise_for_status()
            if response.content:
                return response.json()
            return None
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.text,
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}


@app.get("/promociones")
async def listar_promociones() -> Any:
    return await _proxy("GET", f"{GESTOR_PROMOCIONES_URL}/promociones")


@app.post("/promociones", status_code=201)
async def crear_promocion(payload: dict[str, Any]) -> Any:
    return await _proxy("POST", f"{GESTOR_PROMOCIONES_URL}/promociones", json=payload)


@app.post("/nba-nbo/evaluate")
async def evaluar_nba_nbo(payload: dict[str, Any]) -> Any:
    return await _proxy("POST", f"{MOTOR_NBA_NBO_URL}/evaluate", json=payload)
