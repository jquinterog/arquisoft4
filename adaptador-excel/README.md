# Adaptador Excel

Consume eventos `promotion_created` desde Kafka y los registra en un archivo Excel.

## Flujo

1. Lee eventos desde el topico `promociones.creadas`.
2. Extrae el `payload` del evento.
3. Agrega una fila al archivo Excel configurado.

## Archivo de salida

Por defecto, en ejecucion local usa:

```text
data/promociones.xlsx
```

En Kubernetes usa:

```text
/data/promociones.xlsx
```

Ese directorio se monta con un `PersistentVolumeClaim` para que el archivo sobreviva reinicios del pod.

Para copiarlo desde Minikube:

```bash
kubectl cp -n arquisoft-local deploy/adaptador-excel:/data/promociones.xlsx ./promociones.xlsx
```

Tambien puedes consultar el estado del archivo haciendo port-forward al servicio:

```bash
kubectl port-forward -n arquisoft-local service/adaptador-excel 8001:8000
curl http://localhost:8001/excel/status
```

Y descargar el archivo generado por el pod:

```bash
curl -L http://localhost:8001/excel/download -o promociones.xlsx
```

## Variables

```text
KAFKA_BOOTSTRAP_SERVERS=kafka-service:9092
KAFKA_TOPIC_PROMOCIONES_CREADAS=promociones.creadas
KAFKA_CONSUMER_GROUP=adaptador-excel
EXCEL_FILE_PATH=/data/promociones.xlsx
```
