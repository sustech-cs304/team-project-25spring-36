from typing import Dict, Callable, List, Optional, Union

import pytest
import requests
from fastapi import status

from intellide.tests.conftest import SERVER_BASE_URL, unique_string_generator, unique_path_generator
from intellide.tests.test_user import unique_user_dict_generator, user_register_success
from intellide.tests.utils import assert_code
from intellide.utils.path import path_first_n, path_iterate_parents, path_parts, path_join


@pytest.fixture(scope="session", autouse=True)
def init(
        store: Dict,
        unique_user_dict_generator: Callable,
):
    store["user_dict_teacher"] = unique_user_dict_generator()
    store["user_dict_student"] = unique_user_dict_generator()
    data = user_register_success(store["user_dict_teacher"])
    store["user_token_teacher"] = data["token"]
    store["user_id_teacher"] = data["user_id"]
    data = user_register_success(store["user_dict_student"])
    store["user_token_student"] = data["token"]
    store["user_id_student"] = data["user_id"]


@pytest.mark.dependency
def test_course_post_success(
        store: Dict,
        unique_string_generator: Callable,
):
    user_token_teacher = store["user_token_teacher"]
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/course",
        headers={
            "Access-Token": user_token_teacher,
        },
        json={
            "name": unique_string_generator(),
            "description": unique_string_generator(),
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    store["course_id_base"] = str(response["data"]["course_id"])


@pytest.mark.dependency(depends=["test_course_post_success"])
def test_course_student_join_success(
        store: Dict,
):
    user_token_student = store["user_token_student"]
    course_id_base = store["course_id_base"]
    course_student_join_success(user_token_student, course_id_base)


@pytest.mark.dependency(depends=["test_course_post_success"])
def test_course_get_success_role_teacher(
        store: Dict,
):
    user_token_teacher = store["user_token_teacher"]
    course_id_base = store["course_id_base"]
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/course",
        headers={
            "Access-Token": user_token_teacher,
        },
        params={
            "role": "teacher",
        }
    ).json()
    assert_code(response, status.HTTP_200_OK)
    assert course_id_base in {course["id"] for course in response["data"]}


@pytest.mark.dependency(depends=["test_course_student_join_success"])
def test_course_get_success_role_student(
        store: Dict,
):
    user_token_student = store["user_token_student"]
    course_id_base = store["course_id_base"]
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/course",
        headers={
            "Access-Token": user_token_student,
        },
        params={
            "role": "student",
        }
    ).json()
    assert_code(response, status.HTTP_200_OK)
    assert course_id_base in {course["id"] for course in response["data"]}


@pytest.mark.dependency(depends=["test_course_student_join_success"])
def test_course_student_get_success(
        store: Dict,
):
    user_dict_student = store["user_dict_student"]
    user_token_student = store["user_token_student"]
    course_id_base = store["course_id_base"]
    students = course_student_get_success(user_token_student, course_id_base)
    assert user_dict_student["username"] in {student["username"] for student in students}


@pytest.mark.dependency(depends=["test_course_student_get_success"])
def test_course_student_delete_quit(
        store: Dict,
        unique_user_dict_generator: Callable,
):
    user_token_teacher = store["user_token_teacher"]
    course_id_base = store["course_id_base"]
    data = user_register_success(unique_user_dict_generator())
    student_token = data["token"]
    student_id = data["user_id"]
    course_student_join_success(student_token, course_id_base)
    course_student_delete_success(
        user_token=student_token,
        course_id=course_id_base,
    )
    assert student_id not in {
        student["id"] for student in
        course_student_get_success(user_token_teacher, course_id_base)
    }


@pytest.mark.dependency(depends=["test_course_student_get_success"])
def test_course_student_delete_kick(
        store: Dict,
        unique_user_dict_generator: Callable,
):
    user_token_teacher = store["user_token_teacher"]
    course_id_base = store["course_id_base"]
    data = user_register_success(unique_user_dict_generator())
    student_token = data["token"]
    student_id = data["user_id"]
    course_student_join_success(student_token, course_id_base)
    course_student_delete_success(
        user_token=user_token_teacher,
        course_id=course_id_base,
        student_id=student_id,
    )
    assert student_id not in {
        student["id"] for student in
        course_student_get_success(user_token_teacher, course_id_base)
    }


@pytest.mark.dependency(depends=["test_course_post_success"])
def test_course_directory_post_success(
        store: Dict,
        unique_string_generator: Callable,
):
    user_token_teacher = store["user_token_teacher"]
    course_id_base = store["course_id_base"]
    store["course_directory_id_base"] = str(
        course_directory_post_success(
            user_token=user_token_teacher,
            course_id=course_id_base,
            directory_name=unique_string_generator(),
        )["course_directory_id"]
    )


@pytest.mark.dependency(depends=["test_course_directory_post_success"])
def test_course_directory_get_success(
        store: Dict,
):
    user_token_teacher = store["user_token_teacher"]
    course_id_base = store["course_id_base"]
    course_directory_id_base = store["course_directory_id_base"]
    assert course_directory_id_base in {
        course_directory["id"]
        for course_directory in course_directory_get_success(
            user_token_teacher,
            course_id_base,
        )
    }


@pytest.mark.dependency(depends=["test_course_directory_get_success"])
def test_course_directory_delete_success(
        store: Dict,
        unique_string_generator: Callable,
):
    user_token_teacher = store["user_token_teacher"]
    course_id_base = store["course_id_base"]
    course_directory_id = str(
        course_directory_post_success(
            user_token=user_token_teacher,
            course_id=course_id_base,
            directory_name=unique_string_generator(),
        )["course_directory_id"]
    )
    response = requests.delete(
        url=f"{SERVER_BASE_URL}/api/course/directory",
        headers={
            "Access-Token": user_token_teacher,
        },
        params={
            "course_directory_id": course_directory_id,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    assert course_directory_id not in {
        course_directory["id"]
        for course_directory in course_directory_get_success(
            user_token_teacher,
            course_id_base,
        )
    }


@pytest.mark.dependency(depends=["test_course_directory_post_success"])
def test_course_directory_entry_post_success(
        store: Dict,
        unique_path_generator: Callable,
        temp_file_path: str,
):
    user_token_teacher = store["user_token_teacher"]
    course_directory_id_base = store["course_directory_id_base"]
    path = unique_path_generator(depth=4, suffix="txt")
    store["course_directory_entry_path_base"] = path
    store["course_directory_entry_id_base"] = str(
        course_directory_entry_post_success(
            user_token_teacher,
            course_directory_id_base,
            path,
            file_path=temp_file_path,
        )["course_directory_entry_id"])


@pytest.mark.dependency(depends=["test_course_directory_entry_post_success"])
def test_course_directory_entry_get_success(
        store: Dict,
):
    user_token_teacher = store["user_token_teacher"]
    course_directory_id_base = store["course_directory_id_base"]
    course_directory_entry_id_base = store["course_directory_entry_id_base"]
    assert course_directory_entry_id_base in {
        course_directory_entry["id"]
        for course_directory_entry in
        course_directory_entry_get_success(
            user_token_teacher,
            course_directory_id_base,
            "/",
            True,
        )
    }


@pytest.mark.dependency(depends=["test_course_directory_entry_post_success"])
def test_course_directory_entry_download_success(
        store: Dict,
        temp_file_content: bytes,
):
    user_token_teacher = store["user_token_teacher"]
    course_directory_entry_id_base = store["course_directory_entry_id_base"]
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/course/directory/entry/download",
        headers={
            "Access-Token": user_token_teacher,
        },
        params={
            "course_directory_entry_id": course_directory_entry_id_base,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.content == temp_file_content


@pytest.mark.dependecy(depends=["test_course_directory_entry_get_success"])
def test_course_directory_entry_delete_success(
        store: Dict,
        unique_path_generator: Callable,
):
    user_token_teacher = store["user_token_teacher"]
    course_directory_id_base = store["course_directory_id_base"]
    path = unique_path_generator(depth=4)
    course_directory_entry_id = course_directory_entry_post_success(
        user_token_teacher,
        course_directory_id_base,
        path,
    )["course_directory_entry_id"]
    root_course_directory_entry_id = course_directory_entry_get_success(
        user_token_teacher,
        course_directory_id_base,
        path_first_n(path, 1),
        False,
    )["id"]
    response = requests.delete(
        url=f"{SERVER_BASE_URL}/api/course/directory/entry",
        headers={
            "Access-Token": user_token_teacher,
        },
        params={
            "course_directory_entry_id": root_course_directory_entry_id,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    course_directory_entries = course_directory_entry_get_success(
        user_token_teacher,
        course_directory_id_base,
        "/",
        True,
    )
    course_directory_entry_paths = {
        course_directory_entry["path"]
        for course_directory_entry in course_directory_entries
    }
    course_directory_entry_ids = {
        course_directory_entry["id"]
        for course_directory_entry in course_directory_entries
    }
    for parent in path_iterate_parents(path):
        assert parent not in course_directory_entry_paths
    assert course_directory_entry_id not in course_directory_entry_ids


@pytest.mark.dependecy(depends=["test_course_directory_entry_get_success"])
def test_course_directory_entry_move_success(
        store: Dict,
        unique_path_generator: Callable,
):
    user_token_teacher = store["user_token_teacher"]
    course_directory_id_base = store["course_directory_id_base"]
    path = unique_path_generator(depth=4)
    course_directory_entry_post_success(
        user_token_teacher,
        course_directory_id_base,
        path,
    )
    root_course_directory_entry_id = course_directory_entry_get_success(
        user_token_teacher,
        course_directory_id_base,
        path_first_n(path, 2),
        False,
    )["id"]
    dst_path = unique_path_generator(depth=2)
    response = requests.put(
        url=f"{SERVER_BASE_URL}/api/course/directory/entry/move",
        headers={
            "Access-Token": user_token_teacher,
        },
        json={
            "course_directory_entry_id": root_course_directory_entry_id,
            "dst_path": dst_path,
        }
    ).json()
    assert_code(response, status.HTTP_200_OK)
    course_directory_entries = course_directory_entry_get_success(
        user_token_teacher,
        course_directory_id_base,
        "/",
        True,
    )
    course_directory_entry_paths = {
        course_directory_entry["path"]
        for course_directory_entry in course_directory_entries
    }
    assert "/" + path_parts(dst_path, 0) in course_directory_entry_paths
    assert dst_path in course_directory_entry_paths
    assert path_join(dst_path, path_parts(path, 2)) in course_directory_entry_paths
    assert path_join(dst_path, path_parts(path, 2), path_parts(path, 3)) in course_directory_entry_paths


def course_student_get_success(
        user_token: str,
        course_id: int,
) -> List[Dict]:
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/course/student",
        headers={
            "Access-Token": user_token,
        },
        params={
            "course_id": course_id,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def course_student_join_success(
        student_token: str,
        course_id: int,
) -> Dict:
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/course/student/join",
        headers={
            "Access-Token": student_token,
        },
        json={
            "course_id": course_id,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def course_student_delete_success(
        user_token: str,
        course_id: int,
        student_id: Optional[int] = None,
) -> None:
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/course/directory",
        headers={
            "Access-Token": user_token,
        },
        params={
            "course_id": course_id,
            "student_id": student_id,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)


def course_directory_post_success(
        user_token: str,
        course_id: int,
        directory_name: str,
) -> Dict:
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/course/directory",
        headers={
            "Access-Token": user_token,
        },
        json={
            "course_id": course_id,
            "name": directory_name,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def course_directory_get_success(
        user_token: str,
        course_id: int,
) -> List[Dict]:
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/course/directory",
        headers={
            "Access-Token": user_token,
        },
        params={
            "course_id": course_id,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def course_directory_entry_post_success(
        user_token: str,
        course_directory_id: int,
        path: str,
        file_path: Optional[str] = None
):
    headers = {
        "Access-Token": user_token,
    }
    data = {
        "course_directory_id": course_directory_id,
        "path": path,
    }
    if file_path:
        with open(file_path, "rb") as f:
            response = requests.post(
                url=f"{SERVER_BASE_URL}/api/course/directory/entry",
                headers=headers,
                data=data,
                files={
                    "file": f,
                },
            ).json()
    else:
        response = requests.post(
            url=f"{SERVER_BASE_URL}/api/course/directory/entry",
            headers=headers,
            data=data,
        ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def course_directory_entry_get_success(
        user_token: str,
        course_directory_id: int,
        path: str,
        fuzzy: bool,
) -> Union[Dict, List[Dict]]:
    response = requests.get(
        url=f"{SERVER_BASE_URL}/api/course/directory/entry",
        headers={
            "Access-Token": user_token,
        },
        params={
            "course_directory_id": course_directory_id,
            "path": path,
            "fuzzy": fuzzy
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]
