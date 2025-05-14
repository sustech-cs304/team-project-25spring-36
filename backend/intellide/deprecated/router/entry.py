import os
import uuid
from typing import Dict, Optional, Sequence

import aiofiles
import aiofiles.os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from intellide.config import STORAGE_PATH
from intellide.database.database import database
from intellide.database.model import (
    Entry,
    EntryType,
)
from intellide.storage.storage import storage_write_file, storage_get_file_response
from intellide.utils.auth import jwe_decode
from intellide.utils.path import path_normalize, path_dir_base_name
from intellide.utils.response import ok, bad_request, internal_server_error, APIError

api = APIRouter(prefix="/entry")


@api.get("")
async def entry_get(
    entry_path: str,
    entry_depth: Optional[int] = None,
    db: AsyncSession = Depends(database),
    access_info: Dict = Depends(jwe_decode),
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
    # 规范化文件路径
    entry_path = path_normalize(entry_path)
    # 返回文件或目录信息
    return ok(data=[entry.dict() for entry in await select_entries(access_info["user_id"], entry_path, entry_depth, db)])


@api.post("")
async def entry_post(
    entry_path: str = Form(...),
    entry_type: EntryType = Form(...),
    is_collaborative: bool = Form(False),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(database),
    access_info: Dict = Depends(jwe_decode),
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
    # 获取用户 ID
    await post_entry(
        owner_id=access_info["user_id"],
        entry_path=entry_path,
        is_collaborative=is_collaborative,
        entry_type=entry_type,
        file=file,
        db=db,
    )
    return ok()


@api.delete("")
async def entry_delete(
    entry_path: str,
    db: AsyncSession = Depends(database),
    access_info: Dict = Depends(jwe_decode),
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
    # 规范化文件路径
    # 寻找文件或目录
    await delete_entry(
        owner_id=access_info["user_id"],
        entry_path=entry_path,
        db=db,
    )
    return ok()


class EntryMoveRequest(BaseModel):
    src_entry_path: str
    dst_entry_path: str


@api.put("/move")
async def entry_move(
    request: EntryMoveRequest,
    db: AsyncSession = Depends(database),
    access_info: Dict = Depends(jwe_decode),
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
    # 验证文件路径是否相同
    await move_entry(
        owner_id=access_info["user_id"],
        src_entry_path=request.src_entry_path,
        dst_entry_path=request.dst_entry_path,
        db=db,
    )
    return ok()


@api.get("/download")
async def entry_download(
    entry_path: str,
    db: AsyncSession = Depends(database),
    access_info: Dict = Depends(jwe_decode),
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
        return await download_entry(entry_path, access_info["user_id"], db)
    except HTTPException:
        raise
    except APIError as e:
        raise HTTPException(status_code=e.code(), detail=e.message())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def post_entry_parents(
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


async def select_entries(
    owner_id: int,
    entry_path: str,
    entry_depth: Optional[int],
    db: AsyncSession,
) -> Sequence[Entry]:
    query = select(Entry).where(Entry.entry_path.like(f"{entry_path}%"), Entry.owner_id == owner_id)
    # 限制文件深度
    if entry_depth:
        query = query.where(Entry.entry_depth <= entry_depth)
    result = await db.execute(query)
    return result.scalars().all()


async def select_entry_by_entry_path(
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
        raise APIError(bad_request, "Invalid entry path")
    # 查询 Entry 记录
    result = await db.execute(select(Entry).where(Entry.entry_path == entry_path, Entry.owner_id == owner_id))
    entry: Entry = result.scalar()
    if not nullable and entry is None:
        raise APIError(bad_request, message="Entry not found")
    return entry


async def download_entry(
    entry_path: str,
    owner_id: int,
    db: AsyncSession,
) -> FileResponse:
    entry: Entry = await select_entry_by_entry_path(entry_path, owner_id, db)
    # 验证文件类型
    if entry.entry_type != EntryType.FILE:
        raise HTTPException(status_code=400, detail="Entry is not a file")
    # 获取文件名
    _, file_name = path_dir_base_name(entry_path)
    # 返回文件内容
    return storage_get_file_response(entry.storage_name, file_name)


async def delete_entry(
    owner_id: int,
    entry_path: str,
    db: AsyncSession,
):
    # 寻找文件或目录
    entry: Entry = await select_entry_by_entry_path(entry_path, owner_id, db)
    # 删除文件或目录
    if entry.entry_type == EntryType.FILE:
        # 删除文件
        await aiofiles.os.remove(os.path.join(STORAGE_PATH, entry.storage_name))
        await db.delete(entry)
    elif entry.entry_type == EntryType.DIRECTORY:
        # 删除目录及其子项
        result = await db.execute(
            select(Entry).where(
                Entry.entry_path.like(f"{entry.entry_path}%"),
                Entry.owner_id == entry.owner_id,
            )
        )
        sub_entries: Sequence[Entry] = result.scalars().all()
        for sub_entry in sub_entries:
            if sub_entry.entry_type == EntryType.FILE:
                await aiofiles.os.remove(os.path.join(STORAGE_PATH, sub_entry.storage_name))
            await db.delete(sub_entry)
    else:
        raise APIError(internal_server_error, "Invalid entry type")
    await db.commit()


async def post_entry(
    owner_id: int,
    entry_path: str,
    is_collaborative: bool,
    entry_type: EntryType,
    file: Optional[UploadFile],
    db: AsyncSession,
):
    # 查询 Entry 记录
    entry: Optional[Entry] = await select_entry_by_entry_path(entry_path, owner_id, db, nullable=True)
    if entry is not None:
        raise APIError(bad_request, message="Entry already exists")
    # 验证及自动创建父目录
    await post_entry_parents(entry_path, owner_id, db)
    # 创建 Entry 记录
    if entry_type == EntryType.FILE:
        # 验证文件是否为空
        if file is None:
            raise APIError(bad_request, "Missing file")
        # 生成文件别名
        storage_name = uuid.uuid4().hex
        # 异步保存文件到指定目录
        await storage_write_file(storage_name, await file.read())
        # 创建新的 Entry 记录
        db.add(
            Entry(
                owner_id=owner_id,
                entry_type=entry_type,
                entry_path=entry_path,
                storage_name=storage_name,
                is_collaborative=is_collaborative,
            )
        )
    elif entry_type == EntryType.DIRECTORY:
        # 创建新的目录 Entry 记录
        db.add(
            Entry(
                owner_id=owner_id,
                entry_type=entry_type,
                entry_path=entry_path,
            )
        )
    else:
        raise APIError(internal_server_error, "Invalid entry type")
    await db.commit()


async def move_entry(
    owner_id: int,
    src_entry_path: str,
    dst_entry_path: str,
    db: AsyncSession,
):
    if src_entry_path == dst_entry_path:
        raise APIError(bad_request, "Entry path unchanged")
    # 获取用户 ID
    src_entry: Entry = await select_entry_by_entry_path(src_entry_path, owner_id, db)
    dst_entry: Entry = await select_entry_by_entry_path(
        dst_entry_path,
        owner_id,
        db,
        nullable=True,
    )
    # 断言新路径不存在
    if dst_entry is not None:
        raise APIError(bad_request, "New entry already exists")
    # 验证及自动创建父目录
    await post_entry_parents(dst_entry_path, owner_id, db)
    # 移动文件或目录
    if src_entry.entry_type == EntryType.DIRECTORY:
        result = await db.execute(
            select(Entry).where(
                Entry.entry_path.like(f"{src_entry.entry_path}%"),
                Entry.owner_id == owner_id,
            )
        )
        sub_entries: Sequence[Entry] = result.scalars().all()
        for sub_entry in sub_entries:
            sub_entry.entry_path = dst_entry_path + sub_entry.entry_path[len(src_entry.entry_path) :]
    elif src_entry.entry_type == EntryType.FILE:
        src_entry.entry_path = dst_entry_path
    else:
        raise APIError(internal_server_error, "Invalid entry type")
    await db.commit()
