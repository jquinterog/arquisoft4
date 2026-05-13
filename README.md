# Proyecto Arquisoft

Local Kubernetes application for Minikube using Python services, MongoDB, and Kafka.

## Services

- `api-gateway`: public HTTP entry point.
- `motor-nba-nbo`: basic NBA/NBO decision service.
- `gestor-promociones`: promotion CRUD service, MongoDB persistence, Kafka event publisher.
- `adaptador-excel`: Kafka consumer that currently logs promotion-created events.

## Local Deployment

Start Minikube and point Docker to the Minikube daemon:

```bash
minikube start
eval $(minikube docker-env)
```

Build local images:

```bash
./scripts/build-images.sh
```

Deploy infrastructure and services:

```bash
./scripts/deploy-local.sh
```

Expose the API Gateway:

```bash
./scripts/port-forward.sh
```

Then call:

```bash
curl http://localhost:8000/health
```

Create a promotion:

```bash
curl -X POST http://localhost:8000/promociones \
  -H "Content-Type: application/json" \
  -d '{"name":"Promo ejemplo","segment":"general","channel":"web","priority":10}'
```
