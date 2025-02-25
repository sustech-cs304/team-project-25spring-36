import uuid
import aiofiles
import aiofiles.os
import os

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Dict, Optional, List, LiteralString

from backend.util.encrypt import jwt_verify
from backend.util.response import ok, bad_request, internal_server_error
from backend.util.path import path_normalize
from backend.database.engine import database
from backend.database.model import Entry, EntryType
from backend.config import ENTRY_STORAGE_PATH

api = APIRouter(prefix="/entry")


@api.get("")
async def entry_get(
    entry_path: LiteralString,
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
        entry_path = path_normalize(entry_path)
        if not entry_path:
            return bad_request(message="Invalid entry path")
        # 获取用户 ID
        owner_id = access_info["user_id"]
        # 查询 Entry 记录列表
        query = select(Entry).where(Entry.entry_path.like(f"{entry_path}%"), Entry.owner_id == owner_id)
        # 限制文件深度
        if entry_depth:
            query = query.where(Entry.entry_depth <= entry_depth)
        result = await db.execute(query)
        entries: List[Entry] = result.scalars().all()
        # 返回文件或目录信息
        return ok(data=[entry.dict() for entry in entries])
    except:
        return internal_server_error()


class EntryPostRequest(BaseModel):
    entry_path: LiteralString
    entry_type: EntryType
    is_collabrative: bool = False
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
        # 验证文件路径
        request.entry_path = path_normalize(request.entry_path)
        if not request.entry_path:
            return bad_request(message="Invalid entry path")
        # 获取用户 ID
        owner_id = access_info["user_id"]
        # 验证文件是否已存在
        result = await db.execute(select(Entry).where(Entry.entry_path == request.entry_path, Entry.owner_id == owner_id))
        entry: Entry = result.first()
        if entry is not None:
            return bad_request(message="Entry already exists")
        # 目录设置协作缺省值
        if request.entry_type == EntryType.DIRECTORY:
            request.is_collabrative = False
        # 验证及自动创建父目录
        await create_parent_directories(db, request.entry_path, owner_id)
        # 创建 Entry 记录
        if request.entry_type == EntryType.FILE:
            # 验证文件是否为空
            if request.file is None:
                return bad_request(message="Missing file")
            # 生成文件别名
            storage_name = uuid.uuid4().hex
            # 异步保存文件到指定目录
            async with aiofiles.open(os.path.join(ENTRY_STORAGE_PATH, storage_name), "wb") as buf:
                while chunk := await request.file.read(1024 * 1024):  # 逐块读取 1MB
                    await buf.write(chunk)
            # 创建新的 Entry 记录
            db.add(
                Entry(
                    owner_id=owner_id,
                    entry_type=request.entry_type,
                    entry_path=request.entry_path,
                    storage_name=storage_name,
                    is_collabrative=request.is_collabrative,
                )
            )
        elif request.entry_type == EntryType.DIRECTORY:
            # 创建新的目录 Entry 记录
            db.add(
                Entry(
                    owner_id=owner_id,
                    entry_type=request.entry_type,
                    entry_path=request.entry_path,
                    storage_name=None,
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
    entry_path: LiteralString,
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
        entry_path = path_normalize(entry_path)
        if not entry_path:
            return bad_request(message="Invalid entry path")
        # 获取用户 ID
        owner_id = access_info["user_id"]
        # 查询 Entry 记录
        result = await db.execute(select(Entry).where(Entry.entry_path == entry_path, Entry.owner_id == owner_id))
        entry: Entry = result.first()
        # 验证文件是否存在
        if entry is None:
            return bad_request(message="Entry not found")
        if entry.entry_type == EntryType.FILE:
            # 删除文件
            await aiofiles.os.remove(os.path.join(ENTRY_STORAGE_PATH, entry.storage_name))
            await db.delete(entry)
        elif entry.entry_type == EntryType.DIRECTORY:
            # 删除目录及其子项
            result = await db.execute(select(Entry).where(Entry.entry_path.like(f"{entry_path}%"), Entry.owner_id == owner_id))
            sub_entries: List[Entry] = result.scalars().all()
            for sub_entry in sub_entries:
                if sub_entry.entry_type == EntryType.FILE:
                    await aiofiles.os.remove(os.path.join(ENTRY_STORAGE_PATH, sub_entry.storage_name))
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
    entry_path: LiteralString
    new_entry_path: LiteralString


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
        # 规范化文件路径
        request.entry_path, request.new_entry_path = path_normalize(request.entry_path), path_normalize(request.new_entry_path)
        if not request.entry_path or not request.new_entry_path:
            return bad_request(message="Invalid entry path")
        # 验证文件路径是否相同
        if request.entry_path == request.new_entry_path:
            return bad_request(message="Entry path unchanged")
        # 获取用户 ID
        owner_id = access_info["user_id"]
        # 查询 Entry 记录
        result = await db.execute(select(Entry).where(Entry.entry_path == request.entry_path, Entry.owner_id == owner_id))
        entry: Entry = result.first()
        # 验证文件是否存在
        if entry is None:
            return bad_request(message="Entry not found")
        # 验证新文件是否已存在
        result = await db.execute(select(Entry).where(Entry.entry_path == request.new_entry_path, Entry.owner_id == owner_id))
        new_entry: Entry = result.first()
        if new_entry is not None:
            return bad_request(message="New entry already exists")
        # 验证及自动创建父目录
        await create_parent_directories(db, request.new_entry_path, owner_id)
        # 移动文件或目录
        if entry.entry_type == EntryType.DIRECTORY:
            result = await db.execute(select(Entry).where(Entry.entry_path.like(f"{request.entry_path}%"), Entry.owner_id == owner_id))
            sub_entries: List[Entry] = result.scalars().all()
            for sub_entry in sub_entries:
                sub_entry.entry_path = request.new_entry_path + sub_entry.entry_path[len(request.entry_path) :]
        entry.entry_path = request.new_entry_path
        # 提交数据库事务
        await db.commit()
        return ok()
    except:
        await db.rollback()
        return internal_server_error()


@api.get("/download")
async def entry_download(
    entry_path: LiteralString,
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
        # 规范化文件路径
        entry_path = path_normalize(entry_path)
        if not entry_path:
            return bad_request(message="Invalid entry path")
        # 获取用户 ID
        owner_id = access_info["user_id"]
        # 查询 Entry 记录
        result = await db.execute(select(Entry).where(Entry.entry_path == entry_path, Entry.owner_id == owner_id))
        entry: Entry = result.first()
        # 验证文件是否存在
        if entry is None:
            return bad_request(message="Entry not found")
        # 验证文件类型
        if entry.entry_type != EntryType.FILE:
            return bad_request(message="Entry is not a file")
        # 返回文件内容
        async with aiofiles.open(os.path.join(ENTRY_STORAGE_PATH, entry.storage_name), "rb") as buf:
            return await buf.read()
    except:
        return internal_server_error()


async def create_parent_directories(
    db: AsyncSession,
    entry_path: LiteralString,
    owner_id: int,
):
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
        entry: Entry = result.first()
        if entry is None:
            db.add(
                Entry(
                    owner_id=owner_id,
                    entry_type=EntryType.DIRECTORY,
                    entry_path=path,
                    storage_name=None,
                )
            )
    await db.commit()
