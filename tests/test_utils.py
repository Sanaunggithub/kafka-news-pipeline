import pytest
from datetime import datetime

from shared.utils import retry, truncate, utcnow


def test_utcnow_returns_datetime():
    now = utcnow()
    assert isinstance(now, datetime)


def test_utcnow_is_utc():
    now = utcnow()
    assert now.tzinfo is not None


def test_truncate_short_text():
    text = "short"
    assert truncate(text, 10) == text


def test_truncate_long_text():
    text = "Hello world!"
    assert truncate(text, 10) == "Hello w..."


def test_truncate_exact_length():
    text = "1234567890"
    assert truncate(text, 10) == text


def test_truncate_custom_length():
    text = "123456789012345678901"
    assert truncate(text, 20) == "12345678901234567..."


@pytest.mark.asyncio
async def test_retry_success():
    async def succeed():
        return "ok"

    assert await retry(succeed) == "ok"


@pytest.mark.asyncio
async def test_retry_fails_then_succeeds():
    attempts = 0

    async def flaky():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("temporary failure")
        return "done"

    result = await retry(flaky, retries=3)

    assert result == "done"
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_all_fail():
    attempts = 0

    async def always_fail():
        nonlocal attempts
        attempts += 1
        raise ValueError("always failing")

    with pytest.raises(ValueError):
        await retry(always_fail, retries=2)

    assert attempts == 2