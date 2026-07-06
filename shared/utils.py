import asyncio
from datetime import datetime, timezone
from shared.logger import get_logger

logger = get_logger("Utils")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def retry(func, retries: int = 3, delay: float = 2.0):
    last_exception = None
    for attempt in range(1, retries + 1):
        try:
            return await func()
        except Exception as exc:
            last_exception = exc
            if attempt >= retries:
                logger.warning("Retry %d/%d failed; no more retries", attempt, retries)
                break
            logger.warning(
                "Attempt %d/%d failed, retrying in %.1f seconds: %s",
                attempt,
                retries,
                delay,
                exc,
            )
            await asyncio.sleep(delay)
    raise last_exception


def truncate(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."