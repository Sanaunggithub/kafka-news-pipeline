import json
import ssl
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.helpers import create_ssl_context
from shared.config import settings
from shared.logger import get_logger

logger = get_logger("Kafka")


def _value_serializer(value):
    return json.dumps(value).encode("utf-8")


def _value_deserializer(value):
    if value is None:
        return None
    return json.loads(value.decode("utf-8"))


def _get_ssl_context():
    if settings.KAFKA_SECURITY_PROTOCOL in ("SSL", "SASL_SSL") and settings.KAFKA_SSL_CAFILE:
        context = ssl.create_default_context(cafile=settings.KAFKA_SSL_CAFILE)
        return context
    return None


def _get_sasl_config():
    if settings.KAFKA_SECURITY_PROTOCOL == "SASL_SSL":
        return {
            "sasl_mechanism": settings.KAFKA_SASL_MECHANISM,
            "sasl_plain_username": settings.KAFKA_SASL_USERNAME,
            "sasl_plain_password": settings.KAFKA_SASL_PASSWORD,
        }
    return {}


async def get_producer() -> AIOKafkaProducer:
    ssl_context = _get_ssl_context()
    sasl_config = _get_sasl_config()

    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=_value_serializer,
        security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
        ssl_context=ssl_context,
        **sasl_config,
    )
    await producer.start()
    logger.info("Kafka producer started")
    return producer


async def get_consumer(topic: str, group_id: str) -> AIOKafkaConsumer:
    ssl_context = _get_ssl_context()
    sasl_config = _get_sasl_config()

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=group_id,
        auto_offset_reset="earliest",
        value_deserializer=_value_deserializer,
        security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
        ssl_context=ssl_context,
        session_timeout_ms=30000,
        heartbeat_interval_ms=10000,
        request_timeout_ms=40000,
        connections_max_idle_ms=540000,
        **sasl_config,
    )
    await consumer.start()
    logger.info("Kafka consumer started for topic %s and group %s", topic, group_id)
    return consumer