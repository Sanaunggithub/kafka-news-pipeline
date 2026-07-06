import json

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from shared.config import settings
from shared.logger import get_logger

logger = get_logger("Kafka")


def _value_serializer(value):
    return json.dumps(value).encode("utf-8")


def _value_deserializer(value):
    if value is None:
        return None
    return json.loads(value.decode("utf-8"))


async def get_producer() -> AIOKafkaProducer:
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=_value_serializer,
    )
    await producer.start()
    logger.info("Kafka producer started")
    return producer


async def get_consumer(topic: str, group_id: str) -> AIOKafkaConsumer:
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=group_id,
        auto_offset_reset="earliest",
        value_deserializer=_value_deserializer,
    )
    await consumer.start()
    logger.info("Kafka consumer started for topic %s and group %s", topic, group_id)
    return consumer