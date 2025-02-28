import asyncio
from itertools import count

import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from intellide.config import DATABASE_ADMIN_URL, DATABASE_NAME
from intellide.database.startup import startup as database_startup
from intellide.main import app as application
from intellide.storage.startup import startup as storage_startup


@pytest.fixture(scope="session", autouse=True)
def startup():
    async def drop_database_tables():
        # 连接目标数据库
        async_engine = create_async_engine(DATABASE_ADMIN_URL, echo=True, future=True)
        async with async_engine.connect() as conn:
            conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
            # 确保数据库存在才执行删除操作
            await conn.execute(text(f"DROP DATABASE IF EXISTS {DATABASE_NAME}"))

    async def _init():
        await drop_database_tables()
        await database_startup()
        await storage_startup()

    asyncio.run(_init())


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def app():
    async with LifespanManager(application) as manager:
        yield manager.app


@pytest.fixture(scope="session")
async def client(app):
    async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test",
    ) as client:
        yield client


@pytest.fixture(scope="session")
def counter():
    return count(start=1000)


@pytest.fixture(scope="session")
def f4uint(counter):
    counter = count(start=1000)
    return lambda: next(counter)


@pytest.fixture(scope="session")
def f4ustr(counter):
    counter = count(start=1000)
    return lambda: f"test_{hex(next(counter))}"
