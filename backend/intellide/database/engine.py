import asyncio
from typing import List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker

from intellide.config import DATABASE_ADMIN_URL, DATABASE_URL, DATABASE_NAME
from intellide.database.model import SQLAlchemyBaseModel

# 连接目标数据库
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# 创建数据库会话生成器
session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore


async def database():
    """
    数据库会话生成器

    返回:
    - 数据库会话对象
    """
    async with session() as db:
        yield db


async def _create_pg_database(
        async_engine: AsyncEngine,
        database_name: str,
):
    """
    创建 PostgreSQL 数据库

    参数:
    - engine: AsyncEngine 对象
    - database_name: 要创建的数据库名称
    """
    try:
        async with async_engine.connect() as conn:
            # 设置隔离级别为 AUTOCOMMIT
            conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
            # 创建数据库
            await conn.execute(text(f"CREATE DATABASE {database_name}"))
    except:
        pass


async def _create_pg_extensions(
        async_engine: AsyncEngine,
        extensions: List[str],
):
    """
    创建 PostgreSQL 数据库扩展

    参数:
    - engine: AsyncEngine 对象
    - extensions: 要创建的扩展列表
    """
    try:
        async with async_engine.connect() as conn:
            # 创建数据库扩展
            for extension in extensions:
                await conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {extension}"))
            await conn.commit()
    except:
        pass


async def _create_pg_tables(
        async_engine: AsyncEngine,
):
    """
    创建 PostgreSQL 数据库表格

    参数:
    - engine: AsyncEngine 对象
    """
    async with async_engine.connect() as conn:
        # 创建所有表格
        await conn.run_sync(SQLAlchemyBaseModel.metadata.create_all)
        await conn.commit()


# 初始化数据库
async def _startup():
    """
    初始化数据库，包括创建数据库、扩展和表格
    """
    await _create_pg_database(
        async_engine=create_async_engine(DATABASE_ADMIN_URL, future=True),
        database_name=DATABASE_NAME,
    )
    await _create_pg_extensions(
        async_engine=engine,
        extensions=["pg_trgm"],
    )
    await _create_pg_tables(
        async_engine=engine,
    )


# 启动数据库初始化任务
asyncio.create_task(_startup())
