import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from backend.config import DATABASE_ADMIN_URL, DATABASE_URL, DATABASE_NAME


async def create_pg_database(engine: AsyncEngine, database_name: str):
    try:
        async with engine.connect() as conn:
            # 创建数据库
            await conn.execute(text(f"CREATE DATABASE {database_name}"))
            await conn.commit()
    except:
        pass


async def create_pg_extensions(engine: AsyncEngine, extensions: list[str]):
    try:
        async with engine.connect() as conn:
            for extension in extensions:
                await conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {extension}"))
            await conn.commit()
    except:
        pass


async def database():
    """
    数据库会话生成器

    返回:
    - 数据库会话对象
    """
    async with session() as session:
        yield session


# 连接目标数据库
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# 创建数据库会话生成器
session = sessionmaker(engine, class_=AsyncSession)

# 初始化数据库
asyncio.run(
    create_pg_database(
        engine=create_async_engine(DATABASE_ADMIN_URL, future=True),
        database_name=DATABASE_NAME,
    )
)
asyncio.run(
    create_pg_extensions(
        engine=engine,
        extensions=["pg_trgm"],
    )
)
