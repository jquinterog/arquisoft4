import asyncio
import json
import os
from collections import Counter
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DEFAULT_REPLICAS = (
    "http://motor-nba-nbo-0.motor-nba-nbo:8000,"
    "http://motor-nba-nbo-1.motor-nba-nbo:8000,"
    "http://motor-nba-nbo-2.motor-nba-nbo:8000"
)

MOTOR_NBA_NBO_REPLICAS = os.getenv("MOTOR_NBA_NBO_REPLICAS", DEFAULT_REPLICAS)
MOTOR_NBA_NBO_TIMEOUT = float(os.getenv("MOTOR_NBA_NBO_TIMEOUT", "10"))

app = FastAPI(title="Voting Engine")


class EvaluacionRequest(BaseModel):
    cliente_id: str = Field(..., min_length=1)
    segmento: str = "general"
    canal: str = "web"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "voting"}


@app.post("/evaluate")
async def evaluate(payload: EvaluacionRequest) -> dict[str, Any]:
    replicas = _parse_replicas(MOTOR_NBA_NBO_REPLICAS)
    if len(replicas) < 3:
        raise HTTPException(status_code=500, detail="Se requieren al menos 3 replicas configuradas")

    responses = await _query_replicas(replicas, payload.model_dump())

    hash_counter = Counter(item["hash"] for item in responses)
    majority_hash, majority_votes = hash_counter.most_common(1)[0]
    unanimous = majority_votes == len(responses)
    consistent = majority_votes >= 2

    majority_item = next(item for item in responses if item["hash"] == majority_hash)
    majority_payload = majority_item["response"]

    discrepant_replicas = [
        item["replica"] for item in responses if item["hash"] != majority_hash
    ]

    if isinstance(majority_payload, dict):
        final_response: dict[str, Any] = dict(majority_payload)
    else:
        final_response = {"result": majority_payload}

    if not consistent:
        final_response = {
            "decision": "inconsistente",
            "detail": "No hubo mayoria entre replicas",
            "resultados": [item["response"] for item in responses],
        }

    final_response["_voting"] = {
        "replicas_consultadas": len(responses),
        "unanimidad": unanimous,
        "consistencia": consistent,
        "votos_ganadores": majority_votes,
        "replicas_con_discrepancia": discrepant_replicas,
        "replica_ganadora": majority_item["replica"],
    }

    return final_response


def _parse_replicas(raw_replicas: str) -> list[str]:
    return [item.strip().rstrip("/") for item in raw_replicas.split(",") if item.strip()]


async def _query_replicas(replicas: list[str], payload: dict[str, Any]) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=MOTOR_NBA_NBO_TIMEOUT) as client:
        tasks = [
            _query_single_replica(client=client, replica_url=replica_url, payload=payload)
            for replica_url in replicas
        ]
        return await asyncio.gather(*tasks)


async def _query_single_replica(
    client: httpx.AsyncClient,
    replica_url: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        response = await client.post(f"{replica_url}/evaluate", json=payload)
        response.raise_for_status()
        parsed = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Error consultando replica {replica_url}: {exc}",
        ) from exc

    return {
        "replica": replica_url,
        "response": parsed,
        "hash": _stable_hash(parsed),
    }


def _stable_hash(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
