import asyncio
import json
import os
import time
from collections import Counter
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from kubernetes import client, config
    try:
        config.load_incluster_config()
        K8S_AVAILABLE = True
    except Exception:
        K8S_AVAILABLE = False
except ImportError:
    K8S_AVAILABLE = False

DEFAULT_REPLICAS = (
    "http://motor-nba-nbo-0.motor-nba-nbo:8000,"
    "http://motor-nba-nbo-1.motor-nba-nbo:8000,"
    "http://motor-nba-nbo-2.motor-nba-nbo:8000"
)

MOTOR_NBA_NBO_REPLICAS = os.getenv("MOTOR_NBA_NBO_REPLICAS", DEFAULT_REPLICAS)
MOTOR_NBA_NBO_TIMEOUT = float(os.getenv("MOTOR_NBA_NBO_TIMEOUT", "10"))
DEFECTIVE_QUARANTINE_SECONDS = float(os.getenv("DEFECTIVE_QUARANTINE_SECONDS", "15"))
RECOVERY_HEALTH_TIMEOUT = float(os.getenv("RECOVERY_HEALTH_TIMEOUT", "2"))

# Estado global de replicas defectuosas
DEFECTIVE_REPLICAS: dict[str, float] = {}
DEFECTIVE_LOCK = asyncio.Lock()

ANSI_COLORS = [
    "\033[91m",  # rojo
    "\033[92m",  # verde
    "\033[93m",  # amarillo
    "\033[94m",  # azul
    "\033[95m",  # magenta
    "\033[96m",  # cian
]
ANSI_RESET = "\033[0m"

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
    evaluation_start_time = time.time()

    replicas = _parse_replicas(MOTOR_NBA_NBO_REPLICAS)
    if len(replicas) < 3:
        print(f"Error: Se requieren al menos 3 replicas configuradas, pero se encontraron {len(replicas)}: {replicas}")
        raise HTTPException(status_code=500, detail="Se requieren al menos 3 replicas configuradas")

    await _recover_healthy_replicas()
    async with DEFECTIVE_LOCK:
        defective_snapshot = dict(DEFECTIVE_REPLICAS)

    # Filtrar replicas defectuosas
    active_replicas = [r for r in replicas if r not in defective_snapshot]
    if len(active_replicas) < 2:
        print(f"Advertencia: Menos de 2 replicas activas. Todas defectuosas: {list(defective_snapshot.keys())}")
        # Si no hay suficientes replicas, usar todas (fuerza recuperación)
        active_replicas = replicas
        async with DEFECTIVE_LOCK:
            DEFECTIVE_REPLICAS.clear()
        print(f"Reset de replicas defectuosas. Usando todas: {active_replicas}")

    print(f":::::::::: Consultando Motor NBA/NBO ::::::::::")
    responses = await _query_replicas(active_replicas, payload.model_dump())

    for index, item in enumerate(responses):
        color = ANSI_COLORS[index*2+1]#color = ANSI_COLORS[index % len(ANSI_COLORS)]
        response_text = json.dumps(item["response"], ensure_ascii=False, indent=2)
        has_discrepancy = item["hash"] != responses[0]["hash"]
        discrepancy_text = "SI" if has_discrepancy else "NO"
        print(
            f"{color}Replica {index + 1} | {item['replica']} | hash={item['hash']} | discrepancia={discrepancy_text}\n"
            f"{ANSI_RESET}"
        )

    hash_counter = Counter(item["hash"] for item in responses)
    majority_hash, majority_votes = hash_counter.most_common(1)[0]
    unanimous = majority_votes == len(responses)
    consistent = majority_votes >= 2

    majority_item = next(item for item in responses if item["hash"] == majority_hash)
    majority_payload = majority_item["response"]

    discrepant_replicas = [
        item["replica"] for item in responses if item["hash"] != majority_hash
    ]

    detection_time_ms = (time.time() - evaluation_start_time) * 1000
    

    # Marcar replicas defectuosas y disparar reemplazo
    if discrepant_replicas:
        print(f"{ANSI_COLORS[0]}[DETECCIÓN] Tiempo de detección de discrepancia: {detection_time_ms:.2f}ms")
        print(f"[DEFECTUOSA] Se encontraron {len(discrepant_replicas)} replica(s) con discrepancia: {discrepant_replicas}{ANSI_RESET}")
        for defective_replica in discrepant_replicas:
            await _mark_defective_and_restart(defective_replica)

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

    async with DEFECTIVE_LOCK:
        current_defective = list(DEFECTIVE_REPLICAS.keys())

    final_response["_voting"] = {
        "replicas_consultadas": len(responses),
        "replicas_activas": len(active_replicas),
        "replicas_defectuosas": current_defective,
        "unanimidad": unanimous,
        "consistencia": consistent,
        "votos_ganadores": majority_votes,
        "replicas_con_discrepancia": discrepant_replicas,
        "replica_ganadora": majority_item["replica"],
        "detection_time_ms": round(detection_time_ms, 2),
    }

    print(f":::::::::: Fin de la consulta ::::::::::")
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


@app.get("/defective-replicas")
async def get_defective_replicas() -> dict[str, Any]:
    """Retorna lista de replicas marcadas como defectuosas."""
    async with DEFECTIVE_LOCK:
        replicas = list(DEFECTIVE_REPLICAS.keys())
    return {
        "defective_replicas": replicas,
        "count": len(replicas),
    }


@app.post("/reset-defective-replicas")
async def reset_defective_replicas() -> dict[str, Any]:
    """Resetea todas las replicas defectuosas (operacion de recuperacion manual)."""
    async with DEFECTIVE_LOCK:
        cleared = list(DEFECTIVE_REPLICAS.keys())
        DEFECTIVE_REPLICAS.clear()
    print(f"[RESET] Replicas defectuosas reseteadas: {cleared}")
    return {
        "message": "Replicas defectuosas reseteadas",
        "cleared": cleared,
    }


async def _mark_defective_and_restart(replica_url: str) -> None:
    """Marca una replica como defectuosa e inicia su reemplazo (restart en k8s)."""
    async with DEFECTIVE_LOCK:
        DEFECTIVE_REPLICAS[replica_url] = time.time()

    print(f"{ANSI_COLORS[0]}[DEFECTUOSA] Replica marcada como defectuosa: {replica_url}")
    print(f"[DEFECTUOSA] Replicas defectuosas totales: {list(DEFECTIVE_REPLICAS.keys())}{ANSI_RESET}")

    # Intentar extraer el nombre del pod del URL para restart en k8s
    pod_name = _extract_pod_name_from_url(replica_url)
    if pod_name:
        await _restart_pod(pod_name)
    else:
        print(f"[ALERTA] No se pudo extraer nombre del pod de {replica_url}")


async def _recover_healthy_replicas() -> None:
    now = time.time()
    async with DEFECTIVE_LOCK:
        defective_items = list(DEFECTIVE_REPLICAS.items())

    if not defective_items:
        return

    recovery_candidates = [
        replica_url
        for replica_url, marked_at in defective_items
        if (now - marked_at) >= DEFECTIVE_QUARANTINE_SECONDS
    ]

    if not recovery_candidates:
        return

    recovered: list[str] = []
    async with httpx.AsyncClient(timeout=RECOVERY_HEALTH_TIMEOUT) as client:
        checks = [
            _is_replica_healthy(client=client, replica_url=replica_url)
            for replica_url in recovery_candidates
        ]
        results = await asyncio.gather(*checks)

    for replica_url, is_healthy in zip(recovery_candidates, results):
        if is_healthy:
            recovered.append(replica_url)

    if not recovered:
        return

    async with DEFECTIVE_LOCK:
        for replica_url in recovered:
            DEFECTIVE_REPLICAS.pop(replica_url, None)

    print(f"[RECOVERY] Replicas recuperadas y reingresadas al voting: {recovered}")


async def _is_replica_healthy(client: httpx.AsyncClient, replica_url: str) -> bool:
    try:
        response = await client.get(f"{replica_url}/health")
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def _extract_pod_name_from_url(replica_url: str) -> str | None:
    """Extrae el nombre del pod de una URL headless service.
    Ejemplo: http://motor-nba-nbo-0.motor-nba-nbo-headless:8000 -> motor-nba-nbo-0"""
    try:
        # Formato esperado: http://motor-nba-nbo-X.motor-nba-nbo-headless:8000
        parts = replica_url.replace("http://", "").replace("https://", "").split(".")
        if parts:
            return parts[0]
    except Exception as e:
        print(f"[ERROR] No se pudo parsear pod name de {replica_url}: {e}")
    return None


async def _restart_pod(pod_name: str) -> None:
    """Reinicia un pod mediante la API de Kubernetes."""
    if not K8S_AVAILABLE:
        print(f"[ALERTA] Kubernetes client no disponible. Saltando restart de {pod_name}")
        return
    
    try:
        namespace = "arquisoft-local"
        print(f"[RESTART] Iniciando reemplazo del pod: {pod_name} en namespace {namespace}")
        
        v1 = client.CoreV1Api()
        v1.delete_namespaced_pod(
            name=pod_name,
            namespace=namespace,
            grace_period_seconds=30,
        )
        
        print(f"[RESTART] Pod {pod_name} ha sido marcado para eliminacion (reinicio)")
        print(f"[RESTART] El StatefulSet lo reenspawnará automáticamente")
    except client.exceptions.ApiException as e:
        if e.status == 404:
            print(f"[ALERTA] Pod {pod_name} no encontrado. Puede ya haber sido eliminado")
        else:
            print(f"[ERROR RESTART] Error de API al eliminar pod {pod_name}: {e}")
    except Exception as e:
        print(f"[ERROR] Exception durante restart de {pod_name}: {e}")
