import json
import logging
import os
from typing import Any

from aiokafka import AIOKafkaProducer


logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-service:9092")
KAFKA_TOPIC_PROMOCIONES_CREADAS = os.getenv(
    "KAFKA_TOPIC_PROMOCIONES_CREADAS", "promociones.creadas"
)


class KafkaPublisher:
    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()

    async def publish_promotion_created(self, event: dict[str, Any]) -> None:
        if not self._producer:
            raise RuntimeError("Kafka producer is not started")
        await self._producer.send_and_wait(KAFKA_TOPIC_PROMOCIONES_CREADAS, event)
        logger.info(
            "promotion_created_event_published",
            extra={"event_id": event.get("event_id"), "topic": KAFKA_TOPIC_PROMOCIONES_CREADAS},
        )


publisher = KafkaPublisher()
