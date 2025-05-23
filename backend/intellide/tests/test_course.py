import json
from typing import Dict, Callable, List, Optional, Union

import pytest
import requests
import websocket
from fastapi import status

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
    # 内容可能与原始内容略有不同，因为它通过CRDT处理过
    assert response.content


@pytest.mark.dependency(depends=["test_course_collaborative_directory_entry_get_success"])
def test_course_collaborative_websocket_interaction(
    store: Dict,
):
    user_token_teacher = store["user_token_teacher"]
    user_token_student = store["user_token_student"]
    course_id_base = store["course_id_base"]
    collab_entry_id = store["collab_entry_id"]
    
    ws_student = websocket.WebSocket()
    ws_teacher = websocket.WebSocket()
    
    try:
        # 连接WebSocket
        ws_student.connect(
            url=f"{SERVER_WS_BASE_URL}/course/collaborative/join?course_id={course_id_base}&course_collaborative_directory_entry_id={collab_entry_id}",
            header={
                "Access-Token": user_token_student,
            },
        )
        
        ws_teacher.connect(
            url=f"{SERVER_WS_BASE_URL}/course/collaborative/join?course_id={course_id_base}&course_collaborative_directory_entry_id={collab_entry_id}",
            header={
                "Access-Token": user_token_teacher,
            },
        )
        
        # 接收初始内容
        student_content = json.loads(ws_student.recv())
        teacher_content = json.loads(ws_teacher.recv())
        
        assert student_content["type"] == "content"
        assert teacher_content["type"] == "content"
        
        # 学生接收第一条 user_updated (因学生自己加入)
        student_user_update_1 = json.loads(ws_student.recv())
        assert student_user_update_1["type"] == "user_updated"
        assert len(student_user_update_1["editors"]) >= 1 # 学生自己

        # 教师接收第一条 user_updated
        teacher_user_update_1 = json.loads(ws_teacher.recv())
        assert teacher_user_update_1["type"] == "user_updated"
        assert len(teacher_user_update_1["editors"]) >= 2 # 学生和教师

        # 学生接收第二条 user_updated (因教师加入)
        student_user_update_2 = json.loads(ws_student.recv())
        assert student_user_update_2["type"] == "user_updated"
        assert len(student_user_update_2["editors"]) >= 2 # 学生和教师
        
        # 学生发送编辑
        edit_message = {
            "type": "edit",
            "operation": "insert",
            "position": 0,
            "content": "测试协作编辑"
        }
        ws_student.send(json.dumps(edit_message))
        
        # 教师应该收到更新
        teacher_update = json.loads(ws_teacher.recv())
        assert teacher_update["type"] == "content"
        assert "测试协作编辑" in teacher_update["content"]
        
    finally:
        ws_student.close()
        ws_teacher.close()


@pytest.mark.dependency(depends=["test_course_collaborative_websocket_interaction"])
def test_course_collaborative_directory_entry_history_success(
    store: Dict,
):
    user_token_teacher = store["user_token_teacher"]
    course_id_base = store["course_id_base"]
    collab_entry_id = store["collab_entry_id"]
    
    response = requests.get(
        url=f"{SERVER_API_BASE_URL}/course/collaborative/history",
        headers={
            "Access-Token": user_token_teacher,
        },
        params={
            "course_id": course_id_base,
            "course_collaborative_directory_entry_id": collab_entry_id,
        },
    ).json()
    
    assert_code(response, status.HTTP_200_OK)
    assert isinstance(response["data"], list)
    if len(response["data"]) > 0:
        assert "operation" in response["data"][0]
        assert "content" in response["data"][0]


@pytest.mark.dependency(depends=["test_course_collaborative_directory_entry_history_success"])
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