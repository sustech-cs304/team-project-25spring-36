import random
import secrets
import string
from typing import Callable

import pytest
import requests
from fastapi import status

from intellide.database.model import UserRole
from intellide.tests.conftest import SERVER_BASE_URL
from intellide.tests.utils import *


def user_register_success(
        user_register_dict: Dict,
) -> str:
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/user/register",
        json=user_register_dict,
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def user_login_success(
        user_login_dict: Dict,
) -> str:
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/user/login",
        json={
            "username": user_login_dict["username"],
            "password": user_login_dict["password"],
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def user_get_success(
        token: str
) -> Dict:
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/user",
        headers={
            "Access-Token": token,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


@pytest.fixture(scope="session")
def unique_user_dict_generator(
        unique_string_generator: Callable,
) -> Callable:
    def _unique_user_generator():
        email = f"{unique_string_generator()}@{unique_string_generator()}.com"
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        cache_set(f"register:code:{email}", code, ttl=300)
        return {
            "username": unique_string_generator(),
            "password": unique_string_generator(),
            "role": random.choice([str(v) for v in UserRole]),
            "email": email,
            "code": code,
        }

    return _unique_user_generator


@pytest.fixture(scope="session", autouse=True)
def init(
        store: Dict,
        unique_user_dict_generator: Callable,
):
    store["user_dict_default"] = unique_user_dict_generator()


@pytest.mark.dependency
def test_user_register_success(
        store: Dict,
):
    user_dict_default = store["user_dict_default"]
    user_register_success(user_dict_default)


@pytest.mark.dependency(depends=["test_user_register_success"])
def test_user_register_failure_username_occupied(
        store: Dict,
):
    user_dict_default = store["user_dict_default"]
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/user/register",
        json=user_dict_default,
    ).json()
    assert_code(response, status.HTTP_400_BAD_REQUEST)


@pytest.mark.dependency(depends=["test_user_register_success"])
def test_user_login_success(
        store: Dict,
):
    user_dict_default = store["user_dict_default"]
    user_login_success(user_dict_default)


@pytest.mark.dependency(depends=["test_user_login_success"])
def test_user_login_failure_username_not_exists(
        store: Dict,
        unique_string_generator: Callable,
):
    user_dict_default = store["user_dict_default"]
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/user/login",
        json={
            "username": unique_string_generator(),
            "password": user_dict_default["password"],
        },
    ).json()
    assert_code(response, status.HTTP_400_BAD_REQUEST)


@pytest.mark.dependency(depends=["test_user_login_success"])
def test_user_login_failure_password_incorrect(
        store: Dict,
        unique_string_generator: Callable,
):
    user_dict_default = store["user_dict_default"]
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/user/login",
        json={
            "username": user_dict_default["username"],
            "password": unique_string_generator(),
        },
    ).json()
    assert_code(response, status.HTTP_400_BAD_REQUEST)


@pytest.mark.dependency(depends=["test_user_login_success"])
def test_user_get_success(
        store: Dict,
):
    user_dict_default = store["user_dict_default"]
    user_token = user_login_success(user_dict_default)
    user_select_dict = user_get_success(user_token)
    assert_dict(user_select_dict, user_dict_default, ("username", "role", "email",))


@pytest.mark.dependency(depends=["test_user_get_success"])
def test_user_get_failure_token_incorrect(
        unique_string_generator: Callable,
):
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/user",
        headers={
            "Access-Token": unique_string_generator(),
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.dependency(depends=["test_user_get_success"])
def test_user_put_success(
        unique_user_dict_generator: Callable,
):
    # 先注册新用户
    new_user_dict = unique_user_dict_generator()
    new_user_token = user_register_success(new_user_dict)
    # 更新用户信息
    update_user_dict = unique_user_dict_generator()
    response = requests.put(
        url=f"{SERVER_BASE_URL}/api/user",
        json={
            "username": update_user_dict["username"],
            "email": update_user_dict["email"],
            "role": update_user_dict["role"]
        },
        headers={
            "Access-Token": new_user_token,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    # 获取更新后的用户信息
    after_update_user_dict = user_get_success(new_user_token)
    assert_dict(after_update_user_dict, update_user_dict, ("username", "role",))


@pytest.mark.dependency(depends=["test_user_get_success"])
def test_user_update_failure_username_occupied(
        store: Dict,
        unique_user_dict_generator: Callable,
):
    user_dict_default = store["user_dict_default"]
    # 先注册用户
    new_user_dict = unique_user_dict_generator()
    new_user_token = user_register_success(new_user_dict)
    # 更新用户名为已存在
    update_user_dict = {
        "username": user_dict_default["username"],
    }
    response = requests.put(
        url=f"{SERVER_BASE_URL}/api/user",
        json=update_user_dict,
        headers={
            "Access-Token": new_user_token,
        },
    ).json()
    assert_code(response, status.HTTP_400_BAD_REQUEST)
