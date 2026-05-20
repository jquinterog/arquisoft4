# Proyecto Arquisoft

Aplicacion local para Minikube con servicios Python, Kafka y componentes de negocio separados.

## Componentes

- `api-gateway`: punto de entrada HTTP.
- `voting`: componente de votacion que consulta 3 replicas de `motor-nba-nbo` y detecta discrepancias.
- `motor-nba-nbo`: servicio basico de decision NBA/NBO.
- `locust-voting`: pruebas de carga para `POST /nba-nbo/evaluate` via Locust.
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

## Consultar la base de datos

Ver las ultimas campanas:

```bash
./scripts/query-db.sh
```

Ejecutar una consulta especifica:

```bash
./scripts/query-db.sh "select count(*) from campaigns;"
```

Abrir una consola `psql` interactiva:

```bash
kubectl exec -it -n arquisoft-local deploy/postgres -- psql -U postgres -d teknoshop_campaigns
```

Comandos utiles dentro de `psql`:

```sql
\dt
\d campaigns
select * from campaigns order by created_at desc limit 5;
\q
```

## Voting para NBA/NBO

El flujo de evaluacion `POST /nba-nbo/evaluate` en `api-gateway` enruta al componente `voting`.

`voting` consulta las tres replicas direccionables de `motor-nba-nbo`:

- `motor-nba-nbo-0.motor-nba-nbo:8000`
- `motor-nba-nbo-1.motor-nba-nbo:8000`
- `motor-nba-nbo-2.motor-nba-nbo:8000`

Con esto retorna la respuesta mayoritaria y metadatos `_voting` para saber si hubo unanimidad o discrepancias.

### Prueba de discrepancia via API Gateway y Voting

Esta prueba verifica que `voting` detecta discrepancias cuando una sola replica responde diferente.

1. Exponer una replica especifica (`motor-nba-nbo-0`) en local:

```bash
kubectl port-forward --namespace arquisoft-local pod/motor-nba-nbo-0 8001:8000
```

2. Activar respuesta forzada en esa replica:

```bash
curl -X POST http://127.0.0.1:8001/force-different-response
```

3. Ejecutar la evaluacion desde `api-gateway` (pasa por `voting`):

```bash
curl -X POST http://127.0.0.1:8000/nba-nbo/evaluate \
  -H "Content-Type: application/json" \
  -d '{"cliente_id":"cliente-voting-1","segmento":"general","canal":"WEB"}'
```

4. Validar en la respuesta el objeto `_voting`:

- `replicas_consultadas` debe ser `3`.
- `consistencia` debe ser `true` (hay mayoria de 2/3).
- `unanimidad` debe ser `false`.
- `replicas_con_discrepancia` debe incluir la replica forzada (ejemplo: `motor-nba-nbo-0...`).

5. Ejecutar otra evaluacion con el mismo request. Como el flag era de un solo uso, se deberia volver a ver unanimidad (`unanimidad: true`) salvo que exista otro factor externo.

6. Detener port-forward.

## Monitoreo de replicas defectuosas y recuperacion automatica

El componente `voting` detecta automaticamente cuando una replica produce respuestas discrepantes y la marca como defectuosa. Ademas, inicia automaticamente el reinicio (replacement) de la replica fallida.

### Metricas de deteccion

En cada respuesta de `_voting` se incluyen:

- `detection_time_ms`: tiempo en milisegundos que tardo el voting en detectar la discrepancia.
- `replicas_defectuosas`: lista de URLs de replicas marcadas como defectuosas.
- `replicas_activas`: cantidad de replicas consultadas (excluye las defectuosas).
- `replicas_con_discrepancia`: replicas que votaron diferente en esta evaluacion.

### Flujo de recuperacion

1. Una replica produce respuesta discrepante.
2. `voting` la marca como defectuosa e inicia su restart via API de Kubernetes.
3. El pod es eliminado y el StatefulSet lo reenspawna automaticamente.
4. La replica defectuosa se excluye de futuras evaluaciones.

### Endpoints de administracion (acceso directo a voting)

Ver replicas marcadas como defectuosas:

```bash
curl -X GET http://127.0.0.1:{VOTING_PORT}/defective-replicas
```

Resetear manualmente todas las replicas defectuosas:

```bash
curl -X POST http://127.0.0.1:{VOTING_PORT}/reset-defective-replicas
```

Estos endpoints son utiles para monitoreo y recuperacion manual en caso de ser necesario.

## Pruebas de carga con Locust

Existe un proyecto dedicado para cargar el endpoint `evaluate` que usa la tactica de voting:

```bash
cd locust-voting
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
locust -f locustfile.py --host http://127.0.0.1:8000
```

Abrir `http://127.0.0.1:8089` para iniciar la prueba desde la UI de Locust.
