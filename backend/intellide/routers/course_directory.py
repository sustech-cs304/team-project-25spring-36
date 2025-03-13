from typing import Dict, Sequence, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from intellide.database import database
from intellide.database.model import (
    UserRole,
    CourseDirectoryPermission,
    CourseDirectory,
)
from intellide.routers.course import (
    course_entry_info,
    course_user_info,
)
from intellide.utils.auth import jwe_decode
from intellide.utils.response import ok, forbidden

# 创建课程路由前缀
api = APIRouter(prefix="/course/directory")


@api.get("")
async def course_directory_get(
        course_id: int,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """
    获取课程目录列表

    参数：
        course_id: 课程ID
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        课程所有目录的列表

    异常：
        APIError: 当用户没有权限访问该课程时抛出
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取用户角色和课程信息
    role, course = await course_user_info(
        course_id=course_id,
        user_id=user_id,
        db=db,
    )

    # 如果用户没有权限，返回权限拒绝
    if role is None:
        return forbidden("Permission denied")

    # 查询课程的所有目录
    result = await db.execute(select(CourseDirectory).where(CourseDirectory.course_id == course_id))
    course_directories: Sequence[CourseDirectory] = result.scalars().all()

    # 返回课程目录的列表
    return ok(data=[course_directory.dict() for course_directory in course_directories])


class CourseDirectoryPostRequest(BaseModel):
    """
    创建课程目录请求

    属性：
        course_id: 课程ID
        name: 目录名称
        permission: 目录权限（可选）
    """

    course_id: int  # 课程ID
    name: str  # 目录名称
    permission: Optional[CourseDirectoryPermission] = None  # 目录权限（可选）


@api.post("")
async def course_directory_post(
        request: CourseDirectoryPostRequest,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """
    创建课程目录

    参数：
        request: 包含目录名称和权限的请求对象
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        新建目录的ID

    异常：
        APIError: 当用户不是教师时抛出
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取用户角色和课程信息
    role, course = await course_user_info(
        course_id=request.course_id,
        user_id=user_id,
        db=db,
    )

    # 如果用户不是教师，返回权限拒绝
    if role != UserRole.TEACHER:
        return forbidden("Permission denied")

    # 创建新的课程目录
    course_directory = CourseDirectory(
        course_id=course.id,
        name=request.name,
        permission=request.permission,
    )
    db.add(course_directory)

    # 提交数据库更改
    await db.commit()
    await db.refresh(course_directory)

    # 返回新建目录的ID
    return ok(data={"course_directory_id": course_directory.id})


@api.delete("")
async def course_directory_delete(
        course_directory_id: int,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """
    删除课程目录

    参数：
        course_directory_id: 目录ID
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        删除成功返回OK

    异常：
        APIError: 当用户不是教师时抛出
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取课程和目录信息
    course, course_directory, _ = await course_entry_info(
        db=db,
        course_directory_id=course_directory_id,
    )

    # 获取用户在课程中的角色
    role, _ = await course_user_info(
        course_id=course.id,
        user_id=user_id,
        db=db,
    )

    # 如果用户不是教师，返回权限拒绝
    if role != UserRole.TEACHER:
        return forbidden("Permission denied")

    # 删除课程目录
    await db.delete(course_directory)

    # 提交数据库更改
    await db.commit()

    # 返回成功响应
    return ok()
