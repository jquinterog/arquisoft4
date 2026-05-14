# K8s Minikube Application Plan

## Goal

Build a local Kubernetes application on Minikube using the architecture shown in the provided diagram:

- API Gateway
- Motor NBA/NBO
- Gestor de promociones
- MongoDB database for promotions
- Kafka
- Excel adapter

Each custom component will live in its own folder and will be implemented in Python. Infrastructure components such as MongoDB and Kafka will be deployed through Kubernetes manifests.

## Proposed Repository Structure

```text
proyecto-arquisoft/
├── api-gateway/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes.py
│   │   └── clients.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── motor-nba-nbo/
│   ├── app/
│   │   ├── main.py
│   │   ├── rules.py
│   │   └── schemas.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── gestor-promociones/
│   ├── app/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── kafka.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── adaptador-excel/
│   ├── app/
│   │   ├── main.py
│   │   ├── consumer.py
│   │   └── handlers.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── k8s/
│   ├── namespace.yaml
│   ├── api-gateway/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   ├── motor-nba-nbo/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   ├── gestor-promociones/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── secret.yaml
│   ├── adaptador-excel/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   ├── mongo/
│   │   ├── statefulset.yaml
│   │   ├── service.yaml
│   │   ├── pvc.yaml
│   │   └── secret.yaml
│   └── kafka.yaml
├── scripts/
│   ├── build-images.sh
│   ├── deploy-local.sh
│   └── port-forward.sh
└── K8S_MINIKUBE_PLAN.md
```

## Component Responsibilities

### API Gateway

Python FastAPI service that exposes the public API for local users or test clients.

Responsibilities:

- Receive external HTTP requests.
- Route promotion-related operations to `gestor-promociones`.
- Route rule or decision-related operations to `motor-nba-nbo`.
- Provide a single external entry point through a Kubernetes `Service`, preferably `NodePort` for Minikube.

Expected calls:

- `API Gateway -> Motor NBA/NBO`
- `API Gateway -> Gestor de promociones`

### Motor NBA/NBO

Python FastAPI service containing NBA/NBO decision logic.

Responsibilities:

- Evaluate business rules.
- Return next-best-action or next-best-offer decisions.
- Optionally call `gestor-promociones` to fetch eligible promotions, as shown by the diagram arrow from Motor NBA/NBO to Gestor de promociones.

Expected calls:

- `Motor NBA/NBO -> Gestor de promociones`

### Gestor de promociones

Python FastAPI service that owns promotion business operations.

Responsibilities:

- Create, update, fetch, and validate promotions.
- Persist promotions in MongoDB.
- Publish an event to Kafka when a promotion is created.
- Use structured logs for request handling, persistence operations, and event publication.
- It will not consume Kafka events in the current design.

Expected calls:

- `Gestor de promociones -> MongoDB`
- `Gestor de promociones -> Kafka`

### Adaptador Excel

Python worker service that consumes promotion events from Kafka.

Responsibilities:

- Subscribe to promotion-created events.
- Log consumed events with structured logs.
- Keep the processing handler intentionally minimal for now.
- Leave Excel-specific processing for a later implementation phase.

Expected calls:

- `Kafka -> Adaptador Excel`

Initial behavior:

- Run as a long-running consumer.
- Read events from Kafka.
- Acknowledge/log the event.
- Do nothing else until the Excel behavior is defined later.

### Kafka

Kafka will be the event backbone.

Recommended local approach:

- Use a single plain Kubernetes manifest in `k8s/kafka.yaml`.
- Use a `Service` named `kafka-service`.
- Use a `Deployment` with the official `apache/kafka:latest` image.
- Run Kafka in KRaft mode to avoid ZooKeeper.
- Rely on Kafka's local-development default behavior for topic creation.

Reason for this simplified Kafka manifest:

- It is closer to the classroom/reference example.
- It avoids Helm and extra topic initialization jobs.
- Kubernetes just pulls the Kafka image and runs a single broker.
- This is enough for Minikube development.

Initial topics:

- `promociones.creadas`

### MongoDB

MongoDB stores promotion data.

Recommended local approach:

- Use a Kubernetes `StatefulSet`.
- Use a `PersistentVolumeClaim` backed by Minikube storage.
- Store credentials in Kubernetes `Secret`.

Initial database:

- Database: `promociones`
- Collection: `promociones`

## Suggested Python Stack

Use a consistent Python stack across services:

```text
fastapi
uvicorn[standard]
pydantic
httpx
python-dotenv
```

Additional dependencies by component:

```text
gestor-promociones:
  pymongo
  aiokafka

adaptador-excel:
  aiokafka

tests:
  pytest
  pytest-asyncio
```

## Kubernetes Deployment Strategy

### Namespace

Create one namespace for the whole application:

```text
arquisoft-local
```

### Services

Use internal `ClusterIP` services for service-to-service communication:

```text
api-gateway.arquisoft-local.svc.cluster.local
motor-nba-nbo.arquisoft-local.svc.cluster.local
gestor-promociones.arquisoft-local.svc.cluster.local
mongo.arquisoft-local.svc.cluster.local
kafka-service.arquisoft-local.svc.cluster.local
adaptador-excel.arquisoft-local.svc.cluster.local
```

Expose only the API Gateway externally:

- `NodePort` for a simple Minikube setup, or
- `Ingress` if Minikube ingress is enabled.

### Configuration

Use `ConfigMap` for non-secret settings:

- Service URLs
- Kafka bootstrap servers
- Kafka topic names
- Mongo database and collection names

Use `Secret` for sensitive settings:

- Mongo username
- Mongo password
- Any future API keys

### Images

Build images directly into the Minikube Docker environment:

```bash
eval $(minikube docker-env)
docker build -t arquisoft/api-gateway:local ./api-gateway
docker build -t arquisoft/motor-nba-nbo:local ./motor-nba-nbo
docker build -t arquisoft/gestor-promociones:local ./gestor-promociones
docker build -t arquisoft/adaptador-excel:local ./adaptador-excel
```

Kubernetes deployments should use:

```yaml
imagePullPolicy: Never
```

This avoids needing a remote image registry for local Minikube development.

## Deployment Flow

1. Start Minikube.

   ```bash
   minikube start
   ```

2. Point Docker to Minikube.

   ```bash
   eval $(minikube docker-env)
   ```

3. Build custom Python service images.

   ```bash
   ./scripts/build-images.sh
   ```

4. Deploy namespace, MongoDB, and Kafka.

   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/mongo/
   kubectl apply -f k8s/kafka.yaml
   kubectl rollout status deployment/kafka -n arquisoft-local --timeout=180s
   ```

5. Deploy custom services.

   ```bash
   kubectl apply -f k8s/gestor-promociones/
   kubectl apply -f k8s/motor-nba-nbo/
   kubectl apply -f k8s/adaptador-excel/
   kubectl apply -f k8s/api-gateway/
   ```

6. Check workloads.

   ```bash
   kubectl get pods -n arquisoft-local
   kubectl get services -n arquisoft-local
   ```

7. Open the API Gateway.

   ```bash
   minikube service api-gateway -n arquisoft-local
   ```

## Initial API Sketch

### API Gateway

```text
GET  /health
GET  /promociones
POST /promociones
POST /nba-nbo/evaluate
```

### Gestor de promociones

```text
GET    /health
GET    /promociones
GET    /promociones/{id}
POST   /promociones
PUT    /promociones/{id}
DELETE /promociones/{id}
```

### Motor NBA/NBO

```text
GET  /health
POST /evaluate
```

### Adaptador Excel

```text
GET  /health
```

The service will primarily run a Kafka consumer. The `/health` endpoint is optional but useful if the service is implemented as a small FastAPI app with a background consumer task.

## Initial Message Contracts

### Promotion Document

```json
{
  "id": "promo-001",
  "name": "Promo ejemplo",
  "description": "Descripcion de la promocion",
  "segment": "premium",
  "channel": "web",
  "priority": 10,
  "active": true,
  "starts_at": "2026-05-01T00:00:00Z",
  "ends_at": "2026-06-01T00:00:00Z"
}
```

### Kafka Event

```json
{
  "event_type": "promotion_created",
  "event_id": "uuid",
  "source": "gestor-promociones",
  "payload": {
    "id": "promo-001",
    "name": "Promo ejemplo",
    "segment": "premium",
    "channel": "web",
    "priority": 10,
    "active": true
  }
}
```

## Implementation Phases

### Phase 1: Local Skeleton

- Create Python FastAPI skeletons for each custom service.
- Add `Dockerfile` and `requirements.txt` per service.
- Add `/health` endpoint for every service.
- Add Kubernetes deployments and services.
- Verify that all pods run in Minikube.

### Phase 2: Core Promotion Flow

- Implement CRUD in `gestor-promociones`.
- Connect `gestor-promociones` to MongoDB.
- Route API Gateway promotion endpoints to `gestor-promociones`.
- Add basic tests around promotion validation and persistence.

### Phase 3: Kafka Integration

- Deploy Kafka.
- Add producer support in `gestor-promociones`.
- Publish `promotion_created` events to `promociones.creadas` when a promotion is created.
- Add consumer support in `adaptador-excel`.
- Have `adaptador-excel` consume and log events without applying business behavior yet.

### Phase 4: NBA/NBO Logic

- Implement first version of rule evaluation.
- Connect API Gateway to `motor-nba-nbo`.
- Connect `motor-nba-nbo` to `gestor-promociones`.
- Add tests for rule decisions.

### Phase 5: Excel Import

- Keep this as a future phase.
- Define what Excel processing should mean after the initial Kafka consumer is working.
- Decide later whether the adapter should generate files, read files, transform data, call another system, or expose an upload API.

## Assumptions

- This is a local development architecture intended to run on Minikube, not a production Kubernetes cluster.
- All custom components should be implemented in Python.
- FastAPI is acceptable for HTTP APIs.
- MongoDB is the source of truth for promotion data.
- Kafka is used for asynchronous promotion-created events.
- The API Gateway is the only service exposed outside the cluster.
- Internal services communicate using Kubernetes DNS and `ClusterIP` services.
- Docker images can be built locally inside the Minikube Docker daemon.
- Secrets for local development can be simple Kubernetes `Secret` manifests, with the understanding that production would need stronger secret management.
- The Excel adapter will initially consume Kafka events and do no business processing.
- The NBA/NBO engine can start with deterministic business rules in Python before introducing a more advanced rules engine or ML model.
- The API Gateway can stay unauthenticated because this is local development only.
- MongoDB will run as a single local instance.
- Spanish names are preferred for folders, APIs, Kubernetes resources, and domain concepts.
- Structured logs are sufficient for initial observability.
- Helper scripts for building images and deploying to Minikube should be included.
- Sample Excel files are not needed yet.
- Folder and Kubernetes resource names will use Spanish where practical. The API Gateway keeps the `api-gateway` name because it is a common platform term and matches the diagram.

## Resolved Questions

1. The Excel adapter will read Kafka events and do nothing else for now.
2. `gestor-promociones` will publish an event to Kafka when a promotion is created.
3. `gestor-promociones` will not consume Kafka events.
4. Promotion fields can be assumed for the first implementation.
5. NBA/NBO decision rules can be assumed for the first implementation.
6. The API Gateway can be open because this is local development.
7. Kafka should use a single simple Kubernetes manifest instead of Helm or a topic initialization job.
8. MongoDB should be a single local instance.
9. Spanish naming is preferred.
10. Structured logs are enough for initial observability.
11. Helper scripts should be included.
12. Sample Excel files should not be included yet.

## Follow-up Questions

1. When a promotion is created, should `gestor-promociones` publish the Kafka event only after MongoDB persistence succeeds? -> yes
2. If Kafka publication fails after the promotion is saved, should the create request fail, or should the API return success and log the event-publish failure? -> return success and log the failure.
3. Should update/delete operations also publish events later, or is the first implementation strictly create-only? -> let's start with create-only for the first implementation.

## Recommended Next Step

Start with Phase 1 and Phase 2:

1. Scaffold the four Python services.
2. Add Dockerfiles.
3. Add basic Kubernetes manifests.
4. Deploy MongoDB.
5. Implement promotion CRUD through API Gateway and Gestor de promociones.

This creates a working vertical slice before adding the Kafka consumer behavior in `adaptador-excel`.
