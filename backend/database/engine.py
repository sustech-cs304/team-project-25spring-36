from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.config import DATABASE_ADMIN_URL, DATABASE_URL, DATABASE_NAME

# 创建数据库
try:
    with create_engine(DATABASE_ADMIN_URL, isolation_level="AUTOCOMMIT").connect() as conn:
        conn.execute(text(f"CREATE DATABASE {DATABASE_NAME}"))
except:
    # 如果数据库已存在，则忽略错误
    pass

# 连接目标数据库
engine = create_engine(DATABASE_URL, echo=True)

# 创建 pg_trgm 扩展
try:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        conn.commit()
except:
    pass
# 创建数据库会话生成器
session = sessionmaker(bind=engine)


def database():
    """
    数据库会话生成器

    返回:
    - 数据库会话对象
    """
    db = session()
    try:
        yield db
    finally:
        db.close()
