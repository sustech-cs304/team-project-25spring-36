from typing import Dict, List, Any, Callable

import pytest
from fastapi import status
from httpx import AsyncClient, Response
from sqlalchemy.future import select

from intellide.database.engine import async_session
from intellide.database.model import User
from intellide.utils.encrypt import jwt_decode


# 统一数据库查询逻辑
async def get_user(
        field: str,
        value: Any,
) -> User:
    async with async_session() as db:
        query = select(User)
        if field == "id":
            query = query.filter(User.id == value)
        elif field == "username":
            query = query.filter(User.username == value)
        else:
            raise ValueError("field not supported")
        result = await db.execute(query)
        return result.scalar()


# 统一 Token 解析和校验
async def assert_token_valid(
        token: str,
        field: str,
        value: Any,
):
    user_id = jwt_decode(token)["user_id"]
    user = await get_user(field, value)
    assert user_id == user.id


# 统一断言 HTTP 响应码
def assert_response_code(
        response: Response,
        expected_code: int,
):
    assert response.json()["code"] == expected_code


def assert_dict(
        src: Dict,
        dst: Dict,
        keys: List[str],
):
    for key in keys:
        assert src[key] == dst[key]


# 预定义测试用户数据
@pytest.fixture(scope="session")
def user_data(
        f4ustr: Callable,
) -> Dict:
    return {
        "username": f4ustr(),
        "password": f4ustr(),
        "role": "student",
    }


@pytest.mark.anyio
@pytest.mark.dependency()
async def test_user_register_success(
        client: AsyncClient,
        user_data: Dict,
):
    response = await client.post(
        url="/api/user/register",
        json=user_data,
    )
    assert_response_code(response, status.HTTP_200_OK)
    await assert_token_valid(response.json()["data"], "username", user_data["username"])


@pytest.mark.anyio
@pytest.mark.dependency(depends=["test_user_register_success"])
async def test_user_register_failure_username_duplicated(
        client: AsyncClient,
        user_data: Dict,
):
    response = await client.post(
        url="/api/user/register",
        json=user_data,
    )
    assert_response_code(response, status.HTTP_400_BAD_REQUEST)


@pytest.mark.anyio
@pytest.mark.dependency(depends=["test_user_register_success"])
async def test_user_login_success(
        client: AsyncClient,
        user_data: Dict,
):
    response = await client.post(
        url="/api/user/login",
        json={
            "username": user_data["username"],
            "password": user_data["password"],
        },
    )
    print(response.json())
    assert_response_code(response, status.HTTP_200_OK)
    await assert_token_valid(response.json()["data"], "username", user_data["username"])


@pytest.mark.anyio
@pytest.mark.dependency(depends=["test_user_register_success"])
async def test_user_login_failure_username_incorrect(
        client: AsyncClient,
        user_data: Dict,
        f4ustr: Callable,
):
    response = await client.post(
        url="/api/user/login",
        json={
            "username": f4ustr(),
            "password": user_data["password"],
        },
    )
    assert_response_code(response, status.HTTP_400_BAD_REQUEST)


@pytest.mark.anyio
@pytest.mark.dependency(depends=["test_user_register_success"])
async def test_user_login_failure_password_incorrect(
        client: AsyncClient,
        user_data: Dict,
        f4ustr: Callable,
):
    response = await client.post(
        url="/api/user/login",
        json={
            "username": user_data["username"],
            "password": f4ustr(),
        },
    )
    assert_response_code(response, status.HTTP_400_BAD_REQUEST)


@pytest.mark.anyio
@pytest.mark.dependency(depends=["test_user_register_success"])
async def test_user_update_success(
        client: AsyncClient,
        f4ustr: Callable,
):
    # 先注册新用户
    user = {
        "username": f4ustr(),
        "password": f4ustr(),
        "role": "student",
    }
    response = await client.post(url="/api/user/register", json=user)
    user_token = response.json()["data"]
    # 更新用户信息
    update_user = {
        "username": f4ustr(),
        "password": f4ustr(),
        "role": "teacher",
    }
    response = await client.put(
        url="/api/user",
        json=update_user,
        headers={
            "Access-Token": user_token,
        },
    )
    assert_response_code(response, status.HTTP_200_OK)
    # 获取更新后的用户信息
    response = await client.get(
        url="/api/user",
        headers={
            "Access-Token": user_token,
        },
    )
    user = response.json()["data"]
    assert_dict(user, update_user, ["username", "password", "role"])


@pytest.mark.anyio
@pytest.mark.dependency(depends=["test_user_register_success"])
async def test_user_update_failure_username_duplicated(
        client: AsyncClient,
        user_data: Dict,
        f4ustr: Callable,
):
    # 先注册用户
    user = {
        "username": f4ustr(),
        "password": f4ustr(),
        "role": "student",
    }
    response = await client.post(
        url="/api/user/register",
        json=user,
    )
    user_token = response.json()["data"]
    # 更新用户名为已存在
    update_user = {
        "username": user_data["username"],
    }
    response = await client.put(
        url="/api/user",
        json=update_user,
        headers={
            "Access-Token": user_token,
        },
    )
    assert_response_code(response, status.HTTP_400_BAD_REQUEST)
