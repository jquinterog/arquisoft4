import asyncio
import json
import logging
import os
from typing import Any

from aiokafka import AIOKafkaConsumer

from app.excel_writer import append_event, ensure_workbook


logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-service:9092")
KAFKA_TOPIC_PROMOCIONES_CREADAS = os.getenv(
    "KAFKA_TOPIC_PROMOCIONES_CREADAS", "promociones.creadas"
)
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "adaptador-excel")


class PromotionConsumer:
    def __init__(self) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        ensure_workbook()
        self._consumer = AIOKafkaConsumer(
            KAFKA_TOPIC_PROMOCIONES_CREADAS,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=KAFKA_CONSUMER_GROUP,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
            enable_auto_commit=False,
        )
        await self._consumer.start()
        self._running = True
        self._task = asyncio.create_task(self._consume())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
        if self._consumer:
            await self._consumer.stop()

    async def _consume(self) -> None:
        if not self._consumer:
            return
        try:
            async for message in self._consumer:
                try:
                    await self.handle_event(message.value)
                    await self._consumer.commit()
                except Exception:
                    logger.exception("promotion_event_processing_failed")
                if not self._running:
                    break
        except asyncio.CancelledError:
            return

    async def handle_event(self, event: dict[str, Any]) -> None:
        info = await asyncio.to_thread(append_event, event)
        logger.info(
            "promotion_event_consumed event_id=%s event_type=%s source=%s excel_path=%s excel_data_rows=%s",
            event.get("event_id"),
            event.get("event_type"),
            event.get("source"),
            info["path"],
            info["data_rows"],
        )


consumer = PromotionConsumer()
