from typing import Dict, Sequence, List, Optional, Tuple

from fastapi import APIRouter, Depends, UploadFile, Form, File, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from intellide.database.database import database
from intellide.database.model import (
    Course, CourseStudent, UserRole, CourseDirectoryPermission, CourseDirectory, CourseDirectoryEntry, EntryType
)
from intellide.storage.storage import generate_storage_name, async_write_file, get_file_response
from intellide.utils.auth import jwe_decode
from intellide.utils.path import path_normalize, path_iterate_parents, path_dir_base_name
from intellide.utils.response import ok, bad_request, forbidden, not_implemented, APIError

api = APIRouter(prefix="/course")


@api.get("")
async def course_get(
        role: UserRole,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    if role == UserRole.TEACHER:
        user_id = access_info["user_id"]
        result = await db.execute(select(Course).where(Course.owner_id == user_id))
        courses: Sequence[Course] = result.scalars().all()
        return ok(
            data=[
                course.dict() for course in courses
            ]
        )
    elif role == UserRole.STUDENT:
        user_id = access_info["user_id"]
        result = await db.execute(select(CourseStudent).where(CourseStudent.student_id == user_id))
        course_students: Sequence[CourseStudent] = result.scalars().all()
        courses: List[Course] = []
        for course_student in course_students:
            result = await db.execute(select(Course).where(Course.id == course_student.course_id))
            course: Course = result.scalar()
            courses.append(course)
        return ok(
            data=[
                course.dict() for course in courses
            ]
        )
    else:
        return not_implemented("Not implemented")


class CoursePostRequest(BaseModel):
    name: str
    description: str


@api.post("")
async def course_post(
        request: CoursePostRequest,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    user_id = access_info["user_id"]
    course = Course(
        owner_id=user_id,
        name=request.name,
        description=request.name,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return ok(
        data={
            "course_id": course.id
        }
    )


@api.delete("")
async def course_delete(
        course_id: int,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    user_id = access_info["user_id"]
    role, course = await course_user_info(
        course_id=course_id,
        user_id=user_id,
        db=db,
    )
    if role != UserRole.TEACHER:
        return forbidden("Permission denied")
    await db.delete(course)
    await db.commit()
    return ok()


@api.get("/student")
async def course_student_get(
        course_id: int,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    user_id = access_info["user_id"]
    role, _ = course_user_info(course_id, user_id, db)
    if role is None:
        return forbidden("Permission denied")
    result = await db.execute(
        select(CourseStudent).where(
            CourseStudent.course_id == course_id
        )
    )
    return ok(
        data=[
            course_student.dict() for course_student in result.scalars().all()
        ]
    )


class CourseStudentJoinRequest(BaseModel):
    course_id: int


@api.post("/student/join")
async def course_student_join(
        request: CourseStudentJoinRequest,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    user_id = access_info["user_id"]
    role, course = await course_user_info(
        course_id=request.course_id,
        user_id=user_id,
        db=db,
    )
    if role is not None:
        return bad_request("Already joined")
    course_student = CourseStudent(
        course_id=course.id,
        student_id=user_id,
    )
    db.add(course_student)
    await db.commit()
    return ok()


@api.delete("/student/kick")
async def course_student_kick(
        course_id: int,
        student_id: Optional[int] = None,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    user_id = access_info["user_id"]
    result = await db.execute(
        select(Course).where(
            Course.id == course_id,
        )
    )
    course: Course = result.scalar()
    if not course:
        return bad_request("Course not found")
    if student_id:
        # 踢出指定学生
        if course.owner_id != user_id:
            return forbidden("Permission denied")
        course_student = await select_course_student(
            course_id=course_id,
            student_id=student_id,
            db=db,
        )
    else:
        # 退出课程
        course_student = await select_course_student(
            course_id=course_id,
            student_id=user_id,
            db=db,
        )
    await db.delete(course_student)
    await db.commit()
    return ok()


@api.get("/directory")
async def course_directory_get(
        course_id: int,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    user_id = access_info["user_id"]
    role, course = await course_user_info(
        course_id=course_id,
        user_id=user_id,
        db=db,
    )
    if role is None:
        return forbidden("Permission denied")
    result = await db.execute(select(CourseDirectory).where(CourseDirectory.course_id == course_id))
    course_directories: Sequence[CourseDirectory] = result.scalars().all()
    return ok(
        data=[
            course_directory.dict() for course_directory in course_directories
        ]
    )


class CourseDirectoryPostRequest(BaseModel):
    course_id: int
    name: str
    permission: Optional[CourseDirectoryPermission] = None


@api.post("/directory")
async def course_directory_post(
        request: CourseDirectoryPostRequest,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    user_id = access_info["user_id"]
    role, course = await course_user_info(
        course_id=request.course_id,
        user_id=user_id,
        db=db,
    )
    if role != UserRole.TEACHER:
        return forbidden("Permission denied")
    course_directory = CourseDirectory(
        course_id=course.id,
        name=request.name,
        permission=request.permission,
    )
    db.add(course_directory)
    await db.commit()
    return ok()


@api.delete("/directory")
async def course_directory_delete(
        course_directory_id: int,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    user_id = access_info["user_id"]
    course, course_directory, _ = await course_entry_info(
        db=db,
        course_directory_id=course_directory_id,
    )
    role, _ = await course_user_info(
        course_id=course.id,
        user_id=user_id,
        db=db,
    )
    if role != UserRole.TEACHER:
        return forbidden("Permission denied")
    await db.delete(course_directory)
    await db.commit()
    return ok()


class CourseDirectoryEntryPostRequest(BaseModel):
    course_id: int
    course_directory_id: int
    path: str


@api.post("/directory/entry")
async def course_directory_entry_post(
        course_directory_id: int = Form(...),
        path: str = Form(...),
        file: Optional[UploadFile] = File(None),
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    user_id = access_info["user_id"]
    user_role, course, course_directory, __ = await course_info(
        db=db,
        course_directory_id=course_directory_id,
        user_id=user_id
    )
    if user_role is None:
        return forbidden("Permission denied")
    if user_role == UserRole.STUDENT:
        ...  # TODO: check permission
    path = path_normalize(path)
    result = await db.execute(
        select(CourseDirectoryEntry).where(
            CourseDirectoryEntry.course_directory_id == course_directory.id,
            CourseDirectoryEntry.path == path,
        )
    )
    course_directory_entry: CourseDirectoryEntry = result.scalar()
    if course_directory_entry:
        return bad_request("Entry already exists")
    await insert_course_directory_entry_parent_recursively(
        course_directory_id=course_directory.id,
        child=path,
        db=db,
    )
    if file is not None:
        storage_name = generate_storage_name()
        await async_write_file(
            storage_name=storage_name,
            content=await file.read(),
        )
        course_directory_entry = CourseDirectoryEntry(
            course_directory_id=course_directory.id,
            path=path,
            type=EntryType.FILE,
            storage_name=storage_name,
            is_collaborative=False,
        )
        db.add(course_directory_entry)
    else:
        course_directory_entry = CourseDirectoryEntry(
            course_directory_id=course_directory.id,
            path=path,
            type=EntryType.DIRECTORY,
        )
        db.add(course_directory_entry)
    await db.commit()
    return ok()


@api.delete("/directory/entry")
async def course_directory_entry_delete(
        course_directory_entry_id: int,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    user_id = access_info["user_id"]
    role, course, course_directory, course_directory_entry = await course_info(
        db=db,
        course_directory_entry_id=course_directory_entry_id,
        user_id=user_id
    )
    if role is None:
        return forbidden("Permission denied")
    if role == UserRole.STUDENT:
        ...  # TODO: check permission
    path = course_directory_entry.path
    result = await db.execute(
        select(CourseDirectoryEntry).where(
            CourseDirectoryEntry.course_directory_id == course_directory.id,
            CourseDirectoryEntry.path.like(f"{path}%")
        )
    )
    for course_directory_entry in result.scalars().all():
        await db.delete(course_directory_entry)
    await db.commit()
    return ok()


@api.get("/directory/entry/download")
async def course_directory_entry_download(
        course_directory_entry_id: int,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    user_id = access_info["user_id"]
    role, course, course_directory, course_directory_entry = await course_info(
        db=db,
        course_directory_entry_id=course_directory_entry_id,
        user_id=user_id
    )
    if role is None:
        return forbidden("Permission denied")
    if role == UserRole.STUDENT:
        ...  # TODO: check permission
    if course_directory_entry.type != EntryType.FILE:
        raise HTTPException(status_code=400, detail="Course directory entry is not a file")
    _, file_name = path_dir_base_name(course_directory_entry.path)
    return get_file_response(course_directory_entry.storage_name, file_name)


class CourseDirectoryEntryMoveRequest(BaseModel):
    course_directory_entry_id: int
    dst_path: str


@api.put("/directory/entry/move")
async def course_directory_entry_move(
        request: CourseDirectoryEntryMoveRequest,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    user_id = access_info["user_id"]
    request.dst_path = path_normalize(request.dst_path)
    role, course, course_directory, course_directory_entry = await course_info(
        db=db,
        course_directory_entry_id=request.course_directory_entry_id,
        user_id=user_id
    )
    if role is None:
        return forbidden("Permission denied")
    elif role == UserRole.STUDENT:
        ...  # TODO: check permission
    src_path = course_directory_entry.path
    await insert_course_directory_entry_parent_recursively(
        course_directory_id=course_directory.id,
        child=request.dst_path,
        db=db,
    )
    result = await db.execute(
        select(CourseDirectoryEntry).where(
            CourseDirectoryEntry.course_directory_id == course_directory.id,
            CourseDirectoryEntry.path.like(f"{request.dst_path}%")
        )
    )
    for course_directory_entry in result.scalars().all():
        course_directory_entry.path = request.dst_path + course_directory_entry.path[len(src_path):]
    await db.commit()
    return ok()


async def select_course_student(
        course_id: int,
        student_id: int,
        db: AsyncSession,
        nullable: bool = False
) -> CourseStudent:
    result = await db.execute(
        select(CourseStudent).where(
            CourseStudent.course_id == course_id,
            CourseStudent.student_id == student_id,
        )
    )
    course_student: CourseStudent = result.scalar()
    if not nullable and not course_student:
        raise APIError(bad_request, "Course student not found")
    return course_student


async def course_user_info(
        course_id: int,
        user_id: int,
        db: AsyncSession,
) -> Tuple[Optional[UserRole], Course]:
    result = await db.execute(
        select(Course).where(
            Course.id == course_id,
        )
    )
    course: Course = result.scalar()
    if not course:
        raise APIError(bad_request, "Course not found")
    if course.owner_id == user_id:
        return UserRole.TEACHER, course
    result = await db.execute(
        select(CourseStudent).where(
            CourseStudent.student_id == user_id,
            CourseStudent.course_id == course_id,
        )
    )
    course_student: CourseStudent = result.scalar()
    if course_student:
        return UserRole.STUDENT, course
    return None, course


async def course_entry_info(
        db: AsyncSession,
        course_directory_entry_id: Optional[int] = None,
        course_directory_id: Optional[int] = None,
        course_id: Optional[int] = None,
) -> Tuple[Optional[Course], Optional[CourseDirectory], Optional[CourseDirectoryEntry]]:
    if course_directory_entry_id:
        result = await db.execute(
            select(CourseDirectoryEntry).where(
                CourseDirectoryEntry.id == course_directory_entry_id,
            )
        )
        course_directory_entry: Optional[CourseDirectoryEntry] = result.scalar()
        if not course_directory_entry:
            raise APIError(bad_request, "Course directory entry not found")
        course_directory_id = course_directory_entry.course_directory_id
    else:
        course_directory_entry = None
    if course_directory_id:
        result = await db.execute(
            select(CourseDirectory).where(
                CourseDirectory.id == course_directory_id
            )
        )
        course_directory: Optional[CourseDirectory] = result.scalar()
        if not course_directory:
            raise APIError(bad_request, "Course directory not found")
        course_id = course_directory.course_id
    else:
        course_directory = None
    if course_id:
        result = await db.execute(
            select(Course).where(
                Course.id == course_id
            )
        )
        course: Optional[Course] = result.scalar()
        if not course:
            raise APIError(bad_request, "Course not found")
    else:
        course = None
    return course, course_directory, course_directory_entry


async def course_info(
        db: AsyncSession,
        user_id: int,
        course_id: Optional[int] = None,
        course_directory_id: Optional[int] = None,
        course_directory_entry_id: Optional[int] = None,
) -> Tuple[
    Optional[UserRole], Course, Optional[CourseDirectory], Optional[CourseDirectoryEntry]]:
    course, course_directory, course_directory_entry = await course_entry_info(
        db=db,
        course_id=course_id,
        course_directory_id=course_directory_id,
        course_directory_entry_id=course_directory_entry_id,
    )
    user_role, course = await course_user_info(
        course_id=course.id,
        user_id=user_id,
        db=db,
    )
    return user_role, course, course_directory, course_directory_entry,


async def insert_course_directory_entry_parent_recursively(
        course_directory_id: int,
        child: str,
        db: AsyncSession,
        commit: bool = False,
) -> None:
    """
    验证及自动创建父目录

    参数:
    - db: 数据库会话
    - entry_path: 文件或目录路径
    - owner_id: 用户 ID
    """
    for child in path_iterate_parents(child, include_self=False):
        result = await db.execute(
            select(CourseDirectoryEntry).where(
                CourseDirectoryEntry.course_directory_id == course_directory_id,
                CourseDirectoryEntry.path == child,
            )
        )
        if result.scalar() is None:
            db.add(
                CourseDirectoryEntry(
                    course_directory_id=course_directory_id,
                    path=child,
                    type=EntryType.DIRECTORY,
                )
            )
    if commit:
        await db.commit()
