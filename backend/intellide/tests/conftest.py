import asyncio

import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from intellide.config import DATABASE_ADMIN_URL, DATABASE_NAME
from intellide.database.startup import startup as database_startup
from intellide.main import app
from intellide.storage.startup import startup as storage_startup


async def database_clean():
    # 连接目标数据库
    async_engine = create_async_engine(DATABASE_ADMIN_URL, echo=True, future=True)
    async with async_engine.connect() as conn:
        conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        # 确保数据库存在才执行删除操作
        await conn.execute(text(f"DROP DATABASE IF EXISTS {DATABASE_NAME}"))


@pytest.fixture(scope="session", autouse=True)
def init():
    async def _init():
        await database_clean()
        await database_startup()
        await storage_startup()

    asyncio.run(_init())


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


@pytest.fixture(scope='session')
async def application():
    async with LifespanManager(app) as manager:
        yield manager.app


@pytest.fixture(scope='session')
async def client(application):
    async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test",
    ) as client:
        yield client


def assert_json_response_code(
        response: dict,
        code: int,
):
    assert response['code'] == code
