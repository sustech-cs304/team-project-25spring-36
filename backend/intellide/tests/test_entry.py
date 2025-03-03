import os.path
from typing import Callable, Optional

import pytest
import requests
from fastapi import status

from intellide.storage.storage import get_storage_path
from intellide.tests.conftest import SERVER_BASE_URL
from intellide.tests.test_user import user_register_success, unique_user_dict_generator
from intellide.tests.utils import *
from intellide.utils.path import path_iterate_parents, path_first_n, path_parts


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
    url = f"{SERVER_BASE_URL}/api/entry"
    headers = {
        "Access-Token": user_token,
    }
    data = {
        "entry_path": entry_path,  # 文件路径
        "entry_type": entry_type,  # 条目类型：file或directory
        "is_collaborative": is_collaborative  # 布尔值需要转为字符串
    }
    if file_path:
        with open(file_path, "rb") as f:
            return requests.post(
                url=url,
                headers=headers,
                data=data,
                files={
                    "file": f
                }
            ).json()
    else:
        return requests.post(
            url=url,
            headers=headers,
            data=data,
        ).json()


@pytest.fixture(scope="session")
def entry_path_file(
        unique_path_generator: Callable,
) -> str:
    return unique_path_generator(depth=3, suffix="txt")


@pytest.fixture(scope="session")
def entry_path_directory(
        unique_path_generator: Callable,
) -> str:
    return unique_path_generator(depth=3)


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
    storage_name = entry_get_success(user_token_default, entry_path_file)[0]["storage_name"]
    assert os.path.exists(get_storage_path(storage_name))
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
def test_entry_post_failure_entry_path_occupied(
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
def test_entry_download_failure_target_not_file(
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


@pytest.mark.dependency(depends=["test_entry_get_success"])
def test_entry_move_success_file(
        user_token_default: str,
        temp_file_path: str,
        unique_path_generator: Callable,
):
    src_entry_file_path = unique_path_generator(depth=3, suffix="txt")
    dst_entry_file_path = unique_path_generator(depth=1, suffix="txt")
    assert_code(
        entry_post(
            user_token_default,
            src_entry_file_path,
            "file",
            "false",
            temp_file_path
        ),
        status.HTTP_200_OK
    )
    assert_code(
        requests.put(
            url=f"{SERVER_BASE_URL}/api/entry/move",
            headers={
                "Access-Token": user_token_default,
            },
            json={
                "src_entry_path": src_entry_file_path,
                "dst_entry_path": dst_entry_file_path
            }
        ).json(),
        status.HTTP_200_OK
    )
    entry_paths = {d["entry_path"] for d in entry_get_success(user_token_default, "/")}
    assert src_entry_file_path not in entry_paths
    assert dst_entry_file_path in entry_paths


@pytest.mark.dependency(depends=["test_entry_get_success"])
def test_entry_move_success_directory(
        user_token_default: str,
        temp_file_path: str,
        unique_path_generator: Callable,
):
    src_entry_directory_path = unique_path_generator(depth=4)
    dst_entry_directory_path = unique_path_generator(depth=3)
    src_entry_directory_move_path = path_first_n(src_entry_directory_path, 3)
    assert_code(
        entry_post(
            user_token_default,
            src_entry_directory_path,
            "directory",
            "false",
            temp_file_path
        ),
        status.HTTP_200_OK
    )
    assert_code(
        requests.put(
            url=f"{SERVER_BASE_URL}/api/entry/move",
            headers={
                "Access-Token": user_token_default,
            },
            json={
                "src_entry_path": src_entry_directory_move_path,
                "dst_entry_path": dst_entry_directory_path
            }
        ).json(),
        status.HTTP_200_OK
    )
    entry_paths = {d["entry_path"] for d in entry_get_success(user_token_default, "/")}
    assert src_entry_directory_path not in entry_paths
    assert src_entry_directory_move_path not in entry_paths
    assert dst_entry_directory_path in entry_paths
    assert dst_entry_directory_path + "/" + path_parts(src_entry_directory_path, 3) in entry_paths


@pytest.mark.dependency(depends=["test_entry_move_success_file", "test_entry_move_success_directory"])
def test_entry_move_failure_entry_path_same(
        user_token_default: str,
        temp_file_path: str,
        unique_path_generator: Callable,
):
    entry_path = unique_path_generator(depth=3)
    assert_code(
        requests.put(
            url=f"{SERVER_BASE_URL}/api/entry/move",
            headers={
                "Access-Token": user_token_default,
            },
            json={
                "src_entry_path": entry_path,
                "dst_entry_path": entry_path
            }
        ).json(),
        status.HTTP_400_BAD_REQUEST
    )


@pytest.mark.dependency(depends=["test_entry_move_success_file", "test_entry_move_success_directory"])
def test_entry_move_failure_entry_path_occupied(
        user_token_default: str,
        temp_file_path: str,
        unique_path_generator: Callable,
):
    src_entry_path = unique_path_generator(depth=3)
    dst_entry_path = unique_path_generator(depth=3)
    assert_code(
        entry_post(
            user_token_default,
            src_entry_path,
            "directory",
            "false",
            temp_file_path
        ),
        status.HTTP_200_OK
    )
    assert_code(
        entry_post(
            user_token_default,
            dst_entry_path,
            "directory",
            "false",
            temp_file_path
        ),
        status.HTTP_200_OK
    )
    assert_code(
        requests.put(
            url=f"{SERVER_BASE_URL}/api/entry/move",
            headers={
                "Access-Token": user_token_default,
            },
            json={
                "src_entry_path": src_entry_path,
                "dst_entry_path": dst_entry_path
            }
        ).json(),
        status.HTTP_400_BAD_REQUEST
    )


@pytest.mark.dependency(depends=["test_entry_get_success"])
def test_entry_delete_success_file(
        user_token_default: str,
        temp_file_path: str,
        unique_path_generator: Callable,
):
    entry_path = unique_path_generator(depth=3, suffix="txt")
    assert_code(
        entry_post(
            user_token_default,
            entry_path,
            "file",
            "false",
            temp_file_path
        ),
        status.HTTP_200_OK
    )
    storage_name = entry_get_success(user_token_default, entry_path)[0]["storage_name"]
    assert_code(
        requests.delete(
            url=f"{SERVER_BASE_URL}/api/entry",
            headers={
                "Access-Token": user_token_default,
            },
            params={
                "entry_path": entry_path
            }
        ).json(),
        status.HTTP_200_OK
    )
    entry_paths = {d["entry_path"] for d in entry_get_success(user_token_default, "/")}
    assert entry_path not in entry_paths
    assert path_first_n(entry_path, 2) in entry_paths
    assert path_first_n(entry_path, 1) in entry_paths
    assert not os.path.exists(get_storage_path(storage_name))


@pytest.mark.dependency(depends=["test_entry_get_success"])
def test_entry_delete_success_directory(
        user_token_default: str,
        temp_file_path: str,
        unique_path_generator: Callable,
):
    entry_path = unique_path_generator(depth=4)
    assert_code(
        entry_post(
            user_token_default,
            entry_path,
            "directory",
            "false"
        ),
        status.HTTP_200_OK
    )
    assert_code(
        requests.delete(
            url=f"{SERVER_BASE_URL}/api/entry",
            headers={
                "Access-Token": user_token_default,
            },
            params={
                "entry_path": path_first_n(entry_path, 3)
            }
        ).json(),
        status.HTTP_200_OK
    )
    entry_paths = {d["entry_path"] for d in entry_get_success(user_token_default, "/")}
    assert entry_path not in entry_paths
    assert path_first_n(entry_path, 3) not in entry_paths
    assert path_first_n(entry_path, 2) in entry_paths
    assert path_first_n(entry_path, 1) in entry_paths


@pytest.mark.dependency(depends=["test_entry_delete_success_file", "test_entry_delete_success_directory"])
def test_entry_delete_failure_entry_path_not_exists(
        user_token_default: str,
        unique_path_generator: Callable,
):
    assert_code(
        requests.delete(
            url=f"{SERVER_BASE_URL}/api/entry",
            headers={
                "Access-Token": user_token_default,
            },
            params={
                "entry_path": unique_path_generator(depth=3)
            }
        ).json(),
        status.HTTP_400_BAD_REQUEST
    )
