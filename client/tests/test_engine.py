import asyncio

import pytest

from engine import QLPEngine
from exceptions.protocol_exceptions import QLPError


# @pytest.fixture(scope='session', autouse=True)
# def loop():
#     return asyncio.get_event_loop()


@pytest.fixture
async def engine():
    return QLPEngine()


@pytest.mark.asyncio
async def test_singleton(engine):
    another_engine = QLPEngine()
    assert id(engine) == id(another_engine)


@pytest.mark.asyncio
async def test_deny_double_start(engine):
    await engine.start()
    with pytest.raises(QLPError):
        await engine.start()


@pytest.mark.asyncio
async def test_deny_double_stop(engine):
    await engine.start()
    await engine.stop()
    with pytest.raises(QLPError):
        await engine.stop()
