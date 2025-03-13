from typing import Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from intellide.database import database
from intellide.database.model import (
    CourseStudent,
    UserRole,
    User,
)
from intellide.routers.course import (
    course_user_info,
)
from intellide.utils.auth import jwe_decode
from intellide.utils.response import ok, bad_request, forbidden

# 创建课程路由前缀
api = APIRouter(prefix="/course/student")


@api.get("")
async def course_student_get(
        course_id: int,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """获取课程学生列表

    参数：
        course_id: 课程ID
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        课程中所有学生的信息列表

    异常：
        APIError: 当用户没有权限访问该课程时抛出
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取用户角色和课程信息
    role, _ = await course_user_info(course_id, user_id, db)

    # 如果用户没有权限，返回权限拒绝
    if role is None:
        return forbidden("Permission denied")

    # 查询课程的所有学生
    result = await db.execute(select(CourseStudent).where(CourseStudent.course_id == course_id))
    users = []

    # 获取每个学生的信息
    for course_student in result.scalars().all():
        result = await db.execute(select(User).where(User.id == course_student.student_id))
        user: User = result.scalar()
        users.append(user)

    # 返回学生信息列表
    return ok(data=[user.dict() for user in users])


class CourseStudentJoinRequest(BaseModel):
    """学生加入课程请求

    属性：
        course_id: 课程ID
    """

    course_id: int  # 课程ID


@api.post("/join")
async def course_student_join(
        request: CourseStudentJoinRequest,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """学生加入课程

    参数：
        request: 包含课程ID的请求对象
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        新建的选课记录ID

    异常：
        APIError: 当学生已加入该课程时抛出
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取用户角色和课程信息
    role, course = await course_user_info(
        course_id=request.course_id,
        user_id=user_id,
        db=db,
    )

    # 如果用户已加入该课程，返回错误
    if role is not None:
        return bad_request("Already joined")

    # 创建新的选课记录
    course_student = CourseStudent(
        course_id=course.id,
        student_id=user_id,
    )
    db.add(course_student)

    # 提交数据库更改
    await db.commit()
    await db.refresh(course_student)

    # 返回新建的选课记录ID
    return ok(data={"course_student_id": course_student.id})


@api.delete("")
async def course_student_delete(
        course_id: int,
        course_student_id: Optional[int] = None,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """退出课程或将学生移出课程

    参数：
        course_id: 课程ID
        course_student_id: 选课记录ID(教师操作时需要)
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        退出成功返回OK

    异常：
        APIError: 当用户权限不足或记录不存在时抛出
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取用户角色和课程信息
    role, course = await course_user_info(
        course_id=course_id,
        user_id=user_id,
        db=db,
    )

    # 如果用户是教师
    if role == UserRole.TEACHER:
        # 如果没有提供选课记录ID，返回错误
        if course_student_id is None:
            return bad_request("Course student id is required")
        # 查询选课记录
        result = await db.execute(
            select(CourseStudent).where(
                CourseStudent.id == course_student_id,
            )
        )
        course_student: CourseStudent = result.scalar()
    # 如果用户是学生
    elif role == UserRole.STUDENT:
        # 查询该学生的选课记录
        result = await db.execute(
            select(CourseStudent).where(
                CourseStudent.course_id == course_id,
                CourseStudent.student_id == user_id,
            )
        )
        course_student: CourseStudent = result.scalar()
    # 如果用户没有权限
    else:
        return forbidden("Permission denied")

    # 删除选课记录
    await db.delete(course_student)
    # 提交数据库更改
    await db.commit()
    # 返回成功响应
    return ok()
