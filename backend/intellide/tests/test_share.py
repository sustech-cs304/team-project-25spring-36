from typing import Callable

import pytest
import requests
from fastapi import status

from intellide.tests.conftest import SERVER_BASE_URL
from intellide.tests.test_user import user_login_success, unique_user_dict_generator
from intellide.tests.utils import *


@pytest.fixture(scope="session")
def user_dict_inviter(
        unique_user_dict_generator: Callable
) -> Dict:
    return unique_user_dict_generator()


@pytest.fixture(scope="session")
def user_dict_receiver(
        unique_user_dict_generator: Callable
) -> Dict:
    return unique_user_dict_generator()


@pytest.mark.dependency(depends=["test_user_register_success"])
def test_create_share_token_success(
        user_dict_inviter: Dict,
        user_dict_receiver: Dict,
):
    inviter_token = user_login_success(user_dict_inviter)
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/share/token/create",
        headers={
            "Access-Token": inviter_token,
        },
        json={
            "entry_path": "/aa/bb/file.txt",  # 文件路径
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
