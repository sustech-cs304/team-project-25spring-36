import time

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container

from intellide.config import (
    DOCKER_URL,
    DOCKER_CONTAINER_POSTGRESQL_NAME,
    DOCKER_CONTAINER_REDIS_NAME,
    DOCKER_ENABLE,
    DATABASE_PORT,
    CACHE_PORT,
)


async def startup():
    def wait(container: Container):
        while container.status != "running":
            time.sleep(0.5)
            container.reload()

    if not DOCKER_ENABLE:
        return

    try:
        # 连接 Docker 服务
        client = docker.DockerClient(base_url=DOCKER_URL)
        # 拉取 Redis 和 PostgreSQL 镜像
        try:
            client.images.get("postgres:latest")
        except docker.errors.ImageNotFound:
            client.images.pull("postgres:latest")
        try:
            client.images.get("redis:latest")
        except docker.errors.ImageNotFound:
            client.images.pull("redis:latest")
        # 启动 PostgreSQL 容器
        try:
            postgres = client.containers.get(DOCKER_CONTAINER_POSTGRESQL_NAME)
            if postgres.status != "running":
                postgres.start()
        except NotFound:
            postgres = None
        if postgres is None:
            postgres = client.containers.run(
                "postgres:latest",
                name="software-engineering-project-postgres",
                environment={
                    "POSTGRES_USER": "postgres",
                    "POSTGRES_PASSWORD": "123456",
                },
                ports={"5432/tcp": DATABASE_PORT},
                detach=True,
            )
        wait(postgres)
        # 启动 Redis 容器
        try:
            redis = client.containers.get(DOCKER_CONTAINER_REDIS_NAME)
            if redis.status != "running":
                redis.start()
        except NotFound:
            redis = None
        if redis is None:
            redis = client.containers.run(
                "redis:latest",
                name="software-engineering-project-redis",
                command="redis-server --requirepass 123456",
                ports={"6379/tcp": CACHE_PORT},
                detach=True,
            )
        wait(redis)
    except DockerException as e:
        print(f"Error occurred while starting containers: {e}")
