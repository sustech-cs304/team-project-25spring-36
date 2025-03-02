from typing import Callable

import pytest
import requests
from fastapi import status

from intellide.tests.conftest import SERVER_BASE_URL
from intellide.tests.test_entry import entry_post, unique_path_generator
from intellide.tests.test_user import user_register_success, unique_user_dict_generator
from intellide.tests.utils import *
from intellide.utils.path import path_first_n


@pytest.fixture(scope="session")
def user_dict_inviter(
        unique_user_dict_generator: Callable
) -> Dict:
    return unique_user_dict_generator()


@pytest.fixture(scope="session")
def user_token_inviter(
        user_dict_inviter: Dict
) -> str:
    return user_register_success(user_dict_inviter)


@pytest.fixture(scope="session")
def user_dict_receiver(
        unique_user_dict_generator: Callable
) -> Dict:
    return unique_user_dict_generator()


@pytest.fixture(scope="session")
def user_token_receiver(
        user_dict_receiver: Dict
) -> str:
    return user_register_success(user_dict_receiver)


@pytest.fixture(scope="session")
def entry_path_inviter(
        user_token_inviter: str,
        unique_path_generator: Callable,
        temp_file_path: str,
) -> str:
    entry_path = unique_path_generator(depth=4, suffix="txt")
    assert_code(
        entry_post(
            user_token_inviter,
            entry_path,
            "file",
            "false",
            temp_file_path
        ),
        status.HTTP_200_OK
    )
    return entry_path


@pytest.fixture(scope="session")
def shared_entry_path_inviter(
        entry_path_inviter: str,
) -> str:
    return path_first_n(entry_path_inviter, 2)


@pytest.fixture(scope="session")
def shared_entry_tokens() -> List:
    return []


@pytest.mark.dependency
def test_share_token_create_success(
        user_token_inviter: str,
        shared_entry_path_inviter: str,
        shared_entry_tokens: List,
):
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/share/token/create",
        headers={
            "Access-Token": user_token_inviter,
        },
        json={
            "entry_path": shared_entry_path_inviter,  # 文件路径
            # TODO: 添加权限
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    shared_entry_tokens.append(response["data"])


@pytest.mark.dependency(depends=["test_share_token_create_success"])
def test_share_token_parse_success(
        user_token_receiver: str,
        shared_entry_tokens: Dict,
):
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/share/token/parse",
        headers={
            "Access-Token": user_token_receiver,
        },
        json={
            "token": shared_entry_tokens[0],  # 文件路径
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)


@pytest.mark.dependency(depends=["test_share_token_parse_success"])
def test_share_list_success(
        user_token_receiver: str,
):
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/share/list",
        headers={
            "Access-Token": user_token_receiver,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    # TODO: 校验返回数据
