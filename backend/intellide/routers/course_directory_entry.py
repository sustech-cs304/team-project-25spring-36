from typing import Dict, Sequence, Optional

from fastapi import APIRouter, Depends, UploadFile, Form, File, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from intellide.database import database
from intellide.database.model import (
    CourseDirectoryPermission,
    CourseDirectoryPermissionType,
    UserRole,
    CourseDirectoryEntry,
    EntryType,
)
from intellide.routers.course import (
    course_user_entry_info,
)
from intellide.storage import (
    storage_name_create,
    storage_write_file,
    storage_get_file_response,
    storage_remove_file,
)
from intellide.utils.auth import jwe_decode
from intellide.utils.path import path_normalize, path_dir_base_name, path_iterate_parents, path_prefix
from intellide.utils.response import forbidden, ok, bad_request, not_implemented, APIError

# 创建课程路由前缀
api = APIRouter(prefix="/course/directory/entry")


@api.post("")
async def course_directory_entry_post(
        course_directory_id: int = Form(...),
        path: str = Form(...),
        file: Optional[UploadFile] = File(None),
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """
    创建课程目录条目

    参数：
        course_directory_id: 课程目录ID
        path: 条目路径
        file: 可选的上传文件
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        新建条目的ID

    异常：
        APIError: 当路径无效或条目已存在时抛出
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取用户角色、课程、目录和条目信息
    user_role, course, course_directory, __ = await course_user_entry_info(db=db,
                                                                           course_directory_id=course_directory_id,
                                                                           user_id=user_id)
    # 规范化路径
    path = path_normalize(path)
    # 如果路径无效，返回错误
    if not path:
        return bad_request("Invalid path")

    # 如果用户是学生，检查权限
    if user_role == UserRole.STUDENT:
        # 检查上一个存在的父目录的作者是否是当前用户
        # 写在了check_if_skip_permission_check_for_upload函数中
        if not await check_if_skip_permission_check_for_upload(db=db, path=path,
                                                               course_directory_id=course_directory.id,
                                                               user_id=user_id):
            if not verify_permissions(
                    path_prefix(path),
                    course_directory.permission,
                    CourseDirectoryPermissionType.UPLOAD,
            ):
                return forbidden("No upload permission")

    # 查询是否已存在相同路径的条目
    result = await db.execute(
        select(CourseDirectoryEntry).where(
            CourseDirectoryEntry.course_directory_id == course_directory.id,
            CourseDirectoryEntry.path == path,
        )
    )
    course_directory_entry: CourseDirectoryEntry = result.scalar()
    # 如果条目已存在，返回错误
    if course_directory_entry:
        return bad_request("Entry already exists")

    # 递归插入父目录
    await insert_course_directory_entry_parent_recursively(
        course_directory_id=course_directory.id,
        user_id=user_id,
        child=path,
        db=db,
    )

    # 如果上传了文件，创建文件条目
    if file is not None:
        storage_name = storage_name_create()
        await storage_write_file(
            storage_name=storage_name,
            content=await file.read(),
        )
        course_directory_entry = CourseDirectoryEntry(
            course_directory_id=course_directory.id,
            author_id=user_id,
            path=path,
            type=EntryType.FILE,
            storage_name=storage_name,
        )
        db.add(course_directory_entry)
    # 如果没有上传文件，创建目录条目
    else:
        course_directory_entry = CourseDirectoryEntry(
            course_directory_id=course_directory.id,
            author_id=user_id,
            path=path,
            type=EntryType.DIRECTORY,
        )
        db.add(course_directory_entry)

    # 提交数据库更改
    await db.commit()
    await db.refresh(course_directory_entry)

    # 返回新建条目的ID
    return ok(data={"course_directory_entry_id": course_directory_entry.id})


@api.get("")
async def course_directory_entry_get(
        course_directory_id: int,
        path: str,
        fuzzy: bool = True,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """
    获取课程目录条目

    参数：
        course_directory_id: 课程目录ID
        path: 条目路径
        fuzzy: 是否模糊匹配路径
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        fuzzy=True时返回所有匹配的条目列表
        fuzzy=False时返回精确匹配的单个条目

    异常：
        APIError: 当用户没有权限或条目不存在时抛出
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取用户角色、课程、目录和条目信息
    role, course, course_directory, _ = await course_user_entry_info(db=db, course_directory_id=course_directory_id,
                                                                     user_id=user_id)

    # 规范化路径
    path = path_normalize(path)

    # 如果是模糊匹配路径
    if fuzzy:
        # 查询所有匹配的条目
        result = await db.execute(
            select(CourseDirectoryEntry).where(
                CourseDirectoryEntry.course_directory_id == course_directory.id,
                CourseDirectoryEntry.path.like(f"{path}%"),
            )
        )
        course_directory_entries: Sequence[CourseDirectoryEntry] = result.scalars().all()
        if not course_directory_entries:
            return bad_request("No entries found")
        if role == UserRole.STUDENT:
            allowed_entrys = []
            # 检查每个条目的权限
            for course_directory_entry in course_directory_entries:
                if course_directory_entry.author_id == user_id or verify_permissions(
                        course_directory_entry.path,
                        course_directory.permission,
                        CourseDirectoryPermissionType.READ,
                ):
                    allowed_entrys.append(course_directory_entry)
            if not allowed_entrys:
                return bad_request("No read permission for all entries in result of fuzzy match")
            # 返回所有匹配的条目列表
            return ok(data=[course_directory_entry.dict() for course_directory_entry in allowed_entrys])
        else:
            return ok(data=[course_directory_entry.dict() for course_directory_entry in course_directory_entries])
    else:
        # 查询精确匹配的条目
        result = await db.execute(
            select(CourseDirectoryEntry).where(
                CourseDirectoryEntry.course_directory_id == course_directory.id,
                CourseDirectoryEntry.path == path,
            )
        )
        course_directory_entry: CourseDirectoryEntry = result.scalar()
        # 如果条目不存在，返回错误
        if not course_directory_entry:
            return bad_request("Course directory entry not found")
        if role == UserRole.STUDENT:
            if course_directory_entry.author_id != user_id:
                if not verify_permissions(
                        course_directory_entry.path,
                        course_directory.permission,
                        CourseDirectoryPermissionType.READ,
                ):
                    return forbidden("No read permission")
        # 返回精确匹配的单个条目
        return ok(data=course_directory_entry.dict())


@api.delete("")
async def course_directory_entry_delete(
        course_directory_entry_id: int,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """
    删除课程目录条目

    参数：
        course_directory_entry_id: 目录条目ID
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        删除成功返回OK

    异常：
        APIError: 当用户没有权限时抛出
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取用户角色、课程、目录和条目信息
    role, course, course_directory, course_directory_entry = await course_user_entry_info(
        db=db, course_directory_entry_id=course_directory_entry_id, user_id=user_id
    )
    # 如果条目不存在，返回错误
    if not course_directory_entry:
        return bad_request("Course directory entry not found")

    # 如果用户是学生，检查权限
    if role == UserRole.STUDENT:
        if course_directory_entry.type == EntryType.FILE:
            if course_directory_entry.author_id != user_id:
                if not verify_permissions(
                        course_directory_entry.path,
                        course_directory.permission,
                        CourseDirectoryPermissionType.DELETE,
                ):
                    return forbidden("No delete permission")
        else:
            # 删除文件夹需要检查文件夹内所有条目都有DELETE权限
            # 如果有一个条目没有DELETE权限，则返回错误
            result = await db.execute(
                select(CourseDirectoryEntry).where(
                    CourseDirectoryEntry.course_directory_id == course_directory.id,
                    CourseDirectoryEntry.path.like(f"{course_directory_entry.path}%"),
                )
            )
            course_directory_entries: Sequence[CourseDirectoryEntry] = result.scalars().all()
            for course_directory_entry in course_directory_entries:
                if course_directory_entry.author_id != user_id:
                    if course_directory_entry.author_id != user_id:
                        if not verify_permissions(
                                course_directory_entry.path,
                                course_directory.permission,
                                CourseDirectoryPermissionType.DELETE,
                        ):
                            return forbidden("No delete permission for some entries in the directory")
    # 删除课程目录条目
    await delete_course_directory_entry(course_directory_entry_id, db)

    # 提交数据库更改
    await db.commit()

    # 返回成功响应
    return ok()


@api.get("/download")
async def course_directory_entry_download(
        course_directory_entry_id: int,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """
    下载课程目录条目文件

    参数：
        course_directory_entry_id: 目录条目ID
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        文件下载响应

    异常：
        APIError: 当用户没有权限或条目不是文件时抛出
    """
    # 获取用户ID
    user_id = access_info["user_id"]

    # 获取用户角色、课程、目录和条目信息
    role, course, course_directory, course_directory_entry = await course_user_entry_info(
        db=db, course_directory_entry_id=course_directory_entry_id, user_id=user_id
    )

    # 如果条目不存在，返回错误
    if not course_directory_entry:
        return bad_request("Course directory entry not found")

    # 如果用户是学生，检查权限
    if role == UserRole.STUDENT:
        if course_directory_entry.author_id != user_id:
            if not verify_permissions(
                    course_directory_entry.path,
                    course_directory.permission,
                    CourseDirectoryPermissionType.READ,
            ):
                return forbidden("No read permission")

    # 如果条目不是文件类型，抛出错误
    if course_directory_entry.type != EntryType.FILE:
        raise HTTPException(status_code=400, detail="Course directory entry is not a file")

    # 获取文件名
    _, file_name = path_dir_base_name(course_directory_entry.path)

    # 返回文件下载响应
    return storage_get_file_response(course_directory_entry.storage_name, file_name)


class CourseDirectoryEntryMoveRequest(BaseModel):
    """
    移动课程目录条目请求

    属性：
        course_directory_entry_id: 要移动的条目ID
        dst_path: 目标路径
    """

    course_directory_entry_id: int  # 要移动的条目ID
    dst_path: str  # 目标路径


@api.put("/move")
async def course_directory_entry_move(
        request: CourseDirectoryEntryMoveRequest,
        access_info: Dict = Depends(jwe_decode),
        db: AsyncSession = Depends(database),
):
    """移动课程目录条目

    参数：
        request: 包含条目ID和目标路径的请求对象
        access_info: 包含用户ID等信息的字典
        db: 数据库会话对象

    返回：
        移动成功返回OK

    异常：
        APIError: 当用户没有权限或目标路径无效时抛出
    """
    # 获取用户ID
    user_id = access_info["user_id"]
    # 规范化目标路径
    request.dst_path = path_normalize(request.dst_path)
    # 如果目标路径无效，返回错误
    if not request.dst_path:
        return bad_request("Invalid destination path")

    # 获取用户角色、课程、目录和条目信息
    role, course, course_directory, course_directory_entry = await course_user_entry_info(
        db=db, course_directory_entry_id=request.course_directory_entry_id, user_id=user_id
    )

    # 如果用户是学生，检查权限
    if role == UserRole.STUDENT:
        if course_directory_entry.author_id != user_id:
            if not verify_permissions(
                    course_directory_entry.path,
                    course_directory.permission,
                    CourseDirectoryPermissionType.DELETE,
            ):
                return forbidden("No delete permission")
        if not await check_if_skip_permission_check_for_upload(db=db, path=request.dst_path,
                                                               course_directory_id=course_directory.id,
                                                               user_id=user_id):
            if not verify_permissions(
                    path_prefix(request.dst_path),
                    course_directory.permission,
                    CourseDirectoryPermissionType.UPLOAD,
            ):
                return forbidden("No upload permission")
    # 获取当前条目的根路径
    root_path = course_directory_entry.path

    # 递归插入目标路径的父目录
    await insert_course_directory_entry_parent_recursively(
        course_directory_id=course_directory.id,
        user_id=user_id,
        child=request.dst_path,
        db=db,
    )

    # 查询所有以根路径开头的条目
    result = await db.execute(
        select(CourseDirectoryEntry).where(
            CourseDirectoryEntry.course_directory_id == course_directory.id,
            CourseDirectoryEntry.path.like(f"{root_path}%")
        )
    )
    course_directory_entries: Sequence[CourseDirectoryEntry] = result.scalars().all()

    # 更新每个条目的路径
    for course_directory_entry in course_directory_entries:
        course_directory_entry.path = request.dst_path + course_directory_entry.path[len(root_path):]

    # 提交数据库更改
    await db.commit()
    return ok()


async def insert_course_directory_entry_parent_recursively(
        course_directory_id: int,
        user_id: int,
        child: str,
        db: AsyncSession,
        commit: bool = False,
) -> None:
    """
    递归插入课程目录的父目录

    参数：
        course_directory_id: 课程目录ID
        child: 子目录路径
        db: 数据库会话对象
        commit: 是否自动提交事务
    """
    # 遍历子目录路径的所有父目录
    for path in path_iterate_parents(child, include_self=False):
        # 查询当前父目录是否已存在
        result = await db.execute(
            select(CourseDirectoryEntry).where(
                CourseDirectoryEntry.course_directory_id == course_directory_id,
                CourseDirectoryEntry.path == path,
            )
        )
        # 如果父目录不存在，则创建新的目录条目
        if result.scalar() is None:
            db.add(
                CourseDirectoryEntry(
                    course_directory_id=course_directory_id,
                    author_id=user_id,
                    path=path,
                    type=EntryType.DIRECTORY,
                )
            )
    # 如果需要提交事务，则提交数据库更改
    if commit:
        await db.commit()


async def delete_course_directory_entry(
        course_directory_entry_id: int,
        db: AsyncSession,
        commit: bool = False,
):
    """
    删除课程目录条目

    参数：
        course_directory_entry_id: 目录条目ID
        db: 数据库会话对象
        commit: 是否自动提交事务

    异常：
        APIError: 当条目不存在或类型未实现时抛出
    """
    # 查询要删除的目录条目
    result = await db.execute(select(CourseDirectoryEntry).where(CourseDirectoryEntry.id == course_directory_entry_id))
    course_directory_entry: CourseDirectoryEntry = result.scalar()

    # 如果条目不存在，抛出错误
    if not course_directory_entry:
        raise APIError(bad_request, "Course directory entry not found")

    # 如果条目是文件类型，删除存储中的文件并删除数据库记录
    if course_directory_entry.type == EntryType.FILE:
        await storage_remove_file(course_directory_entry.storage_name)  # 删除存储中的文件
        await db.delete(course_directory_entry)  # 删除数据库记录

    # 如果条目是目录类型，删除目录及其所有子条目
    elif course_directory_entry.type == EntryType.DIRECTORY:
        path = course_directory_entry.path
        result = await db.execute(
            select(CourseDirectoryEntry).where(
                CourseDirectoryEntry.course_directory_id == course_directory_entry.course_directory_id,
                CourseDirectoryEntry.path.like(f"{path}%")
            )
        )
        # 删除所有匹配的子条目
        for entry in result.scalars().all():
            await db.delete(entry)

    # 如果条目类型未实现，抛出错误
    else:
        raise APIError(not_implemented, "Not implemented")

    # 如果需要提交事务，提交数据库更改
    if commit:
        await db.commit()


def verify_permissions(
        entry_path: str,
        permissions: CourseDirectoryPermission,
        needed_permission_type: CourseDirectoryPermissionType
) -> bool:
    """
    检查用户是否对共享目录中的指定条目路径具有某种权限。
    
    参数:
        entry_path: 要检查的条目路径
        permissions: 路径到权限的映射字典
        needed_permission_type: 需要的权限类型
        
    返回:
        如果用户具有需要的权限则返回True，否则返回False
    """
    # 检查条目路径本身是否有显式权限
    if entry_path in permissions:
        # 将字符串权限值转换为枚举类型进行比较
        entry_permissions = permissions[entry_path]
        if str(needed_permission_type) not in entry_permissions:
            return False
    # 递归检查父路径
    current_path = entry_path
    while current_path != "":
        # 获取父路径
        current_path = path_prefix(current_path)
        if current_path in permissions:
            # 将字符串权限值转换为枚举类型进行比较
            entry_permissions = permissions[current_path]
            if str(needed_permission_type) not in entry_permissions:
                return False
            break
    return True


async def check_if_skip_permission_check_for_upload(
        path: str,
        course_directory_id: int,
        user_id: int,
        db: AsyncSession,
) -> bool:
    """
    在用户是学生时，检查上传操作是否可以跳过权限检查

    参数:
        path: 要检查的条目路径
        course_directory_id: 课程目录ID
        user_id: 用户ID
        db: 数据库会话对象

    返回:
        如果可以跳过权限检查则返回True，否则返回False
    """
    for parent in path_iterate_parents(path, include_self=False):
        # 查询当前父目录是否已存在
        temp_result = await db.execute(
            select(CourseDirectoryEntry).where(
                CourseDirectoryEntry.course_directory_id == course_directory_id,
                CourseDirectoryEntry.path == parent,
            )
        )
        # 直到找到第一个存在的的父目录
        if temp_result.scalar() is not None:
            if temp_result.scalar().author_id == user_id:
                # 比如创建/a/b/c/d.txt,但现在只有a存在,
                # b和c还没有被创建,那我需要去检测a的作者是否是当前用户
                # 如果a的作者是当前用户,可以跳过权限检查
                return True
            else:
                return False
    return False
