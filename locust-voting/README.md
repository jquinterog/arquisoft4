# Locust Voting Load Test

Proyecto para ejecutar pruebas de carga contra `POST /nba-nbo/evaluate` del `api-gateway`.

## Requisitos

- Python 3.11+
- Endpoint accesible del API Gateway (por ejemplo `http://127.0.0.1:8000`)

## Instalacion

```bash
cd locust-voting
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecucion (UI web de Locust)

```bash
locust -f locustfile.py --host http://127.0.0.1:8000
```

Abrir `http://127.0.0.1:8089` para configurar usuarios, tasa de spawn y tiempo de ejecucion.

## Variables opcionales

- `LOCUST_EVALUATE_PATH`: path del endpoint a probar (default `/nba-nbo/evaluate`)
- `LOCUST_SEGMENTS`: segmentos separados por coma (default `general,premium,frecuente`)
- `LOCUST_CHANNELS`: canales separados por coma (default `WEB,APP,CALL_CENTER`)

## Docker

```bash
docker build -t locust-voting:local .
docker run --rm -it -p 8089:8089 locust-voting:local \
  -f /app/locustfile.py --host http://host.docker.internal:8000
```
