import os.path
from typing import Callable, Optional

import pytest
import requests
from fastapi import status

from intellide.tests.conftest import SERVER_BASE_URL
from intellide.tests.test_user import user_register_success, unique_user_dict_generator
from intellide.tests.utils import *
from intellide.utils.path import path_iterate_parents


def entry_get_success(
        user_token: str,
        entry_path: str,
) -> List:
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/entry",
        headers={
            "Access-Token": user_token,
        },
        params={
            "entry_path": entry_path,
        }
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def entry_post(
        user_token: str,
        entry_path: str,
        entry_type: str,
        is_collaborative: str,
        file_path: Optional[str] = None,
) -> Dict:
    return requests.post(
        url=f"{SERVER_BASE_URL}/api/entry",
        headers={
            "Access-Token": user_token,
        },
        data={
            "entry_path": entry_path,  # 文件路径
            "entry_type": entry_type,  # 条目类型：file或directory
            "is_collaborative": is_collaborative  # 布尔值需要转为字符串
        },
        files={"file": open(file_path, "rb")} if file_path else None
    ).json()


@pytest.fixture(scope="session")
def temp_file_content() -> bytes:
    return b"TEST FILE"


@pytest.fixture(scope="session")
def temp_file_path(
        temp_file_content: bytes,
) -> str:
    test_file = os.path.join(os.path.dirname(__file__), "..", "..", "temp", "file.txt")
    # 写入测试文件
    with open(test_file, "wb") as fp:
        fp.write(temp_file_content)
    # 返回文件路径
    yield test_file
    # 清理测试文件
    if os.path.exists(test_file):
        os.remove(test_file)


@pytest.fixture(scope="session")
def entry_path_file() -> str:
    return "/aa/bb/file.txt"


@pytest.fixture(scope="session")
def entry_path_directory() -> str:
    return "/ww/tt/ee"


# 预定义测试用户数据
@pytest.fixture(scope="session")
def user_dict_default(
        unique_user_dict_generator: Callable
) -> Dict:
    return unique_user_dict_generator()


@pytest.fixture(scope="session")
def user_token_default(
        user_dict_default: Dict,
):
    return user_register_success(user_dict_default)


@pytest.mark.dependency
def test_entry_post_success(
        user_token_default: str,
        entry_path_file: str,
        entry_path_directory: str,
        temp_file_path: str,
):
    assert_code(
        entry_post(
            user_token_default,
            entry_path_file,
            "file",
            "false",
            temp_file_path
        ),
        status.HTTP_200_OK
    )
    assert_code(
        entry_post(
            user_token_default,
            entry_path_directory,
            "directory",
            "false"
        ),
        status.HTTP_200_OK
    )


@pytest.mark.dependency(depends=["test_entry_post_success"])
def test_entry_post_failure_entry_path_duplicated(
        user_token_default: str,
        entry_path_file: str,
        entry_path_directory: str,
        temp_file_path: str,
):
    assert_code(
        entry_post(
            user_token_default,
            entry_path_file,
            "file",
            "false",
            temp_file_path
        ),
        status.HTTP_400_BAD_REQUEST
    )
    assert_code(
        entry_post(
            user_token_default,
            entry_path_directory,
            "directory",
            "false"
        ),
        status.HTTP_400_BAD_REQUEST
    )


@pytest.mark.dependency(depends=["test_entry_post_success"])
def test_entry_get_success(
        user_token_default: str,
        entry_path_file: str,
        entry_path_directory: str,
):
    response = entry_get_success(user_token_default, "/")
    entry_paths = {d["entry_path"] for d in response}
    for path in path_iterate_parents(entry_path_file):
        assert path in entry_paths
    for path in path_iterate_parents(entry_path_directory):
        assert path in entry_paths


@pytest.mark.dependency(depends=["test_entry_post_success"])
def test_entry_download_success(
        user_token_default: str,
        entry_path_file: str,
        temp_file_content: bytes,
):
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/entry/download",
        headers={
            "Access-Token": user_token_default,
        },
        params={
            "entry_path": entry_path_file,
        }
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.content == temp_file_content


@pytest.mark.dependency(depends=["test_entry_post_success"])
def test_entry_download_failure_entry_path_not_exists(
        user_token_default: str,
):
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/entry/download",
        headers={
            "Access-Token": user_token_default,
        },
        params={
            "entry_path": "/not_exists",
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.dependency(depends=["test_entry_post_success"])
def test_entry_download_failure_target_is_not_file(
        user_token_default: str,
        entry_path_directory: str
):
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/entry/download",
        headers={
            "Access-Token": user_token_default,
        },
        params={
            "entry_path": entry_path_directory,
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
