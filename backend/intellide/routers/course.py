from typing import Dict, Sequence, List, Optional, Tuple

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from intellide.database import database
from intellide.database.model import (
    Course,
    CourseStudent,
    UserRole,
    CourseDirectory,
    CourseDirectoryEntry,
)
from intellide.utils.auth import jwe_decode
from intellide.utils.response import ok, bad_request, forbidden, not_implemented, APIError

# 创建课程路由前缀
api = APIRouter(prefix="/course")


@api.get("")
async def course_get(
        role: UserRole,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """获取课程列表

    参数：
        role: 用户角色(教师/学生)
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        教师: 返回创建的所有课程
        学生: 返回加入的所有课程

    异常：
        APIError: 当用户没有权限访问该课程时抛出
    """
    # 如果是教师角色
    if role == UserRole.TEACHER:
        # 获取教师ID
        user_id = access_info["user_id"]
        # 查询该教师创建的所有课程
        result = await db.execute(select(Course).where(Course.teacher_id == user_id))
        courses: Sequence[Course] = result.scalars().all()
        # 返回教师创建的所有课程
        return ok(data=[course.dict() for course in courses])

    # 如果是学生角色
    elif role == UserRole.STUDENT:
        user_id = access_info["user_id"]
        # 查询该学生的所有选课记录
        result = await db.execute(select(CourseStudent).where(CourseStudent.student_id == user_id))
        course_students: Sequence[CourseStudent] = result.scalars().all()
        courses: List[Course] = []
        # 获取每个选课记录对应的课程信息
        for course_student in course_students:
            result = await db.execute(select(Course).where(Course.id == course_student.course_id))
            course: Course = result.scalar()
            courses.append(course)
        # 返回学生加入的所有课程
        return ok(data=[course.dict() for course in courses])

    # 如果角色未实现，返回未实现错误
    else:
        return not_implemented("Not implemented")


# 课程创建请求的数据模型
class CoursePostRequest(BaseModel):
    """
    课程创建请求

    属性：
        name: 课程名称
        description: 课程描述
    """

    name: str  # 课程名称
    description: str  # 课程描述


@api.post("")
async def course_post(
        request: CoursePostRequest,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """
    创建新课程

    参数：
        request: 包含课程名称和描述的请求对象
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    异常：
        新创建的课程ID
    """
    # 获取创建者ID
    user_id = access_info["user_id"]
    # 创建新课程记录
    course = Course(
        teacher_id=user_id,
        name=request.name,
        description=request.name,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return ok(data={"course_id": course.id})


@api.delete("")
async def course_delete(
        course_id: int,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """
    删除课程

    参数：
        course_id: 要删除的课程ID
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        删除成功返回OK

    异常：
        APIError: 当用户不是教师或课程不存在时抛出
    """
    # 获取用户ID
    user_id = access_info["user_id"]
    # 检查用户权限和课程是否存在
    role, course = await course_user_info(
        course_id=course_id,
        user_id=user_id,
        db=db,
    )
    # 只有教师可以删除课程
    if role != UserRole.TEACHER:
        return forbidden("Permission denied")
    # 删除课程记录
    await db.delete(course)
    await db.commit()
    return ok()


async def course_user_info(
        course_id: int,
        user_id: int,
        db: AsyncSession,
) -> Tuple[Optional[UserRole], Course]:
    """
    获取用户在课程中的角色信息

    参数：
        course_id: 课程ID
        user_id: 用户ID
        db: 数据库会话对象

    返回：
        元组(用户角色, 课程对象)

    异常：
        APIError: 当课程不存在时抛出
    """
    # 查询课程是否存在
    result = await db.execute(
        select(Course).where(
            Course.id == course_id,
        )
    )
    course: Course = result.scalar()
    # 如果课程不存在，抛出错误
    if not course:
        raise APIError(bad_request, "Course not found")

    # 检查用户是否是该课程的教师
    if course.teacher_id == user_id:
        return UserRole.TEACHER, course

    # 检查用户是否是该课程的学生
    result = await db.execute(
        select(CourseStudent).where(
            CourseStudent.student_id == user_id,
            CourseStudent.course_id == course_id,
        )
    )
    course_student: CourseStudent = result.scalar()
    # 如果用户是学生，返回学生角色
    if course_student:
        return UserRole.STUDENT, course

    # 如果用户既不是教师也不是学生，返回None
    return None, course


async def course_entry_info(
        db: AsyncSession,
        course_directory_entry_id: Optional[int] = None,
        course_directory_id: Optional[int] = None,
        course_id: Optional[int] = None,
) -> Tuple[Optional[Course], Optional[CourseDirectory], Optional[CourseDirectoryEntry]]:
    """获取课程条目相关信息

    参数：
        db: 数据库会话对象
        course_directory_entry_id: 目录条目ID
        course_directory_id: 目录ID
        course_id: 课程ID

    返回：
        元组(课程对象, 目录对象, 条目对象)

    异常：
        APIError: 当相关对象不存在时抛出
    """
    # 如果提供了目录条目ID，则查询该条目信息
    if course_directory_entry_id:
        result = await db.execute(
            select(CourseDirectoryEntry).where(
                CourseDirectoryEntry.id == course_directory_entry_id,
            )
        )
        course_directory_entry: Optional[CourseDirectoryEntry] = result.scalar()
        # 如果条目不存在，抛出错误
        if not course_directory_entry:
            raise APIError(bad_request, "Course directory entry not found")
        # 获取目录ID
        course_directory_id = course_directory_entry.course_directory_id
    else:
        course_directory_entry = None

    # 如果提供了目录ID，则查询该目录信息
    if course_directory_id:
        result = await db.execute(select(CourseDirectory).where(CourseDirectory.id == course_directory_id))
        course_directory: Optional[CourseDirectory] = result.scalar()
        # 如果目录不存在，抛出错误
        if not course_directory:
            raise APIError(bad_request, "Course directory not found")
        # 获取课程ID
        course_id = course_directory.course_id
    else:
        course_directory = None

    # 如果提供了课程ID，则查询该课程信息
    if course_id:
        result = await db.execute(select(Course).where(Course.id == course_id))
        course: Optional[Course] = result.scalar()
        # 如果课程不存在，抛出错误
        if not course:
            raise APIError(bad_request, "Course not found")
    else:
        course = None

    # 返回课程、目录和条目信息
    return course, course_directory, course_directory_entry


async def course_user_entry_info(
        db: AsyncSession,
        user_id: int,
        course_id: Optional[int] = None,
        course_directory_id: Optional[int] = None,
        course_directory_entry_id: Optional[int] = None,
) -> Tuple[Optional[UserRole], Course, Optional[CourseDirectory], Optional[CourseDirectoryEntry]]:
    """
    获取课程及相关信息

    参数：
        db: 数据库会话对象
        user_id: 用户ID
        course_id: 课程ID(可选)
        course_directory_id: 目录ID(可选)
        course_directory_entry_id: 条目ID(可选)

    返回：
        元组(用户角色, 课程对象, 目录对象, 条目对象)

    异常：
        APIError: 当用户没有权限时抛出
    """
    # 获取课程、目录和条目信息
    course, course_directory, course_directory_entry = await course_entry_info(
        db=db,
        course_id=course_id,
        course_directory_id=course_directory_id,
        course_directory_entry_id=course_directory_entry_id,
    )

    # 检查用户在该课程中的角色
    user_role, course = await course_user_info(
        course_id=course.id,
        user_id=user_id,
        db=db,
    )

    # 如果用户没有任何角色(既不是教师也不是学生)，则拒绝访问
    if user_role is None:
        raise APIError(forbidden, "Permission denied")

    # 返回用户角色、课程、目录和条目信息
    return (
        user_role,
        course,
        course_directory,
        course_directory_entry,
    )
