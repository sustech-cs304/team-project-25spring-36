import psycopg2

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


DB_DRIVER = "postgresql"
DB_USER = "postgres"
DB_PASSWORD = "123456"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "ide"

DB_CONNECTION_URL = f"{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
DB_ADMIN_URL = f"{DB_CONNECTION_URL}/postgres"
DB_DATABASE_URL = f"{DB_CONNECTION_URL}/{DB_NAME}"

# 创建数据库
try:
    with create_engine(DB_ADMIN_URL, isolation_level="AUTOCOMMIT").connect() as conn:
        conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
except psycopg2.errors.DuplicateDatabase:
    pass
# 连接目标数据库
engine = create_engine(DB_DATABASE_URL, echo=True)
session = sessionmaker(bind=engine)


def database():
    db = session()
    try:
        yield db
    finally:
        db.close()
