import os.path
import random
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


def user_select_success(
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
        return {
            "username": unique_string_generator(),
            "password": unique_string_generator(),
            "role": random.choice([str(v) for v in UserRole]),
        }

    return _unique_user_generator


# 预定义测试用户数据
@pytest.fixture(scope="session")
def default_user_dict_sender(
        unique_user_dict_generator: Callable
) -> Dict:
    return unique_user_dict_generator()

# 预定义测试用户数据
@pytest.fixture(scope="session")
def default_user_dict_receiver(
        unique_user_dict_generator: Callable
) -> Dict:
    return unique_user_dict_generator()


@pytest.mark.dependency
def test_user_register_success(
        default_user_dict_sender: Dict,
        default_user_dict_receiver: Dict,
):
    user_register_success(default_user_dict_sender)
    user_register_success(default_user_dict_receiver)


@pytest.mark.dependency(depends=["test_user_register_success"])
def test_user_upload_success(
        default_user_dict_sender: Dict,
        default_user_dict_receiver: Dict,
):
    sender_token = user_login_success(default_user_dict_sender)
    receiver_token = user_login_success(default_user_dict_receiver)
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/entry",
        headers={
            "Access-Token": sender_token,
        },
        data={
            "entry_path": "/aa/bb/file.txt",  # 文件路径
            "entry_type": "file",  # 条目类型：file或directory
            "is_collaborative": "false"  # 布尔值需要转为字符串

        },
        files={
            "file": open(os.path.join(os.path.dirname(__file__), "..", "..", "temp", "file.txt"), "rb")
        }
    ).json()
    assert_code(response, status.HTTP_200_OK)



