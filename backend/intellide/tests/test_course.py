from typing import Dict, Callable

import pytest
import requests
from fastapi import status

from intellide.tests.conftest import SERVER_BASE_URL, unique_string_generator
from intellide.tests.test_user import unique_user_dict_generator, user_register_success
from intellide.tests.utils import assert_code


@pytest.fixture(scope="session", autouse=True)
def init(
        store: Dict,
        unique_user_dict_generator: Callable,
):
    store["user_dict_teacher"] = unique_user_dict_generator()
    store["user_dict_student"] = unique_user_dict_generator()
    store["user_token_teacher"] = user_register_success(store["user_dict_teacher"])
    store["user_token_student"] = user_register_success(store["user_dict_student"])


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
    response = requests.post(
        url=f"{SERVER_BASE_URL}/api/course/student/join",
        headers={
            "Access-Token": user_token_student,
        },
        json={
            "course_id": course_id_base,
        },
    ).json()
    assert_code(response, status.HTTP_200_OK)


@pytest.mark.dependency(depends=["test_course_post_success"])
def test_course_get_success_teacher(
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
def test_course_get_success_student(
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
