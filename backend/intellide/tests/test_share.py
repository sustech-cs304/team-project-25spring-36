from typing import Callable, Optional

import pytest
import requests
from fastapi import status

from intellide.tests.conftest import SERVER_BASE_URL, unique_path_generator
from intellide.tests.test_entry import entry_post
from intellide.tests.test_user import user_register_success, unique_user_dict_generator
from intellide.tests.utils import *
from intellide.utils.encrypt import jwt_decode
from intellide.utils.path import path_first_n, path_iterate_parents


def shared_entry_info_get_success(
        user_token: str
) -> Dict:
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/share/info",
        headers={
            "Access-Token": user_token,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def shared_entry_get_success(
        user_token: str,
        shared_entry_id: int,
        entry_path: str,
) -> Dict:
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/share",
        headers={
            "Access-Token": user_token,
        },
        params={
            "shared_entry_id": shared_entry_id,
            "entry_path": entry_path,
        }
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def shared_entry_post(
        user_token: str,
        shared_entry_id: int,
        shared_entry_type: str,
        entry_path: str,
        file_path: Optional[str] = None,
) -> Dict:
    url = f"{SERVER_BASE_URL}/api/share"
    headers = {
        "Access-Token": user_token,
    }
    params = {
        "shared_entry_id": shared_entry_id,
    }
    data = {
        "entry_path": entry_path,
        "entry_type": shared_entry_type,
        "is_collaborative": "false"
    }
    if file_path:
        with open(file_path, "rb") as file:
            response = requests.post(
                url=url,
                headers=headers,
                params=params,
                data=data,
                files={
                    "file": file
                }
            ).json()
    else:
        response = requests.post(
            url=url,
            headers=headers,
            params=params,
            data=data,
        ).json()
    return response


def shared_entry_post_success(
        user_token: str,
        shared_entry_id: int,
        shared_entry_type: str,
        entry_path: str,
        file_path: Optional[str] = None,
) -> Dict:
    response = shared_entry_post(
        user_token,
        shared_entry_id,
        shared_entry_type,
        entry_path,
        file_path
    )
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def shared_entry_token_create_success(
        user_token: str,
        entry_path: str,
        permissions: Dict,
) -> str:
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/share/token/create",
        headers={
            "Access-Token": user_token,
        },
        json={
            "entry_path": entry_path,  # 文件路径
            "permissions": permissions
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def shared_entry_token_parse_success(
        user_token: str,
        share_token: str
) -> None:
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/share/token/parse",
        headers={
            "Access-Token": user_token,
        },
        json={
            "token": share_token,  # 文件路径
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)


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
def shared_entry_base_path(
        entry_path_inviter: str,
) -> str:
    return path_first_n(entry_path_inviter, 2)


@pytest.fixture(scope="session")
def shared_entry_base_token_ref() -> Ref[str]:
    return Ref()


@pytest.fixture(scope="session")
def shared_entry_base_permissions() -> Dict:
    return {
        "": "read_write",
    }


@pytest.fixture(scope="session")
def shared_entry_base_id_ref() -> Ref[int]:
    return Ref()


@pytest.fixture(scope="session")
def shared_entry_base_ref() -> Ref[Dict]:
    return Ref()


@pytest.mark.dependency
def test_shared_entry_token_create_success(
        user_token_inviter: str,
        shared_entry_base_path: str,
        shared_entry_base_id_ref: Ref[int],
        shared_entry_base_token_ref: Ref[str],
        shared_entry_base_permissions: Dict,
):
    token = shared_entry_token_create_success(
        user_token_inviter,
        shared_entry_base_path,
        shared_entry_base_permissions
    )
    shared_entry_base_token_ref.set(token)
    shared_entry_id = jwt_decode(token)["shared_entry_id"]
    shared_entry_base_id_ref.set(shared_entry_id)


@pytest.mark.dependency(depends=["test_shared_entry_token_create_success"])
def test_shared_entry_token_parse_success(
        user_token_receiver: str,
        shared_entry_base_token_ref: Ref,
):
    shared_entry_token_parse_success(user_token_receiver, shared_entry_base_token_ref.get())


@pytest.mark.dependency(depends=["test_shared_entry_token_parse_success"])
def test_shared_entry_info_get_success(
        user_token_receiver: str,
        shared_entry_base_id_ref: Ref[int],
):
    shared_entry_infos = shared_entry_info_get_success(user_token_receiver)
    assert shared_entry_infos
    shared_entry_base_id = shared_entry_base_id_ref.get()
    shared_entry_ids = {info["shared_entry_id"] for info in shared_entry_infos}
    assert shared_entry_base_id in shared_entry_ids
    # TODO: 校验返回数据


@pytest.mark.dependency(depends=["test_shared_entry_token_parse_success"])
def test_shared_entry_get_success(
        user_token_receiver: str,
        shared_entry_base_id_ref: Ref[int],
):
    shared_entry_base_id = shared_entry_base_id_ref.get()
    shared_entry_get_success(
        user_token_receiver,
        shared_entry_base_id,
        "/"
    )


@pytest.mark.dependency(depends=["test_shared_entry_get_success"])
def test_shared_entry_post_success(
        user_token_receiver: str,
        shared_entry_base_id_ref: Ref[int],
        unique_path_generator: Callable,
        temp_file_path: str,
        shared_entry_base_path: str,
):
    shared_entry_base_id = shared_entry_base_id_ref.get()
    shared_entry_path_post_directory = unique_path_generator(depth=2)
    shared_entry_post_success(
        user_token_receiver,
        shared_entry_base_id,
        "directory",
        shared_entry_path_post_directory
    )
    shared_entry_path_post_file = unique_path_generator(depth=3, suffix="txt")
    shared_entry_post_success(
        user_token_receiver,
        shared_entry_base_id,
        "file",
        shared_entry_path_post_file,
        temp_file_path
    )
    shared_entry_paths = {
        entry["entry_path"] for entry in shared_entry_get_success(
            user_token_receiver,
            shared_entry_base_id,
            "/"
        )
    }

    for parent in path_iterate_parents(shared_entry_path_post_directory):
        assert parent in shared_entry_paths
    for parent in path_iterate_parents(shared_entry_path_post_file):
        assert parent in shared_entry_paths


@pytest.mark.dependency(depends=["test_shared_entry_post_success"])
def test_shared_entry_move_success(
        user_token_receiver: str,
        shared_entry_base_id_ref: Ref[int],
        unique_path_generator: Callable,
):
    shared_entry_base_id = shared_entry_base_id_ref.get()
    shared_entry_src_path = unique_path_generator(depth=4)
    shared_entry_dst_path = unique_path_generator(depth=4)
    shared_entry_post_success(
        user_token_receiver,
        shared_entry_base_id,
        "directory",
        shared_entry_src_path,
    )
    response = requests.put(
        url=f"{SERVER_BASE_URL}/api/share/move",
        headers={
            "Access-Token": user_token_receiver,
        },
        json={
            "src_entry_path": shared_entry_src_path,
            "dst_entry_path": shared_entry_dst_path,
        },
        params={
            "shared_entry_id": shared_entry_base_id,
        }
    ).json()

    assert_code(response, status.HTTP_200_OK)
    shared_entry_paths = {
        entry["entry_path"] for entry in shared_entry_get_success(
            user_token_receiver,
            shared_entry_base_id,
            "/"
        )
    }
    assert shared_entry_src_path not in shared_entry_paths
    assert shared_entry_dst_path in shared_entry_paths


@pytest.mark.dependency(depends=["test_shared_entry_post_success"])
def test_shared_entry_delete_success(
        user_token_receiver: str,
        shared_entry_base_id_ref: Ref[int],
        unique_path_generator: Callable,
        temp_file_path: str,
):
    shared_entry_base_id = shared_entry_base_id_ref.get()
    shared_entry_path_post = unique_path_generator(depth=4, suffix="txt")
    shared_entry_post_success(
        user_token_receiver,
        shared_entry_base_id,
        "file",
        shared_entry_path_post,
        temp_file_path,
    )
    response = requests.delete(
        url=f"{SERVER_BASE_URL}/api/share",
        headers={
            "Access-Token": user_token_receiver,
        },
        params={
            "shared_entry_id": shared_entry_base_id,
            "entry_path": shared_entry_path_post,
        }
    ).json()
    assert_code(response, status.HTTP_200_OK)
    shared_entry_paths = {
        entry["entry_path"] for entry in shared_entry_get_success(
            user_token_receiver,
            shared_entry_base_id,
            "/"
        )
    }
    assert shared_entry_path_post not in shared_entry_paths


@pytest.mark.dependency(depends=["test_shared_entry_post_success"])
def test_shared_entry_basic_permission_success(
        user_token_inviter: str,
        user_token_receiver: str,
        entry_path_inviter: str,
        unique_path_generator: Callable,
        unique_user_dict_generator: Callable,
        temp_file_path: str,
):
    shared_entry_path = path_first_n(entry_path_inviter, 2)
    read_token = shared_entry_token_create_success(
        user_token_inviter,
        shared_entry_path,
        {"": "read"}
    )
    read_token_shared_entry_id = jwt_decode(read_token)["shared_entry_id"]
    read_write_token = shared_entry_token_create_success(
        user_token_inviter,
        shared_entry_path,
        {"": "read_write"}
    )
    read_write_token_shared_entry_id = jwt_decode(read_write_token)["shared_entry_id"]
    shared_entry_token_parse_success(user_token_receiver, read_token)
    shared_entry_token_parse_success(user_token_receiver, read_write_token)
    assert_code(
        shared_entry_post(
            user_token_receiver,
            read_token_shared_entry_id,
            "directory",
            unique_path_generator(depth=4)
        ),
        status.HTTP_403_FORBIDDEN
    )
    shared_entry_post_success(
        user_token_receiver,
        read_write_token_shared_entry_id,
        "directory",
        unique_path_generator(depth=4)
    )
