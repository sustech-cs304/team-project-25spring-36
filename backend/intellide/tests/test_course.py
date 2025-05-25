import json
import time
from typing import Dict, Callable, List, Optional, Union

import pytest
import requests
import websocket
from fastapi import status
import y_py

from intellide.tests.conftest import (
    SERVER_API_BASE_URL,
    SERVER_WS_BASE_URL,
    unique_string_generator,
    unique_path_generator,
)
from intellide.tests.test_user import unique_user_dict_generator, user_register_success
from intellide.tests.utils import assert_code
from intellide.utils.path import (
    path_first_n,
    path_iterate_parents,
    path_parts,
    path_join,
)


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
        url=f"{SERVER_API_BASE_URL}/course",
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
        url=f"{SERVER_API_BASE_URL}/course",
        headers={
            "Access-Token": user_token_teacher,
        },
        params={
            "role": "teacher",
        },
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
        url=f"{SERVER_API_BASE_URL}/course",
        headers={
            "Access-Token": user_token_student,
        },
        params={
            "role": "student",
        },
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
    assert student_id not in {student["id"] for student in course_student_get_success(user_token_teacher, course_id_base)}


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
    assert student_id not in {student["id"] for student in course_student_get_success(user_token_teacher, course_id_base)}


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
        url=f"{SERVER_API_BASE_URL}/course/directory",
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
        )["course_directory_entry_id"]
    )


@pytest.mark.dependency(depends=["test_course_directory_entry_post_success"])
def test_course_directory_entry_get_success(
    store: Dict,
):
    user_token_teacher = store["user_token_teacher"]
    course_directory_id_base = store["course_directory_id_base"]
    course_directory_entry_id_base = store["course_directory_entry_id_base"]
    assert course_directory_entry_id_base in {
        course_directory_entry["id"]
        for course_directory_entry in course_directory_entry_get_success(
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
        url=f"{SERVER_API_BASE_URL}/course/directory/entry/download",
        headers={
            "Access-Token": user_token_teacher,
        },
        params={
            "course_directory_entry_id": course_directory_entry_id_base,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.content == temp_file_content


@pytest.mark.dependency(depends=["test_course_directory_entry_get_success"])
def test_course_directory_entry_delete_success_and_fail(
    store: Dict,
    unique_path_generator: Callable,
):
    user_token_teacher = store["user_token_teacher"]
    user_token_student = store["user_token_student"]
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
    response_student = requests.delete(
        url=f"{SERVER_API_BASE_URL}/course/directory/entry",
        headers={
            "Access-Token": user_token_student,
        },
        params={
            "course_directory_entry_id": root_course_directory_entry_id,
        },
    ).json()
    assert_code(response_student, status.HTTP_403_FORBIDDEN)
    response_teacher = requests.delete(
        url=f"{SERVER_API_BASE_URL}/course/directory/entry",
        headers={
            "Access-Token": user_token_teacher,
        },
        params={
            "course_directory_entry_id": root_course_directory_entry_id,
        },
    ).json()
    assert_code(response_teacher, status.HTTP_200_OK)
    course_directory_entries = course_directory_entry_get_success(
        user_token_teacher,
        course_directory_id_base,
        "/",
        True,
    )
    course_directory_entry_paths = {course_directory_entry["path"] for course_directory_entry in course_directory_entries}
    course_directory_entry_ids = {course_directory_entry["id"] for course_directory_entry in course_directory_entries}
    for parent in path_iterate_parents(path):
        assert parent not in course_directory_entry_paths
    assert course_directory_entry_id not in course_directory_entry_ids


@pytest.mark.dependency(depends=["test_course_directory_entry_get_success"])
def test_course_directory_entry_move_success_and_fail(
    store: Dict,
    unique_path_generator: Callable,
):
    user_token_teacher = store["user_token_teacher"]
    user_token_student = store["user_token_student"]
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
    response_student = requests.put(
        url=f"{SERVER_API_BASE_URL}/course/directory/entry/move",
        headers={
            "Access-Token": user_token_student,
        },
        json={
            "course_directory_entry_id": root_course_directory_entry_id,
            "dst_path": dst_path,
        },
    ).json()
    assert_code(response_student, status.HTTP_403_FORBIDDEN)
    response_teacher = requests.put(
        url=f"{SERVER_API_BASE_URL}/course/directory/entry/move",
        headers={
            "Access-Token": user_token_teacher,
        },
        json={
            "course_directory_entry_id": root_course_directory_entry_id,
            "dst_path": dst_path,
        },
    ).json()
    assert_code(response_teacher, status.HTTP_200_OK)
    course_directory_entries = course_directory_entry_get_success(
        user_token_teacher,
        course_directory_id_base,
        "/",
        True,
    )
    course_directory_entry_paths = {course_directory_entry["path"] for course_directory_entry in course_directory_entries}
    assert "/" + path_parts(dst_path, 0) in course_directory_entry_paths
    assert dst_path in course_directory_entry_paths
    assert path_join(dst_path, path_parts(path, 2)) in course_directory_entry_paths
    assert path_join(dst_path, path_parts(path, 2), path_parts(path, 3)) in course_directory_entry_paths


@pytest.mark.dependency(depends=["test_course_post_success"])
def test_course_chat_success(
    store: Dict,
    unique_string_generator: Callable,
):
    user_token_teacher = store["user_token_teacher"]
    user_token_student = store["user_token_student"]
    user_id_student = store["user_id_student"]
    course_id_base = store["course_id_base"]

    ws_student = websocket.WebSocket()
    ws_teacher = websocket.WebSocket()
    try:
        ws_student.connect(
            url=f"{SERVER_WS_BASE_URL}/course/chat/{course_id_base}",
            header={
                "Access-Token": user_token_student,
            },
        )
        ws_teacher.connect(
            url=f"{SERVER_WS_BASE_URL}/course/chat/{course_id_base}",
            header={
                "Access-Token": user_token_teacher,
            },
        )
        data = {
            "type": "message",
            "data": unique_string_generator(),
        }
        ws_student.send(json.dumps(data))
        response = json.loads(ws_teacher.recv())
        assert user_id_student == response["user_id"]
        assert data == response["data"]
    finally:
        ws_student.close()
        ws_teacher.close()


def course_student_get_success(
    user_token: str,
    course_id: int,
) -> List[Dict]:
    response = requests.get(
        url=f"{SERVER_API_BASE_URL}/course/student",
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
        url=f"{SERVER_API_BASE_URL}/course/student/join",
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
        url=f"{SERVER_API_BASE_URL}/course/directory",
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
        url=f"{SERVER_API_BASE_URL}/course/directory",
        headers={
            "Access-Token": user_token,
        },
        json={
            "course_id": course_id,
            "name": directory_name,
            "permission": {
                "": ["read", "upload"],
            },
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def course_directory_get_success(
    user_token: str,
    course_id: int,
) -> List[Dict]:
    response = requests.get(
        url=f"{SERVER_API_BASE_URL}/course/directory",
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
    file_path: Optional[str] = None,
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
                url=f"{SERVER_API_BASE_URL}/course/directory/entry",
                headers=headers,
                data=data,
                files={
                    "file": f,
                },
            ).json()
    else:
        response = requests.post(
            url=f"{SERVER_API_BASE_URL}/course/directory/entry",
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
        url=f"{SERVER_API_BASE_URL}/course/directory/entry",
        headers={
            "Access-Token": user_token,
        },
        params={
            "course_directory_id": course_directory_id,
            "path": path,
            "fuzzy": fuzzy,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]

def course_homework_assignment_post_success(
    user_token: str,
    course_id: int,
    title: str,
    description: str,
    course_directory_entry_ids: List[int],
) -> Dict:
    from datetime import datetime, timedelta
    
    deadline = (datetime.now() + timedelta(days=7)).isoformat()
    
    response = requests.post(
        url=f"{SERVER_API_BASE_URL}/course/homework/assignment",
        headers={
            "Access-Token": user_token,
        },
        json={
            "course_id": course_id,
            "title": title,
            "description": description,
            "deadline": deadline,
            "course_directory_entry_ids": course_directory_entry_ids,
        },
    ).json()
    
    if "detail" in response:
        pytest.fail(f"API请求失败: {response}")
        
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def course_homework_assignment_get_success(
    user_token: str,
    course_id: int,
) -> List[Dict]:
    response = requests.get(
        url=f"{SERVER_API_BASE_URL}/course/homework/assignment",
        headers={
            "Access-Token": user_token,
        },
        params={
            "course_id": course_id,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def course_homework_submission_post_success(
    user_token: str,
    assignment_id: int,
    title: str,
    description: str,
    course_directory_entry_ids: List[int],
) -> Dict:
    response = requests.post(
        url=f"{SERVER_API_BASE_URL}/course/homework/submission",
        headers={
            "Access-Token": user_token,
        },
        json={
            "assignment_id": assignment_id,
            "title": title,
            "description": description,
            "course_directory_entry_ids": course_directory_entry_ids,
        },
    )
    
    if response.status_code != 200:
        pytest.fail(f"API请求失败: {response.status_code}")
    
    result = response.json()
    assert_code(result, status.HTTP_200_OK)
    return result["data"]


def course_homework_submission_get_success(
    user_token: str,
    assignment_id: int,
) -> List[Dict]:
    response = requests.get(
        url=f"{SERVER_API_BASE_URL}/course/homework/submission",
        headers={
            "Access-Token": user_token,
        },
        params={
            "assignment_id": assignment_id,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


def course_homework_submission_grade_success(
    user_token: str,
    submission_id: int,
    grade: float,
    feedback: str,
) -> Dict:
    response = requests.put(
        url=f"{SERVER_API_BASE_URL}/course/homework/submission/grade",
        headers={
            "Access-Token": user_token,
        },
        json={
            "submission_id": submission_id,
            "grade": grade,
            "feedback": feedback,
        },
    ).json()
    
    assert_code(response, status.HTTP_200_OK)
    return response["data"]


@pytest.mark.dependency(depends=["test_course_directory_entry_post_success"])
def test_course_homework_assignment_post_success(
    store: Dict,
    unique_string_generator: Callable,
):
    user_token_teacher = store["user_token_teacher"]
    course_id_base = store["course_id_base"]
    course_directory_entry_id_base = store["course_directory_entry_id_base"]
    
    assignment = course_homework_assignment_post_success(
        user_token=user_token_teacher,
        course_id=course_id_base,
        title=unique_string_generator(),
        description=unique_string_generator(),
        course_directory_entry_ids=[course_directory_entry_id_base],
    )
    
    assert "id" in assignment
    store["assignment_id_base"] = assignment["id"]


@pytest.mark.dependency(depends=["test_course_homework_assignment_post_success"])
def test_course_homework_assignment_get_success(
    store: Dict,
):
    user_token_teacher = store["user_token_teacher"]
    course_id_base = store["course_id_base"]
    assignment_id_base = store["assignment_id_base"]
    
    assignments = course_homework_assignment_get_success(
        user_token=user_token_teacher,
        course_id=course_id_base,
    )
    
    assert assignment_id_base in {assignment["id"] for assignment in assignments}


@pytest.mark.dependency(depends=["test_course_homework_assignment_post_success"])
def test_course_homework_submission_post_success(
    store: Dict,
    unique_string_generator: Callable,
    temp_file_path: str,
):
    user_token_student = store["user_token_student"]
    assignment_id_base = store["assignment_id_base"]
    course_directory_id_base = store["course_directory_id_base"]
    
    student_path = f"/student_homework/{unique_string_generator()}.txt"
    student_entry = course_directory_entry_post_success(
        user_token=user_token_student,
        course_directory_id=course_directory_id_base,
        path=student_path,
        file_path=temp_file_path,
    )
    student_entry_id = student_entry["course_directory_entry_id"]
    
    submission = course_homework_submission_post_success(
        user_token=user_token_student,
        assignment_id=assignment_id_base,
        title=unique_string_generator(),
        description=unique_string_generator(),
        course_directory_entry_ids=[student_entry_id],
    )
    
    assert "id" in submission
    store["submission_id_base"] = submission["id"]


@pytest.mark.dependency(depends=["test_course_homework_submission_post_success"])
def test_course_homework_submission_get_success(
    store: Dict,
):
    user_token_teacher = store["user_token_teacher"]
    assignment_id_base = store["assignment_id_base"]
    submission_id_base = store["submission_id_base"]
    
    submissions = course_homework_submission_get_success(
        user_token=user_token_teacher,
        assignment_id=assignment_id_base,
    )
    
    assert submission_id_base in {submission["id"] for submission in submissions}


@pytest.mark.dependency(depends=["test_course_homework_submission_post_success"])
def test_course_homework_submission_grade_success(
    store: Dict,
    unique_string_generator: Callable,
):
    user_token_teacher = store["user_token_teacher"]
    submission_id_base = store["submission_id_base"]
    
    grade = 85.5
    feedback = unique_string_generator()
    graded_submission = course_homework_submission_grade_success(
        user_token=user_token_teacher,
        submission_id=submission_id_base,
        grade=grade,
        feedback=feedback,
    )
    
    assert float(graded_submission["grade"]) == grade
    assert graded_submission["feedback"] == feedback


@pytest.mark.dependency(depends=["test_course_homework_assignment_post_success"])
def test_course_homework_assignment_status_success(
    store: Dict,
):
    user_token_student = store["user_token_student"]
    course_id_base = store["course_id_base"]
    
    response = requests.get(
        url=f"{SERVER_API_BASE_URL}/course/homework/assignment/status",
        headers={
            "Access-Token": user_token_student,
        },
        params={
            "course_id": course_id_base,
        },
    ).json()
    
    assert_code(response, status.HTTP_200_OK)
    status_list = response["data"]
    assert isinstance(status_list, list)


@pytest.mark.dependency(depends=["test_course_homework_assignment_post_success"])
def test_course_homework_assignment_update_success(
    store: Dict,
    unique_string_generator: Callable,
):
    user_token_teacher = store["user_token_teacher"]
    assignment_id_base = store["assignment_id_base"]
    
    new_title = unique_string_generator()
    response = requests.put(
        url=f"{SERVER_API_BASE_URL}/course/homework/assignment",
        headers={
            "Access-Token": user_token_teacher,
        },
        json={
            "assignment_id": assignment_id_base,
            "title": new_title,
        },
    ).json()
    
    assert_code(response, status.HTTP_200_OK)
    updated_assignment = response["data"]
    assert updated_assignment["title"] == new_title


@pytest.mark.dependency(depends=["test_course_homework_submission_grade_success", "test_course_homework_assignment_update_success"])
def test_course_homework_assignment_delete_success(
    store: Dict,
):
    user_token_teacher = store["user_token_teacher"]
    course_id_base = store["course_id_base"]
    assignment_id_base = store["assignment_id_base"]
    
    response = requests.delete(
        url=f"{SERVER_API_BASE_URL}/course/homework/assignment",
        headers={
            "Access-Token": user_token_teacher,
        },
        params={
            "assignment_id": assignment_id_base,
        },
    ).json()
    
    assert_code(response, status.HTTP_200_OK)
    
    assignments = course_homework_assignment_get_success(
        user_token=user_token_teacher,
        course_id=course_id_base,
    )
    
    assert assignment_id_base not in {assignment["id"] for assignment in assignments}


@pytest.mark.dependency(depends=["test_course_homework_assignment_delete_success"])
def test_course_collaborative_directory_entry_post_success(
    store: Dict,
    temp_file_path: str,
):
    user_token_teacher = store["user_token_teacher"]
    course_id_base = store["course_id_base"]
    
    # 使用二进制模式打开文件
    with open(temp_file_path, "rb") as f:
        file_content = f.read()
    
    # 调试输出
    response = requests.post(
        url=f"{SERVER_API_BASE_URL}/course/collaborative",
        headers={
            "Access-Token": user_token_teacher,
        },
        params={
            "course_id": course_id_base,
        },
        files={
            "file": ("test_file.txt", file_content, "text/plain"),
        },
    )
    
    # 先检查状态码，再尝试解析JSON
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert_code(response_json, status.HTTP_200_OK)
    assert "course_collaborative_directory_entry_id" in response_json["data"]
    store["collab_entry_id"] = response_json["data"]["course_collaborative_directory_entry_id"]


@pytest.mark.dependency(depends=["test_course_collaborative_directory_entry_post_success"])
def test_course_collaborative_directory_entry_get_success(
    store: Dict,
):
    user_token_teacher = store["user_token_teacher"]
    course_id_base = store["course_id_base"]
    collab_entry_id = store["collab_entry_id"]
    
    response = requests.get(
        url=f"{SERVER_API_BASE_URL}/course/collaborative",
        headers={
            "Access-Token": user_token_teacher,
        },
        params={
            "course_id": course_id_base,
        },
    ).json()
    
    assert_code(response, status.HTTP_200_OK)
    assert isinstance(response["data"], list)
    assert collab_entry_id in [int(entry["id"]) for entry in response["data"]]


@pytest.mark.dependency(depends=["test_course_collaborative_directory_entry_post_success"])
def test_course_collaborative_directory_entry_download_success(
    store: Dict,
    temp_file_content: bytes,
):
    user_token_teacher = store["user_token_teacher"]
    course_id_base = store["course_id_base"]
    collab_entry_id = store["collab_entry_id"]
    
    response = requests.get(
        url=f"{SERVER_API_BASE_URL}/course/collaborative/download",
        headers={
            "Access-Token": user_token_teacher,
        },
        params={
            "course_id": course_id_base,
            "course_collaborative_directory_entry_id": collab_entry_id,
        },
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.content == temp_file_content


# 辅助函数：将 bytes 转换为十六进制字符串
def bytes_to_hex(data_bytes: bytes) -> str:
    return data_bytes.hex()

# 辅助函数：将十六进制字符串转换为 bytes
def hex_to_bytes(hex_str: str) -> bytes:
    return bytes.fromhex(hex_str)

# 内联的辅助函数：处理从WebSocket接收到的消息
def process_incoming_ws_message(
    ws_conn: websocket.WebSocket,
    client_ydoc: y_py.YDoc,
    client_current_editors: List[int],
    client_received_messages: List[Dict],
    client_user_id_for_log: int,
    timeout: float = 0.2
) -> Optional[Dict]:
    try:
        ws_conn.settimeout(timeout)
        raw_message = ws_conn.recv()
        message = json.loads(raw_message)
        client_received_messages.append(message)

        if message.get("type") == "update":
            update_bytes = hex_to_bytes(message["update"])
            y_py.apply_update(client_ydoc, update_bytes)
        elif message.get("type") == "user_updated":
            client_current_editors[:] = message.get("editors", [])
        return message
    except websocket.WebSocketTimeoutException:
        return None
    except Exception as e:
        print(f"Client {client_user_id_for_log} receive error: {e}")
        return None

# 尝试接收并处理所有挂起的消息
def drain_client_messages(
    ws_conn: websocket.WebSocket,
    client_ydoc: y_py.YDoc,
    client_current_editors: List[int],
    client_received_messages: List[Dict],
    client_user_id_for_log: int,
    max_attempts=5,
    timeout=0.2
):
    for _ in range(max_attempts):
        if process_incoming_ws_message(
            ws_conn, client_ydoc, client_current_editors, client_received_messages, client_user_id_for_log, timeout
        ) is None:
            break


@pytest.mark.dependency(depends=["test_course_collaborative_directory_entry_get_success"])
def test_course_collaborative_websocket_interaction(
    store: Dict,
    temp_file_content: bytes, # 用于验证初始文档内容是否正确加载
):
    user_token_teacher = store["user_token_teacher"]
    user_id_teacher = store["user_id_teacher"]
    user_token_student = store["user_token_student"]
    user_id_student = store["user_id_student"]
    course_id_base = store["course_id_base"]
    collab_entry_id = store["collab_entry_id"]

    ws_url = f"{SERVER_WS_BASE_URL}/course/collaborative/join?course_id={course_id_base}&course_collaborative_directory_entry_id={collab_entry_id}"

    # 模拟客户端 1 (Student)
    ws_client1: Optional[websocket.WebSocket] = None
    ydoc_client1 = y_py.YDoc()
    ytext_client1 = ydoc_client1.get_text("text")
    current_editors_client1: List[int] = []
    received_messages_client1: List[Dict] = []

    # 模拟客户端 2 (Teacher)
    ws_client2: Optional[websocket.WebSocket] = None
    ydoc_client2 = y_py.YDoc()
    ytext_client2 = ydoc_client2.get_text("text")
    current_editors_client2: List[int] = []
    received_messages_client2: List[Dict] = []

    try:
        # 1. 客户端1 (学生) 连接并同步
        print(f"客户端 {user_id_student} 正在连接...")
        ws_client1 = websocket.WebSocket()
        ws_client1.connect(url=ws_url, header={"Access-Token": user_token_student})
        
        state_vector_c1 = y_py.encode_state_vector(ydoc_client1)
        print(f"客户端 {user_id_student} 正在发送同步请求...")
        ws_client1.send(json.dumps({
            "type": "sync",
            "state_vector": bytes_to_hex(state_vector_c1)
        }))
        
        time.sleep(0.5) 
        drain_client_messages(ws_client1, ydoc_client1, current_editors_client1, received_messages_client1, user_id_student)
        
        assert str(ytext_client1) == temp_file_content.decode("utf-8"), "Client 1 initial content mismatch"
        assert user_id_student in current_editors_client1, "Client 1 not in editors list after connect"
        print(f"客户端 {user_id_student} 初始同步成功。编辑者列表: {current_editors_client1}")

        # 2. 客户端2 (老师) 连接并同步
        print(f"客户端 {user_id_teacher} 正在连接...")
        ws_client2 = websocket.WebSocket()
        ws_client2.connect(url=ws_url, header={"Access-Token": user_token_teacher})

        state_vector_c2 = y_py.encode_state_vector(ydoc_client2)
        print(f"客户端 {user_id_teacher} 正在发送同步请求...")
        ws_client2.send(json.dumps({
            "type": "sync",
            "state_vector": bytes_to_hex(state_vector_c2)
        }))

        time.sleep(0.5)
        drain_client_messages(ws_client2, ydoc_client2, current_editors_client2, received_messages_client2, user_id_teacher)
        # Client 1 也应该收到 client 2 加入的 user_updated 消息
        drain_client_messages(ws_client1, ydoc_client1, current_editors_client1, received_messages_client1, user_id_student)

        assert str(ytext_client2) == temp_file_content.decode("utf-8"), "Client 2 initial content mismatch"
        assert user_id_teacher in current_editors_client2, "Client 2 not in its own editors list"
        assert user_id_student in current_editors_client2, "Client 1 not in Client 2's editors list"
        
        assert user_id_student in current_editors_client1, "Client 1 not in its own updated editors list (after C2 join)"
        assert user_id_teacher in current_editors_client1, "Client 2 not in Client 1's editors list (after C2 join)"
        assert len(current_editors_client1) == 2, f"Client 1 editor list count incorrect: {current_editors_client1}"
        assert len(current_editors_client2) == 2, f"Client 2 editor list count incorrect: {current_editors_client2}"
        print(f"客户端 {user_id_teacher} 初始同步成功。客户端1的编辑者列表: {current_editors_client1}，客户端2的编辑者列表: {current_editors_client2}")


        # 3. 客户端1 发送增量更新
        text_to_insert_c1 = "Update_from_C1 "
        
        # 记录编辑前的状态向量用于生成精确delta
        sv_ydoc_client1_before_edit = y_py.encode_state_vector(ydoc_client1)
        with ydoc_client1.begin_transaction() as txn:
            ytext_client1.insert(txn, 0, text_to_insert_c1) # 在开头插入
        delta_c1 = y_py.encode_state_as_update(ydoc_client1, sv_ydoc_client1_before_edit)# 生成精确delta，实际在前端应由Yjs监听自动生成
        
        print(f"客户端 {user_id_student} 正在发送更新: '{text_to_insert_c1}'")
        ws_client1.send(json.dumps({
            "type": "update",
            "update": bytes_to_hex(delta_c1)
        }))

        time.sleep(0.5) 
        drain_client_messages(ws_client2, ydoc_client2, current_editors_client2, received_messages_client2, user_id_teacher) # Client 2 应该收到 update
        drain_client_messages(ws_client1, ydoc_client1, current_editors_client1, received_messages_client1, user_id_student) # Client 1 可能会收到自己的广播

        expected_content_after_c1 = text_to_insert_c1 + temp_file_content.decode("utf-8")
        assert str(ytext_client1) == expected_content_after_c1, f"Client 1 content incorrect. Expected '{expected_content_after_c1}', got '{str(ytext_client1)}'"
        assert str(ytext_client2) == expected_content_after_c1, f"Client 2 content not updated. Expected '{expected_content_after_c1}', got '{str(ytext_client2)}'"
        print("客户端1的更新已被两个客户端处理完成。")

        # 4. 客户端2 发送增量更新
        text_to_insert_c2 = "Interjection_from_C2 "
        
        sv_ydoc_client2_before_edit = y_py.encode_state_vector(ydoc_client2)
        with ydoc_client2.begin_transaction() as txn:
            ytext_client2.insert(txn, len(text_to_insert_c1), text_to_insert_c2) # 在C1内容之后，原始文件内容之前插入
        delta_c2 = y_py.encode_state_as_update(ydoc_client2, sv_ydoc_client2_before_edit)# 生成精确delta，实际在前端应由Yjs监听自动生成

        print(f"客户端 {user_id_teacher} 正在发送更新: '{text_to_insert_c2}'")
        ws_client2.send(json.dumps({
            "type": "update",
            "update": bytes_to_hex(delta_c2)
        }))

        time.sleep(0.5)
        drain_client_messages(ws_client1, ydoc_client1, current_editors_client1, received_messages_client1, user_id_student) # Client 1 应该收到 update
        drain_client_messages(ws_client2, ydoc_client2, current_editors_client2, received_messages_client2, user_id_teacher) # Client 2 可能会收到自己的广播

        expected_content_final = text_to_insert_c1 + text_to_insert_c2 + temp_file_content.decode("utf-8")
        assert str(ytext_client1) == expected_content_final, f"Client 1 content incorrect after C2 edit. Expected '{expected_content_final}', got '{str(ytext_client1)}'"
        assert str(ytext_client2) == expected_content_final, f"Client 2 content incorrect after its own edit. Expected '{expected_content_final}', got '{str(ytext_client2)}'"
        print("客户端2的更新已被两个客户端处理完成。本地内容验证通过。")

        # 5. 客户端1 断开连接
        print(f"客户端 {user_id_student} 正在断开连接...")
        if ws_client1:
            ws_client1.close()
            ws_client1 = None # Mark as closed
        
        time.sleep(0.5) 
        drain_client_messages(ws_client2, ydoc_client2, current_editors_client2, received_messages_client2, user_id_teacher) # client2 应该收到 user_updated

        assert user_id_teacher in current_editors_client2, "Client 2 not in editors list after Client 1 disconnects"
        assert user_id_student not in current_editors_client2, "Client 1 still in editors list on Client 2 after disconnecting"
        assert len(current_editors_client2) == 1, f"Editors list on Client 2 has incorrect count: {current_editors_client2}"
        print("客户端2已得知客户端1的断开连接。")

    finally:
        print("正在清理WebSocket连接...")
        if ws_client1:
            ws_client1.close()
        if ws_client2:
            ws_client2.close()

    # 6. 数据持久化验证
    print("正在尝试下载最终内容进行持久化验证...")
    download_response = requests.get(
        url=f"{SERVER_API_BASE_URL}/course/collaborative/download",
        headers={"Access-Token": user_token_teacher}, # Teacher token to download
        params={
            "course_id": course_id_base,
            "course_collaborative_directory_entry_id": collab_entry_id,
        },
    )
    assert download_response.status_code == status.HTTP_200_OK
    downloaded_text = download_response.content.decode('utf-8')
    assert downloaded_text == expected_content_final, f"Downloaded content mismatch. Expected '{expected_content_final}', got '{downloaded_text}'"
    print("最终内容持久化验证成功。\ndownloaded_text: ", downloaded_text, "\nexpected_content_final: ", expected_content_final)
    
    # 验证last_updated_by是否被正确更新
    print("正在验证last_updated_by...")
    entry_response = requests.get(
        url=f"{SERVER_API_BASE_URL}/course/collaborative",
        headers={"Access-Token": user_token_teacher},
        params={
            "course_id": course_id_base,
        },
    )
    assert entry_response.status_code == status.HTTP_200_OK
    entries = entry_response.json()["data"]
    target_entry = next((entry for entry in entries if int(entry["id"]) == collab_entry_id), None)
    assert target_entry is not None, "协作条目未找到"
    # 由于客户端2(教师)是最后修改文档的，所以last_updated_by应该是教师ID
    assert int(target_entry["last_updated_by"]) == user_id_teacher, f"last_updated_by值错误。期望：{user_id_teacher}，实际：{target_entry['last_updated_by']}"
    print(f"last_updated_by验证成功,由user_id={target_entry['last_updated_by']}最后更新，教师的user_id={user_id_teacher}")


@pytest.mark.dependency(depends=["test_course_collaborative_websocket_interaction"])
def test_course_collaborative_directory_entry_delete_success(
    store: Dict,
):
    user_token_teacher = store["user_token_teacher"]
    course_id_base = store["course_id_base"]
    collab_entry_id = store["collab_entry_id"]
    
    # 学生尝试删除（应该失败）
    user_token_student = store["user_token_student"]
    response_student = requests.delete(
        url=f"{SERVER_API_BASE_URL}/course/collaborative",
        headers={
            "Access-Token": user_token_student,
        },
        params={
            "course_id": course_id_base,
            "course_collaborative_directory_entry_id": collab_entry_id,
        },
    ).json()
    assert_code(response_student, status.HTTP_403_FORBIDDEN)
    
    # 教师删除（应该成功）
    response_teacher = requests.delete(
        url=f"{SERVER_API_BASE_URL}/course/collaborative",
        headers={
            "Access-Token": user_token_teacher,
        },
        params={
            "course_id": course_id_base,
            "course_collaborative_directory_entry_id": collab_entry_id,
        },
    ).json()
    assert_code(response_teacher, status.HTTP_200_OK)
    
    # 验证已删除
    response_get = requests.get(
        url=f"{SERVER_API_BASE_URL}/course/collaborative",
        headers={
            "Access-Token": user_token_teacher,
        },
        params={
            "course_id": course_id_base,
        },
    ).json()
    assert_code(response_get, status.HTTP_200_OK)
    assert collab_entry_id not in [entry["id"] for entry in response_get["data"]]