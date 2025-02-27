from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from intellide.config import DATABASE_URL

# 连接目标数据库
async_engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# 创建数据库会话生成器
async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore


async def database():
    """
    数据库会话生成器

    返回:
    - 数据库会话对象
    """
    async with async_session() as db:
        yield db
