import os
import uuid
from typing import Dict, Optional, Sequence

import aiofiles
import aiofiles.os
from fastapi import APIRouter, Depends, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from intellide.config import STORAGE_PATH
from intellide.database.engine import database
from intellide.database.model import Entry, EntryType
from intellide.util.encrypt import jwt_verify
from intellide.util.path import path_normalize, path_split_dir_base_name
from intellide.util.response import ok, bad_request, internal_server_error
from intellide.util.storage import async_write_file, get_file_response

api = APIRouter(prefix="/entry")


@api.get("")
async def entry_get(
        entry_path: str,
        entry_depth: Optional[int] = None,
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwt_verify),
):
    """
    获取文件或目录信息

    参数:
    - entry_path: 文件或目录路径
    - entry_depth: 文件深度（可选）
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回文件或目录信息
    """
    try:
        # 规范化文件路径
        try:
            entry_path = path_normalize(entry_path)
        except:
            return bad_request(message="Invalid entry path")
        # 获取用户 ID
        owner_id = access_info["user_id"]
        # 查询 Entry 记录列表
        query = select(Entry).where(Entry.entry_path.like(f"{entry_path}%"), Entry.owner_id == owner_id)
        # 限制文件深度
        if entry_depth:
            query = query.where(Entry.entry_depth <= entry_depth)
        result = await db.execute(query)
        entries: Sequence[Entry] = result.scalars().all()
        # 返回文件或目录信息
        return ok(data=[entry.dict() for entry in entries])
    except:
        return internal_server_error()


class EntryPostRequest(BaseModel):
    entry_path: str
    entry_type: EntryType
    is_collaborative: bool = False
    file: Optional[UploadFile] = None


@api.post("")
async def entry_post(
        request: EntryPostRequest,
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwt_verify),
):
    """
    上传文件或创建目录

    参数:
    - request: 包含文件或目录信息的 EntryPostRequest 对象(需要为form-data)
    - db: 数据库会话
    - access_info: 访问信息(通过 JWT 验证后的用户信息)

    返回:
    - 成功时返回空响应
    """
    try:
        # 获取用户 ID
        owner_id = access_info["user_id"]
        try:
            await find_entry(request.entry_path, owner_id, db)
        except ValueError as e:
            return bad_request(message=str(e))
        # 验证及自动创建父目录
        await create_parent_directories(request.entry_path, owner_id, db)
        # 创建 Entry 记录
        if request.entry_type == EntryType.FILE:
            # 验证文件是否为空
            if request.file is None:
                return bad_request(message="Missing file")
            # 生成文件别名
            storage_name = uuid.uuid4().hex
            # 异步保存文件到指定目录
            await async_write_file(storage_name, await request.file.read())
            # 创建新的 Entry 记录
            db.add(
                Entry(
                    owner_id=owner_id,
                    entry_type=request.entry_type,
                    entry_path=request.entry_path,
                    storage_name=storage_name,
                    is_collaborative=request.is_collaborative,
                )
            )
        elif request.entry_type == EntryType.DIRECTORY:
            # 创建新的目录 Entry 记录
            db.add(
                Entry(
                    owner_id=owner_id,
                    entry_type=request.entry_type,
                    entry_path=request.entry_path,
                )
            )
        else:
            return internal_server_error()
        # 提交数据库事务
        await db.commit()
        return ok()
    except:
        await db.rollback()
        return internal_server_error()


@api.delete("")
async def entry_delete(
        entry_path: str,
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwt_verify),
):
    """
    删除文件或目录

    参数:
    - entry_path: 文件或目录路径
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回空响应
    """
    try:
        # 规范化文件路径
        owner_id = access_info["user_id"]
        # 寻找文件或目录
        try:
            entry: Entry = await find_entry(entry_path, owner_id, db)
        except ValueError as e:
            return bad_request(message=str(e))
        if entry.entry_type == EntryType.FILE:
            # 删除文件
            await aiofiles.os.remove(os.path.join(STORAGE_PATH, entry.storage_name))
            await db.delete(entry)
        elif entry.entry_type == EntryType.DIRECTORY:
            # 删除目录及其子项
            result = await db.execute(
                select(Entry).where(Entry.entry_path.like(f"{entry_path}%"), Entry.owner_id == owner_id))
            sub_entries: Sequence[Entry] = result.scalars().all()
            for sub_entry in sub_entries:
                if sub_entry.entry_type == EntryType.FILE:
                    await aiofiles.os.remove(os.path.join(STORAGE_PATH, sub_entry.storage_name))
                await db.delete(sub_entry)
        else:
            return internal_server_error()
        # 提交数据库事务
        await db.commit()
        return ok()
    except:
        await db.rollback()
        return internal_server_error()


class EntryMoveRequest(BaseModel):
    entry_path: str
    new_entry_path: str


@api.put("/move")
async def entry_move(
        request: EntryMoveRequest,
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwt_verify),
):
    """
    移动文件或目录

    参数:
    - request: 包含文件或目录移动信息
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回空响应
    """
    try:
        # 验证文件路径是否相同
        if request.entry_path == request.new_entry_path:
            return bad_request(message="Entry path unchanged")
        # 获取用户 ID
        owner_id = access_info["user_id"]
        try:
            entry: Entry = await find_entry(request.entry_path, access_info["user_id"], db)
            new_entry: Entry = await find_entry(request.new_entry_path, access_info["user_id"], db, nullable=True)
            # 断言新路径不存在
            if new_entry is not None:
                return bad_request(message="New entry already exists")
        except ValueError as e:
            return bad_request(message=str(e))
        # 验证及自动创建父目录
        await create_parent_directories(request.new_entry_path, owner_id, db)
        # 移动文件或目录
        if entry.entry_type == EntryType.DIRECTORY:
            result = await db.execute(
                select(Entry).where(Entry.entry_path.like(f"{request.entry_path}%"), Entry.owner_id == owner_id))
            sub_entries: Sequence[Entry] = result.scalars().all()
            for sub_entry in sub_entries:
                sub_entry.entry_path = request.new_entry_path + sub_entry.entry_path[len(request.entry_path):]
        entry.entry_path = request.new_entry_path
        # 提交数据库事务
        await db.commit()
        return ok()
    except:
        await db.rollback()
        return internal_server_error()


@api.get("/download")
async def entry_download(
        entry_path: str,
        db: AsyncSession = Depends(database),
        access_info: Dict = Depends(jwt_verify),
):
    """
    下载文件

    参数:
    - entry_path: 文件路径
    - db: 数据库会话
    - access_info: 访问信息（通过 JWT 验证后的用户信息）

    返回:
    - 成功时返回文件内容
    """
    try:
        # 获取用户 ID
        owner_id = access_info["user_id"]
        try:
            entry: Entry = await find_entry(entry_path, owner_id, db)
        except ValueError as e:
            return bad_request(message=str(e))
        # 验证文件类型
        if entry.entry_type != EntryType.FILE:
            return bad_request(message="Entry is not a file")
        # 获取文件名
        _, file_name = path_split_dir_base_name(entry_path)
        # 返回文件内容
        return get_file_response(entry.storage_name, file_name)
    except:
        return internal_server_error()


async def create_parent_directories(
        entry_path: str,
        owner_id: int,
        db: AsyncSession,
) -> None:
    """
    验证及自动创建父目录

    参数:
    - db: 数据库会话
    - entry_path: 文件或目录路径
    - owner_id: 用户 ID
    """
    path = ""
    for seg in entry_path.strip("/").split("/")[:-1]:
        path += "/" + seg
        result = await db.execute(select(Entry).where(Entry.entry_path == path, Entry.owner_id == owner_id))
        entry: Entry = result.scalar()
        if entry is None:
            db.add(
                Entry(
                    owner_id=owner_id,
                    entry_type=EntryType.DIRECTORY,
                    entry_path=path,
                )
            )
    await db.commit()


async def find_entry(
        entry_path: str,
        owner_id: int,
        db: AsyncSession,
        nullable: bool = False,
) -> Optional[Entry]:
    """
    查询 Entry 记录
    
    参数:
        - entry_path: 文件或目录路径
        - owner_id: 用户 ID
        - db: 数据库会话
        - nullable: 是否允许返回 None
        
    返回:
        - Entry 记录
    """
    # 规范化文件路径
    try:
        entry_path = path_normalize(entry_path)
    except:
        raise ValueError("Invalid entry path")
    # 查询 Entry 记录
    result = await db.execute(select(Entry).where(Entry.entry_path == entry_path, Entry.owner_id == owner_id))
    entry: Entry = result.scalar()
    if not nullable and entry is None:
        raise ValueError("Entry not found")
    return entry
