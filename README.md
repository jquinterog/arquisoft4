# TeknoShop Campaign Service (MVP)

Microservicio backend para gestionar campanas comerciales NBO/NBA en arquitectura omnicanal.

## Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- Alembic
- Pytest

## Estructura

app/
  main.py
  database.py
  models/
    campaign.py
  schemas/
    campaign.py
  repositories/
    campaign_repository.py
  services/
    campaign_service.py
  routers/
    campaign_router.py
  enums/
    campaign_enums.py
  exceptions/
    campaign_exceptions.py

tests/
  conftest.py
  test_campaign_service.py
  test_campaign_router.py

## Requisitos

- Python 3.11+
- PostgreSQL en ejecucion

## Configuracion local

1. Crear base de datos:

```sql
CREATE DATABASE teknoshop_campaigns;
```

2. Configurar variables de entorno:

```bash
cp .env.example .env
```

3. Crear entorno virtual e instalar dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Ejecutar migraciones:

```bash
alembic upgrade head
```

5. Levantar servicio:

```bash
uvicorn app.main:app --reload
```

6. Ejecutar pruebas:

```bash
pytest -q
```

## Ejecutar con contenedores (Docker Compose)

1. Construir imagenes y levantar servicios:

```bash
docker compose up --build -d
```

2. Verificar estado de contenedores:

```bash
docker compose ps
```

3. Ver logs de la API:

```bash
docker compose logs -f api
```

4. Probar health check:

```bash
curl http://127.0.0.1:8000/health
```

5. Ejecutar pruebas dentro del contenedor de API (opcional):

```bash
docker compose exec api pytest -q
```

6. Bajar servicios:

```bash
docker compose down
```

7. Bajar servicios y eliminar volumen de Postgres:

```bash
docker compose down -v
```

Notas:

- La API ejecuta migraciones automaticamente al iniciar (`alembic upgrade head`).
- Dentro de Docker, la API usa `DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/teknoshop_campaigns`.

API docs:

- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Endpoints

- POST /campaigns
- GET /campaigns
- GET /campaigns/{campaign_id}
- PUT /campaigns/{campaign_id}
- PATCH /campaigns/{campaign_id}/activate
- PATCH /campaigns/{campaign_id}/pause
- PATCH /campaigns/{campaign_id}/cancel

## Ejemplos de Request/Response

### Crear campana

Request:

```json
{
  "name": "Oferta iPhone 15 Web",
  "description": "Descuento para clientes premium en canal web",
  "type": "NEXT_BEST_OFFER",
  "channel": "WEB",
  "priority": 1,
  "start_date": "2026-05-20T10:00:00Z",
  "end_date": "2026-06-20T10:00:00Z",
  "action_message": "Aprovecha 15% de descuento en iPhone 15 hoy"
}
```

Response 201 (resumen):

```json
{
  "id": "1c0f6de6-1ce6-4a88-aa1b-80f7f9af95ff",
  "status": "DRAFT"
}
```

### Activar campana

Request: PATCH /campaigns/{campaign_id}/activate

Response 200 (resumen):

```json
{
  "id": "1c0f6de6-1ce6-4a88-aa1b-80f7f9af95ff",
  "status": "ACTIVE"
}
```

### Filtro por estado/canal/tipo

Request: GET /campaigns?status=ACTIVE&channel=WEB&type=NEXT_BEST_OFFER

Response 200:

```json
[
  {
    "id": "1c0f6de6-1ce6-4a88-aa1b-80f7f9af95ff",
    "name": "Oferta iPhone 15 Web",
    "status": "ACTIVE",
    "channel": "WEB",
    "type": "NEXT_BEST_OFFER"
  }
]
```

## Reglas de negocio implementadas

- No se puede activar una campana vencida.
- No se puede activar una campana si start_date >= end_date.
- Una campana cancelada no puede volver a activarse.
- Solo campanas en estado DRAFT o PAUSED pueden activarse.
- Solo campanas ACTIVE pueden pausarse.
- priority >= 1.
- name, action_message, channel y type son obligatorios.
