import psycopg2

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.config import DATABASE_ADMIN_URL, DATABASE_URL, DATABASE_NAME


# 创建数据库
try:
    with create_engine(DATABASE_ADMIN_URL, isolation_level="AUTOCOMMIT").connect() as conn:
        conn.execute(text(f"CREATE DATABASE {DATABASE_NAME}"))
except psycopg2.errors.DuplicateDatabase:
    pass
# 连接目标数据库
engine = create_engine(DATABASE_URL, echo=True)
session = sessionmaker(bind=engine)


def database():
    db = session()
    try:
        yield db
    finally:
        db.close()
