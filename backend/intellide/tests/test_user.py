import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.future import select

from intellide.database.engine import async_session
from intellide.database.model import User
from intellide.tests.conftest import assert_json_response_code
from intellide.utils.encrypt import jwt_verify


async def get_user_by_username(
    username: str,
) -> User:
    async with async_session() as db:
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalar()


async def assert_token(token: str, username: str):
    user_id = jwt_verify(token)["user_id"]
    user = await get_user_by_username(username)
    assert user_id == user.id


@pytest.mark.anyio
@pytest.mark.dependency()
async def test_user_register_success(client: AsyncClient):
    response = await client.post(
        url="/api/user/register",
        json={
            "username": "test",
            "password": "test",
            "role": "student",
        },
    )
    response = response.json()
    assert_json_response_code(response, status.HTTP_200_OK)
    await assert_token(response["data"], "test")


@pytest.mark.anyio
@pytest.mark.dependency(depends=["test_user_register_success"])
async def test_user_register_failure_duplicate_username(client: AsyncClient):
    response = await client.post(
        url="/api/user/register",
        json={
            "username": "test",
            "password": "test",
            "role": "student",
        },
    )
    response = response.json()
    assert_json_response_code(response, status.HTTP_400_BAD_REQUEST)


@pytest.mark.anyio
@pytest.mark.dependency(depends=["test_user_register_success"])
async def test_user_login_success(client: AsyncClient):
    response = await client.post(
        url="/api/user/login",
        json={
            "username": "test",
            "password": "test",
        },
    )
    response = response.json()
    assert_json_response_code(response, status.HTTP_200_OK)
    await assert_token(response["data"], "test")


@pytest.mark.anyio
@pytest.mark.dependency(depends=["test_user_register_success"])
async def test_user_login_failure_username_not_exist(client: AsyncClient):
    response = await client.post(
        url="/api/user/login",
        json={
            "username": "test0",
            "password": "test",
        },
    )
    response = response.json()
    assert_json_response_code(response, status.HTTP_400_BAD_REQUEST)


@pytest.mark.anyio
@pytest.mark.dependency(depends=["test_user_register_success"])
async def test_user_login_failure_password_incorrect(client: AsyncClient):
    response = await client.post(
        url="/api/user/login",
        json={
            "username": "test",
            "password": "test0",
        },
    )
    response = response.json()
    assert_json_response_code(response, status.HTTP_400_BAD_REQUEST)


@pytest.mark.anyio
@pytest.mark.dependency(depends=["test_user_register_success"])
async def test_user_update_success(client: AsyncClient):
    response = await client.post(
        url="/api/user/register",
        json={
            "username": "update",
            "password": "update",
            "role": "student",
        },
    )
    response = response.json()
    token = response["data"]
    response = await client.put(
        url="/api/user",
        json={
            "username": "update1",
            "password": "update2",
            "role": "teacher",
        },
        headers={
            "Access-Token": token,
        },
    )
    response = response.json()
    assert_json_response_code(response, status.HTTP_200_OK)


@pytest.mark.anyio
@pytest.mark.dependency(depends=["test_user_register_success"])
async def test_user_update_failure_username_duplicated(client: AsyncClient):
    response = await client.post(
        url="/api/user/register",
        json={
            "username": "update",
            "password": "update",
            "role": "student",
        },
    )
    response = response.json()
    token = response["data"]
    response = await client.put(
        url="/api/user",
        json={
            "username": "test",
        },
        headers={
            "Access-Token": token,
        },
    )
    response = response.json()
    assert_json_response_code(response, status.HTTP_400_BAD_REQUEST)


