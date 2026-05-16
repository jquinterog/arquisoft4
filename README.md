# Proyecto Arquisoft

Aplicacion local para Minikube con servicios Python, Kafka y componentes de negocio separados.

## Componentes

- `api-gateway`: punto de entrada HTTP.
- `motor-nba-nbo`: servicio basico de decision NBA/NBO.
- `componente-promociones`: componente autocontenido para gestion de campanas/promociones con FastAPI, PostgreSQL y Alembic.
- `adaptador-excel`: consumidor Kafka que agrega los eventos de promociones creadas a un archivo Excel.

## Componente de promociones

El componente de promociones tiene su propio Dockerfile, dependencias, migraciones, configuracion local y README:

```bash
cd componente-promociones
```

Ver [componente-promociones/README.md](componente-promociones/README.md) para ejecutarlo localmente con Python o Docker Compose.

## Minikube

La integracion de Kubernetes usa `componente-promociones` y PostgreSQL.

Flujo local actual:

```bash
minikube start
eval $(minikube docker-env)
./scripts/build-images.sh
./scripts/deploy-local.sh
./scripts/port-forward.sh
```

Ejemplo para crear una promocion/campana a traves del API Gateway:

```bash
curl -X POST http://localhost:8000/promociones \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Oferta iPhone 15 Web",
    "description": "Descuento para clientes premium en canal web",
    "type": "NEXT_BEST_OFFER",
    "channel": "WEB",
    "priority": 1,
    "start_date": "2026-05-20T10:00:00Z",
    "end_date": "2026-06-20T10:00:00Z",
    "action_message": "Aprovecha 15% de descuento en iPhone 15 hoy"
  }'
```
