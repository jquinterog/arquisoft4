import json
import logging
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from aiokafka import AIOKafkaProducer

from componente_promociones.models.campaign import Campaign


logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-service:9092")
KAFKA_TOPIC_PROMOCIONES_CREADAS = os.getenv(
    "KAFKA_TOPIC_PROMOCIONES_CREADAS", "promociones.creadas"
)
KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "true").lower() == "true"


class KafkaPublisher:
    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        if not KAFKA_ENABLED:
            return
        if self._producer:
            return
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
        )
        await producer.start()
        self._producer = producer

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            self._producer = None

    async def publish_campaign_created(self, campaign: Campaign) -> None:
        if not KAFKA_ENABLED:
            logger.info("promotion_created_event_skipped", extra={"reason": "kafka_disabled"})
            return
        await self.start()
        if not self._producer:
            raise RuntimeError("Kafka producer is not available")

        event = {
            "event_type": "promotion_created",
            "event_id": str(uuid4()),
            "source": "componente-promociones",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": campaign_to_event_payload(campaign),
        }
        await self._producer.send_and_wait(KAFKA_TOPIC_PROMOCIONES_CREADAS, event)
        logger.info(
            "promotion_created_event_published",
            extra={"event_id": event["event_id"], "campaign_id": str(campaign.id)},
        )

    async def publish_campaign_created_safely(self, campaign: Campaign) -> None:
        try:
            await self.publish_campaign_created(campaign)
        except Exception as exc:
            logger.error(
                "promotion_created_event_publish_failed",
                extra={"campaign_id": str(campaign.id), "error": str(exc)},
            )


def campaign_to_event_payload(campaign: Campaign) -> dict[str, Any]:
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "description": campaign.description,
        "type": campaign.type.value,
        "status": campaign.status.value,
        "channel": campaign.channel.value,
        "priority": campaign.priority,
        "start_date": campaign.start_date.isoformat(),
        "end_date": campaign.end_date.isoformat(),
        "action_message": campaign.action_message,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
    }


publisher = KafkaPublisher()
