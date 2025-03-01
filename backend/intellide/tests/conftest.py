import os
import socket
import subprocess
from itertools import count

import pytest
import urllib3
from sqlalchemy import create_engine, text

from intellide.config import DATABASE_ENGINE, DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT, \
    DATABASE_NAME, SERVER_HOST, SERVER_PORT

WORK_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..")

LOG_DIRECTORY = os.path.join(WORK_DIRECTORY, "logs")

DATABASE_TEST_BASE_URL = f"{DATABASE_ENGINE}+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}"
DATABASE_TEST_ADMIN_URL = f"{DATABASE_ENGINE}+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/postgres"
DATABASE_TEST_URL = f"{DATABASE_ENGINE}+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

SERVER_BASE_URL = f"http://{SERVER_HOST if SERVER_HOST != '0.0.0.0' else 'localhost'}:{SERVER_PORT}"


@pytest.fixture(scope="session", autouse=True)
def net():
    def allowed_gai_family():
        return socket.AF_INET

    urllib3.util.connection.allowed_gai_family = allowed_gai_family


# 清理数据库
@pytest.fixture(scope="session", autouse=True)
def clean():
    """测试前后清理数据库"""
    engine = create_engine(DATABASE_TEST_ADMIN_URL, isolation_level="AUTOCOMMIT")

    def drop():
        try:
            with engine.connect() as conn:
                # 终止所有连接
                conn.execute(
                    text(
                        """
                            SELECT pg_terminate_backend(pg_stat_activity.pid)
                            FROM pg_stat_activity
                            WHERE datname = :dbname AND pid <> pg_backend_pid();
                        """
                    ),
                    {"dbname": DATABASE_NAME},
                )
                # 删除数据库
                conn.execute(text(f"DROP DATABASE IF EXISTS {DATABASE_NAME}"))
        except Exception:
            import traceback

            traceback.print_exc()

    # **测试前清理**
    drop()
    yield  # 允许后续 fixture 执行


# 启动测试服务器
@pytest.fixture(scope="session", autouse=True)
def server(clean):
    """启动 FastAPI 服务器，并在测试结束后关闭。"""
    os.makedirs(LOG_DIRECTORY, exist_ok=True)
    # 日志文件
    with open(os.path.join(LOG_DIRECTORY, "test.log"), "w") as log:
        # 启动服务器
        process = subprocess.Popen(
            args=[
                "uvicorn",
                "intellide.main:app",
                "--host",
                SERVER_HOST,
                "--port",
                f"{SERVER_PORT}",
                "--log-level",
                "trace"
            ],
            cwd=WORK_DIRECTORY,
            stdout=log,
            stderr=log,
        )
        # 返回进程对象，方便测试用例使用
        yield process
        # **关闭服务器**
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


@pytest.fixture(scope="session")
def unique_counter():
    return count(start=1000)


@pytest.fixture(scope="session")
def unique_string_generator(unique_counter):
    unique_counter = count(start=1000)
    return lambda: f"str_{hex(next(unique_counter))}"


@pytest.fixture(scope="session")
def unique_integer_generator(unique_counter):
    unique_counter = count(start=1000)
    return lambda: next(unique_counter)
