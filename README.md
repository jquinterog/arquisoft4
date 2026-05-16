# Proyecto Arquisoft

Aplicacion local para Minikube con servicios Python, Kafka y componentes de negocio separados.

## Componentes

- `api-gateway`: punto de entrada HTTP.
- `motor-nba-nbo`: servicio basico de decision NBA/NBO.
- `componente-promociones`: componente autocontenido para gestion de campanas/promociones con FastAPI, PostgreSQL y Alembic.
- `adaptador-excel`: consumidor Kafka que por ahora registra eventos.

## Componente de promociones

El componente de promociones tiene su propio Dockerfile, dependencias, migraciones, configuracion local y README:

```bash
cd componente-promociones
```

Ver [componente-promociones/README.md](componente-promociones/README.md) para ejecutarlo localmente con Python o Docker Compose.

## Minikube

La integracion completa con Kubernetes se mantiene en `k8s/` y se ajustara despues para usar el componente autocontenido de promociones.

Flujo local actual:

```bash
minikube start
eval $(minikube docker-env)
./scripts/build-images.sh
./scripts/deploy-local.sh
./scripts/port-forward.sh
```
